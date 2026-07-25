# Chapter 11 — A Decision Framework You Can Actually Use

← [Chapter 10](10-observability.md) · [Tutorial index](README.md) · Next: [The case studies](../case-studies/)

---

## In one line

Five questions, in order, instead of "it depends".

---

## The five questions

Ask them **in this order**, for every piece of communication you design. Each one narrows the choice.

### Q1. Can the caller continue without the answer?

| Answer | Choose |
|---|---|
| **No** — the caller cannot produce a response without it | **Synchronous.** HTTP or gRPC. |
| **Yes** — the caller can respond now and let the rest happen later | **Asynchronous.** Publish a message. |

This is the biggest fork, and it is a **business** question, not a technical one. Ask the product owner: *"If this step took 30 seconds, would we still accept the order?"*

Watch for the false "no". "The user needs to see the payment confirmed" usually means "the user needs to know we received their order" — which is `202 Accepted` plus a push update, not a blocking charge.

→ Chapters [2](02-synchronous.md) and [3](03-asynchronous.md).

---

### Q2. Does anyone need to replay this later?

Only ask this if Q1 said asynchronous.

| Answer | Choose |
|---|---|
| **Yes** — rebuild a read model, onboard a new consumer with history, reprocess after a bug fix, or the log is your audit trail | **Event log**: Kafka |
| **No** — once processed, it is done | **Queue**: RabbitMQ, Azure Service Bus, SQS |

Be honest. "We might need replay one day" is not a yes. A yes means you can **name the consumer** that needs it.

→ Chapter [4](04-choosing-a-broker.md).

---

### Q3. One consumer or many, now and in future?

| Answer | Choose |
|---|---|
| Exactly one service must act | **Command → queue.** Name it `DoSomething`. |
| Several services care, or may care later | **Event → topic.** Name it `SomethingHappened`. |

The test from chapter 3: *"Would it be a bug if nobody handled this?"* Yes → command. No → event.

Default to events. Adding a consumer to a topic costs nothing. Turning a command into an event later means changing the producer.

→ Chapter [3](03-asynchronous.md).

---

### Q4. What breaks if this message arrives twice?

| Answer | You must |
|---|---|
| Nothing — it sets an absolute value | Nothing extra. It is naturally idempotent. |
| Money moves twice, stock doubles, an email is duplicated | Add an **inbox** table, or an **idempotency key** at the boundary |

There is no third option, and no broker setting that removes this. At-least-once is the ground truth.

Do this work **before** you go live. Retrofitting idempotency after a double-charge incident is much more expensive, and by then it is a customer-trust problem, not an engineering one.

→ Chapter [8](08-outbox-and-idempotency.md).

---

### Q5. Who owns this data, and who is merely reading it?

| Answer | Do this |
|---|---|
| One clear owner, others read | Owner exposes an API and publishes events. Readers keep a local snapshot if they need speed. |
| Two services both write it | **Stop.** The boundary is wrong. Merge them, or split the data so each part has one owner. |
| Nobody knows | Decide today, and write it down. An undecided owner becomes a shared table within a year. |

This is the question that prevents a distributed monolith, and the one teams skip.

→ Chapter [6](06-boundaries-and-data.md).

---

## The framework as a flowchart

```
                    ┌─────────────────────────────────────┐
                    │ Q1. Can the caller continue         │
                    │     without the answer?             │
                    └──────────────┬──────────────────────┘
                    NO             │             YES
          ┌────────────────────────┴───────────────────────┐
          ▼                                                ▼
   ┌─────────────┐                          ┌──────────────────────────┐
   │ SYNCHRONOUS │                          │ Q2. Need replay later?   │
   │ HTTP / gRPC │                          └───────────┬──────────────┘
   └──────┬──────┘                             YES      │      NO
          │                              ┌──────────────┴──────────────┐
          ▼                              ▼                             ▼
  Add all 5 resilience              ┌─────────┐                  ┌──────────┐
  layers (chapter 9).               │  KAFKA  │                  │  QUEUE   │
  The user is waiting.              └────┬────┘                  └─────┬────┘
                                         └────────────┬────────────────┘
                                                      ▼
                                    ┌──────────────────────────────────┐
                                    │ Q3. One consumer or many?        │
                                    │  one → command  ·  many → event  │
                                    └────────────────┬─────────────────┘
                                                     ▼
                                    ┌──────────────────────────────────┐
                                    │ Q4. Safe if delivered twice?     │
                                    │  no → inbox / idempotency key    │
                                    └────────────────┬─────────────────┘
                                                     ▼
                                    ┌──────────────────────────────────┐
                                    │ Q5. Who owns the data?           │
                                    │  two writers → fix the boundary  │
                                    └──────────────────────────────────┘
```

> **Diagram: reuse D4** — [`images/svg/d4-broker-decision.svg`](../images/svg/d4-broker-decision.svg)

---

## Worked examples

### Example 1 — "Send a confirmation email when an order is placed"

| Q | Answer | Result |
|---|---|---|
| Q1 | The user does not wait for SMTP | **Async** |
| Q2 | Nobody replays emails | **Queue**, not Kafka |
| Q3 | Notifications, Analytics, and Loyalty all care | **Event** on a topic |
| Q4 | A duplicate email is embarrassing | **Inbox** table in Notifications |
| Q5 | Notifications owns delivery; Ordering owns the order | Clean |

**Design:** `OrderPlaced` event → topic → Notifications subscription with an inbox.

---

### Example 2 — "Check stock before accepting an order"

| Q | Answer | Result |
|---|---|---|
| Q1 | You cannot accept an order for something you do not have | **Sync** |
| Q2–Q4 | Not applicable | — |
| Q5 | Inventory owns stock. Ordering only reads it. | Clean |

