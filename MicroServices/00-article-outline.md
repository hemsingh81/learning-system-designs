# Article Outline — Microservices Communication

**Status:** Phase 1 deliverable · awaiting your sign-off before drafting
**Target length:** ~5,000 words (LinkedIn article) · ~1,900 characters (LinkedIn hook post)
**Audience:** broad mixed — layered so a junior dev, a senior engineer, and an engineering manager each get value

---

## Working titles

| # | Title | Angle |
|---|---|---|
| 1 | **Microservices Communication: The Field Guide I Wish I'd Had** | Personal, experience-led. Best organic reach. |
| 2 | **How Microservices Actually Talk — Inside, Outside, and Across Boundaries** | Descriptive, matches your three-axis framing. |
| 3 | **Every Way Microservices Communicate, With Working Code for Each** | Repo-forward. Strongest click-through to GitHub. |

**Recommendation:** #1 for the LinkedIn post headline, #2 as the repo README `<h1>`. #3 works as the post's closing CTA line.

---

## The layering rule

Every major section follows the same three-layer structure so readers can exit at any depth:

1. **In one line** — the idea, no jargon. (Manager stops here.)
2. **How it works** — mechanics, diagram, a concrete example. (Most readers stop here.)
3. **The sharp edges** — failure modes, tuning, what bites at scale. (Architects read this.)

Every jargon term is defined the first time it appears. No exceptions — this is the single biggest risk with a mixed audience.

---

## Section-by-section

### 0. Hook — "The 2 a.m. incident" · ~250 words
Open with a concrete failure, not a definition. An order service calls payment synchronously; payment slows to 4 s under load; orders time out; retries amplify the load; the whole checkout path collapses. One paragraph, no blame.

Land the thesis: **the hard part of microservices isn't splitting the code, it's choosing how the pieces talk.**

> Visual: none — text hook, keep it fast.

---

### 1. The three axes · ~400 words
Frame the entire article before any technology appears.

- **East-west** — service to service, inside the trust boundary
- **North-south** — the outside world to your system
- **The boundary itself** — where you draw lines and who owns what data

Argue that most teams obsess over axis 1, under-invest in axis 2, and skip axis 3 entirely — and that skipping axis 3 is what produces a distributed monolith.

Define, plainly: service, boundary, coupling, latency, blast radius.

> **Visual: D1 — Communication landscape** (hero SVG). Also the LinkedIn post image.

---

### 2. Synchronous communication · ~700 words

**In one line:** the caller waits for the answer.

**How it works**
- HTTP/REST — ubiquitous, human-readable, cache-friendly, every tool speaks it
- gRPC — contract-first, binary, HTTP/2, streaming; 5–10× lighter on the wire internally
- Service discovery — how a service finds another without hardcoded URLs

**The sharp edges**
- Temporal coupling: the callee must be alive *right now*
- Latency compounds — 5 hops × 50 ms = 250 ms floor, before any work happens
- Cascading failure and retry storms (call back to the 2 a.m. hook)
- Why "just add a retry" makes it worse without a circuit breaker

**When it's right:** the caller genuinely cannot proceed without the answer, and the answer is fast. Reads, validations, lookups.

> **Visual: D2 — Sync vs async, side by side** (hero SVG)
> **Repo:** `modules/M1-sync-rest`, `modules/M2-sync-grpc`

---

### 3. Asynchronous communication · ~900 words

**In one line:** the caller hands off the message and moves on.

**How it works**
- Queues vs topics — work distribution vs fan-out
- Commands vs events — *do this* vs *this happened* (this distinction drives everything downstream; spend real words here)
- Pub/sub, consumer groups, competing consumers
- Request-reply over a broker — and why it's usually a smell

**The sharp edges**
- Eventual consistency, in plain language, with a real user-visible example
- Message ordering — what you actually get, and per-partition ordering
- At-least-once delivery means **duplicates are normal, not exceptional**
- Poison messages and dead-letter queues
- Debugging is genuinely harder — sets up the observability section

