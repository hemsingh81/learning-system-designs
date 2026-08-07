# 47 · Concept: System Design (30 questions)

[← LLM Application Integration](46-concept-llm-application-integration.md) · [Home](README.md) · [Next → Redis Cache](48-concept-redis-cache.md)

This file covers **system design** — how I design scalable, reliable, maintainable systems — in simple English with real depth, the way I'd answer in an architecture interview. I ground answers in projects A–E (TCW platforms, RAG assistant, integrations).

> Simple one-liner: *"System design is choosing components and how they talk so the system meets its scale, reliability, latency, security and cost requirements — and stays simple enough to run and change. I start from requirements and trade-offs, not from favourite tech."*

**Jump to:** [SD1 What it is](#sd1--what-is-system-design) · [SD2 Requirements](#sd2--functional-vs-non-functional) · [SD3 Approach](#sd3--my-approach-to-a-design-question) · [SD4 Scalability](#sd4--scalability) · [SD5 Vertical vs horizontal](#sd5--vertical-vs-horizontal-scaling) · [SD6 Load balancing](#sd6--load-balancing) · [SD7 Stateless](#sd7--stateless-services) · [SD8 Caching](#sd8--caching) · [SD9 Databases](#sd9--choosing-a-database) · [SD10 SQL vs NoSQL](#sd10--sql-vs-nosql)
> [SD11 Replication](#sd11--replication) · [SD12 Sharding](#sd12--sharding) · [SD13 CAP](#sd13--cap-theorem) · [SD14 Consistency](#sd14--consistency-models) · [SD15 Async & queues](#sd15--async-messaging) · [SD16 Microservices](#sd16--microservices-vs-monolith) · [SD17 API design](#sd17--api-design) · [SD18 Rate limiting](#sd18--rate-limiting) · [SD19 Availability](#sd19--high-availability) · [SD20 Resilience](#sd20--resilience-patterns)
> [SD21 Observability](#sd21--observability) · [SD22 Security](#sd22--security) · [SD23 CDN](#sd23--cdn-and-edge) · [SD24 Bottlenecks](#sd24--finding-bottlenecks) · [SD25 Estimation](#sd25--capacity-estimation) · [SD26 Trade-offs](#sd26--trade-offs) · [SD27 Data flow](#sd27--data-flow-and-idempotency) · [SD28 Cost](#sd28--cost) · [SD29 Pitfalls](#sd29--common-pitfalls) · [SD30 My approach](#sd30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of system design in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. Design starts from requirements, not from favourite tech.** Before I draw a box I ask: how many users, how much data, how fast, how available, how secure, how much budget? Those **non-functional requirements** decide everything. On projects A–E I've watched good tech fail because it answered a requirement nobody actually had.

**2. It's building blocks and how they connect.** Services, databases, caches, queues, gateways, CDNs — the design is choosing these pieces and wiring them so the whole meets its needs while staying simple enough to run and change.

**3. Scale horizontally, and to do that, stay stateless.** Vertical scaling (a bigger box) runs out fast. Horizontal scaling (more boxes behind a **load balancer**) is how real systems grow. The enabler is **stateless services** — no session stuck on one machine — so any request can hit any instance.

**4. Caching is the cheapest big win, and the trickiest.** A cache in front of slow work cuts latency and load dramatically. The hard part is invalidation and staleness — so I cache what's read often and changes rarely, and I'm deliberate about how it expires.

**5. The database choice and its guarantees drive the design.** SQL for strong consistency and relationships; NoSQL for scale and flexible shapes. **Replication** gives availability and read scale; **sharding** gives write scale. Each brings consistency trade-offs I have to own.

**6. CAP forces an honest choice under failure.** When the network partitions, I pick availability or strong consistency — I can't have both at that moment. Most real systems lean on **eventual consistency** where it's safe, and demand strong consistency only where correctness is money (like a balance).

**7. Async and resilience keep the system up under stress.** Queues decouple producers from consumers, absorb spikes and smooth load. Resilience patterns — timeouts, retries with backoff, circuit breakers, idempotency, rate limiting — stop one slow dependency from cascading into a full outage.

**8. If I can't see it, I can't run it — and every choice is a trade-off.** Observability (logs, metrics, traces) is how I find bottlenecks and know the system is healthy. And there is no "right" design — only the best trade-off for *these* constraints, stated out loud so everyone understands the cost.

**The full-stack / architect lens:** the later Q&As go into replication and sharding detail, consistency models, microservices vs monolith, API design, high availability, CDN and edge, capacity estimation, data flow and idempotency, security and cost. The through-line: **requirements-driven decision-making under trade-offs**, grounded in what the system actually has to do.

**One rule I never break:** *I never pick the architecture before I know the numbers — requirements and trade-offs come first, technology second.*

---

## SD1 · What is system design?

**Simple explanation.** **System design** is deciding the **building blocks** of a system (services, databases, caches, queues, gateways) and **how they connect** so the whole meets its requirements — scale, speed, reliability, security, cost — while staying maintainable.

**Architect's view:** It's requirements-driven decision-making under trade-offs. There's no single "right" design — only the best fit for *these* constraints.

**Follow-ups**
- *"One-line?"* — Choosing and connecting components to meet requirements and trade-offs.
- *"Right answer?"* — There isn't one — it's the best trade-off for the given needs.

---

## SD2 · Functional vs non-functional

**Simple explanation.** **Functional** requirements = what it does (features). **Non-functional (NFRs)** = how well: scale, latency, availability, security, cost, maintainability. Good design is mostly driven by NFRs — they decide the architecture.

**Follow-ups**
- *"Which matters more in design?"* — NFRs shape the architecture; features fit inside it.
- *"Example NFR?"* — "99.9% uptime, <300ms p95, 10k req/s" — these drive choices.

---

## SD3 · My approach to a design question

**Simple explanation.** I follow a repeatable flow: **1) clarify requirements & scale**, **2) define APIs & data**, **3) sketch a high-level design**, **4) deep-dive the hard parts**, **5) address NFRs (scale, reliability, security)**, **6) discuss trade-offs & bottlenecks**. Requirements first, tech last.

