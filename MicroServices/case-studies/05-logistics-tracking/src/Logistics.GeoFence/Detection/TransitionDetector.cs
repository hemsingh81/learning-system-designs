using Logistics.Contracts;
using Logistics.GeoFence.Spatial;
using Logistics.GeoFence.State;

namespace Logistics.GeoFence.Detection;

// ─────────────────────────────────────────────────────────────────────────────
// GEO-FENCE TRANSITION DETECTION
//
// The naive version is one line and is wrong in three expensive ways:
//
//     if (fence.Contains(ping)) Publish(new VehicleArrived(...));
//
//   WRONG 1  It checks all 500,000 fences per ping. At 2,400 pings/sec that is
//            1.2 billion containment tests a second. Not possible.
//
//   WRONG 2  It fires on BEING inside, not on ENTERING. A van parked in a depot
//            fires "arrived" every 5 seconds — 17,280 times a day, per vehicle.
//
//   WRONG 3  GPS jitters by 10–30 metres. A vehicle parked exactly on a boundary
//            flaps inside/outside forever, generating thousands of events an hour.
//
// This file fixes all three: a spatial index, remembered previous state, and
// hysteresis. Wrong 3 is the one teams discover from a notification bill.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class TransitionDetector(
    GeoFenceIndex index,
    IFenceStateStore state,
    IMetrics metrics,
    ILogger<TransitionDetector> log)
{
    /// <summary>
    /// Extra metres a vehicle must travel beyond a fence before we call it a
    /// departure. This dead band is what stops GPS jitter producing a storm of
    /// events for a stationary vehicle.
    ///
    /// 50m is a reasonable default: larger than typical urban GPS error (~15m),
    /// small enough that a real departure is detected within one ping.
    /// </summary>
    private const double HysteresisMetres = 50;

    public async Task<IReadOnlyList<FenceTransition>> EvaluateAsync(
        VehiclePing ping, CancellationToken ct)
    {
        // ── FIX 1: narrow 500,000 fences down to a handful ──────────────────
        //
        // A geohash is a string where nearby points share a prefix. Precision 7
        // is roughly a 150m × 150m cell, so this becomes a prefix lookup rather
        // than half a million distance calculations.
        //
        // Neighbouring cells are included too: a point 2m inside cell A can
        // still be inside a fence whose centre is in cell B.
        var candidates = index.FindCandidates(ping.Latitude, ping.Longitude);

        if (candidates.Count == 0)
        {
            // Still must check for EXITS from fences we were previously inside —
            // leaving a fence means we are no longer near it, so it will not be
            // a candidate any more. Missing this leaves vehicles "inside" forever.
            return await DetectExitsOnlyAsync(ping, ct);
        }

        metrics.FenceCandidates(candidates.Count);

        // ── FIX 2: what was true LAST time? ─────────────────────────────────
        //
        // A transition is a CHANGE. Without the previous state there is no
        // change to detect, only a repeated fact.
        //
        // This store must survive a restart. If it does not, every vehicle
        // currently parked in a depot re-fires "arrived" on every deploy.
        var previous = await state.GetInsideFencesAsync(ping.VehicleId, ct);

        var transitions = new List<FenceTransition>();
        var nowInside   = new HashSet<Guid>();

        foreach (var fence in candidates)
        {
            var wasInside = previous.Contains(fence.Id);

            // ── FIX 3: HYSTERESIS ───────────────────────────────────────────
            //
            // Two different boundaries, on purpose:
            //   • not inside yet → must reach the REAL boundary to enter
            //   • already inside → must pass boundary + 50m to leave
            //
            // A vehicle sitting exactly on the line therefore stays "inside"
            // instead of flapping. This asymmetry is the entire trick.
            var isInside = wasInside
                ? fence.Contains(ping.Latitude, ping.Longitude, extraMetres: HysteresisMetres)
                : fence.Contains(ping.Latitude, ping.Longitude, extraMetres: 0);

            if (isInside) nowInside.Add(fence.Id);

            // ENTERED: was outside, now inside.
            if (!wasInside && isInside)
            {
                transitions.Add(new FenceTransition
                {
                    VehicleId    = ping.VehicleId,
                    FenceId      = fence.Id,
                    FenceType    = fence.Type,
                    ReferenceId  = fence.ReferenceId,     // trip, depot, or customer
                    Kind         = TransitionKind.Entered,
                    Latitude     = ping.Latitude,
                    Longitude    = ping.Longitude,

                    // The DEVICE's time, not ours. A ping from an offline burst
                    // may arrive 20 minutes late, and the transition really
                    // happened when the vehicle was there — not when we heard.
                    OccurredAtUtc = ping.RecordedAtUtc
                });

                log.LogInformation("Vehicle {VehicleId} entered fence {FenceId} ({Type})",
                    ping.VehicleId, fence.Id, fence.Type);
            }

            // LEFT: was inside, now clearly outside (past the hysteresis band).
            else if (wasInside && !isInside)
            {
                transitions.Add(new FenceTransition
                {
                    VehicleId     = ping.VehicleId,
                    FenceId       = fence.Id,
                    FenceType     = fence.Type,
                    ReferenceId   = fence.ReferenceId,
                    Kind          = TransitionKind.Left,
                    Latitude      = ping.Latitude,
                    Longitude     = ping.Longitude,
                    OccurredAtUtc = ping.RecordedAtUtc
                });

                log.LogInformation("Vehicle {VehicleId} left fence {FenceId}",
                    ping.VehicleId, fence.Id);
            }

            // wasInside && isInside  → still inside. NO EVENT. This is the
            // branch that silently prevents 17,280 duplicates per van per day.
        }

        // Fences we were inside but that are no longer candidates: the vehicle
        // moved far enough away that they are not even nearby. Those are exits.
        foreach (var fenceId in previous.Where(id => !nowInside.Contains(id)
                                                  && candidates.All(c => c.Id != id)))
        {
            transitions.Add(new FenceTransition
            {
                VehicleId     = ping.VehicleId,
                FenceId       = fenceId,
                Kind          = TransitionKind.Left,
                Latitude      = ping.Latitude,
                Longitude     = ping.Longitude,
                OccurredAtUtc = ping.RecordedAtUtc
            });
        }

        // ── Persist the new state ───────────────────────────────────────────
        // This must be written even when nothing changed. Skipping the write on
        // a no-change ping means a restart loses the fact that we were inside,
        // and the next ping fires a spurious "entered".
        await state.SetInsideFencesAsync(ping.VehicleId, nowInside, ct);

        if (transitions.Count > 0)
            metrics.FenceTransitions(transitions.Count);

        return transitions;
    }

    /// <summary>
    /// No candidate fences nearby, but we may still be recorded as inside one.
    /// That means we have left it. Without this, a vehicle that drives straight
    /// out of a large fence stays "inside" it in our state forever.
    /// </summary>
    private async Task<IReadOnlyList<FenceTransition>> DetectExitsOnlyAsync(
        VehiclePing ping, CancellationToken ct)
    {
        var previous = await state.GetInsideFencesAsync(ping.VehicleId, ct);
        if (previous.Count == 0) return [];

        var transitions = previous.Select(fenceId => new FenceTransition
        {
            VehicleId     = ping.VehicleId,
            FenceId       = fenceId,
            Kind          = TransitionKind.Left,
            Latitude      = ping.Latitude,
            Longitude     = ping.Longitude,
            OccurredAtUtc = ping.RecordedAtUtc
        }).ToList();

        await state.SetInsideFencesAsync(ping.VehicleId, [], ct);
        return transitions;
    }
}

