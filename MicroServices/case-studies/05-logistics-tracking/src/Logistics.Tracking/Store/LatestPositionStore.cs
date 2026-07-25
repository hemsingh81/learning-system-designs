using System.Text.Json;
using Logistics.Contracts;
using StackExchange.Redis;

namespace Logistics.Tracking.Store;

// ─────────────────────────────────────────────────────────────────────────────
// LATEST-VALUE-WINS
//
// The question this answers: "where is vehicle 4471 right now?"
//
// The wrong way:
//
//     SELECT TOP 1 * FROM position_history
//     WHERE vehicle_id = @id ORDER BY recorded_at DESC
//
// That is an index seek over 200 million rows a day, run 30,000 times a second
// by map viewers, to fetch one row we already had a moment ago.
//
// The right way: one key per vehicle, overwritten every 5 seconds. 12,000 keys
// in total, forever, regardless of how long the system runs. O(1) read, O(1)
// write, and the memory footprint never grows.
//
// TWO details that look small and are not:
//
//   TTL      a vehicle that stops reporting DISAPPEARS rather than sitting on
//            the map at an hours-old position, looking perfectly live.
//
//   ORDERING a late ping from an offline burst must NEVER overwrite a newer
//            position. Without this check, a van that reconnects appears to
//            teleport back to where it was 20 minutes ago.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class LatestPositionStore(
    IConnectionMultiplexer redis,
    IMetrics metrics,
    ILogger<LatestPositionStore> log)
{
    private readonly IDatabase _db = redis.GetDatabase();

    /// <summary>
    /// No ping for 30 minutes → the vehicle is gone from the live view.
    ///
    /// Missing is honest. Stale-pretending-to-be-live is not: a customer
    /// watching a van that "has not moved in two hours" will call support, and
    /// the van is usually fine — it is the data that is dead.
    /// </summary>
    private static readonly TimeSpan PositionTtl = TimeSpan.FromMinutes(30);

    private static string Key(Guid vehicleId) => $"pos:{vehicleId:N}";

    /// <summary>
    /// Store a position, but only if it is genuinely newer.
    /// Returns false when an older ping was correctly ignored.
    /// </summary>
    public async Task<bool> UpdateAsync(VehiclePing ping, CancellationToken ct)
    {
        var key = Key(ping.VehicleId);

        // ── Out-of-order protection ─────────────────────────────────────────
        //
        // Offline vehicles buffer pings and send bursts on reconnection, so a
        // 20-minute-old ping arriving now is completely normal. It belongs in
        // history — it does NOT belong in "where is this van right now".
        var existing = await _db.StringGetAsync(key);

        if (existing.HasValue)
        {
            var current = JsonSerializer.Deserialize<VehiclePing>(existing!)!;

            if (ping.RecordedAtUtc <= current.RecordedAtUtc)
            {
                metrics.StalePingIgnored();
                return false;             // normal, not an error
            }
        }

        // ── Write with a sliding TTL ────────────────────────────────────────
        // Every ping refreshes the expiry, so an active vehicle never expires
        // and an inactive one drops off automatically after 30 minutes.
        await _db.StringSetAsync(
            key,
            JsonSerializer.SerializeToUtf8Bytes(ping),
            expiry: PositionTtl);

        // A second, small key for the fleet view. Reading 12,000 full position
        // blobs to draw an operations map would move megabytes per refresh;
        // this sorted set holds just enough to place a dot.
        await _db.SortedSetAddAsync(
            "fleet:active",
            ping.VehicleId.ToString("N"),
            ping.RecordedAtUtc.Ticks);

        metrics.PositionUpdated();
        return true;
    }

    /// <summary>Where is this vehicle now? Null means we genuinely do not know —
    /// no ping within the TTL. Callers must show "location unavailable" rather
    /// than the last thing they happen to remember.</summary>
    public async Task<VehiclePing?> GetAsync(Guid vehicleId)
    {
        var value = await _db.StringGetAsync(Key(vehicleId));

        if (!value.HasValue)
        {
            metrics.PositionMiss();
            return null;
        }

        return JsonSerializer.Deserialize<VehiclePing>(value!);
    }

    /// <summary>
    /// Positions for several vehicles at once — one round trip, not N.
    /// The operations map asks for 200 vehicles; 200 separate calls would be
    /// 200 network round trips for data that fits in one response.
    /// </summary>
    public async Task<IReadOnlyDictionary<Guid, VehiclePing>> GetManyAsync(
        IReadOnlyCollection<Guid> vehicleIds)
    {
        if (vehicleIds.Count == 0) return new Dictionary<Guid, VehiclePing>();

        var keys   = vehicleIds.Select(id => (RedisKey)Key(id)).ToArray();
        var values = await _db.StringGetAsync(keys);          // one MGET

        var result = new Dictionary<Guid, VehiclePing>(vehicleIds.Count);
        var ids    = vehicleIds.ToArray();

        for (var i = 0; i < values.Length; i++)
        {
            if (!values[i].HasValue) continue;                // expired or never seen
            result[ids[i]] = JsonSerializer.Deserialize<VehiclePing>(values[i]!)!;
        }

        return result;
    }

    /// <summary>
    /// Vehicles that have reported within the given window.
    ///
    /// Reads the sorted set, so it never touches the 200-million-row history
    /// table. Nothing on the live path may query that table — one large export
    /// running at the same time would stop the live map for everyone.
    /// </summary>
    public async Task<IReadOnlyList<Guid>> GetActiveVehiclesAsync(TimeSpan within)
    {
        var cutoff = DateTime.UtcNow.Subtract(within).Ticks;

        var entries = await _db.SortedSetRangeByScoreAsync(
            "fleet:active", start: cutoff, stop: double.PositiveInfinity);

        return entries.Select(e => Guid.Parse(e!)).ToList();
    }

    /// <summary>
    /// Trim vehicles that stopped reporting from the fleet set.
    ///
    /// The position keys expire on their own via the TTL; a sorted set has no
    /// per-member expiry, so it needs this sweep. Without it the set grows
    /// forever with vehicles that were decommissioned years ago.
    /// </summary>
    public async Task<long> SweepInactiveAsync(CancellationToken ct)
    {
        var cutoff  = DateTime.UtcNow.Subtract(PositionTtl).Ticks;
        var removed = await _db.SortedSetRemoveRangeByScoreAsync(
            "fleet:active", double.NegativeInfinity, cutoff);

        if (removed > 0)
            log.LogInformation("Swept {Count} inactive vehicles from the fleet set", removed);

        return removed;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// WHY REDIS AND NOT POSTGRES
//
//   Read rate         ~30,000/sec (map viewers)
//   Write rate        ~2,400/sec  (pings)
//   Working set       12,000 keys, a few KB each — a few MB in total
//   Durability need   NONE. Every value is replaced within 5 seconds, and the
//                     history table holds the permanent record.
//
// That last line is what makes this an easy decision. Losing the entire cache
// costs 5 seconds of map staleness and nothing else — so paying for disk
// durability on this path would buy nothing and cost latency.
//
// Note the contrast with the banking case study, where the equivalent question
// has the opposite answer. Same shape of decision; different consequences.
// ─────────────────────────────────────────────────────────────────────────────
