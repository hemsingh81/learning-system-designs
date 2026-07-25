namespace Trading.Positions.Domain;

// ─────────────────────────────────────────────────────────────────────────────
// AVERAGE COST AND PROFIT-AND-LOSS
//
// Pure. No database, no clock, no logging, no I/O of any kind.
//
// Why that matters more here than almost anywhere else in these case studies:
// users check these numbers against their own spreadsheets, and they are not
// forgiving. "Your app says my average cost is 2842.17, my calculator says
// 2842.16" is a support ticket, and sometimes a regulator's question.
//
// The awkward cases are all one-line unit tests here, and all production
// incidents if this logic is tangled up with infrastructure:
//
//   • a partial fill, then another at a different price
//   • selling more than you hold (going short)
//   • flipping from long to short in ONE order
//   • a fill of quantity 0 (some brokers really do send these)
//   • closing a position exactly to zero
// ─────────────────────────────────────────────────────────────────────────────

public static class PnlCalculator
{
    /// <summary>
    /// Apply a fill to a position and return the new state.
    ///
    /// Weighted-average cost, which is the standard for most retail brokers.
    /// FIFO lot matching (needed for tax in some jurisdictions) is a different
    /// method — see ApplyFifo below.
    /// </summary>
    public static PositionState Apply(PositionState current, Fill fill)
    {
        if (fill.Quantity == 0) return current;      // brokers do send these

        var signedFill = fill.Side == FillSide.Buy ? fill.Quantity : -fill.Quantity;
        var newQty     = current.Quantity + signedFill;

        // ── CASE 1: opening, or adding to an existing position ──────────────
        // Same direction (or starting from flat): recompute the weighted average.
        if (current.Quantity == 0 || Math.Sign(current.Quantity) == Math.Sign(signedFill))
        {
            // Weighted average of what we held and what we just bought.
            //   (100 × 2840.75 + 50 × 2845.00) / 150 = 2842.1667
            var totalCost = (Math.Abs(current.Quantity) * current.AverageCost)
                          + (fill.Quantity * fill.Price);

            var totalQty = Math.Abs(current.Quantity) + fill.Quantity;

            return current with
            {
                Quantity    = newQty,

                // Round to 4 places at every step, always the same way. Rounding
                // only at display time makes two screens disagree by a paisa,
                // and that is a ticket every single time.
                AverageCost = Math.Round(totalCost / totalQty, 4, MidpointRounding.ToEven),

                // Adding to a position realises nothing. Only closing does.
                RealisedPnl = current.RealisedPnl
            };
        }

        // ── CASE 2: reducing or closing ─────────────────────────────────────
        // Opposite direction. This is where profit or loss becomes real.
        var closingQty = Math.Min(Math.Abs(current.Quantity), fill.Quantity);

        // Long:  profit = (sell price − average cost) × quantity
        // Short: profit = (average cost − buy price)  × quantity
        var pnlPerUnit = current.Quantity > 0
            ? fill.Price - current.AverageCost
            : current.AverageCost - fill.Price;

        var realised = Math.Round(pnlPerUnit * closingQty, 4, MidpointRounding.ToEven);

        // ── CASE 2a: closed exactly to flat ─────────────────────────────────
        if (newQty == 0)
        {
            return current with
            {
                Quantity    = 0,

                // Reset to zero, NOT to the last price. A flat position has no
                // cost basis, and leaving a stale average here corrupts the very
                // next trade's P&L.
                AverageCost = 0m,
                RealisedPnl = current.RealisedPnl + realised
            };
        }

        // ── CASE 2b: partially closed, same direction ───────────────────────
        if (Math.Sign(newQty) == Math.Sign(current.Quantity))
        {
            return current with
            {
                Quantity    = newQty,

                // Average cost does NOT change when you sell part of a holding.
                // The remaining shares still cost what they cost. Recomputing it
                // here is one of the most common bugs in position tracking.
                AverageCost = current.AverageCost,
                RealisedPnl = current.RealisedPnl + realised
            };
        }

        // ── CASE 2c: FLIPPED through zero in one fill ───────────────────────
        // Long 100, sell 150 → short 50.
        // Two things happened: the 100 closed (realising P&L), and a NEW short
        // 50 opened at the fill price. Handling this as one operation is the
        // classic source of a wrong average cost after a reversal.
        return current with
        {
            Quantity    = newQty,
            AverageCost = fill.Price,          // the new position starts here
            RealisedPnl = current.RealisedPnl + realised
        };
    }

