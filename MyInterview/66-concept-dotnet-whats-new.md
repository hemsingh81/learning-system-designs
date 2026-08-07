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
- *Is .NET Framework dead?* — Not dead, but frozen. .NET Framework 4.8 is the last version — it still gets security servicing and ships with Windows, so my existing legacy apps keep running, but it will never get new features, cross-platform support, or the yearly performance gains. So I keep old Framework apps alive on 4.8 while they earn their keep, but every new service starts on modern .NET. The practical tell: if a feature only exists on .NET 8+ (Native AOT, minimal APIs, keyed DI), Framework will never get it.
- *Do I have to upgrade every year?* — No, and I deliberately don't. I hop LTS-to-LTS (6→8→10) and skip the odd STS releases in production, which means I only move roughly every two years while staying supported the whole time. Each hop stays small because the cadence is small — jumping 6→8 is two years of change, not a decade like the old Framework upgrades. The odd releases (7, 9) are where I trial features on internal tools so I'm ready when they land in the next LTS.

---

## DW2 · LTS vs STS and support

**Simple explanation.** **LTS (Long-Term Support)** = even versions (6, 8, 10), supported **3 years**. **STS (Standard-Term Support)** = odd versions (7, 9), supported **18 months**. After that a version stops getting security patches — that's the real deadline.

**Old way vs new way.** In the .NET Framework era support was tied to Windows and lasted a decade, so upgrades were rare and huge. Now support windows are short and predictable, so upgrades are small and frequent — much less risky per hop.

**Architect's view:** running past end-of-support is a security finding in a regulated firm like TCW. I never let a production service drift onto an unsupported runtime.

**Follow-ups**
- *Which do you pick for a new production API?* — The latest LTS, every time. It gives the longest support runway (3 years of security patches), the most stable ecosystem, and the most base images/libraries already tested against it. That means I can build now and not be forced into an upgrade project for roughly two years, which is exactly the rhythm a business can plan around. For a TCW-style regulated platform, "how long until this runtime is unsupported" is a compliance question, and LTS gives me the best answer.
- *When would you use an STS?* — Only for something low-risk that genuinely benefits from a feature that shipped in the odd release, and where I'm comfortable upgrading again in ~18 months. A typical case is an internal admin tool or a spike where I want to try, say, a .NET 7 feature early. I'd never put a customer-facing, regulated service on an STS, because the 18-month clock forces an upgrade sooner than the business wants. The mental model: STS = "early access to try things"; LTS = "where production lives."

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
- *Can you run Framework code on Linux?* — No — .NET Framework is Windows-only by design (it's tied to the Windows OS and IIS). That single limitation is often the whole business case for migrating: modern .NET runs on Linux, so I can move to cheaper Linux VMs, slim Linux containers, and Kubernetes, and cut hosting cost while gaining faster cold starts. On one migration this alone was the headline number the client cared about — Linux container hosting was materially cheaper than the Windows/IIS footprint it replaced.
- *What's the migration tooling?* — The two I lean on are the **.NET Upgrade Assistant** (a CLI/Visual Studio tool that automates much of the project-file and code changes) and the **API portability analyzer** (which scans your Framework code and reports which APIs have modern-.NET equivalents and which don't). I run the portability analyzer first to size the effort and spot blockers, then use the Upgrade Assistant to do the mechanical work.

```bash
# size the migration and drive the mechanical changes
dotnet tool install -g upgrade-assistant
upgrade-assistant analyze .\LegacyApp.sln   # what will need attention
upgrade-assistant upgrade .\LegacyApp.sln   # apply the guided upgrade
```

---

## DW4 · How I plan an upgrade

**Simple explanation.** My upgrade recipe: (1) bump the target framework, (2) update NuGet packages, (3) read the official **breaking-changes** page for that version, (4) run analyzers/tests, (5) fix warnings, (6) load-test, (7) ship to a canary slot behind a flag, (8) roll out.

**Why it matters.** Most upgrades are quick because the cadence is small — but skipping the breaking-changes review is how teams get surprised in production.

