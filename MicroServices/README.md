# Microservices Communication — A Complete Tutorial

How services talk to each other, how they talk to the outside world, and where you draw the lines between them.

Written in plain English. Every term is explained the first time it appears. Every pattern has runnable-shaped sample code.

---

## Who this is for

| You are | Read this way |
|---|---|
| **New to microservices** | Read the tutorial chapters in order. Skip the "Sharp edges" boxes on the first pass. |
| **Experienced backend dev** | Read chapter 11 (the decision framework) first, then jump to the chapters you argue about at work. |
| **Engineering manager / architect** | Read the "In one line" and "When to use it" parts of each chapter, then read the five case studies. |

---

## How the folders are organised

```
MicroServices/
├── README.md                 ← you are here (the map)
├── 00-article-outline.md     ← origin notes — not required reading, see below
│
├── images/                   ← EVERY image lives here, nowhere else
│   ├── svg/                  ← source diagrams, hand-authored, dark theme
│   └── png/                  ← 1600×900 exports for social posts
│
├── diagrams/
│   └── README.md             ← all 10 diagrams (D1–D10) as inline Mermaid + colour rules
│
├── interview-prep/           ← 137 Q&A in collapsible blocks, linked to the detail
│   ├── README.md
│   ├── 01-fundamentals.md
│   ├── 02-communication.md
│   ├── 03-boundaries-and-edges.md
│   ├── 04-reliability.md
│   ├── 05-observability.md
│   ├── 06-system-design-scenarios.md
│   └── 07-rapid-fire.md
│
├── tutorial/                 ← the teaching material, 11 chapters
│   ├── README.md             ← chapter index + reading paths
│   ├── 01-three-axes.md
│   ├── 02-synchronous.md
│   ├── 03-asynchronous.md
│   ├── 04-choosing-a-broker.md
│   ├── 05-gateway-and-bff.md
│   ├── 06-boundaries-and-data.md
│   ├── 07-saga.md
│   ├── 08-outbox-and-idempotency.md
│   ├── 09-resilience.md
│   ├── 10-observability.md
│   └── 11-decision-framework.md
│
└── case-studies/             ← five real-world systems, with code
    ├── README.md             ← how to compare the five
    ├── 01-ecommerce/
    ├── 02-banking-payments/
    ├── 03-stock-market-data/
    ├── 04-trading-app/
    └── 05-logistics-tracking/
```

**One rule for images.** All image files live in `images/`. A document links to them with a relative path such as `../images/svg/d1-landscape.svg`. If you add a diagram, add it to `images/svg/`, export a PNG to `images/png/`, and link it. Never keep a copy next to a document.

[00-article-outline.md](00-article-outline.md) is a short origin note, not required reading — it maps each planned section of the original outline to where it actually ended up (mostly the tutorial chapters, expanded well beyond what was planned).

---

## The tutorial

Eleven chapters. Each one follows the same shape, so you always know where you are:

1. **In one line** — the idea, no jargon.
2. **The words you need** — terms defined before they are used.
3. **How it works** — mechanics, a diagram, and code.
4. **Sharp edges** — what breaks, and how it breaks in production.
5. **When to use it / when not to** — the decision.
6. **Try it yourself** — a small exercise, usually "now break it".

| # | Chapter | The one thing it teaches |
|---|---|---|
| 1 | [The three axes](tutorial/01-three-axes.md) | Inside, outside, and the boundary — most teams only think about the first |
| 2 | [Synchronous communication](tutorial/02-synchronous.md) | The caller waits, and inherits every delay downstream |
| 3 | [Asynchronous communication](tutorial/03-asynchronous.md) | The caller hands off and leaves; duplicates become normal |
| 4 | [Choosing a broker](tutorial/04-choosing-a-broker.md) | RabbitMQ vs Kafka vs Azure Service Bus vs Dapr, with reasons |
| 5 | [Gateway and BFF](tutorial/05-gateway-and-bff.md) | One front door, tailored per client |
| 6 | [Boundaries and data ownership](tutorial/06-boundaries-and-data.md) | Share a database and you have one service with extra latency |
| 7 | [Sagas](tutorial/07-saga.md) | You cannot roll back across services; you can only apologise correctly |
| 8 | [Outbox and idempotency](tutorial/08-outbox-and-idempotency.md) | The dual-write bug almost everyone ships first |
| 9 | [Resilience](tutorial/09-resilience.md) | Timeout → retry → breaker → bulkhead → fallback, in that order |
| 10 | [Observability](tutorial/10-observability.md) | You cannot debug what you cannot trace |
| 11 | [The decision framework](tutorial/11-decision-framework.md) | Five questions that pick the pattern for you |

---

## The case studies

Same patterns, five different worlds. Each folder has an in-depth write-up **and** sample code with a recommended folder structure.

| # | Case study | Defining constraint | Patterns it shows |
|---|---|---|---|
| 1 | [E-commerce checkout](case-studies/01-ecommerce/) | Checkout must stay up during a traffic spike | Sync reads, async saga, outbox, choreography |
| 2 | [Banking and payments](case-studies/02-banking-payments/) | Money must never move twice | Idempotency keys, double-entry ledger, strict FIFO, orchestration |
| 3 | [Stock market data feed](case-studies/03-stock-market-data/) | 200,000 price ticks per second, replayable | Kafka partitions, fan-out, backpressure, replay |
| 4 | [Trading app](case-studies/04-trading-app/) | An order must be risk-checked before it leaves | Sync risk gate, async execution, state machine, push to client |
| 5 | [Logistics tracking](case-studies/05-logistics-tracking/) | Continuous location updates from thousands of vehicles | Streaming, partition by vehicle, geo-fence events, SSE push |

