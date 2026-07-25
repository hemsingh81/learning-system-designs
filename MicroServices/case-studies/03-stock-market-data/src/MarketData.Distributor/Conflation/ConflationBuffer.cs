using System.Collections.Concurrent;
using MarketData.Contracts;

namespace MarketData.Distributor.Conflation;

// ─────────────────────────────────────────────────────────────────────────────
// CONFLATION — LATEST VALUE WINS
//
// The problem: 200,000 ticks a second, 12,000 connected browsers. Sending every
// tick to every subscriber is 2.4 billion messages a second. It is not merely
// expensive; it is arithmetic that does not work.
//
// The insight: a human cannot read 200 price changes a second. Nobody can. If
// RELIANCE ticks 40 times in 100ms, the eye needs only the 40th.
//
// So the display path keeps only the LATEST price per symbol and flushes 10
// times a second. Intermediate ticks are dropped on purpose.
//
// ─── THE CRITICAL BOUNDARY ───────────────────────────────────────────────────
//
// This is CORRECT for display and WRONG for everything else:
//
//   Candle Builder  → must see EVERY tick, or high/low/volume are wrong
//   Store           → must see EVERY tick, it is the archive
//   Alert Engine    → must see EVERY tick, or "price touched 2850" is missed
//   Risk Engine     → must see EVERY tick
//   Distributor     → conflates. Only here. Only for eyes.
//
// This is only possible because Kafka lets each consumer read the full log at
// its own pace. With a queue, conflating for one consumer would drop the message
// for all of them.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class ConflationBuffer
{
    // Symbol → latest tick. A write simply overwrites; there is no list, so
    // memory is bounded by the number of symbols (~5,000), not by tick rate.
    private readonly ConcurrentDictionary<string, Tick> _latest = new(StringComparer.Ordinal);

    // Which symbols changed since the last flush. Without this, every flush
    // would send all 5,000 symbols even when only 40 moved.
    private readonly ConcurrentDictionary<string, byte> _dirty = new(StringComparer.Ordinal);

    /// <summary>
    /// Record a tick. Called ~200,000 times a second, so it must be O(1),
    /// allocation-free, and lock-free.
    /// </summary>
    public void Update(in Tick tick)
    {
        // Guard against out-of-order arrival. Showing an older price after a
        // newer one makes the display visibly flicker backwards, and users
        // report it as "the price is jumping around".
        if (_latest.TryGetValue(tick.Symbol, out var current) &&
            current.ExchangeTimestampUtc > tick.ExchangeTimestampUtc)
        {
            return;
        }

        _latest[tick.Symbol] = tick;
        _dirty[tick.Symbol]  = 0;

        Conflated++;
    }

    /// <summary>
    /// Take everything that changed since the last call, and reset.
    ///
    /// Called on a 100ms timer. Returns only changed symbols, so a quiet market
    /// costs almost nothing to distribute.
    /// </summary>
    public IReadOnlyList<Tick> DrainChanged()
    {
        if (_dirty.IsEmpty) return [];

        var changed = new List<Tick>(_dirty.Count);

        foreach (var symbol in _dirty.Keys)
        {
            // Remove first, then read. If a tick arrives between the two, it
            // re-marks the symbol dirty and is simply sent on the next flush —
            // never lost, at worst 100ms late.
            _dirty.TryRemove(symbol, out _);

            if (_latest.TryGetValue(symbol, out var tick))
                changed.Add(tick);
        }

        Flushed += changed.Count;
        return changed;
    }

    /// <summary>A new subscriber needs the current price immediately — it must
    /// not stare at an empty box until the symbol next trades, which for an
    /// illiquid stock could be an hour.</summary>
    public Tick? GetLatest(string symbol) =>
        _latest.TryGetValue(symbol, out var tick) ? tick : null;

    // ── Metrics ─────────────────────────────────────────────────────────────
    // The RATIO of these two is the value of this whole class. In a busy market
    // it is typically 50:1 or more — meaning 98% of display traffic never
    // leaves the server.
    public long Conflated { get; private set; }
    public long Flushed   { get; private set; }
}

// ─────────────────────────────────────────────────────────────────────────────
// THE FLUSH LOOP
// ─────────────────────────────────────────────────────────────────────────────

public sealed class ConflationFlushService(
    ConflationBuffer buffer,
    ISubscriptionRegistry subscriptions,
    IHubContext<PriceHub, IPriceClient> hub,
    IMetrics metrics,
    ILogger<ConflationFlushService> log) : BackgroundService
{
    // 10 flushes a second. Faster than the eye needs, slow enough to conflate
    // heavily. 50ms and 200ms are both defensible; 1ms defeats the purpose.
    private static readonly TimeSpan FlushInterval = TimeSpan.FromMilliseconds(100);

    protected override async Task ExecuteAsync(CancellationToken ct)
    {
        using var timer = new PeriodicTimer(FlushInterval);

        while (await timer.WaitForNextTickAsync(ct))
        {
            try
            {
                var changed = buffer.DrainChanged();
                if (changed.Count == 0) continue;

                // Group by symbol so each SignalR group gets ONE message.
                // Sending per connection would multiply the work by 12,000.
                foreach (var tick in changed)
                {
                    // Skip symbols nobody is watching. On a 5,000-symbol feed
                    // with 200 watched symbols, this removes 96% of the work.
                    if (!subscriptions.HasSubscribers(tick.Symbol)) continue;

                    await hub.Clients
                        .Group($"sym:{tick.Symbol}")
                        .PriceUpdate(new PriceUpdate
                        {
                            Symbol    = tick.Symbol,
                            Price     = tick.Price,
                            Timestamp = tick.ExchangeTimestampUtc,

                            // Tell the UI the data may be incomplete, rather than
                            // showing a confident number built over a gap.
                            IsStale   = tick.FollowsGap
                        });
                }

                metrics.ConflationFlush(changed.Count, buffer.Conflated, buffer.Flushed);
            }
            catch (Exception ex)
            {
                // A distribution failure must never stop the loop. The next tick
                // supersedes this one anyway — that is the nature of latest-value-wins.
                log.LogError(ex, "Conflation flush failed");
            }
        }
    }
}

public interface IPriceClient
{
    Task PriceUpdate(PriceUpdate update);
}

public sealed record PriceUpdate
{
    public required string   Symbol    { get; init; }
    public required decimal  Price     { get; init; }
    public required DateTime Timestamp { get; init; }

    /// <summary>True when a sequence gap affected this symbol. The UI shows a
    /// small warning rather than pretending the number is complete.</summary>
    public required bool IsStale { get; init; }
}
