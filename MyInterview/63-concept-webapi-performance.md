# 63 · Concept: Web API / C# Performance Tuning (30 questions)

[← Angular Performance Tuning](62-concept-angular-performance.md) · [Home](README.md) · [Next → SQL Database Performance Tuning](64-concept-sql-performance.md)

This file explains **how I make ASP.NET Core Web APIs (and C#) fast** — in simple English and real depth. I answer from project A, where TCW's .NET Core APIs feed the reporting platform and must respond quickly under morning load, when everyone pulls reports at once.

> Simple one-liner: *"API speed is mostly **not doing work** — async I/O so threads aren't blocked, caching so I don't recompute, fewer/cheaper database calls, and small efficient payloads. I measure first, fix the biggest bottleneck, then measure again."*

## Concepts first — the whole idea before the questions

**Why APIs get slow.** A slow API is almost always one of: (1) **blocked threads** waiting on I/O (database, HTTP, disk) instead of using **async**, (2) **too many or slow database calls** (N+1, missing indexes, over-fetching), (3) **repeated work** that should be **cached**, or (4) **big payloads/serialisation** cost. Fix the right one and the API flies.

**The mental model — a request's journey.** A request enters **Kestrel**, flows through the **middleware pipeline**, hits a **controller/endpoint**, which calls **services** and the **database**, serialises a response, and returns. Time is spent *waiting* (I/O) or *computing* (serialisation, business logic). Async fixes waiting; caching and fewer calls fix computing/round-trips.

```
request → Kestrel → middleware → endpoint → service → DB/HTTP (I/O wait)
                                     ↓ serialise response → client
   async keeps threads free during I/O; cache avoids repeating work
```

**Throughput vs latency.** **Latency** = how long one request takes. **Throughput** = how many requests/sec the service handles. **Async** mainly improves throughput/scalability (threads serve other requests while one waits on I/O); caching and query tuning improve both.

**The golden method (never changes):** **measure → find the biggest bottleneck → fix that one → measure again.** Tools: Application Insights, load tests (k6/JMeter), a profiler (dotnet-trace/PerfView), and DB query stats. Never guess.

**Jump to:** [WP1 What makes an API slow](#wp1--what-makes-a-web-api-slow) · [WP2 Measure first](#wp2--how-do-you-measure-api-performance) · [WP3 Async/await](#wp3--async-io-and-thread-pool) · [WP4 Async pitfalls](#wp4--async-pitfalls) · [WP5 N+1](#wp5--the-n1-problem) · [WP6 EF Core tuning](#wp6--ef-core-query-tuning) · [WP7 AsNoTracking](#wp7--asnotracking-and-projection) · [WP8 Caching](#wp8--caching-strategies) · [WP9 Redis](#wp9--distributed-cache-redis) · [WP10 Response caching](#wp10--response-and-output-caching)
> [WP11 Payload size](#wp11--payload-size-and-compression) · [WP12 Pagination](#wp12--pagination) · [WP13 Serialisation](#wp13--serialisation-cost) · [WP14 Connection pooling](#wp14--connection-pooling) · [WP15 HttpClientFactory](#wp15--httpclientfactory) · [WP16 Resilience](#wp16--resilience-retry-circuit-breaker) · [WP17 Parallelism](#wp17--parallel-and-batched-work) · [WP18 Memory/GC](#wp18--memory-and-gc) · [WP19 Span/pooling](#wp19--span-and-object-pooling) · [WP20 Background work](#wp20--offload-with-background-work)
> [WP21 Rate limiting](#wp21--rate-limiting-and-throttling) · [WP22 Minimal APIs](#wp22--minimal-apis-and-startup) · [WP23 AOT/startup](#wp23--startup-and-aot) · [WP24 Logging cost](#wp24--logging-cost) · [WP25 DbContext lifetime](#wp25--dbcontext-lifetime-pitfalls) · [WP26 Streaming](#wp26--streaming-large-responses) · [WP27 Load testing](#wp27--load-testing) · [WP28 Anti-patterns](#wp28--performance-anti-patterns) · [WP29 A real fix](#wp29--a-real-fix-story) · [WP30 My approach](#wp30--my-approach) · [Section index](#section-index)

---

## WP1 · What makes a Web API slow?

**Simple explanation.** Usually one of four: **blocked threads** (sync I/O instead of async), **database problems** (N+1, missing indexes, over-fetching), **repeated work** that should be **cached**, or **large payloads/serialisation**. I identify which one before changing code — the fixes are different.

**Architect's view:** Most "the API is slow" tickets are really "the database call is slow" or "we call the DB too many times."

**Follow-ups**
- *"First question?"* — Slow per request (latency) or falls over under load (throughput)?
- *"Most common cause?"* — Database round-trips (N+1) and missing async.

---

## WP2 · How do you measure API performance?

**Simple explanation.** I never guess. **Application Insights** (or OpenTelemetry) for end-to-end traces and slow dependencies, **load tests** (k6/JMeter) for throughput, a **profiler** (dotnet-trace/PerfView) for CPU/allocations, and **DB query stats** for slow queries. Measure → fix biggest → re-measure.

**Follow-ups**
- *"Where's the time going?"* — Distributed trace shows DB vs code vs external calls.
- *"Prod vs lab?"* — Watch real telemetry; load-test in a prod-like environment.

---

## WP3 · Async I/O and the thread pool

**Simple explanation.** **async/await** frees the thread while waiting on I/O (DB, HTTP, disk), so it can serve other requests instead of blocking. This dramatically improves **throughput** under load. I make every I/O call async all the way down — no blocking.

```csharp
public async Task<IActionResult> Get() => Ok(await _repo.GetAsync());
```

**Follow-ups**
- *"Async = faster single request?"* — Not really — it improves scalability (more concurrent requests), not one call's latency.
- *"Why threads matter?"* — Blocked threads starve the pool; requests queue and time out.

---

## WP4 · Async pitfalls

**Simple explanation.** The big one is **sync-over-async** — `.Result`/`.Wait()` blocks a thread and can deadlock. Others: `async void`, not passing `CancellationToken`, and unnecessary `Task.Run` on the server. I go async end-to-end, return `Task`, and flow cancellation tokens.

**Follow-ups**
- *"`.Result` danger?"* — Deadlocks and thread starvation — never block on async.
- *"CancellationToken?"* — Pass it so abandoned requests stop doing work.

---

## WP5 · The N+1 problem

**Simple explanation.** **N+1** is one query for a list, then one extra query *per row* for related data — hundreds of round-trips. It's the most common API killer. I fix it by **eager loading** (`Include`) or a **projection/join** that fetches everything in one query.

**Follow-ups**
- *"Symptom?"* — A loop that lazy-loads a navigation property each iteration.
- *"Fix?"* — `Include`/`ThenInclude` or a single projected query ([file 64](64-concept-sql-performance.md)).

---

## WP6 · EF Core query tuning

**Simple explanation.** EF Core is convenient but can generate slow SQL. I **project** to just the columns I need (`Select`), avoid loading whole entities, watch for client-side evaluation, use **compiled queries** for hot paths, and always check the **generated SQL** with logging.

**Follow-ups**
- *"See the SQL?"* — Enable EF query logging / `ToQueryString()`.
- *"Client-side eval trap?"* — A LINQ op EF can't translate pulls all rows then filters in memory — avoid.

---

## WP7 · AsNoTracking and projection

**Simple explanation.** For **read-only** queries, **`AsNoTracking()`** skips EF's change tracking — less memory, faster. Even better, **project** to a DTO (`Select(x => new Dto{…})`) so EF fetches only needed columns and doesn't materialise full entities. Read paths should be lean.

```csharp
var dtos = await db.Reports.AsNoTracking()
    .Select(r => new ReportDto { r.Id, r.Name }).ToListAsync();
```

**Follow-ups**
- *"When tracking?"* — Only when you'll update entities in that request.
- *"Biggest read win?"* — Projection to a slim DTO — less data, less work.

---

## WP8 · Caching strategies

**Simple explanation.** The fastest work is work you don't repeat. I cache expensive, rarely-changing results: **in-memory** (`IMemoryCache`) for single-instance/hot data, **distributed** (Redis) for shared/scaled-out data. Cache-aside is my default: check cache → miss → load → store.

**Follow-ups**
- *"What to cache?"* — Expensive + frequently read + tolerant of slight staleness.
- *"Invalidation?"* — TTL, or evict on write — the hard part; keep it explicit.

---

## WP9 · Distributed cache (Redis)

**Simple explanation.** With multiple API instances, an in-memory cache isn't shared. **Redis** is a fast, shared cache all instances see — consistent data, and it survives restarts. I use it for session, hot lookups, and cache-aside across a scaled-out service ([file 48](48-concept-redis-cache.md)).

**Follow-ups**
- *"In-memory vs Redis?"* — In-memory is faster but per-instance; Redis is shared/consistent.
- *"Serialization cost?"* — Real — keep cached objects small; use efficient formats.

---

## WP10 · Response and output caching

**Simple explanation.** **Output caching** stores the whole response for identical requests so the endpoint isn't re-executed; **response caching** adds HTTP cache headers so clients/proxies cache. For read-heavy, cacheable endpoints this is a huge, cheap win.

**Follow-ups**
- *"Vary by?"* — Cache per query/route/header key so users get the right data.
- *"When not?"* — Personalised or fast-changing responses.

---

## WP11 · Payload size and compression

**Simple explanation.** Smaller responses travel and parse faster. I enable **response compression** (gzip/brotli), return only needed fields (DTOs), avoid huge nested graphs, and page large lists. Less bytes = lower latency, especially on slow networks.

**Follow-ups**
- *"Compression cost?"* — A little CPU for much less bandwidth — usually worth it.
- *"Over-fetching?"* — Return DTOs, not full entities with everything.

---

## WP12 · Pagination

**Simple explanation.** Never return unbounded lists. **Paginate** (offset or keyset/cursor) so each response is small and predictable. **Keyset pagination** stays fast on deep pages where `OFFSET` gets slow. Protects both the API and the database.

**Follow-ups**
- *"Offset vs keyset?"* — Keyset (WHERE id > last) scales to deep pages; offset degrades.
- *"Default page size?"* — Cap it — don't let a client request everything.

---

## WP13 · Serialisation cost

**Simple explanation.** JSON serialisation of large/deep objects costs CPU and allocations. I use **System.Text.Json** (fast), slim DTOs, avoid circular graphs, and consider **source-generated** serialisation for hot paths. For very high throughput, consider compact formats.

**Follow-ups**
- *"System.Text.Json vs Newtonsoft?"* — System.Text.Json is faster/lower-allocation — default.
- *"Source generation?"* — Precompiled serializers cut startup and per-call cost.

---

## WP14 · Connection pooling

**Simple explanation.** Opening a DB connection is expensive; **connection pooling** (on by default with ADO.NET/EF) reuses connections. I make sure I'm not disabling it, I keep connections short-lived (open late, dispose early), and size the pool for load.

**Follow-ups**
- *"Pool exhaustion?"* — Leaked/held-open connections starve the pool — always dispose.
- *"DbContext + pool?"* — Scoped DbContext + `AddDbContextPool` can reduce allocation cost.

---

## WP15 · HttpClientFactory

**Simple explanation.** Creating a `new HttpClient` per call leaks sockets (**socket exhaustion**). **`IHttpClientFactory`** pools and rotates handlers correctly, and lets me add resilience (retry/circuit-breaker) via Polly. Always use it for outbound HTTP (e.g. Aladdin calls).

**Follow-ups**
- *"Why not `new HttpClient()`?"* — Sockets stay in TIME_WAIT; you run out under load.
- *"Typed clients?"* — Yes — clean, injectable, resilient.

---

## WP16 · Resilience (retry, circuit breaker)

**Simple explanation.** Under load, dependencies wobble. I add **timeouts**, **retries with backoff** (for transient faults), and a **circuit breaker** (Polly) so one failing dependency doesn't cascade. Resilience *is* performance — it stops slowness turning into outage.

**Follow-ups**
- *"Retry everything?"* — Only idempotent, transient failures — with backoff + jitter.
- *"Circuit breaker?"* — Trip after repeated failures; fail fast; test-recover ([file 60 DP24](60-concept-design-principles.md#dp24--circuit-breaker)).

---

## WP17 · Parallel and batched work

**Simple explanation.** When a request needs several independent I/O calls, I run them **in parallel** (`Task.WhenAll`) instead of sequentially (kills waterfalls), and **batch** DB/remote calls where possible. This cuts latency without extra threads (it's I/O overlap).

**Follow-ups**
- *"Parallel CPU work?"* — Different — `Parallel.For`/PLINQ for CPU-bound; WhenAll for I/O-bound.
- *"Risk?"* — Overloading a dependency — bound concurrency.

---

## WP18 · Memory and GC

**Simple explanation.** Excess allocations pressure the **garbage collector**, causing pauses and CPU. I reduce allocations on hot paths (avoid needless LINQ chains, big temporary lists, string concatenation), use **Server GC** for throughput, and profile allocations. On the ETL side, memory spikes were a real issue I fixed by streaming.

**Follow-ups**
- *"Server vs Workstation GC?"* — Server GC for high-throughput services (multi-core, parallel).
- *"Find allocations?"* — dotnet-trace/PerfView allocation profiling.

---

## WP19 · Span and object pooling

**Simple explanation.** For very hot paths, **`Span<T>`/`Memory<T>`** process data without allocating, and **object/array pooling** (`ArrayPool`, `ObjectPool`) reuses buffers instead of allocating per request. Advanced, but powerful for parsing/serialisation-heavy services.

**Follow-ups**
- *"When worth it?"* — Proven hot path with high allocation — not everywhere.
- *"StringBuilder/pooling?"* — Reuse buffers to cut GC on repetitive work.

---

## WP20 · Offload with background work

**Simple explanation.** Don't make the caller wait for slow, non-critical work (emails, report generation, exports). I **offload** to a background service/queue (hosted service, Azure Functions, Service Bus) and return quickly. The request stays fast; heavy work runs out-of-band.

**Follow-ups**
- *"Fire-and-forget in a controller?"* — Risky — use a proper queue/hosted service, not a detached task.
- *"Pattern?"* — Accept → enqueue → 202 + status endpoint.

---

## WP21 · Rate limiting and throttling

**Simple explanation.** To protect throughput and fairness, I add **rate limiting** (built into ASP.NET Core) so a noisy client can't starve others or overload the DB. It keeps the service responsive under abuse or spikes — controlled degradation beats collapse.

**Follow-ups**
- *"Algorithms?"* — Token/sliding-window/concurrency limiters — pick per endpoint.
- *"Return?"* — 429 with Retry-After so clients back off.

---

## WP22 · Minimal APIs and startup

**Simple explanation.** **Minimal APIs** have less overhead per request than full MVC for simple endpoints, and start faster. For high-throughput microservices I often use them. Fewer layers = less allocation and dispatch cost on the hot path.

**Follow-ups**
- *"Always minimal?"* — No — controllers still shine for large, structured APIs.
- *"Perf gap?"* — Small per request but adds up at high RPS.

---

## WP23 · Startup and AOT

**Simple explanation.** Cold starts hurt serverless and autoscaling. **ReadyToRun**/**Native AOT** compile ahead of time for faster startup and smaller memory, and **source generators** cut reflection cost. For Functions/containers that scale from zero, this improves the first-request latency.

**Follow-ups**
- *"AOT trade-off?"* — Some reflection-based libs don't work; test compatibility.
- *"Warmups?"* — Keep-alive/pre-warm to avoid cold starts on critical paths.

---

## WP24 · Logging cost

**Simple explanation.** Over-logging (especially in hot loops, or expensive string interpolation for logs that are filtered out) costs CPU and I/O. I use **structured logging** with level checks, log **templates** (not pre-built strings), and sample high-volume logs. Good logging shouldn't slow the service.

**Follow-ups**
- *"Interpolation trap?"* — `LogDebug($"{expensive}")` builds the string even if Debug is off — use templates.
- *"Hot path?"* — Minimal logging; sample/aggregate instead.

---

## WP25 · DbContext lifetime pitfalls

**Simple explanation.** EF's `DbContext` is **not thread-safe** and should be **scoped** (one per request). Sharing it across threads/requests or capturing it in a singleton causes errors and leaks. Parallel queries need **separate** contexts. Right lifetime = correctness *and* performance.

**Follow-ups**
- *"Parallel EF queries?"* — Use separate DbContext instances per parallel operation.
- *"Singleton DbContext?"* — Never — scoped per request; consider pooling.

---

## WP26 · Streaming large responses

**Simple explanation.** For large exports, don't build the whole payload in memory — **stream** it (`IAsyncEnumerable`, streaming JSON, or chunked file responses) so memory stays flat and the client starts receiving sooner. This fixed the ETL memory spikes on A.

**Follow-ups**
- *"IAsyncEnumerable?"* — Stream rows as they're produced — constant memory.
- *"Big files?"* — Stream from storage; don't load fully into memory.

---

## WP27 · Load testing

**Simple explanation.** I validate performance with **load tests** (k6/JMeter/NBomber) in a prod-like environment — measuring latency percentiles (p95/p99), throughput and error rate under realistic concurrency. This finds thread-pool starvation, DB limits and cache gaps *before* users do.

**Follow-ups**
- *"Which percentile?"* — p95/p99 — averages hide the pain users feel.
- *"What breaks first?"* — Often DB connections or a sync-over-async path.

---

## WP28 · Performance anti-patterns

**Simple explanation.** Common traps: **sync-over-async** (`.Result`), **N+1** queries, **`new HttpClient()`** per call, loading full entities when a DTO would do, no caching on read-heavy endpoints, unbounded lists, and heavy logging in hot paths. Each is a known, avoidable killer.

**Follow-ups**
- *"Most damaging?"* — Sync-over-async (thread starvation) and N+1 (DB flood).
- *"Quick audit?"* — Grep for `.Result`, `new HttpClient(`, and missing `AsNoTracking`.

---

## WP29 · A real fix story

**The story.** On TCW (A), a report API was slow under morning load. **App Insights** showed most time in the database, with hundreds of small queries — a classic **N+1** — plus the endpoint re-computed the same reference data every call. Fixes, in order: replaced the N+1 with a single **projected query** (`AsNoTracking` + `Select` DTO), **cached** the reference data in **Redis** (cache-aside), made the whole path **async**, and added **response compression** + **pagination**. Re-measured under load — latency dropped sharply and throughput rose; the morning spike no longer timed out.

**Lesson.** *"I didn't scale the servers — I stopped doing needless work. Fewer DB round-trips + caching beat throwing hardware at it."*

**Follow-ups**
- *"Single biggest win?"* — Killing the N+1 — hundreds of queries became one.
- *"Cross-link?"* — Same method as the backend deep dive ([PB1–PB2](19-performance-deep-dive.md)).

---

## WP30 · My approach

**How I answer (the whole picture).** *"API performance is mostly about **not doing work**. I **measure first** with Application Insights, a profiler and load tests to see whether the cost is I/O waiting, the database, repeated work, or payload size. Then: I make everything **async end-to-end** so threads aren't blocked (throughput), I kill **N+1** and tune **EF Core** with `AsNoTracking` + **projection** (fewer, cheaper queries), I **cache** expensive read-heavy data in **Redis** (cache-aside) and use **output caching**, and I shrink responses with **DTOs, compression and pagination**. For robustness under load I add **HttpClientFactory**, **timeouts/retries/circuit breakers**, **rate limiting** and **streaming** for big payloads, and I offload slow non-critical work to **background jobs**. Then I **measure again** to prove it. On TCW that approach fixed a morning-load timeout without adding a single server — I just stopped doing needless work."*

**Follow-ups**
- *"One lever if forced?"* — The database — fix N+1 and add the right index/cache.
- *"Scale up or optimise?"* — Optimise the bottleneck first; scaling a wasteful service just costs more.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| WP1 | What's slow | Blocked threads, DB, repeated work, payload |
| WP2 | Measure first | App Insights, load tests, profiler, DB stats |
| WP3 | Async I/O | Free threads on I/O → throughput |
| WP4 | Async pitfalls | No `.Result`; flow CancellationToken |
| WP5 | N+1 | One query per row; fix with Include/projection |
| WP6 | EF tuning | Check SQL; project; avoid client-eval |
| WP7 | AsNoTracking | Lean read paths + DTO projection |
| WP8 | Caching | Cache-aside expensive read-heavy data |
| WP9 | Redis | Shared cache for scaled-out APIs |
| WP10 | Output caching | Skip re-executing cacheable endpoints |
| WP11 | Payload/compression | Smaller responses, gzip/brotli |
| WP12 | Pagination | Bounded lists; keyset for deep pages |
| WP13 | Serialisation | System.Text.Json, slim DTOs, source-gen |
| WP14 | Connection pooling | Reuse connections; dispose promptly |
| WP15 | HttpClientFactory | Avoid socket exhaustion |
| WP16 | Resilience | Timeout + retry + circuit breaker |
| WP17 | Parallel/batch | WhenAll for independent I/O |
| WP18 | Memory/GC | Cut allocations; Server GC |
| WP19 | Span/pooling | Zero-alloc hot paths |
| WP20 | Background work | Offload slow non-critical work |
| WP21 | Rate limiting | Protect throughput/fairness |
| WP22 | Minimal APIs | Less overhead per request |
| WP23 | Startup/AOT | Faster cold start (ReadyToRun/AOT) |
| WP24 | Logging cost | Templates + level checks; sample |
| WP25 | DbContext lifetime | Scoped; not thread-safe |
| WP26 | Streaming | Constant memory for large responses |
| WP27 | Load testing | p95/p99 under realistic load |
| WP28 | Anti-patterns | .Result, N+1, new HttpClient() |
| WP29 | Real fix | Kill N+1 + Redis cache + async |
| WP30 | My approach | Measure → stop doing needless work → re-measure |

---

[← Angular Performance Tuning](62-concept-angular-performance.md) · [Home](README.md) · [Next → SQL Database Performance Tuning](64-concept-sql-performance.md)
