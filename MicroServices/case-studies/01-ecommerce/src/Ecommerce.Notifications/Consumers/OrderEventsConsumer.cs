using Ecommerce.Contracts.Events;
using Ecommerce.Notifications.Hubs;
using MassTransit;
using Microsoft.AspNetCore.SignalR;

namespace Ecommerce.Notifications.Consumers;

// ─────────────────────────────────────────────────────────────────────────────
// THE BRIDGE BETWEEN EAST-WEST AND NORTH-SOUTH
//
// This is where an internal event (async, service-to-service) becomes a push to
// a browser (north-south). It is the piece that makes eventual consistency
// acceptable to a human being.
//
// Without it, the user sees "Processing…" and must refresh to learn what
// happened. With it, the page updates itself about a second later.
//
// One consumer class handles several events, because they are all "tell the
// customer what happened to their order". Splitting them into three classes
// would triple the boilerplate for no benefit.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class OrderEventsConsumer(
    IHubContext<OrderHub, IOrderClient> hub,
    IEmailSender email,
    IInboxStore inbox,
    ILogger<OrderEventsConsumer> log)
    : IConsumer<OrderPlaced>,
      IConsumer<OrderConfirmed>,
      IConsumer<OrderCancelled>
{
    // ── Order accepted ──────────────────────────────────────────────────────

    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        var m = context.Message;

        if (!await inbox.TryClaimAsync(context.MessageId, nameof(OrderPlaced), context.CancellationToken))
            return;   // duplicate

        // Push first: it is instant, and it is what the user is staring at.
        await hub.Clients.Group(UserGroup(m.CustomerId)).OrderStatusChanged(new OrderStatusUpdate
        {
            OrderId = m.OrderId,
            Status  = "Pending",
            Message = "We have your order and are confirming it now."
        });

        // Email second: slower, and the user is not waiting for it.
        //
        // NOTE: the email is NOT in a transaction with the inbox row. If the
        // process dies between them, a retry sends a second email. That is the
        // trade made here — one duplicate email is cheaper than the machinery
        // needed to prevent it. Money would deserve the opposite call.
        await email.SendAsync(new EmailMessage
        {
            To       = m.CustomerEmail,
            Template = "order-received",
            Data     = new { m.OrderId, m.Total, m.Currency, ItemCount = m.Lines.Count }
        }, context.CancellationToken);

        log.LogInformation("Notified customer {CustomerId} of order {OrderId}", m.CustomerId, m.OrderId);
    }

    // ── Order confirmed — the moment that closes the consistency gap ────────

    public async Task Consume(ConsumeContext<OrderConfirmed> context)
    {
        var m = context.Message;

        if (!await inbox.TryClaimAsync(context.MessageId, nameof(OrderConfirmed), context.CancellationToken))
            return;

        // THIS is the payoff of the whole async design. The user placed the order
        // ~1 second ago, saw "Processing", and their page now updates itself.
        // No polling, no refresh, no support ticket about a "missing" order.
        await hub.Clients.Group(UserGroup(m.CustomerId)).OrderStatusChanged(new OrderStatusUpdate
        {
            OrderId  = m.OrderId,
            Status   = "Confirmed",
            Message  = "Payment received. Your order is confirmed.",
            IsFinal  = false        // still to ship
        });

        await email.SendAsync(new EmailMessage
        {
            To       = await ResolveEmailAsync(m.CustomerId, context.CancellationToken),
            Template = "order-confirmed",
            Data     = new { m.OrderId, m.TransactionId }
        }, context.CancellationToken);
    }

    // ── Order cancelled — the honest message ────────────────────────────────

    public async Task Consume(ConsumeContext<OrderCancelled> context)
    {
        var m = context.Message;

        if (!await inbox.TryClaimAsync(context.MessageId, nameof(OrderCancelled), context.CancellationToken))
            return;

        // Say what actually happened and what to do next. "Something went wrong"
        // generates a support ticket; "your card was declined, try another" does not.
        var (message, template) = m.Reason switch
        {
            CancellationReason.OutOfStock =>
                ("Sorry — an item sold out before we could confirm your order. You have not been charged.",
                 "order-cancelled-stock"),

            CancellationReason.PaymentDeclined =>
                ("Your payment was declined. Please try another card — your basket is saved.",
                 "order-cancelled-payment"),

            CancellationReason.PaymentTimeout =>
                ("We could not confirm your payment in time. Please try again — you have not been charged.",
                 "order-cancelled-timeout"),

            CancellationReason.FraudSuspected =>
                // Deliberately vague. Never tell a suspected fraudster what tripped the check.
                ("We could not process this order. Please contact support.",
                 "order-cancelled-review"),

            _ => ("Your order could not be completed. You have not been charged.",
                  "order-cancelled-generic")
        };

        await hub.Clients.Group(UserGroup(m.CustomerId)).OrderStatusChanged(new OrderStatusUpdate
        {
            OrderId  = m.OrderId,
            Status   = "Cancelled",
            Message  = message,
            IsFinal  = true,
            CanRetry = m.Reason is CancellationReason.PaymentDeclined
                                or CancellationReason.PaymentTimeout
        });

        await email.SendAsync(new EmailMessage
        {
            To       = await ResolveEmailAsync(m.CustomerId, context.CancellationToken),
            Template = template,
            Data     = new { m.OrderId, Reason = message }
        }, context.CancellationToken);

        log.LogInformation("Order {OrderId} cancelled ({Reason}), customer notified",
            m.OrderId, m.Reason);
    }

    // Group per user, never a broadcast. Broadcasting order updates to every
    // connected client would be a data-protection incident, not just a bug.
    private static string UserGroup(Guid customerId) => $"user:{customerId}";

    private Task<string> ResolveEmailAsync(Guid customerId, CancellationToken ct) =>
        // In a real service this reads a local snapshot kept up to date by
        // CustomerChanged events — NOT a synchronous call to Customers, which
        // would put a live dependency back into an async consumer.
        Task.FromResult($"{customerId}@example.com");
}

// ── The typed hub contract ──────────────────────────────────────────────────
// A typed hub means a rename is a compile error rather than a silent no-op in
// the browser. Untyped SendAsync("OrderStatusChanged", …) fails silently forever.

public interface IOrderClient
{
    Task OrderStatusChanged(OrderStatusUpdate update);
}

public sealed record OrderStatusUpdate
{
    public required Guid   OrderId { get; init; }
    public required string Status  { get; init; }
    public required string Message { get; init; }

    /// <summary>Tells the UI it can stop listening for this order.</summary>
    public bool IsFinal  { get; init; }

    /// <summary>Drives whether a "Try another card" button is shown.</summary>
    public bool CanRetry { get; init; }
}
