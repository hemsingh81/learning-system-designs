using Ecommerce.Ordering.Domain;
using Ecommerce.Ordering.Infrastructure;
using Ecommerce.Ordering.Infrastructure.Outbox;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;

namespace Ecommerce.Ordering.Api;

// ─────────────────────────────────────────────────────────────────────────────
// THE HTTP SURFACE
//
// Thin on purpose. Three jobs only:
//   1. Translate HTTP into a domain call.
//   2. Persist the result AND its events in ONE transaction (the outbox).
//   3. Translate the result back into HTTP.
//
// There is no IBus injected here. That absence is the entire point of chapter 8:
// publishing directly from an endpoint is the dual-write bug.
// ─────────────────────────────────────────────────────────────────────────────

public static class OrdersEndpoints
{
    public static IEndpointRouteBuilder MapOrders(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/orders").RequireAuthorization();

        group.MapPost("/",      PlaceAsync);
        group.MapGet ("/{id}",  GetAsync);

        return app;
    }

    private static async Task<IResult> PlaceAsync(
        PlaceOrderRequest request,
        [FromHeader(Name = "Idempotency-Key")] string? idempotencyKey,
        OrderingDbContext db,
        ILogger<PlaceOrderRequest> log,
        CancellationToken ct)
    {
        // ── 1. Idempotency ──────────────────────────────────────────────────
        // Mobile networks drop responses. Users tap twice. Clients retry.
        // Without this header, all three create duplicate orders.
        if (string.IsNullOrWhiteSpace(idempotencyKey))
            return Results.Problem(
                title: "Idempotency-Key header is required",
                detail: "Send a stable, client-generated key so retries are safe.",
                statusCode: StatusCodes.Status400BadRequest);

        var existing = await db.Orders
            .AsNoTracking()
            .FirstOrDefaultAsync(o => o.IdempotencyKey == idempotencyKey, ct);

        if (existing is not null)
        {
            // A retry, not a new order. Return the ORIGINAL result.
            // 200, not 409 — from the client's point of view this simply succeeded.
            log.LogInformation("Idempotent replay of {Key} → order {OrderId}", idempotencyKey, existing.Id);
            return Results.Ok(OrderResponse.From(existing));
        }

        // ── 2. Domain ───────────────────────────────────────────────────────
        Order order;
        try
        {
            order = Order.Place(
                customerId:     request.CustomerId,
                customerEmail:  request.CustomerEmail,
                currency:       request.Currency ?? "INR",
                idempotencyKey: idempotencyKey,
                lines: request.Lines.Select(l =>
                    OrderLine.Create(l.Sku, l.Name, l.Quantity, l.UnitPrice)));
        }
        catch (ArgumentException ex)
        {
            // A domain rule said no. That is a 400, not a 500 — the caller can fix it.
            return Results.Problem(title: "Invalid order", detail: ex.Message,
                                   statusCode: StatusCodes.Status400BadRequest);
        }

        // ── 3. Persist the order AND its events in ONE transaction ──────────
        db.Orders.Add(order);

        foreach (var domainEvent in order.DomainEvents)
            db.OutboxMessages.Add(OutboxMessage.From(domainEvent));

        order.ClearDomainEvents();

        try
        {
            // Both rows commit, or neither does. This single line is the whole
            // reason we do not lose events when the process dies.
            await db.SaveChangesAsync(ct);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("IX_Orders_IdempotencyKey"))
        {
            // Two identical requests arrived at two instances at the same instant.
            // Both passed the check above; the unique index caught the second.
            // Re-read and return the winner. This is a success, not an error.
            var winner = await db.Orders.AsNoTracking()
                .FirstAsync(o => o.IdempotencyKey == idempotencyKey, ct);

            return Results.Ok(OrderResponse.From(winner));
        }

        // ── 4. 202 Accepted, NOT 201 Created ────────────────────────────────
        // "I have taken responsibility for this." Stock is not reserved and the
        // card is not charged yet. Saying 201 here would be a lie, and lies about
        // eventual consistency become support tickets (chapter 3).
        return Results.Accepted($"/orders/{order.Id}", OrderResponse.From(order));
    }

    private static async Task<IResult> GetAsync(Guid id, OrderingDbContext db, CancellationToken ct)
    {
        var order = await db.Orders
            .AsNoTracking()
            .Include(o => o.Lines)
            .FirstOrDefaultAsync(o => o.Id == id, ct);

        return order is null ? Results.NotFound() : Results.Ok(OrderResponse.From(order));
    }
}

// ── Request / response shapes ────────────────────────────────────────────────
// Deliberately separate from the domain model. If the API shape and the domain
// model are the same class, you cannot change one without changing the other,
// and your public contract becomes hostage to an internal refactor.

public sealed record PlaceOrderRequest
{
    public required Guid   CustomerId    { get; init; }
    public required string CustomerEmail { get; init; }
    public string? Currency { get; init; }
    public required IReadOnlyList<PlaceOrderLine> Lines { get; init; }
}

public sealed record PlaceOrderLine
{
    public required string  Sku       { get; init; }
    public required string  Name      { get; init; }
    public required int     Quantity  { get; init; }
    public required decimal UnitPrice { get; init; }
}

public sealed record OrderResponse
{
    public required Guid    Id       { get; init; }
    public required string  Status   { get; init; }
    public required decimal Total    { get; init; }
    public required string  Currency { get; init; }

    /// <summary>Tells the client whether to keep listening for a push update.
    /// Without it, the UI has to guess whether "Pending" is final.</summary>
    public required bool IsFinal { get; init; }

    public static OrderResponse From(Order o) => new()
    {
        Id       = o.Id,
        Status   = o.Status.ToString(),
        Total    = o.Total,
        Currency = o.Currency,
        IsFinal  = o.Status is OrderStatus.Cancelled or OrderStatus.Delivered
    };
}