**Architect's view:** I upgrade one version at a time even when jumping LTS-to-LTS, so I can isolate any problem to a single release.

**Follow-ups**
- *How long does a typical hop take?* — For a service with a solid automated test suite, an LTS-to-LTS hop is usually hours to a day: bump the `TargetFramework`, update packages, fix a handful of warnings, run the tests, load-test, canary. The tests are what carry the confidence — if I trust them, I trust the upgrade. The hops that drag on are always the ones on codebases with thin test coverage, because then every change has to be verified by hand.
- *Biggest risk?* — By far the most common surprise is a **transitive dependency** — a package your package depends on — that hasn't shipped a build compatible with the new runtime yet. You bump the framework, everything compiles, and then one deep dependency fails at runtime or refuses to restore. That's why I wait a few weeks after a release for the ecosystem to catch up, and why I check the dependency tree (`dotnet list package --include-transitive`) before committing to the hop.

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
- *What about `netstandard2.0`?* — `.NET Standard` is a shared API contract that both .NET Framework and modern .NET implement, so a library targeting `netstandard2.0` can be consumed by *both* worlds. It's still the right target for a shared library that must support legacy Framework apps as well as modern .NET during a long migration. Once every consumer is on modern .NET, I retarget the library to a concrete `net8.0` to unlock the newer APIs that Standard doesn't expose.

```xml
<!-- widest reach: runs on old Framework AND modern .NET -->
<TargetFramework>netstandard2.0</TargetFramework>
```
- *Does multi-targeting slow builds?* — Yes, a little — the compiler builds the project once per target framework, so `net6.0;net8.0` roughly doubles that project's build and test time. Because of that I only multi-target where the compatibility is genuinely required (a shared library with consumers on different runtimes), and I collapse it back to a single target the moment everyone has caught up.

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
- *Do minimal APIs support DI and validation?* — Yes. Handler parameters are resolved automatically — route/query/body values *and* services from the DI container are injected by type. .NET 7 added an **endpoint filter** pipeline (the minimal-API equivalent of action filters) so you can run cross-cutting logic like validation before the handler, and the ecosystem (e.g. FluentValidation, or the built-in `[AsParameters]` binding) covers model validation cleanly.

```csharp
app.MapPost("/orders", (OrderDto dto, IOrderService svc) => svc.CreateAsync(dto))
   .AddEndpointFilter(async (ctx, next) => {
       var dto = ctx.GetArgument<OrderDto>(0);
       if (dto.Total <= 0) return Results.BadRequest("Total must be positive");
       return await next(ctx);
   });
```
- *When not to use them?* — On very large APIs with lots of cross-cutting concerns (complex filters, conventions, shared model binding, big teams needing structure), controllers stay more organised — the ceremony that feels heavy on a tiny service actually earns its keep at scale. My rule of thumb: minimal APIs for focused microservices and a handful of endpoints; controllers once an API grows many endpoints and shared behaviour.

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
- *Where do args go?* — With top-level statements the compiler still gives you the command-line arguments through an implicit `args` variable of type `string[]` — you just use it without declaring it. It's the same array you'd have received as the `Main(string[] args)` parameter.

```csharp
// top-level Program.cs — `args` is available implicitly
if (args.Length > 0) Console.WriteLine($"First arg: {args[0]}");
```
- *Can I still use a classic Program class?* — Absolutely — top-level statements are a convenience, not a mandate. If a team prefers the explicit `class Program { static Main }` shape (for clarity, or to attach attributes, or house-style consistency), that's completely valid and behaves identically. Under the hood the compiler generates an equivalent `Main` for the top-level form anyway, so it's purely a style choice.

---

## DW8 · Hot reload

**Simple explanation.** **.NET 6** added Hot Reload: change code while the app runs and see it update without a full restart — for web, Blazor and desktop.

**Why it matters.** Faster inner loop; I keep app state while tweaking UI or logic.

