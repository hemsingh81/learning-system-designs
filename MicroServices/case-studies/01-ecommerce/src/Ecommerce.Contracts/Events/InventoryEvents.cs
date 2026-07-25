namespace Ecommerce.Contracts.Events;

// ─────────────────────────────────────────────────────────────────────────────
// EVENTS PUBLISHED BY THE INVENTORY SERVICE
//
// Note what is NOT here: no "ReserveStock" command. In this choreographed
// design Inventory reacts to OrderPlaced on its own. Nobody tells it what to do.
//
// If this system moves to orchestration (chapter 7), these events stay exactly
// as they are, and a `ReserveStock` COMMAND is added alongside them. Events and
// commands coexist; they answer different questions.
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>
/// Stock is now held for this order. It is not sold — it is off the shelf,
/// waiting. A reservation always has an expiry: if payment never resolves,
/// the sweeper must be able to reclaim it.
/// </summary>
public sealed record StockReserved
{
    public required Guid OrderId { get; init; }
    public required IReadOnlyList<ReservedLineDto> Lines { get; init; }

    /// <summary>
    /// After this instant the reservation may be swept and the stock returned to sale.
    /// Publishing it lets other services reason about the deadline too.
    /// </summary>
    public required DateTime ExpiresAtUtc { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}

public sealed record ReservedLineDto
{
    public required string Sku      { get; init; }
    public required int    Quantity { get; init; }
}

/// <summary>
/// Stock could not be reserved. The order cannot proceed.
///
/// This is a NEGATIVE OUTCOME EVENT, not an exception. Running out of stock is
/// a normal business outcome, so it travels as a first-class fact, not as a
/// failed message that lands in a dead-letter queue.
/// </summary>
public sealed record StockRejected
{
    public required Guid OrderId { get; init; }

    /// <summary>Exactly which lines failed, and what was actually available.
    /// The UI can say "only 1 left" instead of "something went wrong".</summary>
    public required IReadOnlyList<RejectedLineDto> RejectedLines { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}

public sealed record RejectedLineDto
{
    public required string Sku       { get; init; }
    public required int    Requested { get; init; }
    public required int    Available { get; init; }
}

/// <summary>
/// A reservation has been released and the stock is back on sale.
///
/// Published both by normal compensation (payment failed) and by the sweeper
/// (reservation expired). Consumers cannot tell the difference, and should not
/// need to — the fact is the same either way.
/// </summary>
public sealed record StockReleased
{
    public required Guid OrderId { get; init; }
    public required IReadOnlyList<ReservedLineDto> Lines { get; init; }
    public required ReleaseReason Reason { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}

public enum ReleaseReason
{
    Unknown = 0,
    PaymentFailed = 1,
    OrderCancelled = 2,

    /// <summary>Swept because it timed out. Worth counting as a metric —
    /// a rising number means events are being lost somewhere upstream.</summary>
    Expired = 3
}

/// <summary>
/// Stock was permanently taken (the order shipped). The reservation becomes a sale.
/// This is the point of no return for the stock — it cannot be released after this.
/// </summary>
public sealed record StockCommitted
{
    public required Guid OrderId { get; init; }
    public required IReadOnlyList<ReservedLineDto> Lines { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}
