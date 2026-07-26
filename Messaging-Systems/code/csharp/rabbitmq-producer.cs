// =============================================================================
// rabbitmq-producer.cs — publishing to RabbitMQ
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. One connection per process. Many channels on it. A connection is a TCP
//     socket and is expensive; a channel [a lightweight session inside the
//     connection] is cheap. The classic mistake is one connection per message.
//  2. A channel is NOT thread-safe. Never share one across threads. Pool them,
//     or keep one per worker.
//  3. Declare the topology before publishing: exchange, queues, bindings.
//     Declaration is idempotent — running it twice is fine — but declaring the
//     SAME name with DIFFERENT settings throws and kills the channel.
//  4. Publish to an EXCHANGE with a routing key, never to a queue directly.
//     The exchange decides the destinations. That indirection is the whole
//     point of RabbitMQ: you rewire consumers without touching publishers.
//  5. Turn on publisher confirms. Without them, BasicPublish is fire-and-forget
//     into a socket buffer — it returns success even when the broker never got
//     it. This is the single biggest source of "we lost messages" with Rabbit.
//  6. Set mandatory=true and handle BasicReturn. A message that matches no
//     queue is silently DROPPED by default. Mandatory turns that silence into
//     a callback you can log and alert on.
//  7. Mark messages persistent (DeliveryMode 2) AND declare the queue durable.
//     You need both. Either one alone loses messages on a broker restart.
//  8. Put the message id in the properties. Consumers need it for idempotency.
//
// Persistent + confirms costs throughput — roughly 4x on small messages. That
// is the price of not losing orders. Pay it on the order path; skip it for
// telemetry you can afford to lose.
//
// Run: dotnet run --project . -- rmq-publish
// =============================================================================

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using RabbitMQ.Client;
using RabbitMQ.Client.Events;
using RabbitMQ.Client.Exceptions;

namespace Messaging.Samples.RabbitMq;

public sealed record OrderPlaced(
    string OrderId,
    string CustomerId,
    string Region,
    decimal Total,
    string Currency,
    DateTimeOffset PlacedAtUtc);

public sealed class OrderEventPublisher : IAsyncDisposable
{
    private const string Exchange = "orders";
    private const string DeadLetterExchange = "orders.dlx";
    private const string RetryQueue = "orders.retry";

    private readonly IConnection _connection;
    private readonly IChannel _channel;
    private readonly ILogger<OrderEventPublisher> _log;
    private readonly SemaphoreSlim _publishLock = new(1, 1);   // step 2

    // Tracks unconfirmed publishes so a BasicReturn can be matched to a message.
    private readonly ConcurrentDictionary<ulong, string> _outstanding = new();

    private OrderEventPublisher(
        IConnection connection, IChannel channel, ILogger<OrderEventPublisher> log)
    {
        _connection = connection;
        _channel = channel;
        _log = log;
    }

    public static async Task<OrderEventPublisher> CreateAsync(
        string hostList, ILogger<OrderEventPublisher> log, CancellationToken ct = default)
    {
        var factory = new ConnectionFactory
        {
            UserName = Environment.GetEnvironmentVariable("RABBIT_USER") ?? "guest",
            Password = Environment.GetEnvironmentVariable("RABBIT_PASSWORD") ?? "guest",
            VirtualHost = "/orders",

            // The client reconnects on its own and re-declares everything it
            // knows about. Leave both on — the alternative is writing your own
            // reconnect loop, badly.
            AutomaticRecoveryEnabled = true,
            TopologyRecoveryEnabled = true,
            NetworkRecoveryInterval = TimeSpan.FromSeconds(5),

            // Heartbeats detect a half-open connection [one side thinks it is
            // alive, the other has gone]. Without them a dead connection can
            // sit there for hours looking healthy.
            RequestedHeartbeat = TimeSpan.FromSeconds(30),

            ClientProvidedName = $"order-api-{Environment.MachineName}",
        };

        // Step 1: connect to ALL nodes, not one. Naming a single node means a
        // single point of failure you built yourself.
        var endpoints = new List<AmqpTcpEndpoint>();
        foreach (var host in hostList.Split(',', StringSplitOptions.RemoveEmptyEntries))
            endpoints.Add(new AmqpTcpEndpoint(host.Trim(), 5672));

        var connection = await factory.CreateConnectionAsync(endpoints, ct);

        // Step 5: confirms are per channel and must be requested at creation.
        var channel = await connection.CreateChannelAsync(
            new CreateChannelOptions(
                publisherConfirmationsEnabled: true,
                publisherConfirmationTrackingEnabled: true),
            ct);

        var publisher = new OrderEventPublisher(connection, channel, log);

        // Step 6: catch messages that matched no queue.
        channel.BasicReturnAsync += publisher.OnReturnedAsync;

        await publisher.DeclareTopologyAsync(ct);
        return publisher;
    }