**Follow-ups**
- *"First step always?"* — Clarify requirements and estimate scale — never design blind.
- *"Why this order?"* — Stops premature tech choices; keeps design grounded in needs.

---

## SD4 · Scalability

**Simple explanation.** **Scalability** is handling more load by adding resources without redesigning. I design for it with **stateless services**, **horizontal scaling**, **caching**, **async processing**, and a **scalable data layer** — so I can grow by adding instances.

**Follow-ups**
- *"Scale up or out?"* — Prefer out (horizontal) for elasticity and resilience.
- *"Enabler?"* — Statelessness — without it, horizontal scaling is hard.

---

## SD5 · Vertical vs horizontal scaling

**Simple explanation.** **Vertical** = bigger machine (simple, but a ceiling and a single point of failure). **Horizontal** = more machines (elastic, resilient, but needs statelessness and coordination). I default to horizontal for production scale.

**Follow-ups**
- *"When vertical?"* — Quick wins, or workloads hard to distribute (some databases).
- *"Horizontal need?"* — Stateless app + load balancer + shared data/cache.

---

## SD6 · Load balancing

**Simple explanation.** A **load balancer** spreads traffic across instances, does **health checks**, and enables zero-downtime deploys. On Azure I use Front Door/App Gateway/Load Balancer depending on layer ([file 37](37-concept-azure-services.md)).

**Follow-ups**
- *"Algorithms?"* — Round-robin, least-connections, hash — pick by workload.
- *"Health checks?"* — Route only to healthy instances; drain bad ones.

---

## SD7 · Stateless services

**Simple explanation.** **Stateless** services keep no per-user state in memory — any instance can handle any request. State goes to **Redis/DB** ([file 48](48-concept-redis-cache.md)). This is what makes horizontal scaling, restarts and rolling deploys painless.

**Follow-ups**
- *"Where does state go?"* — External store (Redis/DB) — not the app instance.
- *"Why crucial?"* — Enables scaling, failover, and safe restarts.

---

## SD8 · Caching

**Simple explanation.** **Caching** stores hot data close to use to cut latency and DB load. I cache at multiple layers (CDN, app, distributed **Redis**), pick an **invalidation** strategy, and set **TTLs** ([file 48](48-concept-redis-cache.md)). Caching is one of the highest-impact scaling tools.

**Follow-ups**
- *"Hardest part?"* — Invalidation — keeping cache fresh without serving stale data.
- *"Where cache?"* — CDN for static, Redis for shared data, in-process for tiny hot data.