    /// <summary>
    /// Unrealised profit and loss at the current market price.
    ///
    /// `marketPrice` is a PARAMETER, not something this class fetches. That is
    /// what keeps it pure — and it makes "what is my P&L at 2900?" a function
    /// call rather than a new feature.
    /// </summary>
    public static decimal UnrealisedPnl(PositionState position, decimal marketPrice)
    {
        if (position.Quantity == 0) return 0m;

        // Works for both directions without a branch: a short has a negative
        // quantity, so a price fall produces a positive number.
        return Math.Round(
            (marketPrice - position.AverageCost) * position.Quantity,
            4, MidpointRounding.ToEven);
    }

    /// <summary>
    /// Rebuild a position from its entire fill history.
    ///
    /// This is the reason positions are event-sourced. Two uses, both real:
    ///
    ///   1. Fix a bug in the maths above, then recompute every affected
    ///      position from the fills. No data migration, no apology.
    ///
    ///   2. Prove the stored snapshot is correct. The reconciler runs this and
    ///      compares. Any difference means state and events have diverged, and
    ///      you want to know that from a job, not from a customer.
    /// </summary>
    public static PositionState Rebuild(IEnumerable<Fill> fills)
    {
        var state = PositionState.Flat;

        // Order by time, then by fill ID: two fills can share a millisecond, and
        // an unstable sort would make the rebuild non-deterministic — which
        // defeats the entire point of being able to rebuild.
        foreach (var fill in fills.OrderBy(f => f.ExecutedAtUtc).ThenBy(f => f.Id))
            state = Apply(state, fill);

        return state;
    }
}

public readonly record struct PositionState
{
    /// <summary>Positive = long, negative = short, zero = flat.</summary>
    public required int Quantity { get; init; }

    /// <summary>Weighted average cost of the CURRENT holding. Zero when flat.</summary>
    public required decimal AverageCost { get; init; }

    /// <summary>Cumulative profit and loss from closed quantity. Never resets.</summary>
    public required decimal RealisedPnl { get; init; }

    public static PositionState Flat => new() { Quantity = 0, AverageCost = 0m, RealisedPnl = 0m };

    public bool IsLong  => Quantity > 0;
    public bool IsShort => Quantity < 0;
    public bool IsFlat  => Quantity == 0;
}

public readonly record struct Fill
{
    public required Guid     Id            { get; init; }
    public required string   Symbol        { get; init; }
    public required FillSide Side          { get; init; }
    public required int      Quantity      { get; init; }
    public required decimal  Price         { get; init; }
    public required DateTime ExecutedAtUtc { get; init; }

    /// <summary>Brokerage, taxes, and exchange fees. Real P&L must include these —
    /// a "profitable" trade that loses money after charges is a very common and
    /// very unwelcome discovery for a user.</summary>
    public decimal Charges { get; init; }
}

public enum FillSide { Buy, Sell }

// ─────────────────────────────────────────────────────────────────────────────
// THE TESTS THIS FILE DESERVES
//
//   [Fact] void Buy_from_flat_sets_average_to_fill_price()
//   [Fact] void Second_buy_produces_a_weighted_average()
//   [Fact] void Selling_part_does_not_change_average_cost()
//   [Fact] void Selling_part_realises_proportional_pnl()
//   [Fact] void Closing_to_flat_resets_average_cost_to_zero()
//   [Fact] void Flipping_long_to_short_realises_and_reopens_at_fill_price()
//   [Fact] void Short_position_profits_when_price_falls()
//   [Fact] void Zero_quantity_fill_is_ignored()
//   [Fact] void Rebuild_from_fills_matches_incremental_application()
//   [Fact] void Rebuild_is_deterministic_for_fills_in_the_same_millisecond()
//   [Fact] void Unrealised_pnl_is_zero_when_flat()
//
// Eleven tests, no infrastructure, milliseconds to run — covering the maths a
// user will check with a calculator.
// ─────────────────────────────────────────────────────────────────────────────
