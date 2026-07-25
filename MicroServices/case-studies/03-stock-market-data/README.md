# Case Study 3 — Stock Market Data Feed

← [Banking](../02-banking-payments/) · [All case studies](../README.md) · Next: [Trading app](../04-trading-app/)

---

## The business

A market-data platform. It takes raw price updates from an exchange, cleans them, and delivers them to everyone who needs them: charting screens, risk engines, alerting rules, backtesting jobs, and a storage layer.

Scale, on a normal day:

| Measure | Value |
|---|---|
| Instruments | ~5,000 (equities, futures, options) |
| Peak ticks per second | ~200,000 (market open and close) |
| Average ticks per second | ~40,000 |
| Ticks per trading day | ~1.2 billion |
| Consumers | ~15 services, plus ad-hoc backtests |

---

## The constraint

> **Volume beats everything. And every tick must be replayable, because a backtest run in 2029 must see exactly what the market looked like in 2026.**

Two demands that pull in different directions: go extremely fast, and never lose anything.

**Compare with the previous two case studies:**

| | E-commerce | Banking | Market data |
|---|---|---|---|
| Volume | 5k/min peak | 500/sec | **200,000/sec** |
| A lost message means | An order stalls | A regulatory event | A gap in a chart, and a wrong backtest |
| A duplicate means | A double charge | **Unacceptable** | A corrupted candle |
| Latency budget | Seconds | Seconds | **Milliseconds** |
| Replay | Never | Audit | **Constantly — it is a product feature** |

---

## The services

| Service | Job | Scaling shape |
|---|---|---|
| **Feed Handler** | Connect to the exchange, parse the binary protocol, normalise | One per exchange connection. **Cannot** scale horizontally |
| **Normaliser** | Deduplicate, fix bad ticks, enrich with instrument metadata | Scales with partitions |
| **Candle Builder** | Roll ticks into 1m/5m/1h/1d bars | Scales by symbol |
| **Store** | Write to the time-series database | Scales with partitions |
| **Distributor** | Fan out live prices to browsers over WebSocket | Scales with connections |
| **Alert Engine** | Evaluate user rules against each tick | Scales by rule count |
| **Backtest Runner** | Replay history at maximum speed | Scales by job |

### The one that cannot scale

The **Feed Handler** is a single process per exchange connection, because the exchange gives you one sequenced stream and the sequence numbers must be processed in order to detect gaps.

This is worth calling out because it breaks the usual advice. Not everything scales horizontally. The answer here is **hot standby**: two instances, one active, and a fast failover — plus a gap-detection mechanism so a failover that misses ticks is *visible* rather than silent.

---

## Why Kafka, and why nothing else fits

Run the questions from [chapter 11](../../tutorial/11-decision-framework.md):

**Q1. Can the caller continue without an answer?** Yes. The feed handler never waits for anybody. → Async.

**Q2. Does anyone need to replay?** **Yes, constantly.** Backtesting replays months. A new consumer needs history. A bug fix means reprocessing yesterday. → **Event log.**

**Q3. One consumer or many?** Many, and more every quarter. → Topic.

**Q4. What breaks on a duplicate?** A candle counts a trade twice, and volume is wrong. → Dedupe by sequence number.

**Q5. Who owns the data?** The feed handler owns raw ticks. Everyone else reads. → Clean.

Only a log satisfies Q2, and at this volume only Kafka-class throughput satisfies the rate. A queue would work for the delivery, and would make the product impossible.

### Why not a queue

| Requirement | Queue | Kafka |
|---|---|---|
| 200k msg/sec | Struggles; needs sharding you build yourself | Designed for it |
| Replay last month | **Impossible** — acked messages are gone | Seek to an offset |
| 15 independent consumers | 15 copies of every message | One log, 15 cursors |
| Ordering per symbol | Only with one consumer per queue | Per partition, in parallel |
| Cost of storing a day | Not designed to store | Cheap sequential disk |

