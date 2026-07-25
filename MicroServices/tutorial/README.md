# The Tutorial — 11 Chapters

Read in order the first time. After that, use it as a reference.

---

## The shape of every chapter

Each chapter has the same six parts, so you can always stop at the depth you need:

1. **In one line** — the idea with no jargon at all.
2. **The words you need** — every term defined before it is used.
3. **How it works** — mechanics, a diagram, and real code.
4. **Sharp edges** — the failure modes. This is the part that saves you at 2 a.m.
5. **When to use it, when not to** — the actual decision.
6. **Try it yourself** — a small exercise. Usually: build it, then break it on purpose.

---

## Chapters

### Part 1 — The map

| # | Chapter | Time | Why it matters |
|---|---|---|---|
| 1 | [The three axes](01-three-axes.md) | 10 min | Gives you the vocabulary for every other chapter |

### Part 2 — The two ways to talk

| # | Chapter | Time | Why it matters |
|---|---|---|---|
| 2 | [Synchronous communication](02-synchronous.md) | 20 min | HTTP, gRPC, and why waiting is expensive |
| 3 | [Asynchronous communication](03-asynchronous.md) | 25 min | Queues, topics, commands vs events, eventual consistency |
| 4 | [Choosing a broker](04-choosing-a-broker.md) | 20 min | RabbitMQ vs Kafka vs Azure Service Bus vs Dapr |

### Part 3 — The edges

| # | Chapter | Time | Why it matters |
|---|---|---|---|
| 5 | [Gateway and BFF](05-gateway-and-bff.md) | 15 min | One front door; server-initiated push |
| 6 | [Boundaries and data ownership](06-boundaries-and-data.md) | 20 min | The chapter that prevents a distributed monolith |

### Part 4 — The hard parts

| # | Chapter | Time | Why it matters |
|---|---|---|---|
| 7 | [Sagas](07-saga.md) | 25 min | Transactions across services, and compensation |
| 8 | [Outbox and idempotency](08-outbox-and-idempotency.md) | 20 min | The silent data-divergence bug |
| 9 | [Resilience](09-resilience.md) | 20 min | Timeout, retry, breaker, bulkhead, fallback |
| 10 | [Observability](10-observability.md) | 15 min | Correlation IDs and distributed tracing |

### Part 5 — Deciding

| # | Chapter | Time | Why it matters |
|---|---|---|---|
| 11 | [The decision framework](11-decision-framework.md) | 10 min | Five questions instead of "it depends" |

**Total: about 3.5 hours** of reading, plus the exercises.

---

## Then read the case studies

The chapters teach one pattern at a time. The [case studies](../case-studies/) show many patterns working together under a real constraint, with code:

1. [E-commerce checkout](../case-studies/01-ecommerce/)
2. [Banking and payments](../case-studies/02-banking-payments/)
3. [Stock market data feed](../case-studies/03-stock-market-data/)
4. [Trading app](../case-studies/04-trading-app/)
5. [Logistics tracking](../case-studies/05-logistics-tracking/)

---

## Diagrams

Every chapter links to its diagram in [diagrams/README.md](../diagrams/README.md). The image files themselves live in [images/](../images/).
