using Logistics.Contracts;
using Logistics.Ingest.Publishing;
using Logistics.Ingest.Validation;

namespace Logistics.Ingest.Api;

// ─────────────────────────────────────────────────────────────────────────────
// RECEIVING POSITION PINGS
//
// Two shapes of traffic, and the second one is what most designs forget:
//
//   NORMAL   one ping every 5 seconds per vehicle → ~2,400/sec across the fleet
//
//   BURST    a vehicle comes out of a tunnel or a basement car park and sends
//            20 minutes of buffered pings at once — 240 in a single request
//
// A design that only handles the first shape rejects the second as abuse, and
// loses exactly the proof-of-delivery evidence that a dispute will need.
// ─────────────────────────────────────────────────────────────────────────────

public static class PingEndpoints
{
    public static IEndpointRouteBuilder MapPings(this IEndpointRouteBuilder app)
    {
        var group = app.MapGroup("/pings").RequireAuthorization("device");

        group.MapPost("/",      SingleAsync);
        group.MapPost("/batch", BatchAsync);

        return app;
    }

    // ── The normal path ─────────────────────────────────────────────────────

    private static async Task<IResult> SingleAsync(
        PingRequest request,
        PingValidator validator,
        PingProducer producer,
        CancellationToken ct)
    {
        var ping = request.ToPing();

        var result = validator.Validate(ping, previous: null);

        if (!result.IsValid)
        {
            // A rejected ping is DATA, not just a 400. A device that suddenly
            // sends impossible coordinates has a hardware or firmware problem,
            // and the fleet team needs to know which vehicle it is.
            await producer.PublishRejectedAsync(ping, result.Reason!, ct);

            return Results.BadRequest(new { rejected = true, reason = result.Reason });
        }

        await producer.PublishAsync(ping, ct);

        // 202: we have taken it. Everything downstream is asynchronous, and the
        // device must not wait for geo-fencing, ETA, and notifications to run.
        return Results.Accepted();
    }

    // ── The offline-burst path ──────────────────────────────────────────────

