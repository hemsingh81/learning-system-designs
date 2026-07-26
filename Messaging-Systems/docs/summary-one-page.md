# Messaging Systems — One Page

*Paste this into a design doc or a slide. Everything below fits on one page. Detail: [`tutorial.md`](tutorial.md).*

---

## The three, in one sentence each

| | |
|---|---|
| **Apache Kafka** | A log you can rewind. Nothing is deleted when read, so many teams read the same event independently and you can replay last Tuesday. |
| **Azure Service Bus** | A managed queue with enterprise manners. A message is a job — locked while you work, deleted when done, parked in a DLQ when it will not go through. |
| **RabbitMQ** | A smart router. Publishers hand messages to an exchange, which decides where copies go — so you rewire consumers without touching publishers. |

---

## Decision table

| Attribute | Kafka | Azure Service Bus | RabbitMQ |
|---|---|---|---|
| **Throughput** | Millions/sec | ~1k/sec per messaging unit | 20k–50k/sec |
| **Latency p99** | 10–50 ms | 100–200 ms | **5–15 ms** |
| **Ordering** | Per key — free | Per session — costs concurrency | Per queue — costs parallelism |
| **Replay** | **Excellent** | **None** | Stream queues only |
| **Fan-out cost** | Near zero | One copy per subscription | One full copy per queue |
| **Routing / filtering** | None | SQL + correlation filters | **Best — 4 exchange types** |
| **DLQ** | You build it | **Built in** | Dead-letter exchange + `x-death` |
| **Per-message TTL / scheduling / priority** | No / No / No | **Yes / Yes** / No | **Yes** / Plugin / **Yes** |
| **Max message** | 1 MB | **100 MB Premium** | 128 MB (keep ≪) |
| **Runs on-prem** | Yes | **No** | Yes |
| **Ops burden** | **High — 0.5–1.5 FTE** | **Lowest — near zero** | Medium |
| **Best for** | Streams, CDC, analytics, event sourcing | Business workflows on Azure | Task queues, RPC, routing |

---

## Choosing — five questions, in order

1. **Several teams need the same message, at different times, with history?** Yes → 2. No → 4.
2. **Sustained peak above ~50k msg/sec?** Yes → **Kafka**. No, but replay matters → 3.
3. **All-in on Azure, want zero brokers to operate?** Yes → **Service Bus**. No → **Kafka**.
4. **Need per-message scheduling, TTL, priority, or routing that changes without a redeploy?** Yes → 3. No → 5.
5. **Small ops team a hard constraint?** Yes + Azure → **Service Bus**. Yes, not Azure → **RabbitMQ**. No → **RabbitMQ**.

**Question zero:** do you need a broker at all? A synchronous call, a database table polled by a worker, or a batch job beats a broker you must operate.

**Tie-breaker:** pick the one your team can debug at 3am. Operational familiarity beats a 15% benchmark win.

---

## Choosing by what you are building

| Building this | Pick | Because |
|---|---|---|
| Order / checkout pipeline | Service Bus or RabbitMQ | Retry, DLQ and ordering are broker features, not your code |
| Payment, refund, saga | **Service Bus** | Sessions, duplicate detection, scheduling, transactions |
| Background jobs, RPC, priority work | **RabbitMQ** | Priority queues, lowest latency, minute-long handlers are fine |
| Cross-team integration bus | **RabbitMQ** | Add a binding, get a filtered slice — no producer change |
| Clickstream, IoT, CDC, event sourcing | **Kafka / Event Hubs** | Replay, near-free fan-out, throughput |
| Audit trail, multi-year retention | **Kafka** + tiered storage | Years of retention is a log problem, not a queue problem |
| Under ~100 msg/sec, one consumer | **A database table** | You do not need a broker yet |

**Two archetypes that fool people.** A "queue" that four teams later want to read was always a log — if nobody can say *"could another team want this data?"* is a firm no, choose Kafka. A "stream" of long-running, individually-retriable jobs was always a queue, whatever the volume.

**The one-sentence boundary rule** if you end up with both: *past-tense facts go to the log; imperative commands go to the queue.*

