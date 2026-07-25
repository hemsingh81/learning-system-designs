using Confluent.Kafka;
using MarketData.Contracts;

namespace MarketData.FeedHandler.Publishing;

// ─────────────────────────────────────────────────────────────────────────────
// PUBLISHING 200,000 TICKS A SECOND
//
// Everything here is shaped by one fact: at this rate, per-message work is not
// affordable. A single blocking await per tick would cap you at a few thousand
// a second no matter how fast the hardware is.
//
// Four decisions carry the whole design:
//
//   1. KEY = SYMBOL          → per-symbol ordering, cross-symbol parallelism
//   2. Acks.Leader           → do not wait for replicas (a deliberate trade)
//   3. LingerMs = 5          → batch aggressively
//   4. Fire and forget       → never await a per-message produce
// ─────────────────────────────────────────────────────────────────────────────

public sealed class TickProducer : IAsyncDisposable
{
    private readonly IProducer<string, byte[]> _producer;
    private readonly SequenceTracker           _sequences;
    private readonly IMetrics                  _metrics;
    private readonly ILogger<TickProducer>     _log;

    private const string RawTopic = "market.ticks.raw";
    private const string GapTopic = "market.gaps";

    public TickProducer(
        IConfiguration config,
        SequenceTracker sequences,
        IMetrics metrics,
        ILogger<TickProducer> log)
    {
        _sequences = sequences;
        _metrics   = metrics;
        _log       = log;

        var producerConfig = new ProducerConfig
        {
            BootstrapServers = config["Kafka:BootstrapServers"],

            // ── Acks.Leader, NOT Acks.All ───────────────────────────────────
            // All would wait for every replica and roughly triples produce
            // latency. At 200k/sec that is the difference between keeping up
            // and falling behind.
            //
            // What we accept: if the leader dies before replicating, a few
            // milliseconds of ticks are lost — and the sequence tracker below
            // makes that loss VISIBLE rather than silent.
            //
            // In the banking case study this same line is Acks.All, and that is
            // also correct. Durability is a dial, set by the business.
            Acks = Acks.Leader,

            // ── Batching ────────────────────────────────────────────────────
            // Wait up to 5ms to fill a batch. Five milliseconds of latency buys
            // roughly an order of magnitude of throughput. On this path that is
            // an easy trade; on an order-entry path it would not be.
            LingerMs  = 5,
            BatchSize = 1_000_000,          // 1MB batches

            // Market data compresses extremely well — the same symbols and
            // similar prices repeat constantly. LZ4 is fast enough to stay in
            // the hot path; gzip is not.
            CompressionType = CompressionType.Lz4,

            // ── Idempotent producer ─────────────────────────────────────────
            // Without this, an internal retry after a network blip silently
            // writes the message twice, and a duplicate tick corrupts a candle's
            // volume with no error anywhere.
            EnableIdempotence = true,
            MessageSendMaxRetries = 3,

            // ── Backpressure ────────────────────────────────────────────────
            // If Kafka is unavailable, this buffer fills. When it is full,
            // ProduceAsync BLOCKS (see below) rather than throwing — which
            // slows the reader instead of losing data silently.
            QueueBufferingMaxMessages = 1_000_000,
            QueueBufferingMaxKbytes   = 512_000
        };

        _producer = new ProducerBuilder<string, byte[]>(producerConfig)
            .SetErrorHandler((_, e) =>
            {
                // Log, but do NOT stop. A transient broker error must not kill
                // the feed handler — it is a single point of failure per exchange.
                if (e.IsFatal) _log.LogCritical("Fatal Kafka error: {Reason}", e.Reason);
                else           _log.LogWarning("Kafka error: {Reason}", e.Reason);
            })
            .Build();
    }

