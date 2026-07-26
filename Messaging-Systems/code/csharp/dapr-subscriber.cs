// =============================================================================
// dapr-subscriber.cs — consuming through the Dapr sidecar
//
// THE ALGORITHM, IN PLAIN ENGLISH — read this before the code.
//
//  1. You do not poll, and you do not open a consumer. The sidecar subscribes
//     to the broker and calls YOUR HTTP endpoint. Your consumer is a web
//     handler, which is a genuine mental shift from every other file here.
//  2. Declare the subscription. Either with a [Topic] attribute (programmatic)
//     or a Subscription YAML resource (declarative). Declarative is better for
//     production: routing changes without a redeploy.
//  3. Dapr decides what to do next from your HTTP RESPONSE, not from an ack
//     call. This is THE thing to understand:
//        200 OK  + status SUCCESS  -> acknowledged, message gone
//        200 OK  + status RETRY    -> redelivered per the resiliency policy
//        200 OK  + status DROP     -> discarded, or sent to the dead letter topic
//        non-2xx or an exception   -> treated as RETRY
//     An unhandled exception therefore means infinite retry until the policy
//     gives up. Never let one escape.
//  4. Check the idempotency key first. Dapr is at-least-once like everything
//     else, and its retries make duplicates MORE likely, not less.
//  5. Use YOUR message id from inside the payload — not the CloudEvent `id`,
//     which is generated fresh by Dapr on every publish and is useless for
//     deduplication.
//  6. Classify failures. Transient -> RETRY. Permanent -> DROP, so it goes to
//     the dead letter topic instead of burning the retry budget.
//  7. Configure the dead letter topic on the SUBSCRIPTION, and subscribe to it.
//     A dead letter topic nobody reads is the same slow data-loss machine as
//     any other unwatched DLQ.
//  8. Keep handlers fast. The sidecar holds the broker-level lock or offset
//     while your HTTP call is outstanding; a slow handler causes the same lock
//     expiry and rebalance problems as everywhere else in this repo.
//
// Run: dapr run --app-id payment-worker --app-port 8080 \
//        --resources-path ./components -- dotnet run
// =============================================================================

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Dapr;
using Dapr.AspNetCore;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;

namespace Messaging.Samples.Dapr;

public interface IIdempotencyStore
{
    Task<bool> AlreadyProcessedAsync(string messageId, CancellationToken ct);
    Task MarkProcessedAsync(string messageId, CancellationToken ct);
}

// -----------------------------------------------------------------------------
// MINIMAL API STYLE — the shape most teams use
// -----------------------------------------------------------------------------
public static class SubscriberEndpoints
{
    public static void MapOrderSubscriptions(this WebApplication app)
    {
        // Step 2, programmatic. Dapr calls GET /dapr/subscribe at startup and
        // this attribute is how it learns the mapping. Fine for small services;
        // prefer the YAML in ../../k8s/dapr-components.yaml for production,
        // because routing then changes without a redeploy.
        app.MapPost("/orders/placed", HandleOrderPlacedAsync)
           .WithTopic("pubsub", "orders");

        // Step 7: the dead letter topic needs a subscriber too.
        app.MapPost("/orders/dead-letter", HandleDeadLetterAsync)
           .WithTopic("pubsub", "orders-dlq");
    }

    private static async Task<IResult> HandleOrderPlacedAsync(
        OrderPlaced order,                          // Dapr unwraps the CloudEvent for you
        IIdempotencyStore idempotency,
        IPaymentService payments,
        ILogger<Program> log,
        CancellationToken ct)
    {
        // Step 5: OUR id, from inside the payload. Not the envelope id.
        var messageId = order.MessageId;

        try
        {
            // Step 4: dedupe before doing anything expensive.
            if (await idempotency.AlreadyProcessedAsync(messageId, ct))
            {
                log.LogDebug("Duplicate {MessageId} — acknowledging", messageId);
                return Results.Ok(new { status = "SUCCESS" });   // step 3
            }

            await payments.CaptureAsync(order, ct);
            await idempotency.MarkProcessedAsync(messageId, ct);

            log.LogInformation("Processed {MessageId} for order {OrderId}",
                messageId, order.OrderId);

            return Results.Ok(new { status = "SUCCESS" });
        }
        catch (JsonException ex)
        {
            // Step 6: permanent. A malformed payload never becomes well-formed.
            // DROP sends it to the dead letter topic instead of retrying five
            // times to reach the same conclusion.
            log.LogError(ex, "Unparseable payload for {MessageId} — dropping to DLQ", messageId);
            return Results.Ok(new { status = "DROP" });
        }
        catch (PaymentDeclinedException ex)
        {
            // Step 6: a business rejection is not a transient fault. Retrying a
            // declined card annoys the provider and delays the real answer.
            log.LogWarning("Payment declined for {MessageId}: {Reason}", messageId, ex.Reason);
            return Results.Ok(new { status = "DROP" });
        }
        catch (Exception ex)
        {
            // Step 6: transient. RETRY hands control to the resiliency policy in
            // ../../k8s/dapr-components.yaml — exponential backoff, then the
            // circuit breaker, then the dead letter topic.
            log.LogWarning(ex, "Transient failure on {MessageId} — requesting retry", messageId);
            return Results.Ok(new { status = "RETRY" });
        }

        // NOTE: there is deliberately no path here that lets an exception
        // escape. An unhandled exception is a non-2xx response, which Dapr
        // reads as RETRY — so a NullReferenceException becomes an infinite
        // retry loop that looks exactly like a broker problem and is not one.
    }