    /// <summary>
    /// Step 3. Run this at startup. Idempotent — but the settings must match
    /// what already exists on the broker, or the channel dies with a 406.
    /// </summary>
    private async Task DeclareTopologyAsync(CancellationToken ct)
    {
        await _channel.ExchangeDeclareAsync(Exchange, ExchangeType.Topic,
            durable: true, autoDelete: false, cancellationToken: ct);

        await _channel.ExchangeDeclareAsync(DeadLetterExchange, ExchangeType.Fanout,
            durable: true, autoDelete: false, cancellationToken: ct);

        // Work queues. Quorum queues replicate through Raft and are the right
        // default now — classic mirrored queues are deprecated and had a real
        // split-brain problem.
        var quorumArgs = new Dictionary<string, object?>
        {
            ["x-queue-type"] = "quorum",
            ["x-dead-letter-exchange"] = DeadLetterExchange,

            // Cap the redelivery count so a poison message parks itself instead
            // of looping forever. Quorum queues count redeliveries; classic
            // queues do not, which is another reason to prefer quorum.
            ["x-delivery-limit"] = 5,

            // Bound the queue. An unbounded queue turns a slow consumer into a
            // broker outage — memory fills, the whole node blocks publishers.
            ["x-max-length"] = 1_000_000,
            ["x-overflow"] = "reject-publish",   // fail the publish, do not drop silently
        };

        foreach (var (queue, bindingKey) in new[]
        {
            ("payment.work",   "order.*.placed"),
            ("inventory.work", "order.eu.*"),
            ("audit.all",      "#"),
        })
        {
            await _channel.QueueDeclareAsync(queue, durable: true, exclusive: false,
                autoDelete: false, arguments: quorumArgs, cancellationToken: ct);

            await _channel.QueueBindAsync(queue, Exchange, bindingKey, cancellationToken: ct);
        }

        // Where dead letters land. Nothing leaves here on its own.
        await _channel.QueueDeclareAsync("orders.parked", durable: true, exclusive: false,
            autoDelete: false,
            arguments: new Dictionary<string, object?> { ["x-queue-type"] = "quorum" },
            cancellationToken: ct);
        await _channel.QueueBindAsync("orders.parked", DeadLetterExchange, "",
            cancellationToken: ct);

        // THE DELAY TRICK. RabbitMQ has no native delayed delivery in core.
        // A queue with a TTL and NO consumer, whose dead-letter target is the
        // original exchange, gives you "retry in 30 seconds" for free.
        await _channel.QueueDeclareAsync(RetryQueue, durable: true, exclusive: false,
            autoDelete: false,
            arguments: new Dictionary<string, object?>
            {
                ["x-queue-type"] = "quorum",
                ["x-message-ttl"] = 30_000,               // 30 seconds
                ["x-dead-letter-exchange"] = Exchange,     // then back into the flow
            },
            cancellationToken: ct);

        _log.LogInformation("Topology declared on exchange {Exchange}", Exchange);
    }

    /// <summary>Steps 4-8: publish one message and wait for the broker to confirm.</summary>
    public async Task PublishAsync(OrderPlaced order, CancellationToken ct = default)
    {
        var messageId = $"{order.OrderId}:OrderPlaced";

        // Step 4: routing key encodes what happened, in a shape bindings can
        // pattern-match. "order.eu.placed" is matched by "order.*.placed",
        // "order.eu.*" and "#".
        var routingKey = $"order.{order.Region}.placed";

        var properties = new BasicProperties
        {
            // Step 7: persistent. Pointless without a durable queue, and vice versa.
            Persistent = true,

            // Step 8: identity for the consumer's idempotency check.
            MessageId = messageId,
            CorrelationId = order.OrderId,
            Type = nameof(OrderPlaced),
            ContentType = "application/json",
            ContentEncoding = "utf-8",
            Timestamp = new AmqpTimestamp(DateTimeOffset.UtcNow.ToUnixTimeSeconds()),
            AppId = "order-api",

            Headers = new Dictionary<string, object?>
            {
                ["schema-version"] = 1,
                ["region"] = order.Region,
                ["x-retry-count"] = 0,
            },
        };

        var body = JsonSerializer.SerializeToUtf8Bytes(order);

        // Step 2: one publish at a time on this channel.
        await _publishLock.WaitAsync(ct);
        try
        {
            var seq = await _channel.GetNextPublishSequenceNumberAsync(ct);
            _outstanding[seq] = messageId;

            // Steps 5-6 together: mandatory catches unroutable, and the await
            // does not return until the broker confirms the write.
            await _channel.BasicPublishAsync(
                exchange: Exchange,
                routingKey: routingKey,
                mandatory: true,
                basicProperties: properties,
                body: body,
                cancellationToken: ct);

            _outstanding.TryRemove(seq, out _);

            _log.LogInformation("Published {MessageId} with key {RoutingKey}",
                messageId, routingKey);
        }
        catch (PublishException ex)
        {
            // Nacked by the broker, or returned as unroutable. Either way the
            // message is NOT safely stored. Do not tell the caller it worked.
            _log.LogError(ex, "Publish rejected for {MessageId} (returned={Returned})",
                messageId, ex.IsReturn);
            throw;
        }
        finally
        {
            _publishLock.Release();
        }
    }

