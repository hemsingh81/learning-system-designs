# Case Study 1 — E-commerce Checkout

← [All case studies](../README.md) · Next: [Banking and payments](../02-banking-payments/)

---

## The business

An online store. Customers browse products, add them to a basket, and check out. Behind checkout: stock must be reserved, a card must be charged, an email must go out, a warehouse must be told, and analytics must be updated.

Traffic is **spiky**. A normal Tuesday is 50 orders a minute. A sale is 5,000 orders a minute, starting the second the campaign email lands.

---

## The constraint

> **Checkout must stay up during a traffic spike. A dependency failing must not fail a sale.**

Everything below follows from that sentence. When you are choosing between "correct" and "keeps selling", this business chooses **keeps selling** — and then reconciles.

That is a real decision with real costs. An oversold item means an apology email and a refund. A failed checkout during a campaign means lost revenue and a customer who buys elsewhere. The business has decided the apology is cheaper.

**Banking makes the opposite choice.** Compare with [case study 2](../02-banking-payments/).

---

## The services

| Service | Owns | Never touches |
|---|---|---|
| **Catalog** | Products, prices, descriptions, images | Stock levels |
| **Inventory** | Stock levels, reservations | Prices |
| **Ordering** | Orders, order lines, order status | Payments, stock |
| **Payments** | Payment attempts, transaction IDs, refunds | Orders |
| **Notifications** | Email and push delivery, templates | Anything else |
| **Shipping** | Parcels, carriers, tracking numbers | Orders |

### The ownership table

| Entity | Owner | Readers | How they read it |
|---|---|---|---|
| Product | Catalog | Ordering, BFF | `GET /products`, `ProductChanged` event |
| StockLevel | Inventory | BFF (display only) | `GET /stock`, `StockChanged` event |
| Reservation | Inventory | nobody | — |
| Order | Ordering | Support, Analytics, Shipping | `OrderPlaced`/`OrderConfirmed` events |
| Payment | Payments | Ordering (via events), Finance | `PaymentSucceeded`/`PaymentFailed` |
| Parcel | Shipping | Ordering, BFF | `ParcelShipped` event |

**Every entity has exactly one writer.** That is [chapter 6](../../tutorial/06-boundaries-and-data.md), and it is the first thing to get right.

---

## The communication map

```
Browser ──► Gateway ──► Web BFF ──┬─► Catalog     (sync, cached)
                                  ├─► Inventory   (sync, fallback)
                                  └─► Ordering    (sync, no fallback)

Ordering ──► outbox ──► Broker ──┬─► Inventory       (reserve stock)
                                 ├─► Payments        (charge card)
                                 ├─► Notifications   (email + push)
                                 └─► Analytics       (record)

Notifications ──► SignalR ──► Browser   (live status update)
```

### Every decision, with the reason

| Call | Sync or async | Why |
|---|---|---|
| BFF → Catalog | **Sync** | Cannot render a page without products. Cached hard; falls back to cache on failure |
| BFF → Inventory | **Sync** | "In stock" badge. Falls back to hiding the badge — never fails the page |
| BFF → Ordering (place order) | **Sync** | The user must get an order ID. But it returns `202`, not `201` |
| Ordering → Inventory | **Async** | The reservation can happen 200 ms later. Never fail a sale on it |
| Ordering → Payments | **Async** | **The big one.** See below |
| Ordering → Notifications | **Async** | Nobody waits for SMTP |
| Notifications → Browser | **Push** | Closes the eventual-consistency gap |

### Why payment is asynchronous — the decision that defines this system

The obvious design charges the card inside the checkout request:

```
POST /orders → reserve stock → charge card (2-4s) → 201 Created
```

Under a spike, this is exactly the 2 a.m. incident from [chapter 2](../../tutorial/02-synchronous.md). The payment provider slows down, threads pile up waiting, checkout dies, and retries finish the job.

So this system accepts the order first and charges afterwards:

```
POST /orders → write order + outbox → 202 Accepted (40ms)
                     ↓ async
             reserve stock → charge card → confirm or cancel
                     ↓
             push the result to the browser
```

**What you gain:** checkout responds in 40 ms instead of 4 s. The payment provider can be down for a minute and no order is lost. The spike is absorbed by the queue.

