using MarketData.Contracts;

namespace MarketData.CandleBuilder.Aggregation;

// ─────────────────────────────────────────────────────────────────────────────
// PURE CANDLE AGGREGATION
//
// No Kafka. No database. No DateTime.UtcNow. No logging.
//
// Everything is a function of its inputs, so the whole of it can be unit-tested
// with plain method calls — and candle maths is exactly where subtle bugs live:
//
//   • a tick exactly on a minute boundary
//   • a tick arriving out of order
//   • a symbol that does not trade for 40 minutes
//   • a trade at 15:29:59.999 on the close
//   • the first tick after a sequence gap
//
// Every one of those is a one-line test here. In a class wired to Kafka, each
// is an integration test nobody writes, and a production incident later.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class CandleAggregator(TimeSpan interval)
{
    private readonly Dictionary<string, CandleState> _open = new(8192, StringComparer.Ordinal);

    /// <summary>
    /// Apply one tick.
    ///
    /// Returns a completed candle when this tick starts a NEW bucket, meaning
    /// the previous one is now final. Returns null otherwise.
    ///
    /// Note the model: a candle is emitted when the FIRST tick of the next
    /// bucket arrives — not on a timer. That makes the output a pure function
    /// of the tick stream, so a replay produces byte-identical candles.
    /// See CloseStale below for the illiquid-symbol case this leaves open.
    /// </summary>
    public Candle? Apply(in Tick tick)
    {
        var bucketStart = FloorToInterval(tick.ExchangeTimestampUtc);

        if (!_open.TryGetValue(tick.Symbol, out var state))
        {
            _open[tick.Symbol] = CandleState.Start(tick, bucketStart);
            return null;
        }

        // ── Out-of-order tick ───────────────────────────────────────────────
        // Belongs to a bucket we already closed. Do NOT reopen it: a candle that
        // changes after publication makes every downstream number unreliable.
        //
        // Count it instead. A rising count means an upstream ordering problem —
        // usually a wrong partition key (see the README).
        if (bucketStart < state.BucketStart)
        {
            OutOfOrderCount++;
            return null;
        }

        // ── Same bucket: update in place ────────────────────────────────────
        if (bucketStart == state.BucketStart)
        {
            state.Update(tick);
            return null;
        }

        // ── New bucket: the previous candle is now final ────────────────────
        var completed = state.ToCandle(interval);
        _open[tick.Symbol] = CandleState.Start(tick, bucketStart);
        return completed;
    }

    /// <summary>
    /// Close any candle whose bucket has fully passed.
    ///
    /// This exists because Apply only emits when the NEXT tick arrives. An
    /// illiquid stock that trades at 10:00 and not again until 11:30 would leave
    /// its 10:00 candle open for 90 minutes without this.
    ///
    /// `now` is a PARAMETER, not DateTime.UtcNow. That keeps this class pure and
    /// makes "what happens at a boundary" a test instead of a guess.
    /// </summary>
    public IReadOnlyList<Candle> CloseStale(DateTime now)
    {
        var currentBucket = FloorToInterval(now);
        var closed = new List<Candle>();

        foreach (var (symbol, state) in _open)
        {
            if (state.BucketStart < currentBucket)
                closed.Add(state.ToCandle(interval));
        }

        foreach (var candle in closed)
            _open.Remove(candle.Symbol);

        return closed;
    }

    /// <summary>
    /// Restore in-progress candles after a restart.
    ///
    /// Without this, restarting at 10:30 loses the 10:00–10:30 bar entirely.
    /// The state store persists these; this puts them back.
    /// </summary>
    public void Restore(IEnumerable<CandleState> saved)
    {
        foreach (var state in saved)
            _open[state.Symbol] = state;
    }

    public IReadOnlyCollection<CandleState> Snapshot() => _open.Values;

    /// <summary>Ticks that arrived after their bucket closed. Should be ~0.
    /// A rising number means ordering is broken upstream — export it as a metric.</summary>
    public long OutOfOrderCount { get; private set; }

    /// <summary>
    /// Round a timestamp down to the start of its bucket.
    ///
    /// Ticks (100ns) rather than seconds, so sub-second intervals work and there
    /// is no floating-point rounding anywhere near a price boundary.
    /// </summary>
    private DateTime FloorToInterval(DateTime timestamp)
    {
        var ticks = timestamp.Ticks - (timestamp.Ticks % interval.Ticks);
        return new DateTime(ticks, DateTimeKind.Utc);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// THE MUTABLE STATE OF ONE IN-PROGRESS CANDLE
// ─────────────────────────────────────────────────────────────────────────────

public sealed class CandleState
{
    public string   Symbol      { get; private init; } = "";
    public DateTime BucketStart { get; private init; }

    public decimal Open  { get; private init; }
    public decimal High  { get; private set; }
    public decimal Low   { get; private set; }
    public decimal Close { get; private set; }

    public long    Volume    { get; private set; }
    public decimal TurnOver  { get; private set; }   // Σ(price × quantity) → VWAP
    public int     TickCount { get; private set; }

    /// <summary>True when a sequence gap was seen inside this bucket. The candle
    /// is published with this flag so nobody backtests a hole and gets a
    /// confident, wrong answer.</summary>
    public bool HasGap { get; private set; }

    public static CandleState Start(in Tick tick, DateTime bucketStart) => new()
    {
        Symbol      = tick.Symbol,
        BucketStart = bucketStart,
        Open        = tick.Price,
        High        = tick.Price,
        Low         = tick.Price,
        Close       = tick.Price,
        Volume      = tick.Quantity,
        TurnOver    = tick.Price * tick.Quantity,
        TickCount   = 1,
        HasGap      = tick.FollowsGap
    };

    public void Update(in Tick tick)
    {
        // Open is NEVER updated — it is the first price of the bucket, by definition.
        if (tick.Price > High) High = tick.Price;
        if (tick.Price < Low)  Low  = tick.Price;

        Close      = tick.Price;              // last price wins
        Volume    += tick.Quantity;
        TurnOver  += tick.Price * tick.Quantity;
        TickCount += 1;

        // Once true, always true for this candle. A gap cannot be un-seen.
        if (tick.FollowsGap) HasGap = true;
    }

    public Candle ToCandle(TimeSpan interval) => new()
    {
        Symbol    = Symbol,
        OpenTime  = BucketStart,
        CloseTime = BucketStart.Add(interval),
        Open      = Open,
        High      = High,
        Low       = Low,
        Close     = Close,
        Volume    = Volume,

        // VWAP from turnover, never an average of prices. Averaging prices
        // ignores size and gives a number that looks plausible and is wrong.
        Vwap      = Volume > 0 ? TurnOver / Volume : Close,

        TickCount = TickCount,
        IsComplete = !HasGap
    };
}

// ─────────────────────────────────────────────────────────────────────────────
// WHAT THE TESTS FOR THIS FILE LOOK LIKE
//
//   [Fact] void Open_is_the_first_price_of_the_bucket()
//   [Fact] void Close_is_the_last_price_of_the_bucket()
//   [Fact] void High_and_low_track_extremes()
//   [Fact] void Tick_exactly_on_the_boundary_starts_a_new_bucket()
//   [Fact] void Tick_one_ms_before_the_boundary_stays_in_the_old_bucket()
//   [Fact] void Out_of_order_tick_does_not_reopen_a_closed_candle()
//   [Fact] void Out_of_order_tick_increments_the_counter()
//   [Fact] void Illiquid_symbol_candle_is_closed_by_CloseStale()
//   [Fact] void Gap_flag_survives_to_the_published_candle()
//   [Fact] void Vwap_is_turnover_over_volume_not_an_average_of_prices()
//   [Fact] void Zero_volume_candle_does_not_divide_by_zero()
//   [Fact] void Restore_rebuilds_in_progress_candles_after_a_restart()
//
// Twelve tests, no infrastructure, milliseconds to run. That is what "keep the
// hard maths pure" buys you.
// ─────────────────────────────────────────────────────────────────────────────
