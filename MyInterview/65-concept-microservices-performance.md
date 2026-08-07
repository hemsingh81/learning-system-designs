# 65 · Concept: Microservices / System Architecture Performance (30 questions)

[← SQL Database Performance Tuning](64-concept-sql-performance.md) · [Home](README.md) · [Next → Back to Home](README.md)

This file explains **how I make microservices and distributed systems fast and scalable** — in simple English and real depth. I answer from project C, the TengizChevroil completion platform built as microservices on managed Azure services, where the system had to stay fast and reliable as load and services grew.

> Simple one-liner: *"System-level performance is about **scaling the right part**, **cutting chatty network calls**, **not letting one slow service take down the rest**, and **caching/async** so work happens where and when it's cheapest. I measure the whole request path first — the bottleneck is rarely where people think."*

## Concepts first — the whole idea before the questions

**Why distributed systems get slow.** In a monolith a call is a function call (nanoseconds). In microservices it's a **network call** (milliseconds) plus serialisation, and it can **fail**. So the new performance problems are: (1) **too many/chatty network hops** per request, (2) **one slow service** stalling everything (cascading failure), (3) **scaling the wrong component**, and (4) **shared bottlenecks** (a database or queue everyone hits). The tools are different from single-app tuning.

**The mental model — the request path.** A user request may fan out through a **gateway** to several services, each hitting a **database, cache, or queue**, some calling each other. Total latency = the slowest path through that graph, plus every network hop. "Performance work" = shorten the path, remove hops, cache, and make slow parts scale independently.

```
client → API gateway → service A → service B → DB/cache
                     ↘ service C (async via queue) → worker
   cut hops · cache · async the non-critical · scale the hot service · isolate failures
```

**Two levers that don't exist in a single app:** **independent scaling** (scale only the hot service, not the whole system) and **resilience** (timeouts, retries, circuit breakers, bulkheads so one failure doesn't cascade). In distributed systems, **resilience *is* performance** — an un-isolated slow dependency turns into a system-wide outage.

**The golden method (still):** **measure the end-to-end path (distributed tracing) → find the slowest hop/service → fix that one (cache, async, scale, or fix its DB) → measure again.** The bottleneck is usually one service, one database, or one chatty call — not "the architecture."

