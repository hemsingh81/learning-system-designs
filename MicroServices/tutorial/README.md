# The Tutorial — One Store, Eleven Chapters

Read in order the first time. After that, use it as a reference.

---

## Start here

**[The running example →](00-the-example.md)**

This tutorial follows **one online store** all the way through. Same services, same customer, same numbers, from chapter 1 to chapter 11.

Every chapter fixes a problem that the previous chapter's fix created. That is not a teaching trick — it is how real systems evolve. You solve one thing, the solution creates a new failure mode, and you solve that.

---

## The story in one table

| Ch | The problem | The fix | What the fix broke |
|---|---|---|---|
| [1](01-three-axes.md) | Nobody can describe how the store works | Draw the map: three axes | Nothing yet — you now see the risks |
| [2](02-synchronous.md) | **The 2 a.m. incident.** Checkout dies during the sale | *(diagnosed, not fixed)* | Understanding *why* it died |
| [3](03-asynchronous.md) | Checkout waits 4 s for payment | Accept now, pay in the background. 4 s → **40 ms** | Cards charged twice. Orders invisible for a second |
| [4](04-choosing-a-broker.md) | The team argues Kafka vs RabbitMQ for a week | Answer one question, decide in ten minutes | Nothing — but you now run a broker |
| [5](05-gateway-and-bff.md) | The mobile app makes 6 calls per screen | One front door, one backend per client | Teams start stepping on each other's data |
| [6](06-boundaries-and-data.md) | Inventory adds a column. Ordering breaks | Database-per-service, one writer per entity | Payment fails after stock is reserved — who cleans up? |
| [7](07-saga.md) | 340 mice vanish from the catalogue | Sagas and compensation | Some orders never publish an event at all |
| [8](08-outbox-and-idempotency.md) | **47 orders stuck at `Pending`.** No errors anywhere | The transactional outbox | Duplicates are now normal, by design |
| [9](09-resilience.md) | The 2 a.m. failure moves into the consumer | Five layers: timeout → retry → breaker → bulkhead → fallback | You cannot tell what happened during an incident |
| [10](10-observability.md) | A customer asks about her ₹49.98. You cannot answer | Correlation IDs and distributed tracing | Nothing — the system is now debuggable |
| [11](11-decision-framework.md) | A new feature arrives. Which pattern applies? | Five questions instead of "it depends" | — |

---

## The shape of every chapter

Seven parts, so you can start anywhere and stop at any depth:

1. **The story so far** — one paragraph of context
2. **In one line** — the idea with no jargon at all
3. **The words you need** — every term defined before it is used
4. **How it works** — mechanics, a diagram, and real code
5. **Sharp edges** — the failure modes. This is the part that saves you at 2 a.m.
6. **When to use it, when not to** — the actual decision
7. **What is still broken** — the problem that sets up the next chapter

---

## Chapters

### Part 1 — The map

| # | Chapter | Time | The one thing it teaches |
|---|---|---|---|
| 0 | [The running example](00-the-example.md) | 5 min | The store, the people, the numbers |
| 1 | [The three axes](01-three-axes.md) | 10 min | East-west, north-south, and the boundary |

### Part 2 — The two ways to talk

| # | Chapter | Time | The one thing it teaches |
|---|---|---|---|
| 2 | [Synchronous communication](02-synchronous.md) | 20 min | Latency is the sum; availability is the product |
| 3 | [Asynchronous communication](03-asynchronous.md) | 25 min | Commands vs events, and duplicates as normal |
| 4 | [Choosing a broker](04-choosing-a-broker.md) | 20 min | Name the consumer that needs replay |

### Part 3 — The edges

| # | Chapter | Time | The one thing it teaches |
|---|---|---|---|
| 5 | [Gateway and BFF](05-gateway-and-bff.md) | 15 min | One front door; shape per client |
| 6 | [Boundaries and data ownership](06-boundaries-and-data.md) | 20 min | One writer per entity, always |

### Part 4 — The hard parts

| # | Chapter | Time | The one thing it teaches |
|---|---|---|---|
| 7 | [Sagas](07-saga.md) | 25 min | You cannot roll back, only apologise correctly |
| 8 | [Outbox and idempotency](08-outbox-and-idempotency.md) | 20 min | Turn loss into duplication, then handle duplication |
| 9 | [Resilience](09-resilience.md) | 20 min | Five layers, in a fixed order |
| 10 | [Observability](10-observability.md) | 15 min | The price of everything in chapters 3–9 |

### Part 5 — Deciding

| # | Chapter | Time | The one thing it teaches |
|---|---|---|---|
| 11 | [The decision framework](11-decision-framework.md) | 10 min | Five questions instead of "it depends" |

**Total: about 3.5 hours** of reading, plus the exercises.

---

## Then read the case studies

The chapters teach one pattern at a time. The [case studies](../case-studies/) show many patterns working together under a real constraint, with code:

1. [E-commerce checkout](../case-studies/01-ecommerce/) — **the same store as this tutorial**, assembled
2. [Banking and payments](../case-studies/02-banking-payments/) — correctness over availability
3. [Stock market data](../case-studies/03-stock-market-data/) — 200,000 messages/sec
4. [Trading app](../case-studies/04-trading-app/) — one synchronous gate, 8 ms
5. [Logistics tracking](../case-studies/05-logistics-tracking/) — one stream, three storage models

Case studies 2–5 reach **opposite conclusions** from the store on several decisions, because their constraints differ. That contrast is the most valuable part of the repo.

---

## Also here

- **[Interview prep](../interview-prep/README.md)** — 137 questions in collapsible blocks, built on this material
- **[How to read the sample code](../case-studies/HOW-TO-READ-THE-CODE.md)** — read this before opening any `.cs` file
- **[Diagrams](../diagrams/README.md)** — all 10 diagrams; image files live in [images/](../images/)
