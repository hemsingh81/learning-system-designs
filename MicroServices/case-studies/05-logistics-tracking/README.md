# Case Study 5 — Logistics and Delivery Tracking

← [Trading app](../04-trading-app/) · [All case studies](../README.md) · [Back to the map](../../README.md)

---

## The business

A delivery company. Thousands of vehicles carry parcels. Every vehicle reports its position continuously. Customers watch their parcel move on a map. Operations staff watch the whole fleet and get told when something goes wrong.

| Measure | Value |
|---|---|
| Active vehicles | ~12,000 |
| Position reports per vehicle | one every 5 seconds |
| Location messages per second | ~2,400 |
| Parcels in flight | ~400,000 |
| Customers watching a live map | ~30,000 at peak |
| Geo-fences (depots, zones, customer addresses) | ~500,000 |

---

## The constraint

> **Only the latest position matters for the map. But the full history matters for proof of delivery, driver disputes, and route optimisation.**

Two different demands on the same stream — and this is the reason to read this case study after [market data](../03-stock-market-data/): the shape is similar, but the reasons differ in an instructive way.

| | Market data | Logistics |
|---|---|---|
| Rate | 200,000/sec | 2,400/sec |
| Hardest problem | Raw throughput | **Cardinality of state** |
| Ordering key | Symbol | Vehicle |
| Stale data | Unacceptable | Normal — vehicles go through tunnels |
| Loss of one message | A gap in a chart | Almost harmless: another arrives in 5 s |
| History | Backtesting | **Legal evidence** |

**The interesting difference: a lost location ping barely matters here.** Another arrives in five seconds and the position is corrected. That single fact allows a much simpler design than market data needed — and recognising when your constraint is *softer* than the textbook case is as valuable as recognising when it is harder.

---

## The services

| Service | Job |
|---|---|
| **Ingest** | Receive pings from vehicle devices. Validate, deduplicate, normalise |
| **Tracking** | Hold the current position of every vehicle (the latest-value store) |
| **GeoFence** | Detect entering and leaving zones. Publish arrival and departure events |
| **Trip** | The state machine of one delivery: assigned → collected → in transit → delivered |
| **ETA** | Predict arrival times from position, traffic, and history |
| **Notify** | "Your parcel is 10 minutes away" |
| **History** | Store every ping, forever. Proof of delivery, disputes, route analysis |
| **Push** | Live map updates to customers and operations |

### The ownership table

| Entity | Owner | Readers |
|---|---|---|
| VehiclePosition (latest) | Tracking | ETA, GeoFence, Push |
| PositionHistory | History | Disputes, route analysis |
| Trip | Trip | ETA, Notify, Push |
| GeoFence definition | GeoFence | nobody |
| Parcel | Trip | Notify, customer API |

---

## The central design idea: two paths from one stream

```
Vehicle device ──HTTPS──► Ingest ──► Kafka: vehicle.pings (key = vehicleId)
                                          │
                    ┌─────────────────────┼──────────────────────┐
                    ▼                     ▼                      ▼
            LATEST-VALUE PATH      EVENT PATH             HISTORY PATH
                    │                     │                      │
              Tracking (Redis)     GeoFence detect        History (append)
                    │                     │                      │
                    ▼                     ▼                      ▼
              Push to maps        Trip state changes      Kept forever
              (conflated)         → Notify, ETA           (compressed)
```

**One stream, three consumers, three completely different storage models:**

| Path | Storage | Why |
|---|---|---|
| Latest value | Redis, one key per vehicle | 12,000 keys total. O(1) read. Overwrite, never append |
| Events | Kafka topics | Arrival and departure are *facts* others react to |
| History | Time-partitioned table | 200 million rows a day, written once, read rarely |

Getting this split right is the whole case study. Using one storage model for all three would be wrong three times over.

---

## Key decisions

### Decision 1 — The latest position is a key-value overwrite, not a stream

12,000 vehicles. Only ever 12,000 current positions, no matter how long the system runs.

```csharp
// One key per vehicle. Overwritten every 5 seconds. Bounded forever.
await redis.StringSetAsync(
    $"pos:{ping.VehicleId}",
    Serialize(ping),
    expiry: TimeSpan.FromMinutes(30));   // no ping for 30 min → the vehicle is gone
```

**Why not query the history table for "where is vehicle 4471 now?"** Because that means an index seek over 200 million rows a day, 30,000 times a second, when the answer is a single key lookup.