**When it's right:** the caller doesn't need the answer to continue; the work can absorb delay; you want independent failure domains.

> **Visual: D3 — Commands vs events** (Mermaid)
> **Repo:** `modules/M3-queues-rabbitmq`, `modules/M4-streaming-kafka`

---

### 4. Choosing a broker without cargo-culting · ~800 words · **CENTREPIECE**

This is the section people will screenshot. It is the direct payoff of "one example of each, with reasoning."

Same order-fulfilment flow, four implementations:

| Tool | Mental model | Shines when | Costs you |
|---|---|---|---|
| **RabbitMQ** | Smart broker, dumb consumer | Task distribution, per-message ack, retries, DLQ, priority | No replay; broker holds routing logic |
| **Kafka** | Dumb broker, smart consumer | Replayable event log, many independent consumers, ordered per key, high throughput | Operational weight; no per-message ack semantics |
| **Azure Service Bus** | Managed enterprise messaging | Sessions/FIFO, scheduled delivery, duplicate detection, transactions, zero ops | Cloud lock-in, cost, throughput ceiling vs Kafka |
| **Dapr** | Portability layer over any of the above | Multi-cloud, swap brokers by config, sidecar-standardised | Sidecar overhead; abstraction hides broker-specific power |

Then the honest part — **a decision flowchart**, plus a short "signals you chose wrong" list:
- Using Kafka purely as a work queue → you wanted RabbitMQ
- Replaying a RabbitMQ queue to rebuild state → you wanted Kafka
- Writing your own retry/DLQ/outbox plumbing three times → you wanted Dapr or MassTransit
- Using Dapr but reaching past it to native broker features → the abstraction is costing more than it saves

> **Visual: D4 — Broker decision flowchart** (hero SVG). Most shareable asset in the article.
> **Repo:** `modules/M3` → `M6`

---

### 5. North-south — talking to the outside world · ~700 words

**In one line:** your system needs one front door, not fifty.

- **API Gateway** — routing, auth, rate limiting, TLS termination (YARP, Ocelot, Azure APIM)
- **BFF** — a tailored backend per client type; why the mobile app and the web app should not share a response shape
- Protocol choice at the edge: REST vs GraphQL vs gRPC-Web — what each optimises for
- **Server-initiated communication**, the axis most articles forget: WebSockets/SignalR, Server-Sent Events, webhooks, long polling
- Gateway anti-patterns: business logic creeping into the gateway; the gateway becoming a deploy bottleneck for every team

> **Visual: D5 — Gateway and BFF topology** (Mermaid)
> **Repo:** `modules/M7-gateway-bff`, `modules/M8-push-signalr-webhooks`

---

### 6. Boundaries — the section everyone skips · ~700 words

**In one line:** if two services share a database, you have one service with extra network calls.

- Bounded contexts in plain language — the same word means different things to different teams ("customer" to billing vs. to support)
- **Database-per-service**, and honest answers to the questions it raises: reporting, joins, referential integrity
- Anti-corruption layer — protecting your model from someone else's
- Contract-first design and versioning: additive changes, consumer-driven contract tests, why breaking a contract is a production incident with a delay fuse

**Distributed monolith checklist** — six symptoms, each one line. Highly quotable, likely the second-most-screenshotted block:
1. Services must deploy together to work
2. Two services write to the same table
3. One team's schema change breaks another team's build
4. A single request fans out through six synchronous hops
5. Nobody can name who owns a given entity
6. Local development requires running the entire system

> **Visual: D6 — Bounded contexts and data ownership** (Mermaid)
> **Repo:** `modules/M5-enterprise-asb` (the boundary write-up lives with the settlement example)

---

### 7. The hard parts · ~900 words

**7a. Distributed transactions and the saga pattern**
- Why two-phase commit doesn't fit; what you trade for availability
- **Choreography** — services react to events; no coordinator; simple at 3 services, opaque at 10
- **Orchestration** — one coordinator drives the flow; visible and testable; a component that can itself fail
- **Compensating actions** — you can't roll back, you can only apologise correctly (refund, restock, cancel)