public sealed record FenceTransition
{
    public required Guid           VehicleId     { get; init; }
    public required Guid           FenceId       { get; init; }
    public FenceType               FenceType     { get; init; }

    /// <summary>What the fence is about: a trip, a depot, a customer address.
    /// This is what lets the Trip service react without knowing about geometry.</summary>
    public string?                 ReferenceId   { get; init; }

    public required TransitionKind Kind          { get; init; }
    public required double         Latitude      { get; init; }
    public required double         Longitude     { get; init; }

    /// <summary>The DEVICE's timestamp. For a late offline burst this is minutes
    /// in the past, and that is correct — the event happened then.</summary>
    public required DateTime       OccurredAtUtc { get; init; }
}

public enum TransitionKind { Entered, Left }

public enum FenceType
{
    Depot,
    CustomerAddress,
    RestrictedZone,
    TollZone,

    /// <summary>Driver welfare: the vehicle has not moved for too long.</summary>
    IdleZone
}

// ─────────────────────────────────────────────────────────────────────────────
// THE TESTS THIS FILE DESERVES
//
//   [Fact] void Entering_a_fence_fires_exactly_one_event()
//   [Fact] void Staying_inside_fires_nothing()
//   [Fact] void Leaving_fires_exactly_one_event()
//   [Fact] void Jitter_on_the_boundary_fires_nothing()          ← hysteresis
//   [Fact] void Leaving_requires_crossing_the_hysteresis_band()
//   [Fact] void Driving_far_away_fires_an_exit_with_no_candidates()
//   [Fact] void State_survives_a_restart_without_a_false_entry()
//   [Fact] void Late_offline_ping_uses_the_device_timestamp()
//   [Fact] void Overlapping_fences_each_fire_independently()
//
// A sequence of coordinates in, a list of events out. No Kafka, no Redis, no
// clock — which is exactly why the awkward cases get tested at all.
// ─────────────────────────────────────────────────────────────────────────────