**Architect's view:** a productivity win for the team; it doesn't change architecture but it speeds delivery.

**Follow-ups**
- *Does every change hot-reload?* — No. Edits *inside* a method body — tweaking logic, changing a string, adjusting markup — apply live. But **structural** changes (adding a new type, changing a method signature, editing fields, altering generics) can't be patched into the running process and still require a full rebuild/restart. In practice the fast, in-body edits are the ones you make most often during UI or logic tweaking, which is where the time saving comes from.
- *Works in CI?* — No, and it isn't meant to. Hot Reload is purely a **developer inner-loop** feature — it speeds up the write-run-see cycle on your machine. CI builds and runtime deployments always do a clean compile from source, so Hot Reload has no role there; it never affects the artifact that ships.

---

## DW9 · record structs

**Simple explanation.** C# 10 / .NET 6 added **record structs** — value-type records with built-in equality, combining struct performance with record convenience.

```csharp
public readonly record struct Money(decimal Amount, string Currency);
```

**Architect's view:** I use them for small, immutable value objects (money, coordinates) on hot paths where I want value semantics without heap allocation.

**Follow-ups**
- *record class vs record struct?* — A `record` (class) is a **reference type** — it lives on the heap and is passed by reference, so copies are cheap but you pay an allocation and GC pressure per instance. A `record struct` is a **value type** — it lives inline (on the stack or embedded in its container), so there's no heap allocation, but it's *copied by value* every time you pass it around. So I choose by cost: many tiny, short-lived values on a hot path → `record struct` to avoid allocations; larger objects or ones passed around a lot → `record` class to avoid copy cost.
- *Are they immutable?* — It depends on the modifier. A `readonly record struct` is fully immutable — the compiler forbids mutating its fields after construction. A plain `record struct` is **mutable** (its auto-properties get setters), which surprises people who expect record = immutable. For value objects I almost always write `readonly record struct` so the immutability guarantee is real.

```csharp
public readonly record struct Money(decimal Amount, string Currency); // immutable
public record struct Point(int X, int Y);   // mutable: p.X = 5; is allowed
```

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
- *Distributed rate limiting across instances?* — The built-in limiter counts requests **per process**, so if I run 4 instances behind a load balancer with a 100/min limit, the real system-wide limit is effectively 400/min. When I need a true **global** limit (e.g. "100/min per customer across the whole cluster"), I back it with a shared store like Redis so all instances read and increment the same counter. So: built-in limiter for simple per-instance protection; Redis-backed counter when the limit must be enforced fleet-wide.
- *What response on limit?* — The standard is HTTP **429 Too Many Requests**, and I always include a **`Retry-After`** header so well-behaved clients know how long to wait before retrying instead of hammering the endpoint.

```csharp
builder.Services.AddRateLimiter(o => {
    o.RejectionStatusCode = StatusCodes.Status429TooManyRequests;
    o.OnRejected = (ctx, _) => {
        ctx.HttpContext.Response.Headers.RetryAfter = "60";
        return ValueTask.CompletedTask;
    };
});
```

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
- *How to invalidate?* — Output caching supports **tags**: you attach one or more tags to a cached route, then call `EvictByTagAsync` when the underlying data changes to purge every response carrying that tag. This is far more precise than waiting for a TTL to expire — the cache stays warm until the data actually changes, then clears exactly the affected entries.

```csharp
app.MapGet("/report/{id}", GetReport).CacheOutput(p => p.Tag("reports"));
// when a report changes:
await outputCacheStore.EvictByTagAsync("reports", ct);
```
- *Can it use Redis?* — Yes. By default output caching stores entries in memory (per instance), but you can plug in a **distributed cache store** (such as Redis) so the cached responses are shared across all instances. That matters behind a load balancer — otherwise each instance keeps its own copy and hit rates suffer. For the TCW reporting APIs I'd back it with Azure Cache for Redis so a warm cache benefits every node.

---

## DW12 · .NET 7 performance