Read [case-studies/README.md](case-studies/README.md) for a side-by-side comparison of what each one chose and why.

---

## Interview preparation

**[interview-prep/](interview-prep/README.md) — 137 questions and answers.**

Every question is in a collapsible block: read the question, answer it in your head, then expand to check. Every answer has the same three parts — *the 30-second answer* (what you say first), *if they dig deeper* (the trade-off and the failure mode), and *the follow-up to expect* — then links to the full explanation in the tutorial or a case study.

| # | Section | Q | Covers |
|---|---|---|---|
| 1 | [Fundamentals](interview-prep/01-fundamentals.md) | 12 | What they are, when *not* to use them, distributed monoliths |
| 2 | [Communication](interview-prep/02-communication.md) | 20 | Sync vs async, commands vs events, brokers, partitions |
| 3 | [Boundaries and edges](interview-prep/03-boundaries-and-edges.md) | 16 | Data ownership, contracts, gateway, BFF, webhooks |
| 4 | [Reliability](interview-prep/04-reliability.md) | 24 | **The highest-value section** — sagas, outbox, idempotency, resilience |
| 5 | [Observability](interview-prep/05-observability.md) | 12 | Correlation IDs, tracing, metrics, health checks |
| 6 | [System design scenarios](interview-prep/06-system-design-scenarios.md) | 8 | "Design me X" — worked answers with a structure to follow |
| 7 | [Rapid fire](interview-prep/07-rapid-fire.md) | 45 | One-liners for the quick round or a revision pass |

Short on time? [Rapid fire](interview-prep/07-rapid-fire.md) plus the [six most-asked questions](interview-prep/README.md#the-six-questions-you-are-most-likely-to-be-asked).

---

## The technology used in the samples

The samples are **.NET 10 / C#**, because that is the widest-used enterprise stack for this shape of system, and because the messaging libraries are mature.

| Concern | What the samples use | Equally valid alternatives |
|---|---|---|
| HTTP service | ASP.NET Core Minimal APIs | Spring Boot, NestJS, FastAPI, Go chi |
| Fast internal calls | gRPC | HTTP + Protobuf, Thrift |
| Queue | RabbitMQ | Azure Service Bus, AWS SQS, Redis Streams |
| Event log / stream | Kafka | Redpanda, Azure Event Hubs, AWS Kinesis |
| Managed enterprise bus | Azure Service Bus | AWS SNS+SQS, Google Pub/Sub |
| Portability layer | Dapr | MassTransit, NServiceBus |
| Gateway | YARP | Ocelot, Kong, Envoy, Azure APIM |
| Push to browser | SignalR | raw WebSockets, Server-Sent Events |
| Tracing | OpenTelemetry | vendor SDKs (all converge on OTel anyway) |
| Database | PostgreSQL / SQL Server | any relational DB; the patterns do not change |

**The patterns are the point, not the tools.** Every idea here works the same in Java, Go, Node, or Python. Only the syntax changes.

---

## How to read the sample code

> **Start here: [HOW-TO-READ-THE-CODE.md](case-studies/HOW-TO-READ-THE-CODE.md)**
>
> It gives you a reading order across all 26 files, explains the layout every file follows, and — importantly — lists the ~30 types the samples reference that are **deliberately not included** (`OutboxMessage`, `IMetrics`, the DbContexts, and so on), with a one-line description of each. Without that list you will go looking for files that do not exist.

Each case study's `src/` folder holds the files that **carry the pattern** — the contracts, the handlers, the outbox, the saga, the consumer. They are written as real, complete files, not fragments.

What they are **not**: a full solution you clone and build with zero setup. There is no `.sln`, no NuGet lock file, and no CI. That is deliberate — the goal is that you read the file, understand the pattern, and copy the shape into your own service. Each README tells you exactly which extra packages you would add to run it for real.

Where a case study ships a `docker-compose.yml`, that file is real and works — it starts the infrastructure (broker, database, tracing) so you can run your own version of the services against it.

---

## The diagram set

Ten diagrams share one visual language. The colours mean something and never change:

| Colour | Meaning |
|---|---|
| 🟠 Amber | **Synchronous** — the caller is blocked |
| 🟢 Green | **Asynchronous** — decoupled, event-driven |
| 🔵 Blue | **North-south** — edge, external, client-facing |
| 🔴 Red | **Failure path** — compensation, retry, dead-letter |
| 🟣 Purple | **Abstraction layer** — Dapr, service mesh |
| ⚪ Slate | Infrastructure, storage, neutral |

Once you know the code, you can read any diagram in the set without a legend. Full set: [diagrams/README.md](diagrams/README.md).

---

## Suggested order for a first read

If you have one hour:

1. [Chapter 1 — the three axes](tutorial/01-three-axes.md) (10 min)
2. [Chapter 2 — synchronous](tutorial/02-synchronous.md) and [Chapter 3 — asynchronous](tutorial/03-asynchronous.md) (20 min)
3. [Chapter 8 — outbox and idempotency](tutorial/08-outbox-and-idempotency.md) (10 min) — this is the bug you have in production right now
4. [Case study 1 — e-commerce](case-studies/01-ecommerce/) (20 min)

Then come back for chapters 4–7 and 9–11 when you hit the problem they solve.