**The TTL is doing real work.** A vehicle that stops reporting simply disappears rather than sitting on the map at a position from three hours ago. Absence of data is honest; stale data pretending to be live is not.

### Decision 2 — Partition by vehicle, and understand why it differs from market data

```csharp
Key = ping.VehicleId      // NOT the region, NOT the depot, NOT null
```

Same reasoning as market data's symbol key, but a different failure if you get it wrong.

**Why not partition by region?** Because regions are wildly unequal. Mumbai would be one enormous partition and a rural zone would be nearly empty — and a vehicle crossing a region boundary would jump partitions, so its own pings could arrive out of order at exactly the moment it matters (a border crossing).

**Why does ordering matter at all here?** Geo-fencing. If "entered depot" and "left depot" are processed out of order, you record a departure before an arrival, and the trip state machine goes wrong. Per-vehicle ordering makes that impossible.

### Decision 3 — Geo-fencing is stateful, and that is the hard part

500,000 fences and 2,400 pings a second. Checking every fence for every ping is 1.2 billion checks a second. Not possible.

Three techniques, all needed:

**1. Spatial index.** An R-tree or geohash prefix reduces "which fences might contain this point?" from 500,000 to about 5.

```csharp
// Geohash: nearby points share a string prefix, so this is a prefix lookup,
// not a distance calculation against every fence.
var cell      = Geohash.Encode(ping.Latitude, ping.Longitude, precision: 7);
var candidates = _fenceIndex.WithinCell(cell);      // ~5 fences, not 500,000
```

**2. Remember the previous state.** A fence event fires on a *transition*, not on being inside.

```csharp
// Without this, a van parked inside a depot fires "arrived" every 5 seconds,
// all day. That is 17,280 duplicate notifications per vehicle per day.
var wasInside = _previousState.IsInside(ping.VehicleId, fence.Id);
var isInside  = fence.Contains(ping.Latitude, ping.Longitude);

if (!wasInside && isInside) Publish(new VehicleEnteredFence(...));
if (wasInside && !isInside) Publish(new VehicleLeftFence(...));
```

**3. Hysteresis.** GPS jitters by 10–30 metres. A vehicle parked exactly on a boundary would flap between inside and outside forever.

```csharp
// Enter at the real boundary; leave only after clearly leaving.
// Without this, one parked van can generate thousands of events an hour.
var enterRadius = fence.Radius;
var exitRadius  = fence.Radius + 50;   // 50 metres of dead band
```

**This third point is the one teams discover in production**, usually via a notification bill or a customer receiving 400 "your parcel has arrived" messages.

### Decision 4 — History is written in batches and never read on the hot path

200 million rows a day, written once, read almost never — but when it is read, it is for a dispute or a legal request, so it must be complete and it must be exact.

| Property | Choice |
|---|---|
| Write pattern | Batched, 5,000 rows or 2 seconds |
| Partitioning | By day, so old data can be compressed and dropped cheaply |
| Compression | Roughly 15:1 — consecutive positions are extremely similar |
| Retention | 2 years hot, then cold object storage |
| Index | `(vehicle_id, recorded_at)` only. Every real query has both |

**Nothing on the live path ever reads this table.** The moment a "quick" live query is added to it, one legal export locks the table and the live map stops updating for everyone.

### Decision 5 — Conflation for maps, exactly as in market data

30,000 customers watching maps. Sending every ping to every viewer is impossible and pointless — a map that updates more than twice a second just looks jittery.

```csharp
// Same pattern as case study 3's ConflationBuffer, different tuning.
// Market data flushes at 100ms because prices matter. A van moving at 40 km/h
// travels 5 metres in 500ms; nobody can see that on a phone screen.
private static readonly TimeSpan FlushInterval = TimeSpan.FromMilliseconds(500);
```

And critically, **each customer receives only the one vehicle carrying their parcel** — never the fleet. Broadcasting all vehicle positions to every viewer would be both a bandwidth problem and a privacy incident.

### Decision 6 — Offline vehicles are normal, not an error

Vans go through tunnels, into basement car parks, and into areas with no signal. The device buffers pings and sends them in a burst on reconnection.

So the system must accept **late, batched, out-of-order** data as routine:

```csharp
// A burst of 200 pings covering the last 20 minutes is NORMAL, not an attack.
// Reject them and you lose the proof-of-delivery evidence for that window.
foreach (var ping in batch.OrderBy(p => p.RecordedAtUtc))
{
    // History: accept everything, in time order.
    await history.AppendAsync(ping, ct);

    // Latest value: only if it is genuinely newer. A 20-minute-old ping must
    // never overwrite the position the vehicle reported 5 seconds ago.
    if (ping.RecordedAtUtc > current.RecordedAtUtc)
        await tracking.UpdateAsync(ping, ct);

    // Geo-fencing: replay in order, so entries and exits are still detected.
    // The events are published late, and downstream must tolerate that.
    await geoFence.EvaluateAsync(ping, ct);
}
```

**The device's clock is the truth for ordering; the server's clock records arrival.** Both are stored, because a driver dispute may turn on the difference.

---

## Walkthrough: a parcel's last mile

```
t=0s        Device      GPS fix → POST /pings { vehicle: 4471, lat, lon, 14:32:05 }
t=0.02s     Ingest      validate, dedupe on (vehicleId, recordedAt) → Kafka
t=0.05s     Tracking    SET pos:4471 (overwrite)
t=0.06s     GeoFence    geohash → 4 candidate fences
t=0.07s     GeoFence      fence "customer-88291" (150m): was outside, now inside
t=0.08s     GeoFence    publish VehicleEnteredFence
t=0.10s     Trip        consume → trip T-9931 → status "Arriving"
t=0.12s     ETA         consume → recompute: 2 minutes
t=0.15s     Notify      consume → SMS "Your parcel arrives in about 2 minutes"
t=0.18s     Push        consume → live map updates for that one customer
t=0.20s     History     buffer the ping for the next batch write

t=180s      Driver      marks delivered in the app
t=180.1s    Trip        status = Delivered; capture GPS + photo + signature
t=180.3s    History     store the proof-of-delivery record, permanently
```

The customer got a useful notification **150 milliseconds** after the van crossed an invisible line.

---

## Folder structure

`src/` sits alongside a real [`docker-compose.yml`](docker-compose.yml) — Kafka (key = vehicleId), Redis with persistence on for the geo-fence state, TimescaleDB for the permanent history, and Jaeger.

```
src/
├── Logistics.Contracts/
│   ├── VehiclePing.cs
│   └── Events/  GeoFenceEvents.cs, TripEvents.cs
│
├── Logistics.Ingest/
│   ├── Api/         PingEndpoints.cs      ← accepts single pings AND offline batches
│   ├── Validation/  PingValidator.cs      ← rejects impossible movement
│   └── Publishing/  PingProducer.cs
│
├── Logistics.Tracking/
│   ├── Store/       LatestPositionStore.cs   ← Redis. Overwrite, never append
│   └── Consumers/   PingConsumer.cs
│
├── Logistics.GeoFence/
│   ├── Spatial/
│   │   ├── GeoFenceIndex.cs     ← geohash index. 500,000 → ~5 candidates
│   │   ├── Geohash.cs           ← pure. Fully unit-tested
│   │   └── FenceGeometry.cs     ← circle and polygon containment. Pure
│   ├── State/       FenceStateStore.cs      ← previous inside/outside per vehicle
│   └── Detection/   TransitionDetector.cs   ← hysteresis lives here
│
├── Logistics.Trip/
│   ├── Domain/      Trip.cs, TripState.cs, ProofOfDelivery.cs
│   └── Consumers/   GeoFenceEventConsumer.cs
│
├── Logistics.History/
│   └── Writers/     BatchPingWriter.cs      ← the same batching shape as case study 3
│
└── Logistics.Push/
    ├── Hubs/        TrackingHub.cs
    └── Conflation/  MapConflationBuffer.cs
```

### Why this layout

**`Spatial/` is pure maths.** Geohash encoding, point-in-polygon, and distance are exactly the code that must be right and is easy to get subtly wrong (the international date line, the poles, a polygon that crosses ±180° longitude). Pure functions make these unit tests instead of field reports.

**`State/FenceStateStore.cs` is separate from detection.** The previous inside/outside state is what turns "is inside" into "just entered", and it must survive a restart — otherwise every vehicle currently parked in a depot re-fires "arrived" on deploy.

**`Detection/TransitionDetector.cs` holds the hysteresis.** One file, one concept, testable with a sequence of coordinates.

