# Chapter 7 — Sagas: Transactions Across Services

← [Chapter 6](06-boundaries-and-data.md) · [Tutorial index](README.md) · Next: [Chapter 8 — Outbox and idempotency](08-outbox-and-idempotency.md)

---

## The story so far

The databases are split ([chapter 6](06-boundaries-and-data.md)). Then the warehouse manager calls.

> *"The system says we have 0 wireless mice. I am looking at 340 of them."*

You investigate. Priya ordered 2 mice last week. `Inventory` reserved them. Her card declined. `Ordering` marked the order failed and emailed her.

**Nobody told `Inventory`.** Those 2 mice are still reserved — not on sale, not sold. Multiply by every declined card for six weeks and 340 units have quietly vanished from the catalogue.

This chapter is about finishing what you start, across services that cannot share a transaction.

---

## In one line

You cannot roll back across services. You can only apologise correctly.

---

## The words you need

| Word | Plain meaning |
|---|---|
| **Transaction** | A group of changes that all happen, or none happen. |
| **ACID** | The guarantees one database gives a transaction: Atomic, Consistent, Isolated, Durable. |
| **Two-phase commit (2PC)** | A protocol to make several databases commit together. Ask everyone "ready?", then tell everyone "commit". |
| **Saga** | A sequence of local transactions, where each step has an **undo** step. |
| **Compensating action** | The undo. Not a rollback — a new action that reverses the effect of a previous one. |
| **Choreography** | No coordinator. Each service reacts to events from the others. |
| **Orchestration** | One coordinator drives the flow and tells each service what to do. |
| **Pivot step** | The step after which you can no longer cancel, only go forward. |
| **State machine** | An object that is in exactly one named state and moves between states on defined events. |

---

## The problem

In the old monolith, this was one transaction and it was never wrong:

```sql
BEGIN TRANSACTION;
  UPDATE stock   SET available = available - 2 WHERE sku = 'SKU-88';
  INSERT INTO payments (order_id, amount) VALUES ('o-123', 49.98);
  UPDATE orders  SET status = 'Confirmed'      WHERE id = 'o-123';
COMMIT;   -- all three, or none. The database guaranteed it.
```

Now it is three services with three databases. **That single `COMMIT` is gone.** You have three separate commits, and anything can happen between them:

```
Inventory commits.  ✓   2 mice reserved
Payments commits.   ✓   card DECLINED, payment row written as failed
Ordering commits.   ✓   order marked failed

Nobody ran the undo for step 1.       ← the 340 missing mice
```

---

## Why two-phase commit does not fit

2PC exists and does solve this. It is also almost never right for microservices:

| Problem | Effect |
|---|---|
| **The coordinator is a single point of failure** | If it dies between "prepare" and "commit", every participant holds locks and waits. Forever |
| **Locks are held across the network** | A stock row locked for the whole protocol — hundreds of milliseconds. Throughput collapses |
| **Every participant must support it** | Acme Pay's REST API does not. Neither does your broker |
| **It trades availability for consistency** | If one of five participants is unreachable, nothing commits |

The saga trade is the opposite: **stay available, accept a short window of inconsistency, and clean up explicitly.**

---

## The saga idea

Break the transaction into local steps. Give each step an undo:

| Step | Do | Undo (compensate) |
|---|---|---|
| 1 | Reserve 2 × SKU-88 | Release the reservation |
| 2 | Charge ₹49.98 | Refund ₹49.98 |
| 3 | Confirm order | Cancel order |
| 4 | Ship parcel | *(cannot undo — see pivot step)* |

If step 2 fails, run step 1's undo. If step 3 fails, undo 2 then 1.

**The key insight:** "refund the card" is not a rollback. The charge really happened. It is on Priya's statement. The refund is a **second, real event** that makes things right. She may even see both lines on her bank statement — and that is correct behaviour, not a bug.

> This is why the chapter title says *apologise correctly*. You cannot make it as if nothing happened. You can only make the outcome fair.

---

## Two ways to run a saga

