# 66 · Concept: .NET & C# — What's New (Version Evolution) (30 questions)

[← Microservices / System Architecture Performance](65-concept-microservices-performance.md) · [Home](README.md) · [Next → SQL Server What's New](67-concept-sqlserver-whats-new.md)

This file explains **what is new in .NET and C#** — release by release, in simple English, with the *why it matters* and *how it compares to the old way*. As an architect I keep the TCW platforms (Projects A, B) on a supported .NET version and use new features deliberately, not for fashion. Every code sample is C#.

> Simple one-liner: *".NET ships once a year — even-numbered releases (6, 8, 10) are LTS (3 years support), odd ones (7, 9) are STS (18 months). I stay on an LTS in production and adopt new C# features when they make the code simpler or faster, never just because they exist."*

**Jump to (the release model):** [DW1 Release cadence](#dw1--the-net-release-cadence) · [DW2 LTS vs STS](#dw2--lts-vs-sts-and-support) · [DW3 .NET Framework vs .NET](#dw3--net-framework-vs-modern-net) · [DW4 How I upgrade](#dw4--how-i-plan-an-upgrade) · [DW5 target framework moniker](#dw5--tfms-and-multi-targeting)
> **.NET 6 (LTS):** [DW6 Minimal APIs](#dw6--minimal-apis) · [DW7 Top-level statements](#dw7--top-level-statements) · [DW8 Hot reload](#dw8--hot-reload) · [DW9 record structs](#dw9--record-structs)
> **.NET 7:** [DW10 Rate limiting](#dw10--built-in-rate-limiting) · [DW11 Output caching](#dw11--output-caching) · [DW12 Perf gains](#dw12--net-7-performance)
> **.NET 8 (LTS):** [DW13 Native AOT](#dw13--native-aot) · [DW14 Keyed DI](#dw14--keyed-services-in-di) · [DW15 TimeProvider](#dw15--timeprovider-testable-time) · [DW16 Blazor United](#dw16--blazor-render-modes)
> **.NET 9:** [DW17 What .NET 9 adds](#dw17--net-9-highlights) · [DW18 Hybrid cache](#dw18--hybridcache)
> **C# language:** [DW19 Records](#dw19--records-c-9) · [DW20 Nullable refs](#dw20--nullable-reference-types) · [DW21 Pattern matching](#dw21--pattern-matching-evolution) · [DW22 Global usings](#dw22--global-and-implicit-usings) · [DW23 Required members](#dw23--required-members-c-11) · [DW24 Primary constructors](#dw24--primary-constructors-c-12) · [DW25 Collection expressions](#dw25--collection-expressions-c-12)
> **EF & runtime:** [DW26 EF Core new](#dw26--whats-new-in-ef-core) · [DW27 Perf every year](#dw27--why-net-gets-faster-each-year)
> **Decisions:** [DW28 When to adopt](#dw28--when-do-i-adopt-a-new-version) · [DW29 Migration risks](#dw29--migration-risks-and-known-issues) · [DW30 My approach](#dw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in .NET" in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. .NET is now one unified, yearly product.** The old split — .NET Framework (Windows-only, legacy), .NET Core, Xamarin — is gone. Since .NET 5 it is just **".NET"**: one cross-platform runtime, one SDK, a new major version every November. Knowing *which* version I'm on and *when it loses support* is the first architectural fact.

**2. LTS vs STS decides my support runway.** Even numbers (6, 8, 10) are **LTS** — 3 years of support. Odd numbers (7, 9) are **STS** — 18 months. In production I stay on LTS so I'm never forced into a rushed upgrade. I only ride an STS on internal tools.

**3. "New" comes in two streams: the runtime/framework and the C# language.** A release like .NET 8 bundles *runtime* features (Native AOT, keyed DI, better GC) and a matching *C# version* (C# 12: primary constructors, collection expressions). I keep the two ideas separate in my head.

**4. Most new features are about writing *less* code or running *faster*.** Minimal APIs, top-level statements, records, collection expressions — all reduce ceremony. Native AOT, tiered compilation and per-release GC work make the same code faster. Every year .NET gets measurably quicker with no code change.

**5. The theme since .NET 6 is "cloud-native and fast-start".** Minimal APIs, Native AOT (tiny, quick-booting binaries), built-in rate limiting and output caching all target containers and serverless, where cold-start and memory cost money. On Project C (Azure) this matters directly.

**6. Old way vs new way is the interview gold.** For every feature I can say the *before* and the *after* — e.g. a controller + Startup.cs (old) vs a minimal API in `Program.cs` (new); a null-checking `if` (old) vs nullable reference types catching it at compile time (new). That contrast is what interviewers want.

**7. Upgrading is a managed risk, not a button.** I bump the TFM, read the breaking-changes list, run the analyzers, test hard, and ship behind a flag. "Newer" is only better once it's proven on my workload.

**8. I adopt deliberately.** A new feature earns its place if it makes code simpler, safer or faster for *my* team. I don't rewrite working code just to use primary constructors. YAGNI applies to language features too.

**The full-stack / architect lens:** the later Q&As go release-by-release (6→7→8→9) and feature-by-feature (records, nullable refs, pattern matching, primary constructors, collection expressions, keyed DI, Native AOT, HybridCache) with old-vs-new code, plus EF Core changes, why the runtime keeps getting faster, migration risks/EOL, and how I decide when to adopt. They all trace back to the core: stay supported, adopt for real benefit, and always know the before-and-after.

**One rule I never break:** *run production on a supported (ideally LTS) version, and adopt a new feature only when it makes the code simpler, safer, or faster — never for novelty.*

---

## DW1 · The .NET release cadence

**Simple explanation.** Since .NET 5, Microsoft ships a **new major version every November**. There is no ".NET Core" name anymore and no ".NET 4-style" long gaps. The timeline: .NET 5 (2020), 6 (2021, LTS), 7 (2022), 8 (2023, LTS), 9 (2024), 10 (2025, LTS).

**Why it matters.** Predictable cadence lets me plan upgrades on a calendar. I know an LTS lands every two years, so I can pick an upgrade rhythm the business can live with.

**Architect's view:** I treat "which .NET version and when does it go end-of-life" as a standing item in the architecture decision record, reviewed every year.

**Follow-ups**
- *Is .NET Framework dead?* — It's still supported (4.8 is "done" but serviced) for legacy apps, but all new work goes on modern .NET. I don't start anything new on Framework.
- *Do I have to upgrade every year?* — No. I hop LTS-to-LTS (6→8→10) and skip the odd releases in production.

---

## DW2 · LTS vs STS and support

**Simple explanation.** **LTS (Long-Term Support)** = even versions (6, 8, 10), supported **3 years**. **STS (Standard-Term Support)** = odd versions (7, 9), supported **18 months**. After that a version stops getting security patches — that's the real deadline.

**Old way vs new way.** In the .NET Framework era support was tied to Windows and lasted a decade, so upgrades were rare and huge. Now support windows are short and predictable, so upgrades are small and frequent — much less risky per hop.

**Architect's view:** running past end-of-support is a security finding in a regulated firm like TCW. I never let a production service drift onto an unsupported runtime.

**Follow-ups**
- *Which do you pick for a new production API?* — The latest LTS. Longest runway, most stability.
- *When would you use an STS?* — An internal tool where I want a specific new feature and can upgrade again in a year.

---

## DW3 · .NET Framework vs modern .NET

**Simple explanation.** **.NET Framework** (up to 4.8) is Windows-only, closed, and legacy. **Modern .NET** (5+) is cross-platform (Windows/Linux/macOS), open-source, faster, and container-friendly. They are different products that happen to share a language (C#).

**Old way vs new way.**

| Aspect | .NET Framework 4.8 | Modern .NET (8) |
|---|---|---|
| Platform | Windows only | Windows/Linux/macOS |
| Hosting | IIS | Kestrel, containers, anywhere |
| Startup | `Global.asax`, `web.config` | `Program.cs`, `appsettings.json` |
| DI | Third-party (Autofac) | Built-in |
| Performance | Baseline | Much faster, lower memory |

**Architect's view:** for migrations I use the *strangler-fig* pattern — stand up the new .NET service beside the old Framework app and move endpoints across gradually, never a big-bang rewrite.

**Follow-ups**
- *Can you run Framework code on Linux?* — No. That's often the reason to migrate (cheaper Linux hosting/containers).
- *What's the migration tooling?* — The .NET Upgrade Assistant and the API portability analyzer.

---

## DW4 · How I plan an upgrade

**Simple explanation.** My upgrade recipe: (1) bump the target framework, (2) update NuGet packages, (3) read the official **breaking-changes** page for that version, (4) run analyzers/tests, (5) fix warnings, (6) load-test, (7) ship to a canary slot behind a flag, (8) roll out.

**Why it matters.** Most upgrades are quick because the cadence is small — but skipping the breaking-changes review is how teams get surprised in production.

**Architect's view:** I upgrade one version at a time even when jumping LTS-to-LTS, so I can isolate any problem to a single release.

**Follow-ups**
- *How long does a typical hop take?* — For a well-tested service, hours to a day. The tests carry the confidence.
- *Biggest risk?* — Transitive dependencies that haven't updated yet.

---

## DW5 · TFMs and multi-targeting

**Simple explanation.** A **Target Framework Moniker (TFM)** like `net8.0` in the `.csproj` says which .NET a project builds for. A **library** can *multi-target* (`net6.0;net8.0`) to support consumers on different versions.

```xml
<!-- New: single app targeting an LTS -->
<TargetFramework>net8.0</TargetFramework>

<!-- Library supporting two runtimes -->
<TargetFrameworks>net6.0;net8.0</TargetFrameworks>
```

**Architect's view:** shared internal libraries multi-target so one team's upgrade doesn't force everyone to move at once.

**Follow-ups**
- *What about `netstandard2.0`?* — Still useful for libraries that must work on old Framework *and* modern .NET.
- *Does multi-targeting slow builds?* — Slightly; I only do it where the compatibility is genuinely needed.

---

## DW6 · Minimal APIs

**Simple explanation.** Introduced in **.NET 6**, minimal APIs let me define endpoints directly in `Program.cs` without controller classes — great for small services and microservices.

**Old way vs new way.**

```csharp
// OLD (controllers): Startup.cs + WeatherController.cs, lots of ceremony
[ApiController, Route("weather")]
public class WeatherController : ControllerBase {
    [HttpGet] public IActionResult Get() => Ok(new { temp = 21 });
}

// NEW (.NET 6 minimal API): one file
var app = WebApplication.Create(args);
app.MapGet("/weather", () => new { temp = 21 });
app.Run();
```

**Architect's view:** I use minimal APIs for focused microservices and lightweight endpoints; I still reach for controllers on large APIs where filters, model binding and organisation pay off.

**Follow-ups**
- *Do minimal APIs support DI and validation?* — Yes — parameters are injected, and .NET 8 added a filter pipeline and better validation support.
- *When not to use them?* — Very large APIs with many cross-cutting concerns; controllers stay cleaner there.

---

## DW7 · Top-level statements

**Simple explanation.** From C# 9 / .NET 6 the boilerplate `Main` method and `Program` class are optional — I write program code at the top of `Program.cs`.

**Old vs new.**

```csharp
// OLD
using System;
class Program { static void Main() => Console.WriteLine("Hi"); }

// NEW
Console.WriteLine("Hi");
```

**Architect's view:** less noise for newcomers and samples; the compiler still generates the `Main` under the hood.

**Follow-ups**
- *Where do args go?* — An implicit `args` string array is available.
- *Can I still use a classic Program class?* — Yes, it's a choice, not a mandate.

---

## DW8 · Hot reload

**Simple explanation.** **.NET 6** added Hot Reload: change code while the app runs and see it update without a full restart — for web, Blazor and desktop.

**Why it matters.** Faster inner loop; I keep app state while tweaking UI or logic.

**Architect's view:** a productivity win for the team; it doesn't change architecture but it speeds delivery.

**Follow-ups**
- *Does every change hot-reload?* — No — structural changes (new types, signature changes) still need a rebuild.
- *Works in CI?* — It's a dev-loop feature, not a runtime one.

---

## DW9 · record structs

**Simple explanation.** C# 10 / .NET 6 added **record structs** — value-type records with built-in equality, combining struct performance with record convenience.

```csharp
public readonly record struct Money(decimal Amount, string Currency);
```

**Architect's view:** I use them for small, immutable value objects (money, coordinates) on hot paths where I want value semantics without heap allocation.

**Follow-ups**
- *record class vs record struct?* — Class = reference type (heap); struct = value type (stack/inline). Pick by allocation and copy cost.
- *Are they immutable?* — `readonly record struct` is; plain record struct is mutable.

---

## DW10 · Built-in rate limiting

**Simple explanation.** **.NET 7** added a first-class **rate-limiting middleware** — fixed window, sliding window, token bucket, concurrency — no third-party library needed.

```csharp
builder.Services.AddRateLimiter(o =>
    o.AddFixedWindowLimiter("api", opt => {
        opt.PermitLimit = 100; opt.Window = TimeSpan.FromMinutes(1);
    }));
app.UseRateLimiter();
app.MapGet("/data", () => "ok").RequireRateLimiting("api");
```

**Old vs new.** Before .NET 7 I hand-rolled this or used Redis/Polly. Now it's in the box.

**Architect's view:** I put rate limiting at the API edge to protect downstream services and the database — a resilience default.

**Follow-ups**
- *Distributed rate limiting across instances?* — The built-in limiter is per-instance; for global limits I still back it with Redis.
- *What response on limit?* — 429; I return `Retry-After`.

---

## DW11 · Output caching

**Simple explanation.** **.NET 7** added **output caching** middleware — cache the whole response for a route on the server, with tag-based invalidation.

```csharp
builder.Services.AddOutputCache();
app.UseOutputCache();
app.MapGet("/report", GetReport).CacheOutput(p => p.Expire(TimeSpan.FromMinutes(5)));
```

**Old vs new.** Different from *response caching* (client/proxy headers) — output caching is server-controlled and far more reliable.

**Architect's view:** great for expensive, rarely-changing reads like reference data on the TCW reporting APIs.

**Follow-ups**
- *How to invalidate?* — Tag responses and evict by tag when the data changes.
- *Can it use Redis?* — Yes, with a distributed cache store for multi-instance.

---

## DW12 · .NET 7 performance

**Simple explanation.** .NET 7 was a big performance release — hundreds of improvements to the JIT, GC, and core libraries, plus **on-stack replacement (OSR)** so hot loops get optimised without restart.

**Architect's view:** "free" speed — recompiling my service on 7 made it faster with zero code change. I quote this when justifying upgrades.

**Follow-ups**
- *How do you prove the gain?* — Benchmark before/after with BenchmarkDotNet and load tests.
- *Which workloads benefit most?* — Compute-heavy and high-throughput APIs.

---

## DW13 · Native AOT

**Simple explanation.** **.NET 8** matured **Native AOT (Ahead-Of-Time)** compilation: compile straight to a native binary with **no JIT and no runtime needed**. Result: tiny, super-fast-starting, low-memory executables.

**Old vs new.** Normally .NET JIT-compiles at startup (slower cold start, needs the runtime). AOT produces a self-contained native app — ideal for serverless and containers.

**Architect's view:** I use AOT for small, high-density microservices and Azure Functions where cold-start and per-instance memory drive cost. The trade-off: no runtime reflection/dynamic code, so not everything is AOT-compatible.

**Follow-ups**
- *What breaks under AOT?* — Reflection-heavy libraries and runtime code-gen. I check compatibility first.
- *How much faster is start-up?* — Often milliseconds vs hundreds of ms; memory can drop dramatically.

---

## DW14 · Keyed services in DI

**Simple explanation.** **.NET 8** added **keyed services**: register multiple implementations of the same interface under different keys and resolve by key.

```csharp
// NEW (.NET 8)
builder.Services.AddKeyedScoped<INotifier, EmailNotifier>("email");
builder.Services.AddKeyedScoped<INotifier, SmsNotifier>("sms");

public class OrderService([FromKeyedServices("sms")] INotifier notifier) { }
```

**Old vs new.** Before .NET 8 I used a factory or a strategy dictionary to pick an implementation. Keyed DI makes it native.

**Architect's view:** cleaner than home-grown factories for "same interface, several flavours" (payment providers, notifiers).

**Follow-ups**
- *Overuse risk?* — Too many keys hide complexity; sometimes separate interfaces are clearer.
- *Works with `IEnumerable<T>`?* — You can still inject all implementations when you need the whole set.

---

## DW15 · TimeProvider (testable time)

**Simple explanation.** **.NET 8** added `TimeProvider` — an abstraction over the clock so I can inject and fake "now" in tests instead of calling `DateTime.UtcNow` directly.

```csharp
public class Token(TimeProvider clock) {
    public bool Expired(DateTimeOffset issued) =>
        clock.GetUtcNow() - issued > TimeSpan.FromHours(1);
}
// tests use FakeTimeProvider to control time
```

**Old vs new.** Before, static `DateTime.UtcNow` made time-dependent logic almost untestable. Now it's injectable.

**Architect's view:** I mandate `TimeProvider` for any expiry/scheduling logic — it removes flaky, time-based tests.

**Follow-ups**
- *Also for timers/delays?* — Yes, `TimeProvider` can create timers, so `Task.Delay` is fakeable too.
- *Where does FakeTimeProvider live?* — `Microsoft.Extensions.TimeProvider.Testing`.

---

## DW16 · Blazor render modes

**Simple explanation.** **.NET 8** unified Blazor: one model where each component can render **Server**, **WebAssembly**, **Auto**, or **static SSR** — pick per component.

**Old vs new.** Previously you chose Blazor Server *or* Blazor WASM up front. Now it's a per-component decision with streaming SSR.

**Architect's view:** static SSR for content pages, interactive modes only where needed — best of both without committing the whole app.

**Follow-ups**
- *What's "Auto"?* — Server first for fast load, then WASM downloads and takes over.
- *Do I need it?* — Only if I'm doing Blazor; for React/Angular shops it's not relevant.

---

## DW17 · .NET 9 highlights

**Simple explanation.** **.NET 9** (STS) focuses on performance and cloud: better GC (adaptive server GC), more AOT scenarios, `HybridCache`, improved LINQ, and OpenAPI document generation built in (replacing Swashbuckle's default role).

**Architect's view:** I treat 9 as a preview of what lands in the next LTS (10). I trial its features on internal tools, keep production on 8 until 10.

**Follow-ups**
- *Built-in OpenAPI — does it replace Swagger UI?* — It generates the JSON doc; I still add a UI (Swagger UI/Scalar) if I want the page.
- *Worth upgrading prod to 9?* — Usually I wait for 10 (LTS) unless a specific 9 feature is needed.

---

## DW18 · HybridCache

**Simple explanation.** **`HybridCache`** (.NET 9) combines an **in-memory (L1)** and a **distributed (L2, e.g. Redis)** cache behind one API, with stampede protection (only one caller recomputes a missing value).

```csharp
var data = await cache.GetOrCreateAsync(key,
    async ct => await LoadAsync(ct));
```

**Old vs new.** Before, I wired `IMemoryCache` + `IDistributedCache` myself and hand-rolled stampede protection. HybridCache does both.

**Architect's view:** exactly the pattern I built by hand on the reporting APIs — now standard, with the cache-stampede fix included.

**Follow-ups**
- *What's stampede protection?* — On a cache miss, many requests would all hit the DB at once; HybridCache lets one compute while others wait.
- *Tag invalidation?* — Yes, it supports tagging for grouped eviction.

---

## DW19 · Records (C# 9)

**Simple explanation.** **Records** are reference types with **value-based equality**, immutability by default, and a concise syntax — perfect for DTOs and domain values.

```csharp
public record Customer(int Id, string Name);
var a = new Customer(1, "Sam");
var b = a with { Name = "Sam Two" }; // non-destructive copy
bool same = a == new Customer(1, "Sam"); // true (value equality)
```

**Old vs new.** Before records, a value object meant a class plus hand-written `Equals`, `GetHashCode`, `ToString` and a copy method — dozens of lines. Records give it in one.

**Architect's view:** I use records for DTOs, API contracts, and immutable domain values; classes for entities with behaviour and mutable state.

**Follow-ups**
- *What is `with`?* — A non-destructive mutation: copy with a few fields changed.
- *Are records always immutable?* — Positional records are init-only by default; you can add settable properties, but I keep them immutable.

---

## DW20 · Nullable reference types

**Simple explanation.** **Nullable reference types (NRT)**, on by default in new projects since .NET 6, make the compiler warn when a reference might be null — turning a class of runtime `NullReferenceException`s into compile-time warnings.

```csharp
#nullable enable
string name = null;      // warning
string? maybe = null;    // fine, explicitly nullable
int len = maybe.Length;  // warning: possible null
```

**Old vs new.** Before, every reference could silently be null and you found out at runtime. Now the type says whether null is allowed.

**Architect's view:** I keep NRT enabled and treat the warnings as errors in CI — it's the cheapest bug-prevention in C#.

**Follow-ups**
- *Does it change runtime behaviour?* — No — it's compile-time analysis only.
- *The `!` operator?* — The null-forgiving operator; I use it sparingly and only when I can prove non-null.

---

## DW21 · Pattern matching evolution

**Simple explanation.** C# pattern matching has grown release by release: type patterns, `switch` expressions (C# 8), relational and logical patterns (C# 9), list patterns (C# 11).

```csharp
// switch expression + relational/logical patterns
string band = age switch {
    < 13 => "child",
    >= 13 and < 20 => "teen",
    _ => "adult"
};
// list pattern (C# 11)
if (arr is [1, _, 3]) { /* first 1, last 3 */ }
```

**Old vs new.** Replaces long `if/else` chains and `switch` statements with concise, exhaustive expressions.

**Architect's view:** clearer branching and the compiler warns if I miss a case — safer than nested ifs.

**Follow-ups**
- *Property patterns?* — Yes: `p is { Age: > 18, Country: "US" }`.
- *Any downside?* — Over-clever patterns hurt readability; I keep them simple.

---

## DW22 · Global and implicit usings

**Simple explanation.** **Global usings** (C# 10) declare a `using` once for the whole project; **implicit usings** auto-include the common namespaces for the project type.

```csharp
// GlobalUsings.cs
global using System.Text.Json;
```
```xml
<ImplicitUsings>enable</ImplicitUsings>
```

**Old vs new.** Removes the repeated wall of `using` lines at the top of every file.

**Architect's view:** I keep a single `GlobalUsings.cs` for shared namespaces — cleaner files, one place to manage.

**Follow-ups**
- *Can it hide dependencies?* — A little; I keep the global list short and obvious.
- *Per-project?* — Yes, each project has its own set.

---

## DW23 · Required members (C# 11)

**Simple explanation.** The **`required`** modifier forces callers to set a property during initialization — compile-time enforcement without a big constructor.

```csharp
public class Order {
    public required string CustomerId { get; init; }
    public required decimal Total { get; init; }
}
var o = new Order { CustomerId = "C1", Total = 10m }; // must set both
```

**Old vs new.** Before, you enforced mandatory fields with constructors or runtime checks. Now the compiler enforces it.

**Architect's view:** pairs well with `init` and records for safe, clear object creation.

**Follow-ups**
- *Works with records?* — Yes.
- *Can I bypass it?* — Only via `[SetsRequiredMembers]` on a constructor that sets them.

---

## DW24 · Primary constructors (C# 12)

**Simple explanation.** **Primary constructors** let any class or struct declare constructor parameters on the type line and use them anywhere in the body — not just records.

```csharp
// NEW (C# 12)
public class OrderService(IOrderRepo repo, ILogger<OrderService> log) {
    public Task Save(Order o) { log.LogInformation("saving"); return repo.Add(o); }
}
// OLD: fields + constructor assigning each one
```

**Old vs new.** Removes the classic "private field + constructor assignment" boilerplate for DI — a big win since almost every service does exactly that.

**Architect's view:** I use them for DI-heavy services; it cuts noise. I still write an explicit constructor when I need validation logic.

**Follow-ups**
- *Are the parameters fields?* — They're captured; the compiler creates backing storage as needed.
- *Downside?* — Parameters are mutable within the type; for strict immutability I still prefer readonly fields or records.

---

## DW25 · Collection expressions (C# 12)

**Simple explanation.** A unified `[...]` syntax to create arrays, lists, spans, etc., plus the **spread** operator `..`.

```csharp
int[] a = [1, 2, 3];
List<int> b = [0, ..a, 4];   // spread: 0,1,2,3,4
Span<int> s = [1, 2, 3];
```

**Old vs new.** Replaces `new List<int> { 1, 2, 3 }` / `new[] {…}` variety with one consistent, terse form.

**Architect's view:** small but constant readability win, especially with spread for merging collections.

**Follow-ups**
- *Does it work for any collection?* — Any type the compiler knows how to build, including custom ones via a builder.
- *Performance?* — The compiler picks an efficient construction; for spans it can avoid allocation.

---

## DW26 · What's new in EF Core

**Simple explanation.** EF Core ships with each .NET release. Recent highlights: **bulk `ExecuteUpdate`/`ExecuteDelete`** (EF 7) for set-based updates without loading entities; **JSON column mapping** (EF 7); **complex types** and better raw-SQL (EF 8); improved LINQ translation each year.

```csharp
// NEW (EF 7): one SQL UPDATE, no entities loaded
await db.Orders.Where(o => o.Stale)
                .ExecuteUpdateAsync(s => s.SetProperty(o => o.Archived, true));
// OLD: load all, loop, SaveChanges — slow and chatty
```

**Architect's view:** `ExecuteUpdate/Delete` fixed a real performance pain — bulk operations used to load thousands of entities just to change a flag.

**Follow-ups**
- *Does ExecuteUpdate use change tracking?* — No — it's a direct SQL statement, so combine carefully with tracked entities.
- *JSON columns — when?* — For flexible sub-documents inside a relational row.

---

## DW27 · Why .NET gets faster each year

**Simple explanation.** Every release invests in the **JIT** (better codegen, OSR, PGO), the **GC** (regions, DATAS/adaptive sizing), and the **BCL** (faster LINQ, spans, less allocation). The same code runs faster after an upgrade.

**Architect's view:** I use this as a concrete upgrade justification — "recompiling on the new LTS typically buys measurable throughput and lower memory for free." I always confirm with a benchmark.

**Follow-ups**
- *What's PGO?* — Profile-Guided Optimization: the runtime optimises based on real execution patterns (dynamic PGO is on by default in .NET 8).
- *Does it ever regress?* — Rarely; that's why I benchmark before/after.

---

## DW28 · When do I adopt a new version?

**Simple explanation.** My rule: **production on the latest LTS**; adopt an STS only for internal tools or a must-have feature. I wait a few weeks after release for the ecosystem (libraries, base images) to catch up.

**Architect's view:** I balance three things — support runway, real feature benefit, and dependency readiness. "Newest" loses to "supported and proven" in production.

**Follow-ups**
- *How do you decide a feature is worth adopting?* — It must make code simpler, safer, or faster for my team — not just be new.
- *Do you refactor old code to new syntax?* — Only opportunistically, when I'm already in that file.

---

## DW29 · Migration risks and known issues

**Simple explanation.** The usual risks: **breaking API changes**, **removed/obsolete APIs**, **behavioural changes** (e.g. trimming/AOT limits), **package incompatibility**, and **base-image changes** in Docker. Every version has an official breaking-changes list — I read it first.

**Architect's view:** I mitigate with strong tests, one-version-at-a-time hops, a canary deployment, and a fast rollback plan. On regulated platforms I also re-run security scans post-upgrade.

**Follow-ups**
- *Most common surprise?* — A transitive dependency that hasn't shipped a compatible version yet.
- *AOT/trimming gotchas?* — Reflection-based code can break; I test the published, trimmed artifact, not just debug.

---

## DW30 · My approach

**Simple explanation.** I keep production on a **supported LTS**, track the yearly cadence as an ADR item, and adopt new C#/runtime features **deliberately** — for simpler, safer, or faster code. For every feature I can state the *old way*, the *new way*, and *why the change helps*.

**Architect's view:** version currency is a security and cost decision as much as a feature one. Staying supported protects the firm; adopting the right features keeps the codebase clean and the runtime fast. On TCW I upgrade LTS-to-LTS with tests and canaries, and I never chase novelty for its own sake.

**Follow-ups**
- *One sentence on your upgrade philosophy?* — "Supported by default, modern on purpose."
- *How do you keep the team current?* — Short internal write-ups of "what's new and where we'll use it" each LTS.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| DW1 | Release cadence | New major version every November since .NET 5 |
| DW2 | LTS vs STS | Even = LTS (3 yrs), odd = STS (18 mo); prod on LTS |
| DW3 | Framework vs .NET | Framework = legacy/Windows; modern .NET = cross-platform/fast |
| DW4 | Planning upgrades | Bump TFM, read breaking changes, test, canary, roll out |
| DW5 | TFMs & multi-targeting | `net8.0`; libraries multi-target for compatibility |
| DW6 | Minimal APIs | Endpoints without controllers (.NET 6) |
| DW7 | Top-level statements | No boilerplate Main/Program |
| DW8 | Hot reload | Edit running app without restart |
| DW9 | record structs | Value-type records for small immutable values |
| DW10 | Rate limiting | Built-in limiter middleware (.NET 7) |
| DW11 | Output caching | Server-side response caching with tags (.NET 7) |
| DW12 | .NET 7 performance | Big JIT/GC/OSR gains — free speed |
| DW13 | Native AOT | Native binary, no JIT — fast start, low memory (.NET 8) |
| DW14 | Keyed DI | Multiple implementations by key (.NET 8) |
| DW15 | TimeProvider | Injectable, testable clock (.NET 8) |
| DW16 | Blazor render modes | Per-component Server/WASM/Auto/SSR (.NET 8) |
| DW17 | .NET 9 highlights | Perf, more AOT, built-in OpenAPI, HybridCache |
| DW18 | HybridCache | L1+L2 cache with stampede protection (.NET 9) |
| DW19 | Records (C# 9) | Value-equality, immutable DTOs with `with` |
| DW20 | Nullable refs | Null bugs caught at compile time |
| DW21 | Pattern matching | switch expressions, relational/list patterns |
| DW22 | Global/implicit usings | Declare usings once |
| DW23 | required members | Compiler-enforced mandatory properties (C# 11) |
| DW24 | Primary constructors | Cut DI boilerplate (C# 12) |
| DW25 | Collection expressions | `[...]` and spread `..` (C# 12) |
| DW26 | EF Core new | ExecuteUpdate/Delete, JSON columns, complex types |
| DW27 | Yearly perf | JIT/GC/BCL improvements each release |
| DW28 | When to adopt | Prod on LTS; adopt features for real benefit |
| DW29 | Migration risks | Breaking changes, deps, AOT/trimming limits |
| DW30 | My approach | Supported by default, modern on purpose |

---

[← Microservices / System Architecture Performance](65-concept-microservices-performance.md) · [Home](README.md) · [Next → SQL Server What's New](67-concept-sqlserver-whats-new.md)
