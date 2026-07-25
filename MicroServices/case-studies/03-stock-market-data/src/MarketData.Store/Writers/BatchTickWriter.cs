using System.Diagnostics;
using Confluent.Kafka;
using MarketData.Contracts;
using Npgsql;

namespace MarketData.Store.Writers;

// ─────────────────────────────────────────────────────────────────────────────
// WRITING 200,000 ROWS A SECOND
//
// One decision dominates: NEVER write per row.
//
//   Per-row INSERT           ~2,000 rows/sec       ← impossible here
//   Batched INSERT (10k)     ~150,000 rows/sec
//   COPY / bulk binary       ~1,000,000 rows/sec   ← what we use
//
// The second decision is subtler and easier to get wrong:
//
//   COMMIT THE KAFKA OFFSET ONLY AFTER THE WRITE IS DURABLE.
//
// Commit first and a crash loses the whole buffer permanently, with no record
// of what was lost. Commit after and a crash re-reads those ticks — a duplicate,
// which the primary key absorbs. Loss is unrecoverable; duplication is not.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class BatchTickWriter(
    NpgsqlDataSource dataSource,
    IMetrics metrics,
    ILogger<BatchTickWriter> log) : BackgroundService
{
    private const int    BatchSize    = 10_000;
    private static readonly TimeSpan MaxBufferAge = TimeSpan.FromSeconds(1);

    private readonly List<Tick> _buffer = new(BatchSize);
    private readonly Stopwatch  _sinceFlush = Stopwatch.StartNew();

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        var config = new ConsumerConfig
        {
            BootstrapServers = "kafka:9092",
            GroupId          = "market-store",

            // MANUAL commits. The whole correctness argument above depends on
            // this being false — auto-commit would move the offset on a timer,
            // with no relationship to whether the data reached the database.
            EnableAutoCommit = false,

            // A new consumer group starts at the beginning, so a fresh deployment
            // backfills whatever is still in the log rather than silently skipping it.
            AutoOffsetReset = AutoOffsetReset.Earliest,

            // Large fetches: we want throughput, not low latency, on this path.
            FetchMinBytes   = 1_000_000,
            FetchWaitMaxMs  = 100,

            // If we stop calling Consume for longer than this, Kafka assumes we
            // died and rebalances. It must be comfortably longer than the worst
            // flush — otherwise a slow database causes an endless rebalance loop,
            // which looks like a Kafka problem and is really a database problem.
            MaxPollIntervalMs = 300_000
        };

        using var consumer = new ConsumerBuilder<string, byte[]>(config)
            .SetPartitionsRevokedHandler((c, partitions) =>
            {
                // A rebalance is taking our partitions away. Flush what we hold
                // and commit, or those ticks are re-read by whoever gets the
                // partition next — pure duplicate work.
                log.LogInformation("Partitions revoked, flushing {Count} buffered ticks", _buffer.Count);
                FlushAsync(c, CancellationToken.None).GetAwaiter().GetResult();
            })
            .Build();

        consumer.Subscribe("market.ticks.clean");

        log.LogInformation("Store consumer started");

        while (!ct.IsCancellationRequested)
        {
            try
            {
                // Short timeout so the time-based flush below stays responsive
                // even when no messages are arriving.
                var result = consumer.Consume(TimeSpan.FromMilliseconds(100));

                if (result is not null)
                    _buffer.Add(TickSerializer.Deserialize(result.Message.Value));

                // ── Flush on size OR age ────────────────────────────────────
                // The age bound matters: without it, a quiet symbol's last few
                // ticks sit in the buffer until the next busy period — possibly
                // hours, and invisible in every dashboard.
                if (_buffer.Count >= BatchSize || (_buffer.Count > 0 && _sinceFlush.Elapsed > MaxBufferAge))
                    await FlushAsync(consumer, ct);
            }
            catch (OperationCanceledException) when (ct.IsCancellationRequested)
            {
                break;
            }
            catch (ConsumeException ex)
            {
                log.LogError(ex, "Consume error: {Reason}", ex.Error.Reason);
                await Task.Delay(TimeSpan.FromSeconds(1), ct);
            }
        }

        // Final flush on shutdown, or the buffer is lost.
        await FlushAsync(consumer, CancellationToken.None);
        consumer.Close();
    }

    private async Task FlushAsync(IConsumer<string, byte[]> consumer, CancellationToken ct)
    {
        if (_buffer.Count == 0) return;

        var count = _buffer.Count;
        var sw    = Stopwatch.StartNew();

        try
        {
            // ── 1. Write, using binary COPY ─────────────────────────────────
            // PostgreSQL's COPY is roughly 10× faster than a multi-row INSERT
            // and does not build a giant SQL string in memory.
            await using var conn   = await dataSource.OpenConnectionAsync(ct);
            await using var writer = await conn.BeginBinaryImportAsync(
                "COPY ticks (symbol, exchange_time, price, quantity, sequence_number, follows_gap) " +
                "FROM STDIN (FORMAT BINARY)", ct);

            foreach (var tick in _buffer)
            {
                await writer.StartRowAsync(ct);
                await writer.WriteAsync(tick.Symbol,               NpgsqlTypes.NpgsqlDbType.Text, ct);
                await writer.WriteAsync(tick.ExchangeTimestampUtc, NpgsqlTypes.NpgsqlDbType.TimestampTz, ct);
                await writer.WriteAsync(tick.Price,                NpgsqlTypes.NpgsqlDbType.Numeric, ct);
                await writer.WriteAsync(tick.Quantity,             NpgsqlTypes.NpgsqlDbType.Bigint, ct);
                await writer.WriteAsync(tick.SequenceNumber,       NpgsqlTypes.NpgsqlDbType.Bigint, ct);
                await writer.WriteAsync(tick.FollowsGap,           NpgsqlTypes.NpgsqlDbType.Boolean, ct);
            }

            await writer.CompleteAsync(ct);   // ← the data is durable at this line

            // ── 2. ONLY NOW commit the offset ───────────────────────────────
            //
            // If the process dies between step 1 and step 2, Kafka redelivers
            // these ticks and we write them again. The primary key
            // (symbol, exchange_time, sequence_number) absorbs the duplicate.
            //
            // If we had committed first and died before step 1, these ticks would
            // be gone forever, and nothing would ever tell us which ones.
            //
            // Duplicate: recoverable. Loss: not. Always choose duplicate.
            consumer.Commit();

            _buffer.Clear();
            _sinceFlush.Restart();

            metrics.TicksWritten(count, sw.Elapsed);

            if (sw.ElapsedMilliseconds > 500)
            {
                // A slow flush is the first sign of trouble: it pushes the buffer
                // towards MaxPollIntervalMs and, past that, into a rebalance loop.
                log.LogWarning("Slow flush: {Count} ticks in {Ms}ms", count, sw.ElapsedMilliseconds);
            }
        }
        catch (PostgresException ex) when (ex.SqlState == "23505")
        {
            // Duplicate key: these ticks are already stored, from a redelivery
            // after an earlier crash. This is the design working as intended.
            //
            // Commit the offset so we move past them — NOT committing would
            // replay the same batch forever.
            log.LogInformation("Batch of {Count} already stored (redelivery), skipping", count);

            consumer.Commit();
            _buffer.Clear();
            _sinceFlush.Restart();
        }
        catch (Exception ex)
        {
            // Do NOT commit. Do NOT clear the buffer. The next attempt retries
            // the same data. Falling behind is recoverable; losing ticks is not.
            log.LogError(ex, "Flush failed for {Count} ticks, will retry", count);

            metrics.FlushFailed();

            // Back off so a database that is down does not get hammered while
            // consumer lag grows (which is the alert that should be firing).
            await Task.Delay(TimeSpan.FromSeconds(2), ct);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// THE TABLE
//
//   CREATE TABLE ticks (
//     symbol           text        NOT NULL,
//     exchange_time    timestamptz NOT NULL,
//     price            numeric(18,4) NOT NULL,
//     quantity         bigint      NOT NULL,
//     sequence_number  bigint      NOT NULL,
//     follows_gap      boolean     NOT NULL DEFAULT false,
//
//     -- This is what makes a redelivery harmless. Without it, the retry-safe
//     -- ordering above would silently double every replayed batch.
//     PRIMARY KEY (symbol, exchange_time, sequence_number)
//   );
//
//   -- TimescaleDB: partition by time so old chunks compress and drop cheaply.
//   SELECT create_hypertable('ticks', 'exchange_time', chunk_time_interval => INTERVAL '1 day');
//
//   -- 1.2 billion rows/day compresses roughly 20:1 — prices repeat constantly.
//   ALTER TABLE ticks SET (timescaledb.compress, timescaledb.compress_segmentby = 'symbol');
//   SELECT add_compression_policy('ticks', INTERVAL '7 days');
// ─────────────────────────────────────────────────────────────────────────────