**`Ingest/Validation/PingValidator.cs` exists** because devices lie. A ping claiming a vehicle moved 400 km in 5 seconds is a GPS glitch, and letting it through corrupts the map, the ETA, and the distance-travelled report all at once.

---

## The code

> Read [HOW-TO-READ-THE-CODE.md](../HOW-TO-READ-THE-CODE.md) first. `TransitionDetector.cs` is the most concrete file in the whole set — three named bugs and their three fixes, in one banner. A good place to start if the other case studies feel abstract.

| File | Shows |
|---|---|
| [`Logistics.GeoFence/Detection/TransitionDetector.cs`](src/Logistics.GeoFence/Detection/TransitionDetector.cs) | Spatial indexing, transition detection, hysteresis |
| [`Logistics.Tracking/Store/LatestPositionStore.cs`](src/Logistics.Tracking/Store/LatestPositionStore.cs) | Latest-value-wins with TTL and out-of-order protection |
| [`Logistics.Ingest/Api/PingEndpoints.cs`](src/Logistics.Ingest/Api/PingEndpoints.cs) | Accepting offline batches and validating impossible movement |

---

## Failure modes

| What fails | What happens | Who notices |
|---|---|---|
| **A vehicle loses signal** | Device buffers; sends a burst later | Map shows the last known position, with a timestamp |
| **Ingest down** | Devices retry; their buffers hold | Positions freeze, then catch up |
| **Tracking (Redis) down** | Live map has no positions | Customers see "location unavailable" — **not** a stale position |
| **GeoFence down** | No arrival notifications | Notifications are late; trips still complete manually |
| **History behind** | Live system unaffected | Only visible to a dispute query |
| **A ping is lost** | Almost nothing — another arrives in 5 s | Nobody |
| **GPS jitter at a boundary** | Hysteresis absorbs it | Nobody, *if* hysteresis exists |
| **No hysteresis** | Thousands of duplicate notifications | **Customers, loudly. And the SMS bill.** |

**The last two rows are the whole point of this case study.** The most expensive failure here is not an outage — it is a correctness bug that sends 400 text messages to one customer.

---

## Now break it

1. **Remove hysteresis.** Park a vehicle exactly on a fence boundary and feed it real GPS jitter. Count the events. Then add hysteresis and count again. The difference is your notification bill.
2. **Remove the previous-state check.** Park a van inside a depot for an hour. Count "arrived" events — you should see roughly 720. Add the check and repeat.
3. **Simulate a 20-minute offline period**, then send the buffered burst. Confirm: history gets all pings, the latest position is *not* set to a 20-minute-old ping, and fence transitions are still detected in the right order.
4. **Send a ping claiming 400 km of movement in 5 seconds.** The validator must reject it. Then remove the validator and watch it corrupt the map, the ETA, and the distance report at once.
5. **Set the key to region instead of vehicle.** Drive a vehicle across a region boundary and check whether its enter/exit events are still ordered correctly. They will not be.
6. **Drop the Redis TTL.** Stop a vehicle's pings. Watch it sit on the map forever, at a position from hours ago, looking perfectly live. Put the TTL back.
7. **Query the history table from the live map path.** Then run a two-year export at the same time. Watch the live map stop for everybody. This is why nothing live reads that table.
8. **Turn off conflation** with 10,000 map viewers. Watch the push service fall over — and note that nothing else does, because each consumer reads the stream at its own pace.
9. **Send the same ping twice** (same vehicle, same timestamp). Confirm the history table's primary key absorbs it and no duplicate distance is recorded.

---

## What this case study teaches

- **One stream can feed three different storage models**, and choosing them separately is the design.
- **Latest-value-wins is a legitimate pattern**, and a key-value overwrite with a TTL is often the right store for "current state" — not a query over history.
- **A TTL is honesty.** Missing is better than stale-pretending-to-be-live.
- **Stateful stream processing is where the hard bugs live.** Transition detection and hysteresis are small ideas that cost real money when missing.
- **Late and out-of-order data can be routine** rather than exceptional, and designing for it beats rejecting it.
- **Recognise when your constraint is softer than the textbook case.** A lost ping here is nearly harmless, and that fact buys a much simpler design than [market data](../03-stock-market-data/) could allow itself.

---

← [Trading app](../04-trading-app/) · [All case studies](../README.md) · [Back to the map](../../README.md)
