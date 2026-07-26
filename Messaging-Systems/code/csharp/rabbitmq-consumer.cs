// =============================================================================
// rabbitmq-consumer.cs — consuming from RabbitMQ, safely
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Set a prefetch count [how many unacknowledged messages the broker will
//     push to this consumer at once]. The default is unlimited. Unlimited means
//     the first consumer to connect grabs the entire queue into its memory
//     while every other consumer sits idle. This is the number one RabbitMQ
//     production incident, and it is one line to prevent.
//  2. Use manual acknowledgement. With autoAck the broker deletes the message
//     the instant it writes it to the socket — before your code has seen it.
//  3. Check the idempotency key before working. Redelivery happens on every
//     reconnect, so duplicates are normal, not exceptional.
//  4. Do the work, then ack. In that order. Always.
//  5. On failure, choose deliberately:
//       BasicAck                        — done.
//       BasicNack(requeue: false)       — send to the dead-letter exchange.
//       BasicNack(requeue: true)        — put it BACK AT THE HEAD of the queue.
//     That last one is a trap. A message that always fails, requeued to the
//     head, is re-delivered instantly, forever, pinning a core at 100%. Never
//     requeue blindly. Requeue only when you know the fault was transient AND
//     you have a retry ceiling.
//  6. For delayed retry, republish to the retry queue [a queue with a TTL and
//     no consumer that dead-letters back into the main exchange]. Increment a
//     retry-count header each time so you can stop after N.
//  7. Handle the shutdown path: cancel the consumer, let in-flight work finish,
//     then close. Killing the process mid-message means redelivery, which step
//     3 absorbs — but a clean close is faster and quieter.
//  8. Watch for connection recovery. The client reconnects for you, but your
//     consumer tag changes and any un-acked messages are redelivered. Do not
//     hold state across a recovery event.
//
// Run: dotnet run --project . -- rmq-consume
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using RabbitMQ.Client.Exceptions;

namespace Messaging.Samples.RabbitMq;

public interface IIdempotencyStore
{
    Task<bool> AlreadyProcessedAsync(string messageId, CancellationToken ct);
    Task MarkProcessedAsync(string messageId, CancellationToken ct);
}

public sealed class PaymentWorkConsumer : BackgroundService
{
    private const string Queue = "payment.work";
    private const string Exchange = "orders";
    private const string RetryQueue = "orders.retry";
    private const int MaxRetries = 5;

    // Step 1. Tune this: roughly (messages you can process per second) x
    // (round-trip latency in seconds) x 2. For fast handlers 50-200 is normal;
    // for slow handlers 1-10. Start low and raise it while watching latency.
    private const ushort PrefetchCount = 20;

    private readonly string _hostList;
    private readonly IIdempotencyStore _idempotency;
    private readonly ILogger<PaymentWorkConsumer> _log;

    private IConnection? _connection;
    private IChannel? _channel;

    public PaymentWorkConsumer(
        string hostList, IIdempotencyStore idempotency, ILogger<PaymentWorkConsumer> log)
    {
        _hostList = hostList;
        _idempotency = idempotency;
        _log = log;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        var factory = new ConnectionFactory
        {
            UserName = Environment.GetEnvironmentVariable("RABBIT_USER") ?? "guest",
            Password = Environment.GetEnvironmentVariable("RABBIT_PASSWORD") ?? "guest",
            VirtualHost = "/orders",
            AutomaticRecoveryEnabled = true,
            TopologyRecoveryEnabled = true,
            NetworkRecoveryInterval = TimeSpan.FromSeconds(5),
            RequestedHeartbeat = TimeSpan.FromSeconds(30),
            ConsumerDispatchConcurrency = 4,      // parallel handler dispatch
            ClientProvidedName = $"payment-worker-{Environment.MachineName}",
        };

        var endpoints = new List<AmqpTcpEndpoint>();
        foreach (var h in _hostList.Split(',', StringSplitOptions.RemoveEmptyEntries))
            endpoints.Add(new AmqpTcpEndpoint(h.Trim(), 5672));

        _connection = await factory.CreateConnectionAsync(endpoints, stoppingToken);
        _channel = await _connection.CreateChannelAsync(cancellationToken: stoppingToken);

        // Step 8: know when the ground moved under you.
        _connection.ConnectionShutdownAsync += (_, args) =>
        {
            _log.LogWarning("Connection shut down: {Initiator} {ReplyCode} {ReplyText}",
                args.Initiator, args.ReplyCode, args.ReplyText);
            return Task.CompletedTask;
        };
        _connection.RecoverySucceededAsync += (_, _) =>
        {
            _log.LogInformation("Connection recovered — un-acked messages will redeliver");
            return Task.CompletedTask;
        };

        // Step 1, applied. global:false means "per consumer", which is what you
        // want. global:true spreads the limit across the whole channel and is
        // almost never the intent.
        await _channel.BasicQosAsync(
            prefetchSize: 0,
            prefetchCount: PrefetchCount,
            global: false,
            cancellationToken: stoppingToken);

        var consumer = new AsyncEventingBasicConsumer(_channel);
        consumer.ReceivedAsync += OnReceivedAsync;

        // Step 2: autoAck FALSE.
        var consumerTag = await _channel.BasicConsumeAsync(
            queue: Queue,
            autoAck: false,
            consumerTag: $"payment-{Environment.MachineName}-{Guid.NewGuid():N}",
            noLocal: false,
            exclusive: false,
            arguments: null,
            consumer: consumer,
            cancellationToken: stoppingToken);

        _log.LogInformation("Consuming {Queue} with prefetch {Prefetch}", Queue, PrefetchCount);

        try
        {
            await Task.Delay(Timeout.Infinite, stoppingToken);
        }
        catch (OperationCanceledException) { /* shutting down */ }
        finally
        {
            // Step 7: stop the flow first, then close.
            await SafeAsync(() => _channel!.BasicCancelAsync(consumerTag, noWait: false));
            await Task.Delay(TimeSpan.FromSeconds(5));   // let in-flight work land
            await SafeAsync(() => _channel!.CloseAsync());
            await SafeAsync(() => _connection!.CloseAsync());
            _log.LogInformation("Consumer stopped cleanly");
        }
    }

    private async Task OnReceivedAsync(object sender, BasicDeliverEventArgs ea)
    {
        var ct = CancellationToken.None;
        var channel = _channel!;
        var messageId = ea.BasicProperties.MessageId ?? $"delivery-{ea.DeliveryTag}";
        var retryCount = ReadRetryCount(ea.BasicProperties);

        try
        {
            // Step 3.
            if (await _idempotency.AlreadyProcessedAsync(messageId, ct))
            {
                _log.LogDebug("Duplicate {MessageId} (redelivered={Redelivered}) — acking",
                    messageId, ea.Redelivered);
                await channel.BasicAckAsync(ea.DeliveryTag, multiple: false, ct);
                return;
            }

            var order = JsonSerializer.Deserialize<OrderPlaced>(ea.Body.Span)
                        ?? throw new InvalidOperationException("Body deserialised to null");

            // Step 4: work, then mark, then ack.
            await ProcessAsync(order, ct);
            await _idempotency.MarkProcessedAsync(messageId, ct);

            await channel.BasicAckAsync(ea.DeliveryTag, multiple: false, ct);

            _log.LogInformation("Processed {MessageId} for order {OrderId}",
                messageId, order.OrderId);
        }
        catch (JsonException ex)
        {
            // Permanently broken. Straight to the dead-letter exchange.
            _log.LogError(ex, "Unparseable message {MessageId} — dead-lettering", messageId);
            await channel.BasicNackAsync(ea.DeliveryTag, multiple: false, requeue: false, ct);
        }
        catch (Exception ex) when (retryCount < MaxRetries)
        {
            // Step 6: delayed retry via the TTL queue. This is NOT a requeue —
            // we publish a fresh copy into orders.retry and ack the original.
            _log.LogWarning(ex,
                "Attempt {Attempt} failed for {MessageId} — scheduling retry via {RetryQueue}",
                retryCount + 1, messageId, RetryQueue);

            await RepublishForRetryAsync(channel, ea, retryCount + 1, ct);

            // Ack the original only after the retry copy is safely published.
            await channel.BasicAckAsync(ea.DeliveryTag, multiple: false, ct);
        }
        catch (Exception ex)
        {
            // Out of retries. Park it. Note requeue: false — the whole point.
            _log.LogError(ex,
                "Exhausted {MaxRetries} retries for {MessageId} — dead-lettering",
                MaxRetries, messageId);
            await channel.BasicNackAsync(ea.DeliveryTag, multiple: false, requeue: false, ct);
        }
    }

    /// <summary>
    /// Step 6, the mechanism. Publishing to the retry queue by name is one of
    /// the few times you address a queue directly — the default exchange ("")
    /// routes to the queue whose name equals the routing key.
    /// </summary>
    private static async Task RepublishForRetryAsync(
        IChannel channel, BasicDeliverEventArgs ea, int nextRetry, CancellationToken ct)
    {
        var headers = new Dictionary<string, object?>();
        if (ea.BasicProperties.Headers is not null)
            foreach (var kv in ea.BasicProperties.Headers) headers[kv.Key] = kv.Value;

        headers["x-retry-count"] = nextRetry;
        headers["x-original-routing-key"] = ea.RoutingKey;
        headers["x-retried-at"] = DateTimeOffset.UtcNow.ToString("O");

        var props = new BasicProperties
        {
            Persistent = true,
            MessageId = ea.BasicProperties.MessageId,        // keep identity for dedupe
            CorrelationId = ea.BasicProperties.CorrelationId,
            Type = ea.BasicProperties.Type,
            ContentType = ea.BasicProperties.ContentType,
            Headers = headers,
        };

        await channel.BasicPublishAsync(
            exchange: "",              // default exchange
            routingKey: RetryQueue,    // = the queue name
            mandatory: true,
            basicProperties: props,
            body: ea.Body,
            cancellationToken: ct);
    }

    private static int ReadRetryCount(IReadOnlyBasicProperties props)
    {
        if (props.Headers is null) return 0;
        if (!props.Headers.TryGetValue("x-retry-count", out var raw) || raw is null) return 0;

        return raw switch
        {
            int i => i,
            long l => (int)l,
            byte[] b => int.TryParse(Encoding.UTF8.GetString(b), out var p) ? p : 0,
            _ => 0,
        };
    }

    private async Task SafeAsync(Func<Task> action)
    {
        try { await action(); }
        catch (Exception ex) { _log.LogDebug(ex, "Shutdown step failed, continuing"); }
    }

    private static Task ProcessAsync(OrderPlaced order, CancellationToken ct) => Task.CompletedTask;
}

// =============================================================================
// PARKED-QUEUE TRIAGE — draining orders.parked
//
// ALGORITHM:
//  1. Pull messages one at a time with BasicGet. Do NOT open a streaming
//     consumer on a dead-letter queue: you want to look before you act.
//  2. Read the x-death header. RabbitMQ writes a full audit trail there — the
//     original queue, the reason, the count, and when. That header is the whole
//     reason the dead-letter exchange is worth wiring up.
//  3. Group by reason. Fix the cause, then replay the group.
//  4. Replay by publishing back to the ORIGINAL exchange with the ORIGINAL
//     routing key, both of which are in x-death.
//  5. Ack the parked copy only after the replay is confirmed.
// =============================================================================

public sealed class ParkedQueueTriage
{
    private const string ParkedQueue = "orders.parked";

    private readonly IChannel _channel;
    private readonly ILogger _log;

    public ParkedQueueTriage(IChannel channel, ILogger log)
    {
        _channel = channel;
        _log = log;
    }

    public async Task<int> ReplayAsync(int max = 100, CancellationToken ct = default)
    {
        var replayed = 0;

        for (var i = 0; i < max; i++)
        {
            // Step 1.
            var result = await _channel.BasicGetAsync(ParkedQueue, autoAck: false, ct);
            if (result is null) break;

            // Step 2.
            var death = ReadFirstDeath(result.BasicProperties);

            _log.LogInformation(
                "Parked {MessageId}: queue={Queue} reason={Reason} count={Count} key={Key}",
                result.BasicProperties.MessageId,
                death.Queue, death.Reason, death.Count, death.RoutingKey);

            // Step 3.
            if (death.Reason is not ("rejected" or "delivery_limit"))
            {
                await _channel.BasicNackAsync(result.DeliveryTag, false, requeue: true, ct);
                continue;
            }

            // Step 4: original exchange, original routing key, reset counters.
            var headers = new Dictionary<string, object?>();
            if (result.BasicProperties.Headers is not null)
                foreach (var kv in result.BasicProperties.Headers)
                    if (kv.Key != "x-death") headers[kv.Key] = kv.Value;

            headers["x-retry-count"] = 0;
            headers["x-replayed-at"] = DateTimeOffset.UtcNow.ToString("O");
            headers["x-replay-of"] = death.Reason;

            var props = new BasicProperties
            {
                Persistent = true,
                MessageId = result.BasicProperties.MessageId,
                CorrelationId = result.BasicProperties.CorrelationId,
                Type = result.BasicProperties.Type,
                ContentType = result.BasicProperties.ContentType,
                Headers = headers,
            };

            try
            {
                await _channel.BasicPublishAsync(
                    exchange: death.Exchange,
                    routingKey: death.RoutingKey,
                    mandatory: true,
                    basicProperties: props,
                    body: result.Body,
                    cancellationToken: ct);

                // Step 5.
                await _channel.BasicAckAsync(result.DeliveryTag, multiple: false, ct);
                replayed++;
            }
            catch (PublishException ex)
            {
                _log.LogError(ex, "Replay failed — leaving message parked");
                await _channel.BasicNackAsync(result.DeliveryTag, false, requeue: true, ct);
            }
        }

        _log.LogInformation("Replayed {Count} parked messages", replayed);
        return replayed;
    }

    private sealed record Death(string Queue, string Reason, long Count, string Exchange, string RoutingKey);

    /// <summary>
    /// x-death is an array of maps. The FIRST entry is the most recent death.
    /// Values arrive as byte[] for strings — a detail that trips up everyone
    /// reading this header for the first time.
    /// </summary>
    private static Death ReadFirstDeath(IReadOnlyBasicProperties props)
    {
        if (props.Headers is null ||
            !props.Headers.TryGetValue("x-death", out var raw) ||
            raw is not List<object> entries ||
            entries.Count == 0 ||
            entries[0] is not Dictionary<string, object> first)
        {
            return new Death("unknown", "unknown", 0, "orders", "#");
        }

        return new Death(
            Queue: Str(first, "queue") ?? "unknown",
            Reason: Str(first, "reason") ?? "unknown",
            Count: first.TryGetValue("count", out var c) && c is long l ? l : 0,
            Exchange: Str(first, "exchange") ?? "orders",
            RoutingKey: first.TryGetValue("routing-keys", out var rk)
                        && rk is List<object> { Count: > 0 } keys
                        && keys[0] is byte[] kb
                            ? Encoding.UTF8.GetString(kb)
                            : "#");
    }

    private static string? Str(Dictionary<string, object> map, string key) =>
        map.TryGetValue(key, out var v) && v is byte[] b ? Encoding.UTF8.GetString(b) : v as string;
}