    /// <summary>
    /// Step 7. The dead letter topic is a normal topic; subscribe to it and
    /// triage. Always return SUCCESS here — a failure in the DLQ handler that
    /// returns RETRY creates a loop with nowhere left to fall through to.
    /// </summary>
    private static async Task<IResult> HandleDeadLetterAsync(
        [FromBody] JsonElement raw,
        ILogger<Program> log,
        CancellationToken ct)
    {
        log.LogError("DEAD LETTER: {Payload}", raw.ToString());

        // In production: persist for triage, increment a metric, alert on depth.
        // The replay path belongs in a separate scheduled job, not here.
        await Task.CompletedTask;

        return Results.Ok(new { status = "SUCCESS" });
    }
}

// -----------------------------------------------------------------------------
// CONTROLLER STYLE — same semantics, plus access to the raw CloudEvent
// -----------------------------------------------------------------------------
[ApiController]
public sealed class OrderEventsController : ControllerBase
{
    private readonly IIdempotencyStore _idempotency;
    private readonly ILogger<OrderEventsController> _log;

    public OrderEventsController(IIdempotencyStore idempotency, ILogger<OrderEventsController> log)
    {
        _idempotency = idempotency;
        _log = log;
    }

    /// <summary>
    /// Taking the CloudEvent explicitly gives you the envelope metadata —
    /// most usefully the trace id, for correlating logs across services.
    ///
    /// Note what is NOT here: no delivery count, no broker offset, no lock
    /// token, no partition. Those exist in the native clients in this folder
    /// and Dapr does not surface them. If a runbook step needs them, that
    /// service should not be on Dapr.
    /// </summary>
    [Topic("pubsub", "orders")]
    [HttpPost("/orders/placed-with-envelope")]
    public async Task<IActionResult> HandleAsync(
        [FromBody] CloudEvent<OrderPlaced> cloudEvent, CancellationToken ct)
    {
        var order = cloudEvent.Data;

        // Step 5 again, because it is the mistake people make:
        //   cloudEvent.Id  -> Dapr's, random, DIFFERENT on every republish
        //   order.MessageId -> ours, deterministic, correct for deduplication
        var messageId = order.MessageId;

        if (await _idempotency.AlreadyProcessedAsync(messageId, ct))
            return Ok(new { status = "SUCCESS" });

        _log.LogInformation("Handling {MessageId} (cloudevent {CeId}, type {Type})",
            messageId, cloudEvent.Id, cloudEvent.Type);

        await _idempotency.MarkProcessedAsync(messageId, ct);
        return Ok(new { status = "SUCCESS" });
    }
}

// -----------------------------------------------------------------------------
// REGISTRATION
// -----------------------------------------------------------------------------
public static class SubscriberStartup
{
    public static WebApplication Build(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        builder.Services.AddDaprClient();
        builder.Services.AddControllers().AddDapr();

        var app = builder.Build();

        // Required: parses the CloudEvents envelope into your model.
        // Forget this and every handler receives the envelope instead of the
        // payload, and deserialisation fails in a confusing way.
        app.UseCloudEvents();

        // Required: serves GET /dapr/subscribe so the sidecar learns the
        // topic-to-endpoint mapping at startup.
        app.MapSubscribeHandler();

        app.MapControllers();
        app.MapOrderSubscriptions();

        // Step 8 support: readiness gates traffic until the sidecar is up.
        app.MapGet("/healthz", () => Results.Ok());

        return app;
    }
}

public interface IPaymentService
{
    Task CaptureAsync(OrderPlaced order, CancellationToken ct);
}

public sealed class PaymentDeclinedException(string reason) : Exception(reason)
{
    public string Reason { get; } = reason;
}
