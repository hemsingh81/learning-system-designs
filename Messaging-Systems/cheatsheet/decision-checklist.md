# One-Page Decision Checklist

Work top to bottom. Stop at the first section that gives you a clear answer. Take it to a design review and defend each box you ticked.

---

## 0. Do you need a broker at all?

Tick every box that is **true**:

- [ ] The producer must not wait for the consumer to finish
- [ ] The consumer can be down without the producer failing
- [ ] Traffic is spiky and something must absorb the spike
- [ ] More than one system needs the same event
- [ ] You need to retry work independently of the original request

**Zero or one box ticked** → you probably do not need a broker. A synchronous call, a database table polled by a worker, or a scheduled batch job is simpler, cheaper, and easier to debug. A broker you have to operate is not free.

**Two or more** → continue.

---

## 1. Hard constraints — these eliminate options

| Constraint | If true, this happens |
|---|---|
| Must run on-premises or air-gapped | **Service Bus is out** |
| Must replay history (audit, rebuild, reprocess) | **Service Bus is out** unless you pair it with Event Hubs |
| Sustained peak above ~50k msg/sec | **Kafka or Event Hubs.** Rabbit and Service Bus will fight you |
| Team of two, no platform team, no Kafka experience | **Kafka is out** unless it is fully managed |
| Regulator requires a message-level audit trail with retention | **Kafka** (or Event Hubs Capture) |
| Messages larger than 1 MB | **Service Bus Premium** (100 MB), or store the payload in blob storage and send a pointer |
| Sub-5ms broker latency required | **RabbitMQ** |
| Zero infrastructure to operate is non-negotiable | **Service Bus** (or a managed Kafka) |

Anything eliminated here stays eliminated. Do not argue it back in on features.

---

## 2. The five questions

Answer in order. Full version with reasoning: [`../images/svg/broker-decision.svg`](../images/svg/broker-decision.svg)

1. **Do several teams need the same message, at different times, with history?**
   Yes → go to 2. No → go to 4.

2. **Is your peak above ~50k msg/sec sustained?**
   Yes → **Kafka**. No, but replay still matters → go to 3.

3. **All-in on Azure, and want zero brokers to operate?**
   Yes → **Service Bus** (+ Event Hubs if you need replay). No → **Kafka**.

4. **Do you need per-message scheduling, per-message TTL, priority, or routing rules that change without a redeploy?**
   Yes → go to 3. No → go to 5.

5. **Is a small ops team your hard constraint?**
   Yes, on Azure → **Service Bus**. Yes, not on Azure → **RabbitMQ**. No → **RabbitMQ**.

---

## 3. Sanity-check the answer

Before you commit, confirm all of these:

- [ ] Someone on the team has run this in production before — or the budget includes a managed service
- [ ] You can name the on-call person for it
- [ ] The failure mode is understood: Kafka → rebalance loops; Rabbit → blocked publishers; Service Bus → lock expiry and throttling
- [ ] The cost at 3× today's volume has been calculated, not guessed
- [ ] The exit path is known — what migrating off it would cost

If two options both survive, **pick the one your team can debug at 3am**. Operational familiarity beats a 15% benchmark advantage every time.

---

## 4. Design decisions to make before writing code

Answer these in the design doc. Every one of them is expensive to change later.

### Ordering
- [ ] What is the ordering unit? (per order, per customer, per account — rarely global)
- [ ] Kafka: what is the partition key? Service Bus: what is the `SessionId`? Rabbit: does one queue need one consumer?
- [ ] You have accepted that ordering costs parallelism

### Delivery
- [ ] Consumers are idempotent — there is a real idempotency key and a real store
- [ ] The key is deterministic (`order-123:OrderPlaced`), **not** `Guid.NewGuid()`
- [ ] You are not claiming exactly-once across a database boundary

### Durability
- [ ] Kafka: `acks=all` **and** `min.insync.replicas=2`. Rabbit: confirms **and** persistent **and** durable. Service Bus: PeekLock, not ReceiveAndDelete
- [ ] Replication factor 3, spread across availability zones
- [ ] Dual writes are handled by an outbox, not by hope

### Failure
- [ ] There is a DLQ, it has a named owner, and depth > 0 alerts
- [ ] Retry is bounded, with backoff, and only for transient faults
- [ ] Business rejections (declined card) go straight to the DLQ, never retried
- [ ] Poison messages cannot block the partition or spin a consumer

### Capacity
- [ ] Kafka partitions sized for peak parallelism — **this cannot be lowered later**
- [ ] Queues are bounded (`x-max-length`, `maxSizeInMegabytes`)
- [ ] Autoscaling is on queue depth, not CPU
- [ ] You know what happens when the queue is full: block, reject, or drop — and which you want

### Schema
- [ ] Message format chosen (Avro/Protobuf with a registry, or JSON with an explicit version field)
- [ ] Version travels in a header
- [ ] The evolution rule is written down: add optional fields only; never remove or repurpose