---

## Partitioning — the most important design decision here

A Kafka topic is split into partitions. The **key** decides which partition a message lands in, and that single choice decides both **ordering** and **parallelism**.

```csharp
await producer.ProduceAsync("market.ticks", new Message<string, Tick>
{
    Key   = tick.Symbol,        // ← this one line decides everything below
    Value = tick
});
```

### What each candidate key would do

| Key | Ordering you get | Parallelism you get | Verdict |
|---|---|---|---|
| `null` (round-robin) | **None** | Maximum | ✗ Candles would be built from out-of-order ticks |
| Constant | Total, global | **1 consumer** | ✗ 200k/sec through one thread. Impossible |
| **Symbol** | Per symbol | Up to partition count | ✓ **Correct** |
| Exchange | Per exchange | 3–4 partitions | ✗ Too coarse; hot partitions |
| `symbol + timestamp` | Effectively none | Maximum | ✗ Ordering lost, which is the thing that matters |

**Symbol is right** because the ordering that actually matters is *within one instrument*. Nothing needs RELIANCE and TCS ordered relative to each other; everything needs RELIANCE's own ticks in sequence.

### How many partitions

```
peak rate                  200,000 ticks/sec
one consumer handles       ~20,000 ticks/sec
minimum partitions         10
headroom for growth (3×)   30
round up                   64 partitions
```

**Over-provision deliberately.** Consumers cannot exceed partitions, and adding partitions later re-hashes keys — which breaks ordering for in-flight symbols. 64 partitions on a topic doing 40k/sec costs almost nothing today and saves a painful migration later ([chapter 4, edge 1](../../tutorial/04-choosing-a-broker.md)).

### The hot-partition problem

Symbols are not equal. On a volatile day, one stock can be 15% of all ticks, and its partition becomes the bottleneck while 63 others idle.

Mitigations, in order of preference:

1. **More partitions** so the hot key is a smaller share of one consumer's work.
2. **A dedicated topic** for the top 20 symbols by volume, with its own consumer group.
3. **Sub-keying** (`RELIANCE-0`, `RELIANCE-1`) — but only for consumers that genuinely do not need per-symbol ordering, such as raw storage.

Never sub-key the candle builder. It needs strict per-symbol order.

---

## The pipeline

```
Exchange (binary, UDP multicast)
    │
    ▼
Feed Handler ──► market.ticks.raw      (64 partitions, key = symbol, 24h retention)
    │
    ▼
Normaliser  ──► market.ticks.clean     (64 partitions, key = symbol, 7d retention)
    │
    ├──────► Candle Builder ──► market.candles  (16 partitions, 90d retention)
    ├──────► Store           ──► TimescaleDB / ClickHouse  (forever)
    ├──────► Distributor     ──► WebSocket to browsers
    └──────► Alert Engine    ──► alerts topic
```

### Why two topics, not one

`raw` is exactly what the exchange sent, warts and all. `clean` is normalised and deduplicated.

**Keeping both matters.** When a candle looks wrong, the first question is "was the raw tick wrong, or did we break it?" With only one topic, that question is unanswerable. 24 hours of raw retention answers it in a minute.

---

## Walkthrough: one tick

```
t=0.000ms   Exchange       UDP packet, binary, 42 bytes
t=0.150ms   Feed Handler   parse → Tick { RELIANCE, 2841.50, 100, seq=8,432,109 }
t=0.180ms   Feed Handler   sequence check: expected 8,432,109 ✓ no gap
t=0.400ms   Feed Handler   produce to market.ticks.raw (async, batched, no ack wait)

t=2.100ms   Normaliser     consume; dedupe on (symbol, seq); price sanity check
t=2.400ms   Normaliser     enrich with lot size, tick size, sector
t=2.600ms   Normaliser     produce to market.ticks.clean

t=4.000ms   Candle Builder consume → update the in-memory 1m bar for RELIANCE
t=4.100ms   Distributor    consume → push to 12,000 subscribed browsers
t=4.200ms   Store          consume → buffer for a batched write
t=4.300ms   Alert Engine   consume → 3 rules match → publish alerts

t=1,000ms   Store          flush 40,000 buffered ticks in ONE batch insert
t=60,000ms  Candle Builder minute closes → emit the final 1m candle → market.candles
```