    /// <summary>
    /// Publish one tick. Called ~200,000 times a second, so it must not allocate
    /// more than necessary and must never block on the happy path.
    /// </summary>
    public void Publish(in Tick tick)
    {
        // ── 1. Gap detection, before anything else ──────────────────────────
        // The exchange numbers every message. A jump means we missed some.
        //
        // A gap must become DATA, not just a log line: downstream consumers mark
        // affected candles incomplete so nobody backtests against a hole and gets
        // a confident, wrong answer.
        var gap = _sequences.Check(tick.Symbol, tick.SequenceNumber);

        if (gap is { } g)
        {
            _log.LogWarning("Sequence gap on {Symbol}: expected {Expected}, got {Actual} ({Count} missing)",
                tick.Symbol, g.Expected, g.Actual, g.MissingCount);

            _metrics.GapDetected(tick.Symbol, g.MissingCount);
            PublishGap(g);
        }

        // ── 2. Fire and forget ──────────────────────────────────────────────
        //
        // `Produce` (not `ProduceAsync`) hands the message to the client's
        // internal queue and returns immediately. A background thread batches
        // and sends it.
        //
        // Awaiting a per-message ProduceAsync here would serialise the whole
        // feed and cap us at a few thousand ticks a second.
        try
        {
            _producer.Produce(
                RawTopic,
                new Message<string, byte[]>
                {
                    // ── THE MOST IMPORTANT LINE IN THIS FILE ────────────────
                    // Key = symbol means:
                    //   • all RELIANCE ticks go to ONE partition → strictly ordered
                    //   • different symbols spread across 64 partitions → parallel
                    //
                    // null here would destroy ordering. A constant would destroy
                    // parallelism. Both failures are silent until a candle is wrong.
                    Key   = tick.Symbol,
                    Value = TickSerializer.Serialize(tick),

                    // Kafka timestamp = EXCHANGE time, not our time. Replays and
                    // backtests must see the market's clock, never the server's.
                    Timestamp = new Timestamp(tick.ExchangeTimestampUtc)
                },
                DeliveryHandler);   // called on a background thread
        }
        catch (ProduceException<string, byte[]> ex) when (ex.Error.Code == ErrorCode.Local_QueueFull)
        {
            // ── BACKPRESSURE ────────────────────────────────────────────────
            // The internal buffer is full: Kafka is down or we are producing
            // faster than it can accept.
            //
            // There is no good option here, only a chosen one. We drop and COUNT,
            // because blocking would stall the exchange socket and cause the
            // exchange to disconnect us — which loses far more data.
            //
            // The counter is what makes this survivable: loss is measured.
            _metrics.TickDropped(tick.Symbol);

            _log.LogError("Producer queue full — dropping tick for {Symbol}. " +
                          "Kafka is unavailable or too slow.", tick.Symbol);
        }
    }

    // Runs on a background thread, once per message. Keep it tiny — anything
    // slow here becomes a throughput ceiling for the whole producer.
    private void DeliveryHandler(DeliveryReport<string, byte[]> report)
    {
        if (report.Error.IsError)
        {
            _metrics.PublishFailed(report.Topic);

            // Do not retry here: the client already retried. A failure at this
            // point means the message is genuinely lost, and the honest response
            // is to count it so the gap is visible.
            _log.LogError("Delivery failed for {Topic}: {Reason}", report.Topic, report.Error.Reason);
        }
        else
        {
            _metrics.TickPublished(report.Partition.Value);
        }
    }

    private void PublishGap(SequenceGap gap)
    {
        // Gaps are rare and important, so this path can afford to be slower and
        // more durable than the tick path.
        _producer.Produce(GapTopic, new Message<string, byte[]>
        {
            Key   = gap.Symbol,
            Value = TickSerializer.SerializeGap(gap)
        });
    }

    public async ValueTask DisposeAsync()
    {
        // Flush before exiting, or everything still in the batch buffer is lost.
        // 10 seconds is generous; a shutdown that cannot flush in that time has
        // a bigger problem than this handler.
        _log.LogInformation("Flushing producer before shutdown");
        _producer.Flush(TimeSpan.FromSeconds(10));
        _producer.Dispose();
        await ValueTask.CompletedTask;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// SEQUENCE TRACKING
//
// The exchange numbers every message per symbol. This class is the only thing
// standing between "we lost data" and "we lost data and nobody knows".
// ─────────────────────────────────────────────────────────────────────────────

public sealed class SequenceTracker
{
    // Plain Dictionary, not ConcurrentDictionary: the feed handler is
    // single-threaded per connection by design (see the README — it cannot
    // scale horizontally). A concurrent collection here would add lock overhead
    // 200,000 times a second for no benefit.
    private readonly Dictionary<string, long> _expected = new(8192, StringComparer.Ordinal);

    public SequenceGap? Check(string symbol, long sequenceNumber)
    {
        if (!_expected.TryGetValue(symbol, out var expected))
        {
            // First tick for this symbol today. Nothing to compare against.
            _expected[symbol] = sequenceNumber + 1;
            return null;
        }

        if (sequenceNumber == expected)
        {
            _expected[symbol] = sequenceNumber + 1;
            return null;                                  // the normal path
        }

        if (sequenceNumber < expected)
        {
            // A REPLAY or a duplicate — the exchange resent something.
            // Not a gap. The normaliser will deduplicate it downstream.
            return null;
        }

        // sequenceNumber > expected: we missed (sequenceNumber - expected) messages.
        var gap = new SequenceGap(symbol, expected, sequenceNumber, sequenceNumber - expected);
        _expected[symbol] = sequenceNumber + 1;           // resync, do not stall
        return gap;
    }
}

public readonly record struct SequenceGap(
    string Symbol,
    long   Expected,
    long   Actual,
    long   MissingCount);
