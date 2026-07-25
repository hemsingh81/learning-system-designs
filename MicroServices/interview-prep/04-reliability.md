# 4 — Reliability

← [Boundaries and edges](03-boundaries-and-edges.md) · [Interview index](README.md) · Next: [Observability →](05-observability.md)

24 questions. **This is the highest-value section.** Sagas, the outbox, idempotency, and resilience are where interviews separate people who have run distributed systems from people who have read about them.

---

## Transactions and sagas

<details id="q1">
<summary><b>Q1 · Why not use two-phase commit across services?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

It works, and it is almost never the right answer:

- The **coordinator is a single point of failure** — if it dies between "prepare" and "commit", every participant holds locks and waits, indefinitely.
- **Locks are held across the network**, so throughput collapses.
- **Every participant must support it** — your payment provider's REST API does not, and neither does Kafka.
- It **trades availability for consistency**: your uptime becomes the product of everyone's uptime.

**If they dig deeper**

The saga trade is the opposite: stay available, accept a short window of inconsistency, and clean up explicitly with compensating actions.

Worth saying: 2PC is not *wrong*, it is *unsuited*. Within one database across multiple tables, use a normal transaction — that is 2PC's problem domain done properly.

**Follow-up to expect:** *"So when is a distributed transaction fine?"* → When both halves are in one service and one database. Which is exactly the point of Q4 below.