Exchange to browser in about **4 milliseconds**. Nothing in that path is synchronous.

---

## Key decisions

### Decision 1 — Fire-and-forget producing, with bounded loss

```csharp
var config = new ProducerConfig
{
    Acks             = Acks.Leader,      // NOT All. See below.
    LingerMs         = 5,                // batch for 5ms — huge throughput win
    BatchSize        = 1_000_000,
    CompressionType  = CompressionType.Lz4,
    EnableIdempotence = true             // no duplicates from producer retries
};
```

`Acks.Leader` instead of `Acks.All` means: do not wait for replicas.

**Why:** `Acks.All` roughly triples produce latency. At 200k/sec that is the difference between keeping up and falling behind.

**What you accept:** if the leader broker dies in the window before replication, a few milliseconds of ticks are lost.

**Why that is acceptable here, and only here:** a lost tick is a tiny gap in a chart, and the sequence-gap detector *flags* it so it is visible rather than silent. Compare with [banking](../02-banking-payments/), where a lost message is a regulatory event and `Acks.All` is mandatory. **Same setting, opposite answer, because the business is different.**

### Decision 2 — Gap detection is a first-class feature

The exchange gives every tick a sequence number. The feed handler tracks it:

```csharp
if (tick.SequenceNumber != expected)
{
    var missing = tick.SequenceNumber - expected;

    // A gap is DATA, not just a log line. Downstream consumers mark their
    // candles "incomplete" so nobody backtests against a hole and gets a
    // confident, wrong answer.
    await producer.ProduceAsync("market.gaps", new GapDetected(
        symbol, expected, tick.SequenceNumber - 1, missing));

    metrics.GapDetected(symbol, missing);
}
```

**The principle: a system that can lose data must be able to say where.** Silent loss is far more damaging than visible loss, because it produces confident wrong answers.

### Decision 3 — Conflation for the browser, not for the engine

12,000 browsers cannot each receive 200,000 updates a second, and no human can read them.

So the Distributor **conflates**: it keeps only the latest price per symbol and sends a snapshot 10 times a second.

```csharp
// Latest value wins. Intermediate ticks are DELIBERATELY dropped for display.
_latest[tick.Symbol] = tick;

// Every 100ms, flush what changed.
foreach (var (symbol, tick) in _latest.DrainChanged())
    await hub.Clients.Group($"sym:{symbol}").PriceUpdate(tick);
```

**Crucially, this happens only on the display path.** The Candle Builder, the Store, and the Alert Engine all see every tick. Conflating for them would corrupt volume, miss the day's high, and skip an alert.

> **The lesson: different consumers of the same stream may need different completeness guarantees.** That is only possible because Kafka lets each consumer read the full log at its own pace.

### Decision 4 — Batch writes, always

Writing 200,000 rows individually is impossible. Writing 200,000 rows in batches of 10,000 is routine.

```csharp
// Flush on whichever comes first: 10,000 rows, or 1 second.
// The time bound matters — without it, a quiet symbol's last few ticks
// sit in a buffer until the next busy period, which can be hours.
if (_buffer.Count >= 10_000 || _sinceFlush.Elapsed > TimeSpan.FromSeconds(1))
    await FlushAsync(ct);
```

**And commit the Kafka offset only *after* the flush succeeds.** Committing first means a crash loses the buffer permanently, with no way to know what was lost.

### Decision 5 — Retention tiers, priced deliberately