**Design:** `Ordering` → gRPC → `Inventory`, 500 ms timeout, circuit breaker, and a fallback ("allow the order, verify asynchronously") if the business accepts a small oversell risk.

**Note how Q1 can be re-answered.** Many retailers deliberately accept the order and reconcile stock afterwards — trading a rare oversell for a checkout that never fails. That is a business decision, and it converts a sync call into an async one. Always ask.

---

### Example 3 — "Publish every price tick to whoever wants it"

| Q | Answer | Result |
|---|---|---|
| Q1 | The feed handler never waits | **Async** |
| Q2 | Backtesting replays months of ticks | **Kafka**, clearly |
| Q3 | Charting, risk, alerts, storage — many | **Event** on a topic |
| Q4 | A duplicate tick corrupts a candle | Dedupe by `(symbol, sequenceNumber)` |
| Q5 | The feed handler owns raw ticks; everyone else reads | Clean |

**Design:** Kafka topic partitioned by symbol, retention 7 days hot plus cold archive, consumers dedupe on sequence number. This is [case study 3](../case-studies/03-stock-market-data/).

---

### Example 4 — "Move money between two accounts"

| Q | Answer | Result |
|---|---|---|
| Q1 | The user must know it succeeded | **Sync API**, async settlement behind it |
| Q2 | The ledger **is** the audit trail; regulators may ask for replay | **Kafka** or an append-only ledger table |
| Q3 | Ledger, notifications, fraud, reporting | **Event** |
| Q4 | A duplicate moves money twice — the worst possible outcome | **Idempotency key**, mandatory, plus an inbox |
| Q5 | The ledger owns balances. Nothing else writes them. Ever. | Clean, and non-negotiable |

**Design:** `POST /transfers` with a required `Idempotency-Key`, returns `202`. A saga with orchestration ([chapter 7](07-saga.md)) coordinates debit and credit, with the ledger as the single writer. This is [case study 2](../case-studies/02-banking-payments/).

---

## The short version, for a whiteboard

Copy this into your design doc template:

```
1. Can the caller continue without the answer?      No → sync.  Yes → async.
2. Does anyone need to replay it?                   Yes → log (Kafka).  No → queue.
3. One consumer or many?                            One → command.  Many → event.
4. What breaks if it arrives twice?                 Anything → inbox / idempotency key.
5. Who owns this data?                              Two writers → the boundary is wrong.
```

---

## Anti-patterns, and what each one really means

| What you see | What it means | What to do |
|---|---|---|
| Six sync hops for one request | Latency = sum, availability = product | Make hops async, or merge the services |
| Two services writing one table | The boundary is wrong | One writer, others via API or events |
| Kafka used purely as a work queue | Paying cluster ops for an unused feature | Use a queue |
| Replaying a queue to rebuild state | You need a log | Use Kafka |
| Retry with no circuit breaker | Turns a slowdown into an outage | Add the breaker |
| The same event handled twice, incorrectly | No idempotency | Add an inbox |
| Publishing after `SaveChanges` | The dual-write bug | Add an outbox |
| A saga with no timeouts | Stuck flows nobody notices | Add a timeout on every wait |
| A trace that stops at the broker | Context not propagated | Inject and extract at publish/consume |
| DB check in the liveness probe | Restart storms during a DB blip | Move it to readiness |
| Business logic in the gateway | Rules owned by nobody | Move it into the service |
| One shared `Common.Models` library | A monolith wearing a NuGet costume | Share contracts only |

---

## Before you build: a one-page design checklist

For every new service or flow, answer these. If you cannot, you are not ready to write code.

**Communication**
- [ ] For each call, which of the five questions decided it? Write the answer down.
- [ ] Every sync call has a timeout, and a number you can justify.
- [ ] Every sync call has a circuit breaker.
- [ ] Every consumer is idempotent, and you know how (natural / inbox / key).
- [ ] Every publish that follows a database write goes through an outbox.

**Boundaries**
- [ ] Every entity has exactly one owning service, written in the ownership table.
- [ ] No service reads another service's database.
- [ ] Contracts are versioned; you know how you would ship a breaking change.

**Failure**
- [ ] You know what happens if each dependency is down for 5 minutes.
- [ ] You know which features are allowed to degrade, and how.
- [ ] Every wait in every saga has a timeout.
- [ ] Every queue has a dead-letter queue, and the DLQ has an alert.

**Visibility**
- [ ] One correlation ID flows end to end, including across the broker.
- [ ] Traces join up across HTTP **and** messages.
- [ ] Queue depth, DLQ depth, and outbox pending are on a dashboard with alerts.
- [ ] You can answer "where is order X right now?" with one query.

**Honesty**
- [ ] You can name what you bought by splitting this service.
- [ ] The team can operate what you are about to build.
- [ ] Local development runs one service without the other twelve.

---

## The closing thought

Go back to the 2 a.m. incident from the start of this tutorial: payments got slow, orders timed out, retries amplified the load, checkout collapsed.

What would have prevented it?

1. **A timeout** on the payment call — so a slow call fails fast instead of holding a thread.
2. **A circuit breaker** — so once payments was clearly struggling, the retries stopped.
3. **An async handoff** — so an order never depended on a card being charged inside the request.

Three changes. Not a rewrite. Not a new framework. Not a migration.

That is the actual lesson of this whole tutorial: **the hard part of microservices is not splitting the code, it is choosing how the pieces talk.** Almost every serious outage in a distributed system traces back to one of the choices in these eleven chapters — usually a missing timeout, a missing breaker, a missing idempotency check, or a boundary drawn in the wrong place.

Now go and read the [case studies](../case-studies/), where all of it happens at once.

---

← [Chapter 10](10-observability.md) · [Tutorial index](README.md) · Next: [Case studies](../case-studies/)
