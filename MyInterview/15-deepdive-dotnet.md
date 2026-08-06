# 15 · Deep Dive: .NET & C# (10 questions)

[← Full-Stack Hands-On](14-fullstack-hands-on.md) · [Home](README.md) · [Next → Deep Dive: React & TypeScript](16-deepdive-react-typescript.md)

This is the .NET-heavy round — where they go past "can you write an endpoint" into "do you understand the runtime". I have written C# for 19 years, so I answer these from real production code on the TCW reporting platform (A) and the TengizChevroil completion apps (C), not from a book.

> Opening line for a .NET-deep panel: *"I do not just use .NET — I understand what it does under my code: the thread pool, the allocations, the async state machine. That is what stops me writing a feature that works in the demo and falls over at volume."*

**Jump to:** [D1 DI & lifetimes](#d1--dependency-injection-and-service-lifetimes) · [D2 middleware](#d2--the-middleware-pipeline) · [D3 LINQ & deferred](#d3--linq-deferred-execution-and-the-traps) · [D4 allocations & Span](#d4--allocations-gc-and-span) · [D5 concurrency](#d5--concurrency-beyond-asyncawait) · [D6 resilience/Polly](#d6--resilience-with-polly) · [D7 caching](#d7--caching-that-actually-helps) · [D8 EF advanced](#d8--entity-framework-core-advanced) · [D9 minimal APIs & gRPC](#d9--minimal-apis-and-grpc) · [D10 config & options](#d10--configuration-options-and-secrets) · [Section index](#section-index)

---

## D1 · Dependency injection and service lifetimes

**What they are testing.** Whether I understand the three lifetimes and the bug that eats teams alive: the captive dependency.

**How I answer.** Three lifetimes, and I pick deliberately:

```csharp
builder.Services.AddSingleton<IClock, SystemClock>();          // one for the app
builder.Services.AddScoped<IReportService, ReportService>();   // one per request
builder.Services.AddTransient<IValidator, Validator>();        // one per resolve
builder.Services.AddDbContext<AppDb>(o => o.UseSqlServer(cs)); // Scoped by default
```

- **Singleton** — stateless, thread-safe, expensive to build (e.g. an `HttpClient` factory, a config cache).
- **Scoped** — lives for one HTTP request. `DbContext` is Scoped, because it is a unit of work and is *not* thread-safe.
- **Transient** — cheap, stateless, new every time.

**The trap I always watch for — the captive dependency:** injecting a Scoped service (like `DbContext`) into a Singleton. The Singleton captures that one `DbContext` forever, and you get cross-request data bleed and threading bugs. .NET's scope validation catches this in development, and I leave it on:

```csharp
// throws at startup if a Singleton captures a Scoped service
builder.Host.UseDefaultServiceProvider(o => o.ValidateScopes = true);
```

If a Singleton genuinely needs per-request data, it takes an `IServiceScopeFactory` and creates a scope explicitly — never captures one.

**Lesson.** *"Lifetimes are not decoration — injecting a DbContext into a Singleton is a data-corruption bug. Leave scope validation on so the runtime catches it at startup, not in production."*

**Follow-ups**
- *"Why is DbContext not a Singleton?"* — It tracks entities and is not thread-safe. One shared instance across concurrent requests corrupts change tracking.
- *"Keyed services?"* — .NET 8 keyed DI lets me register two implementations of one interface and resolve by key — useful for SQL Server vs Snowflake data-access variants.
- *"Constructor vs `IServiceProvider`?"* — Constructor injection always; pulling from the provider (service locator) hides dependencies and I treat it as a smell.

---

## D2 · The middleware pipeline

**What they are testing.** Whether I understand request flow and ordering — the source of subtle auth and CORS bugs.

**How I answer.** Middleware is an ordered chain; each component can act before and after the next. **Order is behaviour**, not style:

```csharp
app.UseExceptionHandler("/error"); // 1. outermost: catch everything below
app.UseHttpsRedirection();
app.UseRouting();                  // 2. decide which endpoint
app.UseCors("reporting");          // 3. after routing, before auth
app.UseAuthentication();           // 4. who are you
app.UseAuthorization();            // 5. may you do this (needs routing + authn first)
app.MapControllers();              // 6. run the endpoint
```

Get the order wrong and you get real bugs: authorization before routing means the endpoint metadata (its `[Authorize]` policy) is not known yet; CORS after auth means the browser preflight fails. I put the exception handler outermost so it wraps the entire pipeline — that is where the centralised error handling from [F10](14-fullstack-hands-on.md#f10--how-do-you-handle-errors-across-the-stack) lives.

Custom middleware I have written — a correlation-ID injector so a request is traceable across the stack ([F12](14-fullstack-hands-on.md#f12--walk-me-through-debugging-a-production-issue-in-code)):

```csharp
app.Use(async (ctx, next) =>
{
    var id = ctx.Request.Headers["X-Correlation-ID"].FirstOrDefault() ?? Guid.NewGuid().ToString();
    ctx.Response.Headers["X-Correlation-ID"] = id;
    using (_logger.BeginScope(new Dictionary<string, object> { ["CorrelationId"] = id }))
        await next();
});
```

**Lesson.** *"Middleware order is the behaviour. Authorization needs routing before it and authentication before it — the classic bug is a policy that silently never runs because the order is wrong."*

**Follow-ups**
- *"`Use` vs `Map` vs `Run`?"* — `Use` chains and can call next; `Run` is terminal; `Map` branches on a path.
- *"Short-circuiting?"* — A middleware that does not call `next()` stops the pipeline — how a rate-limiter or auth gate rejects early.
- *"Where does the correlation ID go?"* — Into the log scope, so every log line for that request carries it. That is what makes distributed debugging possible.

---

## D3 · LINQ, deferred execution and the traps

**What they are testing.** Whether I know *when* a LINQ query runs — the difference between `IEnumerable` and `IQueryable` is a real performance bug.

**How I answer.** LINQ is deferred — nothing runs until you enumerate (`ToList`, `foreach`, `Count`). The trap is where the work happens:

```csharp
// IQueryable: the WHERE is translated to SQL and runs in the database — GOOD
IQueryable<Position> q = _db.Positions.Where(p => p.MarketValue > 1_000_000);
var big = await q.ToListAsync(ct); // SELECT ... WHERE MarketValue > 1000000

// BAD: ToList() first pulls the WHOLE table into memory, THEN filters in C#
var bad = _db.Positions.ToList().Where(p => p.MarketValue > 1_000_000);
```

That second line is a classic production killer — it looks identical but pulls millions of rows over the wire. The rule: keep it `IQueryable` until the filtering and projection are done, then materialise. On the reporting platform, projecting to exactly the columns a report needs before `ToListAsync` is what keeps reads inside the deadline.

**Two more traps I check for:**
- **Multiple enumeration** — enumerating the same `IEnumerable` twice runs the query twice. If I need it more than once, I `ToList()` once and reuse.
- **Client-side evaluation** — calling a C# method EF cannot translate forces the query to run in memory. EF Core throws on this now, which I welcome.

**Lesson.** *"`IQueryable` runs in the database; `IEnumerable` runs in memory. The single most expensive LINQ bug is a `.ToList()` in the middle of a query — it drags the whole table across before you filter it."*

**Follow-ups**
- *"`First` vs `Single` vs `FirstOrDefault`?"* — `Single` asserts exactly one (throws otherwise) — I use it when "more than one" is a real bug I want surfaced.
- *"`Select` vs `SelectMany`?"* — `SelectMany` flattens nested collections into one sequence.
- *"How do you spot the in-memory bug?"* — Log the generated SQL, or watch memory/row counts. A query returning far more rows than the screen shows is the tell.

---

## D4 · Allocations, GC and Span

**What they are testing.** Whether I understand memory — the difference between code that works and code that survives at volume.

**How I answer.** C# is garbage-collected, but allocations are not free — they create GC pressure, and Gen 2 collections pause. On hot paths (an ETL processing millions of rows, a tight parsing loop) I reduce allocations deliberately.

**Value types vs reference types:** a `struct` lives on the stack (no heap allocation) when it is local; a `class` always allocates on the heap. For a small, short-lived, immutable value in a hot loop, a `readonly struct` avoids the allocation.

**`Span<T>` / `ReadOnlySpan<T>`** — slice arrays and strings with zero allocation:

```csharp
// parse a fixed-width Aladdin record without allocating substrings
ReadOnlySpan<char> line = record.AsSpan();
var ticker   = line.Slice(0, 8).Trim();     // no new string allocated
var quantity = long.Parse(line.Slice(8, 12)); // parse directly off the span
```

The old way (`record.Substring(0, 8)`) allocates a new string every call — in a million-row loop that is a million throwaway strings. `Span` slices into the existing memory.

**Other real ones:** `StringBuilder` instead of `+=` string concatenation in a loop; `ArrayPool<T>` to reuse buffers; and being aware that `async`/closures/LINQ lambdas allocate too — fine everywhere except the hottest paths.

**Lesson.** *"I do not micro-optimise everywhere — that is premature. But on a million-row ETL path I reach for `Span` and `StringBuilder`, because a substring per row is a million allocations the GC has to clean up."*

**Follow-ups**
- *"When NOT to do this?"* — Everywhere that is not a measured hot path. Readable code first; optimise where the profiler points.
- *"Gen 0/1/2?"* — Short-lived objects die cheaply in Gen 0; objects that survive get promoted, and Gen 2 collection is the expensive one. Keep hot-path objects short-lived or don't allocate them.
- *"`stackalloc`?"* — For a small, fixed buffer on the stack with zero heap cost — used with `Span` for parsing.

---

## D5 · Concurrency beyond async/await

**What they are testing.** Whether I can handle parallel work safely — I bound concurrency against the rate-limited Aladdin API ([F2](14-fullstack-hands-on.md#f2--how-do-you-write-correct-async-c)).

**How I answer.** First I separate the two: **async** is for I/O waits (don't block a thread); **parallelism** is for CPU work (use many threads). Confusing them is where bugs come from.

**Bounded parallel I/O** — fetch many entities without hammering the API:

```csharp
await Parallel.ForEachAsync(entityTypes,
    new ParallelOptions { MaxDegreeOfParallelism = 4, CancellationToken = ct },
    async (type, token) => await _aladdin.FetchAsync(type, token));
```

**Thread-safe shared state** — if parallel tasks write to a shared collection, I use a concurrent type, never a plain `List`:

```csharp
var results = new ConcurrentBag<Position>();
// or Interlocked for a counter, or a lock for a critical section
Interlocked.Increment(ref _processedCount);
```

**Channels** for producer/consumer — an ingestion producer and a load consumer decoupled with back-pressure:

```csharp
var channel = Channel.CreateBounded<Position>(1000); // back-pressure at 1000
// producer writes, consumer reads — bounded so a fast producer can't OOM us
```

**Lesson.** *"Async frees a thread on I/O; parallelism uses threads for CPU — don't mix them up. And any state shared across parallel tasks needs a concurrent collection, `Interlocked`, or a lock — a plain `List` will corrupt or throw."*

**Follow-ups**
- *"`lock` vs `SemaphoreSlim`?"* — `lock` is synchronous and can't be held across `await`; `SemaphoreSlim` has `WaitAsync` for async critical sections and doubles as a concurrency limiter.
- *"Deadlock avoidance?"* — Async-all-the-way (no `.Result`), consistent lock ordering, and keep critical sections tiny.
- *"`ConfigureAwait(false)`?"* — In library code, to not force resuming on the captured context — avoids a class of deadlock and is slightly faster.

---

## D6 · Resilience with Polly

**What they are testing.** Whether my integration code survives a flaky dependency — the Aladdin API is external and occasionally slow or down.

**How I answer.** I do not hand-roll retry loops — I use Polly (now in `Microsoft.Extensions.Http.Resilience`) and layer the policies:

```csharp
builder.Services.AddHttpClient<AladdinClient>()
    .AddResilienceHandler("aladdin", pipeline =>
    {
        pipeline.AddRetry(new HttpRetryStrategyOptions {
            MaxRetryAttempts = 3,
            BackoffType = DelayBackoffType.Exponential,   // 1s, 2s, 4s
            UseJitter = true                              // avoid thundering herd
        });
        pipeline.AddCircuitBreaker(new HttpCircuitBreakerStrategyOptions {
            FailureRatio = 0.5, MinimumThroughput = 10,
            BreakDuration = TimeSpan.FromSeconds(30)      // stop hammering a dead service
        });
        pipeline.AddTimeout(TimeSpan.FromSeconds(10));     // don't wait forever
    });
```

The key ones: **retry with exponential backoff + jitter** for transient blips; **circuit breaker** so when the dependency is genuinely down I stop calling it for a while instead of piling on; **timeout** so one slow call can't hang the pipeline. This is the code behind the "retry logic" on the FastAPI/ETL side too — same principle, applied to the .NET clients.

**Critical distinction:** I only retry **idempotent / transient** failures. Retrying a validation error (400) just fails slower; retrying a non-idempotent write can double-apply. Retry is for the network blip, not the logic error.

**Lesson.** *"Resilience is retry-with-backoff for transient failures, a circuit breaker so I stop hammering a dead dependency, and a timeout so nothing hangs forever. And I only retry idempotent operations — retrying a write that isn't idempotent is how you get duplicates."*

**Follow-ups**
- *"Why jitter?"* — So a fleet of clients doesn't retry in lockstep and create a synchronised spike (thundering herd).
- *"Circuit breaker states?"* — Closed (normal), Open (failing, reject fast), Half-Open (test one call to see if it recovered).
- *"Where does idempotency come from?"* — Keying the operation (entity + as-of) so a retry replaces rather than duplicates — same as the ETL in [F4](14-fullstack-hands-on.md#f4--write-a-fastapi-etl-ingestion-endpoint).

---

## D7 · Caching that actually helps

**What they are testing.** Whether I cache deliberately — with invalidation, not just to make a demo fast.

**How I answer.** I cache what is expensive and stable, and I always answer the two hard questions: *what invalidates it* and *what happens on a miss*.

```csharp
// a report for a fixed as-of date is IMMUTABLE — perfect to cache
var report = await _cache.GetOrCreateAsync($"report:{type}:{asOf}", async entry =>
{
    entry.AbsoluteExpirationRelativeToNow = TimeSpan.FromHours(1);
    return await _reports.BuildAsync(type, asOf, ct);
});
```

**In-memory (`IMemoryCache`)** for single-instance, small, hot data. **Distributed (`IDistributedCache`, Redis)** when I have multiple instances behind a load balancer — in-memory would give each instance a different view. On A, a report for a past as-of date never changes, so it caches beautifully; today's live report does not, so I don't cache it stale.

**The trap — cache stampede:** when a popular key expires, many requests miss at once and all rebuild it. I guard the rebuild so only one request does the work while others wait.

**Lesson.** *"Caching without an invalidation story is just a bug with better latency. I cache immutable things (a past-dated report) freely, and I never cache data that must be correct-to-the-second."*

**Follow-ups**
- *"Cache-aside vs write-through?"* — Cache-aside (load on miss) for reads; write-through when I need the cache consistent with every write.
- *"Redis over in-memory when?"* — The moment there is more than one instance, or the cache must survive a restart.
- *"How do you avoid stale financial data?"* — Only cache by immutable key (as-of date). Anything "current" is not cached, or has a very short TTL with explicit invalidation.

---

## D8 · Entity Framework Core, advanced

**What they are testing.** EF beyond CRUD — tracking, concurrency, bulk, and the sharp edges.

**How I answer.** The levers I actually use on a data-heavy app:

**Tracking vs no-tracking** — read-only queries skip change tracking:
```csharp
var rows = await _db.Positions.AsNoTracking()
    .Where(p => p.AsOf == asOf).ToListAsync(ct); // faster, less memory for reads
```

**Optimistic concurrency** — a `rowversion` column so two edits don't silently overwrite:
```csharp
modelBuilder.Entity<Trade>().Property(t => t.RowVersion).IsRowVersion();
// SaveChanges throws DbUpdateConcurrencyException if the row changed under me
```

**Bulk operations** — EF7+ `ExecuteUpdate`/`ExecuteDelete` run set-based SQL without loading entities:
```csharp
await _db.Positions.Where(p => p.AsOf < cutoff)
    .ExecuteDeleteAsync(ct); // one DELETE, no loading 1M entities to remove them
```

**Compiled queries** for a hot query run millions of times, and **split queries** to avoid the cartesian explosion of multiple `Include`s. And I know EF's limits — for the deadline-critical reporting reads I drop to hand-tuned SQL ([F3](14-fullstack-hands-on.md#f3--entity-framework-or-dapper-show-me)), because I want to own the plan.

**Lesson.** *"EF is excellent until you fight it. `AsNoTracking` for reads, `rowversion` for concurrency, `ExecuteUpdate/Delete` for bulk — and hand-written SQL for the one query where the deadline lives."*

**Follow-ups**
- *"Lazy vs eager vs explicit loading?"* — Eager (`Include`) mostly; lazy loading I disable because it hides N+1s.
- *"How do you handle migrations at scale?"* — EF migrations scripted out and reviewed; on A the DB utility generator standardises schema-change → release into one repeatable path.
- *"Cartesian explosion?"* — Multiple collection `Include`s multiply rows; `AsSplitQuery()` issues separate queries instead.

---

## D9 · Minimal APIs and gRPC

**What they are testing.** Whether I know the newer hosting models and when each fits.

**How I answer.** **Minimal APIs** for small, focused services — less ceremony than controllers:

```csharp
app.MapGet("/health/ready", async (AppDb db, CancellationToken ct) =>
    await db.Database.CanConnectAsync(ct) ? Results.Ok() : Results.StatusCode(503));
```

I use minimal APIs for health checks, small internal services, and lightweight functions. For a real domain with a team and many endpoints — like the reporting platform — I still prefer controllers ([F1](14-fullstack-hands-on.md#f1--build-a-clean-aspnet-core-web-api-endpoint)) for the structure and filters.

**gRPC** when the caller is another service and I want a typed contract and speed:
```protobuf
service Positions {
  rpc GetPositions (PortfolioRequest) returns (stream Position);
}
```
gRPC shines for internal service-to-service calls — binary Protobuf, HTTP/2, streaming, and a shared `.proto` contract. I would **not** expose gRPC to browsers (needs gRPC-Web) or to a public partner who expects REST/JSON. REST for the front end and external consumers; gRPC between my own services where the performance and the contract pay off.

**Lesson.** *"Minimal APIs for small services and health checks, controllers for a real domain, REST for browsers and partners, gRPC between my own services. Matching the hosting model to the caller is the decision — not picking the newest one."*

**Follow-ups**
- *"gRPC vs REST performance?"* — gRPC is faster (binary, HTTP/2, streaming) but harder to debug and not browser-native. Trade convenience for speed only where it counts.
- *"Endpoint filters on minimal APIs?"* — Yes — they give validation/cross-cutting concerns similar to controller filters.
- *"Versioning APIs?"* — URL or header versioning, with the contract explicit — an integration contract is a promise ([R5](06-rfp-presales.md#r5--how-do-you-work-with-sales-commercial-and-legal)).

---

## D10 · Configuration, options and secrets

**What they are testing.** Whether I handle config and secrets like production, not like a tutorial with a hard-coded connection string.

**How I answer.** Layered configuration with the strongly-typed options pattern, and secrets never in source.

```csharp
// strongly-typed, validated at startup
builder.Services.AddOptions<AladdinOptions>()
    .Bind(builder.Configuration.GetSection("Aladdin"))
    .ValidateDataAnnotations()
    .ValidateOnStart();  // fail fast at boot if config is invalid, not at first call

// injected where needed
public AladdinClient(IOptions<AladdinOptions> options) => _opts = options.Value;
```

Config layers in order: `appsettings.json` → environment-specific `appsettings.Production.json` → environment variables → **Azure Key Vault** for secrets. Connection strings, API keys and the Aladdin credentials live in Key Vault, pulled via managed identity — so no secret is ever in a file, a repo, or an environment variable a human can read. `ValidateOnStart` means a missing or malformed setting crashes the app at boot with a clear message, rather than throwing on the first request at 5 a.m.

**Lesson.** *"Strongly-typed options, validated on start, with secrets in Key Vault via managed identity. A hard-coded connection string is a security incident waiting to happen, and config that fails at first-use instead of at boot fails at the worst possible time."*

**Follow-ups**
- *"`IOptions` vs `IOptionsSnapshot` vs `IOptionsMonitor`?"* — `IOptions` is singleton/static; `IOptionsSnapshot` is per-request (picks up changes); `IOptionsMonitor` pushes live changes — useful for feature flags.
- *"Why managed identity?"* — No secret to store or rotate at all — Azure hands the app an identity, and Key Vault trusts it. See [F9](14-fullstack-hands-on.md#f9--wire-up-auth-across-the-stack).
- *"Feature flags?"* — Azure App Configuration with feature management, so I can turn a feature on without a redeploy.

---

## Section index

| # | Question | Core message |
|---|---|---|
| D1 | DI & lifetimes | Injecting a Scoped DbContext into a Singleton corrupts data — validate scopes |
| D2 | Middleware pipeline | Order is behaviour; authz needs routing + authn before it |
| D3 | LINQ & deferred execution | `IQueryable` runs in the DB; a mid-query `.ToList()` drags the whole table over |
| D4 | Allocations, GC, Span | On a hot path, `Span`/`StringBuilder` kill per-row allocations |
| D5 | Concurrency | Async for I/O, parallelism for CPU; shared state needs concurrent types |
| D6 | Resilience (Polly) | Retry+backoff+jitter, circuit breaker, timeout — only retry idempotent ops |
| D7 | Caching | No invalidation story = a bug with better latency; cache immutable keys |
| D8 | EF Core advanced | `AsNoTracking`, `rowversion`, `ExecuteUpdate/Delete`; hand-SQL the hot query |
| D9 | Minimal APIs & gRPC | Match hosting to caller: REST for browsers, gRPC between own services |
| D10 | Config, options, secrets | Typed options validated on start; secrets in Key Vault via managed identity |

---

[← Full-Stack Hands-On](14-fullstack-hands-on.md) · [Home](README.md) · [Next → Deep Dive: React & TypeScript](16-deepdive-react-typescript.md)