    private static async Task<IResult> BatchAsync(
        BatchPingRequest request,
        PingValidator validator,
        PingProducer producer,
        ILogger<BatchPingRequest> log,
        CancellationToken ct)
    {
        // A generous but real limit. 240 pings is 20 minutes of buffering, which
        // is normal. 10,000 is a broken device or someone probing the endpoint.
        if (request.Pings.Count > 1000)
            return Results.BadRequest(new { error = "batch too large (max 1000 pings)" });

        if (request.Pings.Count == 0)
            return Results.Ok(new { accepted = 0, rejected = 0 });

        // ── ORDER BY DEVICE TIME ────────────────────────────────────────────
        //
        // Devices do not always buffer in order, and JSON arrays arrive in
        // whatever order the client serialised them.
        //
        // Order matters here for one specific reason: geo-fence transitions are
        // computed by comparing each ping with the previous state. Feed them out
        // of order and you record "left the depot" before "arrived at the depot",
        // and the trip state machine goes wrong in a way that is very hard to
        // debug later.
        var ordered = request.Pings
            .Select(p => p.ToPing(request.VehicleId))
            .OrderBy(p => p.RecordedAtUtc)
            .ToList();

        var accepted = 0;
        var rejected = 0;
        VehiclePing? previous = null;

        foreach (var ping in ordered)
        {
            // Validation is stateful across the batch: "did this vehicle move
            // 400 km in 5 seconds?" can only be answered against the previous
            // ping, and inside a batch that previous ping is right here.
            var result = validator.Validate(ping, previous);

            if (!result.IsValid)
            {
                rejected++;

                // Skip the bad ping but KEEP GOING. One glitched fix in the
                // middle of a 240-ping burst must not discard the other 239 —
                // those are the evidence for a delivery dispute.
                await producer.PublishRejectedAsync(ping, result.Reason!, ct);
                continue;
            }

            // Marked as late so downstream can treat it correctly:
            //   • History  stores it normally
            //   • Tracking ignores it if a newer position already exists
            //   • GeoFence still evaluates it, and publishes events with the
            //     DEVICE timestamp so the sequence stays truthful
            await producer.PublishAsync(ping with { IsLateArrival = true }, ct);

            previous = ping;
            accepted++;
        }

        var span = ordered[^1].RecordedAtUtc - ordered[0].RecordedAtUtc;

        log.LogInformation(
            "Accepted an offline burst from vehicle {VehicleId}: {Accepted} pings covering {Minutes:F0} " +
            "minutes ({Rejected} rejected)",
            request.VehicleId, accepted, span.TotalMinutes, rejected);

        return Results.Accepted(value: new { accepted, rejected });
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// VALIDATION — BECAUSE DEVICES LIE
//
// GPS receivers produce genuinely impossible readings: a lost fix defaults to
// (0,0) off the coast of Africa, a cold start can jump hundreds of kilometres,
// and a reflected signal in a city can throw a position across a river.
//
// Letting these through corrupts three things at once — the live map, the ETA,
// and the distance-travelled report that drives driver pay. That last one turns
// a data-quality bug into a payroll dispute.
// ─────────────────────────────────────────────────────────────────────────────

public sealed class PingValidator
{
    /// <summary>Fast enough to be impossible for a delivery van, slow enough not
    /// to reject a genuinely fast vehicle on a motorway.</summary>
    private const double MaxSpeedKmh = 200;

    public ValidationResult Validate(VehiclePing ping, VehiclePing? previous)
    {
        // ── Coordinates in range ────────────────────────────────────────────
        if (ping.Latitude is < -90 or > 90 || ping.Longitude is < -180 or > 180)
            return ValidationResult.Invalid("coordinates out of range");

        // ── The null island check ───────────────────────────────────────────
        // (0,0) is in the Atlantic. It means "no GPS fix", not "at sea".
        // Almost every fleet system has shipped this bug at least once.
        if (Math.Abs(ping.Latitude) < 0.0001 && Math.Abs(ping.Longitude) < 0.0001)
            return ValidationResult.Invalid("null island (0,0) — no GPS fix");

        // ── Timestamp sanity ────────────────────────────────────────────────
        var now = DateTime.UtcNow;

        // Some clock skew is normal; a device an hour in the future is broken.
        if (ping.RecordedAtUtc > now.AddMinutes(5))
            return ValidationResult.Invalid("timestamp is in the future");

        // Older than a day means a device that was offline far longer than any
        // real buffer, or a clock reset. Accepting it would rewrite history.
        if (ping.RecordedAtUtc < now.AddDays(-1))
            return ValidationResult.Invalid("timestamp is more than a day old");

        // ── Impossible movement ─────────────────────────────────────────────
        if (previous is not null)
        {
            var seconds = (ping.RecordedAtUtc - previous.RecordedAtUtc).TotalSeconds;

            if (seconds > 0)
            {
                var km    = Haversine(previous.Latitude, previous.Longitude,
                                      ping.Latitude,     ping.Longitude);
                var speed = km / (seconds / 3600.0);

                if (speed > MaxSpeedKmh)
                    return ValidationResult.Invalid(
                        $"implausible speed {speed:F0} km/h over {km:F1} km in {seconds:F0}s");
            }
        }

        // ── Accuracy ────────────────────────────────────────────────────────
        // A fix accurate to ±500m is worse than useless for geo-fencing: it
        // will trigger arrivals at the wrong address.
        if (ping.AccuracyMetres > 200)
            return ValidationResult.Invalid($"GPS accuracy {ping.AccuracyMetres}m is too poor");

        return ValidationResult.Valid();
    }

    /// <summary>Great-circle distance in kilometres. Pure, and easy to test
    /// against known city-pair distances.</summary>
    private static double Haversine(double lat1, double lon1, double lat2, double lon2)
    {
        const double earthRadiusKm = 6371.0;

        var dLat = ToRadians(lat2 - lat1);
        var dLon = ToRadians(lon2 - lon1);

        var a = Math.Sin(dLat / 2) * Math.Sin(dLat / 2)
              + Math.Cos(ToRadians(lat1)) * Math.Cos(ToRadians(lat2))
              * Math.Sin(dLon / 2) * Math.Sin(dLon / 2);

        return earthRadiusKm * 2 * Math.Atan2(Math.Sqrt(a), Math.Sqrt(1 - a));
    }

    private static double ToRadians(double degrees) => degrees * Math.PI / 180.0;
}

public readonly record struct ValidationResult
{
    public bool    IsValid { get; private init; }
    public string? Reason  { get; private init; }

    public static ValidationResult Valid() => new() { IsValid = true };
    public static ValidationResult Invalid(string reason) => new() { IsValid = false, Reason = reason };
}

public sealed record PingRequest
{
    public required Guid     VehicleId      { get; init; }
    public required double   Latitude       { get; init; }
    public required double   Longitude      { get; init; }
    public required DateTime RecordedAtUtc  { get; init; }
    public double            SpeedKmh       { get; init; }
    public double            HeadingDegrees { get; init; }
    public double            AccuracyMetres { get; init; }

    public VehiclePing ToPing() => new()
    {
        VehicleId      = VehicleId,
        Latitude       = Latitude,
        Longitude      = Longitude,
        RecordedAtUtc  = RecordedAtUtc,
        ReceivedAtUtc  = DateTime.UtcNow,     // both times are kept: a driver
        SpeedKmh       = SpeedKmh,            // dispute can turn on the gap
        HeadingDegrees = HeadingDegrees,
        AccuracyMetres = AccuracyMetres
    };
}

public sealed record BatchPingRequest
{
    public required Guid VehicleId { get; init; }
    public required IReadOnlyList<BatchPingItem> Pings { get; init; }
}

public sealed record BatchPingItem
{
    public required double   Latitude       { get; init; }
    public required double   Longitude      { get; init; }
    public required DateTime RecordedAtUtc  { get; init; }
    public double            SpeedKmh       { get; init; }
    public double            HeadingDegrees { get; init; }
    public double            AccuracyMetres { get; init; }

    public VehiclePing ToPing(Guid vehicleId) => new()
    {
        VehicleId      = vehicleId,
        Latitude       = Latitude,
        Longitude      = Longitude,
        RecordedAtUtc  = RecordedAtUtc,
        ReceivedAtUtc  = DateTime.UtcNow,
        SpeedKmh       = SpeedKmh,
        HeadingDegrees = HeadingDegrees,
        AccuracyMetres = AccuracyMetres
    };
}