    /// <summary>
    /// Step 6. Fires when the exchange had no queue for the routing key. The
    /// usual cause is a typo in a binding, or a queue nobody redeclared after a
    /// cluster rebuild. Treat it as a production defect, not a warning.
    /// </summary>
    private Task OnReturnedAsync(object sender, BasicReturnEventArgs args)
    {
        _log.LogError(
            "UNROUTABLE: exchange={Exchange} key={RoutingKey} reply={Code} {Text} messageId={MessageId}",
            args.Exchange, args.RoutingKey, args.ReplyCode, args.ReplyText,
            args.BasicProperties.MessageId);

        // In production: write it to a local durable store and alert. A returned
        // message that only reaches a log line is a lost message.
        return Task.CompletedTask;
    }

    public async ValueTask DisposeAsync()
    {
        // Closing the channel waits for outstanding confirms.
        await _channel.CloseAsync();
        await _channel.DisposeAsync();
        await _connection.CloseAsync();
        await _connection.DisposeAsync();
        _publishLock.Dispose();
    }
}

// =============================================================================
// THE OUTBOX PATTERN — the only honest way to make a database write and a
// message publish atomic. Applies to all three brokers; shown here once.
//
// ALGORITHM:
//  1. In ONE database transaction, write the business row AND a row in an
//     outbox table. They commit together or not at all. No broker involved yet.
//  2. A separate publisher process polls the outbox for unsent rows, in order.
//  3. It publishes each one and waits for the broker confirm.
//  4. Only after the confirm does it mark the row sent.
//  5. If it crashes between 3 and 4, the row is published twice. That is fine —
//     the consumer's idempotency check absorbs it. At-least-once by design.
//
// Why bother: without this, "save order then publish" can save the order and
// fail to publish, and nobody downstream ever hears about it. That is the
// classic dual-write problem, and no amount of retry logic fixes it.
// =============================================================================

public sealed class OutboxPublisher
{
    private readonly OrderEventPublisher _publisher;
    private readonly IOutboxRepository _outbox;
    private readonly ILogger<OutboxPublisher> _log;

    public OutboxPublisher(
        OrderEventPublisher publisher, IOutboxRepository outbox, ILogger<OutboxPublisher> log)
    {
        _publisher = publisher;
        _outbox = outbox;
        _log = log;
    }

    public async Task PumpAsync(CancellationToken ct)
    {
        while (!ct.IsCancellationRequested)
        {
            // Step 2. Order by sequence — publishing out of order defeats the
            // point of having per-key ordering downstream.
            var batch = await _outbox.FetchUnsentAsync(batchSize: 200, ct);

            if (batch.Count == 0)
            {
                await Task.Delay(TimeSpan.FromMilliseconds(500), ct);
                continue;
            }

            foreach (var row in batch)
            {
                try
                {
                    var order = JsonSerializer.Deserialize<OrderPlaced>(row.Payload)!;

                    await _publisher.PublishAsync(order, ct);   // step 3
                    await _outbox.MarkSentAsync(row.Id, ct);    // step 4
                }
                catch (Exception ex)
                {
                    // Leave the row unsent. The next pass retries it. Stop the
                    // batch here so ordering is preserved.
                    _log.LogError(ex, "Outbox row {Id} failed — will retry", row.Id);
                    break;
                }
            }
        }
    }
}

public sealed record OutboxRow(long Id, string AggregateId, byte[] Payload, DateTimeOffset CreatedAt);

public interface IOutboxRepository
{
    Task<IReadOnlyList<OutboxRow>> FetchUnsentAsync(int batchSize, CancellationToken ct);
    Task MarkSentAsync(long id, CancellationToken ct);
}
