using Ecommerce.Contracts.Events;

namespace Ecommerce.Ordering.Domain;

// ─────────────────────────────────────────────────────────────────────────────
// THE ORDER AGGREGATE
//
// This file has NO references to: EF Core, HttpClient, IBus, ILogger, or any
// other infrastructure. That is deliberate and it is testable in isolation —
// every rule below can be unit tested with `new` and no mocks at all.
//
// The aggregate raises events into a local list. It does not publish them.
// Publishing is infrastructure's job, via the outbox (chapter 8).
// ─────────────────────────────────────────────────────────────────────────────

public sealed class Order
{
    private readonly List<OrderLine> _lines = [];
    private readonly List<object>    _domainEvents = [];

    public Guid        Id             { get; private set; }
    public Guid        CustomerId     { get; private set; }
    public string      CustomerEmail  { get; private set; } = "";
    public OrderStatus Status         { get; private set; }
    public string      Currency       { get; private set; } = "INR";

    /// <summary>The client's retry key. Unique index in the database — this is what
    /// makes "customer tapped Pay twice on a bad connection" harmless.</summary>
    public string IdempotencyKey { get; private set; } = "";

    public string?  TransactionId    { get; private set; }
    public string?  CancellationNote { get; private set; }
    public DateTime PlacedAtUtc      { get; private set; }
    public DateTime UpdatedAtUtc     { get; private set; }

    public IReadOnlyList<OrderLine> Lines        => _lines;
    public IReadOnlyList<object>    DomainEvents => _domainEvents;

    /// <summary>Computed, never stored. A stored total that disagrees with its lines
    /// is one of the most common and most expensive data bugs in retail systems.</summary>
    public decimal Total => _lines.Sum(l => l.LineTotal);

    private Order() { }   // for EF

    // ── Creation ────────────────────────────────────────────────────────────

    public static Order Place(
        Guid customerId,
        string customerEmail,
        string currency,
        IEnumerable<OrderLine> lines,
        string idempotencyKey)
    {
        var lineList = lines.ToList();

        // Validate at the boundary of the aggregate. An Order object that exists
        // is always valid — there is no such thing as a half-built order.
        if (customerId == Guid.Empty)              throw new ArgumentException("customerId is required");
        if (string.IsNullOrWhiteSpace(customerEmail)) throw new ArgumentException("customerEmail is required");
        if (string.IsNullOrWhiteSpace(idempotencyKey)) throw new ArgumentException("idempotencyKey is required");
        if (lineList.Count == 0)                   throw new ArgumentException("an order needs at least one line");
        if (lineList.Count > 100)                  throw new ArgumentException("too many lines (max 100)");

        var duplicateSku = lineList.GroupBy(l => l.Sku).FirstOrDefault(g => g.Count() > 1);
        if (duplicateSku is not null)
            throw new ArgumentException($"duplicate sku '{duplicateSku.Key}' — merge the quantities first");

        var now = DateTime.UtcNow;

        var order = new Order
        {
            // Version 7 GUIDs are time-ordered, so inserts stay at the end of the
            // clustered index instead of fragmenting it. Free performance.
            Id             = Guid.CreateVersion7(),
            CustomerId     = customerId,
            CustomerEmail  = customerEmail,
            Currency       = currency,
            Status         = OrderStatus.Pending,
            IdempotencyKey = idempotencyKey,
            PlacedAtUtc    = now,
            UpdatedAtUtc   = now
        };

        order._lines.AddRange(lineList);

        order.Raise(new OrderPlaced
        {
            OrderId       = order.Id,
            CustomerId    = customerId,
            CustomerEmail = customerEmail,
            Total         = order.Total,
            Currency      = currency,
            OccurredAtUtc = now,
            Lines = lineList.Select(l => new OrderLineDto
            {
                Sku       = l.Sku,
                Name      = l.Name,
                Quantity  = l.Quantity,
                UnitPrice = l.UnitPrice
            }).ToList()
        });

        return order;
    }

    // ── State transitions ───────────────────────────────────────────────────
    //
    // Every transition is idempotent: calling it twice from the target state is
    // a no-op, not an exception. That matters because the event that triggers it
    // WILL sometimes be delivered twice (chapter 8).

    public void Confirm(string transactionId)
    {
        if (Status == OrderStatus.Confirmed) return;      // duplicate delivery. Fine.

        if (Status != OrderStatus.Pending)
            throw new InvalidOperationException($"cannot confirm an order in state {Status}");

        Status        = OrderStatus.Confirmed;
        TransactionId = transactionId;
        UpdatedAtUtc  = DateTime.UtcNow;

        Raise(new OrderConfirmed
        {
            OrderId       = Id,
            CustomerId    = CustomerId,
            TransactionId = transactionId,
            OccurredAtUtc = UpdatedAtUtc
        });
    }

    public void Cancel(CancellationReason reason, string detail)
    {
        if (Status == OrderStatus.Cancelled) return;      // duplicate delivery. Fine.

        // A shipped order cannot be cancelled — that is a return, a different process
        // with different money movements. Modelling it as "cancel" hides that fact.
        if (Status is OrderStatus.Shipped or OrderStatus.Delivered)
            throw new InvalidOperationException($"cannot cancel an order in state {Status}; use the returns flow");

        Status           = OrderStatus.Cancelled;
        CancellationNote = detail;
        UpdatedAtUtc     = DateTime.UtcNow;

        Raise(new OrderCancelled
        {
            OrderId       = Id,
            CustomerId    = CustomerId,
            Reason        = reason,
            ReasonDetail  = detail,
            OccurredAtUtc = UpdatedAtUtc
        });
    }

    public void MarkShipped()
    {
        if (Status == OrderStatus.Shipped) return;

        if (Status != OrderStatus.Confirmed)
            throw new InvalidOperationException($"cannot ship an order in state {Status}");

        Status       = OrderStatus.Shipped;
        UpdatedAtUtc = DateTime.UtcNow;
    }

    // ── Events ──────────────────────────────────────────────────────────────

    private void Raise(object e) => _domainEvents.Add(e);

    /// <summary>Called by infrastructure after the events have been copied into the outbox.</summary>
    public void ClearDomainEvents() => _domainEvents.Clear();
}

public sealed class OrderLine
{
    public string  Sku       { get; private init; } = "";
    public string  Name      { get; private init; } = "";
    public int     Quantity  { get; private init; }
    public decimal UnitPrice { get; private init; }

    public decimal LineTotal => Quantity * UnitPrice;

    private OrderLine() { }

    public static OrderLine Create(string sku, string name, int quantity, decimal unitPrice)
    {
        if (string.IsNullOrWhiteSpace(sku)) throw new ArgumentException("sku is required");
        if (quantity  <= 0) throw new ArgumentException("quantity must be positive");
        if (quantity  > 999) throw new ArgumentException("quantity looks like a typo (max 999)");
        if (unitPrice <  0) throw new ArgumentException("unitPrice cannot be negative");

        return new OrderLine { Sku = sku, Name = name, Quantity = quantity, UnitPrice = unitPrice };
    }
}

public enum OrderStatus
{
    /// <summary>Accepted, nothing reserved or charged yet. This is what `202 Accepted` means.</summary>
    Pending = 0,
    Confirmed = 1,
    Shipped = 2,
    Delivered = 3,
    Cancelled = 4
}
