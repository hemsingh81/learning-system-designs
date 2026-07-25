using System.Net;
using System.Net.Http.Json;
using System.Text.Json.Serialization;

namespace Ecommerce.Payments.Gateways;

// ─────────────────────────────────────────────────────────────────────────────
// AN ANTI-CORRUPTION LAYER OVER AN EXTERNAL PAYMENT PROVIDER
//
// Two jobs:
//   1. Keep the provider's model out of our domain (chapter 6).
//   2. Make a non-idempotent operation safe to retry (chapter 8).
//
// Job 2 is the important one. Charging a card is the least forgiving operation
// in most systems: the request can succeed on their side and time out on ours,
// and we cannot tell the difference. An idempotency key is the only way out.
// ─────────────────────────────────────────────────────────────────────────────

public interface IPaymentGateway
{
    Task<ChargeResult> ChargeAsync(Guid orderId, decimal amount, string currency, CancellationToken ct);
    Task<RefundResult> RefundAsync(Guid orderId, string transactionId, decimal amount, CancellationToken ct);
}

public sealed class AcmePspGateway(
    HttpClient http,
    ILogger<AcmePspGateway> log) : IPaymentGateway
{
    public async Task<ChargeResult> ChargeAsync(
        Guid orderId, decimal amount, string currency, CancellationToken ct)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, "/v1/charges")
        {
            Content = JsonContent.Create(new AcmeChargeRequest
            {
                // Acme wants the smallest currency unit as an integer.
                // Never send decimals to a payment API — rounding differences are real money.
                AmountMinor = (long)Math.Round(amount * 100m, MidpointRounding.ToEven),
                Currency    = currency.ToLowerInvariant(),
                Reference   = orderId.ToString()
            })
        };

        // ── THE MOST IMPORTANT LINE IN THIS FILE ────────────────────────────
        // Derived from the order, so it is IDENTICAL on every retry attempt.
        // Acme returns the ORIGINAL charge instead of creating a second one.
        //
        // Guid.NewGuid() here would defeat the entire mechanism and would be
        // indistinguishable from correct code in a review. Never do it.
        request.Headers.Add("Idempotency-Key", $"charge-{orderId}");

        try
        {
            using var response = await http.SendAsync(request, ct);

            // 409 from Acme means "this key was used with DIFFERENT parameters".
            // That is a bug on our side, not a transient failure. Never retry it.
            if (response.StatusCode == HttpStatusCode.Conflict)
            {
                log.LogError("Idempotency key reused with different parameters for order {OrderId}", orderId);
                return ChargeResult.Failed("idempotency_conflict",
                    "the same key was sent with different amounts — investigate");
            }

            // 402 means the card was declined. That is a normal business outcome,
            // NOT an error. Retrying a declined card just annoys the bank.
            if (response.StatusCode == HttpStatusCode.PaymentRequired)
            {
                var declined = await response.Content
                    .ReadFromJsonAsync<AcmeErrorResponse>(cancellationToken: ct);

                return ChargeResult.Failed(
                    declined?.Code ?? "card_declined",
                    declined?.Message ?? "the card was declined");
            }

            // 5xx and 429 ARE transient. Throw so the Polly pipeline retries
            // with backoff and jitter (chapter 9). The idempotency key makes
            // that retry safe.
            response.EnsureSuccessStatusCode();

            var body = await response.Content.ReadFromJsonAsync<AcmeChargeResponse>(cancellationToken: ct)
                       ?? throw new InvalidOperationException("empty response from Acme");

            // Translate their model into ours. Their vocabulary stops here.
            return body.Status switch
            {
                "succeeded" => ChargeResult.Succeeded(body.Id),

                // Some providers return 200 with a pending status for 3-D Secure.
                // Treating this as success would confirm an unpaid order.
                "pending"   => ChargeResult.Pending(body.Id),

                "failed"    => ChargeResult.Failed(body.FailureCode ?? "unknown",
                                                   body.FailureMessage ?? "charge failed"),

                _           => ChargeResult.Failed("unknown_status",
                                                   $"Acme returned an unrecognised status '{body.Status}'")
            };
        }
        catch (TaskCanceledException) when (!ct.IsCancellationRequested)
        {
            // A TIMEOUT, not a cancellation. This is the dangerous case:
            // the charge may have SUCCEEDED on Acme's side.
            //
            // We must not report failure — that would cancel a paid order.
            // We report Unknown, and the caller re-sends with the SAME idempotency
            // key, which returns the original charge if it exists.
            log.LogWarning("Charge timed out for order {OrderId}. Outcome is UNKNOWN — " +
                           "safe to retry with the same idempotency key", orderId);

            return ChargeResult.Unknown("timeout — retry with the same key to learn the real outcome");
        }
    }

    public async Task<RefundResult> RefundAsync(
        Guid orderId, string transactionId, decimal amount, CancellationToken ct)
    {
        var request = new HttpRequestMessage(HttpMethod.Post, $"/v1/charges/{transactionId}/refunds")
        {
            Content = JsonContent.Create(new { amount_minor = (long)Math.Round(amount * 100m) })
        };

        // Compensation needs an idempotency key just as much as the original action.
        // A double refund is a direct loss, and it is a real bug that ships regularly.
        request.Headers.Add("Idempotency-Key", $"refund-{orderId}");

        using var response = await http.SendAsync(request, ct);
        response.EnsureSuccessStatusCode();

        var body = await response.Content.ReadFromJsonAsync<AcmeRefundResponse>(cancellationToken: ct)!;
        return new RefundResult(body!.Id, body.Status == "succeeded");
    }
}