---

## SD9 · Choosing a database

**Simple explanation.** I pick the DB by **data shape and access pattern**: relational + transactions → SQL; flexible/huge scale → NoSQL; search → search engine; caching → Redis; vectors → vector DB ([file 44](44-concept-vector-databases-chroma.md)). Often **polyglot** — the right store per job.

**Follow-ups**
- *"First question?"* — Access patterns and consistency needs, not popularity.
- *"Polyglot okay?"* — Yes — use different stores for different needs, with care on ops.

---

## SD10 · SQL vs NoSQL

**Simple explanation.** **SQL** — structured, relationships, strong consistency, transactions (finance). **NoSQL** — flexible schema, horizontal scale, high throughput (documents, key-value, wide-column). I choose by consistency needs, scale and data shape ([file 50](50-concept-data-design.md)).

**Follow-ups**
- *"Finance default?"* — SQL — transactions and integrity matter most.
- *"NoSQL win?"* — Massive scale, flexible/denormalised data, simple access patterns.

---

## SD11 · Replication

**Simple explanation.** **Replication** keeps copies of data on multiple nodes for **availability** and **read scaling**. Common patterns: primary-replica (writes to primary, reads from replicas) and multi-primary. It adds **replication lag** to reason about.

**Follow-ups**
- *"Benefit?"* — Failover + more read capacity.
- *"Catch?"* — Replica lag → reads may be slightly stale (eventual consistency).

---

## SD12 · Sharding

**Simple explanation.** **Sharding** splits data across nodes by a **shard key** so no single node holds everything — enabling write/storage scale beyond one machine. The hard parts are choosing a good key and handling cross-shard queries.

**Follow-ups**
- *"Good shard key?"* — Even distribution, aligned to access patterns — avoids hotspots.
- *"Downside?"* — Cross-shard joins/transactions get complex — shard only when needed.

---

## SD13 · CAP theorem

**Simple explanation.** **CAP**: during a network **partition**, a distributed store can guarantee **Consistency** or **Availability**, not both. So I choose: **CP** (correct but may reject during partition — finance) or **AP** (always answers, may be stale).

**Follow-ups**
- *"Finance choice?"* — Usually CP — correctness over availability for money.
- *"AP example?"* — Social feed — staleness is fine, uptime matters.

---

## SD14 · Consistency models

**Simple explanation.** **Strong consistency** = every read sees the latest write (needed for balances). **Eventual consistency** = reads may lag but converge (fine for feeds, caches). I pick per data type — strong where correctness is critical, eventual where scale/availability wins.

**Follow-ups**
- *"Mix both?"* — Yes — strong for money, eventual for analytics/caches.
- *"Cost of strong?"* — More coordination → higher latency/lower availability.

---

## SD15 · Async messaging

**Simple explanation.** **Queues/streams** ([file 49](49-concept-kafka.md)) decouple producers from consumers, absorb spikes (**buffering**), enable retries, and let services scale independently. I use them for slow work, event-driven flows, and integrations — core to resilient design.

**Follow-ups**
- *"Why async?"* — Decoupling, load smoothing, resilience, independent scaling.
- *"Queue vs stream?"* — Queue for task hand-off; stream (Kafka) for event log/replay.

---

## SD16 · Microservices vs monolith

**Simple explanation.** **Monolith** — simple to build/deploy, great to start. **Microservices** — independent scaling/deploy per team, but distributed complexity. I start with a **well-structured monolith** and split out services when scale/teams justify it — not by default.

**Follow-ups**
- *"Start with micro?"* — Rarely — premature microservices add huge complexity.
- *"When split?"* — Clear bounded contexts, independent scale/teams, proven need.

---

## SD17 · API design

**Simple explanation.** Good APIs are **clear, consistent, versioned**, and secure. I use REST for CRUD, consider **GraphQL** for flexible reads and **gRPC** for internal high-performance calls, with pagination, proper status codes, and an **API gateway** for cross-cutting concerns.

**Follow-ups**
- *"Versioning?"* — Version from day one to evolve without breaking clients.
- *"Gateway role?"* — Auth, rate limiting, routing, observability in one place.

---

## SD18 · Rate limiting