📖 [Chapter 7 — Why two-phase commit does not fit](../tutorial/07-saga.md#why-two-phase-commit-does-not-fit)

</details>

---

<details id="q2">
<summary><b>Q2 · What is a saga?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A sequence of local transactions, where each step has an **undo** step. If step 3 fails, you run the undos for steps 2 and 1.

The key insight: the undo is not a rollback. "Refund the card" is a **second, real event** — the original charge really happened and is on the customer's statement.

**If they dig deeper**

| Step | Do | Undo |
|---|---|---|
| 1 | Reserve stock | Release stock |
| 2 | Charge card | Refund card |
| 3 | Confirm order | Cancel order |
| 4 | Ship parcel | *cannot undo* |

The framing worth using in an interview: **you cannot roll back across services, you can only apologise correctly.** You are not making it as if nothing happened; you are making the outcome fair.

**Follow-up to expect:** *"What do you lose compared to a transaction?"* → Isolation — ACID's "I". Halfway through, other users can see intermediate state: stock reserved but order unconfirmed. You design for it with explicit states rather than hoping nobody looks.

📖 [Chapter 7 — The saga idea](../tutorial/07-saga.md#the-saga-idea)

</details>

---

<details id="q3">
<summary><b>Q3 · Choreography or orchestration?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐⭐ <i>never answer with one word</i></summary>

**The 30-second answer**

**Choreography** — no coordinator, each service reacts to events. Simple at 3 steps, opaque at 10.

**Orchestration** — one coordinator owns the flow. One more component, but the flow is a single readable file.

I default to choreography and switch to orchestration the first time someone asks "what actually happens after an order is placed?" and three people give three different answers.

**If they dig deeper**

| Question | Choreography | Orchestration |
|---|---|---|
| How many steps? | 2–4 | 5+ |
| "Where is order X stuck?" | Search five services' logs | One query |
| Flow changes often? | Painful | Easy — one file |
| Extra component? | No | Yes |
| Compensation decisions | Each service alone | Coordinator, with full context |
| Risk | Hidden flow; accidental cycles | Coordinator becomes a god object |

**The two case studies show both, and the reasons differ.** E-commerce uses choreography: four steps, stable flow, nothing to build. Banking uses orchestration: compliance reviews the flow, support must answer "where is this transfer?", and compensation needs to know *whether the ledger posted before the payment failed* — which only a coordinator holding state can answer.

**Follow-up to expect:** *"What is the danger of orchestration?"* → The saga becoming a god object. It should decide **sequence and compensation**, never policy. "If the customer is Gold, skip the credit check" belongs in the credit-check service. The moment the saga holds business rules, every team must edit it to ship anything.

📖 [Chapter 7 — Choosing between them](../tutorial/07-saga.md#choosing-between-them)

</details>

---

<details id="q4">
<summary><b>Q4 · Design a money transfer between two accounts.</b> &nbsp;·&nbsp; <code>Staff+</code> &nbsp;⭐ <i>the premise is a trap</i></summary>

**The 30-second answer**

The debit and the credit go in **one local database transaction, in one service**. Not a saga.

A saga coordinates everything *around* the posting — fraud screening, the outbound payment, notifications — but never *through* it. If debit and credit are in two services, there is a window where money exists in neither account or both.

**If they dig deeper**

```csharp
using var tx = await db.Database.BeginTransactionAsync(IsolationLevel.Serializable, ct);
db.JournalEntries.Add(debit);
db.JournalEntries.Add(credit);
await db.SaveChangesAsync(ct);
await tx.CommitAsync(ct);      // both, or neither. Real ACID.
```

And `Serializable`, not `ReadCommitted` — otherwise two concurrent transfers from the same account both read a balance of 1,000, both pass a check for 800, and you have created an overdraft that nobody notices until a customer complains.

This is chapter 7's most useful note in practice: **"we need a distributed transaction here" usually means the boundary is wrong.** Merging is a legitimate answer.

**Follow-up to expect:** *"What if the accounts are at different banks?"* → Then you genuinely cannot have one transaction, and it becomes a saga with an `Unknown` state and a reconciler. Which is exactly what the banking case study does for external payments — and note it never auto-retries an ambiguous one.

📖 [Case study 2 — Why the ledger posting is NOT a saga](../case-studies/02-banking-payments/README.md#why-the-ledger-posting-is-not-a-saga)

</details>

---

<details id="q5">
<summary><b>Q5 · What makes a compensating action correct?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Four rules:

1. **It must be idempotent.** The compensating message can arrive twice.
2. **It must handle "nothing to undo."** The step may never have run.
3. **It can fail too** — so retry it, with backoff, and alert if it never succeeds.
4. **Some steps cannot be undone.** Design so irreversible steps come last.

**If they dig deeper**

Rule 1 deserves a specific warning, and it is the thing I would want a senior candidate to raise unprompted:

> A "do" step that runs twice usually fails loudly — a duplicate key, a rejected charge. An **"undo" that runs twice succeeds silently** and quietly invents inventory you do not have, or credits money you never took. Nobody notices until a stock count or an audit.

Hence the guards:

```csharp
if (reservation is null)     return;   // never reserved — nothing to undo
if (reservation.IsReleased)  return;   // already released — do NOT release twice
```

**Follow-up to expect:** *"What if the refund API is down?"* → Retry, aggressively and for a long time, then alert a human. Compensation is not allowed to give up quietly: a failed refund is a customer charged for nothing, which is a legal problem, not a bug.

📖 [Chapter 7 — Compensating actions in practice](../tutorial/07-saga.md#compensating-actions-in-practice)

</details>

---

<details id="q6">
<summary><b>Q6 · What is a pivot step?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

The point of no return. After it, the saga must go forward, not backward.

You cannot un-send an email. You cannot un-ship a parcel that is on a truck.

```
Reserve stock   ← can undo
Charge card     ← can undo (refund)
────── PIVOT: hand the parcel to the courier ──────
Send email      ← cannot undo, but harmless
Deliver         ← must go forward
```

**If they dig deeper**

The design rule: **irreversible steps come last**, after everything that can fail has already succeeded.

If an irreversible step sits in the middle of your saga, that is a design bug, not an implementation detail — reorder the steps. If it genuinely cannot be moved, you need a manual-resolution path with a human in it, because no code can undo it.

**Follow-up to expect:** *"What if you discover the pivot too late?"* → You get the state the banking case study calls `NeedsManualResolution`, and someone has to fix it by hand. Which is fine as a designed escape hatch and terrible as a surprise.

📖 [Chapter 7 — Rule 3: some steps cannot be undone](../tutorial/07-saga.md#rule-3--some-steps-cannot-be-undone-the-pivot-step)

</details>

---

<details id="q7">
<summary><b>Q7 · What is the dual-write problem?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐⭐ <i>the separator question</i></summary>

**The 30-second answer**

Writing the same fact to two places — your database and the broker — without a shared transaction.

```csharp
await db.SaveChangesAsync();        // ① commits
await bus.Publish(new OrderPlaced(...));   // ② separate act — crash here?
```

Crash between ① and ② and the order exists but the event never fires. Payments never charges, nothing errors, and nothing in any log says "error". The order sits at `Pending` forever.

**If they dig deeper**

Swapping the order is worse: publish first, crash before the commit, and Payments charges a card for an order you have no record of.

And the "clever" fix fails too:

```csharp
using var tx = ...;
await db.SaveChangesAsync();
await bus.Publish(evt);      // if the COMMIT then fails, this is already gone
await tx.CommitAsync();      // you cannot un-publish
```

**The core truth to state:** a database transaction cannot include a network call to a different system. Every attempt to make it look like it can is a bug with better camouflage.

**Follow-up to expect:** *"So what do you do?"* → The transactional outbox — Q8.

📖 [Chapter 8 — The bug almost everyone ships first](../tutorial/08-outbox-and-idempotency.md#the-bug-almost-everyone-ships-first)

</details>

---

<details id="q8">
<summary><b>Q8 · Explain the transactional outbox.</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐ <i>commonly asked</i></summary>

**The 30-second answer**

Stop trying to do two things atomically. Do one: write to your own database.

```
BEGIN
  INSERT INTO orders  (…)     ← the business fact
  INSERT INTO outbox  (…)     ← the intention to publish
COMMIT                        ← both or neither. One database. Real atomicity.

… a background relay reads the outbox and publishes …
```

**If they dig deeper**

The one-line summary worth memorising:

> **The outbox turns an unsolvable problem (loss) into a solvable one (duplication).**

If the relay crashes after publishing but before marking the row sent, it republishes on restart. That is a duplicate, not a loss — and duplicates are handled by idempotent consumers.

The detail that shows you have actually built one: the relay must publish with the **same `MessageId` every time**, taken from the outbox row. Generate a fresh ID per attempt and every retry looks like a brand-new message, so consumer dedupe silently never matches.

**Follow-up to expect:** *"Polling or CDC?"* → Start with polling every 500 ms; it is simple, needs no extra infrastructure, and the delay is invisible next to the eventual consistency you already have. Move to CDC (Debezium) only when you can measure that polling is a problem.

📖 [Chapter 8 — The fix: the transactional outbox](../tutorial/08-outbox-and-idempotency.md#the-fix-the-transactional-outbox)

</details>

---

<details id="q9">
<summary><b>Q9 · A message is delivered twice. How do you handle it?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐⭐ <i>the production-experience test</i></summary>

**The 30-second answer**

Three levels, in order of preference:

1. **Natural idempotency** — the operation is already safe to repeat. `SET status = 'Confirmed'` is fine; `balance -= amount` is not.
2. **An inbox table** — record every processed `(MessageId, Consumer)` in the same transaction as the work.
3. **An idempotency key** — when the side effect is in someone else's system, send them a stable key so *they* dedupe.

**If they dig deeper**

The rule for level 1: **set absolute values, do not apply deltas.**

For level 2, the detail that matters is that the `SELECT` check is only an optimisation. **The primary key on `(MessageId, Consumer)` is the actual guarantee**, because two instances can both pass the check before either commits:

```csharp
catch (DbUpdateException ex) when (ex.IsUniqueViolationOn("PK_InboxMessages"))
{
    return;   // another instance won the race and did the work. Not an error.
}
```

And it must be a **composite** key. Keyed on `MessageId` alone, the second consumer of the same event silently processes nothing.

**Follow-up to expect:** *"How long do you keep inbox rows?"* → Longer than your broker's maximum retention or retry window. If Kafka keeps 7 days, keep inbox rows at least 8 — otherwise a very late redelivery is treated as new.

📖 [Chapter 8 — The other half: idempotent consumers](../tutorial/08-outbox-and-idempotency.md#the-other-half-idempotent-consumers)

</details>

---

<details id="q10">
<summary><b>Q10 · What is an idempotency key and where does it come from?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

A stable, client-supplied value that identifies one logical operation, so a retry is recognised rather than re-executed.

**It must come from the client.** A server-generated key is new on every retry, which defeats the mechanism at exactly the moment it is needed.

**If they dig deeper**

Two directions, and both matter:

**Outbound** — derive it from the entity so it is identical on every attempt:

```csharp
request.Headers.Add("Idempotency-Key", $"charge-{orderId}");
// Guid.NewGuid() here would be indistinguishable from correct code in review,
// and would silently break everything this exists to prevent.
```

**Inbound** — expose it on your own write APIs, with a unique index:

```csharp
var existing = await db.Orders.FirstOrDefaultAsync(o => o.IdempotencyKey == key, ct);
if (existing is not null) return Results.Ok(existing);   // the retry. Same result.
```

**Follow-up to expect:** *"What if the same key arrives with different data?"* → Reject with 409. That is a client bug, and silently returning an unrelated order would be worse. The banking case study does exactly this.

📖 [Chapter 8 — Level 3: idempotency keys at the boundary](../tutorial/08-outbox-and-idempotency.md#level-3--idempotency-keys-at-the-boundary)

</details>

---

<details id="q11">
<summary><b>Q11 · Does exactly-once delivery exist?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Not across a broker and your database, whatever the marketing says.

Kafka has exactly-once *within Kafka*: read a topic, process, write a topic, transactionally. The moment your side effect is a database write, a card charge, or an email, you are back to at-least-once.

**If they dig deeper**

The reason is simple and worth stating plainly: you cannot atomically commit to two independent systems. Either you ack the message first (and risk losing work) or you do the work first (and risk doing it twice). There is no third option.

So the industry converged on at-least-once **plus idempotency**, which is effectively "exactly-once processing" without pretending you have exactly-once delivery.

**Follow-up to expect:** *"What about exactly-once semantics in Kafka Streams?"* → Genuine, and genuinely limited to Kafka-to-Kafka. It is a strong tool for stream processing and does nothing for your database or a third-party API.

📖 [Chapter 4 — Sharp edges](../tutorial/04-choosing-a-broker.md#sharp-edges)

</details>

---

<details id="q12">
<summary><b>Q12 · Your saga is stuck. How did that happen and how do you prevent it?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Almost always the same cause: **a step whose reply never arrived, and no timeout on the wait.**

The saga sits in `AwaitingPayment` forever and nobody notices, because nothing errored.

**If they dig deeper**

Every wait needs a timeout and a decision about what to do when it fires:

```csharp
Schedule(() => PaymentTimeout, x => x.PaymentTimeoutTokenId, s => s.Delay = TimeSpan.FromMinutes(5));

During(AwaitingPayment,
    When(PaymentTimeout.Received)
        .If(c => c.Saga.StockReserved,
            b => b.Send(c => new ReleaseStock(c.Saga.CorrelationId)))
        .TransitionTo(Compensating));
```

Note `.If(c => c.Saga.StockReserved, …)` — compensate only what actually happened. The saga state records what was done precisely so the undo does not fire for a step that never ran.

**And monitor saga state.** A count of sagas by state over time is one of the most useful dashboards in a distributed system. Sagas sitting in one state for over an hour are real customers with real problems.

**Follow-up to expect:** *"What about two messages for the same saga arriving at once?"* → Optimistic concurrency with a `Version` column, and retry on conflict. Without it, two instances both load, both decide, and one silently overwrites the other's decision.

📖 [Chapter 7 — Rule 4: add a timeout for every wait](../tutorial/07-saga.md#rule-4--add-a-timeout-for-every-wait)

</details>

---

## Resilience

<details id="q13">
<summary><b>Q13 · Name the five resilience layers, in order, and say why the order matters.</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

```
Timeout → Retry → Circuit breaker → Bulkhead → Fallback
```

Bound the wait, retry sensibly, stop when it is clearly dead, contain the damage, degrade gracefully.

The order matters because each layer only works if the one outside it exists:

- Retry without timeout = you retry after 100 seconds. Useless.
- Retry without a breaker = you attack a struggling service and finish it off.
- Breaker without a bulkhead = one slow dependency still eats all your threads before the breaker notices.
- Bulkhead without a fallback = you correctly reject the call, then return a 500 anyway.

**If they dig deeper**

A useful asymmetry to mention: synchronous calls need all five because a user is waiting. Asynchronous consumers need fewer, because the queue itself absorbs failure and time. That is another argument for async where you can use it.

**Follow-up to expect:** *"Which one do teams most often skip?"* → The bulkhead. Everyone has timeouts and retries; far fewer cap concurrency per dependency, which is why one slow dependency so often takes down an entire service.

📖 [Chapter 9 — The order matters](../tutorial/09-resilience.md#the-order-matters)

</details>

---

<details id="q14">
<summary><b>Q14 · How do you choose a timeout value?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

Measure, do not guess:

1. Look at the dependency's **p99** latency.
2. Set the timeout to roughly **2–3× p99**.
3. Sanity check against your own SLA — if you must answer in 500 ms, a 2-second timeout on a dependency is already a lie.

**If they dig deeper**

**Timeouts must shrink as you go deeper:**

```
Gateway 5s → BFF 4s → Ordering 3s → Inventory 1s
```

Otherwise the outer layer gives up while inner work continues, burning resources on a result nobody will read.

And never rely on defaults. `HttpClient` defaults to 100 seconds. No user waits 100 seconds — they refresh, and now you have two hung requests.

**Follow-up to expect:** *"What happens when the client disconnects?"* → Ideally the work stops. Pass `HttpContext.RequestAborted` all the way down so a cancelled request does not keep computing a response nobody will read.

📖 [Chapter 9 — How to choose the number](../tutorial/09-resilience.md#how-to-choose-the-number)

</details>

---

<details id="q15">
<summary><b>Q15 · What should you retry, and what should you never retry?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

| Retry | Never retry |
|---|---|
| Timeout, connection refused | 400, 401, 403, 404, 422 |
| 503, 502, 504 | Any non-idempotent write without an idempotency key |
| 429 — but honour `Retry-After` | |
| 500 — maybe once; often a bug that will fail again | |

**If they dig deeper**

The rule behind the table: retry when the failure is **transient and the request had no effect**. A 400 will be a 400 next time. A `POST /charge` that timed out may have *succeeded*, so retrying it without an idempotency key risks double-charging.

Retrying a `429` immediately is a specific mistake worth naming: the service told you the one useful thing it could — slow down — and you ignored it.

**Follow-up to expect:** *"How many retries?"* → Three is a reasonable default, but the more important number is total time. Three retries with exponential backoff can take 30 seconds; if your budget is 3 seconds, you needed one retry, not three.

📖 [Chapter 9 — What to retry and what not to](../tutorial/09-resilience.md#what-to-retry-and-what-not-to)

</details>

---

<details id="q16">
<summary><b>Q16 · Why does retry need jitter?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

Without it, everyone who failed at the same moment retries at the same moment:

```
t=0s   1000 requests fail (service restarts)
t=1s   1000 retries arrive together  ← spike, it falls over again
t=3s   1000 retries arrive together  ← again
t=7s   1000 retries arrive together  ← it never gets a quiet moment to recover
```

Jitter spreads them out so the service actually gets a chance to come back.

**If they dig deeper**

This is the **thundering herd**, and it is why a service can stay down long after the original cause is fixed. The retries themselves become the outage.

```csharp
pipeline.AddRetry(new HttpRetryStrategyOptions
{
    BackoffType = DelayBackoffType.Exponential,
    UseJitter   = true,              // ← the important line
    Delay       = TimeSpan.FromMilliseconds(200)
});
```

**Follow-up to expect:** *"Retries multiply load — how do you bound that?"* → Three retries means 4× traffic when things go wrong, on a service that may already be overloaded. Retry budgets (allow retries up to ~10% of traffic) solve it properly; service meshes support them directly. Without a mesh, the circuit breaker is your protection.

📖 [Chapter 9 — Why jitter is not optional](../tutorial/09-resilience.md#why-jitter-is-not-optional)

</details>

---

<details id="q17">
<summary><b>Q17 · Why is retrying without a circuit breaker dangerous?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐⭐ <i>the cascading-failure test</i></summary>

**The 30-second answer**

Because a retry against an overloaded service is an attack on your own system. It turns a slowdown into an outage.

**If they dig deeper**

The full cascade, which is worth being able to narrate:

1. `Payments` gets slow — 200 ms to 4 s. Not down. Just slow.
2. `Ordering` calls it and waits 4 s per request.
3. Each waiting request holds a thread and a connection. The pool fills.
4. `Ordering` is now slow for **every** request, including ones that never touch payments.
5. The gateway's calls to `Ordering` time out.
6. **Retries kick in. Every timed-out request is now sent three times.**
7. Traffic to `Payments` triples. It goes from slow to dead.
8. Checkout is fully down, and the original cause is invisible under 10,000 timeout errors.

**Step 6 made it worse.** That is the answer.

The breaker fixes it: after 20 failures it opens, every subsequent call fails in under a millisecond without touching the network, `Ordering` stays healthy for everything else, and `Payments` gets zero traffic and a chance to recover.

**Follow-up to expect:** *"How do you tune it?"* → Failure ratio 0.5, minimum throughput 20, sampling 30 s, break 15–30 s as starting points. And **one breaker per dependency** — a global breaker means a failing recommendations service stops your payment calls.

📖 [Chapter 9 — Layer 3: circuit breaker](../tutorial/09-resilience.md#layer-3--circuit-breaker)

</details>

---

<details id="q18">
<summary><b>Q18 · What is a bulkhead and what does it protect against?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

A cap on concurrent calls to one dependency, so it cannot consume all your resources.

Named after a ship's watertight compartments: a hole in one does not sink the vessel.

**If they dig deeper**

The failure it prevents happens *before* the circuit breaker notices:

```
Payments is slow (4s). Ordering has 200 threads.
50 req/sec × 4s = 200 threads all waiting on Payments.
GET /orders — which never touches Payments — has no thread left.
Your entire service is down because ONE dependency is slow.
```

With a bulkhead of 20 concurrent + 10 queued, a slow `Payments` occupies at most 30 of your resources. The other 170 keep serving. **Degraded, not down.**

```csharp
pipeline.AddConcurrencyLimiter(new ConcurrencyLimiterOptions
{
    PermitLimit = 20,
    QueueLimit  = 10      // number 31 fails instantly
});
```

**Follow-up to expect:** *"How do you size it?"* → From the dependency's normal concurrency plus headroom, weighted by importance. A critical dependency gets a bigger share; a nice-to-have gets a small one so it can never starve the rest.

📖 [Chapter 9 — Layer 4: bulkhead](../tutorial/09-resilience.md#layer-4--bulkhead)

</details>

---

<details id="q19">
<summary><b>Q19 · What makes a good fallback?</b> &nbsp;·&nbsp; <code>Mid</code></summary>

**The 30-second answer**

One that answers "what is the best thing I can still do?" — a cached value, a default, a partial response, deferring the work, or an honest failure.

The most important part is not the code. It is **deciding in advance which features are allowed to fail**, and writing that list down before an incident.

**If they dig deeper**

| Feature | If its dependency is down |
|---|---|
| Checkout | **Must work.** Degrade to async payment |
| Product page | **Must work.** Serve from cache |
| Recommendations | Show best sellers |
| Reviews | Hide the section |
| Live stock count | Show "In stock" without a number |

That table is an architectural artefact, and producing one is a strong signal in an interview.

**Follow-up to expect:** *"What is the danger of fallbacks?"* → They hide failures. If you always serve stale cache when the price service is down, nobody notices it has been down a week. **Every fallback must emit a metric**, and past a threshold, an alert. Degraded must be visible.

📖 [Chapter 9 — Layer 5: fallback](../tutorial/09-resilience.md#layer-5--fallback)

</details>

---

<details id="q20">
<summary><b>Q20 · Liveness or readiness — what is the difference and why does it matter?</b> &nbsp;·&nbsp; <code>Senior</code> &nbsp;⭐ <i>a favourite</i></summary>

**The 30-second answer**

- **Liveness** — "is this process broken beyond repair?" Failure → the platform **kills and restarts** the pod.
- **Readiness** — "should I receive traffic right now?" Failure → the platform **stops sending traffic**, no restart.

**Rule: liveness checks only the process. Readiness checks the dependencies.**

**If they dig deeper**

The classic incident, and the reason this question gets asked:

```
Database has a 30-second blip.
The DB check is in the LIVENESS probe, so liveness fails on every pod.
Kubernetes restarts every pod, all at once.
All pods start cold, empty caches, all reconnect to the database simultaneously.
The database, already struggling, falls over completely.
A 30-second blip becomes a 20-minute outage — caused by the health check.
```

**Follow-up to expect:** *"Should readiness fail if a non-critical dependency is down?"* → No. If the recommendation service is down but you can still take orders, stay ready and serve degraded. Reserve "not ready" for "I genuinely cannot serve a correct response."

📖 [Chapter 9 — Health checks: liveness vs readiness](../tutorial/09-resilience.md#health-checks--liveness-vs-readiness)

</details>

---

<details id="q21">
<summary><b>Q21 · What is fail-open versus fail-closed, and how do you choose?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

When a check cannot run, do you allow the operation or block it?

- **Fail open** — allow. Right when the check protects against something recoverable.
- **Fail closed** — block. Right when the check protects against harm you cannot undo.

**If they dig deeper**

The two case studies choose oppositely, on purpose:

| System | Check unavailable | Choice | Why |
|---|---|---|---|
| E-commerce | Inventory down | **Fail open** — accept the order | A rare oversell is an apology email. A failed checkout during a sale is lost revenue |
| Trading | Risk down | **Fail closed** — reject every order | An unchecked order is a regulatory incident and a position nobody authorised |

Same architecture, opposite answer, because the cost of being wrong is different.

**Follow-up to expect:** *"Who decides?"* → The business, explicitly, and it should be written down. An engineer choosing "allow the sale" alone at 5 p.m. is making a commercial decision without authority. Getting that agreement in writing is part of the design work.

📖 [Case study 4 — Decision 1](../case-studies/04-trading-app/README.md#decision-1--risk-is-synchronous-and-its-budget-is-8-ms)

</details>

---

<details id="q22">
<summary><b>Q22 · A call to an external API times out. Did it succeed?</b> &nbsp;·&nbsp; <code>Staff+</code> &nbsp;⭐ <i>the maturity question</i></summary>

**The 30-second answer**

**You do not know.** That is the entire point, and the answer is to model it.

Treating a timeout as failure is how a customer's card gets charged for an order you then cancel. Treating it as success is how you ship goods that were never paid for.

**If they dig deeper**

`Unknown` must be a first-class state:

```csharp
catch (TaskCanceledException) when (!ct.IsCancellationRequested)
{
    // A TIMEOUT, not a cancellation. The charge MAY have succeeded.
    return ChargeResult.Unknown("retry with the same idempotency key to learn the truth");
}
```

Then resolve it — do not guess:

- **Retry with the same idempotency key.** The provider returns the original result if it exists.
- **Query by your reference** to ask what actually happened.
- **Escalate to a human** if it stays ambiguous.

Both the banking and trading case studies have this state, and both refuse to auto-retry an ambiguous money operation.

**Follow-up to expect:** *"Why not just retry automatically?"* → For an idempotent call with a key, you can and should. For an operation without one — an order to an exchange, a payment to another bank — a retry is a guess with money attached, and a duplicate position costs real money to unwind while the market moves.

📖 [Case study 2 — Decision 5](../case-studies/02-banking-payments/README.md#decision-5--never-auto-retry-an-ambiguous-payment)

</details>

---

<details id="q23">
<summary><b>Q23 · How do you stop a lost event from breaking things permanently?</b> &nbsp;·&nbsp; <code>Senior</code></summary>

**The 30-second answer**

A **sweeper**: a background job that finds work stuck past its deadline and resolves it.

Every async flow needs one, because events do get lost and the failure is silent — nothing errors, work simply stops moving.

**If they dig deeper**

The e-commerce example: a `PaymentFailed` event is lost, so the stock reservation is never released. Without a sweeper, that stock is off sale forever, and no alert fires.

```csharp
var stale = await db.Reservations
    .Where(r => !r.IsReleased && !r.IsConfirmed && r.ExpiresAtUtc < DateTime.UtcNow)
    .ToListAsync(ct);

foreach (var r in stale)
{
    r.Release();
    log.LogWarning("Reservation {OrderId} expired and was swept", r.OrderId);
}
```

**The sweep count is a health metric.** In a healthy system it is zero. A rising number means events are being lost upstream, and you want to learn that from a counter rather than from a customer.

**Follow-up to expect:** *"Where else does this pattern appear?"* → Saga timeouts, the trading reservation ledger, and expiring inbox and outbox rows. It is the same idea each time: anything with a deadline needs something that notices the deadline passing.

📖 [Case study 1 — Decision 2](../case-studies/01-ecommerce/README.md#decision-2--reserve-stock-before-payment)

</details>

---

<details id="q24">
<summary><b>Q24 · How do you prove your data is still correct?</b> &nbsp;·&nbsp; <code>Staff+</code></summary>

**The 30-second answer**

A reconciliation job that runs on a schedule and checks the invariant you rely on — in production, not in CI.

A test proves the code was correct when you wrote it. Reconciliation proves the **data** is correct right now.

**If they dig deeper**

Bugs, bad migrations, manual database edits, and partial failures all corrupt data in ways no unit test can see. The banking case study checks four things nightly:

1. Global debits equal credits, per currency.
2. Every individual journal balances.
3. Cached balances match balances derived from entries.
4. No entry has been modified after it was written.

And it keeps every report, because "when did this start?" is always the first question after a discrepancy is found.

**Follow-up to expect:** *"What if reconciliation finds a problem?"* → Alert immediately, and know in advance whether you stop the affected flow. For a ledger, an unbalanced book means freeze postings and investigate. Deciding that during the incident is too late.

📖 [Case study 2 — `DailyReconciliationJob.cs`](../case-studies/02-banking-payments/src/Banking.Ledger/Jobs/DailyReconciliationJob.cs)

</details>

---

← [Boundaries and edges](03-boundaries-and-edges.md) · [Interview index](README.md) · Next: [Observability →](05-observability.md)