**What you pay:**

- The user sees "Processing" for a second or two. The UI must handle it honestly.
- Some orders will be cancelled *after* the customer saw a success page. That needs a clear email.
- Stock is reserved before payment clears, so a failed payment must release it — that is the saga.

This trade is right for retail, and wrong for banking. It is the whole reason both case studies exist.

---

## Walkthrough: one order, end to end

```
t=0ms      Browser        POST /api/orders  (Idempotency-Key: a1b2c3)
t=2ms      Gateway        validate JWT, rate limit, mint correlation ID
t=5ms      Ordering       check idempotency key → not seen before
t=8ms      Ordering       create Order (status = Pending)
t=12ms     Ordering       INSERT order + INSERT outbox row  ← ONE transaction
t=15ms     Ordering       202 Accepted { orderId, status: "Pending" }
t=18ms     Browser        show "Processing your order…"

t=180ms    Relay          publish OrderPlaced to the broker
t=190ms    Inventory      consume → reserve 2 × SKU-88 → publish StockReserved
t=195ms    Notifications  consume → send "we got your order" email
t=200ms    Analytics      consume → record the funnel event

t=210ms    Payments       consume StockReserved → charge the card
t=1,150ms  Payments       gateway replies OK → publish PaymentSucceeded

t=1,160ms  Ordering       consume → status = Confirmed → publish OrderConfirmed
t=1,170ms  Shipping       consume → create parcel → publish ParcelCreated
t=1,175ms  Notifications  consume → SignalR push to the browser
t=1,180ms  Browser        page updates itself to "Order confirmed ✓"
```

The customer waited **15 ms** for a response and saw the confirmation **1.2 seconds** later without refreshing.

### The unhappy path

```
t=1,150ms  Payments       card declined → publish PaymentFailed
t=1,160ms  Inventory      consume PaymentFailed → release the reservation
t=1,160ms  Ordering       consume PaymentFailed → status = PaymentFailed
t=1,170ms  Notifications  consume → SignalR push + email "payment did not go through"
t=1,180ms  Browser        "Payment failed — please try another card" + a retry button
```

Stock is back on sale within 20 ms of the decline. Nobody had to write a rollback.

---

## Key decisions

### Decision 1 — Choreography, not orchestration

Four steps: reserve → charge → confirm → ship. Each service reacts to events; there is no coordinator.

**Why:** the flow is short and stable, and choreography costs nothing to build.

**The cost, stated honestly:** the flow is not written down anywhere. To understand checkout you read four services. The day someone asks "what happens between placing and shipping?" and gets three different answers, move to orchestration ([chapter 7](../../tutorial/07-saga.md)).

**The trigger to switch:** a fifth or sixth step. Fraud checks and loyalty points are what usually push this over the line.

### Decision 2 — Reserve stock before payment

**Why:** selling something you do not have is worse than briefly holding stock you might not sell.

**The cost:** a reservation must expire. If `PaymentFailed` is lost, stock is held forever. So reservations have a TTL and a sweeper releases stale ones:

