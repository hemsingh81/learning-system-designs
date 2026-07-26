// =============================================================================
// dapr-publisher.cs — publishing through the Dapr sidecar
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Inject DaprClient. It talks to a sidecar on localhost, NOT to a broker.
//     There is no connection string, no SASL config, no AMQP endpoint. The
//     broker is named in a YAML file the sidecar reads — see
//     ../../k8s/dapr-components.yaml
//  2. Publish with three things: the COMPONENT name, the TOPIC name, and the
//     payload. The component name ("pubsub") is the indirection — it is what
//     lets you swap Kafka for RabbitMQ without touching this file.
//  3. Set a partition key in metadata when order matters. This maps to the
//     Kafka partition key and the Service Bus SessionId. Without it you get no
//     ordering on any broker, and ordering is usually the thing you needed.
//  4. Put YOUR OWN deterministic message id inside the payload. Dapr wraps the
//     payload in a CloudEvents envelope with its own random `id`, and that id
//     changes on every republish — so it is useless as an idempotency key.
//  5. Do not assume the sidecar is ready. Your app can start before daprd. The
//     first publishes after startup can fail; retry them.
//  6. Use bulk publish for high-volume paths. One round trip instead of N.
//  7. Use rawPayload only when a NON-Dapr consumer reads the same topic. It
//     removes the CloudEvents envelope — and the distributed tracing that
//     envelope was carrying.
//  8. For a database write plus a publish, use the Dapr outbox (state store
//     config) or your own outbox table. Never a bare dual write.
//
// WHAT THIS FILE CANNOT DO, no matter how you configure it:
//   - reset an offset or replay a Kafka topic
//   - open a Kafka transaction
//   - schedule a Service Bus message for future delivery
//   - set a RabbitMQ priority or choose an exchange type
// If you need any of those, use the native client in this folder instead.
// See ../../docs/dapr.md#4-what-you-give-up-per-broker
//
// Run: dapr run --app-id order-api --resources-path ./components -- dotnet run
// =============================================================================

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Dapr.Client;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.Dapr;

public sealed record OrderPlaced(
    string MessageId,          // step 4: OURS, deterministic. Not the CloudEvent id.
    string OrderId,
    string CustomerId,
    string Region,
    decimal Total,
    string Currency,
    DateTimeOffset PlacedAtUtc);

public sealed class OrderEventPublisher
{
    // Step 2: these are the ONLY two names in this file. Neither names a broker.
    private const string PubSubComponent = "pubsub";
    private const string Topic = "orders";

    private readonly DaprClient _dapr;
    private readonly ILogger<OrderEventPublisher> _log;

    // Step 1: DaprClient is thread-safe and should be a singleton.
    // builder.Services.AddDaprClient();
    public OrderEventPublisher(DaprClient dapr, ILogger<OrderEventPublisher> log)
    {
        _dapr = dapr;
        _log = log;
    }

    /// <summary>Steps 2-4: the normal path.</summary>
    public async Task PublishAsync(OrderPlaced order, CancellationToken ct = default)
    {
        // Step 3: the partition key. This single line is the difference between
        // ordered and unordered delivery, on every broker Dapr supports.
        //   Kafka       -> partition key
        //   Service Bus -> SessionId
        //   RabbitMQ    -> routing behaviour, where the component supports it
        var metadata = new Dictionary<string, string>
        {
            ["partitionKey"] = order.OrderId,

            // Per-message TTL, where the underlying broker supports it.
            // Kafka does NOT — it has topic-level retention only, so this is
            // silently ignored there. Portable code, non-portable behaviour:
            // that is the abstraction leaking, and it leaks quietly.
            ["ttlInSeconds"] = "86400",
        };

        try
        {
            await _dapr.PublishEventAsync(PubSubComponent, Topic, order, metadata, ct);

            _log.LogInformation("Published {MessageId} for order {OrderId}",
                order.MessageId, order.OrderId);
        }
        catch (DaprException ex)
        {
            // Step 5. A DaprException does NOT tell you whether the broker
            // rejected the message or the sidecar was unreachable. That
            // distinction is available in the native clients and is gone here.
            // Treat every failure as "possibly not published" and let the
            // outbox or a retry handle it.
            _log.LogError(ex, "Publish failed for {MessageId} — sidecar or broker unreachable",
                order.MessageId);
            throw;
        }
    }

