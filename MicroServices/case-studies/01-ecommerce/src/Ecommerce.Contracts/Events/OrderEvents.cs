namespace Ecommerce.Contracts.Events;

// ─────────────────────────────────────────────────────────────────────────────
// EVENTS PUBLISHED BY THE ORDERING SERVICE
//
// Rules that apply to every event in this file:
//
// 1. PAST TENSE. An event is a fact that already happened. It cannot be rejected.
//    "OrderPlaced", not "PlaceOrder" and not "ProcessOrder".
//
// 2. IMMUTABLE. `record` with init-only properties. Nobody mutates an event.
//
// 3. SELF-CONTAINED. Include the data consumers need. A consumer should not have
//    to call back to Ordering to do its job — that would recreate the synchronous
//    coupling we removed.
//
// 4. NO DOMAIN TYPES. Primitives and simple DTOs only. If Ordering's `Order`
//    class leaked in here, every consumer would depend on Ordering's internals.
//
// 5. ADDITIVE CHANGES ONLY. New optional field: fine. Renaming, removing, or
//    changing the meaning of a field: publish a V2 instead. See chapter 6.
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>
/// A customer's order has been accepted. Status is Pending — nothing is
/// reserved or charged yet.
///
/// Consumers today: Inventory (reserve), Notifications (ack email), Analytics.
/// New consumers may subscribe at any time; Ordering does not need to know.
/// </summary>
public sealed record OrderPlaced
{
    public required Guid   OrderId    { get; init; }
    public required Guid   CustomerId { get; init; }

    /// <summary>Money is always (amount, currency). An amount alone is a bug waiting to happen.</summary>
    public required decimal Total    { get; init; }
    public required string  Currency { get; init; }

    public required IReadOnlyList<OrderLineDto> Lines { get; init; }

    /// <summary>Denormalised so Notifications does not have to call Customers.</summary>
    public required string CustomerEmail { get; init; }

    /// <summary>When the business event happened — NOT when the message was published.
    /// Those differ by however long the outbox row waited.</summary>
    public required DateTime OccurredAtUtc { get; init; }
}

public sealed record OrderLineDto
{
    public required string  Sku       { get; init; }
    public required string  Name      { get; init; }   // denormalised for the email
    public required int     Quantity  { get; init; }
    public required decimal UnitPrice { get; init; }
}

/// <summary>Payment succeeded and the order is confirmed. Shipping starts here.</summary>
public sealed record OrderConfirmed
{
    public required Guid     OrderId       { get; init; }
    public required Guid     CustomerId    { get; init; }
    public required string   TransactionId { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}

/// <summary>
/// The order will not proceed. Everything already done for it must be undone.
/// Inventory listens to release its reservation.
/// </summary>
public sealed record OrderCancelled
{
    public required Guid     OrderId       { get; init; }
    public required Guid     CustomerId    { get; init; }

    /// <summary>Machine-readable. Consumers branch on this; humans read the message.</summary>
    public required CancellationReason Reason { get; init; }
    public required string   ReasonDetail  { get; init; }
    public required DateTime OccurredAtUtc { get; init; }
}

public enum CancellationReason
{
    // Value 0 is deliberately "Unknown". If a producer forgets to set the field,
    // consumers see Unknown rather than silently treating it as PaymentDeclined.
    Unknown = 0,
    OutOfStock = 1,
    PaymentDeclined = 2,
    PaymentTimeout = 3,
    CustomerCancelled = 4,
    FraudSuspected = 5
}

// ─────────────────────────────────────────────────────────────────────────────
// VERSIONING EXAMPLE
//
// Suppose finance needs tax broken out. `Total` alone is no longer enough.
// You do NOT edit OrderPlaced — old consumers would silently break.
// You publish BOTH for as long as any v1 consumer still exists:
//
//   public sealed record OrderPlacedV2
//   {
//       public required Guid    OrderId  { get; init; }
//       public required decimal Subtotal { get; init; }
//       public required decimal Tax      { get; init; }
//       public required string  Currency { get; init; }
//       …
//   }
//
// Then: measure who still consumes v1 → wait until that is zero for a week →
// stop publishing v1 → delete it. Weeks, not hours. That is correct.
// ─────────────────────────────────────────────────────────────────────────────