```csharp
// Inventory/Services/ReservationSweeper.cs — the safety net for a lost event.
// Without this, one dropped message silently removes stock from sale forever.
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

**Every async flow needs a sweeper like this.** Events get lost. Plan for it.

### Decision 3 — Allow a small oversell rather than fail checkout

When `Inventory` is unreachable, the BFF hides the stock badge and the order is still accepted. Stock is verified asynchronously, and a rare oversell becomes an apology email.

**Why:** during a sale, failing checkout costs far more than the occasional refund.

**The cost:** real customer disappointment, occasionally. This must be a written, agreed business decision — not something an engineer chose alone at 5 p.m.

### Decision 4 — `202 Accepted`, and the UI never lies

The API says "I have taken responsibility for this", not "this is done". The UI shows `Processing`, and SignalR updates it.

**Why:** it is true, and eventual consistency you hide becomes a support ticket ([chapter 3](../../tutorial/03-asynchronous.md)).

### Decision 5 — A queue, not Kafka

**Why:** nobody replays orders. Question 2 of [the framework](../../tutorial/11-decision-framework.md) is a clear no. RabbitMQ or Azure Service Bus gives per-message retry and DLQ, which is exactly what this flow needs, without cluster operations.

**When that changes:** if analytics wants to rebuild a funnel from six months of history, add Kafka *for analytics only*. Do not migrate the transactional flow.

---

## Folder structure

`src/` sits alongside a real [`docker-compose.yml`](docker-compose.yml) — RabbitMQ, SQL Server, Jaeger, and a WireMock stand-in for the payment provider. Start it and run your own version of the services below against working infrastructure.

```
src/
├── Ecommerce.Contracts/                  ← the ONLY shared project. Events + commands only.
│   ├── Events/
│   │   ├── OrderEvents.cs
│   │   ├── InventoryEvents.cs
│   │   └── PaymentEvents.cs
│   └── Commands/
│       └── ShippingCommands.cs
│
├── Ecommerce.Ordering/
│   ├── Api/                              ← HTTP surface. Thin. No business rules.
│   │   └── OrdersEndpoints.cs
│   ├── Domain/                            ← business rules. No EF, no HTTP, no broker.
│   │   ├── Order.cs
│   │   ├── OrderLine.cs
│   │   └── OrderStatus.cs
│   ├── Consumers/                         ← reacts to other services' events
│   │   ├── PaymentSucceededConsumer.cs
│   │   └── PaymentFailedConsumer.cs
│   ├── Infrastructure/
│   │   ├── OrderingDbContext.cs
│   │   ├── Configurations/
│   │   └── Outbox/                        ← OutboxMessage + relay (see chapter 8)
│   └── Program.cs
│
├── Ecommerce.Inventory/
│   ├── Domain/          Stock.cs, Reservation.cs
│   ├── Consumers/       OrderPlacedConsumer.cs, PaymentFailedConsumer.cs
│   ├── Services/        ReservationSweeper.cs
│   └── Infrastructure/
│
├── Ecommerce.Payments/
│   ├── Consumers/       StockReservedConsumer.cs
│   ├── Gateways/        IPaymentGateway.cs, AcmePspGateway.cs   ← ACL over the provider
│   └── Infrastructure/
│
├── Ecommerce.Notifications/
│   ├── Consumers/       OrderEventsConsumer.cs
│   ├── Hubs/            OrderHub.cs
│   └── Templates/
│
└── Ecommerce.Bff.Web/
    ├── Endpoints/       CheckoutEndpoints.cs, OrderDetailsEndpoint.cs
    └── Clients/         CatalogClient.cs, InventoryClient.cs, OrderingClient.cs