**Simple explanation.** **Rate limiting** protects the system from overload and abuse by capping requests per client (token/leaky bucket). I apply it at the gateway, with clear **429** responses and quotas per tenant — essential for stability and fairness.

**Follow-ups**
- *"Where?"* — At the edge/gateway, before it hits core services.
- *"Algorithm?"* — Token bucket is common — allows bursts within a limit.

---

## SD19 · High availability

**Simple explanation.** **HA** means no single point of failure: run **multiple instances across zones/regions**, use **load balancers + health checks**, **replicate data**, and automate **failover**. I design to a target (e.g. 99.9%) and remove SPOFs to reach it.

**Follow-ups**
- *"Key idea?"* — Redundancy everywhere + automatic failover.
- *"Multi-region?"* — For strict uptime/DR, at extra cost/complexity.

---

## SD20 · Resilience patterns

**Simple explanation.** I build in **timeouts**, **retries with backoff**, **circuit breakers**, **bulkheads** (isolate failures), **fallbacks**, and **idempotency**. These stop one failing dependency from cascading into a full outage.

**Follow-ups**
- *"Circuit breaker?"* — Stop calling a failing service; fail fast and recover.
- *"Bulkhead?"* — Isolate resources so one overloaded part doesn't sink the rest.

---

## SD21 · Observability

