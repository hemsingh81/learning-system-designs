// =============================================================================
// kafka-consumer.cs — consuming order events, safely
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Join a consumer group [a named team of consumers that splits the
//     partitions between its members]. The group name is your identity; change
//     it and you start reading from scratch.
//  2. Turn OFF auto-commit. Auto-commit saves your position on a timer, whether
//     or not the work succeeded. That is how you silently lose messages.
//  3. Poll in a loop. Kafka's client is a state machine that only makes
//     progress while you call Consume. If you block the loop for longer than
//     max.poll.interval.ms, the group decides you are dead and takes your
//     partitions away — mid-work.
//  4. For each record: check the idempotency key first. If you have seen it,
//     skip straight to committing. This is what makes at-least-once delivery
//     safe to build on.
//  5. Do the work, then record the key and commit the offset — in that order,
//     and ideally in ONE database transaction with the work itself.
//  6. If the work fails: retry a few times in-process with backoff. If it still
//     fails, publish the record to a dead-letter topic and commit past it.
//     Never let one bad message stall the partition forever.
//  7. Commit in batches, not per message. Committing every record makes the
//     consumer group coordinator the bottleneck.
//  8. On shutdown, stop polling, commit what you have, and Close the consumer.
//     Close triggers a clean rebalance instead of a 45-second timeout.
//
// The offset you commit is "the next record I want", i.e. processed + 1.
// Off-by-one here reprocesses or skips exactly one message per restart, which
// is a maddening bug to find.
//
// Run: dotnet run --project . -- consume
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Confluent.Kafka;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.Kafka;

/// <summary>
/// Anything that can tell you "have I already handled this message id?".
/// Back it with a table that has a unique index on MessageId and a TTL cleanup
/// job. Redis works too, but a database gives you the transaction in step 5.
/// </summary>
public interface IIdempotencyStore
{
    Task<bool> AlreadyProcessedAsync(string messageId, CancellationToken ct);
    Task MarkProcessedAsync(string messageId, CancellationToken ct);
}

public sealed class OrderEventConsumer : BackgroundService
{
    private const string Topic = "orders.v1";
    private const string DeadLetterTopic = "orders.v1.dlq";
    private const int CommitEveryN = 100;
    private const int MaxInProcessRetries = 3;

    private readonly IConsumer<string, byte[]> _consumer;
    private readonly IProducer<string, byte[]> _dlqProducer;
    private readonly IIdempotencyStore _idempotency;
    private readonly ILogger<OrderEventConsumer> _log;

    private int _sinceLastCommit;

    public OrderEventConsumer(
        string bootstrapServers,
        IIdempotencyStore idempotency,
        ILogger<OrderEventConsumer> log)
    {
        _idempotency = idempotency;
        _log = log;

        var config = new ConsumerConfig
        {
            BootstrapServers = bootstrapServers,

            // Step 1: this name is your bookmark. Treat it as production config,
            // never as something derived from the hostname or a Guid.
            GroupId = "payments-service",

            // Step 2. Non-negotiable for anything that matters.
            EnableAutoCommit = false,

            // Where to start when the group has no committed offset at all.
            // Earliest = replay the topic. Latest = only new traffic. Getting
            // this wrong on first deploy either floods you or silently skips.
            AutoOffsetReset = AutoOffsetReset.Earliest,

            // Step 3: the two timeouts people confuse.
            //   SessionTimeout      — how long the group waits for a heartbeat.
            //   MaxPollInterval     — how long your processing may take between
            //                         Consume calls.
            // Slow handler? Raise MaxPollInterval, not SessionTimeout.
            SessionTimeoutMs = 45_000,
            MaxPollIntervalMs = 300_000,
            HeartbeatIntervalMs = 3_000,

            // Cooperative rebalancing moves only the partitions that need to
            // move, instead of stopping the whole group. Use it. The old
            // eager strategy is a self-inflicted outage on every deploy.
            PartitionAssignmentStrategy = PartitionAssignmentStrategy.CooperativeSticky,

            // Read only what a transaction has committed.
            IsolationLevel = IsolationLevel.ReadCommitted,

            FetchMinBytes = 1,
            FetchWaitMaxMs = 100,
            MaxPartitionFetchBytes = 1024 * 1024,

            SecurityProtocol = SecurityProtocol.SaslSsl,
            SaslMechanism = SaslMechanism.ScramSha512,
            SaslUsername = Environment.GetEnvironmentVariable("KAFKA_USER"),
            SaslPassword = Environment.GetEnvironmentVariable("KAFKA_PASSWORD"),
        };

        _consumer = new ConsumerBuilder<string, byte[]>(config)
            .SetPartitionsAssignedHandler((_, parts) =>
                _log.LogInformation("Assigned: {Partitions}", string.Join(",", parts)))
            .SetPartitionsRevokedHandler((c, parts) =>
            {
                // Last chance to commit before the partitions move away.
                _log.LogInformation("Revoked: {Partitions}", string.Join(",", parts));
                SafeCommit(c);
            })
            .SetErrorHandler((_, e) => _log.LogWarning("Consumer error: {Reason}", e.Reason))
            .Build();

        _dlqProducer = new ProducerBuilder<string, byte[]>(
            new ProducerConfig { BootstrapServers = bootstrapServers, Acks = Acks.All })
            .Build();
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        _consumer.Subscribe(Topic);
        _log.LogInformation("Subscribed to {Topic}", Topic);

        try
        {
            // Step 3: the poll loop.
            while (!stoppingToken.IsCancellationRequested)
            {
                ConsumeResult<string, byte[]>? result;
                try
                {
                    result = _consumer.Consume(TimeSpan.FromMilliseconds(500));
                }
                catch (ConsumeException ex)
                {
                    _log.LogError(ex, "Consume failed: {Reason}", ex.Error.Reason);
                    continue;
                }

                if (result is null || result.IsPartitionEOF) continue;

                await HandleOneAsync(result, stoppingToken);
            }
        }
        catch (OperationCanceledException)
        {
            // Normal shutdown.
        }
        finally
        {
            // Step 8: Close, not just Dispose. Close leaves the group cleanly so
            // the rebalance happens in milliseconds instead of after a timeout.
            SafeCommit(_consumer);
            _consumer.Close();
            _dlqProducer.Flush(TimeSpan.FromSeconds(10));
            _log.LogInformation("Consumer closed cleanly");
        }
    }

    private async Task HandleOneAsync(
        ConsumeResult<string, byte[]> result, CancellationToken ct)
    {
        var messageId = GetHeader(result, "message-id") ?? $"{result.TopicPartitionOffset}";

        // Step 4: dedupe BEFORE doing anything expensive.
        if (await _idempotency.AlreadyProcessedAsync(messageId, ct))
        {
            _log.LogDebug("Duplicate {MessageId} — skipping", messageId);
            MaybeCommit(result);
            return;
        }

        // Step 6: bounded in-process retry.
        for (var attempt = 1; attempt <= MaxInProcessRetries; attempt++)
        {
            try
            {
                var order = JsonSerializer.Deserialize<OrderPlaced>(result.Message.Value)
                            ?? throw new InvalidOperationException("Body deserialised to null");

                // Step 5: work + mark, ideally in one database transaction.
                await ProcessAsync(order, ct);
                await _idempotency.MarkProcessedAsync(messageId, ct);

                MaybeCommit(result);
                return;
            }
            catch (JsonException ex)
            {
                // A message that cannot be parsed will never parse. Retrying is
                // pure waste — go straight to the dead-letter topic.
                _log.LogError(ex, "Unparseable message at {Offset} — dead-lettering",
                    result.TopicPartitionOffset);
                await DeadLetterAsync(result, "deserialization-failed", ex, ct);
                MaybeCommit(result);
                return;
            }
            catch (Exception ex) when (attempt < MaxInProcessRetries)
            {
                // Exponential backoff: 200ms, 400ms, 800ms. Keep the total well
                // under MaxPollIntervalMs or the group will evict you mid-retry.
                var delay = TimeSpan.FromMilliseconds(200 * Math.Pow(2, attempt - 1));
                _log.LogWarning(ex, "Attempt {Attempt} failed for {MessageId}, retrying in {Delay}",
                    attempt, messageId, delay);
                await Task.Delay(delay, ct);
            }
            catch (Exception ex)
            {
                _log.LogError(ex, "All {Max} attempts failed for {MessageId} — dead-lettering",
                    MaxInProcessRetries, messageId);
                await DeadLetterAsync(result, "max-retries-exceeded", ex, ct);
                MaybeCommit(result);
                return;
            }
        }
    }

    /// <summary>
    /// Kafka has no built-in dead-letter queue. You build one: a normal topic,
    /// plus the original headers, plus why it failed. Without the reason header
    /// the DLQ is unusable — you will be guessing at 3am.
    /// </summary>
    private async Task DeadLetterAsync(
        ConsumeResult<string, byte[]> original, string reason, Exception ex, CancellationToken ct)
    {
        var headers = new Headers();
        foreach (var h in original.Message.Headers) headers.Add(h);

        headers.Add("dlq-reason", Encoding.UTF8.GetBytes(reason));
        headers.Add("dlq-exception", Encoding.UTF8.GetBytes(ex.GetType().FullName ?? "unknown"));
        headers.Add("dlq-message", Encoding.UTF8.GetBytes(Truncate(ex.Message, 900)));
        headers.Add("dlq-origin", Encoding.UTF8.GetBytes(original.TopicPartitionOffset.ToString()));
        headers.Add("dlq-at", Encoding.UTF8.GetBytes(DateTimeOffset.UtcNow.ToString("O")));

        await _dlqProducer.ProduceAsync(DeadLetterTopic, new Message<string, byte[]>
        {
            Key = original.Message.Key,     // keep the key so replay keeps ordering
            Value = original.Message.Value, // the ORIGINAL bytes, never a re-serialised copy
            Headers = headers,
        }, ct);
    }

    /// <summary>Step 7: batch the commits.</summary>
    private void MaybeCommit(ConsumeResult<string, byte[]> result)
    {
        if (++_sinceLastCommit < CommitEveryN) return;

        try
        {
            // Commit "the next offset I want" = processed + 1.
            _consumer.Commit(new[] { new TopicPartitionOffset(
                result.TopicPartition, result.Offset + 1) });
            _sinceLastCommit = 0;
        }
        catch (KafkaException ex)
        {
            // A failed commit is not fatal — the next one covers it. It DOES
            // mean a restart right now would reprocess, which step 4 handles.
            _log.LogWarning(ex, "Commit failed: {Reason}", ex.Error.Reason);
        }
    }

    private void SafeCommit(IConsumer<string, byte[]> c)
    {
        try { c.Commit(); }
        catch (KafkaException ex) { _log.LogWarning("Final commit failed: {Reason}", ex.Error.Reason); }
    }

    private static string? GetHeader(ConsumeResult<string, byte[]> r, string key) =>
        r.Message.Headers.TryGetLastBytes(key, out var bytes)
            ? Encoding.UTF8.GetString(bytes)
            : null;

    private static string Truncate(string s, int max) =>
        s.Length <= max ? s : s[..max];

    private static Task ProcessAsync(OrderPlaced order, CancellationToken ct)
    {
        // Your business logic. Keep it fast, or move the slow part to its own
        // topic — a handler that takes 30 seconds will wreck the whole partition.
        return Task.CompletedTask;
    }

    public override void Dispose()
    {
        _consumer.Dispose();
        _dlqProducer.Dispose();
        base.Dispose();
    }
}
