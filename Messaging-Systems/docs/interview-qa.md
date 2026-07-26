# Interview Q&A — Messaging Systems

41 questions with model answers. Answers are collapsed — read the question, answer it out loud, *then* open the block. Reading the answers straight through teaches you much less.

**Role tags** show who is typically asked each question. They are a guide, not a rule: an Architect who cannot answer the beginner questions crisply is a red flag, and an SDE I who nails an advanced one has just made an impression.

| Tag | Role |
|---|---|
| **SDE I** | Junior / graduate engineer |
| **SDE II** | Mid-level engineer |
| **Senior** | Senior engineer |
| **Architect** | Staff / principal / solution architect |
| **SRE** | Site reliability / platform engineer |

**Sections:** [Beginner (1–15)](#beginner) · [Intermediate (16–30)](#intermediate) · [Advanced (31–41)](#advanced)

---

## Beginner

### 1. What is a message broker, and why would you use one instead of a direct API call?
`SDE I` `SDE II`

<details><summary>Answer</summary>

A broker is a server that sits between two programs and holds messages for them. The sender hands over a message and moves on; the receiver picks it up when ready.

Use one when you need:
- **Decoupling** — the sender does not need the receiver to be running
- **Buffering** — absorb a traffic spike instead of failing under it
- **Fan-out** — one event, many independent consumers
- **Retry** — the broker holds the message until the work succeeds

Use a direct API call when you need an answer *right now* to continue — a price quote, an availability check, an auth decision.

**The strong version of this answer** adds the counter-case: a broker is not free. It is another system to run, another failure mode to learn, another hop to debug. At low volume with one consumer, a database table polled by a worker is simpler and transactional with your business data.
</details>

---

### 2. Explain the difference between a queue and a topic.
`SDE I`

<details><summary>Answer</summary>

- **Queue** — point to point. Many workers can compete, but each message goes to exactly **one** of them. Used for work distribution: "somebody process this order".
- **Topic** — publish/subscribe. Each subscriber gets its **own copy** of every message. Used for notification: "an order was placed, whoever cares".

The word "topic" is overloaded and it is worth saying so:
- **Service Bus topic** — a fan-out point; each subscription is an independent durable copy.
- **Kafka topic** — a partitioned log. Fan-out comes from *consumer groups*, not from the topic itself.
- **RabbitMQ** has no topics; it has *exchanges* that route to queues.
</details>

---

### 3. What is a dead-letter queue?
`SDE I` `SDE II`

<details><summary>Answer</summary>

A place messages go after they have failed too many times, so they stop blocking everything behind them and wait for a human.

Messages land there when:
- A retry limit is exceeded
- The TTL expires before processing
- The consumer explicitly rejects the message as unprocessable

Support differs sharply:
- **Service Bus** — built in. Every queue and subscription has one, automatically.
- **RabbitMQ** — a dead-letter exchange you wire up. In return you get the `x-death` header, which records the original queue, reason, count and timestamp.
- **Kafka** — no native concept. A DLQ is a normal topic plus the discipline to add reason headers.

**The point that separates a good answer:** a DLQ nobody reads is a slow-motion data-loss machine. It needs an alert on depth > 0 and a named owner.
</details>

---

### 4. What does "at-least-once delivery" mean?
`SDE I` `SDE II`

<details><summary>Answer</summary>

The broker guarantees the message arrives, but it may arrive more than once.

It happens because the consumer does the work *then* acknowledges. If the acknowledgement is lost — network blip, process restart, expired lock — the broker assumes failure and redelivers. The work happens twice.

The alternative, at-most-once, acknowledges first and does the work after, so a crash in between loses the message silently.

All three brokers in this comparison are at-least-once in practice. **Duplicates are normal operation, not a fault.** The consumer must be idempotent.
</details>

---

### 5. What is consumer lag?
`SDE I` `SRE`

<details><summary>Answer</summary>

How far behind a consumer is — the gap between the newest message and the last one the consumer processed. In Kafka it is measured in messages: `log-end-offset − committed-offset`.

Non-zero lag is normal. Growing lag means consumers are slower than producers.

**The answer that shows operational experience:** read lag as a *derivative*, not a level. Lag of 50,000 that is falling is fine. Lag of 5,000 that is climbing is an incident. Alert on the trend and on estimated time-to-drain, not the raw number — otherwise every traffic spike pages someone for a system that is working correctly.
</details>

---

### 6. What is a partition in Kafka?
`SDE I` `SDE II`

<details><summary>Answer</summary>

One ordered slice of a topic. A topic with 12 partitions is 12 independent append-only logs.

Partitions serve two purposes at once, which is why they matter so much:
1. **Parallelism** — each partition is read by one member of a consumer group, so 12 partitions means up to 12 concurrent consumers.
2. **Ordering** — messages within a partition are strictly ordered; across partitions there is no order at all.

Messages with the same key always go to the same partition, which is how you get per-entity ordering for free.

**The trap worth mentioning:** partition count can be increased but never decreased, and increasing it changes the key-to-partition mapping — so ordering for in-flight keys breaks across the change. Size it up front.
</details>

---

### 7. What is the difference between a Kafka consumer group and a single consumer?
`SDE I`

<details><summary>Answer</summary>

A consumer group is a named team that splits the partitions between its members. Each partition goes to exactly one member; add a member and the partitions redistribute.

Two consumers in the **same** group split the work. Two consumers in **different** groups each get *all* the messages, independently, with their own bookmarks.

That is Kafka's fan-out mechanism: adding an eleventh consumer group costs the broker almost nothing, because it is just another sequential read of the same file.
</details>

---

### 8. Why do we need message acknowledgement?
`SDE I`

<details><summary>Answer</summary>

So the broker knows the work actually happened. Until you acknowledge, the broker holds the message and assumes you might fail.

If a consumer takes a message and dies, the un-acknowledged message becomes available again and another consumer picks it up. Without acknowledgement, that message would be lost.

**The critical ordering:** acknowledge *after* the work, never before. Acknowledging first is at-most-once and loses messages. This is one line of code and it is the difference between losing orders and not.
</details>

---

### 9. What is a routing key in RabbitMQ?
`SDE I` `SDE II`

<details><summary>Answer</summary>

A label the publisher attaches to a message. The exchange compares it against binding patterns to decide which queues get a copy.

With a topic exchange, `order.eu.placed` matches:
- `order.*.placed` — `*` is exactly one word
- `order.eu.*`
- `#` — zero or more words, so it matches everything
- but **not** `order.us.*`

The publisher never names a queue. That indirection is the point of RabbitMQ: add a binding and a new consumer starts receiving a filtered slice of an existing stream, with no producer change and no redeploy.
</details>

---

### 10. What happens if a consumer is slower than the producer?
`SDE I` `SRE`

<details><summary>Answer</summary>

Messages accumulate. What happens next differs by broker, and the differences matter:

- **Kafka** — lag grows. The broker is unbothered; messages sit on disk until retention expires. If retention expires before you catch up, **you lose data you never read**.
- **RabbitMQ** — the queue grows in memory. Cross the memory watermark and the broker **blocks all publishers cluster-wide** — one slow consumer becomes everyone's outage.
- **Service Bus** — the queue grows to its size limit, then sends are rejected.

Fixes: scale consumers out (up to the partition count on Kafka), make the handler faster, or apply backpressure at the producer.
</details>

---

### 11. What is idempotency and why does it matter here?
`SDE I` `SDE II` `Senior`

<details><summary>Answer</summary>

Doing an operation twice has the same effect as doing it once.

It matters because every broker here delivers at-least-once, so duplicates will happen. Without idempotency you double-charge a customer.

Two ways to get it:
1. **Dedupe store** — every message carries a deterministic id; the consumer records processed ids with a unique constraint and skips repeats.
2. **Naturally idempotent operations** — `SET status = 'shipped'` is safe to repeat; `balance = balance - 50` is not.

**The detail that separates a real answer:** the id must be *deterministic* — derived from the business event, like `order-123:OrderPlaced`. `Guid.NewGuid()` produces a different id on every retry, which defeats the entire mechanism.
</details>

---

### 12. What is TTL on a message?
`SDE I`

<details><summary>Answer</summary>

Time to live — how long a message stays valid. After that it is deleted, or moved to the dead-letter queue if configured.

Useful when stale work is worse than no work: a payment authorisation from 30 minutes ago, or a "your driver is 2 minutes away" notification.

Support differs:
- **Service Bus** — per message and per queue
- **RabbitMQ** — per message and per queue (and the per-queue version enables the delayed-retry trick)
- **Kafka** — **topic-level retention only.** No per-message TTL exists.
</details>

---

### 13. What does "durable" mean for a queue or message?
`SDE I` `SRE`

<details><summary>Answer</summary>

It survives a broker restart, because it was written to disk rather than held only in memory.

In RabbitMQ this needs **two** independent settings and people routinely set only one:
- `durable: true` on the **queue** — the queue definition survives
- `Persistent = true` on the **message** — the message body survives

Either alone loses data. A persistent message in a non-durable queue dies with the queue.

Kafka is disk-first by design — everything is written to a log file. Service Bus persists everything; there is nothing to configure.
</details>

---

### 14. When would you NOT use a message broker?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

- You need the answer immediately to continue — use a synchronous call
- Volume is low (hundreds/sec) with one consumer — a database table polled by a worker is simpler and transactional with your data
- The work is a scheduled batch — use a scheduler
- The two components are already in the same process and always deployed together
- Nobody will own the broker operationally

A broker adds a system to run, a failure mode to learn, and a hop to debug. That is worth it often, but not by default. "We might need to scale later" is not a reason to add one now.
</details>

---

### 15. What is the difference between push and pull delivery?
`SDE I` `SDE II`

<details><summary>Answer</summary>

- **Push** — the broker sends messages to the consumer as they arrive. Lower latency; the broker must manage flow control so it does not overwhelm a slow consumer. RabbitMQ and Service Bus push.
- **Pull** — the consumer asks for messages when ready. Natural backpressure, because a busy consumer simply does not ask. Kafka pulls.

The consequences show up in tuning. RabbitMQ's push model needs **prefetch** to limit how many unacknowledged messages a consumer holds. Kafka's pull model needs **poll interval** limits so a consumer that stops asking is detected as dead.
</details>

---

## Intermediate

### 16. Explain exactly-once semantics. Is it real?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

Partly. The honest answer names the boundary.

**Real:** Kafka's transactional producer gives exactly-once **within Kafka**. Reading an input topic, writing an output topic, and committing the offset all land atomically. Genuinely works.

**Not real:** exactly-once across Kafka and your database, or Kafka and a payment API. Two independent systems cannot commit atomically without a distributed transaction protocol nobody wants to run.

So what you actually build is:

> **Effectively-once = at-least-once delivery + idempotent consumer.**

The broker may deliver five times. The consumer checks a key, sees it has already done the work, and skips. The side effect happens once.

**This is a trap question.** Answering a flat "yes, Kafka has exactly-once" is the wrong answer. Naming the boundary is the right one.
</details>

---

### 17. How do you guarantee message ordering?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

First, establish *what* needs ordering. Global ordering means one partition and one consumer — no parallelism — and is almost never a real requirement. Per-entity ordering is what people mean 95% of the time.

| Broker | Mechanism | Parallelism cost |
|---|---|---|
| **Kafka** | Same key → same partition | **None.** Different keys run concurrently. |
| **Service Bus** | `SessionId` | High — one worker per session at a time |
| **RabbitMQ** | One queue, one consumer | Total — or use the consistent-hash plugin |

Kafka has the best ordering story of the three because ordering costs it nothing.

**The follow-up that catches people:** what breaks ordering in Kafka? Increasing the partition count changes the key-to-partition mapping, so a key can move partitions and its in-flight messages can be processed out of order across the change.
</details>

---

### 18. What is the outbox pattern and what problem does it solve?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

It solves the **dual-write problem**: "save the order to the database, then publish an event" is two operations, and the first can succeed while the second fails. The order exists and nobody downstream ever hears about it. Retry logic cannot fix this, because the process can die between the two.

The pattern:
1. In **one** database transaction, write the business row **and** a row in an `outbox` table. No broker involved.
2. A separate process polls the outbox for unsent rows, in order.
3. It publishes each and waits for the broker confirm.
4. Only then marks the row sent.
5. Crash between 3 and 4? It publishes twice — absorbed by the consumer's idempotency check.

**The better version:** point Debezium (CDC) at the outbox table so rows publish from the database transaction log. No polling, lower latency, one fewer process.
</details>

---

### 19. How does Kafka achieve durability?
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

Replication, not fsync. Each partition has N replicas on different brokers; one is leader, the rest follow.

The contract needs **two** settings, and setting only one is a common and dangerous mistake:

```
acks=all                  # producer: wait for all in-sync replicas
min.insync.replicas=2     # broker: "all in-sync" must mean at least 2
```

`acks=all` alone is theatre. If the in-sync set has shrunk to one replica, "all" means "one" — and a broker failure loses acknowledged data. With `min.insync.replicas=2`, the broker rejects the write instead. Loud failure over silent loss.

Also: `unclean.leader.election.enable=false`. When true, an out-of-sync replica can become leader and silently discard records the old leader had acknowledged.
</details>

---

### 20. Explain prefetch and why the default is dangerous.
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

Prefetch is how many un-acknowledged messages the broker will push to one consumer at once.

**RabbitMQ's default is unlimited.** The first consumer to connect pulls the entire queue into its own memory while every other consumer sits idle. Two consequences: no load balancing, and that memory counts toward the watermark that blocks publishers cluster-wide.

The fix is one line: `BasicQos(prefetchCount: 20, global: false)`.

Both directions are wrong:
- Too low → consumers idle between round trips (`consumer_utilisation` near 0.3)
- Too high → uneven distribution and memory pressure

Rule of thumb: (messages/sec you handle) × (round-trip seconds) × 2. Start at 20.

**On Service Bus prefetch is worse than inefficient — it is a correctness issue.** Prefetched messages hold their locks from the moment they land in your buffer. Prefetch 100 with a 2-second handler means later messages sit locked for minutes, expire, and get redelivered to other workers. `PrefetchCount = 0` is the safe default.
</details>

---

### 21. How do you handle a poison message?
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

A poison message fails every time no matter how often you retry. Left unhandled it blocks the partition (Kafka) or spins a consumer at 100% CPU forever (RabbitMQ with `requeue: true`).

**Three-tier retry:**
1. **In-process** — 3 attempts, exponential backoff (200ms, 400ms, 800ms). Catches blips. Keep the total under your poll interval or lock duration.
2. **Delayed retry** — republish with a delay: a Service Bus scheduled message, a RabbitMQ TTL queue, a Kafka retry topic. Catches "the database was down for two minutes".
3. **Dead-letter** — after N attempts, park it with the failure reason. A human decides.

**The classification rule that matters most:** retry transient failures, dead-letter permanent ones, immediately. A malformed JSON body will never parse. A declined card will never be approved. Retrying either five times is five wasted deliveries and five misleading log lines.
</details>

---

### 22. What is a rebalance and why is it a problem?
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

Kafka redistributing partitions across a consumer group when a member joins or leaves.

Two strategies:
- **Eager** (old default) — stops the *entire* group, reassigns everything, restarts. Every rolling deploy becomes a group-wide stall.
- **Cooperative sticky** (use this) — moves only the partitions that must move; other members keep working.

**The rebalance loop is the classic Kafka outage.** A consumer takes longer than `max.poll.interval.ms` to process a batch. The group evicts it mid-work. That triggers a rebalance. Work restarts. It takes too long again. Forever. Symptoms: sawtoothing throughput, logs full of assignment churn.

**The fix is `max.poll.interval.ms`, not `session.timeout.ms`** — and reaching for session timeout is the wrong turn almost everyone takes first. Heartbeats run on a background thread and are fine; it is your *processing* that is too slow.

Also worth knowing: **static membership** (`group.instance.id`) lets a member that restarts within the session timeout reclaim its exact partitions with no rebalance at all.
</details>

---

### 23. Compare Kafka's fan-out with RabbitMQ's and Service Bus's.
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

- **Kafka** — one copy of the data on disk. Each consumer group reads it independently with its own offset. Adding the eleventh group costs almost nothing: another sequential read of the same file.
- **RabbitMQ** — the exchange writes a **full copy into each bound queue**. Ten consumers means ten copies stored, ten times the memory and disk.
- **Service Bus** — each subscription is an independent copy, same as RabbitMQ.

This is Kafka's strongest structural advantage and the reason it wins for event streaming.

It also explains the "we might add consumers later" heuristic: on Kafka that is free; on the other two it is a real capacity decision.
</details>

---

### 24. When would you choose Service Bus over Kafka?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

- You are on Azure and want **zero** brokers to operate
- The workload is business workflow — orders, payments, approvals — not a firehose
- You need sessions, per-message scheduling, per-message TTL, or broker-side content filtering
- Throughput is under ~10k msg/sec
- Messages can be large (up to 100 MB on Premium)
- Compliance matters and inheriting Azure's certifications is worth real money
- The team is small and its time is better spent on the domain

**And the disqualifier, stated up front:** if anyone says "we might want to reprocess these events later", Service Bus is out on its own — unless you pair it with Event Hubs. Completed means deleted, and no configuration changes that.
</details>

---

### 25. How do you scale consumers, and what limits you?
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

| Broker | Ceiling |
|---|---|
| **Kafka** | **Partition count.** Extra consumers sit idle doing nothing. |
| **Service Bus** | No message ceiling — but with sessions, concurrency is bounded by *active sessions*, not messages |
| **RabbitMQ** | No broker ceiling. Downstream dependencies become the limit. |

**Scale on lag or queue depth, never on CPU.** A worker blocked on a slow payment API uses no CPU while the backlog grows to a million. This is the most common autoscaling mistake in messaging, and it fails silently in exactly the situation where you needed it to work.

Use KEDA — it has scalers for all three.

**The Service Bus sessions ceiling surprises people during their first load test:** forty pods against eight active order sessions leaves thirty-two pods idle while the backlog grows.
</details>

---

### 26. What is log compaction and when would you use it?
`SDE II` `Senior` `Architect`

<details><summary>Answer</summary>

A Kafka retention policy that keeps only the **newest value per key** and discards older values for the same key. The topic becomes a rebuildable table with a change history.

- `cleanup.policy=delete` — drop segments older than the retention window. For **events**: "order placed" is a fact that expires.
- `cleanup.policy=compact` — keep the latest per key forever. For **state**: "the current price of SKU-42".

Use compaction for state that a new service needs to bootstrap from: current inventory levels, latest customer profile, config. A new consumer reads the compacted topic from the beginning and arrives at current state without querying anyone's database.

Writing a null value (a **tombstone**) marks a key deleted. That is also one of the few GDPR-erasure mechanisms available on Kafka.

**The design error to avoid:** compacting an event stream. You lose intermediate events, which is exactly what an event stream is for.
</details>

---

### 27. How would you migrate from RabbitMQ to Kafka?
`Senior` `Architect`

<details><summary>Answer</summary>

**Never migrate messages. Migrate producers and consumers.** Copying queue contents is almost always wrong: formats differ, ids do not survive, ordering breaks, rollback is impossible.

Four phases:
1. **Prepare** — stand up Kafka in production, topology as code, and **make consumers idempotent first** (prerequisite, because the bridge will produce duplicates).
2. **Bridge and shadow** — a bridge *copies* (never moves) from Rabbit to Kafka. New consumers run in shadow: process, compute, **do not write**. Compare outputs.
3. **Cut over** — feature flag per message type. Least critical first, 5% → 50% → 100%, watching a full business cycle between steps.
4. **Retire** — drain Rabbit to zero, keep it read-only 30 days, then delete.

**The Rabbit-to-Kafka-specific trap:** Kafka has no routing. Every exchange binding becomes either a separate topic or consumer-side filtering. Mapping that is usually the largest single piece of work, and it should be done before any code is written.

Every phase must roll back in under 15 minutes.
</details>

---

### 28. What metrics would you alert on?
`SDE II` `SRE`

<details><summary>Answer</summary>

**All three:** DLQ depth **> 0** — always, no exceptions. That is the one alert nobody should argue about.

**Kafka**
- `UnderReplicatedPartitions > 0` for 5 min
- `OfflinePartitionsCount > 0` — page immediately, data is unavailable
- `ActiveControllerCount != 1`
- Consumer lag > 5 minutes of traffic, sustained
- Disk > 85%

**RabbitMQ**
- `connections_blocked > 0` — page. Publishers are stalled cluster-wide.
- `messages_ready` above threshold for 10 min
- Non-empty `partitions` in cluster status
- Memory > 70% of the watermark

**Service Bus**
- `ThrottledRequests > 0`
- `ActiveMessages` > 10 min of traffic
- `NamespaceCpuUsage > 70%`
- `ServerErrors > 0`

**The judgement to show:** alert on trend and time-to-drain, not raw level. Falling lag of 50,000 is fine. Climbing lag of 5,000 is an incident.
</details>

---

### 29. Explain the difference between Kafka's `acks` settings.
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

| Setting | Waits for | Risk |
|---|---|---|
| `acks=0` | Nothing — fire and forget | Loses messages freely. Telemetry only. |
| `acks=1` | The leader only | Lose the leader before followers replicate → data lost |
| `acks=all` | All in-sync replicas | Safe **if paired with `min.insync.replicas`** |

The nuance that matters: `acks=all` means "all *in-sync* replicas", and the in-sync set can shrink. If it shrinks to one, "all" means "one" and you are back to `acks=1` without noticing.

That is why `min.insync.replicas=2` is mandatory alongside it. With RF=3 and min.insync=2 you survive losing one broker; lose two and writes are rejected rather than silently unsafe.

**Setting `acks=all` alone and believing you are durable is one of the most common Kafka misconfigurations.**
</details>

---

### 30. What is backpressure and how does each broker handle it?
`SDE II` `Senior` `SRE`

<details><summary>Answer</summary>

The system signalling that it cannot keep up, so producers slow down instead of making things worse.

- **Kafka** — the producer's local buffer fills, then `ProduceAsync` blocks or throws `Queue full`. The broker itself rarely pushes back; it just accumulates and lag grows.
- **RabbitMQ** — the memory or disk watermark **blocks all publishers cluster-wide**. Effective, and brutally coarse: one deep queue stalls every publisher in the cluster.
- **Service Bus** — the entity hits its size limit and sends are rejected; the tier throttles with `ServiceBusy`.

**The RabbitMQ mitigation worth naming:** bound every queue with `x-max-length` and `x-overflow: reject-publish`. That rejects publishes to *one* queue instead of blocking publishers to *all* of them. The blast-radius difference is enormous and the setting is free.
</details>

---

## Advanced

### 31. Design an ordering guarantee for a system where one customer generates 100× the traffic of others.
`Senior` `Architect`

<details><summary>Answer</summary>

This is **partition skew**. Keying by `customerId` sends all of that customer's traffic to one partition, whose consumer saturates while the others idle. Lag on one partition, low CPU everywhere.

First: **establish the real ordering unit.** Usually it is per *order* or per *account*, not per *customer*. If per-order ordering is sufficient, key by `orderId` and the problem disappears — that is the cheapest fix and it is often available.

If customer-level ordering is genuinely required:

**Composite key with bounded sub-sharding.** Split the hot customer across N sub-partitions while keeping ordering within each:

```csharp
var shard = IsHotCustomer(customerId)
    ? orderId.GetHashCode() % 16      // 16 ordered lanes for the whale
    : 0;
var key = $"{customerId}:{shard}";
```

Ordering now holds per `(customer, shard)`. That is a genuine relaxation and it must be a documented, agreed trade — not a silent one.

**Alternatives worth naming:**
- Dedicated topic and consumer fleet for the hot tenant — isolates blast radius, adds routing complexity
- Two-stage processing: parallel ingest, then a sequencer that orders within a window
- On Service Bus: a `SessionId` per sub-shard, same idea

**The senior signal is asking whether the ordering requirement is real before engineering around it.** Most "we need ordering per customer" requirements are actually "we need ordering per order", and nobody has checked.
</details>

---

### 32. How would you implement exactly-once processing from Kafka into a database?
`Senior` `Architect`

<details><summary>Answer</summary>

You cannot, and saying so clearly is the answer. Kafka transactions do not span an external database. What you build is **effectively-once**.

**Algorithm:**
1. Consumer reads a message carrying a deterministic id.
2. Open a database transaction.
3. Insert the id into a `processed_messages` table with a **unique constraint**.
4. Unique violation → already processed. Roll back, acknowledge, done.
5. Otherwise do the business work **in the same transaction**.
6. Commit. The id and the effect land atomically.
7. Commit the Kafka offset **after** the database commit.
8. Crash between 6 and 7 → the message redelivers, step 4 catches it.

```csharp
await using var tx = await _db.BeginTransactionAsync(ct);
try { await _db.ExecuteAsync("INSERT INTO processed_messages(message_id) VALUES(@id)", new { id }, tx); }
catch (UniqueConstraintViolation) { return; }        // step 4

await DoWorkAsync(order, tx, ct);                    // step 5 — SAME transaction
await tx.CommitAsync(ct);                            // step 6
_consumer.Commit(offset + 1);                        // step 7
```

**The alternative worth mentioning:** store the Kafka *offset itself* in the same database transaction, and on startup seek to the stored offset instead of using committed offsets. That removes the dedupe table entirely and makes the database the single source of truth for position. It is the cleanest version, and it requires `assign()` rather than `subscribe()`, so you give up automatic rebalancing.

**Ordering matters in step 3–7.** Recording the id before the work, in a separate transaction, creates a window where a crash marks work done that never happened — strictly worse than a duplicate.
</details>

---

### 33. A consumer group is stuck. Walk through your diagnosis.
`Senior` `SRE`

<details><summary>Answer</summary>

**First, distinguish stuck from slow.** They look identical on a lag graph and have opposite fixes.

```bash
# Run twice, 30 seconds apart. Compare CURRENT-OFFSET.
kafka-consumer-groups.sh --bootstrap-server $BS --describe --group payments-service
```

| Between runs | Diagnosis |
|---|---|
| Offset not moving | **Stuck** |
| Moving, slower than the topic grows | **Too slow** — scale or optimise |
| Moving on some partitions only | **Skew** — see Q31 |
| `CONSUMER-ID` empty | **No active members** — the group is dead, not slow |

**If stuck, check for a rebalance loop first** — most common, least obvious:

```bash
kubectl logs deploy/payment-worker | grep -iE "rebalanc|revoked|assigned"
```

Repeated Revoked/Assigned every few seconds means processing exceeds `max.poll.interval.ms`. Raise the poll interval or process fewer records per poll. **Not** session timeout.

**If not a rebalance loop:** poison message. Find the wedged offset, read that exact record without joining the group:

```bash
kafka-console-consumer.sh --bootstrap-server $BS --topic orders.v1 \
  --partition 7 --offset 1044235 --max-messages 1 --property print.headers=true
```

**Then check, in order:** a thread dump (deadlock on a downstream call), liveness probes killing busy pods (climbing RESTARTS — the pod is healthy, the probe is wrong), and `STATE: PreparingRebalance` persisting, which means one stuck member is holding the whole group hostage.

**Only after capturing the message** do you skip past it — with the group stopped, since offset reset requires no active members.
</details>

---

### 34. Design a multi-region messaging architecture. Active-active or active-passive?
`Architect`

<details><summary>Answer</summary>

Start by stating what multi-region is *for* — the answer differs completely for latency versus disaster recovery versus data residency.

**Active-passive** — one region serves, the other stands by.
- Simpler; no conflict resolution
- RTO minutes, RPO = replication lag
- Wastes the standby capacity
- Failover is rarely tested and therefore rarely works

**Active-active** — both serve.
- Better latency, no wasted capacity, failover is continuous
- **Conflict resolution becomes your problem**

**The design that works** (and the one in the case study):

1. **Independent cluster per region.** Never stretch one cluster across regions — inter-region latency causes false partitions and destroys quorum behaviour.
2. **Regional ownership of writes.** Route each user to their home region; that region owns their orders. No two regions write the same aggregate.
3. **Async replication for the read-only view** — Cluster Linking or MirrorMaker 2 for Kafka.
4. **A global authority for genuinely contended resources.** Inventory is the classic one: one region owns each SKU. Cross-region reservation is a synchronous call, and it is worth the latency because double-selling costs more.
5. **Failover repoints DNS.** Idempotency absorbs the duplicates that failover produces.

**Per broker:**
- **Kafka** — MirrorMaker 2 or Cluster Linking. Offsets are *translated*, not identical, so a failed-over consumer resumes approximately, not exactly. Design for duplicates.
- **Service Bus** — Geo-DR replicates **metadata only**; in-flight messages are lost, failover is manual, and the pairing breaks afterwards. For real active-active, use independent namespaces and route.
- **RabbitMQ** — federation between independent clusters. Never a stretched cluster.

**The senior signal is stating the RPO honestly:** with async replication, RPO is non-zero by definition. "Zero RPO across regions" requires synchronous replication and the latency cost that implies — usually unacceptable, and worth saying so out loud.
</details>

---

### 35. How do you handle schema evolution without breaking consumers?
`Senior` `Architect`

<details><summary>Answer</summary>

**The rule: add optional fields, never remove or repurpose.**

| Change | Safe |
|---|---|
| Add optional field with a default | ✅ |
| Add required field | ❌ old messages have no value |
| Remove optional field | ⚠️ only after verifying no consumer reads it |
| Rename | ❌ that is a remove plus an add |
| Widen type (int32→int64) | ✅ |
| **Change a field's meaning** | ❌❌ nothing detects it, everything breaks quietly |

That last row is the dangerous one. Repurposing `status` from an enum to a free-text field passes every schema check and breaks every consumer silently.

**Enforcement:**
- **Kafka** — Avro or Protobuf with a Schema Registry, from day one. The registry rejects an incompatible schema at *publish* time rather than at 3am in a consumer. Set compatibility to `BACKWARD` (new consumers read old data) or `FULL`.
- **Service Bus / RabbitMQ** — no registry. JSON with an explicit version **in a header**, not the body, so a consumer can route on version without deserialising. Which matters precisely when the reason it cannot deserialise *is* the version.

**Breaking changes:** publish `v1` and `v2` in parallel, migrate consumers, retire `v1`. Costs double storage and a dual-write period — a deliberate decision, not a default.

**The bit people forget:** on Kafka, messages are replayed. A consumer deployed today may read messages written two years ago. Retention length is a schema-compatibility constraint, and almost nobody writes that down.
</details>

---

### 36. Your RabbitMQ cluster is blocking publishers. Walk through the incident.
`Senior` `SRE`

<details><summary>Answer</summary>

**Recognise it first.** Every publisher stalls at once; consumers keep working. From the application it looks like a total broker failure. The broker is fine and deliberately braking — memory or disk crossed a watermark.

```bash
rabbitmqctl status | grep -A5 -E 'memory|disk_free'
rabbitmqctl list_connections name state | grep blocked
rabbitmqctl list_queues name messages memory | sort -k3 -rn | head -10
```

That last command names the culprit: the queue holding the memory.

**Then, in order:**

1. **Drain the big queue** — scale its consumers. This is the real fix; the queue is deep because nobody is emptying it.
2. **Buy headroom** — `set_vm_memory_high_watermark 0.75`. Temporary. Set a reminder to revert: a permanently raised watermark means the next incident is an OOMKill instead of a block, which is strictly worse.
3. **Free disk** if that was the trigger — expand the PVC.
4. **Purge a non-critical queue.** Destructive. Last resort.

**Prevention, which is the part that matters:** `x-max-length` + `x-overflow: reject-publish` on **every** queue. That rejects publishes to one queue instead of blocking every publisher in the cluster. One workload's growth stops being everyone's outage.

**The architectural question to raise afterwards:** why was the queue that deep? If the answer is "we keep 30 days of telemetry there", the real fix is that RabbitMQ is not an archive and that workload belongs on Kafka.
</details>

---

### 37. Compare the cost models honestly for 50k messages/sec.
`Senior` `Architect`

<details><summary>Answer</summary>

*(Indicative, July 2026. Verify before quoting.)*

**Kafka self-hosted** — 6 brokers × (8 vCPU, 32 GB, 1 TB premium SSD) ≈ **$4,500–6,000/month**, plus **0.5–1 FTE**.

**Confluent Cloud** — same workload ≈ **$8,000–15,000/month**, driven by egress and connectors. Near-zero ops.

**RabbitMQ** — will struggle at 50k/sec sustained with persistence. Feasible at ~20k. Beyond that you are federating clusters and fighting the product.

**Service Bus** — the wrong product at this volume. Premium at 16 MU is ~$11,000/month and still short of 50k/sec. Event Hubs is Azure's answer here, at roughly $2,000–4,000/month.

**The line item everyone omits:** engineering time. A serious Kafka cluster is 0.5–1 FTE — $75k–150k+ annually — which **dwarfs every infrastructure number above**. The self-hosted-versus-managed crossover is almost exactly one engineer's cost.

**And the modelling error specific to Service Bus:** count *operations*, not messages. One message through a topic with three subscriptions, completed, is 1 send + 3 deliveries + 3 completions = **7 operations**. Teams under-model Standard tier by 5–10× because they count messages.

**The strong answer names the non-obvious costs:** cross-AZ data transfer (billed, and easy to forget with replication factor 3), egress from managed services, and the on-call burden as a real cost with a real number attached.
</details>

---

### 38. How would you test a messaging system before production?
`Senior` `SRE` `Architect`

<details><summary>Answer</summary>

**Functional** — the ordinary part. Testcontainers for Kafka and RabbitMQ; Service Bus needs a real Standard namespace since the emulator lacks sessions and transactions.

**Idempotency, explicitly.** Deliver the same message twice in a test and assert the side effect happened once. If this test does not exist, the property does not hold — nobody discovers a broken idempotency check by accident.

**Load** — to peak × 2, sustained for an hour, not a burst. Measure end-to-end latency percentiles, not throughput averages. Watch lag stability rather than peak rate.

**Chaos** — the tests that find real bugs:
- Kill a broker mid-load. Do writes continue? (RF and min.insync working?)
- Kill a consumer mid-message. Is it redelivered and deduped?
- Partition the network. Does the cluster behave as documented?
- Fill a disk. Does it degrade or fall over?
- Introduce a poison message. Does it dead-letter, or wedge the partition?
- Slow a downstream dependency to 30 seconds. Do locks expire? Does the group rebalance?

That last one finds more production bugs than everything else combined.

**Soak** — 24–72 hours at moderate load. Finds connection leaks, memory creep, offset-retention surprises, and certificate expiry.

**Failover drill** — practise the multi-region failover before you need it. An untested failover is not a DR plan; it is a hope.

**The senior signal:** testing the *operational* procedures, not just the code. Can someone follow the runbook? Does the replay path work? Does the DLQ alert actually fire? Run the runbook as a test.
</details>

---

### 39. When would you deliberately run two brokers, and how do you avoid it becoming a mess?
`Architect`

<details><summary>Answer</summary>

**When the system genuinely has two shapes of traffic**, which most large systems do:

- **Firehose** — telemetry, clickstream, CDC, analytics. High volume, fan-out, replay. → Kafka or Event Hubs.
- **Commands** — payments, fulfilment, notifications. Moderate volume, retry semantics, scheduling, DLQ ergonomics. → Service Bus or RabbitMQ.

Forcing both onto one broker means rebuilding the other's strengths in application code. Teams that put job queues on Kafka rebuild retry backoff, scheduling, priority and dead-lettering — badly. Teams that put clickstreams on Service Bus get a five-figure monthly bill and constant throttling.

**How it stays sane — four rules:**

1. **Write the boundary down.** An explicit rule: "events that many services observe → Kafka; commands with one owner and retry semantics → Service Bus." A new engineer must be able to apply it without asking.
2. **One team owns the bridge.** The component copying between them is the highest-risk part of the system and it needs a named owner.
3. **The bridge is idempotent in both directions**, and it *copies* rather than moves.
4. **Count the operational cost honestly.** Two brokers is two on-call rotations, two upgrade cycles, two sets of failure modes. It is worth it when the shapes genuinely differ, and pure overhead when they do not.

**The failure mode to name:** a bad hybrid is one that happened because two teams each picked their favourite and nobody wrote down the boundary. That is indistinguishable from a good hybrid on an architecture diagram and completely different to operate.
</details>

---

### 40. You inherit a system with 40 million messages in one RabbitMQ queue. What do you do?
`Senior` `Architect` `SRE`

<details><summary>Answer</summary>

**First: stabilise. Do not fix.**

40 million messages in a RabbitMQ queue means the broker is at or near its memory watermark, which means publishers are blocked or about to be. The immediate risk is a cluster-wide publish outage, not the backlog itself.

```bash
rabbitmqctl list_connections name state | grep blocked
rabbitmqctl list_queues name messages memory consumers consumer_utilisation
```

**Triage, in order:**

1. **Are publishers blocked?** If yes, that is the incident. See Q36.
2. **Are consumers attached and working?** `consumer_utilisation` near 1.0 means they are saturated — scale out. Near 0 means they are stuck, and scaling does nothing.
3. **Is the backlog still growing?** Growing is an emergency; draining is a schedule.

**Then ask the question that actually matters: is this data still worth processing?**

40 million stale messages is often 40 million messages nobody needs. If they are notifications or telemetry, the honest answer may be to purge and move on — which is a business decision, made with a business owner, and written down.

**If it must be processed:** shovel the backlog to a *separate* queue on *separate* infrastructure and drain it there at a controlled rate. That decouples backlog recovery from live traffic, which is the key move — otherwise you are draining a backlog and serving production from the same memory budget.

**Then fix the cause**, and there are always two:

1. **Why did it grow?** A dead consumer, an unnoticed deploy failure, or a genuine capacity shortfall. Alerting failed here — 40 million is not a number you reach in an hour.
2. **Why was it allowed to grow?** No `x-max-length`. Every queue must be bounded with `x-overflow: reject-publish`, so one workload's failure cannot become everyone's outage.

**The architectural question:** why was a queue holding 40 million messages at all? A queue is a working set. If the requirement is genuinely "retain millions of messages", that is a log, and it belongs on Kafka or a RabbitMQ stream queue.

**The senior signal is the order:** stabilise, then decide whether the data matters, then drain out-of-band, then fix the cause, then fix the architecture. Starting with "how do I process 40 million messages faster" is the junior answer to the wrong question.
</details>

---

---

### 41. When would you put Dapr in front of your broker — and when would that be a mistake?
`Senior` `Architect`

<details><summary>Answer</summary>

**First, name what it is.** Dapr is not a broker. It is a sidecar giving you one pub/sub API, with the actual broker chosen in a YAML file. Your code says `PublishEventAsync("pubsub", "orders", order)` and never names Kafka, Rabbit or Service Bus.

**Use it when:**
- The estate is **polyglot** — one messaging API across four languages is value a per-language library cannot give you
- **Multi-cloud or hybrid is a committed requirement**, not a hypothetical
- **You genuinely do not know the broker yet** — start on RabbitMQ, change one line of YAML later. This is the strongest single case.
- You are on Kafka and wanted a **DLQ, declarative retries and an outbox** anyway. Dapr supplies all three; on Kafka that is 2–3 weeks of engineering you do not do.

**Do not use it when:**
- You need the **broker-defining features**. The Dapr API is the *intersection* of what every supported broker can do.
- Single language, single broker, no swap plan — you are paying a sidecar for portability you will never use
- Latency is genuinely critical, or the team is small

**The table that decides it:**

| You chose | For | Under Dapr |
|---|---|---|
| Kafka | Throughput, fan-out | ✅ Preserved |
| Kafka | **Replay, offset control** | ❌ **Gone** — Dapr owns the offsets |
| Service Bus | **Sessions, scheduling** | ❌ **Gone** |
| RabbitMQ | **Routing, priority** | ❌ **Flattened** |

**The insight worth stating:** the two strongest single-broker reasons — Kafka replay and Service Bus sessions — are *both* incompatible with Dapr. That is not bad luck. Broker-defining features are broker-specific by definition, and an abstraction removes what is specific.

> **The rule:** Dapr fits when you chose your broker for reasons it preserves, and not when you chose it for reasons it hides.

**The tell that it is costing more than it saves:** you are using Dapr but reaching past it for native broker features. The moment you add a Kafka client beside `DaprClient` to reset offsets, drop Dapr for that service.

**Two follow-ups a good candidate raises unprompted:**

1. **CloudEvents.** Dapr wraps your payload in an envelope by default, so a non-Dapr consumer on the same topic breaks. And the envelope `id` is regenerated on every publish — so it is useless as an idempotency key. Keep your own deterministic id inside the payload.
2. **For a .NET-only shop, MassTransit is usually the better answer** — same retry, DLQ, saga and outbox patterns as a NuGet package, no sidecar per pod, and you can still reach native broker config.

📖 [`dapr.md`](dapr.md) · [`tutorial.md#17f`](tutorial.md#17f-dapr--not-choosing-for-now)
</details>

---

## How to use these in an interview

**As the candidate.** The best answers name a **trade-off** and a **boundary**. "Kafka is faster" is weak. "Kafka gives near-free fan-out because consumers read one shared log, but it caps parallelism at your partition count, and that number cannot be lowered later" is strong. Every question above has a version of that.

**As the interviewer.** The tags suggest a level, but the signal is in the follow-up. Ask "when would that be wrong?" after any confident answer. Engineers who have run these systems in production always have an answer; engineers who have only read about them usually do not.

**The five questions that separate levels fastest:** 16 (exactly-once), 22 (rebalancing), 32 (exactly-once into a database), 34 (multi-region), 40 (the inherited backlog). Each has an obvious surface answer and a much better one underneath.

---

*Concepts behind these answers: [`tutorial.md`](tutorial.md). Operational detail: [`../runbooks/`](../runbooks/). Worked incidents: [`production-incidents.md`](production-incidents.md).*