```

### Why this layout

**One project per service, never one project per layer.** A `Ecommerce.Domain` project shared by all services would recreate the monolith. Each service owns its own `Domain/` folder.

**`Contracts` is the only shared project**, and it contains *only* events and commands — no logic, no domain models, no helpers. This is the rule that keeps [chapter 6's edge 3](../../tutorial/06-boundaries-and-data.md) from happening.

**`Domain/` has no infrastructure references.** No `DbContext`, no `HttpClient`, no `IBus`. You should be able to unit test the whole of `Order.cs` with no mocks at all.

**`Consumers/` is a peer of `Api/`.** Both are entry points into the service — one over HTTP, one over the broker. Treating the broker as a second-class citizen in the folder structure leads to treating it that way in the code.

---

## The code

> New to these samples? Read [HOW-TO-READ-THE-CODE.md](../HOW-TO-READ-THE-CODE.md) first — it explains the file layout and lists the referenced types that are deliberately not included. **Files 1–6 of its reading order are all in this case study**, so this is the right place to start.

| File | Shows |
|---|---|
| [`Ecommerce.Contracts/Events/OrderEvents.cs`](src/Ecommerce.Contracts/Events/OrderEvents.cs) | Event design, versioning, past-tense naming |
| [`Ecommerce.Contracts/Events/InventoryEvents.cs`](src/Ecommerce.Contracts/Events/InventoryEvents.cs) | A negative-outcome event (`StockRejected`), and why a reservation carries its own expiry |
| [`Ecommerce.Ordering/Domain/Order.cs`](src/Ecommerce.Ordering/Domain/Order.cs) | A pure aggregate that raises its own events |
| [`Ecommerce.Ordering/Api/OrdersEndpoints.cs`](src/Ecommerce.Ordering/Api/OrdersEndpoints.cs) | Idempotency key, outbox write, `202 Accepted` |
| [`Ecommerce.Inventory/Consumers/OrderPlacedConsumer.cs`](src/Ecommerce.Inventory/Consumers/OrderPlacedConsumer.cs) | Idempotent reservation with a real race guard |
| [`Ecommerce.Inventory/Consumers/PaymentFailedConsumer.cs`](src/Ecommerce.Inventory/Consumers/PaymentFailedConsumer.cs) | Compensation that is safe to run twice |
| [`Ecommerce.Payments/Gateways/AcmePspGateway.cs`](src/Ecommerce.Payments/Gateways/AcmePspGateway.cs) | Idempotency keys against an external provider |
| [`Ecommerce.Notifications/Consumers/OrderEventsConsumer.cs`](src/Ecommerce.Notifications/Consumers/OrderEventsConsumer.cs) | Async → push bridge, closing the consistency gap |
| [`Ecommerce.Bff.Web/Endpoints/CheckoutEndpoints.cs`](src/Ecommerce.Bff.Web/Endpoints/CheckoutEndpoints.cs) | Parallel fan-out with per-dependency fallbacks |

---

## Failure modes

| What fails | What happens | Customer sees |
|---|---|---|
| **Catalog down** | BFF serves from cache | Slightly stale prices |
| **Inventory down** | Stock badge hidden; orders still accepted | No "In stock" label. Rare oversell later |
| **Ordering down** | Checkout fails | "We cannot take orders right now" — the honest one |
| **Payments down** | Orders queue up as `Pending` | "Processing" for longer; confirmed when it recovers |
| **Broker down** | Outbox fills; nothing lost | Orders accepted, everything downstream is delayed |
| **Notifications down** | No email or push | Order still confirmed; status visible on refresh |
| **Relay stuck** | Outbox grows; no events published | Everything stays `Pending` — **alert on this** |
| **PaymentFailed lost** | Reservation never released | Stock held until the sweeper reclaims it |

**Only one row fails the sale.** That is the constraint holding.

**The two rows to alert on hardest:** outbox pending count, and reservation sweeper activity. Both are silent failures — no error, no exception, just orders that quietly stop moving.

---

## Now break it

1. **Stop `Payments`.** Place 20 orders. All return `202`. Start it. Watch all 20 confirm. *This is what async bought you.*
2. **Stop the broker.** Place orders. They still succeed — the outbox absorbs them. Start it. Watch the relay drain. *This is what the outbox bought you.*
3. **Deliver `OrderPlaced` twice** to `Inventory`. If stock drops by 4 instead of 2, your idempotency is broken. Add the inbox check and repeat.
4. **Deliver `PaymentFailed` twice.** If stock goes *up* by 4, your compensation is not idempotent. This is the phantom-inventory bug, and it is very hard to spot in production.
5. **Drop `PaymentFailed` entirely.** Confirm the sweeper releases the reservation. If nothing happens, you have permanently removed stock from sale with one lost message.
6. **Kill `Ordering` between `SaveChangesAsync` and the relay's publish.** Restart. Confirm the event still goes out.
7. **Send the same `Idempotency-Key` twice.** Confirm you get one order and the same ID both times.
8. **Load test at 50× normal.** Watch queue depth grow and drain. Measure how long the backlog takes to clear — that number is your recovery time after a spike, and you should know it before the sale, not during it.
9. **Make the payment provider take 30 seconds.** Confirm checkout latency does not move at all. If it does, something is synchronous that should not be.

---

## What this case study teaches

- **Async is a business decision, not a technical one.** "Charge the card later" is a policy choice, and someone in the business must own it.
- **Choreography is fine until it is not.** Four steps: fine. Six: move to orchestration.
- **Every async flow needs a sweeper.** Events get lost. A timeout-and-reclaim job is not optional.
- **Compensation must be idempotent**, or you invent inventory that does not exist.
- **The UI is part of the architecture.** `202 Accepted` plus a push channel is what makes eventual consistency acceptable to a human.

---

← [All case studies](../README.md) · Next: [Banking and payments](../02-banking-payments/)
