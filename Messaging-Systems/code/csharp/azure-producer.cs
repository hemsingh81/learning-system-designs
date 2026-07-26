// =============================================================================
// azure-producer.cs — sending to Azure Service Bus
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Create ONE ServiceBusClient per process and keep it. It owns the AMQP
//     connection [a long-lived socket that multiplexes many senders]. Creating
//     one per request opens a new connection every time and will exhaust ports.
//  2. Authenticate with a managed identity, not a connection string. A
//     connection string is a password with no expiry sitting in your config.
//  3. Set MessageId on every message. Service Bus can then reject a repeat for
//     you — turn on duplicate detection on the queue and the broker discards a
//     resend of the same MessageId within the detection window.
//  4. Set SessionId when order matters. Everything sharing a SessionId is
//     delivered to one consumer, one at a time, in order.
//  5. Put routing facts in ApplicationProperties, not only in the body.
//     Subscription filters read these WITHOUT deserialising your payload, so a
//     filter on a property is cheap and a filter on the body is impossible.
//  6. Batch when sending many. CreateMessageBatchAsync tells you when the batch
//     is full — respect that answer instead of guessing at message sizes.
//  7. Use ServiceBusMessageBatch's TryAddMessage return value. If it returns
//     false on an EMPTY batch, that single message is over the size limit and
//     will never send — handle it, do not loop forever.
//  8. Schedule instead of sleeping. ScheduleMessageAsync hands the broker a
//     future delivery time. No timer service, no Hangfire, no cron.
//
// Run: dotnet run --project . -- asb-send
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Azure.Messaging.ServiceBus;
using Azure.Messaging.ServiceBus.Administration;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.AzureServiceBus;

public sealed record OrderPlaced(
    string OrderId,
    string CustomerId,
    string Region,
    decimal Total,
    string Currency,
    DateTimeOffset PlacedAtUtc);

public sealed class OrderEventSender : IAsyncDisposable
{
    private const string TopicName = "order-events";
    private const string CommandQueue = "payment-commands";

    private readonly ServiceBusClient _client;
    private readonly ServiceBusSender _topicSender;
    private readonly ServiceBusSender _queueSender;
    private readonly ILogger<OrderEventSender> _log;

    public OrderEventSender(string fullyQualifiedNamespace, ILogger<OrderEventSender> log)
    {
        _log = log;

        var options = new ServiceBusClientOptions
        {
            // AMQP over 5671 is the fast path. Fall back to WebSockets (443)
            // only when a firewall forces it — it costs latency.
            TransportType = ServiceBusTransportType.AmqpTcp,

            RetryOptions = new ServiceBusRetryOptions
            {
                Mode = ServiceBusRetryMode.Exponential,
                MaxRetries = 5,
                Delay = TimeSpan.FromMilliseconds(200),
                MaxDelay = TimeSpan.FromSeconds(30),
                TryTimeout = TimeSpan.FromSeconds(30),
            },
        };

        // Step 1 + 2: one client, managed identity, no secrets in config.
        _client = new ServiceBusClient(
            fullyQualifiedNamespace,            // "my-namespace.servicebus.windows.net"
            new DefaultAzureCredential(),
            options);

        // Senders are cheap and thread-safe. Create per destination, keep them.
        _topicSender = _client.CreateSender(TopicName);
        _queueSender = _client.CreateSender(CommandQueue);
    }

    /// <summary>Steps 3-5: a single well-formed message.</summary>
    public async Task PublishAsync(OrderPlaced order, CancellationToken ct = default)
    {
        var message = new ServiceBusMessage(JsonSerializer.SerializeToUtf8Bytes(order))
        {
            // Step 3. Deterministic, NOT Guid.NewGuid() — a retry of the same
            // logical send must produce the same MessageId or duplicate
            // detection cannot help you.
            MessageId = $"{order.OrderId}:OrderPlaced",

            // Step 4. One order is handled by one worker, in order.
            SessionId = order.OrderId,

            // Subject is the cheap "what is this" field. Filters can match it
            // with sys.Label = 'OrderPlaced', which is the fastest filter kind.
            Subject = nameof(OrderPlaced),

            ContentType = "application/json",
            CorrelationId = order.OrderId,

            // Per-message TTL. A payment authorisation that is 30 minutes old
            // is worse than useless — let the broker bin it automatically.
            TimeToLive = TimeSpan.FromHours(24),
        };

        // Step 5: routing facts as properties. Filters read these for free.
        message.ApplicationProperties["region"] = order.Region;
        message.ApplicationProperties["currency"] = order.Currency;
        message.ApplicationProperties["schema-version"] = 1;
        message.ApplicationProperties["high-value"] = order.Total > 1000m;

        await _topicSender.SendMessageAsync(message, ct);

        _log.LogInformation("Sent {MessageId} to {Topic}", message.MessageId, TopicName);
    }