**Jump to:** [MP1 What makes it slow](#mp1--what-makes-a-distributed-system-slow) · [MP2 Measure the path](#mp2--distributed-tracing) · [MP3 Network is the cost](#mp3--the-network-is-the-new-bottleneck) · [MP4 Chatty calls](#mp4--chatty-vs-coarse-grained-calls) · [MP5 Independent scaling](#mp5--independent-scaling) · [MP6 Horizontal vs vertical](#mp6--horizontal-vs-vertical-scaling) · [MP7 Stateless services](#mp7--stateless-services) · [MP8 Load balancing](#mp8--load-balancing) · [MP9 Caching layers](#mp9--caching-layers) · [MP10 Async messaging](#mp10--async-messaging)
> [MP11 Sync vs async](#mp11--sync-vs-async-communication) · [MP12 API gateway](#mp12--api-gateway) · [MP13 Circuit breaker](#mp13--circuit-breaker-and-timeouts) · [MP14 Bulkhead](#mp14--bulkhead-isolation) · [MP15 Backpressure](#mp15--backpressure-and-queues) · [MP16 Data per service](#mp16--database-per-service) · [MP17 Saga](#mp17--saga-and-distributed-transactions) · [MP18 Eventual consistency](#mp18--eventual-consistency) · [MP19 CQRS](#mp19--cqrs-at-scale) · [MP20 Idempotency](#mp20--idempotency)
> [MP21 Autoscaling](#mp21--autoscaling) · [MP22 Cold start](#mp22--cold-start-and-warmup) · [MP23 N+1 across services](#mp23--n1-across-services) · [MP24 Serialization/protocol](#mp24--protocol-and-serialisation) · [MP25 Observability](#mp25--observability-slis-slos) · [MP26 Managed services](#mp26--managed-services-and-performance) · [MP27 Right-sizing](#mp27--right-sizing-and-cost) · [MP28 Anti-patterns](#mp28--performance-anti-patterns) · [MP29 A real fix](#mp29--a-real-fix-story) · [MP30 My approach](#mp30--my-approach) · [Section index](#section-index)

---

## MP1 · What makes a distributed system slow?

**Simple explanation.** Four big causes: **too many network hops** per request (chatty calls), **one slow service** stalling the chain (or cascading failure), **scaling the wrong component**, and a **shared bottleneck** (a database or queue everyone hammers). I trace the whole path to see which one — the fix is different for each.

**Architect's view:** "The architecture is slow" almost always means "one service or one database is slow, and nothing isolates it."

**Follow-ups**
- *"First question?"* — Where in the request path is the time going? Trace it.
- *"Most common?"* — A chatty call pattern or one shared, overloaded database.

---

## MP2 · Distributed tracing

**Simple explanation.** In microservices you can't profile one process — you need **distributed tracing** (OpenTelemetry / Application Insights) that follows a request across services with a **correlation id**, showing time spent in each hop. It turns "it's slow somewhere" into "service B's DB call is 80% of the latency."

**Follow-ups**
- *"Correlation id?"* — A trace id propagated through every call so you can stitch the timeline.
- *"What it reveals?"* — The one hop/service that dominates latency.

---

## MP3 · The network is the new bottleneck

**Simple explanation.** A monolith method call is nanoseconds; a service-to-service call is **milliseconds** plus serialisation, and it can fail or time out. So the golden rule is **make fewer, coarser calls**. Every hop you remove is latency and a failure mode removed.

**Follow-ups**
- *"Design implication?"* — Draw service boundaries so common operations don't cross many services.
- *"Cost of a hop?"* — Latency + serialisation + a new way to fail.

---

## MP4 · Chatty vs coarse-grained calls

**Simple explanation.** A **chatty** design makes many small calls per request (e.g. loop calling a service per item — the distributed N+1). A **coarse-grained** design fetches what's needed in **one call** (batch endpoint, or aggregate in a BFF/gateway). Fewer, bigger calls beat many tiny ones across a network.

**Follow-ups**
- *"Fix a chatty API?"* — Add a batch endpoint or aggregate server-side (BFF).
- *"BFF?"* — Backend-for-frontend composes several services into one client call.

---

## MP5 · Independent scaling

**Simple explanation.** The biggest microservices win: **scale only the hot service**, not the whole app. On the completion platform, the read/reporting service could scale out under load while low-traffic services stayed small — efficient use of resources a monolith can't match.

**Follow-ups**
- *"Prerequisite?"* — Stateless services so you can add instances freely.
- *"Cost angle?"* — Pay for capacity only where it's needed.

---

## MP6 · Horizontal vs vertical scaling

**Simple explanation.** **Vertical** = a bigger machine (limited, single point). **Horizontal** = more instances behind a load balancer (scales further, more resilient). Microservices favour **horizontal** scaling of stateless services. I scale out first, up only when a component truly needs a bigger box.

**Follow-ups**
- *"Limit of vertical?"* — One machine's ceiling + single point of failure.
- *"Horizontal need?"* — Statelessness + a load balancer + shared/state stores.

---

## MP7 · Stateless services

**Simple explanation.** A **stateless** service keeps no per-user state in memory between requests — any instance can handle any request. This is what makes horizontal scaling and autoscaling work. Session/state goes to a **shared store** (Redis, DB), not the instance.

**Follow-ups**
- *"Where does state go?"* — Redis/DB — externalise it ([file 48](48-concept-redis-cache.md)).
- *"Sticky sessions?"* — Avoid — they break clean horizontal scaling.

---

## MP8 · Load balancing

**Simple explanation.** A **load balancer** spreads requests across instances so no single one is overwhelmed, and routes around unhealthy instances (with **health checks**). It's the front door to horizontal scale. On Azure this is managed (App Gateway / Load Balancer / ingress).

**Follow-ups**
- *"Algorithm?"* — Round-robin / least-connections; health checks remove bad instances.
- *"Auto-recovery?"* — Failing instances are drained and replaced.

---

## MP9 · Caching layers

**Simple explanation.** Caching removes load and latency at every layer: **CDN** (static/edge), **API/response cache**, **distributed cache (Redis)** for hot data shared across instances, and **DB result cache**. The cheapest call is the one you don't make. I cache aggressively where data tolerates slight staleness.

**Follow-ups**
- *"Which layer first?"* — Closest to the user that's safe — CDN/edge, then Redis.
- *"Shared cache?"* — Redis so all instances see the same cached data.

---

## MP10 · Async messaging

**Simple explanation.** Instead of a caller waiting for slow downstream work, services communicate via a **message queue / event bus** (Kafka, Service Bus). The producer returns immediately; a consumer processes later. This **decouples** services, **absorbs spikes**, and keeps the user-facing path fast ([file 49](49-concept-kafka.md)).

**Follow-ups**
- *"Benefit?"* — Decoupling, buffering spikes, resilience (retry from the queue).
- *"When not?"* — When the caller genuinely needs an immediate answer (use sync).

---

## MP11 · Sync vs async communication

**Simple explanation.** **Sync** (HTTP/gRPC) is simple and immediate but couples caller to callee's availability and speed. **Async** (events/queues) decouples and buffers but is eventually consistent. I use **sync for read/immediate needs** and **async for workflows, spikes and cross-service side-effects**.

**Follow-ups**
- *"Rule of thumb?"* — Sync when the user waits for the result; async for everything else.
- *"Overusing sync?"* — Chains of sync calls multiply latency and failure risk.

---

## MP12 · API gateway

**Simple explanation.** An **API gateway** is the single entry point: routing, auth, rate limiting, and **response aggregation** (compose several services into one client call). It cuts client round-trips and centralises cross-cutting concerns — improving both performance and security.

**Follow-ups**
- *"Aggregation win?"* — One client call instead of the client making five — fewer round-trips.
- *"Risk?"* — It can become a bottleneck/SPOF — scale it, keep it thin.

---

## MP13 · Circuit breaker and timeouts

**Simple explanation.** Every remote call needs a **timeout** (never wait forever) and a **circuit breaker** — after repeated failures, stop calling a dead service and fail fast, then test-recover. This stops one slow/failing service from stalling and **cascading** across the system. Resilience *is* performance here.

**Follow-ups**
- *"No timeout danger?"* — Threads pile up waiting → caller dies too → cascade.
- *"With retry?"* — Retry transient faults with backoff, behind a circuit breaker ([file 60 DP24](60-concept-design-principles.md#dp24--circuit-breaker)).

---

## MP14 · Bulkhead isolation

**Simple explanation.** **Bulkheads** (like ship compartments) isolate resources so one overloaded dependency can't sink the whole service — e.g. separate connection/thread pools per downstream. If one dependency floods, only its pool is affected; the rest keep serving.

**Follow-ups**
- *"Analogy?"* — A ship's sealed compartments — one flooded, the ship floats.
- *"Implementation?"* — Separate pools/limits per dependency (Polly bulkhead).

---

## MP15 · Backpressure and queues

**Simple explanation.** When work arrives faster than it can be processed, unbounded queues grow until things fall over. **Backpressure** means signalling "slow down" (or shedding load / bounding queues) so the system degrades gracefully instead of collapsing. Queues absorb spikes; limits prevent meltdown.

**Follow-ups**
- *"Unbounded queue risk?"* — Memory blow-up + ever-growing latency — bound it.
- *"Load shedding?"* — Reject/deprioritise excess work to protect the core.

---

## MP16 · Database-per-service

**Simple explanation.** Each microservice **owns its data** (its own database) so services don't fight over one shared DB and can scale/tune independently. It avoids the shared-DB bottleneck but means no cross-service joins — you compose data via APIs/events instead.

**Follow-ups**
- *"Cost?"* — No cross-DB joins; data duplication; eventual consistency.
- *"Why still do it?"* — Independent scaling/tuning + no shared bottleneck.

---

## MP17 · Saga and distributed transactions

**Simple explanation.** You can't use one ACID transaction across services. A **saga** coordinates a multi-service operation as a series of local transactions with **compensating actions** to undo on failure. It trades strong consistency for availability and scale — the distributed reality.

**Follow-ups**
- *"Orchestration vs choreography?"* — Central coordinator vs services reacting to events — pick by complexity.
- *"Compensation?"* — An action that semantically undoes a completed step.

---

## MP18 · Eventual consistency

**Simple explanation.** In distributed systems, data becomes consistent **soon**, not instantly (CAP trade-off). I design for it: show "processing" states, make reads tolerant of slight lag, and use events to propagate changes. Chasing strong consistency everywhere kills scale and availability.

**Follow-ups**
- *"User impact?"* — A change may take a moment to appear — design UI for it.
- *"When strong consistency?"* — Money/critical invariants — keep those in one service/transaction.

---

## MP19 · CQRS at scale

**Simple explanation.** **CQRS** separates the **write** model from a **read** model optimised for queries — often a pre-computed, denormalised read store updated via events. Reads scale independently and are fast; writes stay clean. Great when reads vastly outnumber writes (reporting).

**Follow-ups**
- *"Read store?"* — A query-optimised projection (even a different DB) kept fresh by events.
- *"Cost?"* — More moving parts + eventual consistency — use when read/write needs diverge ([file 60 DP23](60-concept-design-principles.md#dp23--cqrs)).

---

## MP20 · Idempotency

**Simple explanation.** With retries and at-least-once messaging, the same request can arrive twice. **Idempotent** operations produce the same result no matter how many times they run (via idempotency keys / dedup). Essential so retries (a performance/resilience tool) don't double-charge or double-create.

**Follow-ups**
- *"How?"* — Idempotency key + dedup store; upserts instead of blind inserts.
- *"Why it matters for perf?"* — It lets you retry safely — retries are core to resilience.

---

## MP21 · Autoscaling

**Simple explanation.** **Autoscaling** adds/removes instances automatically based on load (CPU, queue length, request rate). Combined with stateless services it handles spikes without over-provisioning. On managed Azure (App Service/AKS/Container Apps) this is built in — scale out on the morning spike, back down after.

**Follow-ups**
- *"Scale on what?"* — The right signal — often queue depth or RPS, not just CPU.
- *"Watch out?"* — Scale-out lag + cold starts; pre-warm for known spikes.

---

## MP22 · Cold start and warmup

**Simple explanation.** New instances (or serverless functions scaling from zero) have a **cold start** — the first request is slow. I mitigate with **min instances / keep-alive**, faster startup (AOT/ReadyToRun), and pre-warming before known peaks so users don't hit the cold path.

**Follow-ups**
- *"Serverless trade-off?"* — Cheap idle vs cold-start latency — use min-instances for hot paths.
- *"Startup speed?"* — Trim dependencies, AOT, lazy-init non-critical parts.

---

## MP23 · N+1 across services

**Simple explanation.** The distributed N+1: a service loops calling another service once per item — dozens of network round-trips per request. I fix it with a **batch endpoint**, **aggregation** in a BFF/gateway, or by publishing the needed data via events so the caller has it locally.

**Follow-ups**
- *"Detect?"* — Tracing shows a burst of identical downstream calls per request.
- *"Fix?"* — Batch/aggregate, or replicate the data via events (read model).

---

## MP24 · Protocol and serialisation

**Simple explanation.** For high-throughput internal calls, the **protocol** matters: **gRPC** (HTTP/2 + binary Protobuf) is faster and lighter than JSON-over-HTTP for service-to-service. I use gRPC for chatty internal hops and keep JSON/REST at the public edge for compatibility.

**Follow-ups**
- *"gRPC where?"* — Internal, high-frequency service-to-service calls.
- *"REST where?"* — Public APIs / browser clients — compatibility and simplicity.

---

## MP25 · Observability (SLIs, SLOs)

**Simple explanation.** You can't tune what you can't see. **Observability** = metrics + logs + traces, tied to **SLIs** (indicators like p99 latency, error rate) and **SLOs** (targets). I set SLOs, alert on them, and use traces to find the offending service — performance work is driven by these numbers.

**Follow-ups**
- *"Golden signals?"* — Latency, traffic, errors, saturation.
- *"Why SLOs?"* — They define "fast enough" and focus effort on what breaches.

---

## MP26 · Managed services and performance

**Simple explanation.** On the completion platform (C) I built microservices on **managed Azure services** (managed databases, queues, container hosting). Managed services handle scaling, patching, HA and much tuning — so the team optimises **application** behaviour, not infrastructure plumbing. Less ops, more reliable scale.

**Follow-ups**
- *"Trade-off?"* — Less low-level control / possible cost — but far less ops burden and faster, safer scaling.
- *"Cross-link?"* — The managed-Azure decision ([CC1](55-case-study-c-completion-platform.md)).

---

## MP27 · Right-sizing and cost

**Simple explanation.** Performance and **cost** are linked. I right-size instances/warehouses, autoscale to demand, cache to cut compute, and shut down idle resources. Throwing hardware at a wasteful service just costs more — I fix the bottleneck first, then scale efficiently.

**Follow-ups**
- *"Perf vs cost?"* — Optimise the bottleneck, then scale only what's needed — both improve.
- *"Idle cost?"* — Auto-suspend/scale-to-zero non-critical workloads.

---

## MP28 · Performance anti-patterns

**Simple explanation.** Common traps: **chatty/sync call chains** (latency + cascade), **no timeouts/circuit breakers** (one slow service kills all), a **shared database** everyone hits, **stateful services** blocking scale, **unbounded queues**, and **distributed N+1**. Each is a known distributed-systems failure mode.

**Follow-ups**
- *"Most dangerous?"* — Sync chains with no timeouts — cascading failure.
- *"Shared DB?"* — Recreates the monolith bottleneck — own data per service.

---

## MP29 · A real fix story

**The story.** On the completion platform (C), a key user flow slowed under load. **Distributed tracing** showed two problems: a service was making a **chatty per-item call** to another service (distributed N+1), and a **shared reporting query** on one database was the real bottleneck during peaks. Fixes, in order: added a **batch endpoint** to collapse the per-item calls into one, moved the heavy read work behind a **Redis cache** + a **read model** (CQRS-style), added **timeouts + circuit breakers** so a slow dependency couldn't cascade, and enabled **autoscaling** on the hot (stateless) service only. Re-traced under load — fewer hops, cached reads, isolated failures, and the flow stayed fast at peak.

**Lesson.** *"I didn't rewrite the architecture — tracing pointed at one chatty call and one shared query. Fix the hop, cache the read, isolate the failure, scale the hot service."*

**Follow-ups**
- *"Single biggest win?"* — The batch endpoint — many network hops became one.
- *"Cross-link?"* — The completion-platform decisions ([CC1–CC6](55-case-study-c-completion-platform.md)).

---

## MP30 · My approach

**How I answer (the whole picture).** *"At the system level I tune with **distributed tracing** first — the bottleneck is almost always one service, one shared database, or one chatty call, not 'the architecture.' Then I **cut network hops** (batch/aggregate, kill the distributed N+1), **cache** at the right layer (CDN → Redis → read models/CQRS), and move non-critical work to **async messaging** so the user path stays fast and spikes are absorbed. I make services **stateless** so I can **scale the hot one independently** with **autoscaling** behind a **load balancer**, and I treat **resilience as performance** — **timeouts, retries with backoff, circuit breakers and bulkheads** so one slow dependency never cascades. I design for **eventual consistency** and **idempotency** because retries and async are core. Building on **managed Azure services** on the completion platform let the team focus on these application-level wins rather than infrastructure. Then I **measure the whole path again** to prove it — and I never scale a wasteful service before fixing its bottleneck."*

**Follow-ups**
- *"One lever if forced?"* — Tracing — it tells me exactly which hop/service to fix.
- *"Biggest system-level win usually?"* — Removing chatty calls + caching the hot read; isolating failures so slowness doesn't cascade.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| MP1 | What's slow | Hops, one slow service, wrong scaling, shared bottleneck |
| MP2 | Tracing | Follow the request across services |
| MP3 | Network cost | Fewer, coarser calls |
| MP4 | Chatty vs coarse | Batch/aggregate over many small calls |
| MP5 | Independent scaling | Scale only the hot service |
| MP6 | Horizontal vs vertical | Scale out (stateless) first |
| MP7 | Stateless | Externalise state to Redis/DB |
| MP8 | Load balancing | Spread load; health-check out bad nodes |
| MP9 | Caching layers | CDN → Redis → DB result cache |
| MP10 | Async messaging | Decouple, buffer spikes |
| MP11 | Sync vs async | Sync when user waits; async otherwise |
| MP12 | API gateway | Route, secure, aggregate calls |
| MP13 | Circuit breaker | Timeouts + fail fast stop cascades |
| MP14 | Bulkhead | Isolate resources per dependency |
| MP15 | Backpressure | Bound queues; shed load gracefully |
| MP16 | DB-per-service | No shared-DB bottleneck |
| MP17 | Saga | Coordinate multi-service txns + compensate |
| MP18 | Eventual consistency | Design for lag; strong only where needed |
| MP19 | CQRS | Separate, fast, scalable read model |
| MP20 | Idempotency | Safe retries; no duplicates |
| MP21 | Autoscaling | Scale to demand on the right signal |
| MP22 | Cold start | Min instances, fast startup, pre-warm |
| MP23 | Distributed N+1 | Batch/aggregate cross-service calls |
| MP24 | Protocol | gRPC internal, REST at the edge |
| MP25 | Observability | Metrics+logs+traces; SLIs/SLOs |
| MP26 | Managed services | Focus on app, not infra plumbing |
| MP27 | Right-sizing | Fix bottleneck, then scale efficiently |
| MP28 | Anti-patterns | Sync chains, no timeouts, shared DB |
| MP29 | Real fix | Batch + cache + isolate + autoscale |
| MP30 | My approach | Trace → cut hops/cache/async/isolate/scale → re-measure |

---

[← SQL Database Performance Tuning](64-concept-sql-performance.md) · [Home](README.md) · [Next → .NET & C# What's New](66-concept-dotnet-whats-new.md)
