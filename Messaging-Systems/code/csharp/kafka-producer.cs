// =============================================================================
// kafka-producer.cs — publishing order events to Apache Kafka
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Build one producer object when the process starts. Keep it for the whole
//     life of the process. Creating one per message is the single most common
//     performance mistake — each one opens its own TCP connections and its own
//     background batching thread.
//  2. Turn on idempotence [the broker remembers the last few writes from this
//     producer and silently drops a repeat]. This costs almost nothing and
//     removes duplicate writes caused by network retries.
//  3. Ask for acks=all [wait until every in-sync copy of the partition has the
//     record before calling it written]. Combined with min.insync.replicas=2 on
//     the broker, a confirmed write survives losing one broker.
//  4. Choose a key for every message. The key decides the partition, and one
//     partition is one ordered line. Use the entity the ordering is about —
//     orderId here, not customerId, not a random value.
//  5. Put the identity of the message in a header, not only in the body. The
//     consumer needs an idempotency key [a value it can check to spot a repeat]
//     before it deserialises anything.
//  6. Send, and await the delivery report. Do NOT fire and forget: a send that
//     is only queued in memory is not a send. If the process dies, it is gone.
//  7. On failure, look at whether the error is retriable. Retriable means the
//     client already tried and gave up — retry with backoff. Non-retriable
//     means the message is wrong; log it and stop, do not spin.
//  8. Flush on shutdown. Anything still in the in-memory batch is lost if you
//     skip this.
//
// The transactional path at the bottom is only for read-process-write loops
// inside Kafka. It does NOT make a Kafka write and a database write atomic —
// nothing does. For that, use the outbox pattern (see docs/tutorial.md).
//
// Run:  dotnet run --project . -- produce
// See:  README.md in this folder
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Confluent.Kafka;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.Kafka;

public sealed record OrderPlaced(
    string OrderId,
    string CustomerId,
    string Region,
    decimal Total,
    string Currency,
    DateTimeOffset PlacedAtUtc);

/// <summary>
/// One instance per process. Register as a singleton. Thread-safe.
/// </summary>
public sealed class OrderEventProducer : IAsyncDisposable
{
    private const string Topic = "orders.v1";

    private readonly IProducer<string, byte[]> _producer;
    private readonly ILogger<OrderEventProducer> _log;

    public OrderEventProducer(string bootstrapServers, ILogger<OrderEventProducer> log)
    {
        _log = log;

        var config = new ProducerConfig
        {
            BootstrapServers = bootstrapServers,

            // ---- Durability -----------------------------------------------
            // acks=all + broker-side min.insync.replicas=2 is the pair that
            // actually protects you. Setting only one of them is theatre.
            Acks = Acks.All,
            EnableIdempotence = true,          // implies MaxInFlight <= 5 and retries > 0
            MessageSendMaxRetries = 10,
            RetryBackoffMs = 100,

            // ---- Throughput ------------------------------------------------
            // LingerMs is the knob most people leave at 0 and then wonder why
            // throughput is poor. 5ms of waiting lets the client fill a batch,
            // which can be a 10x difference on small messages.
            LingerMs = 5,
            BatchSize = 64 * 1024,
            CompressionType = CompressionType.Zstd,   // lz4 if CPU is tight

            // ---- Backpressure ----------------------------------------------
            // When the local queue fills, block the caller instead of throwing.
            // A throw here usually turns into a dropped order.
            QueueBufferingMaxMessages = 100_000,
            QueueBufferingMaxKbytes = 256 * 1024,
            EnableDeliveryReports = true,

            // ---- Security --------------------------------------------------
            // For a local docker-compose broker, delete these four lines.
            SecurityProtocol = SecurityProtocol.SaslSsl,
            SaslMechanism = SaslMechanism.ScramSha512,
            SaslUsername = Environment.GetEnvironmentVariable("KAFKA_USER"),
            SaslPassword = Environment.GetEnvironmentVariable("KAFKA_PASSWORD"),

            // ---- Identity ---------------------------------------------------
            // Shows up in broker logs and quota metrics. Worth setting.
            ClientId = $"order-api-{Environment.MachineName}",
        };

        _producer = new ProducerBuilder<string, byte[]>(config)
            .SetErrorHandler((_, e) =>
            {
                // Fatal errors mean the producer is dead and must be rebuilt.
                if (e.IsFatal) _log.LogCritical("Kafka producer fatal: {Reason}", e.Reason);
                else _log.LogWarning("Kafka producer error: {Reason}", e.Reason);
            })
            .SetLogHandler((_, m) => _log.LogDebug("librdkafka: {Message}", m.Message))
            .Build();
    }

