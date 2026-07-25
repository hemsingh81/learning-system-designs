using Ecommerce.Contracts.Events;
using Ecommerce.Inventory.Infrastructure;
using MassTransit;
using Microsoft.EntityFrameworkCore;

namespace Ecommerce.Inventory.Consumers;

// ─────────────────────────────────────────────────────────────────────────────
// THE COMPENSATING ACTION
//
// Payment failed, so the stock we reserved must go back on sale.
//
// Notice what Inventory does NOT do: it does not ask why payment failed, it does
// not call Payments, and it does not know Ordering exists. It listens for one
// fact and reverses one action. That is choreography (chapter 7).
//
// COMPENSATION IS THE EASIEST PLACE IN THE WHOLE SYSTEM TO CREATE A BUG.
// A "do" step that runs twice usually fails loudly (a duplicate key, a rejected
// charge). An "undo" step that runs twice succeeds silently and quietly invents
// inventory you do not have. Nobody notices until a stock count.
//
// Hence three guards below, and none of them are optional.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class PaymentFailedConsumer(
    InventoryDbContext db,
    ILogger<PaymentFailedConsumer> log) : IConsumer<PaymentFailed>
{
    private const string ConsumerName = nameof(PaymentFailedConsumer);

    public async Task Consume(ConsumeContext<PaymentFailed> context)
    {
        var msg       = context.Message;
        var messageId = context.MessageId
            ?? throw new InvalidOperationException("MessageId is required for idempotency");

        // ── GUARD 1: message-level. Have we handled this exact message? ─────
        if (await db.InboxMessages.AnyAsync(
                x => x.MessageId == messageId && x.Consumer == ConsumerName,
                context.CancellationToken))
        {
            return;
        }

        var reservation = await db.Reservations
            .Include(r => r.Lines)
            .FirstOrDefaultAsync(r => r.OrderId == msg.OrderId, context.CancellationToken);

        // ── GUARD 2: nothing to undo ────────────────────────────────────────
        // Stock was never reserved (StockRejected came first), so there is no
        // reservation. Releasing here would credit stock we never took.
        if (reservation is null)
        {
            log.LogInformation(
                "No reservation for order {OrderId} — nothing to compensate", msg.OrderId);

            await MarkProcessedAsync(messageId, context.CancellationToken);
            return;
        }

        // ── GUARD 3: state-level. Already undone? ───────────────────────────
        // This is the one that saves you. The sweeper may have expired this
        // reservation a second ago, or a duplicate PaymentFailed may have arrived
        // with a different MessageId (a republish after a producer restart).
        // Guard 1 would not catch that; this does.
        if (reservation.IsReleased)
        {
            log.LogInformation(
                "Reservation for order {OrderId} already released ({Reason}) — no double release",
                msg.OrderId, reservation.ReleaseReason);

            await MarkProcessedAsync(messageId, context.CancellationToken);
            return;
        }

        // Committed stock has shipped. It cannot be released — that is a return,
        // a different business process with different money movement.
        if (reservation.IsCommitted)
        {
            log.LogError(
                "PaymentFailed for order {OrderId} whose stock is already COMMITTED. " +
                "Goods may have shipped without payment — escalating for manual review.",
                msg.OrderId);

            db.OutboxMessages.Add(OutboxMessage.From(new ManualReviewRequired
            {
                OrderId       = msg.OrderId,
                Reason        = "payment failed after stock was committed",
                OccurredAtUtc = DateTime.UtcNow
            }));

            await MarkProcessedAsync(messageId, context.CancellationToken);
            return;
        }

        // ── Do the compensation ─────────────────────────────────────────────
        foreach (var line in reservation.Lines.OrderBy(l => l.Sku, StringComparer.Ordinal))
        {
            var stock = await db.Stocks.FirstAsync(s => s.Sku == line.Sku, context.CancellationToken);
            stock.Release(line.Quantity);
        }

        reservation.Release(ReleaseReason.PaymentFailed);

        db.OutboxMessages.Add(OutboxMessage.From(new StockReleased
        {
            OrderId       = msg.OrderId,
            Lines         = reservation.Lines.Select(l => new ReservedLineDto
                            {
                                Sku = l.Sku, Quantity = l.Quantity
                            }).ToList(),
            Reason        = ReleaseReason.PaymentFailed,
            OccurredAtUtc = DateTime.UtcNow
        }));

        db.InboxMessages.Add(new InboxMessage
        {
            MessageId      = messageId,
            Consumer       = ConsumerName,
            ProcessedAtUtc = DateTime.UtcNow
        });

        try
        {
            await db.SaveChangesAsync(context.CancellationToken);

            log.LogInformation("Released {Count} line(s) for failed order {OrderId}",
                reservation.Lines.Count, msg.OrderId);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("PK_InboxMessages"))
        {
            // Another instance won the race. Its transaction did the release.
            log.LogInformation("Concurrent duplicate release for {OrderId} discarded", msg.OrderId);
        }
    }

    private async Task MarkProcessedAsync(Guid messageId, CancellationToken ct)
    {
        db.InboxMessages.Add(new InboxMessage
        {
            MessageId      = messageId,
            Consumer       = ConsumerName,
            ProcessedAtUtc = DateTime.UtcNow
        });

        try
        {
            await db.SaveChangesAsync(ct);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("PK_InboxMessages"))
        {
            // Already recorded by a concurrent instance. Fine.
        }
    }
}