### Observability
- [ ] Lag/depth dashboards exist before launch, not after the first incident
- [ ] Correlation IDs flow end to end
- [ ] Service Bus only: diagnostic settings are **on now** — you cannot add them retroactively

### Security
- [ ] Authentication is identity-based (Entra ID, mTLS, SCRAM) — not a shared connection string
- [ ] Authorization is least-privilege, scoped per entity
- [ ] TLS in transit; encryption at rest confirmed
- [ ] PII strategy decided — field encryption or crypto-shredding if GDPR erasure applies

---

## 5. Red flags

Each of these has caused a real outage. If any is true, fix it before launch.

- ❌ `enable.auto.commit=true` on a Kafka consumer that matters
- ❌ RabbitMQ prefetch left at the default (unlimited)
- ❌ `BasicNack(requeue: true)` with no retry ceiling
- ❌ `ReceiveAndDelete` mode on Service Bus for anything you would miss
- ❌ `$Default` rule still present on a filtered Service Bus subscription
- ❌ Publishing without confirms on RabbitMQ
- ❌ `min.insync.replicas=1` with `acks=all` — the guarantee is fake
- ❌ Classic mirrored queues on RabbitMQ (removed in 4.x)
- ❌ No DLQ, or a DLQ with no alert
- ❌ Save-to-database-then-publish with no outbox
- ❌ `Guid.NewGuid()` as an idempotency key
- ❌ Autoscaling consumers on CPU
- ❌ One connection per message
- ❌ Unbounded queues
- ❌ Retrying a business rejection
- ❌ Using Dapr while reaching past it for native broker features
- ❌ A Dapr publisher and a native consumer sharing a topic, with the CloudEvents question unanswered
- ❌ Using the CloudEvent envelope `id` as an idempotency key

---

## 5b. Should you abstract over the broker at all?

Dapr (or MassTransit) lets you defer the choice. It is a real option and it has a real price.

**Consider an abstraction if:**
- [ ] The estate is polyglot — three or more languages messaging
- [ ] Multi-cloud or hybrid is a **committed requirement**, not a hypothetical
- [ ] You genuinely do not know which broker yet, and shipping matters more than deciding
- [ ] You were going to build a DLQ, retry policy and outbox anyway (Dapr supplies all three)

**Do not abstract if:**
- [ ] ❌ You need **Kafka replay or offset control** — the abstraction owns the offsets
- [ ] ❌ You need **Service Bus sessions or scheduled messages**
- [ ] ❌ You need **RabbitMQ routing flexibility or priority queues**
- [ ] ❌ Single language, single broker, no swap plan — you are paying for portability you will not use
- [ ] ❌ Latency is genuinely critical
- [ ] ❌ The team is small and would be better off knowing one broker deeply

**The test in one line:** *does the abstraction preserve the reason you chose the broker?* If not, it is the wrong trade — the two strongest single-broker reasons (Kafka replay, Service Bus sessions) are both incompatible with Dapr.

**If you adopt one:**
- [ ] The CloudEvents-vs-raw-payload decision is made **before the first message ships** (changing it later is a breaking schema change)
- [ ] Your own deterministic message id lives **inside** the payload, not in the envelope
- [ ] Sidecar startup and shutdown ordering is handled — readiness gates traffic, `block-shutdown-duration` is set
- [ ] Sidecar memory is in the capacity plan (50–150 MB × pod count)
- [ ] Someone owns the Dapr upgrade cycle
- [ ] **.NET-only?** You compared against MassTransit, which needs no sidecar

Detail: [`../docs/dapr.md`](../docs/dapr.md) · Summary: [`../docs/tutorial.md#17f`](../docs/tutorial.md#17f-dapr--not-choosing-for-now)

---

## 6. Two brokers, deliberately

Most large systems end up hybrid. That is fine when it is a decision and not an accident.

**A good split:**
- Stream/firehose (telemetry, clickstream, CDC, analytics) → **Kafka** or **Event Hubs**
- Commands and workflow (payments, fulfilment, notifications) → **Service Bus** or **RabbitMQ**

**Before you commit to two:**
- [ ] The boundary is written down — which messages go where, and why
- [ ] One team owns the bridge between them
- [ ] The bridge is idempotent in both directions
- [ ] You have counted the operational cost of two systems honestly

**A bad split** is one that happened because two teams each picked their favourite and nobody wrote down the boundary.

---

## 7. Sign-off

| Question | Answer |
|---|---|
| Chosen broker | |
| Primary reason (one sentence) | |
| What we gave up | |
| Peak throughput assumption | |
| Ordering unit | |
| Idempotency key | |
| DLQ owner | |
| On-call owner | |
| Cost at 3× volume | |
| Exit path if this was wrong | |

If the "what we gave up" box is empty, the analysis is not finished. Every choice here costs something.
