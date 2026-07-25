# Case Studies — The Same Patterns, Five Different Worlds

← [Back to the map](../README.md) · [Tutorial](../tutorial/README.md)

---

## Why case studies

The [tutorial](../tutorial/README.md) teaches one pattern per chapter. Real systems use many at once, and the interesting part is **which trade-off each business forces on you**.

Five systems. Each one has a different defining constraint, and that single constraint changes almost every decision downstream.

| # | Case study | Defining constraint | Everything follows from |
|---|---|---|---|
| 1 | [E-commerce checkout](01-ecommerce/) | Checkout must stay up during a traffic spike | *Never let a dependency fail a sale* |
| 2 | [Banking and payments](02-banking-payments/) | Money must never move twice | *Correctness beats availability* |
| 3 | [Stock market data feed](03-stock-market-data/) | 200,000 ticks/sec, replayable | *Volume beats everything* |
| 4 | [Trading app](04-trading-app/) | An order must be risk-checked before it leaves | *One sync gate, everything else async* |
| 5 | [Logistics tracking](05-logistics-tracking/) | Thousands of vehicles reporting continuously | *Latest value wins; history is cheap* |

---

## Side-by-side: what each one chose

| Decision | E-commerce | Banking | Market data | Trading | Logistics |
|---|---|---|---|---|---|
| **Main transport** | Queue (Rabbit/ASB) | Queue + ledger log | Kafka | Kafka + queue | Kafka |
| **Sync calls** | Few, all with fallbacks | Only the API edge | None in the hot path | One: the risk gate | None |
| **Saga style** | Choreography | Orchestration | None needed | Orchestration | None needed |
| **Consistency** | Eventual, visible in UI | Strong inside the ledger | Eventual | Strong for orders | Eventual |
| **Ordering** | Per order | Strict per account | Per symbol | Per account | Per vehicle |
| **Idempotency** | Inbox table | Idempotency key + inbox | Sequence number | Client order ID | Ping ID + timestamp |
| **Replay needed?** | No | Yes — audit | Yes — backtesting | Yes — audit | Sometimes — route history |
| **If a dependency dies** | Degrade, keep selling | **Stop.** Never guess with money | Buffer and catch up | Reject new orders (kill switch) | Buffer; last known position |
| **Peak shape** | Spiky (sales, campaigns) | Steady, with month-end peaks | Constant, huge at open/close | Bursty at open/close | Steady |
| **Hardest problem** | Overselling | Double-spend | Throughput and lag | Latency plus correctness | Cardinality of state |

**Read across a row and you learn more than reading any single column.** Notice how "what happens if a dependency dies" differs completely: e-commerce degrades and keeps selling, banking stops. Both are correct — for their business.

---

## What is in each folder

```
case-studies/0X-name/
├── README.md            ← the in-depth write-up: constraint → design → failure modes
├── docker-compose.yml   ← real, working infrastructure to run against
└── src/                 ← the code that carries the pattern
    ├── <Name>.Contracts/    ← events and commands, shared by all services
    ├── <Name>.<Service>/     ← one folder per service
    └── …
```

Each README follows the same shape:

1. **The business** — what the system does, in plain English.
2. **The constraint** — the one thing that must be true.
3. **The services** — what exists, and who owns what data.
4. **The communication map** — every call and message, and why it is sync or async.
5. **The walkthrough** — one request, followed end to end, with timings.
6. **The key decisions** — each with the reason and the cost.
7. **Folder structure** — the recommended layout, explained.
8. **The code** — the files that matter, with commentary.
9. **Failure modes** — what breaks, and what happens.
10. **Now break it** — exercises.

---

## About the sample code

> ### 📖 Read [HOW-TO-READ-THE-CODE.md](HOW-TO-READ-THE-CODE.md) first
>
> Five minutes. It covers:
> - **A reading order across all 26 files** — by concept, not by case study, because the ideas build on each other
> - **The shape every file follows**, and which parts to read versus skim
> - **The ~30 referenced types that are deliberately missing** (`OutboxMessage`, `IMetrics`, `InboxMessage`, the DbContexts…) and what each one does
> - The libraries and C# 13 syntax you'll run into
> - How to go from reading the code to actually running it
>
> The missing-types list is the important bit. Open a file cold and you *will* hit a symbol that exists nowhere in the folder.

**What it is:** real, complete files showing the pattern. Written the way you would write them in production, including the error handling — because the error handling *is* the lesson.

**What it is not:** a solution you clone and run with zero setup. There is no `.sln`, no lock file, no CI. Each README lists the packages you would add.

**The `docker-compose.yml` files are real.** They start the broker, database, and tracing so you can run your own services against working infrastructure in about a minute.

**Language: C# / .NET 10.** Because the messaging ecosystem is mature and it is the widest-used enterprise stack for this shape of system. Every pattern here works identically in Java, Go, Node, or Python — only the syntax changes.

---

## Suggested reading order

**If you build web applications:** 1 → 4 → 5

**If you work in finance:** 2 → 4 → 3

**If you handle high-volume data:** 3 → 5 → 1

**If you want the widest coverage in two hours:** 1 (breadth) → 2 (correctness) → 3 (scale)

---

## A note on honesty

Every design here has a cost, and each README names it. There is no architecture in this folder without a downside. If a write-up ever reads as though a choice is free, that is a bug in the write-up.

---

← [Back to the map](../README.md) · [Tutorial](../tutorial/README.md)
