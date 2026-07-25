using System.Diagnostics;
using Trading.Contracts;
using Trading.Risk.State;

namespace Trading.Risk.Checks;

// ─────────────────────────────────────────────────────────────────────────────
// THE ONLY SYNCHRONOUS GATE IN THE SYSTEM
//
// Budget: 8 milliseconds, p99. Everything here is shaped by that number.
//
//   NO database queries      a 3ms query is 37% of the budget
//   NO HTTP calls            a 20ms call is 250% of the budget
//   NO async I/O at all      this method is deliberately synchronous
//   NO allocations in the    the GC is a latency spike you cannot schedule
//      happy path
//
// And one rule that matters more than the speed:
//
//   FAIL CLOSED. If we cannot check, we REJECT.
//
// This is the exact opposite of the e-commerce case study, where an unavailable
// Inventory service still lets the sale through. Here, an unchecked order is a
// regulatory incident and a position nobody authorised.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class RiskEngine(
    IReadOnlyList<IRiskCheck> checks,
    RiskStateCache cache,
    ReservationLedger reservations,
    IKillSwitch killSwitch,
    IMetrics metrics,
    ILogger<RiskEngine> log)
{
    /// <summary>
    /// Decide whether an order may proceed.
    ///
    /// SYNCHRONOUS ON PURPOSE. There is no `async` and no `await` here: every
    /// input is already in memory, and introducing a Task would add scheduling
    /// overhead and an invitation for someone to await a network call later.
    /// </summary>
    public RiskDecision Check(OrderRequest order)
    {
        var sw = Stopwatch.GetTimestamp();

        try
        {
            // ── 0. KILL SWITCH, first and cheapest ──────────────────────────
            // Must be the very first check. When someone hits the switch, they
            // need trading to stop NOW, not after five other checks have run.
            if (killSwitch.IsActive(order.UserId, order.Symbol, out var haltReason))
            {
                return Reject(RiskRejectionReason.TradingHalted, haltReason);
            }

            // ── 1. Load the user's state from memory ────────────────────────
            // Updated by events (see Consumers/), never fetched here. A
            // synchronous read of Positions or Ledger would blow the budget
            // three times over — that trade is explained in the README.
            if (!cache.TryGetUser(order.UserId, out var state))
            {
                // We have NO state for this user. We cannot check them.
                // FAIL CLOSED: reject. Do not assume they are fine.
                log.LogWarning("No risk state for user {UserId} — rejecting (fail closed)", order.UserId);

                return Reject(RiskRejectionReason.StateUnavailable,
                    "risk state unavailable, please retry in a moment");
            }

            // ── 2. Is the price we are validating against still fresh? ──────
            // A stale price makes the collar check meaningless: a fat-finger
            // order would be measured against a price from ten minutes ago.
            if (!cache.TryGetPrice(order.Symbol, out var price) || price.IsStale)
            {
                return Reject(RiskRejectionReason.NoMarketData,
                    $"no fresh price for {order.Symbol}");
            }

            // ── 3. Run every check ──────────────────────────────────────────
            // One class per rule. Regulators ask "what does your position-limit
            // rule do?", and the answer is a file, not a search through a method.
            var context = new RiskContext
            {
                Order        = order,
                UserState    = state,
                Price        = price,
                Reservations = reservations
            };

            foreach (var check in checks)
            {
                var result = check.Evaluate(context);

                if (!result.Passed)
                {
                    log.LogInformation("Order rejected by {Check} for user {UserId}: {Reason}",
                        check.Name, order.UserId, result.Detail);

                    metrics.RiskRejection(check.Name);
                    return Reject(result.Reason, result.Detail);
                }
            }

            // ── 4. RESERVE the buying power ─────────────────────────────────
            //
            // This is what closes the cache-staleness gap.
            //
            // Without it: a user places two orders 50ms apart. The fill event
            // for the first has not arrived, so the cache still shows the old
            // buying power, and BOTH orders pass a check only one should.
            //
            // With it: approving the first order immediately holds its value,
            // so the second sees the reduced amount straight away.
            //
            // The hold EXPIRES, so a rejected or lost order cannot freeze a
            // user's buying power forever — the same sweeper principle as the
            // e-commerce reservation.
            var required = order.EstimatedValue(price.Last);

            if (!reservations.TryHold(order.UserId, order.Id, required, TimeSpan.FromSeconds(30)))
            {
                // Lost a race with a concurrent order for the same user.
                return Reject(RiskRejectionReason.InsufficientBuyingPower,
                    "buying power was consumed by another in-flight order");
            }

            metrics.RiskApproved();
            return RiskDecision.Approved(reservationId: order.Id, heldAmount: required);
        }
        catch (Exception ex)
        {
            // ── FAIL CLOSED ─────────────────────────────────────────────────
            // Any unexpected exception means we did not complete the check.
            // An unchecked order must never be allowed through, whatever broke.
            log.LogError(ex, "Risk check threw for user {UserId} — rejecting (fail closed)", order.UserId);

            metrics.RiskError();
            return Reject(RiskRejectionReason.CheckFailed, "risk check could not be completed");
        }
        finally
        {
            var elapsed = Stopwatch.GetElapsedTime(sw);
            metrics.RiskLatency(elapsed);

            // Alert on our own budget. If this fires, something has crept into
            // the hot path — usually a database call added "just for one thing".
            if (elapsed.TotalMilliseconds > 8)
            {
                log.LogWarning("Risk check took {Ms:F2}ms — over the 8ms budget",
                    elapsed.TotalMilliseconds);
            }
        }
    }

    /// <summary>Release a hold when an order is rejected downstream, cancelled,
    /// or filled. Idempotent — releasing twice must not credit twice.</summary>
    public void Release(Guid orderId) => reservations.Release(orderId);

    private static RiskDecision Reject(RiskRejectionReason reason, string detail) =>
        RiskDecision.Rejected(reason, detail);
}