    /// <summary>
    /// Step 4-6 of the algorithm. Returns the offset the broker assigned, which
    /// is worth logging — it is how you find this exact record again later.
    /// </summary>
    public async Task<long> PublishAsync(OrderPlaced order, CancellationToken ct = default)
    {
        // Step 5: identity travels in headers so a consumer can dedupe cheaply.
        var headers = new Headers
        {
            { "message-id",   Encoding.UTF8.GetBytes(Guid.NewGuid().ToString("N")) },
            { "message-type", Encoding.UTF8.GetBytes(nameof(OrderPlaced)) },
            { "schema-version", Encoding.UTF8.GetBytes("1") },
            { "correlation-id", Encoding.UTF8.GetBytes(order.OrderId) },
            { "produced-at",  Encoding.UTF8.GetBytes(DateTimeOffset.UtcNow.ToString("O")) },
        };

        var message = new Message<string, byte[]>
        {
            // Step 4: the key IS the ordering contract. Everything about
            // order-123 goes to the same partition, so it is read in order.
            Key = order.OrderId,
            Value = JsonSerializer.SerializeToUtf8Bytes(order),
            Headers = headers,
            Timestamp = new Timestamp(order.PlacedAtUtc),
        };

        try
        {
            // Step 6: await. A queued send is not a send.
            var result = await _producer.ProduceAsync(Topic, message, ct);

            _log.LogInformation(
                "Published {OrderId} to {Topic}[{Partition}]@{Offset}",
                order.OrderId, result.Topic, result.Partition.Value, result.Offset.Value);

            return result.Offset.Value;
        }
        catch (ProduceException<string, byte[]> ex)
        {
            // Step 7: retriable vs not. This distinction decides whether you
            // retry or page someone.
            if (ex.Error.IsFatal)
            {
                _log.LogCritical(ex, "Fatal produce failure for {OrderId}. Producer must be recreated.", order.OrderId);
                throw;
            }

            _log.LogError(ex,
                "Produce failed for {OrderId}: {Code} {Reason}. Retriable={Retriable}",
                order.OrderId, ex.Error.Code, ex.Error.Reason, ex.Error.IsError);
            throw;
        }
    }

    /// <summary>
    /// Step 8. Called by DI on shutdown. 15 seconds is a reasonable ceiling —
    /// long enough to drain a healthy batch, short enough not to hang a rolling
    /// deploy behind a dead broker.
    /// </summary>
    public ValueTask DisposeAsync()
    {
        var remaining = _producer.Flush(TimeSpan.FromSeconds(15));
        if (remaining > 0)
            _log.LogError("Shutdown dropped {Count} unsent messages", remaining);

        _producer.Dispose();
        return ValueTask.CompletedTask;
    }
}