    /// <summary>
    /// Steps 6-7: batching. This is the difference between 200 msg/sec and
    /// 20,000 msg/sec, and it is three extra lines.
    /// </summary>
    public async Task PublishManyAsync(
        IReadOnlyList<OrderPlaced> orders, CancellationToken ct = default)
    {
        var queued = 0;
        var batch = await _topicSender.CreateMessageBatchAsync(ct);

        foreach (var order in orders)
        {
            var message = BuildMessage(order);

            // Step 7: the broker knows the real limit including headers and
            // AMQP framing. Never compute it yourself.
            if (batch.TryAddMessage(message)) continue;

            if (batch.Count == 0)
            {
                // One message alone does not fit — it will NEVER fit. Sending
                // this batch would loop forever.
                _log.LogError(
                    "Message {MessageId} exceeds the max size on its own. Dropping to DLQ path.",
                    message.MessageId);
                continue;
            }

            // Batch full: flush and start a fresh one.
            await _topicSender.SendMessagesAsync(batch, ct);
            queued += batch.Count;
            batch.Dispose();

            batch = await _topicSender.CreateMessageBatchAsync(ct);
            if (!batch.TryAddMessage(message))
                _log.LogError("Message {MessageId} rejected by an empty batch", message.MessageId);
        }

        if (batch.Count > 0)
        {
            await _topicSender.SendMessagesAsync(batch, ct);
            queued += batch.Count;
        }
        batch.Dispose();

        _log.LogInformation("Sent {Count} of {Total} messages", queued, orders.Count);
    }

    /// <summary>
    /// Step 8: broker-side scheduling. Returns a sequence number you can use to
    /// cancel the delivery later — store it if the schedule is cancellable.
    /// </summary>
    public async Task<long> ScheduleRetryAsync(
        OrderPlaced order, TimeSpan delay, int attempt, CancellationToken ct = default)
    {
        var message = BuildMessage(order);
        message.MessageId = $"{order.OrderId}:retry:{attempt}";  // still deterministic
        message.ApplicationProperties["retry-attempt"] = attempt;

        var sequenceNumber = await _queueSender.ScheduleMessageAsync(
            message, DateTimeOffset.UtcNow.Add(delay), ct);

        _log.LogInformation(
            "Scheduled retry {Attempt} for {OrderId} in {Delay} (seq {Seq})",
            attempt, order.OrderId, delay, sequenceNumber);

        return sequenceNumber;
    }

    /// <summary>
    /// A local transaction: several sends that all land or none do. Works
    /// across entities in one namespace when you set a via-sender. It does NOT
    /// extend to your database — that still needs an outbox.
    /// </summary>
    public async Task SendAtomicallyAsync(
        OrderPlaced order, CancellationToken ct = default)
    {
        using var scope = new System.Transactions.TransactionScope(
            System.Transactions.TransactionScopeAsyncFlowOption.Enabled);

        await _topicSender.SendMessageAsync(BuildMessage(order), ct);
        await _queueSender.SendMessageAsync(BuildMessage(order), ct);

        scope.Complete();   // both, or neither
    }

    private static ServiceBusMessage BuildMessage(OrderPlaced order)
    {
        var m = new ServiceBusMessage(JsonSerializer.SerializeToUtf8Bytes(order))
        {
            MessageId = $"{order.OrderId}:OrderPlaced",
            SessionId = order.OrderId,
            Subject = nameof(OrderPlaced),
            ContentType = "application/json",
            CorrelationId = order.OrderId,
        };
        m.ApplicationProperties["region"] = order.Region;
        m.ApplicationProperties["currency"] = order.Currency;
        m.ApplicationProperties["schema-version"] = 1;
        return m;
    }

    public async ValueTask DisposeAsync()
    {
        await _topicSender.DisposeAsync();
        await _queueSender.DisposeAsync();
        await _client.DisposeAsync();
    }
}

