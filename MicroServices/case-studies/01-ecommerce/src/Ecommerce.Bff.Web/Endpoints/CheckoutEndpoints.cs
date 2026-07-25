using Ecommerce.Bff.Web.Clients;

namespace Ecommerce.Bff.Web.Endpoints;

// ─────────────────────────────────────────────────────────────────────────────
// THE WEB BFF
//
// Two jobs the gateway must NOT do:
//   1. Fan out to several services and shape one response for THIS client.
//   2. Decide which parts of the page are allowed to fail.
//
// Job 2 is the interesting one. This file encodes the business's constraint:
// "checkout must stay up". Every dependency here is classified as either
// ESSENTIAL (failure fails the request) or ENHANCEMENT (failure degrades it).
//
// That classification belongs in code, decided in advance — not in a person's
// head during an incident.
// ─────────────────────────────────────────────────────────────────────────────

public static class CheckoutEndpoints
{
    public static IEndpointRouteBuilder MapCheckout(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/web").RequireAuthorization();

        group.MapGet ("/checkout/summary", GetSummaryAsync);
        group.MapPost("/checkout",         PlaceOrderAsync);

        return app;
    }

    // ── The checkout page ───────────────────────────────────────────────────

    private static async Task<IResult> GetSummaryAsync(
        Guid basketId,
        BasketClient baskets,
        CatalogClient catalog,
        InventoryClient inventory,
        PromotionsClient promotions,
        ILogger<BasketClient> log,
        CancellationToken ct)
    {
        // ESSENTIAL. No basket, no page. There is no sensible fallback.
        var basket = await baskets.GetAsync(basketId, ct);
        if (basket is null) return Results.NotFound();

        var skus = basket.Lines.Select(l => l.Sku).ToArray();

        // Fan out in PARALLEL. Sequential awaits here would triple the page time —
        // this is the single biggest performance decision a BFF makes.
        var productsTask   = catalog.GetBatchAsync(skus, ct);
        var stockTask      = inventory.GetBatchAsync(skus, ct);
        var promotionsTask = promotions.GetForBasketAsync(basketId, ct);

        // WhenAll, but each result is unwrapped with its OWN failure policy below.
        await Task.WhenAll(productsTask, stockTask, promotionsTask)
                  .ContinueWith(_ => { }, TaskContinuationOptions.ExecuteSynchronously);

        // ESSENTIAL: names and prices. The client falls back to its cache inside
        // CatalogClient; if even that fails, we genuinely cannot render a checkout.
        var products = await Unwrap(productsTask, onFailure: () => (IReadOnlyList<ProductDto>?)null);
        if (products is null)
        {
            log.LogError("Catalog unavailable and cache empty — cannot render checkout");
            return Results.Problem(
                title: "Checkout is temporarily unavailable",
                statusCode: StatusCodes.Status503ServiceUnavailable);
        }

        // ENHANCEMENT: the stock badge. If Inventory is down we hide the badge and
        // still let the customer buy. This is the deliberate oversell trade — see
        // "Decision 3" in the README. It is a business decision, written in code.
        var stock = await Unwrap(stockTask, onFailure: () =>
        {
            log.LogWarning("Inventory unavailable — hiding stock badges, accepting oversell risk");
            return (IReadOnlyDictionary<string, int>?)null;
        });

        // ENHANCEMENT: discounts. If Promotions is down, the customer pays full
        // price — which is worse for them, so we say so rather than hiding it.
        var promos = await Unwrap(promotionsTask, onFailure: () =>
        {
            log.LogWarning("Promotions unavailable — showing undiscounted prices");
            return (PromotionsDto?)null;
        });

        return Results.Ok(new CheckoutSummary
        {
            BasketId = basketId,
            Lines = basket.Lines.Select(line =>
            {
                var product = products.FirstOrDefault(p => p.Sku == line.Sku);
                return new CheckoutLine
                {
                    Sku         = line.Sku,
                    Name        = product?.Name ?? line.Sku,
                    UnitPrice   = product?.Price ?? line.PriceAtAdd,
                    Quantity    = line.Quantity,
                    ImageUrl    = product?.ImageUrl,

                    // null means "we do not know", and the UI shows nothing —
                    // not "out of stock", which would lose a sale it need not.
                    StockRemaining = stock?.GetValueOrDefault(line.Sku)
                };
            }).ToList(),

            Discount        = promos?.TotalDiscount ?? 0m,
            DiscountApplied = promos is not null,

            // Tell the UI it is running degraded so it can say so honestly.
            Degraded = stock is null || promos is null
        });
    }

    // ── Placing the order ───────────────────────────────────────────────────

    private static async Task<IResult> PlaceOrderAsync(
        PlaceOrderBody body,
        OrderingClient ordering,
        CancellationToken ct)
    {
        // The BFF forwards the client's idempotency key. It does NOT generate one:
        // a key made here would be new on every retry, which defeats the mechanism
        // exactly when it is needed. The key must come from the client.
        if (string.IsNullOrWhiteSpace(body.IdempotencyKey))
            return Results.BadRequest(new { error = "idempotencyKey is required" });

        // ESSENTIAL and no fallback. If Ordering is down, we cannot take the order,
        // and pretending otherwise would be lying to the customer about their money.
        var result = await ordering.PlaceAsync(body, ct);

        // Pass through the 202. The client shows "Processing…" and waits for the
        // SignalR push. See OrderEventsConsumer for the other half of this handshake.
        return Results.Accepted($"/web/orders/{result.Id}", result);
    }

    // Small helper so each dependency's failure policy is one readable line.
    private static async Task<T> Unwrap<T>(Task<T> task, Func<T> onFailure)
    {
        try   { return await task; }
        catch { return onFailure(); }
    }
}

public sealed record CheckoutSummary
{
    public required Guid BasketId { get; init; }
    public required IReadOnlyList<CheckoutLine> Lines { get; init; }
    public required decimal Discount { get; init; }
    public required bool DiscountApplied { get; init; }

    /// <summary>True when something is degraded. The UI shows a small notice
    /// instead of silently displaying an incomplete page.</summary>
    public required bool Degraded { get; init; }
}

public sealed record CheckoutLine
{
    public required string  Sku       { get; init; }
    public required string  Name      { get; init; }
    public required decimal UnitPrice { get; init; }
    public required int     Quantity  { get; init; }
    public string? ImageUrl { get; init; }

    /// <summary>null = unknown (Inventory unavailable). The UI renders nothing.</summary>
    public int? StockRemaining { get; init; }
}

public sealed record PlaceOrderBody
{
    public required Guid   BasketId       { get; init; }
    public required string IdempotencyKey { get; init; }
    public required Guid   PaymentMethodId { get; init; }
}