// ── Our model. Clean, and nothing to do with Acme's vocabulary. ──────────────

public sealed record ChargeResult
{
    public required ChargeOutcome Outcome        { get; init; }
    public string?                TransactionId  { get; init; }
    public string?                FailureCode    { get; init; }
    public string?                FailureMessage { get; init; }

    public bool IsSuccess => Outcome == ChargeOutcome.Succeeded;

    public static ChargeResult Succeeded(string transactionId) =>
        new() { Outcome = ChargeOutcome.Succeeded, TransactionId = transactionId };

    public static ChargeResult Pending(string transactionId) =>
        new() { Outcome = ChargeOutcome.Pending, TransactionId = transactionId };

    public static ChargeResult Failed(string code, string message) =>
        new() { Outcome = ChargeOutcome.Failed, FailureCode = code, FailureMessage = message };

    public static ChargeResult Unknown(string message) =>
        new() { Outcome = ChargeOutcome.Unknown, FailureMessage = message };
}

public enum ChargeOutcome
{
    Succeeded,
    Failed,

    /// <summary>Awaiting the customer (3-D Secure). Not success. Not failure.</summary>
    Pending,

    /// <summary>We genuinely do not know. Retry with the same idempotency key
    /// to find out. Never treat this as failure — that cancels paid orders.</summary>
    Unknown
}

public sealed record RefundResult(string RefundId, bool Succeeded);

// ── Acme's wire model. Private to this file. Nothing else may see it. ────────

file sealed record AcmeChargeRequest
{
    [JsonPropertyName("amount")]    public required long   AmountMinor { get; init; }
    [JsonPropertyName("currency")]  public required string Currency    { get; init; }
    [JsonPropertyName("reference")] public required string Reference   { get; init; }
}

file sealed record AcmeChargeResponse
{
    [JsonPropertyName("id")]              public required string Id { get; init; }
    [JsonPropertyName("status")]          public required string Status { get; init; }
    [JsonPropertyName("failure_code")]    public string? FailureCode { get; init; }
    [JsonPropertyName("failure_message")] public string? FailureMessage { get; init; }
}

file sealed record AcmeRefundResponse
{
    [JsonPropertyName("id")]     public required string Id { get; init; }
    [JsonPropertyName("status")] public required string Status { get; init; }
}

file sealed record AcmeErrorResponse
{
    [JsonPropertyName("code")]    public string? Code { get; init; }
    [JsonPropertyName("message")] public string? Message { get; init; }
}