| Topic | Retention | Why |
|---|---|---|
| `market.ticks.raw` | 24 hours | Debugging only. Huge volume |
| `market.ticks.clean` | 7 days | Consumer recovery, short reprocessing |
| `market.candles` | 90 days | Charts and most analysis |
| TimescaleDB | Forever | The real archive |
| Cold object storage | Forever, cheap | Backtests older than 90 days |

Keeping 1.2 billion ticks a day in Kafka forever would cost more than the business. Kafka is the **transport and short-term buffer**; the database is the archive. Backtests older than 90 days read from cold storage, not from Kafka.

---

## Folder structure

`src/` sits alongside a real [`docker-compose.yml`](docker-compose.yml) — Kafka tuned for throughput, TimescaleDB, Prometheus/Grafana with a consumer-lag exporter, and Jaeger. The topic-creation commands (partition counts matter) are in the file's header comment.

```
src/
├── MarketData.Contracts/
│   ├── Tick.cs                    ← the core type. Struct, not class. See below.
│   ├── Candle.cs
│   └── GapDetected.cs
│
├── MarketData.FeedHandler/
│   ├── Exchange/
│   │   ├── IExchangeConnection.cs
│   │   ├── NseFeedConnection.cs   ← the binary protocol lives here, and nowhere else
│   │   └── SequenceTracker.cs     ← gap detection
│   ├── Publishing/
│   │   └── TickProducer.cs        ← batched, compressed, fire-and-forget
│   └── Program.cs
│
├── MarketData.Normaliser/
│   ├── Consumers/  TickNormaliser.cs
│   ├── Rules/      PriceSanityRule.cs, DuplicateRule.cs, StaleQuoteRule.cs
│   └── Enrichment/ InstrumentCache.cs   ← loaded once, never a per-tick lookup
│
├── MarketData.CandleBuilder/
│   ├── Aggregation/ CandleAggregator.cs   ← pure. No I/O. Fully unit-tested.
│   ├── Consumers/   TickConsumer.cs
│   └── State/       CandleStateStore.cs   ← survives a restart
│
├── MarketData.Store/
│   ├── Writers/    BatchTickWriter.cs
│   └── Schema/     hypertable definitions
│
├── MarketData.Distributor/
│   ├── Hubs/         PriceHub.cs
│   ├── Conflation/   ConflationBuffer.cs   ← latest value wins
│   └── Subscriptions/SubscriptionRegistry.cs
│
└── MarketData.Backtest/
    └── Replay/     HistoricalReplayer.cs   ← seeks to an offset and reads at full speed
```

### Why this layout

**`Tick` is a struct.** At 200,000 allocations a second, a class means the garbage collector becomes your bottleneck. This is one of the rare cases where that choice is worth making explicitly.

**`Aggregation/CandleAggregator.cs` is pure** — no Kafka, no database, no clock. Candle maths is where subtle bugs live (a tick exactly on a boundary, a day with a late open, a stock that does not trade for an hour). Pure code makes those a unit test instead of a production incident.

**`Exchange/` is an anti-corruption layer.** The exchange's binary protocol is awful and it changes. It is contained in one folder, and the rest of the system only sees `Tick`.

**`State/CandleStateStore.cs` exists** because a half-built candle lives in memory. Without persistence, a restart at 10:30 loses the 10:00–10:30 bar entirely.

---

## The code

> Read [HOW-TO-READ-THE-CODE.md](../HOW-TO-READ-THE-CODE.md) first. `CandleAggregator.cs` is pure logic with no infrastructure — start there, and read its test list at the bottom before the code.

| File | Shows |
|---|---|
| [`MarketData.Contracts/Tick.cs`](src/MarketData.Contracts/Tick.cs) | A high-volume value type, and why it is a struct |
| [`MarketData.FeedHandler/Publishing/TickProducer.cs`](src/MarketData.FeedHandler/Publishing/TickProducer.cs) | Partitioning, batching, backpressure, gap detection |
| [`MarketData.CandleBuilder/Aggregation/CandleAggregator.cs`](src/MarketData.CandleBuilder/Aggregation/CandleAggregator.cs) | Pure aggregation with out-of-order and boundary handling |
| [`MarketData.Store/Writers/BatchTickWriter.cs`](src/MarketData.Store/Writers/BatchTickWriter.cs) | Batching, and committing offsets only after a durable write |
| [`MarketData.Distributor/Conflation/ConflationBuffer.cs`](src/MarketData.Distributor/Conflation/ConflationBuffer.cs) | Latest-value-wins for the display path |