**Simple explanation.** .NET 7 was a big performance release — hundreds of improvements to the JIT, GC, and core libraries, plus **on-stack replacement (OSR)** so hot loops get optimised without restart.

**Architect's view:** "free" speed — recompiling my service on 7 made it faster with zero code change. I quote this when justifying upgrades.

**Follow-ups**
- *How do you prove the gain?* — Never on vibes — I measure. For micro-level changes I use **BenchmarkDotNet** (it handles warmup, multiple runs, and reports mean/allocations reliably), and for the whole service I run a **load test** (k6, JMeter, or Azure Load Testing) against the old and new versions with identical scenarios, comparing throughput (req/s), latency percentiles (p95/p99), and memory. Then I have a real before/after number to justify the upgrade rather than a claim.

```csharp
[MemoryDiagnoser]
public class ParseBench {
    [Benchmark] public int Parse() => int.Parse("12345");
}
// dotnet run -c Release → mean time + bytes allocated, old vs new runtime
```
- *Which workloads benefit most?* — Compute-heavy and high-throughput paths gain the most, because that's where the JIT/GC/BCL improvements compound: tight loops (helped by OSR and PGO), JSON serialization, LINQ over large sets, and high-QPS APIs where lower per-request allocation means less GC pause. I/O-bound code that spends its time waiting on the network or database sees smaller gains, because the runtime isn't the bottleneck there.

---

## DW13 · Native AOT

**Simple explanation.** **.NET 8** matured **Native AOT (Ahead-Of-Time)** compilation: compile straight to a native binary with **no JIT and no runtime needed**. Result: tiny, super-fast-starting, low-memory executables.

**Old vs new.** Normally .NET JIT-compiles at startup (slower cold start, needs the runtime). AOT produces a self-contained native app — ideal for serverless and containers.

**Architect's view:** I use AOT for small, high-density microservices and Azure Functions where cold-start and per-instance memory drive cost. The trade-off: no runtime reflection/dynamic code, so not everything is AOT-compatible.

**Follow-ups**
- *What breaks under AOT?* — Anything that relies on discovering or generating code at **runtime**: heavy **reflection**, `Reflection.Emit`/dynamic code generation, runtime serializers that inspect types on the fly, and some older DI or ORM features. Because AOT trims unused code and there's no JIT to compile new IL at runtime, those patterns either fail to compile or throw at run time. So before committing to AOT I run the publish with warnings-as-errors, check each library's "AOT-compatible" status, and prefer **source-generator**-based alternatives (e.g. `System.Text.Json` source-gen serialization) that produce the code at build time instead.
- *How much faster is start-up?* — The jump is large because there's no JIT warm-up and no runtime to load: cold start often drops from hundreds of milliseconds to single-digit or low-tens of milliseconds, and per-instance memory can fall dramatically (tens of MB instead of hundreds). That's exactly why AOT shines for serverless (Azure Functions) and high-density container workloads — faster scale-out and more instances per node directly cut cost. As always I confirm the actual numbers with a benchmark on the specific service.

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
- *Overuse risk?* — Keyed DI is great for "one interface, a few interchangeable flavours," but if you find yourself with a dozen string keys it usually means the abstraction is doing too much and the keys have become a hidden, stringly-typed switch statement. In those cases separate, well-named interfaces (or a proper strategy/factory with an enum) are clearer and safer than a pile of magic strings. My rule: reach for keyed services when the implementations are genuinely the same shape (payment providers, notifiers); split into distinct interfaces when they start to diverge.
- *Works with `IEnumerable<T>`?* — Yes — keyed registrations don't stop you injecting the whole set. When you need *all* implementations (e.g. run every validator, or fan out to every notifier), you can still resolve them as a collection, and you can also resolve a specific one by key when you need just that flavour.