**Simple explanation.** **Observability** = logs, metrics, traces (the three pillars) plus alerting. I instrument every service so I can see health, latency, errors and trace a request end-to-end ([file 37 Z18](37-concept-azure-services.md#z18--monitoring)). You can't operate what you can't see.

**Follow-ups**
- *"Three pillars?"* — Logs, metrics, distributed traces.
- *"Why traces?"* — Follow one request across services to find the slow/failing hop.

---

## SD22 · Security

**Simple explanation.** I design **defence in depth**: auth (OAuth/OIDC), least-privilege authz, encryption in transit and at rest, secrets in **Key Vault**, private networking, input validation, and auditing ([file 37 Z12](37-concept-azure-services.md#z12--key-vault)). Security is built in, not bolted on — vital in finance.

**Follow-ups**
- *"Layers?"* — Network, identity, app, data — each protected independently.
- *"Secrets?"* — Key Vault + managed identity — never in code/config.

---

## SD23 · CDN and edge

**Simple explanation.** A **CDN** caches static assets (and some dynamic) close to users, cutting latency and origin load. For global apps I put a CDN/edge in front for static content and route API traffic through a global entry point (Front Door).

**Follow-ups**
- *"What to cache at CDN?"* — Images, JS/CSS, static pages — rarely-changing content.
- *"Benefit?"* — Faster global loads + less origin traffic.

---

## SD24 · Finding bottlenecks

**Simple explanation.** I find bottlenecks with **metrics and load testing** — look at latency, throughput, CPU, DB, queue depth. Usually it's the **database**, an N+1 query, a hot lock, or a missing cache. I measure before optimising, never guess.

**Follow-ups**
- *"Most common bottleneck?"* — The database — optimise queries/indexes/caching first.
- *"How locate?"* — Profiling, tracing, load tests — data over intuition.

---

## SD25 · Capacity estimation

**Simple explanation.** I do **back-of-envelope** math: expected users → requests/sec → storage/bandwidth → number of servers. Rough numbers guide the design (do I need sharding? a cache? a queue?). Precision isn't the point — order of magnitude is.

**Follow-ups**
- *"Why estimate?"* — It reveals whether simple or distributed design is needed.
- *"Exact numbers?"* — No — ballpark to make architecture decisions.

---

## SD26 · Trade-offs

**Simple explanation.** Every choice has a cost: consistency vs availability, latency vs durability, simplicity vs flexibility, cost vs performance. Good design is **naming the trade-off and choosing deliberately** for the requirements — not chasing the "best" tech.

**Follow-ups**
- *"Interview signal?"* — Articulating trade-offs, not reciting tech.
- *"Example?"* — Strong consistency costs latency — I accept it for money, not for a feed.

---

## SD27 · Data flow and idempotency

**Simple explanation.** I trace **how data moves** and make operations **idempotent** (safe to retry) using keys/dedup, because retries and at-least-once delivery are normal in distributed systems ([file 49 KF14](49-concept-kafka.md#kf14--delivery-guarantees)). This prevents double-charges and duplicate effects.

**Follow-ups**
- *"Why idempotency?"* — Messages/requests get retried — duplicates must not cause harm.
- *"How?"* — Idempotency keys, dedup tables, upserts.

---

## SD28 · Cost

**Simple explanation.** I design to **requirements, not maximums** — autoscale, right-size, cache to cut DB/compute, use serverless for spiky work, and pick managed services to reduce ops cost ([file 37 Z20](37-concept-azure-services.md#z20--cost-optimization)). Over-engineering is a cost failure too.

**Follow-ups**
- *"Cost lever?"* — Autoscaling + caching + right-sizing.
- *"Over-engineering?"* — Building for scale you don't have wastes money and time.

---

## SD29 · Common pitfalls

**Simple explanation.** Pitfalls: designing before clarifying requirements, premature microservices, no caching, ignoring failure modes, single points of failure, no observability, and over-engineering. I avoid them by starting from requirements and keeping it as simple as the NFRs allow.

**Follow-ups**
- *"Biggest?"* — Jumping to tech before understanding requirements and scale.
- *"Simplicity?"* — Simplest design that meets NFRs — complexity is a cost.

---

## SD30 · My approach

**How I answer (the whole picture).** *"I design from **requirements and trade-offs**, not favourite tech. First I clarify functional needs and, crucially, the **NFRs** — scale, latency, availability, security, cost — and estimate load. Then I define APIs and data, sketch a high-level design (stateless services behind a load balancer, the right databases, caching with **Redis**, async via **queues/Kafka**), and deep-dive the hard parts. I scale **horizontally**, remove single points of failure with **replication and multi-zone HA**, add **resilience patterns** (timeouts, retries, circuit breakers, idempotency), secure it **defence-in-depth** with secrets in Key Vault, and make it **observable** with logs/metrics/traces. Throughout I name trade-offs (CAP, consistency vs latency) and keep the design **as simple as the requirements allow** — avoiding premature microservices and over-engineering. That's the exact approach I used designing TCW's platforms and the RAG assistant."*

**Follow-ups**
- *"One sentence?"* — Requirements first, trade-offs explicit, simplest design that meets the NFRs.
- *"What interviewers want?"* — Structured thinking and clear trade-offs, not memorised architectures.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| SD1 | What it is | Connect components to meet requirements |
| SD2 | FR vs NFR | NFRs drive the architecture |
| SD3 | Approach | Clarify→API/data→HLD→deep-dive→NFR→trade-offs |
| SD4 | Scalability | Grow by adding resources |
| SD5 | Vertical vs horizontal | Prefer horizontal for prod |
| SD6 | Load balancing | Spread traffic, health checks |
| SD7 | Stateless | State external; enables scaling |
| SD8 | Caching | High-impact latency/load cut |
| SD9 | Choosing DB | By access pattern; polyglot |
| SD10 | SQL vs NoSQL | Consistency/scale/data shape |
| SD11 | Replication | Availability + read scaling |
| SD12 | Sharding | Split by key for write/storage scale |
| SD13 | CAP | Pick C or A during partition |
| SD14 | Consistency | Strong for money, eventual for feeds |
| SD15 | Async | Decouple, buffer, resilience |
| SD16 | Micro vs mono | Start monolith, split when justified |
| SD17 | API design | Clear, versioned, secure, gateway |
| SD18 | Rate limiting | Protect from overload/abuse |
| SD19 | HA | Redundancy + failover, no SPOF |
| SD20 | Resilience | Timeouts, retries, breakers, idempotency |
| SD21 | Observability | Logs, metrics, traces, alerts |
| SD22 | Security | Defence in depth; Key Vault |
| SD23 | CDN | Cache static near users |
| SD24 | Bottlenecks | Measure; usually the DB |
| SD25 | Estimation | Back-of-envelope guides design |
| SD26 | Trade-offs | Name and choose deliberately |
| SD27 | Data flow | Idempotency for safe retries |
| SD28 | Cost | Design to requirements; autoscale/cache |
| SD29 | Pitfalls | Premature micro, no cache, SPOF |
| SD30 | My approach | Requirements-first, trade-offs, simple |

---

[← LLM Application Integration](46-concept-llm-application-integration.md) · [Home](README.md) · [Next → Redis Cache](48-concept-redis-cache.md)