---

## Failure modes

| What fails | What happens | Who notices |
|---|---|---|
| **Feed handler crashes** | Standby takes over in ~2 s; the gap is detected and published | Charts show a marked gap |
| **Kafka broker down** | Producer buffers, then blocks; ticks are lost after the buffer fills | Gap events; consumer lag |
| **Normaliser lags** | Downstream sees stale prices | Consumer-lag alert |
| **Candle builder restarts** | Rebuilds partial candles from state, replays from its last offset | Nobody, if state persistence works |
| **Store falls behind** | Buffer grows; consumer lag climbs | Lag alert; disk pressure |
| **Distributor down** | Browsers disconnect and reconnect | Users see a "reconnecting" banner |
| **One symbol is 15% of volume** | That partition lags while others idle | Per-partition lag metric |
| **Exchange sends a bad tick** (₹0.01 for a ₹2,800 stock) | The sanity rule rejects it and publishes to a quarantine topic | Nobody — this is the system working |

**Consumer lag per partition is the single most important metric here.** Not CPU, not memory. Lag tells you whether you are keeping up, and it tells you 20 minutes before anyone else notices.

---

## Now break it

1. **Set the key to `null`.** Watch candles get built from out-of-order ticks. Compare the high/low against a known-good run. This is the fastest way to feel why partitioning matters.
2. **Set the key to a constant.** Watch throughput collapse to one consumer, and lag grow without bound.
3. **Publish the same tick twice.** Confirm the dedupe rule drops it. Then remove the dedupe and check the candle's volume — it will be double, and nothing will error.
4. **Drop a sequence number.** Confirm a `GapDetected` event is published and the affected candle is flagged incomplete. Silent gaps are the failure to fear.
5. **Kill the candle builder at 10:30**, mid-bar. Restart. Is the 10:00–10:30 candle correct, or lost? If lost, your state store is not doing its job.
6. **Commit the Kafka offset *before* the batch write.** Kill the store mid-batch. Count the missing rows. Then put the commit after the write and repeat — zero missing.
7. **Replay yesterday from offset 0.** Confirm you get byte-identical candles. If not, something in your pipeline is non-deterministic — a wall clock, a random ordering, or an unkeyed parallel step. Find it.
8. **Make one symbol 50% of the volume.** Watch its partition lag while others idle. Now try each mitigation from the hot-partition list and measure the difference.
9. **Set `Acks.All`.** Measure the throughput drop. That number is the price of durability, and now you can have an informed argument about paying it.
10. **Connect 10,000 WebSocket clients** and turn conflation off. Watch the Distributor die. Turn it back on. Note that no other consumer was affected — that isolation is what the log bought you.

---

## What this case study teaches

- **The partition key is the most consequential line of code in a streaming system.** It sets ordering and parallelism at the same time.
- **Different consumers of one stream can have different guarantees.** Conflate for the eye, never for the engine.
- **Durability is a dial, not a switch.** `Acks.Leader` is right here and wrong in [banking](../02-banking-payments/) — same setting, different business.
- **Visible loss beats silent loss.** Gap detection is a feature, not error handling.
- **Batch everything on the write path.** Per-row writes are impossible at this scale.
- **Not everything scales horizontally.** The feed handler is a single process, and hot standby is the honest answer.
- **Retention is a budget decision** you must make deliberately, before an investigation makes it for you.

---

← [Banking](../02-banking-payments/) · [All case studies](../README.md) · Next: [Trading app](../04-trading-app/)
