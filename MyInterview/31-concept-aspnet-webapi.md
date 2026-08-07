# 31 · Concept: ASP.NET Core Web API & C# (30 questions)

[← React vs Angular](30-concept-react-vs-angular.md) · [Home](README.md) · [Next → Concept: FastAPI](32-concept-fastapi.md)

This file explains **ASP.NET Core Web API** with **C#** simply and in depth. I built the Web API layer on TCW (Project A) and defined a reusable controller pattern the whole team reuses, so I answer from real code.

> Simple one-liner: *"ASP.NET Core Web API is Microsoft's framework for building fast, cross-platform HTTP APIs in C#. A client sends an HTTP request, it flows through a middleware pipeline to a controller, which returns data — usually JSON."*

**Jump to (fundamentals):** [W1 What it is](#w1--what-is-aspnet-core-web-api) · [W2 Controllers & routing](#w2--controllers-actions-and-routing) · [W3 Middleware pipeline](#w3--the-middleware-pipeline) · [W4 Dependency injection](#w4--dependency-injection) · [W5 async/await](#w5--asyncawait-and-why-it-matters) · [W6 Model binding & validation](#w6--model-binding-and-validation) · [W7 EF Core & data](#w7--entity-framework-core-and-data-access) · [W8 Auth & status codes](#w8--authentication-and-status-codes)
> **Design & REST:** [W9 REST principles](#w9--rest-principles-and-good-api-design) · [W10 Versioning](#w10--api-versioning) · [W11 DTOs & mapping](#w11--dtos-and-mapping) · [W12 Error handling](#w12--global-error-handling) · [W13 Status codes deep](#w13--choosing-the-right-status-code) · [W14 Idempotency](#w14--idempotency-and-safe-methods)
> **Architecture:** [W15 Layered/Clean](#w15--layered-and-clean-architecture) · [W16 Repository & UoW](#w16--repository-and-unit-of-work) · [W17 CQRS & MediatR](#w17--cqrs-and-mediatr) · [W18 Minimal APIs](#w18--minimal-apis-vs-controllers) · [W19 Config & options](#w19--configuration-and-options) · [W20 Background work](#w20--background-jobs-and-hosted-services)
> **Production & performance:** [W21 Caching](#w21--caching) · [W22 Performance tuning](#w22--performance-tuning) · [W23 Resilience](#w23--resilience-retries-and-polly) · [W24 Rate limiting](#w24--rate-limiting-and-throttling) · [W25 Logging & telemetry](#w25--logging-and-observability) · [W26 Health checks](#w26--health-checks-and-readiness)
> **Testing, security & deploy:** [W27 Testing](#w27--testing-the-api) · [W28 Security hardening](#w28--security-hardening) · [W29 Deployment & Azure](#w29--deployment-and-azure-hosting) · [W30 Microservices](#w30--monolith-vs-microservices) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of ASP.NET Core Web API in plain English. I built the Web API layer on TCW (A) and a reusable controller pattern the team still reuses, so this is how I actually hold it in my head. Get these ideas and every question below is a detail hanging off one of them.

**1. It's a framework for HTTP APIs in C#.** The job is simple: a client sends an HTTP request, my service does work, and returns data — usually JSON. It's cross-platform, open-source and very fast. Everything else is *how* the request gets from the wire to my code and back.

**2. The request journey is the spine.** A request flows: **middleware pipeline** (auth, logging, exception handling) → **routing** picks a **controller action** → the action calls **services** to do work → returns a result that gets serialized to JSON. If I can draw that pipeline, I can explain almost anything in the file.

**3. Dependency injection is built in.** Services are registered once and injected where needed, with lifetimes (singleton, scoped, transient) I choose deliberately. DI is what keeps controllers thin and code testable — I inject a service, not `new` it up.

**4. async/await is not optional at scale.** API work is mostly I/O — database, HTTP, files. Async frees the thread while waiting, so the server handles far more concurrent requests with the same hardware. On A, everything touching the DB is async end to end.

**5. Model binding and validation guard the boundary.** Incoming JSON is bound to typed C# models and validated (data annotations / FluentValidation) *before* my logic runs. Bad data is rejected at the door with a clean 400, so business code only ever sees valid input.

**6. REST and status codes are the contract.** Good API design means predictable resources, correct verbs, honest status codes (200/201/204/400/404/409/500), versioning, and DTOs that decouple the wire shape from my entities. The contract is what clients depend on, so I treat it with care.

**7. Architecture keeps it maintainable.** Layered/Clean architecture, repositories, CQRS/MediatR, minimal APIs vs controllers, configuration and options, background/hosted services — these are the patterns that stop a growing API turning into spaghetti. My reusable controller pattern on A is exactly this: structure so new reports plug in instead of being hand-coded.

**The full-stack / architect lens:** the later Q&As go into production concerns — caching, performance tuning, resilience and retries (Polly), rate limiting, logging and observability, health checks, testing, security hardening, Azure deployment, and monolith vs microservices. That's the difference between "it works on my machine" and "it survives under load, at 3am, in production."

**One rule I never break:** *keep controllers thin — they translate HTTP to a service call and back; all real logic lives in tested, injected services.*

---

## W1 · What is ASP.NET Core Web API?

**Simple explanation.** It's the part of ASP.NET Core for building **web APIs** — services that return data (JSON) rather than HTML pages. Other apps (a React front end, a mobile app, another service) call it over HTTP. It's **cross-platform** (Windows/Linux/Mac), open-source, and very fast.

**The request journey:** client → **middleware pipeline** (auth, logging, etc.) → **routing** picks a **controller action** → the action does work (often via services) → returns a result serialized to JSON.

*"On TCW my Web API layer sits between the React screens and the data — I built a reusable controller + Web API pattern so new reports plug in instead of being coded from scratch."*

**Follow-ups**
- *".NET Framework vs .NET Core?"* — .NET Core (now just ".NET") is the modern, cross-platform, faster successor. New work should use it.
- *"REST vs the alternatives?"* — REST over HTTP/JSON is my default; gRPC for high-performance internal service-to-service; GraphQL when clients need flexible queries.

---

## W2 · Controllers, actions, and routing

**Simple explanation.** A **controller** is a C# class grouping related endpoints. Each method is an **action** mapped to an HTTP verb + route. **Routing** decides which action handles an incoming URL.

```csharp
[ApiController]
[Route("api/reports")]
public class ReportsController : ControllerBase
{
    private readonly IReportService _reports;
    public ReportsController(IReportService reports) => _reports = reports;   // DI

    [HttpGet("{type}")]                       // GET /api/reports/equity
    public async Task<ActionResult<Report>> Get(string type)
    {
        var report = await _reports.GetAsync(type);
        return report is null ? NotFound() : Ok(report);   // 404 or 200
    }
}
```

`[ApiController]` adds helpful behaviours (automatic model validation, sensible defaults). `ControllerBase` gives helpers like `Ok()`, `NotFound()`, `BadRequest()`.

**Follow-ups**
- *"Attribute vs conventional routing?"* — For APIs I use attribute routing (`[HttpGet("{id}")]`) — it's explicit and lives next to the action.
- *"Why `ActionResult<T>`?"* — It lets me return either the typed data *or* a status result (like `NotFound()`) from one method.

---

## W3 · The middleware pipeline

**Simple explanation.** Every request passes through a **pipeline** of middleware components, in order — like a series of checkpoints. Each can act on the request, pass it on, and act on the response coming back. Order matters.

```csharp
var app = builder.Build();
app.UseExceptionHandler("/error");  // catch errors first
app.UseHttpsRedirection();
app.UseAuthentication();            // who are you?
app.UseAuthorization();             // are you allowed?
app.MapControllers();               // finally, route to controllers
app.Run();
```

**Analogy:** airport security lanes — each checkpoint (logging, auth) runs in sequence before you reach the gate (the controller).

**Follow-ups**
- *"Why does order matter?"* — e.g. authentication must run before authorization; exception handling must be early to catch everything after it.
- *"Write custom middleware?"* — Yes — for cross-cutting concerns like request logging, correlation IDs, or rate limiting.

---

## W4 · Dependency injection

**Simple explanation.** DI is **built into** ASP.NET Core. You register services once, and the framework supplies them wherever needed (like a controller constructor). This keeps code loosely coupled and testable.

```csharp
builder.Services.AddScoped<IReportService, ReportService>();
```

Three lifetimes — a classic question:
- **Transient** — a new instance every time it's requested.
- **Scoped** — one instance per HTTP request (most common for services/DB context).
- **Singleton** — one instance for the whole app.

**Follow-ups**
- *"Which lifetime for a DbContext?"* — **Scoped** — one per request, so it isn't shared across requests (which would break).
- *"Danger of injecting Scoped into Singleton?"* — A captive dependency bug — the scoped object lives too long. The framework warns you.

---

## W5 · async/await and why it matters

**Simple explanation.** APIs spend most time **waiting** on I/O — databases, other services. `async/await` lets a thread *release* while waiting instead of blocking, so the server handles far more concurrent requests with the same threads. This is critical for throughput.

```csharp
public async Task<Report> GetAsync(string type)
{
    // 'await' frees the thread while the DB works
    return await _db.Reports.FirstOrDefaultAsync(r => r.Type == type);
}
```

**Rule:** go async **all the way down** — don't block on async code with `.Result` or `.Wait()`, which can deadlock.

**Follow-ups**
- *"Does async make one request faster?"* — Not that single request — it improves **scalability** (more requests served at once) by not tying up threads while waiting.
- *"Most common async mistake?"* — Blocking with `.Result`/`.Wait()` (deadlocks/thread starvation), or `async void` (except event handlers).

---

## W6 · Model binding and validation

**Simple explanation.** **Model binding** automatically maps incoming request data (JSON body, route, query) onto C# parameters/objects. **Validation** checks those objects using data annotations before your code runs.

```csharp
public class CreateReportRequest
{
    [Required] public string Type { get; set; } = "";
    [Range(1, 1000)] public int MaxRows { get; set; }
}

[HttpPost]
public IActionResult Create(CreateReportRequest req)
{
    // With [ApiController], invalid models auto-return 400 before we get here
    return Ok();
}
```

**Follow-ups**
- *"Where does the 400 come from?"* — `[ApiController]` auto-returns `400 Bad Request` with the validation errors if the model is invalid — no manual check needed.
- *"Complex/custom validation?"* — Use `IValidatableObject` or a library like FluentValidation for rules that span multiple fields.

---

## W7 · Entity Framework Core and data access

**Simple explanation.** **EF Core** is Microsoft's ORM — it maps C# classes to database tables so I query with LINQ instead of raw SQL. Great for productivity; I still drop to SQL for hot paths.

```csharp
var rows = await _db.Positions
    .Where(p => p.PortfolioId == id)          // becomes a WHERE clause
    .OrderByDescending(p => p.MarketValue)
    .ToListAsync();
```

**Watch out for the N+1 problem** — lazily loading a child per row in a loop fires one query per row. Fix with `.Include()` (eager load) or a projection.

**Follow-ups**
- *"EF Core vs Dapper vs raw SQL?"* — EF Core for productivity; Dapper (micro-ORM) or raw SQL for performance-critical queries where I want full control.
- *"How do you catch a slow EF query?"* — Log the generated SQL, check the execution plan, and rewrite as a projection or tuned query — exactly the performance work I do on TCW.

---

## W8 · Authentication and status codes

**Simple explanation.** **Authentication** = who you are; **Authorization** = what you're allowed to do. In Azure apps I use **Microsoft Entra ID** (formerly Azure AD) with **JWT bearer tokens** — the client sends a token, middleware validates it, and `[Authorize]` guards endpoints.

```csharp
[Authorize(Roles = "Analyst")]
[HttpGet("{type}")]
public Task<ActionResult<Report>> Get(string type) => /* ... */;
```

**HTTP status codes I return correctly:** `200 OK`, `201 Created`, `400 Bad Request` (bad input), `401 Unauthorized` (not logged in), `403 Forbidden` (no permission), `404 Not Found`, `500` (server error).

**Follow-ups**
- *"401 vs 403?"* — 401 = I don't know who you are (log in); 403 = I know who you are, but you're not allowed.
- *"Where do secrets/tokens config live?"* — Never in code — in Azure Key Vault / app configuration, injected at runtime.

---

## W9 · REST principles and good API design

**Simple explanation.** REST is a style for HTTP APIs: model **resources** as nouns (`/reports`, `/portfolios/{id}`), use **HTTP verbs** for actions (GET read, POST create, PUT/PATCH update, DELETE remove), and keep each request **stateless** (the server stores no session between calls — everything needed is in the request/token).

Good design I insist on: plural nouns not verbs in URLs (`/reports`, never `/getReports`), nest relationships (`/portfolios/{id}/positions`), filter/sort/page via query strings (`?page=2&sort=-marketValue`), and return the correct status code every time.

*"On TCW I standardised the URL and response conventions so every new report endpoint looks the same — predictable for the React team consuming it."*

**Follow-ups**
- *"Why stateless?"* — Any server instance can handle any request, so it scales horizontally behind a load balancer with no sticky sessions.
- *"PUT vs PATCH?"* — PUT replaces the whole resource; PATCH updates part of it. I use PATCH for partial edits.
- *"What makes an API 'RESTful' vs just HTTP?"* — Resource nouns, correct verbs, statelessness, and meaningful status codes — not RPC-style verbs in the URL.

---

## W10 · API versioning

**Simple explanation.** Once clients depend on your API, you can't break them — so you **version** it. Common approaches: URL segment (`/api/v2/reports`), a header (`api-version: 2`), or a query string. I usually pick URL versioning because it's the most visible and cache-friendly.

```csharp
builder.Services.AddApiVersioning(o => { o.DefaultApiVersion = new ApiVersion(1, 0); o.AssumeDefaultVersionWhenUnspecified = true; });
[ApiVersion("2.0")] [Route("api/v{version:apiVersion}/reports")]
public class ReportsV2Controller : ControllerBase { /* ... */ }
```

**Follow-ups**
- *"When do you bump a version?"* — Only for **breaking** changes (removing a field, changing a type). Additive changes (new optional field) don't need a new version.
- *"How long support old versions?"* — Announce a deprecation window, monitor usage, and retire once clients have migrated.

---

## W11 · DTOs and mapping

**Simple explanation.** A **DTO** (Data Transfer Object) is a class shaped for the API contract — separate from your database entities. You never expose EF entities directly, because that leaks internal columns, risks over-posting attacks, and couples your API to your schema.

```csharp
public record ReportDto(string Type, decimal Total, DateOnly AsOf);   // API shape
// map entity -> DTO (by hand or with a mapper library)
var dto = new ReportDto(r.Type, r.Total, r.AsOf);
```

*"I keep entities for the database and DTOs for the wire; the React team codes against stable DTOs even if I refactor the tables underneath."*

**Follow-ups**
- *"What's over-posting?"* — A client sets fields it shouldn't (like `IsAdmin`) by binding straight to an entity. A request DTO with only allowed fields prevents it.
- *"AutoMapper — yes or no?"* — Handy for lots of mappings, but I keep hot/critical maps explicit for clarity and to avoid hidden surprises.

---

## W12 · Global error handling

**Simple explanation.** I never let raw exceptions leak to clients. A single **exception-handling middleware** catches everything, logs the detail server-side, and returns a clean, consistent error body — ideally the standard **ProblemDetails** format.

```csharp
app.UseExceptionHandler(exApp => exApp.Run(async ctx => {
    var ex = ctx.Features.Get<IExceptionHandlerFeature>()?.Error;
    logger.LogError(ex, "Unhandled");
    await Results.Problem(title: "An error occurred", statusCode: 500).ExecuteAsync(ctx);
}));
```

**Follow-ups**
- *"Why not try/catch in every controller?"* — Repetitive and easy to miss. One place guarantees consistent handling and logging.
- *"What is ProblemDetails?"* — A standard JSON error shape (RFC 7807) with `title`, `status`, `detail` — clients parse errors uniformly.
- *"Show stack traces to clients?"* — Never in production — it leaks internals. Log it server-side; return a safe message.

---

## W13 · Choosing the right status code

**Simple explanation.** Status codes are the API's language. I use them precisely: `200 OK` (read/update ok), `201 Created` (new resource, with a `Location` header), `202 Accepted` (async work started), `204 No Content` (success, nothing to return, e.g. DELETE), `400` (bad input), `401`/`403` (auth), `404` (not found), `409 Conflict` (e.g. duplicate/version clash), `422` (validation), `429` (too many requests), `500` (server fault).

**Follow-ups**
- *"200 vs 201 vs 204?"* — 201 for a created resource, 204 when there's nothing to send back, 200 otherwise.
- *"When 409?"* — A conflict with current state — like creating a duplicate or an optimistic-concurrency mismatch.
- *"400 vs 422?"* — 400 = malformed request; 422 = well-formed but fails business validation. Many teams use 400 for both — be consistent.

---

## W14 · Idempotency and safe methods

**Simple explanation.** A **safe** method doesn't change data (GET). An **idempotent** method gives the same result no matter how many times it's called (GET, PUT, DELETE). POST is *not* idempotent — calling it twice creates two records. For critical POSTs (payments), I add an **idempotency key** header so a retried request is de-duplicated.

**Follow-ups**
- *"Why does idempotency matter?"* — Networks retry. If a client resends a create after a timeout, an idempotency key stops a duplicate charge/order.
- *"How implement it?"* — Client sends a unique key; the server stores it and returns the original result on any repeat with the same key.

---

## W15 · Layered and Clean Architecture

**Simple explanation (architect lens).** I split the app into layers so responsibilities are clear and dependencies point **inward**:
- **API/Presentation** — controllers, DTOs (HTTP concerns only).
- **Application** — use-cases/business logic, orchestration.
- **Domain** — core entities and rules (no framework dependencies).
- **Infrastructure** — EF Core, external services, files.

Controllers stay thin — they validate input and call the application layer; business rules never live in controllers. This is the structure of my reusable TCW pattern.

**Follow-ups**
- *"Why should dependencies point inward?"* — So the domain doesn't depend on EF or the web — you can swap the database or UI without touching business rules, and it's easy to test.
- *"Isn't this over-engineering for a small API?"* — Yes for a tiny CRUD app — I scale the layering to the app's size; small apps can be simpler.

---

## W16 · Repository and Unit of Work

**Simple explanation.** A **repository** wraps data access behind an interface (`IReportRepository`) so the rest of the app doesn't know it's EF Core. **Unit of Work** groups multiple changes into one transaction that commits together.

**Nuance I mention:** EF Core's `DbContext` **already is** a Unit of Work, and `DbSet` is already repository-like — so I only add explicit repositories when I need to hide EF for testing or swap providers, not by reflex.

**Follow-ups**
- *"Do you always use the repository pattern?"* — No — it can be needless abstraction over EF. I add it when it earns its keep (testability, provider independence).
- *"How does Unit of Work map to EF?"* — `SaveChanges()` commits all tracked changes in one transaction — that's the Unit of Work.

---

## W17 · CQRS and MediatR

**Simple explanation.** **CQRS** (Command Query Responsibility Segregation) separates **writes** (commands that change data) from **reads** (queries that return data), so each is optimised independently. **MediatR** is a popular C# library that sends each command/query to its own handler, keeping controllers tiny.

```csharp
public record GetReport(string Type) : IRequest<ReportDto>;
public class GetReportHandler : IRequestHandler<GetReport, ReportDto> { /* ... */ }
// controller: return await _mediator.Send(new GetReport(type));
```

**Follow-ups**
- *"When is CQRS worth it?"* — Complex domains, or when read and write models differ a lot (e.g. reads from a denormalised store). Overkill for simple CRUD.
- *"Does CQRS require two databases?"* — No — that's an optional extreme. It's primarily about separating the *code paths* for reads and writes.

---

## W18 · Minimal APIs vs controllers

**Simple explanation.** **Minimal APIs** (from .NET 6) let you define endpoints as lambdas without controller classes — less ceremony, great for small services and microservices. **Controllers** offer more structure (filters, model binding conventions) for larger apps.

```csharp
app.MapGet("/reports/{type}", async (string type, IReportService s) => await s.GetAsync(type));
```

**Follow-ups**
- *"Which do you choose?"* — Minimal APIs for small, focused services; controllers for large APIs where the extra structure and filters pay off.
- *"Any performance difference?"* — Minimal APIs are slightly leaner, but for most apps the choice is about structure, not speed.

---

## W19 · Configuration and options

**Simple explanation.** ASP.NET Core reads config from layered sources — `appsettings.json`, environment variables, and (in Azure) Key Vault / App Configuration — with later sources overriding earlier. I bind settings to strongly-typed classes with the **Options pattern**.

```csharp
builder.Services.Configure<AladdinOptions>(builder.Configuration.GetSection("Aladdin"));
// inject IOptions<AladdinOptions> where needed
```

**Follow-ups**
- *"Where do secrets go?"* — Never in `appsettings.json` in source control — Key Vault in production, user-secrets locally.
- *"IOptions vs IOptionsMonitor?"* — `IOptionsMonitor` picks up config changes at runtime; `IOptions` is a fixed snapshot.

---

## W20 · Background jobs and hosted services

**Simple explanation.** For work that shouldn't block the HTTP request — sending emails, processing a queue, scheduled jobs — I use `IHostedService` / `BackgroundService`, or offload to Azure Functions / a queue worker for heavier or independently-scaled work.

```csharp
public class QueueWorker : BackgroundService {
    protected override async Task ExecuteAsync(CancellationToken ct) {
        while (!ct.IsCancellationRequested) { /* process a message */ await Task.Delay(1000, ct); }
    }
}
```

**Follow-ups**
- *"In-process worker vs Azure Function?"* — In-process for light background tasks tied to the app; a separate Function/worker when it must scale or fail independently.
- *"How do you not lose work on restart?"* — Use a durable queue (Service Bus) so messages survive and retry, rather than in-memory state.

---

## W21 · Caching

**Simple explanation.** Caching stores results so you don't recompute or re-query them. Levels I use: **in-memory cache** (fast, per-instance), **distributed cache** (Redis — shared across instances), and **response/output caching** (cache whole responses). Cache read-heavy, slow-changing data; always set an expiry and a way to invalidate.

```csharp
var report = await _cache.GetOrCreateAsync($"report:{type}", async e => {
    e.AbsoluteExpirationRelativeToNow = TimeSpan.FromMinutes(5);
    return await _reports.GetAsync(type);
});
```

**Follow-ups**
- *"In-memory vs Redis?"* — In-memory is fastest but per-server (inconsistent across a scaled-out app); Redis is shared and consistent for multiple instances.
- *"Cache invalidation — the hard part?"* — Yes — I expire by time and bust the key on writes; stale financial data is dangerous, so I cache conservatively.

---

## W22 · Performance tuning

**Simple explanation.** My API performance checklist (real TCW work): go **async all the way**, fix **N+1** EF queries (`.Include`/projection), select only needed columns (`.Select` into a DTO), add **caching** for hot reads, use **pagination** for big lists, enable **response compression**, and pool connections. I always measure first with Application Insights before optimising.

**Follow-ups**
- *"Biggest real-world win you've had?"* — On TCW, rewriting a slow report query (fixing a non-sargable predicate + N+1) protected the pre-market deadline.
- *"How do you find the slow part?"* — Application Insights dependency timings show whether it's the DB, an external call, or my code — I optimise the proven bottleneck.
- *"AsNoTracking?"* — For read-only EF queries, `AsNoTracking()` skips change-tracking overhead and speeds reads.

---

## W23 · Resilience: retries and Polly

**Simple explanation.** Networks and downstream services fail transiently. I make calls resilient with **Polly** (or the built-in resilience handler): **retry with backoff**, **circuit breaker** (stop hammering a dead service), and **timeouts**.

```csharp
builder.Services.AddHttpClient("aladdin").AddStandardResilienceHandler();   // retries + circuit breaker + timeout
```

**Follow-ups**
- *"What's a circuit breaker?"* — After repeated failures it "opens" and fails fast for a while, giving the downstream time to recover instead of piling on load.
- *"Retry everything?"* — Only **idempotent** calls — retrying a non-idempotent POST could duplicate an action (see [W14](#w14--idempotency-and-safe-methods)).

---

## W24 · Rate limiting and throttling

**Simple explanation.** To protect the API from overload or abuse, I limit how many requests a client can make in a window. .NET has **built-in rate limiting** middleware (fixed window, sliding window, token bucket, concurrency).

```csharp
builder.Services.AddRateLimiter(o => o.AddFixedWindowLimiter("api", w => { w.PermitLimit = 100; w.Window = TimeSpan.FromMinutes(1); }));
app.UseRateLimiter();
```

**Follow-ups**
- *"What do you return when limited?"* — `429 Too Many Requests`, ideally with a `Retry-After` header.
- *"Where else can you throttle?"* — At the gateway (Azure API Management / App Gateway) for a first line of defence before requests reach the app.

---

## W25 · Logging and observability

**Simple explanation.** You can't fix what you can't see. I use **structured logging** (`ILogger` with named properties, not string concatenation), **Application Insights** for traces/metrics/dependencies, and **correlation IDs** so one request can be traced across services.

```csharp
_logger.LogInformation("Report {Type} returned {Rows} rows in {Ms}ms", type, rows.Count, ms);
```

**Follow-ups**
- *"Why structured over plain text?"* — You can query/filter by properties (all logs where `Type=equity` and `Ms>500`) — essential for triage.
- *"The three pillars of observability?"* — Logs, metrics, traces — App Insights gives all three; I use them to catch slow queries before they breach a deadline.

---

## W26 · Health checks and readiness

**Simple explanation.** Cloud platforms need to know if the app is alive and ready. ASP.NET Core has built-in **health checks** — a **liveness** probe (is the process up?) and a **readiness** probe (can it serve traffic, e.g. DB reachable?).

```csharp
builder.Services.AddHealthChecks().AddSqlServer(conn).AddAzureBlobStorage(blobConn);
app.MapHealthChecks("/health");
```

**Follow-ups**
- *"Liveness vs readiness?"* — Liveness = restart me if I'm dead; readiness = don't send traffic until dependencies are up. Kubernetes/App Service use these.
- *"Why check dependencies?"* — So the load balancer routes away from an instance that can't reach its database.

---

## W27 · Testing the API

**Simple explanation.** I test at three levels: **unit tests** (xUnit + Moq for services/handlers, no DB), **integration tests** (`WebApplicationFactory` spins up the real pipeline against an in-memory or test DB), and a few **end-to-end** checks on critical journeys.

```csharp
var client = _factory.CreateClient();
var resp = await client.GetAsync("/api/reports/equity");
resp.StatusCode.Should().Be(HttpStatusCode.OK);
```

**Follow-ups**
- *"Unit vs integration — balance?"* — Many fast unit tests for logic; targeted integration tests for routing, model binding, auth and DB behaviour.
- *"How does DI help testing?"* — I inject fakes/mocks for dependencies, so I test a controller or handler in isolation.

---

## W28 · Security hardening

**Simple explanation.** Beyond auth, I harden the API: **HTTPS everywhere** + HSTS, validate/allow-list all input, **parameterised queries / EF** (no string SQL) to stop injection, tight **CORS** (only my front-end origin), **security headers**, secrets in **Key Vault** via Managed Identity, and least-privilege on every resource.

**Follow-ups**
- *"OWASP Top 10 — which hit APIs most?"* — Broken access control and injection top the list — I counter with server-side authorisation on every endpoint and parameterised data access.
- *"How do you manage secrets safely?"* — Key Vault + Managed Identity so no secret is stored in code or config, and access is logged.
- *"Mass assignment protection?"* — Request DTOs with only allowed fields (see [W11](#w11--dtos-and-mapping)).

---

## W29 · Deployment and Azure hosting

**Simple explanation.** I containerise the API (Docker) and host it on **Azure App Service** or **Azure Container Apps / AKS**, with **CI/CD** (Azure DevOps / GitHub Actions) building, testing and deploying automatically. **Deployment slots** give zero-downtime releases and instant rollback via swap.

**Follow-ups**
- *"App Service vs Container Apps vs AKS?"* — App Service for straightforward web APIs; Container Apps for serverless containers/microservices; AKS when I need full Kubernetes control.
- *"How do you release safely?"* — Deploy to a staging slot, smoke-test, then swap into production — rollback is just swapping back.
- *"How does the app get its secrets in Azure?"* — Managed Identity reads Key Vault at startup — no secrets in the pipeline.

---

## W30 · Monolith vs microservices

**Simple explanation (architect lens).** A **monolith** is one deployable app — simplest to build, test and deploy; the right default. **Microservices** split the system into small, independently-deployable services — powerful for scaling teams and parts independently, but they add real complexity (networking, data consistency, observability).

**My mature take:** start with a **well-structured (modular) monolith** and extract microservices only when a clear need appears (independent scaling, team autonomy). On TengizChevroil the platform *was* microservices with Service Bus messaging because the domains and teams genuinely warranted it — I don't reach for them by fashion.

**Follow-ups**
- *"Biggest microservices pitfall?"* — Distributed data — no cross-service transactions, so you handle eventual consistency (sagas, outbox pattern) and it's much harder to debug.
- *"How do microservices communicate?"* — Sync via REST/gRPC for queries; async via a message bus (Service Bus) for events — async keeps them decoupled and resilient.
- *"When would you NOT use microservices?"* — Small team, early product, or unclear domain boundaries — a modular monolith ships faster with far less operational cost.

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| W1 | What it is | Cross-platform C# framework for fast HTTP/JSON APIs |
| W2 | Controllers & routing | Classes group actions mapped to verbs + routes |
| W3 | Middleware pipeline | Ordered checkpoints each request passes through |
| W4 | Dependency injection | Built-in; Transient/Scoped/Singleton lifetimes |
| W5 | async/await | Frees threads during I/O → scales to more requests |
| W6 | Model binding & validation | Auto-maps request data; `[ApiController]` auto-400s bad input |
| W7 | EF Core | ORM with LINQ; watch the N+1; drop to SQL for hot paths |
| W8 | Auth & status codes | Entra ID + JWT; return the correct HTTP codes |
| W9 | REST principles | Resource nouns, correct verbs, stateless design |
| W10 | Versioning | Version only on breaking changes; URL versioning by default |
| W11 | DTOs & mapping | Never expose entities; DTOs stop over-posting & drift |
| W12 | Error handling | One middleware + ProblemDetails; never leak stack traces |
| W13 | Status codes | Pick precisely: 201/204/409/422/429 etc. |
| W14 | Idempotency | GET/PUT/DELETE idempotent; POST needs idempotency keys |
| W15 | Clean architecture | Layers with inward dependencies; thin controllers |
| W16 | Repository & UoW | DbContext is already UoW; add repos only when they earn it |
| W17 | CQRS & MediatR | Separate reads/writes; MediatR keeps controllers tiny |
| W18 | Minimal APIs | Lambdas for small services; controllers for large apps |
| W19 | Config & options | Layered config; Options pattern; secrets in Key Vault |
| W20 | Background work | BackgroundService / Functions + durable queue |
| W21 | Caching | In-memory vs Redis; always expire and invalidate |
| W22 | Performance | Async, fix N+1, project columns, cache, paginate, measure first |
| W23 | Resilience | Polly retries + circuit breaker + timeouts on idempotent calls |
| W24 | Rate limiting | Built-in limiter; return 429 + Retry-After |
| W25 | Logging | Structured logs + App Insights + correlation IDs |
| W26 | Health checks | Liveness vs readiness probes for the platform |
| W27 | Testing | Unit + WebApplicationFactory integration + E2E |
| W28 | Security hardening | HTTPS/HSTS, allow-list input, tight CORS, Key Vault, least privilege |
| W29 | Deployment | Containers on Azure + CI/CD + zero-downtime slot swaps |
| W30 | Micro vs mono | Modular monolith first; microservices only when warranted |

---

[← React vs Angular](30-concept-react-vs-angular.md) · [Home](README.md) · [Next → Concept: FastAPI](32-concept-fastapi.md)
