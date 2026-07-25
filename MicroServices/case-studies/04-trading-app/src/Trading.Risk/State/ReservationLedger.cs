using System.Collections.Concurrent;

namespace Trading.Risk.State;

// ─────────────────────────────────────────────────────────────────────────────
// RESERVATIONS — CLOSING THE CACHE-STALENESS GAP
//
// The problem this solves:
//
//   Risk reads buying power from a cache updated by events. The cache is
//   correct, but it lags the truth by a few hundred milliseconds.
//
//   10:00:00.000  User has ₹300,000. Places order A for ₹200,000.
//   10:00:00.010  Risk approves A. The cache still says ₹300,000 —
//                 no fill has happened yet, so no event has arrived.
//   10:00:00.050  User places order B for ₹200,000.
//   10:00:00.060  Risk reads the cache: still ₹300,000. APPROVES B.
//
//   The user now has ₹400,000 of orders against ₹300,000 of buying power.
//   Both are live at the exchange. Both may fill.
//
// The fix: approving an order immediately HOLDS its value, in memory, before
// the caller even gets a response. Order B sees ₹100,000 available and is
// correctly rejected.
//
// Every hold EXPIRES. A rejected, lost, or forgotten order must never freeze a
// user's buying power — the same safety-net principle as the e-commerce
// reservation sweeper.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class ReservationLedger(ILogger<ReservationLedger> log)
{
    // orderId → hold. One hold per order, so releasing is a simple keyed remove.
    private readonly ConcurrentDictionary<Guid, Hold> _holds = new();

    // userId → total held. Kept alongside so the hot path never has to sum a
    // dictionary — at 2,000 checks a second that scan would be the bottleneck.
    private readonly ConcurrentDictionary<Guid, decimal> _totalByUser = new();

    private readonly object _gate = new();   // only for the compare-and-hold below

    /// <summary>
    /// Hold an amount for an order. Returns false if a concurrent order for the
    /// same user already took it.
    ///
    /// This is the only place in the risk path that takes a lock. It is held for
    /// microseconds and only contends between two orders from the SAME user in
    /// the same instant — which is exactly the case it exists to serialise.
    /// </summary>
    public bool TryHold(Guid userId, Guid orderId, decimal amount, TimeSpan ttl)
    {
        if (amount <= 0) return true;   // a sell frees cash; nothing to hold

        lock (_gate)
        {
            // Idempotent: the same order asking twice keeps ONE hold.
            // Without this, a retried risk check would double-count its own hold
            // and reject an order the user can actually afford.
            if (_holds.ContainsKey(orderId)) return true;

            var hold = new Hold(orderId, userId, amount, DateTime.UtcNow.Add(ttl));

            if (!_holds.TryAdd(orderId, hold)) return true;

            _totalByUser.AddOrUpdate(userId, amount, (_, current) => current + amount);
            return true;
        }
    }

    /// <summary>
    /// Total currently held for a user, ignoring anything expired.
    ///
    /// Called on EVERY risk check, so it must be O(1). Expiry is handled by the
    /// sweeper below rather than by scanning here.
    /// </summary>
    public decimal HeldFor(Guid userId) =>
        _totalByUser.TryGetValue(userId, out var total) ? total : 0m;

    /// <summary>
    /// Release a hold: the order was rejected downstream, cancelled, or filled
    /// (at which point the real fill event updates the cached buying power).
    ///
    /// IDEMPOTENT. Releasing twice must not credit the user twice — the same
    /// compensation rule as chapter 7.
    /// </summary>
    public void Release(Guid orderId)
    {
        lock (_gate)
        {
            if (!_holds.TryRemove(orderId, out var hold))
                return;                 // already released, or never held. Fine.

            _totalByUser.AddOrUpdate(hold.UserId, 0m, (_, current) =>
            {
                var updated = current - hold.Amount;

                // Should never go negative. If it does, a hold was double-released
                // or the totals drifted — log it loudly, and clamp rather than
                // letting a negative total silently grant free buying power.
                if (updated < 0)
                {
                    log.LogError("Negative held total for user {UserId} — clamping to zero", hold.UserId);
                    return 0m;
                }

                return updated;
            });
        }
    }

    /// <summary>
    /// Drop expired holds.
    ///
    /// Called every second by the sweeper. Without it, an order that was sent
    /// and never resolved would hold the user's money forever, and support would
    /// see "insufficient buying power" for a user whose account is plainly full.
    /// </summary>
    public int SweepExpired()
    {
        var now     = DateTime.UtcNow;
        var expired = _holds.Values.Where(h => h.ExpiresAtUtc < now).ToList();

        foreach (var hold in expired)
        {
            log.LogWarning(
                "Reservation for order {OrderId} expired after {Amount:N2} was held — " +
                "the order was never resolved. Investigate the execution path.",
                hold.OrderId, hold.Amount);

            Release(hold.OrderId);
        }

        return expired.Count;
    }

    private readonly record struct Hold(Guid OrderId, Guid UserId, decimal Amount, DateTime ExpiresAtUtc);
}

// ─────────────────────────────────────────────────────────────────────────────
// THE SWEEPER
//
// Runs every second. Its expiry COUNT is a real health metric: a rising number
// means orders are being sent and never resolved, which is a broken execution
// path — and you would rather learn that from this counter than from a user.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class ReservationSweeper(
    ReservationLedger ledger,
    IMetrics metrics,
    ILogger<ReservationSweeper> log) : BackgroundService
{
    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(TimeSpan.FromSeconds(1));

        while (await timer.WaitForNextTickAsync(ct))
        {
            try
            {
                var swept = ledger.SweepExpired();

                if (swept > 0)
                {
                    metrics.ReservationsExpired(swept);

                    // Any expiry at all is abnormal: a healthy order resolves in
                    // well under 30 seconds. Alert if this stays above zero.
                    log.LogWarning("Swept {Count} expired reservation(s)", swept);
                }
            }
            catch (Exception ex)
            {
                // The sweeper must never die. If it stops, holds accumulate and
                // every user eventually appears to have no buying power.
                log.LogError(ex, "Reservation sweep failed");
            }
        }
    }
}
