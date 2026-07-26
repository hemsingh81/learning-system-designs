// =============================================================================
// azure-consumer.cs — receiving from Azure Service Bus, safely
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. Receive in PeekLock mode [the broker hands you the message but keeps a
//     copy, locked, invisible to everyone else]. The other mode,
//     ReceiveAndDelete, deletes on delivery — if your process dies one
//     millisecond later, the message is gone with no trace. Use PeekLock unless
//     losing the message genuinely does not matter.
//  2. The lock has a deadline, default 60 seconds. If you have not completed,
//     abandoned or dead-lettered the message by then, the broker assumes you
//     died and gives it to someone else. Two workers doing the same job is
//     the result.
//  3. Work that may run longer than the lock must renew the lock while it runs.
//     The ServiceBusProcessor does this for you when
//     MaxAutoLockRenewalDuration is set. Set it to your realistic worst case,
//     not your average.
//  4. Check the idempotency key before doing anything. At-least-once delivery
//     means you WILL see repeats, lock expiry being the most common cause.
//  5. Then decide the outcome, explicitly, on every path:
//       CompleteAsync    — done, delete it.
//       AbandonAsync     — release the lock, retry now, DeliveryCount goes up.
//       DeadLetterAsync  — it will never work, park it with a reason.
//       DeferAsync       — I cannot handle it YET, hide it but keep the
//                          sequence number so I can fetch it by hand later.
//  6. Let MaxDeliveryCount do the retry counting. When it is exceeded the
//     broker dead-letters automatically. Do not build a second retry counter
//     in your own code on top of it.
//  7. For ordered work use a session processor. It gives one worker exclusive
//     rights to one SessionId, and lets you keep per-session state.
//  8. Run a DLQ drain job on a schedule. A dead-letter queue nobody reads is a
//     slow-motion data-loss machine.
//
// Run: dotnet run --project . -- asb-receive
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Azure.Identity;
using Azure.Messaging.ServiceBus;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.AzureServiceBus;

public interface IIdempotencyStore
{
    Task<bool> AlreadyProcessedAsync(string messageId, CancellationToken ct);
    Task MarkProcessedAsync(string messageId, CancellationToken ct);
}

// -----------------------------------------------------------------------------
// STANDARD PROCESSOR — competing consumers, no ordering guarantee
// -----------------------------------------------------------------------------
public sealed class PaymentCommandProcessor : BackgroundService
{
    private const string QueueName = "payment-commands";

    private readonly ServiceBusClient _client;
    private readonly ServiceBusProcessor _processor;
    private readonly IIdempotencyStore _idempotency;
    private readonly ILogger<PaymentCommandProcessor> _log;

    public PaymentCommandProcessor(
        string fullyQualifiedNamespace,
        IIdempotencyStore idempotency,
        ILogger<PaymentCommandProcessor> log)
    {
        _idempotency = idempotency;
        _log = log;

        _client = new ServiceBusClient(fullyQualifiedNamespace, new DefaultAzureCredential());

        _processor = _client.CreateProcessor(QueueName, new ServiceBusProcessorOptions
        {
            // Step 1. The default, and the right choice.
            ReceiveMode = ServiceBusReceiveMode.PeekLock,

            // How many messages this instance handles at once. Start LOW.
            // High concurrency plus a slow downstream dependency equals a pile
            // of expired locks and a flood of duplicates.
            MaxConcurrentCalls = 16,

            // Step 3. The SDK renews the lock in the background up to this
            // ceiling. Beyond it, the lock expires and the message redelivers.
            MaxAutoLockRenewalDuration = TimeSpan.FromMinutes(10),

            // We settle every message ourselves. With this true, the SDK
            // completes on return and abandons on throw — which silently hides
            // the DeadLetter decision from you.
            AutoCompleteMessages = false,

            // Prefetch trades latency for throughput. Prefetched messages hold
            // their lock from the moment they arrive in your buffer, so a big
            // prefetch with slow processing expires locks. Zero is safe.
            PrefetchCount = 0,
        });

        _processor.ProcessMessageAsync += OnMessageAsync;
        _processor.ProcessErrorAsync += OnErrorAsync;
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await _processor.StartProcessingAsync(stoppingToken);
        _log.LogInformation("Processing {Queue}", QueueName);

        try
        {
            await Task.Delay(Timeout.Infinite, stoppingToken);
        }
        catch (OperationCanceledException) { /* shutting down */ }
        finally
        {
            // Stop draining gracefully — in-flight messages finish first.
            await _processor.StopProcessingAsync(CancellationToken.None);
            _log.LogInformation("Processor stopped cleanly");
        }
    }

    private async Task OnMessageAsync(ProcessMessageEventArgs args)
    {
        var message = args.Message;
        var messageId = message.MessageId;
        var ct = args.CancellationToken;

        try
        {
            // Step 4: dedupe first, always.
            if (await _idempotency.AlreadyProcessedAsync(messageId, ct))
            {
                _log.LogDebug("Duplicate {MessageId} (delivery {Count}) — completing",
                    messageId, message.DeliveryCount);
                await args.CompleteMessageAsync(message, ct);
                return;
            }

            var order = message.Body.ToObjectFromJson<OrderPlaced>()
                        ?? throw new InvalidOperationException("Empty body");

            await ProcessAsync(order, ct);
            await _idempotency.MarkProcessedAsync(messageId, ct);

            // Step 5: done means gone.
            await args.CompleteMessageAsync(message, ct);

            _log.LogInformation("Completed {MessageId} for order {OrderId}",
                messageId, order.OrderId);
        }
        catch (JsonException ex)
        {
            // A malformed body never becomes well-formed. Straight to the DLQ —
            // retrying it 5 times is 5 wasted deliveries and 5 log lines of noise.
            _log.LogError(ex, "Unparseable body on {MessageId}", messageId);
            await args.DeadLetterMessageAsync(message,
                deadLetterReason: "DeserializationFailed",
                deadLetterErrorDescription: Truncate(ex.Message, 4000),
                cancellationToken: ct);
        }
        catch (PaymentDeclinedException ex)
        {
            // A business rejection is not a transient fault. Retrying a declined
            // card 5 times does nothing except annoy the payment provider.
            _log.LogWarning("Payment declined for {MessageId}: {Reason}", messageId, ex.Reason);
            await args.DeadLetterMessageAsync(message,
                deadLetterReason: "PaymentDeclined",
                deadLetterErrorDescription: ex.Reason,
                cancellationToken: ct);
        }
        catch (Exception ex)
        {
            // Step 6: transient. Abandon and let MaxDeliveryCount do the counting.
            // On the 5th abandon the broker dead-letters it for us.
            _log.LogWarning(ex, "Transient failure on {MessageId}, delivery {Count} of 5",
                messageId, message.DeliveryCount);
            await args.AbandonMessageAsync(message, cancellationToken: ct);
        }
    }

    private Task OnErrorAsync(ProcessErrorEventArgs args)
    {
        // This fires for connection-level problems, not handler exceptions.
        // ServiceBusFailureReason tells you whether it is worth alerting on.
        var level = args.Exception is ServiceBusException { IsTransient: true }
            ? LogLevel.Warning
            : LogLevel.Error;

        _log.Log(level, args.Exception,
            "Service Bus error in {Source} on {Entity}",
            args.ErrorSource, args.EntityPath);

        return Task.CompletedTask;
    }

    private static Task ProcessAsync(OrderPlaced order, CancellationToken ct) => Task.CompletedTask;
    private static string Truncate(string s, int max) => s.Length <= max ? s : s[..max];

    public override void Dispose()
    {
        _processor.DisposeAsync().AsTask().GetAwaiter().GetResult();
        _client.DisposeAsync().AsTask().GetAwaiter().GetResult();
        base.Dispose();
    }
}

public sealed class PaymentDeclinedException(string reason) : Exception(reason)
{
    public string Reason { get; } = reason;
}

// -----------------------------------------------------------------------------
// SESSION PROCESSOR — step 7. Ordering per key, plus per-key state.
//
// ALGORITHM:
//  1. The broker locks a whole SESSION to one worker, not one message.
//  2. That worker receives every message in the session, in order, one at a
//     time. Nobody else can touch the session until the lock is released.
//  3. Session state is a small blob the broker stores for you, keyed by
//     SessionId. Use it for saga progress so a restart resumes instead of
//     starting over.
//  4. MaxConcurrentSessions decides how many DIFFERENT orders you handle at
//     once. MaxConcurrentCallsPerSession should stay 1 — raising it destroys
//     the ordering you turned sessions on for.
// -----------------------------------------------------------------------------
public sealed class OrderSagaProcessor : BackgroundService
{
    private const string QueueName = "payment-commands";

    private readonly ServiceBusClient _client;
    private readonly ServiceBusSessionProcessor _processor;
    private readonly ILogger<OrderSagaProcessor> _log;

    public OrderSagaProcessor(string fqns, ILogger<OrderSagaProcessor> log)
    {
        _log = log;
        _client = new ServiceBusClient(fqns, new DefaultAzureCredential());

        _processor = _client.CreateSessionProcessor(QueueName, new ServiceBusSessionProcessorOptions
        {
            MaxConcurrentSessions = 32,          // 32 orders in flight
            MaxConcurrentCallsPerSession = 1,    // keep this at 1. Always.
            AutoCompleteMessages = false,
            MaxAutoLockRenewalDuration = TimeSpan.FromMinutes(10),
            SessionIdleTimeout = TimeSpan.FromSeconds(30),
        });

        _processor.ProcessMessageAsync += OnSessionMessageAsync;
        _processor.ProcessErrorAsync += args =>
        {
            _log.LogError(args.Exception, "Session processor error");
            return Task.CompletedTask;
        };
    }

    protected override async Task ExecuteAsync(CancellationToken stoppingToken)
    {
        await _processor.StartProcessingAsync(stoppingToken);
        try { await Task.Delay(Timeout.Infinite, stoppingToken); }
        catch (OperationCanceledException) { }
        finally { await _processor.StopProcessingAsync(CancellationToken.None); }
    }

    private async Task OnSessionMessageAsync(ProcessSessionMessageEventArgs args)
    {
        var ct = args.CancellationToken;

        // Step 3: read where this saga got to last time.
        var stateBytes = await args.GetSessionStateAsync(ct);
        var state = stateBytes is null
            ? new SagaState(args.SessionId, "Started", 0)
            : JsonSerializer.Deserialize<SagaState>(stateBytes.ToArray())!;

        try
        {
            var next = Advance(state, args.Message.Subject);

            await args.SetSessionStateAsync(
                new BinaryData(JsonSerializer.SerializeToUtf8Bytes(next)), ct);

            await args.CompleteMessageAsync(args.Message, ct);

            _log.LogInformation("Session {SessionId}: {From} -> {To} (step {Step})",
                args.SessionId, state.Step, next.Step, next.Sequence);

            if (next.Step == "Completed")
            {
                // Clear the state and let the session go — otherwise it lingers.
                await args.SetSessionStateAsync(null, ct);
                await args.CloseSessionAsync(ct);
            }
        }
        catch (Exception ex)
        {
            _log.LogError(ex, "Session {SessionId} failed at {Step}", args.SessionId, state.Step);
            await args.AbandonMessageAsync(args.Message, cancellationToken: ct);
        }
    }

    private static SagaState Advance(SagaState current, string? messageType) => messageType switch
    {
        "OrderPlaced"      => current with { Step = "AwaitingPayment", Sequence = current.Sequence + 1 },
        "PaymentCaptured"  => current with { Step = "AwaitingStock",   Sequence = current.Sequence + 1 },
        "StockReserved"    => current with { Step = "Completed",       Sequence = current.Sequence + 1 },
        _                  => current,
    };

    private sealed record SagaState(string OrderId, string Step, int Sequence);

    public override void Dispose()
    {
        _processor.DisposeAsync().AsTask().GetAwaiter().GetResult();
        _client.DisposeAsync().AsTask().GetAwaiter().GetResult();
        base.Dispose();
    }
}

// -----------------------------------------------------------------------------
// DLQ DRAIN — step 8. Run this on a timer. Fifteen minutes is a good default.
//
// ALGORITHM:
//  1. Open a receiver on the sub-queue "<entity>/$DeadLetterQueue".
//  2. Read the DeadLetterReason and DeadLetterErrorDescription — the broker
//     wrote them, and they are the whole reason the DLQ is useful.
//  3. Decide per reason:
//       transient / config problem now fixed  -> resubmit to the live queue
//       permanently broken                    -> archive to storage, complete
//       unknown                               -> leave it, alert a human
//  4. Resubmit as a NEW message that keeps the original MessageId, so the
//     downstream idempotency check still recognises it.
//  5. Complete the DLQ copy only AFTER the resubmit succeeded. The other order
//     loses messages.
// -----------------------------------------------------------------------------
public sealed class DeadLetterDrain
{
    private readonly ServiceBusClient _client;
    private readonly ILogger _log;

    public DeadLetterDrain(string fqns, ILogger log)
    {
        _client = new ServiceBusClient(fqns, new DefaultAzureCredential());
        _log = log;
    }

    public async Task<int> DrainAsync(
        string queueName, int maxMessages = 100, CancellationToken ct = default)
    {
        // Step 1.
        var dlqPath = ServiceBusReceiver.FormatDeadLetterPath(queueName);
        await using var receiver = _client.CreateReceiver(dlqPath,
            new ServiceBusReceiverOptions { ReceiveMode = ServiceBusReceiveMode.PeekLock });

        await using var sender = _client.CreateSender(queueName);

        var messages = await receiver.ReceiveMessagesAsync(
            maxMessages, TimeSpan.FromSeconds(5), ct);

        var resubmitted = 0;

        foreach (var dead in messages)
        {
            // Step 2.
            var reason = dead.DeadLetterReason ?? "Unknown";
            var detail = dead.DeadLetterErrorDescription ?? "";

            _log.LogInformation("DLQ {MessageId}: {Reason} — {Detail}",
                dead.MessageId, reason, Truncate(detail, 200));

            // Step 3.
            switch (reason)
            {
                case "MaxDeliveryCountExceeded":
                case "TransientDownstreamFailure":
                {
                    // Step 4: same MessageId, fresh envelope.
                    var retry = new ServiceBusMessage(dead.Body)
                    {
                        MessageId = dead.MessageId,
                        SessionId = dead.SessionId,
                        Subject = dead.Subject,
                        ContentType = dead.ContentType,
                        CorrelationId = dead.CorrelationId,
                    };
                    foreach (var kv in dead.ApplicationProperties)
                        retry.ApplicationProperties[kv.Key] = kv.Value;

                    retry.ApplicationProperties["dlq-replayed-at"] =
                        DateTimeOffset.UtcNow.ToString("O");
                    retry.ApplicationProperties["dlq-original-reason"] = reason;

                    await sender.SendMessageAsync(retry, ct);

                    // Step 5: only now.
                    await receiver.CompleteMessageAsync(dead, ct);
                    resubmitted++;
                    break;
                }

                case "DeserializationFailed":
                case "PaymentDeclined":
                    // Never going to work. Archive the bytes somewhere durable,
                    // then remove it so the DLQ depth alert means something.
                    await ArchiveAsync(dead, ct);
                    await receiver.CompleteMessageAsync(dead, ct);
                    break;

                default:
                    // Unknown reason: leave it. Someone should look.
                    await receiver.AbandonMessageAsync(dead, cancellationToken: ct);
                    _log.LogWarning("Unhandled DLQ reason {Reason} on {MessageId} — left in place",
                        reason, dead.MessageId);
                    break;
            }
        }

        return resubmitted;
    }

    private static Task ArchiveAsync(ServiceBusReceivedMessage m, CancellationToken ct)
        => Task.CompletedTask;   // write to Blob Storage in real life

    private static string Truncate(string s, int max) => s.Length <= max ? s : s[..max];
}