Full lookup — 18 workload types with reasoning: [`tutorial.md#17a`](tutorial.md#17a-choose-by-workload)

---

## What actually decides it

Feature tables feel objective, so teams over-weight them. Three things decide harder:

**Your team.** Has anyone run this in production, not a POC? Is there a real on-call rotation? Two or fewer honest yeses rules out self-hosted Kafka regardless of benchmarks. The pattern that repeats: a team picks the technically superior option, runs it badly, and blames the technology.

**Your scale.** The answer changes by an order of magnitude at each step — under 100/sec use a database table; 1k–10k/sec is Service Bus or RabbitMQ; above 50k/sec is Kafka. Design for a growth *curve* you can already see, never for a growth *hope*.

**What leaving costs.** RabbitMQ→Kafka is hard (Kafka has no routing). Kafka→anything is hard (you lose replay). Service Bus→anywhere else is a rewrite. Keep the exit affordable: abstract at the boundary, keep messages self-describing, and make consumers idempotent — that last one is what makes every incremental migration strategy possible.

**Reasons that are not reasons:** "Netflix uses it" · "industry standard" · "we might need scale later" · "it benchmarked 15% faster" · "it's free" (the licence is; the engineer is $150k/year).

---

## What is true of all three

1. **At-least-once is the contract.** Exactly-once exists only inside Kafka, Kafka-to-Kafka. What you build is *effectively-once* = at-least-once + an idempotency key. Duplicates are normal operation, not a fault.
2. **Dual writes do not work.** "Save the order, then publish" can half-fail. Use the **outbox pattern**: business row and outbox row in one database transaction; a separate process publishes and marks sent.
3. **The DLQ needs an owner and an alert at depth > 0.** A DLQ nobody reads is a slow-motion data-loss machine.
4. **Ordering costs parallelism.** Always. Decide the *smallest* unit that needs it — usually one order or one account, almost never global.
5. **Retry transient, dead-letter permanent.** A declined card will never be approved. Retrying it five times delays the real answer by four attempts.

---

## The classic outage per broker

| Broker | Failure | One-line prevention |
|---|---|---|
| **Kafka** | **Rebalance loop** — handler exceeds `max.poll.interval.ms`, gets evicted mid-work, forever | Raise `max.poll.interval.ms` (**not** `session.timeout.ms`); use cooperative rebalancing |
| **Service Bus** | **Lock expiry storm** — high prefetch + slow handler = mass duplicates | `PrefetchCount = 0`; enable auto lock renewal |
| **RabbitMQ** | **Blocked publishers** — memory watermark hit, every publisher cluster-wide stalls | `x-max-length` + `x-overflow: reject-publish` on every queue |

---

## Settings that prevent data loss

```
Kafka        acks=all  AND  min.insync.replicas=2      # both, or neither means anything
             enable.idempotence=true
             unclean.leader.election.enable=false
             enable.auto.commit=false                   # consumer side

Service Bus  ReceiveMode = PeekLock                     # not ReceiveAndDelete
             AutoCompleteMessages = false               # settle every path explicitly
             MessageId = "order-123:OrderPlaced"        # deterministic, NOT Guid.NewGuid()

RabbitMQ     publisherConfirmationsEnabled: true        # else publish is fire-and-forget
             mandatory: true                            # unroutable → callback, not silence
             Persistent = true AND durable: true        # both
             BasicQos(prefetchCount: 20)                # default is UNLIMITED
             BasicNack(requeue: false)                  # requeue:true = infinite poison loop
```

---

## Cost at 50k msg/sec *(indicative, July 2026 — verify before quoting)*

| Option | Infrastructure | Engineering | Total |
|---|---|---|---|
| Kafka self-hosted | $4.5k–6k/mo | 0.5–1 FTE (~$9k/mo) | **~$15k/mo** |
| Confluent Cloud | $8k–15k/mo | ~0.1 FTE | **~$10k–16k/mo** |
| Event Hubs + Service Bus | ~$34k/mo | ~0.25 FTE | **~$37k/mo** |
| RabbitMQ | $1.2k–1.8k/mo | 0.5 FTE | *Will not reach 50k/sec sustained* |

**The line item everyone omits is engineering time**, and it dwarfs every infrastructure number above. The self-hosted-versus-managed crossover is almost exactly one engineer's salary.

**The Service Bus modelling error:** count *operations*, not messages. One message through a topic with three subscriptions, completed, is **7 operations**. Teams under-model Standard tier by 5–10×.

---

## Recommendation for a large system: hybrid, deliberately

Most systems at scale have two shapes of traffic, and forcing both onto one broker means rebuilding the other's strengths in application code.

- **Firehose** — telemetry, clickstream, CDC, analytics, anything replayable → **Kafka** or **Event Hubs**
- **Commands** — payments, fulfilment, notifications, anything with retry semantics → **Service Bus** or **RabbitMQ**

**The boundary rule, written down:**

> An event that many services observe and anyone might replay → **the log**.
> A command with one owner, retry semantics and a dead-letter path → **the queue**.

**Four rules that keep it from becoming a mess:** the boundary is written down; one team owns the bridge; the bridge is idempotent in both directions and *copies* rather than moves; the operational cost of two brokers is counted honestly.

A bad hybrid looks identical on an architecture diagram and is completely different to operate — it is the one where two teams each picked their favourite and nobody wrote down the boundary.

---

## Before you write code

- [ ] Ordering unit decided (per order? per account? — rarely global)
- [ ] Idempotency key is deterministic, and the store exists
- [ ] Outbox pattern in place for any database-plus-publish
- [ ] DLQ exists, has a named owner, and alerts at depth > 0
- [ ] Retry is bounded, with backoff, and only for transient faults
- [ ] Queues bounded; partitions sized for peak (**Kafka partition count cannot be lowered**)
- [ ] Autoscaling on queue depth, **not CPU**
- [ ] Schema version travels in a header; evolution rule is "add optional fields only"
- [ ] Auth is identity-based, not a shared connection string
- [ ] **You can state what you gave up by choosing this** — if that box is empty, the analysis is not finished

---

*Full tutorial: [`tutorial.md`](tutorial.md) · Worked case study: [`case-study-ecommerce.md`](case-study-ecommerce.md) · 30 incidents: [`production-incidents.md`](production-incidents.md) · Runbooks: [`../runbooks/`](../runbooks/)*