**7b. The dual-write problem and the Outbox pattern**
- The bug nearly everyone ships first: write to DB, then publish to broker, crash in between → state and events disagree, silently, forever
- The Outbox fix: one local transaction, a relay publishes afterwards
- **Idempotent consumers** — the required other half; at-least-once delivery guarantees you *will* process duplicates

**7c. Resilience**
- Timeout → retry with exponential backoff and jitter → circuit breaker → bulkhead → fallback
- Why retries without jitter synchronise into a thundering herd
- Backpressure and load shedding: refusing work is a feature

> **Visuals: D7 — Choreography vs orchestration** (hero SVG) · **D8 — Outbox flow** (Mermaid) · **D9 — Resilience layers** (Mermaid)
> **Repo:** `modules/M9-outbox-idempotency`, `modules/M10-observability-resilience`

---

### 8. Making the invisible visible · ~450 words

**In one line:** in a distributed system, you cannot debug what you cannot trace.

- Correlation IDs — the cheapest thing with the highest payoff
- Distributed tracing with OpenTelemetry: traces, spans, context propagation across HTTP *and* broker messages (the part people miss)
- Structured logging and the three pillars, briefly
- Health checks: liveness vs readiness, and why confusing them causes restart loops

Close with the screenshot: a single trace spanning gateway → order → broker → payment → notification. This is the article's "aha" image.

> **Visual: D10 — Trace across five services** (Mermaid, upgraded to SVG for the carousel)
> **Repo:** `modules/M10-observability-resilience`

---

### 9. How it plays out in industry · ~600 words

Five short case studies. Each: the constraint → the choice → the reasoning. No vendor claims I can't support.

| Domain | Defining constraint | Typical shape |
|---|---|---|
| **E-commerce** | Checkout must stay up during traffic spikes | Sync for reads, async saga for order fulfilment |
| **Fintech / payments** | Money must never double-move | Idempotency keys, outbox, strict FIFO, immutable ledger |
| **Ride-hailing / logistics** | Continuous high-volume location updates | Streaming, partition by driver/region, push to client |
| **Healthcare** | Auditability and strict data boundaries | Event log as audit trail, hard bounded contexts, ACL at every seam |
| **Media / streaming** | Massive fan-out from few writes | Pub/sub, CDN at the edge, eventual consistency accepted by design |

---

### 10. A decision framework you can actually use · ~350 words

Not "it depends." Five questions, in order:

1. Can the caller continue without the answer? → **No: sync. Yes: async.**
2. Does anyone need to replay this later? → **Yes: log/streaming. No: queue.**
3. Is it one consumer or many, now and in future? → drives queue vs topic
4. What breaks if this message arrives twice? → determines idempotency work
5. Who owns this data, and who is merely reading it? → determines the boundary

> **Visual: reuse D4**

---

### 11. Close + CTA · ~200 words
Return to the 2 a.m. incident and name what would have prevented it (a timeout, a circuit breaker, and an async handoff — three changes, not a rewrite).

CTA into the repo: every pattern above is runnable, one folder each, `docker compose up`, with a "now break it" exercise so the failure modes are felt rather than read.

---

## Companion assets

| Asset | Spec | Purpose |
|---|---|---|
| LinkedIn hook post | ~1,900 chars, hook in first 210 (pre-"see more") | Drives traffic to article + repo |
| Carousel | 10 slides, 1080×1080, from D1/D2/D4/D7/D10 + checklist blocks | Highest-reach LinkedIn format |
| Repo README | Article #2 variant, Mermaid inline, module index | Landing page from the post |

---

## Open question for you

Section 0 opens with a 2 a.m. production incident. **Do you want that written as something you personally experienced, or as a neutral composite ("a pattern I've seen repeatedly")?** First-person incidents perform significantly better on LinkedIn — but only if the story is genuinely yours. If you have a real one, tell me roughly what happened and I'll write it in your voice.