> **Diagram: D7 — Choreography vs orchestration**
> [`images/svg/d7-saga.svg`](../images/svg/d7-saga.svg) · [Mermaid source](../diagrams/README.md#d7--saga-choreography-vs-orchestration)

![Saga: choreography vs orchestration](../images/svg/d7-saga.svg)

---

## Choreography — nobody is in charge

Each service listens for events and reacts. There is no coordinator.

**Priya's declined card, replayed with choreography:**

```
Ordering    publishes OrderPlaced
Inventory   hears it → reserves 2 × SKU-88 → publishes StockReserved
Payments    hears it → charges card → DECLINED → publishes PaymentFailed
Inventory   hears PaymentFailed → releases 2 × SKU-88 → publishes StockReleased   ← the fix
Ordering    hears PaymentFailed → cancels order
```

That fourth line is the one that was missing. The mice come back.

### Code

```csharp
// Inventory/Consumers/OrderPlacedConsumer.cs — the "do" step
public sealed class OrderPlacedConsumer(InventoryDbContext db) : IConsumer<OrderPlaced>
{
    public async Task Consume(ConsumeContext<OrderPlaced> ctx)
    {
        var m = ctx.Message;

        if (await db.Reservations.AnyAsync(r => r.OrderId == m.OrderId, ctx.CancellationToken))
            return;                                     // already handled (chapter 8)

        var ok = await db.TryReserveAsync(m.Lines, m.OrderId, ctx.CancellationToken);

        db.OutboxMessages.Add(OutboxMessage.From(ok
            ? new StockReserved(m.OrderId, m.Lines)
            : new StockRejected(m.OrderId, "insufficient stock")));

        await db.SaveChangesAsync(ctx.CancellationToken);
    }
}
```

```csharp
// Inventory/Consumers/PaymentFailedConsumer.cs — the "undo" step
// Inventory does not know WHY payment failed, and does not care.
// It knows one thing: if payment failed, its reservation must be released.
public sealed class PaymentFailedConsumer(InventoryDbContext db) : IConsumer<PaymentFailed>
{
    public async Task Consume(ConsumeContext<PaymentFailed> ctx)
    {
        var reservation = await db.Reservations
            .FirstOrDefaultAsync(r => r.OrderId == ctx.Message.OrderId, ctx.CancellationToken);

        if (reservation is null || reservation.IsReleased)
            return;                                     // nothing to undo, or already undone

        reservation.Release();
        db.OutboxMessages.Add(OutboxMessage.From(new StockReleased(reservation.OrderId)));

        await db.SaveChangesAsync(ctx.CancellationToken);
    }
}
```

### Choreography — the honest assessment

**Good:**
- No extra component to build, deploy, or keep alive.
- Very loose coupling — each service only knows about events.
- Adding a step means adding a subscriber. No existing code changes.

**Bad:**
- **The flow exists nowhere.** To understand checkout you must read four services and assemble the sequence in your head. There is no file you can point a new joiner at.
- **Cycles are easy to create by accident.** A reacts to B's event; B reacts to A's. Now you have an infinite loop in production.
- **"Where is order `o-123` stuck?"** has no easy answer. You search logs across four services.
- **Testing the whole flow** requires running everything.

**Use choreography when:** 2–4 steps, the flow rarely changes, each step is genuinely independent.

**Stop using it when:** you reach roughly 5+ steps, or someone draws the flow on a whiteboard and gets it wrong. That is the signal.

---

## Orchestration — one coordinator owns the flow

One component — the saga, or process manager — holds the state and decides the next step.

```
OrderSaga: send ReserveStock  → wait
Inventory: StockReserved      → OrderSaga: send ChargePayment → wait
Payments:  PaymentFailed      → OrderSaga: decides to compensate
OrderSaga: send ReleaseStock  → wait
Inventory: StockReleased      → OrderSaga: order → Cancelled. Done.
```

### Code — the saga as an explicit state machine

```csharp
// Ordering/Sagas/OrderSagaState.cs
public sealed class OrderSagaState : SagaStateMachineInstance
{
    public Guid   CorrelationId { get; set; }        // = OrderId. One saga per order.
    public string CurrentState  { get; set; } = "";

    public Guid     CustomerId   { get; set; }
    public decimal  Total        { get; set; }
    public DateTime StartedAtUtc { get; set; }

    // What has actually happened. This is what makes compensation correct:
    // never undo a step that never ran.
    public bool    StockReserved  { get; set; }
    public bool    PaymentCharged { get; set; }
    public string? TransactionId  { get; set; }
    public string? FailureReason  { get; set; }

    public int Version { get; set; }                 // optimistic concurrency
}
```

```csharp
// Ordering/Sagas/OrderSaga.cs
// The whole business flow, in ONE readable, unit-testable file.
public sealed class OrderSaga : MassTransitStateMachine<OrderSagaState>
{
    public State AwaitingStock   { get; private set; } = null!;
    public State AwaitingPayment { get; private set; } = null!;
    public State Compensating    { get; private set; } = null!;
    public State Confirmed       { get; private set; } = null!;
    public State Cancelled       { get; private set; } = null!;

    public Event<OrderPlaced>       OrderPlaced      { get; private set; } = null!;
    public Event<StockReserved>     StockReserved    { get; private set; } = null!;
    public Event<StockRejected>     StockRejected    { get; private set; } = null!;
    public Event<PaymentSucceeded>  PaymentSucceeded { get; private set; } = null!;
    public Event<PaymentFailed>     PaymentFailed    { get; private set; } = null!;
    public Event<StockReleased>     StockReleased    { get; private set; } = null!;

    public OrderSaga()
    {
        InstanceState(x => x.CurrentState);

        Event(() => OrderPlaced,      x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockReserved,    x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockRejected,    x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentSucceeded, x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => PaymentFailed,    x => x.CorrelateById(m => m.Message.OrderId));
        Event(() => StockReleased,    x => x.CorrelateById(m => m.Message.OrderId));

        Initially(
            When(OrderPlaced)
                .Then(c =>
                {
                    c.Saga.CustomerId   = c.Message.CustomerId;
                    c.Saga.Total        = c.Message.Total;
                    c.Saga.StartedAtUtc = DateTime.UtcNow;
                })
                .Send(c => new ReserveStock(c.Saga.CorrelationId, c.Message.Lines))
                .TransitionTo(AwaitingStock));

        During(AwaitingStock,
            When(StockReserved)
                .Then(c => c.Saga.StockReserved = true)
                .Send(c => new ChargePayment(c.Saga.CorrelationId, c.Saga.Total))
                .TransitionTo(AwaitingPayment),

            // Nothing to compensate — stock was never reserved. Straight to cancelled.
            When(StockRejected)
                .Then(c => c.Saga.FailureReason = c.Message.Reason)
                .Publish(c => new OrderCancelled(c.Saga.CorrelationId, c.Message.Reason))
                .TransitionTo(Cancelled)
                .Finalize());

        During(AwaitingPayment,
            When(PaymentSucceeded)
                .Then(c =>
                {
                    c.Saga.PaymentCharged = true;
                    c.Saga.TransactionId  = c.Message.TransactionId;
                })
                .Publish(c => new OrderConfirmed(c.Saga.CorrelationId))
                .TransitionTo(Confirmed)
                .Finalize(),

            // Priya's card declined → compensate, but ONLY what actually happened.
            When(PaymentFailed)
                .Then(c => c.Saga.FailureReason = c.Message.Reason)
                .If(c => c.Saga.StockReserved,
                    b => b.Send(c => new ReleaseStock(c.Saga.CorrelationId)))
                .TransitionTo(Compensating));

        During(Compensating,
            When(StockReleased)
                .Then(c => c.Saga.StockReserved = false)
                .Publish(c => new OrderCancelled(c.Saga.CorrelationId, c.Saga.FailureReason!))
                .TransitionTo(Cancelled)
                .Finalize());

        SetCompletedWhenFinalized();     // remove finished sagas so the table stays small
    }
}
```

Read that once and you know the entire order process. **That is the whole value proposition.**

And the warehouse question becomes a single query:

```sql
SELECT CurrentState FROM OrderSagaState WHERE CorrelationId = 'o-123';
-- 'Compensating'  → we know exactly where it is
```

### Orchestration — the honest assessment

**Good:**
- **The flow is one readable file.** New joiners understand the business process in ten minutes.
- **It is unit-testable** without infrastructure — feed it events, assert the state.
- **"Where is order `o-123`?"** is one database query.
- **Compensation is explicit**, and can check what actually happened before undoing it.
- **Timeouts are natural** to express.

**Bad:**
- **One more component** to build, deploy, and monitor.
- **The coordinator can itself fail** mid-flow, so its state must be persisted after every step.
- **It can drift into a god object** if you let it hold business rules.
- Services are slightly more coupled — they accept commands from a known coordinator.

---

## Choosing between them

| Question | Choreography | Orchestration |
|---|---|---|
| How many steps? | 2–4 | 5+ |
| Can you draw the flow from memory? | Must be yes | Not needed |
| Do you need "where is it stuck?" | Hard | One query |
| Does the flow change often? | Painful | Easy — one file |
| Extra component to run? | No | Yes |
| Compensation complexity | Each service decides alone | Coordinator decides with full context |
| Risk | Hidden flow, accidental cycles | Coordinator becomes a god object |

**What the store does:** choreography, for now. Four steps, stable flow, nothing to build.

**What would change their mind:** the fraud team wants a check between reservation and payment, and the loyalty team wants points awarded after confirmation. That is six steps. At six steps, nobody can hold the flow in their head — and that is the moment to switch.

> **A practical default:** start with choreography. Move to orchestration the first time someone asks *"what actually happens after an order is placed?"* and three people give three different answers.

---

## Compensating actions in practice

This is where most saga implementations are subtly wrong.

### Rule 1 — Compensation must be idempotent

The compensating message can arrive twice, like any other message.

```csharp
public async Task ReleaseAsync(Guid orderId, CancellationToken ct)
{
    var r = await db.Reservations.FirstOrDefaultAsync(x => x.OrderId == orderId, ct);

    if (r is null)      return;   // never reserved — nothing to do
    if (r.IsReleased)   return;   // already released — do NOT release twice,
                                  // or you credit stock you never took

    r.Release();
    await db.SaveChangesAsync(ct);
}
```

**Without those two guards, a duplicate `ReleaseStock` silently inflates your inventory.** You now have the *opposite* of the warehouse problem: the system says 342 mice when there are 340. That is a very expensive bug to find, because nothing errors.

> A "do" step that runs twice usually fails loudly — a duplicate key, a rejected charge. An **"undo" that runs twice succeeds silently.** That asymmetry is why compensation deserves more care than the forward path.

### Rule 2 — Compensation can fail too

The refund API is down. Now what? You cannot compensate the compensation.

Answer: **retry forever, with backoff, and alert a human if it does not succeed.**

```csharp
cfg.ReceiveEndpoint("payments-refund", e =>
{
    // Compensation is not allowed to give up quietly. A failed refund is a customer
    // who was charged for nothing, and that becomes a legal problem, not a bug.
    e.UseMessageRetry(r => r.Exponential(
        retryLimit:    20,
        minInterval:   TimeSpan.FromSeconds(1),
        maxInterval:   TimeSpan.FromMinutes(30),
        intervalDelta: TimeSpan.FromSeconds(5)));

    e.ConfigureConsumer<RefundPaymentConsumer>(ctx);
    // Still failing after all that? → DLQ + page a human. Never silently drop it.
});
```

### Rule 3 — Some steps cannot be undone (the pivot step)

You cannot un-send Priya's email. You cannot un-ship a parcel that is on a BlueDart van.

The **pivot step** is the point of no return. After it, the saga must go forward, not backward.

```
Reserve stock   ← can undo
Charge card     ← can undo (refund)
────────── PIVOT: hand the parcel to BlueDart ──────────
Send email      ← cannot undo, but harmless
Deliver         ← must go forward
```

Design so irreversible steps come **last**, after everything that can fail has already succeeded. If a step cannot be undone and it sits in the middle of your saga, **that is a design bug** — reorder the steps.

### Rule 4 — Add a timeout for every wait

The most common production saga failure is not a failed step. It is a step whose reply **never arrives**. Without a timeout, that saga sits in `AwaitingPayment` forever and nobody notices.

```csharp
// A saga must never wait forever. Ever.
Schedule(() => PaymentTimeout, x => x.PaymentTimeoutTokenId, s =>
{
    s.Delay    = TimeSpan.FromMinutes(5);
    s.Received = r => r.CorrelateById(m => m.Message.OrderId);
});

During(AwaitingPayment,
    When(PaymentTimeout.Received)
        .Then(c => c.Saga.FailureReason = "payment timed out after 5 minutes")
        .If(c => c.Saga.StockReserved,
            b => b.Send(c => new ReleaseStock(c.Saga.CorrelationId)))
        .TransitionTo(Compensating));
```

**And in a choreographed system you still need this**, just implemented differently — as a sweeper job:

```csharp
// Inventory/Services/ReservationSweeper.cs — the safety net for a lost event
var stale = await db.Reservations
    .Where(r => !r.IsReleased && !r.IsConfirmed && r.ExpiresAtUtc < DateTime.UtcNow)
    .Take(500)
    .ToListAsync(ct);

foreach (var r in stale)
{
    r.Release();
    log.LogWarning("Reservation {OrderId} expired and was swept", r.OrderId);
}
```

**Every async flow needs a sweeper like this.** Events get lost. The sweep count is a health metric: in a healthy system it is zero, and a rising number means events are being lost upstream.

---

## Sharp edges

**Edge 1 — There is no isolation.** ACID's "I" is gone. Halfway through a saga, other customers can see intermediate state: stock reserved but order not confirmed. Design for it with explicit states rather than hoping nobody looks.

**Edge 2 — Semantic locks.** Sometimes you need to stop others touching a half-done thing. Mark the record: `Order.Status = Processing`, and refuse edits in that state. This is a lock you implement in your domain, and you must handle it never being released (see rule 4).

**Edge 3 — Saga state must be persisted after every step.** If the coordinator crashes between "payment charged" and "saving that fact", it will re-charge on restart. Persist the state in the same transaction that publishes the next command — which is the outbox pattern, and the next chapter.

**Edge 4 — Concurrent messages for the same saga.** `StockReserved` and `PaymentTimeout` can arrive at the same instant, at two instances. Both load the saga, both decide, both save. One silently overwrites the other. Fix: optimistic concurrency (the `Version` column) plus retry on conflict. Do not assume it is on by default.

**Edge 5 — The saga table grows forever.** Finalise completed sagas or archive them. A saga table with 40 million rows makes every correlation lookup slow, which slows every message.

**Edge 6 — Do not put business rules in the saga.** *"If the customer is Gold tier, skip the credit check"* belongs in the credit-check service, not the coordinator. The saga owns **sequence and compensation**. The moment it owns policy, every team must change the saga to ship anything, and you have a new bottleneck.

---

## When to use a saga at all

**Use one when:** a business operation spans several services and partial completion is unacceptable. Order fulfilment, account opening, trade settlement, booking a trip.

**Do not use one when:**

| Situation | Do this instead |
|---|---|
| All steps are in one service | Use a database transaction. Simpler and stronger |
| Steps are genuinely independent | Just publish an event. No saga needed |
| Only one step can fail, at the end | Handle that one failure directly |
| You need real ACID across services | Reconsider the boundary |

That last row matters. **"We need a distributed transaction here" is often evidence that you drew the boundary in the wrong place.** Merging two services is a legitimate and often better answer than building a saga. [Case study 2](../case-studies/02-banking-payments/README.md#why-the-ledger-posting-is-not-a-saga) shows exactly this: a bank's debit and credit stay in **one** transaction in **one** service, with the saga around it, never through it.

---

## Try it yourself

**Build it.** The order flow: reserve stock → charge payment → confirm. Once with choreography, once with orchestration. Compare the two codebases for readability.

**Now break it:**

1. Make payment fail. Confirm stock is released and the order ends `Cancelled`. Query the saga state to prove it. *This is the 340 missing mice, fixed.*
2. Make payment fail **and** make the release-stock handler throw. Watch the saga sit in `Compensating`. Now add retries — this is edge/rule 2 in real life.
3. Deliver `PaymentFailed` **twice**. If stock is released twice, you have the phantom-inventory bug. Add the `IsReleased` guard and repeat.
4. Kill the orchestrator right after `StockReserved`. Restart. Does it resume, or is the order stuck forever? If stuck, your state is not persisted correctly.
5. Never send `PaymentSucceeded` at all. Confirm the timeout fires and compensation runs. **If nothing happens, you have the most common real-world saga bug.**
6. Send `StockReserved` and `PaymentTimeout` simultaneously to two orchestrator instances. Check for a lost update. Add optimistic concurrency and repeat.
7. Add a 6th step to the choreographed version, then to the orchestrated version. Time yourself for both. **That difference is the case for orchestration.**

---

## What is still broken

The mice come back. The warehouse manager stops calling.

Then, during a routine check, someone runs a query nobody has run before:

```sql
SELECT COUNT(*) FROM orders
WHERE status = 'Pending' AND placed_at < NOW() - INTERVAL '1 day';
```

**47 rows.**

Forty-seven orders, placed over the last three weeks, still sitting at `Pending`. Never reserved. Never charged. Never cancelled. Never emailed about.

You check the logs for one of them. There is no error. There is no exception. There is no `OrderPlaced` event in the broker at all. The order exists in the database and **the event was never published**.

Nothing in your system is broken. Nothing raised an alert. And 47 customers are waiting for orders that will never move.

The next chapter is the bug that causes this — and it is almost certainly in your production system right now.

---

← [Chapter 6](06-boundaries-and-data.md) · [Tutorial index](README.md) · Next: [Chapter 8 — Outbox and idempotency](08-outbox-and-idempotency.md)