```csharp
// resolve one by key
public class OrderService([FromKeyedServices("sms")] INotifier notifier) { }
// or resolve them all when you need the full set
public class Broadcaster(IEnumerable<INotifier> all) {
    public Task NotifyEveryone(string msg) => Task.WhenAll(all.Select(n => n.SendAsync(msg)));
}
```

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
- *Also for timers/delays?* — Yes — `TimeProvider` isn't just "what time is it," it can also **create timers** and provides `Delay`, so any waiting logic becomes fakeable too. In a test you advance the fake clock and the delay/timer fires immediately, turning what would be a slow, flaky `await Task.Delay(...)` test into a fast, deterministic one.

```csharp
// production code takes TimeProvider and uses its delay
await clock.Delay(TimeSpan.FromMinutes(5), ct);
// test: no real waiting
var fake = new FakeTimeProvider();
fake.Advance(TimeSpan.FromMinutes(5)); // the delay completes instantly
```
- *Where does FakeTimeProvider live?* — In the **`Microsoft.Extensions.TimeProvider.Testing`** NuGet package. I add it to the test project only, then inject a `FakeTimeProvider` in place of the real `TimeProvider.System` so tests can set and advance "now" precisely.

---

## DW16 · Blazor render modes

**Simple explanation.** **.NET 8** unified Blazor: one model where each component can render **Server**, **WebAssembly**, **Auto**, or **static SSR** — pick per component.

**Old vs new.** Previously you chose Blazor Server *or* Blazor WASM up front. Now it's a per-component decision with streaming SSR.

**Architect's view:** static SSR for content pages, interactive modes only where needed — best of both without committing the whole app.

**Follow-ups**
- *What's "Auto"?* — **Auto** render mode gives users the best of both: on the first visit the component renders in **Blazor Server** mode (interactive almost instantly over a SignalR connection, because nothing large has to download), and meanwhile the **WebAssembly** runtime and app download in the background. On the next visit — once WASM is cached — it runs fully client-side with no server round-trips. So you get a fast first load *and* a scalable, offline-capable experience later, without choosing one model up front.
- *Do I need it?* — Only if you're building with **Blazor**. For a React or Angular shop (which is the TCW front-end reality) this is background knowledge, not something I'd use — the equivalent conversation there is CSR vs SSR/hydration in Next.js or Angular Universal. I keep it in my toolkit for .NET-first teams or internal tools where staying entirely in C# across the stack is valuable.

---

## DW17 · .NET 9 highlights

