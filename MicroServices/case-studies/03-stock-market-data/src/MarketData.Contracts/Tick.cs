namespace MarketData.Contracts;

// ─────────────────────────────────────────────────────────────────────────────
// THE TICK
//
// This type is created ~200,000 times a second, so its shape is a performance
// decision, not a style decision.
//
// WHY A READONLY STRUCT AND NOT A CLASS:
//
//   A class means one heap allocation per tick. At 200k/sec that is 200,000
//   allocations a second, roughly 12 GB an hour of garbage. Gen-0 collections
//   run constantly and every pause shows up as a latency spike on the chart.
//
//   A struct lives on the stack or inline in an array. Zero heap allocations
//   on the hot path.
//
// This is deliberately NOT general advice. For the Order aggregate in the
// e-commerce case study, a class is obviously right — a few thousand a minute,
// and mutable behaviour matters far more than allocation.
//
// The rule: reach for a struct when profiling shows allocation is the
// bottleneck, and here it demonstrably is.
// ─────────────────────────────────────────────────────────────────────────────

public readonly record struct Tick
{
    /// <summary>
    /// The instrument. Interned strings, so this field is a pointer to one
    /// shared instance rather than 200,000 copies of "RELIANCE".
    /// </summary>
    public required string Symbol { get; init; }

    /// <summary>
    /// Last traded price. `decimal` — NEVER `double`.
    ///
    /// A double cannot represent 0.1 exactly. Ten ticks of 0.1 sum to
    /// 0.9999999999999999, and a "price crossed 1.00" alert silently never fires.
    /// decimal is slower and correct; for money, correct wins.
    /// </summary>
    public required decimal Price { get; init; }

    /// <summary>Number of units traded.</summary>
    public required long Quantity { get; init; }

    /// <summary>
    /// The EXCHANGE's clock, not ours.
    ///
    /// This is what candles bucket on and what backtests replay against. Using
    /// our server clock would make results depend on network delay and NTP drift,
    /// so a replay would not reproduce the original run — which defeats the
    /// entire purpose of keeping the log.
    /// </summary>
    public required DateTime ExchangeTimestampUtc { get; init; }

    /// <summary>
    /// The exchange's per-symbol sequence number. Three jobs:
    ///   1. Gap detection  (8,432,109 then 8,432,115 → six missing)
    ///   2. Deduplication  (same number twice → drop the second)
    ///   3. Ordering       (a definitive order, independent of arrival time)
    /// </summary>
    public required long SequenceNumber { get; init; }

    /// <summary>
    /// True when a sequence gap was detected immediately before this tick.
    ///
    /// This flag travels all the way to the candle and then to the browser, so
    /// a chart can show "incomplete data here" instead of a confident line drawn
    /// across a hole. Visible loss beats silent loss.
    /// </summary>
    public bool FollowsGap { get; init; }

    /// <summary>Which side initiated the trade. Useful for order-flow analysis.</summary>
    public TickSide Side { get; init; }

    public decimal Turnover => Price * Quantity;

    public override string ToString() =>
        $"{Symbol} {Price:N2} × {Quantity} @ {ExchangeTimestampUtc:HH:mm:ss.fff} #{SequenceNumber}";
}

public enum TickSide : byte
{
    Unknown = 0,
    Buy = 1,
    Sell = 2
}

// ─────────────────────────────────────────────────────────────────────────────
// THE CANDLE
//
// Far fewer of these — one per symbol per interval, so ~5,000 a minute rather
// than 200,000 a second. A class would be perfectly fine; it stays a record
// struct only for consistency with Tick.
// ─────────────────────────────────────────────────────────────────────────────

public readonly record struct Candle
{
    public required string   Symbol    { get; init; }
    public required DateTime OpenTime  { get; init; }
    public required DateTime CloseTime { get; init; }

    public required decimal Open  { get; init; }   // first price in the bucket
    public required decimal High  { get; init; }
    public required decimal Low   { get; init; }
    public required decimal Close { get; init; }   // last price in the bucket

    public required long Volume { get; init; }

    /// <summary>Volume-weighted average price: Σ(price × qty) / Σ(qty).
    /// NOT the average of prices — that ignores size and quietly misleads.</summary>
    public required decimal Vwap { get; init; }

    /// <summary>How many ticks made this candle. A candle built from 2 ticks
    /// is far less meaningful than one built from 2,000, and a chart or a
    /// backtest may want to treat them differently.</summary>
    public required int TickCount { get; init; }

    /// <summary>
    /// False when a sequence gap affected this bucket.
    ///
    /// A backtest MUST check this. Trading on a candle whose high is missing
    /// because six ticks were lost produces confident, wrong results — and that
    /// is worse than no results at all.
    /// </summary>
    public required bool IsComplete { get; init; }

    public decimal Range  => High - Low;
    public decimal Change => Close - Open;
    public bool    IsUp   => Close >= Open;
}

// ─────────────────────────────────────────────────────────────────────────────
// SERIALISATION NOTE
//
// JSON is a poor fit at this rate: a tick is ~180 bytes of JSON versus ~40 bytes
// of a compact binary layout, and parsing costs 5–10× more CPU.
//
// At 200k/sec that difference is roughly 36 MB/sec versus 8 MB/sec on the wire,
// and it is the gap between one broker and four.
//
// Use Protobuf, Avro, MessagePack, or a hand-rolled binary layout. The Kafka
// message stays keyed by symbol either way — the encoding does not change the
// partitioning decision, which is the one that actually shapes the system.
// ─────────────────────────────────────────────────────────────────────────────
