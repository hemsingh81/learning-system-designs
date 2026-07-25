using Trading.Contracts.Events;

namespace Trading.OrderApi.Domain;

// ─────────────────────────────────────────────────────────────────────────────
// THE ORDER STATE MACHINE
//
// Getting these states right matters more than any other modelling decision in
// a trading system. Two rules drive the whole design:
//
//   1. EVERY transition is idempotent. The event that causes it will sometimes
//      arrive twice, and an order that flips Filled → Working on a redelivery
//      is a position the user cannot see.
//
//   2. `Unknown` is a REAL state. We sent the order and the broker did not
//      answer. It may or may not be live at the exchange. A system that only
//      models success and failure will eventually tell a user their order was
//      rejected while it is quietly working — and that is how people lose money.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class Order
{
    private readonly List<object> _domainEvents = [];
    private readonly List<FillRecord> _fills = [];

    public Guid       Id            { get; private set; }
    public Guid       UserId        { get; private set; }
    public string     ClientOrderId { get; private set; } = "";   // the idempotency key
    public string     Symbol        { get; private set; } = "";
    public OrderSide  Side          { get; private set; }
    public OrderType  Type          { get; private set; }
    public int        Quantity      { get; private set; }
    public decimal?   LimitPrice    { get; private set; }
    public decimal?   StopPrice     { get; private set; }
    public OrderState State         { get; private set; }

    public string?  ExchangeOrderId { get; private set; }
    public string?  RejectionReason { get; private set; }
    public DateTime CreatedAtUtc    { get; private set; }
    public DateTime UpdatedAtUtc    { get; private set; }

    public IReadOnlyList<FillRecord> Fills        => _fills;
    public IReadOnlyList<object>     DomainEvents => _domainEvents;

    public int     FilledQuantity  => _fills.Sum(f => f.Quantity);
    public int     RemainingQuantity => Quantity - FilledQuantity;
    public decimal AverageFillPrice =>
        FilledQuantity == 0 ? 0m
        : Math.Round(_fills.Sum(f => f.Price * f.Quantity) / FilledQuantity, 4, MidpointRounding.ToEven);

    /// <summary>True when nothing further can happen to this order.
    /// The client stops listening; the risk reservation is released.</summary>
    public bool IsTerminal => State is OrderState.Filled
                                    or OrderState.Cancelled
                                    or OrderState.Rejected
                                    or OrderState.Expired;

    private Order() { }

    // ── Creation ────────────────────────────────────────────────────────────

    public static Order Place(
        Guid      userId,
        string    clientOrderId,
        string    symbol,
        OrderSide side,
        OrderType type,
        int       quantity,
        decimal?  limitPrice = null,
        decimal?  stopPrice  = null)
    {
        if (string.IsNullOrWhiteSpace(clientOrderId))
            throw new ArgumentException("clientOrderId is required — it is the idempotency key");

        if (quantity <= 0)
            throw new ArgumentException("quantity must be positive");

        // A limit order without a limit price is a market order wearing a
        // disguise, and it will execute at a price the user did not intend.
        if (type is OrderType.Limit or OrderType.StopLimit && limitPrice is null or <= 0)
            throw new ArgumentException($"{type} orders require a positive limit price");

        if (type is OrderType.StopLoss or OrderType.StopLimit && stopPrice is null or <= 0)
            throw new ArgumentException($"{type} orders require a positive stop price");

        var now = DateTime.UtcNow;

        var order = new Order
        {
            Id            = Guid.CreateVersion7(),
            UserId        = userId,
            ClientOrderId = clientOrderId,
            Symbol        = symbol,
            Side          = side,
            Type          = type,
            Quantity      = quantity,
            LimitPrice    = limitPrice,
            StopPrice     = stopPrice,
            State         = OrderState.Received,
            CreatedAtUtc  = now,
            UpdatedAtUtc  = now
        };

        return order;
    }

    // ── Transitions ─────────────────────────────────────────────────────────

    public void MarkChecking()
    {
        if (State == OrderState.Checking) return;
        Transition(OrderState.Received, OrderState.Checking);
    }

    /// <summary>Risk approved it. Now it may be routed to the broker.</summary>
    public void MarkRouted()
    {
        if (State == OrderState.Routed) return;

        Transition(OrderState.Checking, OrderState.Routed);

        Raise(new OrderRouted
        {
            OrderId    = Id,
            UserId     = UserId,
            Symbol     = Symbol,
            Side       = Side,
            Type       = Type,
            Quantity   = Quantity,
            LimitPrice = LimitPrice,
            StopPrice  = StopPrice,
            OccurredAtUtc = UpdatedAtUtc
        });
    }

    /// <summary>The broker accepted it and it is live at the exchange.</summary>
    public void MarkWorking(string exchangeOrderId)
    {
        if (State == OrderState.Working) return;

        // Routed → Working is normal. Unknown → Working happens when the
        // reconciler discovers the order was live all along.
        if (State is not (OrderState.Routed or OrderState.Unknown))
            throw new InvalidOperationException($"cannot mark working from {State}");

        ExchangeOrderId = exchangeOrderId;
        SetState(OrderState.Working);

        Raise(new OrderAcknowledged
        {
            OrderId = Id, UserId = UserId, ExchangeOrderId = exchangeOrderId,
            OccurredAtUtc = UpdatedAtUtc
        });
    }

    /// <summary>
    /// Record a fill. Called once per partial fill, and idempotently — brokers
    /// resend fill messages, and counting one twice invents a position.
    /// </summary>
    public void ApplyFill(string fillId, int quantity, decimal price, DateTime executedAtUtc, decimal charges)
    {
        // IDEMPOTENCY. The broker's fill ID is the key. Without this check a
        // resent fill message doubles the user's position, and no error is raised
        // anywhere — the numbers are simply wrong from then on.
        if (_fills.Any(f => f.FillId == fillId)) return;

        if (State is OrderState.Cancelled or OrderState.Rejected)
            throw new InvalidOperationException($"cannot fill an order in state {State}");

        if (quantity > RemainingQuantity)
            throw new InvalidOperationException(
                $"fill of {quantity} exceeds remaining {RemainingQuantity} — " +
                "the broker and our record disagree, investigate before accepting");

        _fills.Add(new FillRecord(fillId, quantity, price, executedAtUtc, charges));

        SetState(RemainingQuantity == 0 ? OrderState.Filled : OrderState.PartiallyFilled);

        Raise(new OrderFilled
        {
            OrderId        = Id,
            UserId         = UserId,
            Symbol         = Symbol,
            Side           = Side,
            FillId         = fillId,
            Quantity       = quantity,
            Price          = price,
            Charges        = charges,
            IsComplete     = State == OrderState.Filled,
            ExecutedAtUtc  = executedAtUtc,
            OccurredAtUtc  = UpdatedAtUtc
        });
    }

    public void Reject(string reason)
    {
        if (State == OrderState.Rejected) return;

        // A partially filled order cannot be "rejected" — some of it really
        // traded. That is a cancellation of the remainder, which is a different
        // fact and a different number on the user's contract note.
        if (FilledQuantity > 0)
            throw new InvalidOperationException(
                "cannot reject a partially filled order; cancel the remainder instead");

        RejectionReason = reason;
        SetState(OrderState.Rejected);

        Raise(new OrderRejected
        {
            OrderId = Id, UserId = UserId, Reason = reason, OccurredAtUtc = UpdatedAtUtc
        });
    }

    public void Cancel(string reason)
    {
        if (State == OrderState.Cancelled) return;

        if (IsTerminal)
            throw new InvalidOperationException($"cannot cancel an order in state {State}");

        SetState(OrderState.Cancelled);

        Raise(new OrderCancelled
        {
            OrderId          = Id,
            UserId           = UserId,
            Reason           = reason,
            FilledQuantity   = FilledQuantity,   // may be > 0: a partial cancel
            OccurredAtUtc    = UpdatedAtUtc
        });
    }

    /// <summary>
    /// THE STATE THAT MATTERS MOST.
    ///
    /// We sent the order and the broker did not answer. It may be live at the
    /// exchange, or it may never have arrived.
    ///
    /// We do NOT resend — a duplicate order is a real, unwanted position that
    /// costs real money to unwind, and the market moves while you find out.
    /// We do NOT mark it rejected — that tells the user nothing happened, and
    /// they may place the order again.
    ///
    /// We record honestly that we do not know, and a reconciler asks the broker
    /// using our client order ID.
    /// </summary>
    public void MarkUnknown(string reason)
    {
        if (State == OrderState.Unknown) return;
        if (IsTerminal) return;                   // already resolved. Leave it alone.

        RejectionReason = reason;
        SetState(OrderState.Unknown);

        Raise(new OrderStatusUnknown
        {
            OrderId       = Id,
            UserId        = UserId,
            ClientOrderId = ClientOrderId,        // how the reconciler will ask
            Reason        = reason,
            OccurredAtUtc = UpdatedAtUtc
        });
    }

    // ── Plumbing ────────────────────────────────────────────────────────────

    private void Transition(OrderState from, OrderState to)
    {
        if (State != from)
            throw new InvalidOperationException($"cannot go from {State} to {to}; expected {from}");

        SetState(to);
    }

    private void SetState(OrderState state)
    {
        State        = state;
        UpdatedAtUtc = DateTime.UtcNow;
    }

    private void Raise(object e) => _domainEvents.Add(e);

    public void ClearDomainEvents() => _domainEvents.Clear();
}

public sealed record FillRecord(
    string   FillId,
    int      Quantity,
    decimal  Price,
    DateTime ExecutedAtUtc,
    decimal  Charges);

public enum OrderState
{
    /// <summary>Accepted by the API. Not yet risk-checked.</summary>
    Received = 0,

    /// <summary>In the risk gate.</summary>
    Checking = 1,

    /// <summary>Risk approved. On its way to the broker.</summary>
    Routed = 2,

    /// <summary>Live at the exchange.</summary>
    Working = 3,

    PartiallyFilled = 4,
    Filled = 5,
    Cancelled = 6,
    Rejected = 7,
    Expired = 8,

    /// <summary>We sent it; the broker did not answer. Status genuinely unknown.
    /// A human or the reconciler resolves this. Never guessed.</summary>
    Unknown = 9
}

public enum OrderSide { Buy, Sell }

public enum OrderType { Market, Limit, StopLoss, StopLimit }
