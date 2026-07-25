# The Running Example — One Store, Eleven Chapters

[Tutorial index](README.md) · Next: [Chapter 1 — The three axes](01-three-axes.md)

---

## Why one example

Most tutorials teach each pattern with a fresh example. You learn the outbox with an order system, sagas with a travel booking, and resilience with a weather API. Every chapter you rebuild the context from scratch, and the patterns never connect.

This tutorial uses **one store, all the way through**.

Every chapter fixes a problem that the previous chapter's fix created. That is not a teaching trick — it is exactly how real systems evolve. You solve one thing, the solution creates a new failure mode, and you solve that.

By chapter 11 you will have walked the same system from a simple version that falls over at 2 a.m. to one that survives a hundredfold traffic spike.

---

## The store

An online shop that sells electronics. Small, growing, and about to have a very bad night.

### The people

| Who | Role |
|---|---|
| **Priya Sharma** | A customer. Buys a wireless mouse in chapter 2 and keeps buying things for the rest of the tutorial |
| **You** | Just joined the backend team |
| **The team** | Six engineers who split a monolith last year and are now finding out what that cost |

### The services

Six of them. Each owns its own data.

| Service | Owns | Job |
|---|---|---|
| **Catalog** | Products, prices, descriptions, images | What is for sale |
| **Inventory** | Stock levels, reservations | How many are left |
| **Ordering** | Orders, order lines, order status | What people bought |
| **Payments** | Payment attempts, transaction IDs, refunds | Taking the money |
| **Notifications** | Email, SMS, push delivery | Telling the customer |
| **Shipping** | Parcels, carriers, tracking numbers | Getting it there |

### The numbers

These stay the same in every chapter, so you can always reason about scale.

| Measure | Value |
|---|---|
| Normal traffic | **50 orders per minute** |
| Sale peak | **5,000 orders per minute** (100× spike, arriving the second a campaign email lands) |
| Inventory stock lookup | 12 ms |
| Catalog product lookup | 25 ms |
| Payment provider (Acme Pay), normal | 800 ms |
| Payment provider, under load | **4 seconds** ← this number causes chapter 2's disaster |
| Database write | 8 ms |

### The order we follow

Priya's order appears in nearly every chapter. When you see it, it is always the same order:

| Field | Value |
|---|---|
| Order ID | `o-123` |
| Customer | Priya Sharma (`c-77`) |
| Item | `SKU-88` — Wireless Mouse |
| Quantity | 2 |
| Unit price | ₹24.99 |
| **Total** | **₹49.98** |

---

## The story arc

Each chapter has a problem, a fix, and a new problem the fix created.

| Ch | The problem | The fix | What the fix broke |
|---|---|---|---|
| [1](01-three-axes.md) | Nobody can describe how the store actually works | Draw the map: three axes | Nothing yet — you now see the risks |
| [2](02-synchronous.md) | **The 2 a.m. incident.** Checkout dies during the sale | *(diagnosed, not fixed)* | Understanding *why* it died |
| [3](03-asynchronous.md) | Checkout waits 4 s for payment | Accept the order, pay in the background. 4 s → **40 ms** | Priya's card gets charged twice. She can't see her order |
| [4](04-choosing-a-broker.md) | The team argues Kafka vs RabbitMQ for a week | Answer one question and decide in ten minutes | Nothing — but you now run a broker |
| [5](05-gateway-and-bff.md) | The new mobile app makes 6 calls per screen and drains battery | One front door, one backend per client | Teams start stepping on each other's data |
| [6](06-boundaries-and-data.md) | Inventory adds a column. Ordering breaks. Nobody knows why | Database-per-service, one writer per entity | Payment fails after stock is reserved — who cleans up? |
| [7](07-saga.md) | Priya's card declines. Her 2 mice stay reserved forever | Sagas and compensation | Some orders never publish an event at all |
| [8](08-outbox-and-idempotency.md) | **47 orders stuck at `Pending`.** No errors anywhere | The transactional outbox | Duplicates are now normal, by design |
| [9](09-resilience.md) | Payments is slow again and it is taking checkout down with it | Five layers: timeout → retry → breaker → bulkhead → fallback | You cannot tell what happened during the incident |
| [10](10-observability.md) | Priya opens a support ticket. Four log streams, no way to connect them | Correlation IDs and distributed tracing | Nothing — the system is now debuggable |
| [11](11-decision-framework.md) | A new feature arrives. Which pattern applies? | Five questions instead of "it depends" | — |

**Read that table again after you finish the tutorial.** It is the whole thing in one page.

---

## How each chapter is laid out

Every chapter has the same seven parts:

1. **The story so far** — one paragraph, so you can start anywhere
2. **In one line** — the idea, no jargon
3. **The words you need** — every term defined before it is used
4. **How it works** — mechanics, a diagram, and real code
5. **Sharp edges** — what breaks in production
6. **When to use it, when not to** — the decision
7. **What is still broken** — the problem that sets up the next chapter

---

## Where the store goes next

The store in this tutorial is the same system as [case study 1 — E-commerce checkout](../case-studies/01-ecommerce/README.md). Same services, same numbers, same order `o-123`.

The tutorial teaches one pattern per chapter. The case study shows all of them working together, with the folder structure and the code. Read the tutorial first, then the case study to see it assembled.

The other four case studies take the same patterns into businesses with different constraints — [banking](../case-studies/02-banking-payments/README.md), [market data](../case-studies/03-stock-market-data/README.md), [trading](../case-studies/04-trading-app/README.md), and [logistics](../case-studies/05-logistics-tracking/README.md) — and reach **opposite conclusions** from the same patterns, because the constraints differ. That contrast is the most valuable part of the whole repo.

---

[Tutorial index](README.md) · Next: [Chapter 1 — The three axes](01-three-axes.md)
