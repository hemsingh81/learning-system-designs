# 49 · Concept: Kafka (30 questions)

[← Redis Cache](48-concept-redis-cache.md) · [Home](README.md) · [Next → Data Design](50-concept-data-design.md)

This file explains **Apache Kafka** — the distributed event streaming platform I use for decoupled, event-driven systems — in simple English and real depth. I answer from projects A–E, where I used event streaming for integrations and async processing on TCW's platforms.

> Simple one-liner: *"Kafka is a distributed, durable log for events. Producers append events to topics, consumers read them at their own pace, and because events are stored and replayable, it decouples systems and handles huge throughput reliably."*

**Jump to:** [KF1 What is Kafka](#kf1--what-is-kafka) · [KF2 Why use it](#kf2--why-use-kafka) · [KF3 The log](#kf3--the-log-model) · [KF4 Topics](#kf4--topics) · [KF5 Partitions](#kf5--partitions) · [KF6 Producers](#kf6--producers) · [KF7 Consumers](#kf7--consumers) · [KF8 Consumer groups](#kf8--consumer-groups) · [KF9 Offsets](#kf9--offsets) · [KF10 Ordering](#kf10--ordering)
> [KF11 Retention](#kf11--retention) · [KF12 Replication](#kf12--replication) · [KF13 Brokers](#kf13--brokers-and-cluster) · [KF14 Delivery](#kf14--delivery-guarantees) · [KF15 Idempotency](#kf15--idempotency-and-exactly-once) · [KF16 Keys](#kf16--message-keys) · [KF17 Schema](#kf17--schema-and-serialization) · [KF18 vs queue](#kf18--kafka-vs-a-message-queue) · [KF19 vs RabbitMQ](#kf19--kafka-vs-rabbitmq) · [KF20 Kafka vs Redis](#kf20--kafka-vs-redis-pubsub)
> [KF21 Event-driven](#kf21--event-driven-architecture) · [KF22 Kafka Connect](#kf22--kafka-connect) · [KF23 Streams](#kf23--stream-processing) · [KF24 DLQ](#kf24--error-handling-and-dlq) · [KF25 Backpressure](#kf25--consumer-lag-and-scaling) · [KF26 Performance](#kf26--performance) · [KF27 Security](#kf27--security) · [KF28 On Azure](#kf28--kafka-on-azure) · [KF29 Pitfalls](#kf29--common-pitfalls) · [KF30 My approach](#kf30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of Kafka in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. Kafka is a durable, append-only log.** At its heart it's just an ordered file of events that you keep appending to. Producers write to the end; consumers read forward at their own pace. Because the events are stored (not deleted when read), consumers can replay history. Once I stopped thinking "message queue" and started thinking "a log I can re-read," everything else clicked.

**2. Topics and partitions are how it scales.** A topic is a named stream of events. Each topic is split into partitions, and partitions are the unit of parallelism — more partitions means more consumers can work at once. Order is only guaranteed *within* a partition, which is the single most important thing to understand.

**3. The message key decides the partition — and therefore ordering.** Events with the same key land in the same partition and stay in order. On TCW integrations (A/C) I keyed by account or portfolio ID so all events for one entity processed in order, while different entities spread across partitions for throughput.

**4. Consumers, groups and offsets.** Consumers read from partitions; a consumer group shares the work so each partition is handled by exactly one consumer in the group. An offset is a bookmark — where a consumer has read up to. Committing offsets is how a consumer remembers its place and how it can resume or replay.

**5. Retention and replication give durability.** Kafka keeps events for a configured time or size regardless of who has read them, so slow or new consumers still get the data. Replication copies each partition across brokers, so a broker failure doesn't lose data. This durability is what lets services decouple safely.

**6. Delivery guarantees are a choice, not a default.** At-most-once, at-least-once, and exactly-once each have costs. Most real systems run at-least-once and make consumers idempotent — I design handlers so processing the same event twice is safe. Kafka's idempotent producer and transactions enable exactly-once within Kafka when it's truly needed.

**7. Kafka enables event-driven architecture.** Instead of services calling each other synchronously, one service emits an event and others react. This decouples teams and systems, smooths spikes, and lets me add new consumers without touching producers. On project C this turned tight service-to-service coupling into a clean publish/subscribe flow.

**8. It's not a general message queue, and on Azure I have options.** Unlike a queue, Kafka retains and replays events and scales via partitions rather than competing consumers on one queue. On Azure I often use Event Hubs, which speaks the Kafka protocol, so I get the same model as a managed service without running brokers myself.

**The full-stack / architect lens:** the later Q&As go deeper into Kafka Connect, stream processing, dead-letter handling, consumer lag and scaling, schemas/serialization, security, and the exact Azure/Event Hubs setup. The recurring theme is that Kafka's power comes from the log being replayable and partitioned — design around keys, ordering and idempotency and the rest follows.

**One rule I never break:** *design every consumer to be idempotent — assume it will see the same event more than once.*

---

## KF1 · What is Kafka?

**Simple explanation.** **Apache Kafka** is a distributed **event streaming platform** — a durable, ordered **log** of events. Producers write events to **topics**; consumers read them independently and can replay history. It's built for high throughput, durability and decoupling.

**Architect's view:** Kafka is the backbone for event-driven systems — a scalable, replayable event log that lets services communicate without being tightly coupled.

**Follow-ups**
- *"One-line?"* — A durable, distributed log for streaming events between systems.
- *"Just messaging?"* — More — it's a stored, replayable event log, not just transient messages.

---

## KF2 · Why use Kafka?

**Simple explanation.** I use it to **decouple** services (producers don't know consumers), **absorb spikes** (buffer), **scale** throughput, and **replay** events for new consumers or recovery ([file 47 SD15](47-concept-system-design.md#sd15--async-messaging)). It turns tight, fragile integrations into resilient event flows.

**Follow-ups**
- *"Main benefit?"* — Decoupling + durability + replay at high scale.
- *"Why not direct calls?"* — They couple services and fail together; events isolate them.

---

## KF3 · The log model

**Simple explanation.** Kafka stores events in an **append-only log**: new events go to the end, each gets an **offset** (position), and events stay for a **retention** period. Consumers read forward from an offset — nothing is deleted on read, so many consumers can read the same events.

**Follow-ups**
- *"Deleted on read?"* — No — events persist for the retention window; consumers track their own position.
- *"Why a log?"* — Ordering, replay, and multiple independent readers.

---

## KF4 · Topics

**Simple explanation.** A **topic** is a named stream/category of events (e.g. `orders`, `payments`). Producers publish to a topic; consumers subscribe to it. Topics organise events by type — like tables organise rows.

**Follow-ups**
- *"How many topics?"* — One per event type/domain — keep them meaningful.
- *"Subscribe pattern?"* — Consumers pick topics they care about.

---

## KF5 · Partitions

**Simple explanation.** Each topic is split into **partitions** — the unit of parallelism and scale. Events spread across partitions so many consumers can read in parallel. Order is guaranteed **within** a partition, not across the whole topic.

**Follow-ups**
- *"Why partition?"* — Parallelism and horizontal scale of throughput.
- *"Order across partitions?"* — Not guaranteed — use a key to keep related events together ([KF16](#kf16--message-keys)).

---

## KF6 · Producers

**Simple explanation.** **Producers** publish events to topics. They choose the partition (by key or round-robin), can batch for throughput, and set **acks** (how many replicas must confirm) to trade durability against latency.

**Follow-ups**
- *"acks setting?"* — `all` = safest (wait for replicas); `1`/`0` = faster, less durable.
- *"Batching?"* — Yes — groups events for higher throughput.

---

## KF7 · Consumers

**Simple explanation.** **Consumers** read events from partitions, process them, and track their **offset**. They pull at their own pace, so a slow consumer doesn't slow producers — a key decoupling benefit.

**Follow-ups**
- *"Push or pull?"* — Pull — consumers control their rate.
- *"Slow consumer effect?"* — It lags but doesn't block producers or other consumers.

---

## KF8 · Consumer groups

**Simple explanation.** A **consumer group** shares the work of a topic: partitions are split across members, so adding consumers scales processing. Different groups each get the **full** stream — enabling multiple independent uses of the same events.

**Follow-ups**
- *"Scale processing?"* — Add consumers to a group (up to partition count).
- *"Two groups?"* — Each receives all events independently — e.g. analytics + billing.

---

## KF9 · Offsets

**Simple explanation.** An **offset** is a consumer's position in a partition. Consumers **commit** offsets to remember progress. Committing after processing gives **at-least-once**; committing before risks **at-most-once**. Offset handling defines delivery semantics.

**Follow-ups**
- *"Commit when?"* — After successful processing → at-least-once (safe, may duplicate).
- *"Replay?"* — Reset the offset to re-read events from a point.

---

## KF10 · Ordering

**Simple explanation.** Kafka guarantees order **within a partition**. To keep related events ordered (e.g. all events for one account), I give them the **same key** so they land in the same partition. Global ordering across a topic isn't guaranteed.

**Follow-ups**
- *"Guarantee order for an entity?"* — Key by entity id → same partition → ordered.
- *"Global order?"* — Only with a single partition — which limits throughput.

---

## KF11 · Retention

**Simple explanation.** Kafka keeps events for a configured **retention** (time or size), or uses **log compaction** to keep the latest value per key. This lets late/new consumers replay history — unlike a queue that deletes on consumption.

**Follow-ups**
- *"Retention options?"* — Time-based, size-based, or compacted (keep latest per key).
- *"Why keep events?"* — Replay for new consumers, recovery, and auditing.

---

## KF12 · Replication

**Simple explanation.** Each partition is **replicated** across brokers (a **leader** + **followers**). If the leader fails, a follower takes over — no data loss and continued availability. The **replication factor** sets how many copies exist.

**Follow-ups**
- *"Replication factor?"* — Usually 3 in production — survives broker failures.
- *"ISR?"* — In-sync replicas that are caught up and eligible to become leader.

---

## KF13 · Brokers and cluster

**Simple explanation.** A **broker** is a Kafka server; a **cluster** is several brokers sharing partitions and replicas. Adding brokers scales storage and throughput. Coordination is handled by KRaft (or older ZooKeeper).

**Follow-ups**
- *"Scale the cluster?"* — Add brokers; partitions rebalance across them.
- *"Coordination?"* — KRaft (modern) replaces ZooKeeper for metadata/leadership.

---

## KF14 · Delivery guarantees

**Simple explanation.** Kafka offers **at-most-once** (may lose), **at-least-once** (may duplicate — the common default), and **exactly-once** (with idempotent producers + transactions). I usually design for **at-least-once + idempotent consumers** — simpler and robust.

**Follow-ups**
- *"Default in practice?"* — At-least-once with idempotent processing.
- *"Exactly-once cost?"* — More complexity/overhead — use only when truly required.

---

## KF15 · Idempotency and exactly-once

**Simple explanation.** Because at-least-once can duplicate, I make consumers **idempotent** (processing the same event twice has no extra effect) using dedup keys or upserts ([file 47 SD27](47-concept-system-design.md#sd27--data-flow-and-idempotency)). Kafka also supports exactly-once via idempotent producers + transactions.

**Follow-ups**
- *"Why idempotency over exactly-once?"* — Simpler, cheaper, works end-to-end including side effects.
- *"How?"* — Dedup on an event id, or upsert so repeats are harmless.

---

## KF16 · Message keys

**Simple explanation.** A **key** decides the partition (same key → same partition), giving **per-key ordering** and even distribution. I key by the entity (account id, order id) whose events must stay ordered together.

**Follow-ups**
- *"No key?"* — Round-robin distribution, no per-entity ordering.
- *"Bad key?"* — Skewed keys create hot partitions — choose an even, meaningful key.

---

## KF17 · Schema and serialization

**Simple explanation.** Events need a stable **schema** so producers and consumers agree. I use **Avro/Protobuf/JSON** with a **Schema Registry** to enforce compatibility, so schema changes don't break consumers — essential for evolving systems.

**Follow-ups**
- *"Why a registry?"* — Enforces backward/forward compatibility on schema changes.
- *"Format choice?"* — Avro/Protobuf (compact, typed) vs JSON (readable) — trade-off.

---

## KF18 · Kafka vs a message queue

**Simple explanation.** A traditional **queue** deletes messages once consumed and targets one consumer. **Kafka** keeps events (retention), supports **replay**, and lets **many** consumer groups read the same stream. Kafka is a log; a queue is a hand-off.

**Follow-ups**
- *"Pick a queue when?"* — Simple task hand-off, one consumer, no replay needed.
- *"Pick Kafka when?"* — High throughput, multiple consumers, replay, event sourcing.

---

## KF19 · Kafka vs RabbitMQ

**Simple explanation.** **RabbitMQ** is a smart broker (routing, per-message ack, good for task queues/RPC). **Kafka** is a high-throughput, durable, replayable log (streaming, analytics, event sourcing). I pick RabbitMQ for complex routing/tasks, Kafka for streams and scale.

**Follow-ups**
- *"RabbitMQ strength?"* — Flexible routing and per-message handling for task workloads.
- *"Kafka strength?"* — Massive throughput, retention and replay.

---

## KF20 · Kafka vs Redis Pub/Sub

**Simple explanation.** **Redis Pub/Sub** ([file 48 RC13](48-concept-redis-cache.md#rc13--pubsub)) is fast but **ephemeral** — miss it and it's gone. **Kafka** is **durable and replayable**. I use Redis for lightweight real-time broadcasts and Kafka for reliable event pipelines.

**Follow-ups**
- *"Redis Pub/Sub risk?"* — No persistence — offline subscribers lose messages.
- *"Kafka advantage?"* — Stored events consumers can read later or replay.

---

## KF21 · Event-driven architecture

**Simple explanation.** With Kafka, services emit **events** ("order placed") and others react, instead of calling each other directly. This decouples teams, enables new consumers without changing producers, and supports patterns like **event sourcing** and **CQRS**.

**Follow-ups**
- *"Benefit?"* — Loose coupling and easy extension — add consumers freely.
- *"Event sourcing?"* — Store state as a sequence of events; rebuild by replaying.

---

## KF22 · Kafka Connect

**Simple explanation.** **Kafka Connect** moves data in/out of Kafka using ready-made **connectors** (databases, storage, search) — no custom code. It's how I stream a database's changes (CDC) into Kafka or sink events into a warehouse.

**Follow-ups**
- *"CDC?"* — Change Data Capture — stream DB changes as events via a connector.
- *"Why Connect?"* — Reliable, configurable integration without writing pipelines.

---

## KF23 · Stream processing

**Simple explanation.** **Kafka Streams** / **Flink** process events *as they flow* — filtering, aggregating, joining, windowing — producing new streams. Great for real-time analytics, enrichment and alerting without a batch job.

**Follow-ups**
- *"Batch vs stream?"* — Stream = continuous, low-latency; batch = periodic bulk.
- *"Windowing?"* — Aggregate events over time windows (e.g. per-minute counts).

---

## KF24 · Error handling and DLQ

**Simple explanation.** For events that repeatedly fail I use **retries** then a **dead-letter topic (DLQ)** so a poison message doesn't block the partition. I monitor the DLQ and reprocess after fixing the issue.

**Follow-ups**
- *"Poison message?"* — One that always fails — route to DLQ so others proceed.
- *"After DLQ?"* — Alert, inspect, fix, and replay when safe.

---

## KF25 · Consumer lag and scaling

**Simple explanation.** **Consumer lag** = how far behind the latest offset a consumer is. Rising lag means consumers can't keep up — I scale out (more consumers, up to partition count), optimise processing, or add partitions. Lag is my key health metric.

**Follow-ups**
- *"Scale limit?"* — One active consumer per partition — add partitions to scale further.
- *"Monitor what?"* — Consumer lag — the signal that consumers are falling behind.

---

## KF26 · Performance

**Simple explanation.** Kafka is fast due to **sequential disk writes**, **zero-copy** transfer, **batching** and **compression**. I tune batch size, compression, acks, partitions and consumer parallelism to balance throughput, latency and durability.

**Follow-ups**
- *"Throughput vs latency?"* — Bigger batches = throughput; smaller = lower latency.
- *"Compression?"* — Cuts network/storage cost at slight CPU cost.

---

## KF27 · Security

**Simple explanation.** I secure Kafka with **TLS** (encryption), **SASL** (authentication), and **ACLs** (who can read/write which topics), plus private networking. In finance, topics carry sensitive events, so encryption, authz and audit are mandatory ([file 47 SD22](47-concept-system-design.md#sd22--security)).

**Follow-ups**
- *"Three controls?"* — TLS (encrypt), SASL (authenticate), ACLs (authorise).
- *"Sensitive data?"* — Encrypt, restrict topics, and audit access.

---

## KF28 · Kafka on Azure

**Simple explanation.** On Azure I use **Azure Event Hubs** (Kafka-compatible, managed) or **Confluent Cloud** so I get Kafka semantics without operating clusters ([file 37](37-concept-azure-services.md)). Managed = HA, scaling and security handled, which suits a regulated, ops-light setup.

**Follow-ups**
- *"Event Hubs?"* — Managed streaming with a Kafka-compatible endpoint.
- *"Why managed?"* — No cluster ops; built-in scaling, HA and security.

---

## KF29 · Common pitfalls

**Simple explanation.** Pitfalls: too few/many partitions, expecting global ordering, non-idempotent consumers (duplicates cause harm), no schema management, ignoring consumer lag, and no DLQ. I design for at-least-once + idempotency and monitor lag from day one.

**Follow-ups**
- *"Most common?"* — Assuming exactly-once/global order — design for at-least-once + idempotency.
- *"Operational miss?"* — Not monitoring consumer lag — the early warning of trouble.

---

## KF30 · My approach

**How I answer (the whole picture).** *"I use Kafka as the durable, replayable **event backbone** for event-driven systems. Producers publish domain events to **topics**, split into **partitions** for parallelism, **keyed** by entity id so related events stay ordered. Consumers read in **consumer groups** at their own pace, tracking **offsets**, and I design for **at-least-once delivery with idempotent consumers** so duplicates are harmless — reserving exactly-once for when it's truly needed. I set **replication factor 3** for durability, manage schemas with a **Schema Registry**, add **retries + a dead-letter topic** for poison messages, and monitor **consumer lag** as my key health metric. This decouples services, absorbs spikes, and lets me add new consumers (analytics, billing) without touching producers. In Azure I run it as managed **Event Hubs / Confluent**, secured with TLS/SASL/ACLs — exactly how I built resilient integrations on TCW's platforms."*

**Follow-ups**
- *"One sentence?"* — A durable event log: keyed topics/partitions, consumer groups, at-least-once + idempotency, monitored by lag.
- *"Kafka vs queue in a line?"* — Kafka stores and replays events for many consumers; a queue hands a message to one and deletes it.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| KF1 | Kafka | Durable distributed event log |
| KF2 | Why | Decouple, buffer, scale, replay |
| KF3 | Log model | Append-only; read by offset; not deleted on read |
| KF4 | Topics | Named streams of events |
| KF5 | Partitions | Unit of parallelism/scale |
| KF6 | Producers | Publish; choose partition; acks |
| KF7 | Consumers | Pull at own pace; track offset |
| KF8 | Consumer groups | Share work; groups each get full stream |
| KF9 | Offsets | Position; commit = delivery semantics |
| KF10 | Ordering | Per-partition; key for entity order |
| KF11 | Retention | Keep/compact events for replay |
| KF12 | Replication | Leader+followers; RF=3 |
| KF13 | Brokers | Servers form a scalable cluster |
| KF14 | Delivery | At-least-once is common default |
| KF15 | Idempotency | Make consumers safe to retry |
| KF16 | Keys | Same key → same partition → order |
| KF17 | Schema | Registry enforces compatibility |
| KF18 | vs Queue | Log+replay+many consumers vs hand-off |
| KF19 | vs RabbitMQ | Streaming/scale vs routing/tasks |
| KF20 | vs Redis Pub/Sub | Durable vs ephemeral |
| KF21 | Event-driven | Emit events; services react |
| KF22 | Connect | Connectors + CDC without code |
| KF23 | Streams | Process events in real time |
| KF24 | DLQ | Dead-letter poison messages |
| KF25 | Lag | Key health metric; scale to partitions |
| KF26 | Performance | Sequential IO, batching, compression |
| KF27 | Security | TLS + SASL + ACLs |
| KF28 | Azure | Managed Event Hubs/Confluent |
| KF29 | Pitfalls | Global-order myth, non-idempotency |
| KF30 | My approach | Keyed topics, groups, at-least-once + idempotency |

---

[← Redis Cache](48-concept-redis-cache.md) · [Home](README.md) · [Next → Data Design](50-concept-data-design.md)