**Simple explanation.** **.NET 9** (STS) focuses on performance and cloud: better GC (adaptive server GC), more AOT scenarios, `HybridCache`, improved LINQ, and OpenAPI document generation built in (replacing Swashbuckle's default role).

**Architect's view:** I treat 9 as a preview of what lands in the next LTS (10). I trial its features on internal tools, keep production on 8 until 10.

**Follow-ups**
- *Built-in OpenAPI — does it replace Swagger UI?* — Not entirely. .NET 9's built-in support (`Microsoft.AspNetCore.OpenApi`) generates the **OpenAPI JSON document** at runtime — that's the machine-readable contract. It does **not** ship the interactive HTML "try it out" page. So if I want a browsable UI I still add one (Swagger UI, or the lighter **Scalar**) pointed at that generated JSON. The net change is that the document generation moved into the framework, and the UI became a separate, swappable choice.

```csharp
builder.Services.AddOpenApi();      // generates the JSON doc (.NET 9)
app.MapOpenApi();                   // serves /openapi/v1.json
app.MapScalarApiReference();        // optional: a UI on top of it
```
- *Worth upgrading prod to 9?* — Usually not — 9 is an STS with only an 18-month support window, so for production I generally hold on the current LTS (8) and jump straight to the next LTS (10). The exception is when a specific .NET 9 feature (say `HybridCache` or a particular performance win) delivers real value now and I'm comfortable upgrading again within the year. Prod lives on LTS by default; STS is where I trial, not where I settle.

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
- *What's stampede protection?* — A **cache stampede** (or "thundering herd") happens when a popular cached value expires and, in the same instant, hundreds of concurrent requests all miss the cache and all hit the database at once to recompute it — often overwhelming the DB. HybridCache prevents this by ensuring that for a given key, **only the first caller computes** the value while the others wait for that single result and then share it. On the TCW reporting APIs this is exactly the failure mode you get when a heavy report's cache entry lapses at market open; stampede protection turns hundreds of duplicate DB hits into one.
- *Tag invalidation?* — Yes. Like output caching, HybridCache lets you attach **tags** to cached entries and then evict a whole group at once when related data changes, rather than clearing keys one by one or waiting for TTLs.

```csharp
var report = await cache.GetOrCreateAsync(key,
    async ct => await LoadReportAsync(ct),
    tags: ["reports"]);
// when reports change:
await cache.RemoveByTagAsync("reports");
```

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
- *What is `with`?* — The `with` expression performs a **non-destructive mutation**: it creates a *new* record that's a copy of the original with only the named properties changed, leaving the original untouched. This is how you "change" an immutable object safely — you never mutate it, you produce an updated copy. It's invaluable in state management (Redux-style reducers, event sourcing) where you want a new value rather than an in-place edit.

```csharp
var a = new Customer(1, "Sam");
var b = a with { Name = "Sam Two" }; // b is new; a is unchanged
```
- *Are records always immutable?* — Not strictly, but they default toward it. **Positional** record properties are generated as `init`-only, so they can only be set at construction — effectively immutable. However, you *can* add ordinary `{ get; set; }` properties to a record, which makes those parts mutable. My convention is to keep records fully immutable (positional or `init`-only) so their value-equality and "safe to share" guarantees actually hold; if I need mutation I usually reach for a class instead.

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
- *Does it change runtime behaviour?* — No — nullable reference types are **purely compile-time** analysis. The `?` annotations and the warnings they produce are erased when the code compiles; the generated IL is identical whether NRT is on or off, and there's no runtime null-checking added. The whole value is catching "this could be null" at build time (ideally as a CI error) instead of discovering it as a `NullReferenceException` in production.
- *The `!` operator?* — That's the **null-forgiving operator** — it tells the compiler "trust me, this isn't null here," suppressing the warning without changing runtime behaviour. It's an escape hatch, so I use it sparingly and only when I can genuinely prove non-null (e.g. right after a check the analyzer can't follow); scattering `!` everywhere just silences the safety net I turned on in the first place.

```csharp
string? maybe = GetName();
if (maybe is null) throw new InvalidOperationException();
int len = maybe!.Length; // justified: proven non-null above
```

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
- *Property patterns?* — Yes — **property patterns** let you match on an object's members inline, which replaces a chain of `&&` conditions with one readable expression. You can nest them, combine them with relational/logical patterns, and even deconstruct, so complex "does this object look like X" checks become a single, self-documenting pattern.

```csharp
if (person is { Age: > 18, Address.Country: "US" }) { /* adult US resident */ }
var fee = order switch { { Total: > 1000, IsVip: true } => 0m, _ => 9.99m };
```
- *Any downside?* — The main risk is over-cleverness: deeply nested patterns, exotic list patterns, or long `switch` arms can become harder to read than the plain `if/else` they replaced. Pattern matching is a readability tool, so if a pattern needs a second read to understand, I break it into named checks. I keep patterns shallow and obvious and let the compiler's exhaustiveness warnings do the heavy lifting.

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
- *Can it hide dependencies?* — A little — because a `global using` (or an implicit one) makes a namespace available everywhere without appearing at the top of each file, a reader can't tell at a glance where a type came from. That's a minor readability cost. I manage it by keeping global usings **few, obvious, and in one file** (`GlobalUsings.cs`), reserving them for genuinely ubiquitous namespaces (e.g. `System`, `System.Linq`, the project's core namespace) rather than niche ones, so nothing surprising is silently in scope.
- *Per-project?* — Yes — global and implicit usings are scoped **per project**, not solution-wide. Each project declares its own set (via its own `GlobalUsings.cs` and its `<ImplicitUsings>` setting), so importing a namespace globally in one project has no effect on another. That keeps each project's "ambient" namespaces explicit and independent.

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
