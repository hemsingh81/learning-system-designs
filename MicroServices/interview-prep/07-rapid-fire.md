# 7 — Rapid Fire

← [System design scenarios](06-system-design-scenarios.md) · [Interview index](README.md) · [Back to the map](../README.md)

45 short questions. One or two sentences each — the quick-check round, or your revision pass on the train.

Each links to the full explanation if the short answer is not enough.

---

## Basics

<details><summary><b>1 · What is a microservice?</b></summary>

A service you can deploy on its own that owns its own data and does one job for the business. If it shares a database with another service, it is not one.

📖 [Chapter 1](../tutorial/01-three-axes.md)
</details>

<details><summary><b>2 · Microservices vs monolith in one line?</b></summary>

A trade: you buy independent deployment, scaling, and failure; you pay with network latency, eventual consistency, and operational overhead.

📖 [Chapter 6](../tutorial/06-boundaries-and-data.md#when-to-split-when-not-to)
</details>

<details><summary><b>3 · What is a distributed monolith?</b></summary>

Many deployables that still must change and deploy together. All the cost of microservices, none of the benefit.

📖 [Chapter 6](../tutorial/06-boundaries-and-data.md#the-distributed-monolith-checklist)
</details>

<details><summary><b>4 · Fastest way to spot one?</b></summary>

A new developer cannot run one service alone and do useful work.

📖 [Chapter 6](../tutorial/06-boundaries-and-data.md#the-distributed-monolith-checklist)
</details>

<details><summary><b>5 · What is a bounded context?</b></summary>

A part of the business where a word has exactly one meaning. "Customer" means something different to Ordering, Payments, and Support — and all three are correct.

📖 [Chapter 6](../tutorial/06-boundaries-and-data.md#bounded-contexts-explained-with-one-word)
</details>

<details><summary><b>6 · East-west vs north-south?</b></summary>

East-west is service to service inside your network. North-south is the outside world crossing your trust boundary.

📖 [Chapter 1](../tutorial/01-three-axes.md#the-three-axes)
</details>

---

## Sync and async

<details><summary><b>7 · The one question that decides sync vs async?</b></summary>

Can the caller continue without the answer? No → sync. Yes → async.

📖 [Chapter 11](../tutorial/11-decision-framework.md#q1-can-the-caller-continue-without-the-answer)
</details>

<details><summary><b>8 · What happens to availability with 4 sync dependencies at 99.9%?</b></summary>

0.999⁴ = 99.6%, about 3.5 hours of downtime a month caused entirely by other people.

📖 [Chapter 2](../tutorial/02-synchronous.md#edge-1--temporal-coupling)
</details>

<details><summary><b>9 · Latency and availability in a sync chain?</b></summary>

Latency is the **sum**. Availability is the **product**. Both get worse with every hop.

📖 [Chapter 2](../tutorial/02-synchronous.md#edge-2--latency-compounds)
</details>

<details><summary><b>10 · REST or gRPC?</b></summary>

gRPC inside, REST at the edge. gRPC is 5–10× smaller and contract-first; browsers cannot call it directly.

📖 [Chapter 2](../tutorial/02-synchronous.md#option-b--grpc)
</details>

<details><summary><b>11 · Command vs event?</b></summary>

Command = "do this", one named receiver, can be rejected. Event = "this happened", no receiver, past tense, already true.

📖 [Chapter 3](../tutorial/03-asynchronous.md#commands-vs-events--the-distinction-that-drives-everything)
</details>

<details><summary><b>12 · The test for which one you have?</b></summary>

"Would it be a bug if nobody handled this?" Yes → command. No → event.

📖 [Chapter 3](../tutorial/03-asynchronous.md#test-for-which-one-you-have)
</details>

<details><summary><b>13 · Queue vs topic?</b></summary>

Queue = one consumer gets each message (work distribution). Topic = every subscriber gets every message (fan-out).

📖 [Chapter 3](../tutorial/03-asynchronous.md#queues-vs-topics)
</details>

<details><summary><b>14 · What are competing consumers?</b></summary>

Several instances reading one queue to go faster. Each message is handled once, by whichever is free.

📖 [Chapter 3](../tutorial/03-asynchronous.md#queue--work-distribution)
</details>

<details><summary><b>15 · Why is request-reply over a broker a smell?</b></summary>

You pay every cost of async and keep the one cost of sync — the caller still waits. Use HTTP.

📖 [Chapter 3](../tutorial/03-asynchronous.md#request-reply-over-a-broker--usually-a-smell)
</details>

<details><summary><b>16 · Why 202 and not 201?</b></summary>

`202 Accepted` means "I have taken responsibility for this, it is not finished". Saying `201 Created` when payment has not cleared is a lie that becomes a support ticket.

📖 [Chapter 3](../tutorial/03-asynchronous.md#code--publishing-an-event)
</details>

---

## Brokers

<details><summary><b>17 · RabbitMQ vs Kafka in one question?</b></summary>

Does anyone need to re-read old messages? Yes → Kafka. No → RabbitMQ.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#the-decision-as-questions)
</details>

<details><summary><b>18 · The two mental models?</b></summary>

RabbitMQ = smart broker, dumb consumer (a post office). Kafka = dumb broker, smart consumer (a DVR).

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#the-four-options-and-their-mental-models)
</details>

<details><summary><b>19 · What does a Kafka partition key decide?</b></summary>

Two things at once: ordering (guaranteed within a partition) and parallelism (consumers cannot exceed partitions).

📖 [Case study 3](../case-studies/03-stock-market-data/README.md#partitioning--the-most-important-design-decision-here)
</details>

<details><summary><b>20 · Why over-provision partitions?</b></summary>

Adding them later re-hashes keys, so ordering breaks for in-flight entities. Extra partitions cost almost nothing now.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#sharp-edges)
</details>

<details><summary><b>21 · What is a hot partition?</b></summary>

One key taking a disproportionate share of traffic, so its partition lags while others idle. Adding consumers does not help.

📖 [Case study 3](../case-studies/03-stock-market-data/README.md#partitioning--the-most-important-design-decision-here)
</details>

<details><summary><b>22 · Risk of 7-day Kafka retention?</b></summary>

On day 8 your "replayable log" is empty. People discover this during an incident.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#sharp-edges)
</details>

<details><summary><b>23 · When is Dapr worth it?</b></summary>

When multi-cloud portability is a real requirement. The cost is a sidecar and losing broker-specific features.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#dapr--a-portability-layer-over-any-of-the-above)
</details>

<details><summary><b>24 · One sign you chose the wrong broker?</b></summary>

Using Kafka purely as a work queue and never replaying — you are paying cluster operations for an unused feature.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#signals-you-chose-wrong)
</details>

---

## Delivery and idempotency

<details><summary><b>25 · What is at-least-once delivery?</b></summary>

The broker guarantees arrival and accepts that it may arrive more than once. Duplicates are normal operation.

📖 [Chapter 3](../tutorial/03-asynchronous.md#edge-3--duplicates-are-normal-not-exceptional)
</details>

<details><summary><b>26 · Does exactly-once exist?</b></summary>

Not across a broker and your database. Kafka has it within Kafka only. Everywhere else: at-least-once plus idempotency.

📖 [Chapter 4](../tutorial/04-choosing-a-broker.md#sharp-edges)
</details>

<details><summary><b>27 · What is the dual-write problem?</b></summary>

Writing to your database and then publishing to a broker. Crash in between and the state and the events disagree, silently and permanently.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#the-bug-almost-everyone-ships-first)
</details>

<details><summary><b>28 · What does the outbox actually buy you?</b></summary>

It turns an unsolvable problem (loss) into a solvable one (duplication).

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#the-fix-the-transactional-outbox)
</details>

<details><summary><b>29 · The one outbox detail people get wrong?</b></summary>

The relay must republish with the **same `MessageId`**. A fresh ID per attempt makes consumer dedupe silently never match.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#the-relay)
</details>

<details><summary><b>30 · The three levels of idempotency?</b></summary>

Natural (set absolute values), an inbox table, or an idempotency key at an external boundary.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#the-other-half-idempotent-consumers)
</details>

<details><summary><b>31 · Why must the inbox key be composite?</b></summary>

`(MessageId, Consumer)`. Keyed on MessageId alone, the second consumer of the same event silently processes nothing.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#level-2--the-inbox-works-for-everything)
</details>

<details><summary><b>32 · Why is a SELECT check not enough for idempotency?</b></summary>

Two instances can both pass it before either commits. The unique constraint is the real guarantee; the check is a fast path.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#sharp-edges)
</details>

<details><summary><b>33 · Where must an idempotency key come from?</b></summary>

The client. A server-generated key is new on every retry, which defeats the entire mechanism.

📖 [Chapter 8](../tutorial/08-outbox-and-idempotency.md#level-3--idempotency-keys-at-the-boundary)
</details>

---

## Sagas

<details><summary><b>34 · Why not two-phase commit?</b></summary>

The coordinator is a single point of failure, locks are held across the network, and every participant must support it. Your payment provider does not.

📖 [Chapter 7](../tutorial/07-saga.md#why-two-phase-commit-does-not-fit)
</details>

<details><summary><b>35 · A saga in one sentence?</b></summary>

A sequence of local transactions where each step has an undo — and the undo is a new real action, not a rollback.

📖 [Chapter 7](../tutorial/07-saga.md#the-saga-idea)
</details>

<details><summary><b>36 · Choreography or orchestration?</b></summary>

Choreography for 2–4 stable steps. Orchestration at 5+, or when you need to answer "where is order X stuck?".

📖 [Chapter 7](../tutorial/07-saga.md#choosing-between-them)
</details>

<details><summary><b>37 · Why is compensation more dangerous than the forward path?</b></summary>

A "do" that runs twice usually fails loudly. An "undo" that runs twice succeeds silently and invents inventory or money.

📖 [Chapter 7](../tutorial/07-saga.md#rule-1--compensation-must-be-idempotent)
</details>

<details><summary><b>38 · What is a pivot step?</b></summary>

The point of no return. Design so irreversible steps come last.

📖 [Chapter 7](../tutorial/07-saga.md#rule-3--some-steps-cannot-be-undone-the-pivot-step)
</details>

<details><summary><b>39 · The most common real-world saga bug?</b></summary>

A wait with no timeout. The saga sits forever and nothing errors.

📖 [Chapter 7](../tutorial/07-saga.md#rule-4--add-a-timeout-for-every-wait)
</details>

<details><summary><b>40 · When does "we need a distributed transaction" mean something else?</b></summary>

Usually that the boundary is wrong. Merging two services is a legitimate answer.

📖 [Chapter 7](../tutorial/07-saga.md#when-to-use-a-saga-at-all)
</details>

---

## Resilience and operations

<details><summary><b>41 · The five resilience layers in order?</b></summary>

Timeout → retry → circuit breaker → bulkhead → fallback. Each only works because the one outside it exists.

📖 [Chapter 9](../tutorial/09-resilience.md#the-order-matters)
</details>

<details><summary><b>42 · Why is retry without a circuit breaker dangerous?</b></summary>

Three retries means 4× traffic to a service that is already struggling. The retries turn a slowdown into an outage.

📖 [Chapter 9](../tutorial/09-resilience.md#layer-3--circuit-breaker)
</details>

<details><summary><b>43 · Why does retry need jitter?</b></summary>

Without it, everyone who failed at the same moment retries at the same moment — a thundering herd that repeats the failure.

📖 [Chapter 9](../tutorial/09-resilience.md#why-jitter-is-not-optional)
</details>

<details><summary><b>44 · Liveness vs readiness?</b></summary>

Liveness failing restarts the pod; readiness failing just stops traffic. Put the database check in liveness and a 30-second blip becomes a restart storm.

📖 [Chapter 9](../tutorial/09-resilience.md#health-checks--liveness-vs-readiness)
</details>

<details><summary><b>45 · The most important metric in an async system?</b></summary>

Consumer lag per partition — it tells you that you are falling behind about 20 minutes before a human notices.

📖 [Chapter 3](../tutorial/03-asynchronous.md#edge-6--queue-depth-is-your-most-important-metric)
</details>

---

## Ten one-liners worth memorising

| | |
|---|---|
| 1 | Latency is the **sum**; availability is the **product**. |
| 2 | "Would it be a bug if nobody handled this?" — the command/event test. |
| 3 | The outbox turns **loss** into **duplication**. |
| 4 | Duplicates are **normal operation**, not an error. |
| 5 | You cannot roll back across services — you can only **apologise correctly**. |
| 6 | An **undo that runs twice** fails silently. That is the dangerous one. |
| 7 | Retry without a breaker is an **attack on your own system**. |
| 8 | Liveness checks the **process**; readiness checks the **dependencies**. |
| 9 | If two services write the same table, the **boundary is wrong**. |
| 10 | "We need a distributed transaction" usually means **merge the services**. |

---

← [System design scenarios](06-system-design-scenarios.md) · [Interview index](README.md) · [Back to the map](../README.md)