// =============================================================================
// TOPOLOGY AS CODE
//
// ALGORITHM:
//  1. Ask whether the entity exists. Creating an existing entity throws.
//  2. Create it with explicit settings — never rely on portal defaults, they
//     differ between tiers and change over time.
//  3. Create subscriptions, then REMOVE the default $Default rule before
//     adding yours. The default rule is "1=1" and will happily deliver
//     everything alongside your filter if you leave it in place. This is the
//     single most common Service Bus surprise.
//
// Run this at deploy time from a pipeline identity, not at app startup from
// the app identity — your app should not hold Manage rights.
// =============================================================================

public sealed class TopologyProvisioner
{
    private readonly ServiceBusAdministrationClient _admin;
    private readonly ILogger _log;

    public TopologyProvisioner(string fqns, ILogger log)
    {
        _admin = new ServiceBusAdministrationClient(fqns, new DefaultAzureCredential());
        _log = log;
    }

    public async Task EnsureAsync(CancellationToken ct = default)
    {
        const string topic = "order-events";

        // Step 1-2.
        if (!await _admin.TopicExistsAsync(topic, ct))
        {
            await _admin.CreateTopicAsync(new CreateTopicOptions(topic)
            {
                MaxSizeInMegabytes = 5120,
                DefaultMessageTimeToLive = TimeSpan.FromDays(7),
                RequiresDuplicateDetection = true,
                DuplicateDetectionHistoryTimeWindow = TimeSpan.FromMinutes(10),
                EnableBatchedOperations = true,
                SupportOrdering = true,
            }, ct);
            _log.LogInformation("Created topic {Topic}", topic);
        }

        await EnsureSubscriptionAsync(topic, "payments",
            "sys.Label = 'OrderPlaced' AND [high-value] = false", ct);

        await EnsureSubscriptionAsync(topic, "fraud-review",
            "sys.Label = 'OrderPlaced' AND [high-value] = true", ct);

        await EnsureSubscriptionAsync(topic, "inventory-eu",
            "[region] = 'eu'", ct);

        // Audit takes everything — the one case where the default rule is right.
        await EnsureSubscriptionAsync(topic, "audit", null, ct);

        const string queue = "payment-commands";
        if (!await _admin.QueueExistsAsync(queue, ct))
        {
            await _admin.CreateQueueAsync(new CreateQueueOptions(queue)
            {
                RequiresSession = true,                    // ordering per orderId
                MaxDeliveryCount = 5,                      // then straight to DLQ
                LockDuration = TimeSpan.FromMinutes(1),
                DefaultMessageTimeToLive = TimeSpan.FromDays(14),
                DeadLetteringOnMessageExpiration = true,   // expired != silently gone
                RequiresDuplicateDetection = true,
                DuplicateDetectionHistoryTimeWindow = TimeSpan.FromMinutes(10),
                MaxSizeInMegabytes = 5120,
            }, ct);
            _log.LogInformation("Created queue {Queue}", queue);
        }
    }

    private async Task EnsureSubscriptionAsync(
        string topic, string name, string? sqlFilter, CancellationToken ct)
    {
        if (!await _admin.SubscriptionExistsAsync(topic, name, ct))
        {
            await _admin.CreateSubscriptionAsync(new CreateSubscriptionOptions(topic, name)
            {
                MaxDeliveryCount = 5,
                LockDuration = TimeSpan.FromMinutes(1),
                DeadLetteringOnMessageExpiration = true,
                EnableDeadLetteringOnFilterEvaluationExceptions = true,
                DefaultMessageTimeToLive = TimeSpan.FromDays(7),
            }, ct);
        }

        if (sqlFilter is null) return;

        // Step 3: kill the catch-all rule FIRST, then add yours.
        try
        {
            await _admin.DeleteRuleAsync(topic, name, "$Default", ct);
        }
        catch (ServiceBusException ex)
            when (ex.Reason == ServiceBusFailureReason.MessagingEntityNotFound)
        {
            // Already removed on a previous run. Fine.
        }

        var ruleName = "primary";
        if (!await _admin.RuleExistsAsync(topic, name, ruleName, ct))
        {
            await _admin.CreateRuleAsync(topic, name,
                new CreateRuleOptions(ruleName, new SqlRuleFilter(sqlFilter)), ct);
            _log.LogInformation("Subscription {Sub} filter: {Filter}", name, sqlFilter);
        }
    }
}