// ─────────────────────────────────────────────────────────────────────────────
// ONE CHECK PER FILE. This interface is why that is possible.
// ─────────────────────────────────────────────────────────────────────────────

public interface IRiskCheck
{
    string Name { get; }

    /// <summary>Synchronous and allocation-light. Anything doing I/O here is a bug.</summary>
    CheckResult Evaluate(in RiskContext context);
}

public readonly record struct CheckResult
{
    public bool                 Passed { get; private init; }
    public RiskRejectionReason  Reason { get; private init; }
    public string               Detail { get; private init; }

    public static CheckResult Pass() => new() { Passed = true, Detail = "" };

    public static CheckResult Fail(RiskRejectionReason reason, string detail) =>
        new() { Passed = false, Reason = reason, Detail = detail };
}

public readonly record struct RiskContext
{
    public required OrderRequest      Order        { get; init; }
    public required UserRiskState     UserState    { get; init; }
    public required PriceSnapshot     Price        { get; init; }
    public required ReservationLedger Reservations { get; init; }
}

// ─────────────────────────────────────────────────────────────────────────────
// EXAMPLE CHECKS
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>Can the user afford it, counting money already held by in-flight orders?</summary>
public sealed class BuyingPowerCheck : IRiskCheck
{
    public string Name => "buying-power";

    public CheckResult Evaluate(in RiskContext ctx)
    {
        if (ctx.Order.Side == OrderSide.Sell) return CheckResult.Pass();   // selling frees cash

        var required = ctx.Order.EstimatedValue(ctx.Price.Last);

        // Subtract what other in-flight orders already hold. Checking the raw
        // balance would let five concurrent orders each spend the same rupees.
        var available = ctx.UserState.BuyingPower - ctx.Reservations.HeldFor(ctx.Order.UserId);

        return required <= available
            ? CheckResult.Pass()
            : CheckResult.Fail(RiskRejectionReason.InsufficientBuyingPower,
                $"required {required:N2}, available {available:N2}");
    }
}

/// <summary>
/// The fat-finger guard: reject a price far away from the market.
///
/// This is the check that stops someone typing 28410 instead of 2841. It has
/// saved more money than every other rule in this folder combined.
/// </summary>
public sealed class PriceCollarCheck : IRiskCheck
{
    private const decimal MaxDeviationPercent = 10m;

    public string Name => "price-collar";

    public CheckResult Evaluate(in RiskContext ctx)
    {
        if (ctx.Order.Type != OrderType.Limit) return CheckResult.Pass();

        var market    = ctx.Price.Last;
        var limit     = ctx.Order.LimitPrice!.Value;
        var deviation = Math.Abs((limit - market) / market) * 100m;

        return deviation <= MaxDeviationPercent
            ? CheckResult.Pass()
            : CheckResult.Fail(RiskRejectionReason.PriceOutOfRange,
                $"limit {limit:N2} is {deviation:F1}% from the market price {market:N2} " +
                $"(maximum {MaxDeviationPercent}%)");
    }
}

/// <summary>Cap the total position in one symbol, counting in-flight orders.</summary>
public sealed class PositionLimitCheck : IRiskCheck
{
    public string Name => "position-limit";

    public CheckResult Evaluate(in RiskContext ctx)
    {
        var current = ctx.UserState.PositionIn(ctx.Order.Symbol);
        var delta   = ctx.Order.Side == OrderSide.Buy ? ctx.Order.Quantity : -ctx.Order.Quantity;
        var after   = current + delta;

        var limit = ctx.UserState.PositionLimitFor(ctx.Order.Symbol);

        return Math.Abs(after) <= limit
            ? CheckResult.Pass()
            : CheckResult.Fail(RiskRejectionReason.PositionLimitExceeded,
                $"position would become {after}, limit is {limit}");
    }
}

public sealed record RiskDecision
{
    public required bool        IsApproved    { get; init; }
    public RiskRejectionReason? Reason        { get; init; }
    public string?              Detail        { get; init; }
    public Guid?                ReservationId { get; init; }
    public decimal?             HeldAmount    { get; init; }

    public static RiskDecision Approved(Guid reservationId, decimal heldAmount) =>
        new() { IsApproved = true, ReservationId = reservationId, HeldAmount = heldAmount };

    public static RiskDecision Rejected(RiskRejectionReason reason, string detail) =>
        new() { IsApproved = false, Reason = reason, Detail = detail };
}

public enum RiskRejectionReason
{
    InsufficientBuyingPower,
    PositionLimitExceeded,
    OrderValueTooLarge,
    PriceOutOfRange,
    TradingHalted,
    NoMarketData,

    /// <summary>We had no state for this user. Fail closed.</summary>
    StateUnavailable,

    /// <summary>The check itself broke. Fail closed.</summary>
    CheckFailed
}