    /// <summary>
    /// Step 6: bulk publish. One sidecar round trip for many messages.
    /// Worth using above a few hundred messages/sec; the per-message HTTP hop
    /// is small but it is not free.
    /// </summary>
    public async Task PublishManyAsync(
        IReadOnlyList<OrderPlaced> orders, CancellationToken ct = default)
    {
        var response = await _dapr.BulkPublishEventAsync(
            PubSubComponent, Topic, orders, cancellationToken: ct);

        // Partial failure is normal and MUST be handled. Some entries can
        // succeed while others fail — a bulk publish is not atomic.
        if (response.FailedEntries.Count > 0)
        {
            foreach (var failure in response.FailedEntries)
                _log.LogError("Bulk entry failed: {Message}", failure.ErrorMessage);

            throw new InvalidOperationException(
                $"{response.FailedEntries.Count} of {orders.Count} messages failed to publish");
        }

        _log.LogInformation("Bulk published {Count} messages", orders.Count);
    }

    /// <summary>
    /// Step 7: raw payload — no CloudEvents envelope.
    ///
    /// Use this ONLY when a non-Dapr consumer reads the same topic. A native
    /// consumer expecting your JSON will choke on the envelope, and that is the
    /// single most common problem in a mixed Dapr / native estate.
    ///
    /// The cost: you lose the traceid the envelope carried, so distributed
    /// tracing across the publish/subscribe boundary stops working.
    ///
    /// Decide this BEFORE the first message ships. Changing envelope format on
    /// a live topic is a breaking schema change.
    /// </summary>
    public async Task PublishRawAsync(OrderPlaced order, CancellationToken ct = default)
    {
        var metadata = new Dictionary<string, string>
        {
            ["rawPayload"] = "true",
            ["partitionKey"] = order.OrderId,
        };

        await _dapr.PublishEventAsync(PubSubComponent, Topic, order, metadata, ct);
    }

    /// <summary>
    /// Step 8: the transactional outbox, done by Dapr.
    ///
    /// The state store component is configured with:
    ///     outboxPublishPubsub: "pubsub"
    ///     outboxPublishTopic:  "orders"
    ///
    /// With that in place, this state transaction and the resulting publish are
    /// atomic. The message cannot be lost if the process dies after the write,
    /// which is the dual-write problem that no amount of retry logic solves.
    ///
    /// This is the single most valuable thing Dapr offers a team that has not
    /// already built an outbox.
    ///
    /// The catch: your persistence now goes through Dapr's state API. If you
    /// use EF Core with a rich domain model, keep your own outbox table instead
    /// — see rabbitmq-producer.cs in this folder.
    /// </summary>
    public async Task SaveAndPublishAtomicallyAsync(
        OrderPlaced order, CancellationToken ct = default)
    {
        var operations = new List<StateTransactionRequest>
        {
            new(
                key: $"order-{order.OrderId}",
                value: System.Text.Json.JsonSerializer.SerializeToUtf8Bytes(order),
                operationType: StateOperationType.Upsert),
        };

        // Writes state AND publishes to the configured topic, atomically.
        await _dapr.ExecuteStateTransactionAsync("statestore", operations, cancellationToken: ct);

        _log.LogInformation("Order {OrderId} saved and published atomically", order.OrderId);
    }
}

// =============================================================================
// STARTUP — step 5, handled properly.
//
// ALGORITHM:
//  1. Register DaprClient as a singleton.
//  2. Wait for the sidecar to report healthy before serving traffic. Without
//     this, the first requests after a pod start fail with a connection error
//     that looks like a broker outage and is not one.
//  3. Expose readiness only after the sidecar is up.
//  4. On shutdown, let in-flight work finish before the sidecar goes away.
//     Set dapr.io/block-shutdown-duration in the pod annotations to match.
// =============================================================================

public static class DaprStartup
{
    public static async Task WaitForSidecarAsync(
        DaprClient dapr, ILogger log, CancellationToken ct = default)
    {
        // Step 2. Dapr's own health check. Cheap, and it removes a whole class
        // of confusing startup errors.
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(ct);
        timeout.CancelAfter(TimeSpan.FromSeconds(60));

        try
        {
            await dapr.WaitForSidecarAsync(timeout.Token);
            log.LogInformation("Dapr sidecar is ready");
        }
        catch (OperationCanceledException)
        {
            // Fail loudly. A pod that starts without its sidecar will accept
            // traffic and silently fail to publish — the worst possible outcome.
            log.LogCritical("Dapr sidecar did not become ready within 60s");
            throw;
        }
    }
}