// =============================================================================
// TRANSACTIONAL PRODUCER — the read-process-write loop
//
// ALGORITHM, IN PLAIN ENGLISH:
//  1. Give the producer a transactional id that is STABLE across restarts.
//     If it changes on every deploy, the guarantee is gone. Derive it from the
//     partition set you own, not from a Guid.
//  2. Initialise transactions once at startup. This fences out any zombie
//     instance still running with the same id.
//  3. For each batch: begin, produce the outputs, send the input offsets INTO
//     the transaction, then commit. The offsets and the outputs commit together
//     or not at all.
//  4. On a retriable abort, abort and reprocess. On a fatal error, die and let
//     the orchestrator restart you.
//
// This gives exactly-once only for Kafka-to-Kafka. The moment a database or an
// HTTP call is in the loop, you are back to at-least-once plus idempotency.
// =============================================================================

public sealed class TransactionalOrderProcessor
{
    private readonly IProducer<string, byte[]> _producer;
    private readonly IConsumer<string, byte[]> _consumer;
    private readonly ILogger _log;

    public TransactionalOrderProcessor(
        string bootstrapServers, string transactionalId, ILogger log)
    {
        _log = log;

        // Step 1: stable id. "payments-processor-0" for the instance that owns
        // partition 0 — not Guid.NewGuid().
        var producerConfig = new ProducerConfig
        {
            BootstrapServers = bootstrapServers,
            TransactionalId = transactionalId,
            EnableIdempotence = true,
            Acks = Acks.All,
            TransactionTimeoutMs = 60_000,
        };

        var consumerConfig = new ConsumerConfig
        {
            BootstrapServers = bootstrapServers,
            GroupId = "payments-processor",
            EnableAutoCommit = false,                       // the transaction commits offsets
            IsolationLevel = IsolationLevel.ReadCommitted,  // never read uncommitted output
            AutoOffsetReset = AutoOffsetReset.Earliest,
        };

        _producer = new ProducerBuilder<string, byte[]>(producerConfig).Build();
        _consumer = new ConsumerBuilder<string, byte[]>(consumerConfig).Build();

        // Step 2: fences out zombies holding the same transactional id.
        _producer.InitTransactions(TimeSpan.FromSeconds(30));
    }

    public void Run(CancellationToken ct)
    {
        _consumer.Subscribe("orders.v1");

        while (!ct.IsCancellationRequested)
        {
            var batch = new List<ConsumeResult<string, byte[]>>();
            var deadline = DateTime.UtcNow.AddMilliseconds(200);

            while (DateTime.UtcNow < deadline && batch.Count < 500)
            {
                var r = _consumer.Consume(TimeSpan.FromMilliseconds(50));
                if (r is not null) batch.Add(r);
            }

            if (batch.Count == 0) continue;

            // Step 3: everything below either all happens or none of it does.
            _producer.BeginTransaction();
            try
            {
                foreach (var record in batch)
                {
                    var outputs = Transform(record);
                    foreach (var o in outputs)
                        _producer.Produce("payments.v1", o);
                }

                // The offsets go INSIDE the transaction. This is the part
                // people forget, and it is the whole trick.
                _producer.SendOffsetsToTransaction(
                    _consumer.Assignment.ConvertAll(tp =>
                        new TopicPartitionOffset(tp, _consumer.Position(tp))),
                    _consumer.ConsumerGroupMetadata,
                    TimeSpan.FromSeconds(30));

                _producer.CommitTransaction();
                _log.LogInformation("Committed transaction of {Count} records", batch.Count);
            }
            catch (KafkaTxnRequiresAbortException)
            {
                // Step 4: retriable. Abort and let the next loop reprocess.
                _log.LogWarning("Transaction aborted, will reprocess");
                _producer.AbortTransaction();
            }
            catch (KafkaException ex) when (ex.Error.IsFatal)
            {
                _log.LogCritical(ex, "Fatal transaction error — exiting for restart");
                throw;
            }
        }
    }

    private static IEnumerable<Message<string, byte[]>> Transform(
        ConsumeResult<string, byte[]> input)
    {
        yield return new Message<string, byte[]>
        {
            Key = input.Message.Key,
            Value = input.Message.Value,
            Headers = input.Message.Headers,
        };
    }
}
