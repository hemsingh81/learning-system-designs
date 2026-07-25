using Ecommerce.Contracts.Events;
using Ecommerce.Inventory.Domain;
using Ecommerce.Inventory.Infrastructure;
using MassTransit;
using Microsoft.EntityFrameworkCore;

namespace Ecommerce.Inventory.Consumers;

// ─────────────────────────────────────────────────────────────────────────────
// RESERVE STOCK WHEN AN ORDER IS PLACED
//
// This is the "do" half of the saga. Its "undo" half is PaymentFailedConsumer.
//
// Three things make it production-safe, and all three are easy to leave out:
//   1. An idempotency check, because the message WILL arrive twice.
//   2. A database-level guard against overselling under concurrency.
//   3. An expiry on the reservation, so a lost event cannot hold stock forever.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class OrderPlacedConsumer(
    InventoryDbContext db,
    ILogger<OrderPlacedConsumer> log) : IConsumer<OrderPlaced>
{
    private const string ConsumerName = nameof(OrderPlacedConsumer);

    /// <summary>How long stock is held before the sweeper may reclaim it.
    /// Must be comfortably longer than the worst realistic payment time.</summary>
    private static readonly TimeSpan ReservationTtl = TimeSpan.FromMinutes(15);

    public async Task Consume(ConsumeContext<OrderPlaced> context)
    {
        var msg       = context.Message;
        var messageId = context.MessageId
            ?? throw new InvalidOperationException(
                "MessageId is missing. Without it, idempotency is impossible — " +
                "check that the outbox relay sets it (chapter 8).");

        // ── 1. Have we already processed this message? ──────────────────────
        // The fast path. The real guarantee is the primary key at step 5.
        var alreadyProcessed = await db.InboxMessages.AnyAsync(
            x => x.MessageId == messageId && x.Consumer == ConsumerName,
            context.CancellationToken);

        if (alreadyProcessed)
        {
            log.LogInformation("Message {MessageId} already processed, skipping", messageId);
            return;   // A duplicate is normal operation, not an error.
        }

        // ── 2. Try to reserve every line ────────────────────────────────────
        var rejected = new List<RejectedLineDto>();
        var reserved = new List<ReservedLineDto>();

        // Ordered by SKU so concurrent orders always take row locks in the SAME
        // order. Without this, two orders containing the same two SKUs in opposite
        // order can deadlock — a bug that only appears under load, in production.
        foreach (var line in msg.Lines.OrderBy(l => l.Sku, StringComparer.Ordinal))
        {
            var stock = await db.Stocks
                .FirstOrDefaultAsync(s => s.Sku == line.Sku, context.CancellationToken);

            if (stock is null)
            {
                rejected.Add(new RejectedLineDto { Sku = line.Sku, Requested = line.Quantity, Available = 0 });
                continue;
            }

            if (!stock.TryReserve(line.Quantity))
                rejected.Add(new RejectedLineDto
                {
                    Sku = line.Sku, Requested = line.Quantity, Available = stock.Available
                });
            else
                reserved.Add(new ReservedLineDto { Sku = line.Sku, Quantity = line.Quantity });
        }

        var now = DateTime.UtcNow;

        // ── 3. All or nothing ───────────────────────────────────────────────
        // A partly-reserved order is worse than a rejected one: the customer gets
        // half their basket, and the other half is held by nobody.
        if (rejected.Count > 0)
        {
            // Undo anything reserved in this pass before publishing the rejection.
            foreach (var r in reserved)
            {
                var stock = await db.Stocks.FirstAsync(s => s.Sku == r.Sku, context.CancellationToken);
                stock.Release(r.Quantity);
            }

            db.OutboxMessages.Add(OutboxMessage.From(new StockRejected
            {
                OrderId       = msg.OrderId,
                RejectedLines = rejected,
                OccurredAtUtc = now
            }));

            log.LogInformation("Order {OrderId} rejected: {Count} line(s) short", msg.OrderId, rejected.Count);
        }
        else
        {
            // ── 4. Record the reservation, WITH AN EXPIRY ───────────────────
            // The expiry is the safety net for a lost PaymentFailed event.
            // Without it, one dropped message removes stock from sale permanently.
            db.Reservations.Add(Reservation.Create(
                orderId:      msg.OrderId,
                lines:        reserved.Select(r => (r.Sku, r.Quantity)),
                expiresAtUtc: now.Add(ReservationTtl)));

            db.OutboxMessages.Add(OutboxMessage.From(new StockReserved
            {
                OrderId       = msg.OrderId,
                Lines         = reserved,
                ExpiresAtUtc  = now.Add(ReservationTtl),
                OccurredAtUtc = now
            }));

            log.LogInformation("Reserved {Count} line(s) for order {OrderId}", reserved.Count, msg.OrderId);
        }

        // ── 5. Mark the message processed, in the SAME transaction ──────────
        db.InboxMessages.Add(new InboxMessage
        {
            MessageId      = messageId,
            Consumer       = ConsumerName,
            ProcessedAtUtc = now
        });

        try
        {
            // Stock change + outcome event + inbox row: one commit.
            // If the process dies before this line, NOTHING happened and the
            // broker's redelivery reprocesses cleanly.
            await db.SaveChangesAsync(context.CancellationToken);
        }
        catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("PK_InboxMessages"))
        {
            // Two instances raced past step 1 and both did the work. The primary
            // key on (MessageId, Consumer) is the real guarantee, and it just fired.
            // The other instance's transaction committed; ours rolled back entirely.
            // Nothing to do — and do NOT rethrow, or the broker retries a third time.
            log.LogInformation("Concurrent duplicate of {MessageId} lost the race, discarding", messageId);
        }
        catch (DbUpdateConcurrencyException)
        {
            // Someone else changed the same stock row between our read and write.
            // Rethrow so the broker retries — the retry re-reads current stock and
            // decides again. This is optimistic concurrency doing its job.
            log.LogWarning("Concurrent stock update for order {OrderId}, will retry", msg.OrderId);
            throw;
        }
    }
}
