# 02 · Technical Q&A (22 questions)

[← Overview](01-overview-positioning.md) · [Home](README.md) · [Next → System Design](03-system-design.md)

Every answer below is written the way I would actually say it: short sentences, a real project, a decision, a trade-off, and a number.

**Jump to:**
[Architecture & .NET](#part-a--architecture--net-q1q5) ·
[Azure Platform](#part-b--azure-platform-q6q10) ·
[Data & Integration](#part-c--data--integration-q11q15) ·
[Security](#part-d--security-q16q17) ·
[DevOps & Observability](#part-e--devops--observability-q18q20) ·
[AI & LLM](#part-f--ai--llm-q21q22)

---

## Part A — Architecture & .NET (Q1–Q5)

### Q1. How do you decide between a monolith, a modular monolith, and microservices?

**My answer.**

I decide by looking at three things: who deploys it, how the data is shared, and how the team is shaped. Technology comes last.

At TengizChevroil I had to build four business capabilities — commissioning certificates, contract transfer, exception handling, and change notice. On paper that looks like four microservices, and that is roughly what I landed on. But the reason was not fashion. Each of those four had a **different owner, a different approval chain, and a different release rhythm**. Commissioning certificates changed whenever the commissioning standard changed. Change notice was tied to the contracts team. If I had put them in one deployable, every change-notice tweak would have forced a regression test of the certificate workflow, and in a live construction programme that means blocked crews.

So I split by business capability, not by technical layer. Each application got its own ASP.NET Core service on Azure App Services, its own release pipeline, and its own schema boundary in Azure SQL. Where they needed to talk, I defined **explicit REST contracts** rather than letting them read each other's tables. Background and event-shaped work — document generation, notifications, the ETL steps — went to Azure Functions, because those are spiky and I did not want to pay for an always-on plan.

The trade-off I accepted, and I say it plainly: I gave up the easy cross-service transaction. A certificate transfer that touches two services cannot be one database transaction. I handled that with an outbox-style pattern — write the state change and the outgoing message in the same local transaction, then let a Function pick it up and deliver it, with retries and a dead-letter path. That is more moving parts than a monolith, and I only accepted it because the deployment independence was worth it.

Where I would *not* do this: for the TCW reporting API layer, I kept a **modular monolith**. One deployable, clean module boundaries inside it, one release train. There, the whole thing serves a single reporting deadline and a single team owns it. Splitting it would have bought me nothing and cost me latency across service hops inside a tight pre-market window.

**Result.** The four-app split at Tengiz let us automate the workflow end to end and cut manual effort by 60% and processing errors by 25%, while each team released on its own schedule. Release cycle time halved once each app had its own pipeline.

**Lesson.** My rule now: *"Split when the pain of releasing together is bigger than the pain of talking over the network."* If a team cannot yet run its own pipeline and its own on-call, microservices will make them slower, not faster.

**Follow-ups**

- *"How small should a service be?"* — Big enough to own its data and be understood by one team, small enough that one person can explain it in five minutes. If two services always change together, they are one service.
- *"How did you stop them sharing a database?"* — Schema-per-service inside Azure SQL, with no cross-schema reads granted. The permission model enforced the rule, not a code review.
- *"What about distributed transactions?"* — I avoid them. Outbox plus idempotent consumers plus a reconciliation job. Eventual consistency with a visible reconciliation report is easier to defend to an auditor than a two-phase commit nobody understands.
- *"Would you use a service mesh?"* — Not at four services on App Services. The mesh solves problems I did not have. I got retries, timeouts and circuit breaking in the client library instead.

---

### Q2. Walk me through how you design a REST API contract that many teams will consume.

**My answer.**

At TCW, every reporting module used to have its own bespoke server-side code. Each new report meant new controllers, new query shapes, new response formats. It was slow to build and impossible to reason about. My job was to define one server-side controller and Web API pattern that every reporting module reuses.

I started with the **contract, not the code**. I wrote the OpenAPI definition first and reviewed it with the front-end lead and the BAs before a single controller existed. That conversation is where the design gets fixed cheaply. Three rules came out of it.

First, **resources, not verbs**. A report is a resource. Its runs are a sub-resource. So `GET /api/v1/reports/{reportId}` and `GET /api/v1/reports/{reportId}/runs/{runId}/rows`. No `getEquityReportData` endpoints.

Second, **one envelope for everything**. Every response has the same shape, so the React client has one code path for success, error and paging. Errors follow RFC 9457 problem details, plus a correlation id that matches what is in Application Insights.

Third, **paging, filtering and sorting are part of the contract**, not something each report invents. Server-side paging with a stable sort key, because portfolio data grows and a report that returns 200,000 rows will kill the browser and the API at the same time.

```csharp
// The shared response envelope every reporting module returns.
public sealed record ApiResponse<T>(
    T? Data,
    PageInfo? Page = null,
    ProblemDetails? Error = null,
    string TraceId = "");

public sealed record PageInfo(int Page, int Size, long TotalRows, string? NextCursor);

// The shared controller base — this is the pattern the modules inherit.
[ApiController]
[Route("api/v{version:apiVersion}/reports")]
[Authorize(Policy = "ReportReader")]
public abstract class ReportControllerBase<TRow> : ControllerBase
{
    protected IActionResult Ok<T>(T data, PageInfo? page = null) =>
        base.Ok(new ApiResponse<T>(data, page, null, HttpContext.TraceIdentifier));

    protected IActionResult Problem(string title, int status, string detail) =>
        StatusCode(status, new ApiResponse<TRow>(
            default, null,
            new ProblemDetails { Title = title, Status = status, Detail = detail },
            HttpContext.TraceIdentifier));
}
```

The other decision I made was **contract testing**. The OpenAPI spec is published from the build, and the React client generates its types from it. If I break a field name, the front-end build fails in CI — not a user in Los Angeles at 6 a.m.

**Result.** New reporting modules now start from the shared pattern instead of bespoke code, which shortened the build cycle for each new report and made the whole layer reviewable. One envelope, one auth policy shape, one paging behaviour.

**Lesson.** *"A contract you agree in a meeting is a rumour. A contract in OpenAPI, enforced by CI, is an architecture."*

**Follow-ups**

- *"How do you document it?"* — OpenAPI generated from the code, published to the developer portal on every main build. The spec is the documentation; hand-written docs go stale in a week.
- *"REST or GraphQL here?"* — REST. The consumers are known, the shapes are report-specific and cacheable, and I did not want to hand a reporting UI the ability to write arbitrary queries against a database with a pre-market deadline.
- *"What about very large report exports?"* — Those are asynchronous. `POST /reports/{id}/exports` returns 202 with a status URL, the work runs in a Function, and the result lands in Blob Storage behind a short-lived SAS link.

---

### Q3. How do you handle API versioning and breaking changes?

**My answer.**

My starting position is that the cheapest breaking change is the one I do not make. So the first thing I do is make the contract additive-friendly: clients must ignore unknown fields, and I never reuse a field name for a new meaning.

On the TCW reporting APIs I use **URL-path versioning** — `/api/v1/...` — because it is obvious in logs, in the gateway, and to a support engineer at 3 a.m. Header versioning is more elegant and much harder to debug. I chose debuggability.

I only cut a new major version for a genuinely breaking change: a field removed, a type changed, or an auth model change. Everything else is additive and stays on the current version. When I do version, I run **both versions in parallel** for an agreed window — typically one full quarter for internal consumers, longer if an external client is on it. I never surprise a consumer.

The part people forget is knowing **who is still on the old version**. I log the version and the caller's client id on every request, so before deprecating I can pull an Application Insights query and see exactly which teams still call v1 and how often. Deprecation then becomes a conversation with three named teams, not a broadcast email and a hope.

```csharp
// Program.cs — versioning that shows up in the URL and in telemetry.
builder.Services.AddApiVersioning(o =>
{
    o.DefaultApiVersion = new ApiVersion(1, 0);
    o.AssumeDefaultVersionWhenUnspecified = true;
    o.ReportApiVersions = true;   // sends api-supported-versions / api-deprecated-versions headers
}).AddApiExplorer(o => o.GroupNameFormat = "'v'VVV");

// Mark the sunset date on the contract itself, so clients see it in the response headers.
[ApiVersion("1.0", Deprecated = true)]
[ApiVersion("2.0")]
public class PositionsController : ReportControllerBase<PositionRow> { }
```

**Result.** We have retired versions without a single consumer outage, because deprecation was driven by telemetry and an agreed window, not by an announcement.

**Lesson.** *"Versioning is a communication problem with a technical solution attached. The telemetry that tells you who is still calling you is worth more than the versioning scheme itself."*

**Follow-ups**

- *"What if a client refuses to migrate?"* — I find out why. Usually it is capacity, not resistance. I offer a shim: keep v1 alive as a thin translation layer over v2 so I only maintain one real implementation.
- *"Is adding a field a breaking change?"* — Not if consumers ignore unknown fields, which I make a written rule in the contract. Adding a *required request* field is breaking.
- *"How do you version the database underneath?"* — Expand-and-contract. Add the new column, dual-write, backfill, migrate readers, then drop the old column in a later release. Never a big-bang column rename.

---

### Q4. Describe how you structure an ASP.NET Core solution and why.

**My answer.**

I use a layered structure with one hard rule: **dependencies only point inwards, towards the domain**. On the TCW reporting platform the solution looks like this.

- **API project** — controllers, filters, dependency injection wiring, authentication. It knows about HTTP and nothing else.
- **Application project** — the use cases. "Get the equity exposure report for this portfolio on this date." It orchestrates. It has no `SqlConnection` and no `HttpClient` type in it.
- **Core / Domain project** — entities, value types, interfaces, and the pure calculation code. No EF Core, no Azure SDK. This is the part I can unit test without a database.
- **Infrastructure project** — EF Core `DbContext`, repositories, the typed HTTP clients for Aladdin, Snowflake access, Blob Storage.

The reason is not tidiness. It is that the domain rules in an investment-reporting system outlive the technology around them. I have already swapped a data-access approach and a hosting model on live systems. If the calculation of an exposure figure sat inside a repository class, that swap would have been a rewrite.

The rule I enforce hardest is that **Infrastructure types never leak upwards**. When my Application layer needs to react to a database write conflict, it catches a domain-level exception that Infrastructure translated, not a `DbUpdateException`. Otherwise every layer quietly becomes an EF Core project.

I keep this honest with an automated test, not a code review:

```csharp
// A guard test — the build fails if someone references Infrastructure from Core.
[Fact]
public void Core_project_must_not_reference_infrastructure_or_ef()
{
    var core = typeof(PortfolioPosition).Assembly;
    var banned = new[] { "Microsoft.EntityFrameworkCore", "Azure.", "XDhan.Infrastructure" };

    var violations = core.GetReferencedAssemblies()
        .Where(a => banned.Any(b => a.Name!.StartsWith(b, StringComparison.Ordinal)))
        .Select(a => a.Name!)
        .ToList();

    Assert.Empty(violations);
}
```

**Result.** The pure reporting and calculation code is unit tested without a database, so the test suite runs in seconds and engineers actually run it. And when we added Snowflake alongside SQL Server, the change was confined to Infrastructure.

**Lesson.** *"An architecture rule that only lives in a document is a suggestion. Put it in a test and it becomes a rule."*

**Follow-ups**

- *"Is this not over-engineering for a small app?"* — For a small app, yes. I use a two-project split there. I scale the structure to the lifetime of the system, and investment reporting has a long lifetime.
- *"Where do DTOs live?"* — Request/response DTOs in the API project, application-level models in Application. I map by hand with small static mapping classes rather than a mapping library, because hand-written maps are debuggable and show up in stack traces.
- *"How do you handle cross-cutting concerns?"* — Middleware for exception translation, correlation ids and request logging. Not scattered try/catch.

---

### Q5. A third-party API you depend on is slow and sometimes fails. How do you design around it?

**My answer.**

This is the daily reality of the Aladdin integration at TCW. Aladdin is the source of truth for portfolio, position and transaction data. I do not control its uptime, its latency or its rate limits, and my reporting deadline does not move because Aladdin had a bad morning.

I designed four layers of defence.

**One — never call it live from a user request.** The ETL pulls Aladdin on a schedule into SQL Server and Snowflake. The reporting API reads our own store. That single decision removes the third party from the user-facing latency path completely. If Aladdin is down at 9 a.m., yesterday's reports still open instantly.

**Two — retries with backoff and jitter, and a circuit breaker.** I use Polly on the typed HTTP client. Retries only on transient statuses and timeouts, never on a 400 — retrying a bad request just burns rate limit. The circuit breaker matters more than the retry: when Aladdin is genuinely down, hammering it delays its recovery and burns our quota.

**Three — respect the rate limit on purpose.** I made the concurrency explicit and bounded rather than letting the pipeline fan out as wide as it could. Bounded parallelism with a bulkhead means one slow endpoint cannot starve the others.

**Four — checkpoint and resume.** Every ingestion run records where it got to. If it dies at 60%, the next run starts from the checkpoint, not from zero. That plus idempotent writes means a retry is always safe.

```csharp
// Program.cs — resilience policy on the Aladdin typed client.
builder.Services.AddHttpClient<IAladdinClient, AladdinClient>(c =>
{
    c.BaseAddress = new Uri(cfg["Aladdin:BaseUrl"]!);
    c.Timeout = TimeSpan.FromSeconds(30);           // hard ceiling, always set one
})
.AddStandardResilienceHandler(o =>
{
    o.Retry.MaxRetryAttempts = 4;
    o.Retry.BackoffType = DelayBackoffType.Exponential;
    o.Retry.UseJitter = true;                        // stops synchronised retry storms

    o.CircuitBreaker.FailureRatio = 0.5;             // open at 50% failures
    o.CircuitBreaker.MinimumThroughput = 20;
    o.CircuitBreaker.BreakDuration = TimeSpan.FromSeconds(30);

    o.AttemptTimeout.Timeout = TimeSpan.FromSeconds(10);
});
```

And the important operational rule: **when the circuit opens, a human is told immediately** through the automated failure alerting, because a missed pre-market window is a business event, not just a log line. The alert says which feed, which checkpoint, and how much time is left in the window.

**Result.** Late or failing source data becomes a managed, visible delay with a clear owner, instead of a silent gap in a report that someone spots after the market opens.

**Lesson.** *"You cannot make someone else's API reliable. You can make your dependence on it optional inside your deadline."*

**Follow-ups**

- *"What if the data is genuinely late and you will miss the window?"* — The orchestration knows the deadline. At a defined cut-off it publishes the report with the previous good snapshot, clearly marked as stale, and raises an alert. A late report that is silently wrong is far worse than an on-time report that says "as of yesterday's close".
- *"How do you test this?"* — I have a fake Aladdin that can be told to be slow, to 429, and to return partial data. The resilience path gets tested every build, not only during a real outage.
- *"Why not a queue in front?"* — There is one for the downstream fan-out. But the ingest itself is a scheduled pull with a checkpoint, which is simpler and gives me exact restart semantics.

---

## Part B — Azure Platform (Q6–Q10)

### Q6. App Service, Azure Functions, or Container Apps — how do you choose?

**My answer.**

I choose by workload shape and by who has to operate it, and I have used all three on the same programme.

At TengizChevroil, the four completion applications went on **Azure App Services**. They are long-lived request/response web apps with predictable working-hours traffic and a team that knew IIS-style hosting. App Service gave us deployment slots, easy scale rules, and managed certificates without anybody learning container orchestration. The operating model mattered: the support team on site had to be able to look after this.

The **ETL and event work went to Azure Functions** — document generation, notification dispatch, the validation steps in the ingestion path. Those are spiky. They run hard for a few minutes and then nothing. Paying for an always-on plan for that is waste, and Functions gave me a natural per-message unit of work with built-in retry.

I would reach for **Container Apps** when I need containers but not a full Kubernetes operating model — for example a Python service like the FastAPI ETL where I want to control the runtime image, need scale-to-zero, and want revision-based rollout without running AKS.

The trade-off I state honestly: I have deliberately **not** put my clients on AKS. Not because I cannot design for it, but because AKS brings a real operating cost — cluster upgrades, node pools, networking, an on-call rota that understands it. For a client whose platform team is four people, that overhead buys nothing over App Service and Container Apps. If I joined a firm that already runs AKS well, I would use it, because the marginal cost is then zero.

**Result.** At Tengiz that split kept the hosting bill proportional to actual use, and let the on-site team operate the platform themselves after handover.

**Lesson.** *"Pick the least platform you can operate on your worst day. Sophistication you cannot support at 2 a.m. is a liability."*

**Follow-ups**

- *"Functions cold start — was that a problem?"* — Not for background work. For anything user-facing on Functions I use a Premium plan with pre-warmed instances, or I keep it on App Service.
- *"How do you decide plan sizes?"* — From measured p95 CPU and memory over two weeks, then scale rules on the metric that actually moves — usually queue length for the Function work, not CPU.
- *"Durable Functions?"* — Yes, for the multi-step document workflows where I need fan-out/fan-in and a durable state machine without standing up an orchestrator.

---

### Q7. How do you design for reliability and disaster recovery on Azure?

**My answer.**

I start by refusing to answer the question until the business gives me two numbers: **RTO** (how long can we be down) and **RPO** (how much data can we lose). Without those, "highly available" is a wish, and every architect fills the gap with an expensive guess.

On the TCW reporting platform the answer was interesting, because the two halves have different numbers. The **reporting read path** has a tight RTO — if portfolio managers cannot open reports before the market opens, that is a business impact the same morning. The **ingestion pipeline** has a looser RTO but a very tight RPO, because losing a day of position data is a reconciliation problem that takes days to unpick.

So I designed them differently.

For the read path: stateless API on App Service, zone-redundant, behind Front Door, with the data replicated so a region failure means a documented failover rather than a rebuild. Because the API is stateless and reads a replicated store, failover is a routing decision, not a data-recovery exercise.

For the ingestion path: everything is **checkpointed and idempotent**. Each run knows exactly where it got to and can be re-run without double-counting. That is what actually protects the RPO — not the backup schedule, but the fact that I can re-ingest a window from Aladdin and land on the same result. I keep point-in-time restore on Azure SQL and geo-redundant backup, but my first recovery tool is a replay, because it is faster and it is tested weekly by ordinary operations.

The part I insist on: **DR that is never tested does not exist**. I run a documented failover exercise, and I time it. The first time we did it at Tengiz, the documented RTO was two hours and the real number was closer to five, because nobody had written down the DNS and connection-string steps. We fixed the runbook, not the architecture.

**Result.** A tested, timed failover procedure with named owners, and an ingestion path where recovery means "replay the window" rather than "restore the database".

**Lesson.** *"Design to the RPO/RTO the business will pay for, then prove it with a real drill. An untested DR plan is a document, not a capability."*

**Follow-ups**

- *"Active-active or active-passive?"* — Active-passive for these workloads. Active-active on a financial data store means solving write conflicts, and the business did not need the extra nines enough to pay that complexity cost.
- *"How do you handle backups of Snowflake?"* — Time Travel for short windows plus the fact that Snowflake is a derived store — I can rebuild it from the source-of-truth pipeline. That is the real safety net.
- *"What is your single biggest availability risk?"* — The third-party dependency, not Azure. Which is why the read path never touches it live.

---

### Q8. How do you control cloud cost as an architect?

**My answer.**

I treat cost as a non-functional requirement with an owner, exactly like latency. If nobody owns the number, it grows.

Three things I actually do.

**One — right-shape the compute to the workload.** This is where most of the money is. At Tengiz, moving the spiky ETL and document work off always-on App Service plans and onto Azure Functions meant we paid for execution, not for idle capacity. The web apps kept a reserved, right-sized plan because their load is predictable — and predictable load is exactly what reservations are for. Same programme, two opposite decisions, both driven by the load curve.

**Two — put the data in the right store.** At TCW, SQL Server carries the operational and transactional reads; Snowflake carries the analytical and historical work. That split is a cost decision as much as a performance one. Running heavy historical analytics on the transactional database means sizing that database for the worst query anyone ever writes. Separating them lets each be sized for its own job, and Snowflake compute suspends when nobody is querying.

**Three — make cost visible per workload.** Tags on everything, a budget with alerts, and a monthly review where the cost is attributed to a feature, not to a resource group. The moment a team sees "your report export costs this much per month", the conversation becomes an engineering conversation.

The specific thing I watch for in data platforms is **the query nobody noticed**. A scheduled dashboard refresh doing a full scan every fifteen minutes will quietly cost more than the whole application tier. I found exactly that pattern and fixed it by materialising the aggregate once per pipeline run instead of computing it per refresh.

**Result.** Cost that tracks usage rather than peak provisioning, and a review rhythm where cost is a normal engineering topic instead of a finance surprise.

**Lesson.** *"Most cloud waste is not a bad rate. It is idle capacity and repeated work. Fix the load shape and the repetition, then negotiate the rate."*

**Follow-ups**

- *"Reserved instances or pay-as-you-go?"* — Reserve the baseline you are certain of, burst on demand. I do not reserve anything until I have three months of real telemetry.
- *"How do you push back when someone wants a bigger SKU?"* — I ask for the metric. If p95 CPU is 30%, the answer is not a bigger SKU; it is a slow query or a bad scale rule.
- *"Cost of the AI workload?"* — Token cost per answer, tracked per feature, with caching of embeddings and a smaller model for classification steps. See [Q22](#q22-how-do-you-evaluate-and-control-a-rag-system-in-production).

---

### Q9. How do you handle identity, secrets and access in an Azure solution?

**My answer.**

My rule is simple: **no secret in a config file, no password in a connection string, ever**. Everything is identity-based where Azure supports it.

For service-to-service access I use **managed identity**. The App Service or Function has an identity, that identity is granted a role on the SQL database, the storage account, or Key Vault, and there is no credential to rotate, leak or commit. This is the single biggest security improvement available on Azure and it costs nothing.

For anything that genuinely has to be a secret — a third-party API credential like the Aladdin one, an SMTP password — it lives in **Key Vault**, read at runtime through the managed identity, with rotation. The app never sees the value in configuration.

For users, **Microsoft Entra ID** with OpenID Connect. The app never handles a password. Tokens are validated against Entra, and authorisation is done with policies against claims — not with role strings scattered through controllers.

```csharp
// No connection-string password anywhere — the App Service identity is the credential.
builder.Services.AddDbContextPool<AppDbContext>(o =>
    o.UseSqlServer(cfg["Sql:ConnectionString"]));   // "Server=...;Authentication=Active Directory Default;"

// Key Vault for the few real secrets, read via managed identity.
builder.Configuration.AddAzureKeyVault(
    new Uri($"https://{cfg["KeyVault:Name"]}.vault.azure.net/"),
    new DefaultAzureCredential());

// Authorisation as policy, not as scattered string checks.
builder.Services.AddAuthorization(o =>
{
    o.AddPolicy("ReportReader", p => p.RequireAuthenticatedUser()
                                      .RequireClaim("scp", "reports.read"));
    o.AddPolicy("ReportPublisher", p => p.RequireRole("Reporting.Publisher"));
});
```

The other half is **least privilege that is actually reviewed**. Granting `db_datareader` to an application identity is fine; granting `db_owner` because a migration once needed it is how estates rot. I separate the migration identity from the runtime identity, so the running app cannot alter schema even if it is compromised.

**Result.** At TCW and Tengiz, applications run with no stored credentials for Azure resources, and access reviews are a list of role assignments rather than an archaeology exercise across config files.

**Lesson.** *"Every secret you remove is a secret you never have to rotate, audit, or explain in an incident review."*

**Follow-ups**

- *"What about local development?"* — `DefaultAzureCredential` falls back to the developer's own Entra login through Visual Studio or the Azure CLI. Same code, no shared dev secret.
- *"How do you handle a compromised token?"* — Short token lifetimes, revocation at the identity provider, and continuous access evaluation. Plus the audit trail to see what that identity touched.
- *"Who approves role assignments?"* — Privileged Identity Management with just-in-time elevation and an approver. Standing admin access is the thing I remove first on any engagement.

---

### Q10. How do you manage infrastructure and environment promotion?

**My answer.**

Infrastructure is code, in the same repository as the application, reviewed in the same pull request. If the app needs a new queue, the queue appears in the same PR as the code that reads it. That single rule kills most environment drift.

On Azure I use **Bicep**, because it is native, it does not need extra state management, and the team can read it without learning a new language. I have used Terraform where a client was multi-cloud, and I would again — but for an all-Azure estate, Bicep is less machinery for the same result.

The promotion model is **one template, parameters per environment**. Dev, test, UAT and production come from the same file. The environments differ only in parameters — SKU, capacity, retention, and the names. The moment you have a separate template for production, production is untested until the day you need it.

```bicep
// main.bicep — one template, environment differences are parameters only.
param env string                    // 'dev' | 'test' | 'prod'
param location string = resourceGroup().location

var sku = env == 'prod' ? { name: 'P1v3', capacity: 3 } : { name: 'B1', capacity: 1 }

resource plan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: 'asp-reporting-${env}'
  location: location
  sku: sku
}

resource api 'Microsoft.Web/sites@2023-12-01' = {
  name: 'app-reporting-api-${env}'
  location: location
  identity: { type: 'SystemAssigned' }         // managed identity, always
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    siteConfig: {
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}
```

Promotion runs through **Azure DevOps** as a single pipeline with stages and approval gates. The same artifact that passed test is the artifact that goes to production — built once, deployed many times. Production has a manual approval and a deployment window; nothing else differs.

**Result.** At Tengiz this was a large part of halving release cycle time. Environments stopped being snowflakes, so "it works in test" started meaning something.

**Lesson.** *"Environment drift is not a discipline problem, it is a design problem. If the only path to change infrastructure is a reviewed template, drift cannot happen."*

**Follow-ups**

- *"What-if / plan step?"* — Yes, `az deployment group what-if` runs in the PR and posts the diff. Reviewers see what will actually change before approving.
- *"How do you handle database schema in this?"* — Separate migration step with its own identity, run before the app deploy, using expand-and-contract so the old app version still works during the rollout.
- *"Bicep or Terraform if you joined us tomorrow?"* — Whatever you already run well. Consistency in an estate beats my personal preference.

---

## Part C — Data & Integration (Q11–Q15)

### Q11. Why do you run both SQL Server and Snowflake? Is that not duplication?

**My answer.**

It is duplication, and it is deliberate. They answer different questions.

At TCW, **SQL Server and Azure SQL carry the operational tier**: the tables the reporting API reads for a specific portfolio on a specific date, the reference data, the workflow state. Those queries are narrow, indexed, and need to return in milliseconds while a user waits. Relational, transactional, tightly indexed — that is exactly what SQL Server is best at.

**Snowflake carries the analytical tier**: history, cross-portfolio aggregation, time-series comparison, the heavy queries that scan large ranges. Those are wide scans over a lot of data, run by fewer people, and tolerant of seconds rather than milliseconds.

If I forced both onto one engine, one of them suffers. Put the analytics on SQL Server and I have to size that server for the worst analytical query anyone writes, and a single bad scan can slow down the API that has a pre-market deadline. Put the operational reads on Snowflake and I pay warehouse latency on every user click.

So the pipeline lands data in both, from the same ingestion run, with the same validation. The important discipline is that **SQL Server is the operational source and Snowflake is derived**. There is one lineage. I do not let the two drift into two truths — reconciliation checks compare row counts and key aggregates across both after each load, and a mismatch raises an alert before anyone reads a report.

**Result.** The user-facing reporting path stays fast and predictable inside its deadline, while analysts run heavy historical work without ever touching the system that has the deadline.

**Lesson.** *"Separating operational and analytical workloads is not duplication, it is isolation. The duplication is the price you pay for one workload never being able to hurt the other."*

**Follow-ups**

- *"Why not a read replica of SQL Server instead?"* — A replica gives me isolation but not the analytical engine. Large historical scans are cheaper and faster on a columnar warehouse, and Snowflake compute suspends when idle.
- *"How do you keep them consistent?"* — Same run, same validation, then automated reconciliation on counts and control totals. Consistency is checked, not assumed.
- *"What about a lakehouse / Fabric?"* — A reasonable direction, and I would evaluate Microsoft Fabric for a greenfield build. Here, Snowflake was already the firm's analytical standard, and re-platforming an analytical estate needs a business case, not an architect's preference.

---

### Q12. Tell me about a serious database performance problem you solved.

**My answer.**

Report generation was slowing down as data volumes grew — the classic pattern where something is fine at go-live and painful eighteen months later. On an investment-reporting platform with a pre-market window, a report that takes four minutes instead of forty seconds is not an annoyance, it is a missed deadline.

I did not start by adding indexes. I started by finding out **where the time actually went**, because guessing at performance is how you end up with fifteen indexes and slower writes. I pulled the top consumers from Query Store, took the actual execution plan for the worst one, and looked for the usual suspects: a scan where I expected a seek, a huge row-estimate mismatch, or an implicit conversion.

The root cause on the worst query was a **non-SARGable predicate**. The query filtered on a date by wrapping the column in a function, so SQL Server could not use the index at all and scanned the whole table. The second cause was a **key lookup** — the index found the rows, then went back to the clustered index for four more columns, millions of times.

Two fixes.

```sql
-- BEFORE: the function on the column kills the index. Full scan.
SELECT PortfolioId, SecurityId, Quantity, MarketValue
FROM   dbo.Positions
WHERE  CONVERT(date, AsOfDateTime) = @AsOf
  AND  PortfolioId = @PortfolioId;

-- AFTER: a range predicate the optimiser can seek on.
SELECT PortfolioId, SecurityId, Quantity, MarketValue
FROM   dbo.Positions
WHERE  AsOfDateTime >= @AsOf
  AND  AsOfDateTime <  DATEADD(day, 1, @AsOf)
  AND  PortfolioId  = @PortfolioId;

-- AND: a covering index so there is no lookup back to the clustered index.
CREATE NONCLUSTERED INDEX IX_Positions_Portfolio_AsOf
ON dbo.Positions (PortfolioId, AsOfDateTime)
INCLUDE (SecurityId, Quantity, MarketValue);
```

I also changed how the heavy aggregate was produced. It was being recomputed on every report open. Since the underlying data only changes once per ingestion cycle, I **materialise the aggregate once per pipeline run** and the report reads the result. Doing the work once per day instead of once per click is a bigger win than any index.

The last piece was governance, not code. I set the data-modelling and query-tuning standards for the team — no functions on filtered columns, every new query reviewed against its plan, and index changes justified with before/after numbers. That is what stops the problem coming back after I move on.

**Result.** The slow reports came back inside the window, and the pattern was caught in review rather than in production for the next set of reports.

**Lesson.** *"Measure, then fix the biggest thing. And ask whether the work needs to happen at all — the fastest query is the one you computed once and cached."*

**Follow-ups**

- *"How do you find the slow queries?"* — Query Store for the ranked list, `sys.dm_db_missing_index_details` as a hint only, and Application Insights dependency telemetry to see it from the user's side.
- *"Do you trust the missing-index DMV?"* — As a hint, never as an instruction. It suggests wide indexes and ignores the write cost. I always check the plan myself.
- *"What about parameter sniffing?"* — I have hit it. Options are `OPTIMIZE FOR UNKNOWN`, recompile on the specific statement, or splitting the procedure. I pick based on how skewed the data actually is.
- *"Would you just scale the database up?"* — Only as an emergency lever while the real fix ships. Scaling up to hide a table scan means paying monthly for a bug.

---

### Q13. How do you design an ETL pipeline that is safe to re-run?

**My answer.**

Every pipeline I build has to satisfy one rule: **running it twice produces the same result as running it once**. If that is not true, then every retry, every recovery, and every "did that finish?" becomes a manual investigation.

On the Aladdin ingestion at TCW, I built the FastAPI ETL services around four ideas.

**Watermarks.** Each feed tracks the last successfully processed point. The next run asks for data after that watermark. The watermark only advances after the data is committed, so a crash mid-run means the next run redoes that slice — safely, because of the next point.

**Merge, not insert.** Landing data uses a `MERGE` on the natural key, so re-processing the same slice updates rather than duplicates. Duplicated positions in an investment report are not a cosmetic bug; they are a wrong number in front of a portfolio manager.

**Validation before promotion.** Data lands in a staging area first. Validation runs there — row counts against the source, control totals, required fields, referential checks. Only validated data is promoted to the tables the reports read. This is exactly the pattern that cut processing errors by 25% at Tengiz: the errors were always there, we just used to find them downstream.

**Reconciliation after promotion.** After the load, an automated check compares our totals to the source's totals. A break raises an alert with the specific feed and key, not a generic failure.

```python
# FastAPI ETL — the shape of one safe, restartable slice.
async def ingest_positions(as_of: date, run_id: str) -> IngestResult:
    watermark = await state.get_watermark("aladdin.positions")

    # 1. Pull, with retry + backoff handled in the client.
    raw = await aladdin.fetch_positions(since=watermark, as_of=as_of)

    # 2. Land into staging, tagged with the run so a failed run is easy to discard.
    await staging.write("stg_positions", raw, run_id=run_id)

    # 3. Validate BEFORE anything downstream can see it.
    checks = await validate(
        "stg_positions", run_id,
        rules=[row_count_matches_source, no_null_security_id,
               market_value_within_tolerance, portfolio_exists],
    )
    if checks.failed:
        await alerts.raise_break("aladdin.positions", checks, as_of)
        return IngestResult(status="quarantined", detail=checks.summary)

    # 4. Promote with MERGE — safe to run again.
    await warehouse.merge("dbo.Positions", "stg_positions",
                          keys=["PortfolioId", "SecurityId", "AsOfDate"],
                          run_id=run_id)

    # 5. Only now move the watermark.
    await state.set_watermark("aladdin.positions", raw.max_timestamp)
    return IngestResult(status="ok", rows=raw.count)
```

The other thing I insist on is **structured logging with a run id on every line**. When someone asks "what happened to Tuesday's equity load?", I want one query, not a log-file hunt.

**Result.** Failures became re-runnable rather than investigable. A failed slice is retried automatically; a data break is quarantined and alerted with the exact feed and key, so it is fixed before it reaches a report.

**Lesson.** *"Idempotency is what turns a 3 a.m. phone call into an automatic retry."*

**Follow-ups**

- *"What if the source sends corrected data for an old date?"* — The merge handles it, and I keep an audit of what changed and when, because in financial reporting "the number changed" always needs an explanation.
- *"How do you handle schema changes from the source?"* — Contract validation on ingest. An unexpected schema fails fast into quarantine instead of silently loading nulls.
- *"Where does the quarantined data go?"* — It stays in staging tagged with the run id, and appears on a data-quality dashboard with an owner. Nothing is silently dropped.

---

### Q14. You orchestrate across Azure Data Factory, Tidal and Apache Airflow. Why three tools?

**My answer.**

Because I inherited an estate, not a blank page — and I judged that consolidating for elegance would have cost more than it returned.

Here is the honest split. **Tidal Workload Automation** was already the enterprise scheduler. It runs the firm's cross-system job dependencies, including things well outside my platform. **Azure Data Factory** is where the Azure-native movement and pipeline activities live. **Apache Airflow** is where the Python-centric transformation DAGs sit, close to the FastAPI ETL services, where engineers want code-defined dependencies and easy testing.

An architect's instinct is to say "pick one". I looked at what that would actually cost: rewriting the enterprise scheduling that other teams depend on, retraining an operations team, and taking on migration risk against a daily pre-market deadline. The value was not there.

What I did instead was accept the three tools and **fix the real problem, which was the seam between them**. The failure mode in a multi-scheduler estate is not that there are three tools; it is that nobody can answer "is the chain on track?" without opening three consoles.

So I designed a **dependency-aware orchestration layer** across them. Every step, in whichever tool, publishes the same signals: start, finish, row counts, and a status against the deadline. Downstream steps wait on those signals rather than on a clock. That is the key change — the old pattern was "Airflow runs at 04:15 and hopes ADF finished", which fails silently the day ADF is ten minutes late. Now the dependency is explicit.

On top of that: **structured logging with a shared run id across all three**, so one query shows the whole chain, and **automated failure alerting** that knows the deadline. An alert does not just say "job failed"; it says which feed, which step, and how much slack is left before the pre-market window closes. That is the difference between a log and an operational signal.

**Result.** Daily investment reporting lands inside the pre-market window, with the chain visible end to end and failures raised while there is still time to act.

**Lesson.** *"In a real estate you rarely get to pick one tool. Standardise the contract between tools — signals, run ids, and deadlines — and the tool count stops mattering."*

**Follow-ups**

- *"Would you consolidate eventually?"* — Yes, opportunistically. Every new pipeline goes to the standard choice, and the old ones migrate when they are being changed anyway. Migration as a by-product of normal work, not as a project.
- *"What is the risk of that design?"* — The signal layer becomes a dependency itself. So it is deliberately simple, and every step also fails safe: if the signal is missing, downstream waits and alerts rather than assuming success.
- *"How do you handle a partial failure mid-chain?"* — Each step is idempotent and checkpointed, so we restart from the failed step rather than the top. See [Q13](#q13-how-do-you-design-an-etl-pipeline-that-is-safe-to-re-run).

---

### Q15. How do you guarantee data quality in a financial reporting system?

**My answer.**

In investment reporting, a wrong number is worse than no number. So I design quality as a **gate**, not a report. Bad data must not be able to reach a user, even if that means a report is late.

I use four layers.

**Layer one — contract checks at ingest.** Does the payload match the agreed schema? Are required fields present? Are types right? An unexpected shape from the source fails immediately into quarantine rather than loading nulls that look like zeros.

**Layer two — business rules in staging.** Market value within tolerance, quantities non-negative where they must be, every position referencing a portfolio that exists, no duplicate keys for the same as-of date. This is the layer that catches real-world messiness.

**Layer three — reconciliation against the source.** After load, compare control totals to Aladdin's own figures. Row counts, sums by portfolio, position counts. A break is an alert with the exact portfolio and field, routed to a named owner.

**Layer four — completeness against the calendar.** This one catches the failure everyone misses: the feed that succeeded but arrived with only half the portfolios. So I check not just "did it load" but "did everything that should exist, exist". Missing data is a silent failure, and silent failures are the dangerous ones.

The operational rule underneath all of it: **quarantine, alert, never drop**. Failed rows stay visible with a run id and an owner. Nothing is silently discarded, because in a regulated firm "we dropped some rows" is not an acceptable answer to an auditor.

At Tengiz, adding exactly this validation layer to the ADF and Functions ETL is what reduced processing errors by **25%**. The errors were not new; we simply started catching them at the gate instead of discovering them in a completion report weeks later.

**Result.** Data breaks surface within minutes of a load, with the specific feed, portfolio and field named, and with time still left in the window to fix them.

**Lesson.** *"Make the pipeline fail loudly rather than let it publish quietly. A late report gets a phone call. A wrong report gets an investigation."*

**Follow-ups**

- *"Who fixes a data break?"* — It is routed by feed to a named owner, with the runbook link in the alert. Ownership is defined before go-live, not during the first incident.
- *"How do you avoid alert fatigue?"* — Thresholds tuned from real history, breaks grouped by feed rather than per row, and a weekly review that either fixes a noisy rule or deletes it.
- *"Do you ever publish with known gaps?"* — Yes, when the business decides that is better than nothing — but always visibly marked as partial, with the missing scope stated on the report itself.

---

## Part D — Security (Q16–Q17)

### Q16. How do you design authentication and authorisation for an enterprise application?

**My answer.**

The application never handles a password. That is the starting point. Identity is delegated to **Microsoft Entra ID** using OpenID Connect, so the client redirects to Entra, the user authenticates there — with the firm's MFA and conditional access policies — and my application receives a token it validates.

For the reporting platform at TCW, the flow is: React front end uses authorisation code flow with PKCE against Entra, receives an access token scoped to my API, and calls the ASP.NET Core API with it. The API validates signature, issuer, audience and expiry on every request. Service-to-service calls use client credentials or managed identity, never a shared user account.

Authorisation is where most designs go wrong, so I am specific about it. I separate three things:

**Authentication** — who are you. Entra's job.
**Coarse authorisation** — are you allowed to use this endpoint at all. Handled with policies against scopes and app roles.
**Fine authorisation** — are you allowed to see *this portfolio's* data. This one cannot live in a policy attribute, because it depends on the row. It has to be enforced in the query, close to the data.

That last point is the one I always make, because it is the real-world failure. An endpoint that checks `[Authorize(Roles="Analyst")]` and then returns any portfolio the caller asks for has an authorisation bug, not an authentication bug.

```csharp
[ApiController]
[Route("api/v1/reports")]
[Authorize(Policy = "ReportReader")]                  // coarse: can you call this at all
public sealed class PositionsController : ControllerBase
{
    [HttpGet("{portfolioId:guid}/positions")]
    public async Task<IActionResult> Get(Guid portfolioId, DateOnly asOf, CancellationToken ct)
    {
        // FINE authorisation: entitlement is checked against the caller, per row/portfolio.
        var callerId = User.GetObjectId();
        if (!await _entitlements.CanViewPortfolioAsync(callerId, portfolioId, ct))
            return Forbid();                          // 403, and it is audit-logged

        var rows = await _positions.GetAsync(portfolioId, asOf, ct);
        return Ok(rows);
    }
}
```

And every `Forbid` is logged with the caller, the resource and the time — because denied access attempts are exactly what a security review wants to see.

**Result.** One identity model across the applications, MFA and conditional access enforced centrally by the firm rather than reimplemented per app, and entitlement decisions that are testable and auditable.

**Lesson.** *"Authentication is a solved problem — delegate it. Authorisation is your problem, and the fine-grained half of it belongs next to the data."*

**Follow-ups**

- *"Where do you store entitlements?"* — In the application's own store, because entitlement to a portfolio is business data, not directory data. Entra tells me who you are and your broad role; the app decides what you can see.
- *"How do you test authorisation?"* — Integration tests that call endpoints as different principals and assert 403s. A test that only checks the happy path is worse than no test.
- *"Token lifetime?"* — Short access tokens with refresh, so a revoked user loses access in minutes, not hours.
- *"What about service accounts?"* — Replaced with managed identities wherever Azure supports it. See [Q9](#q9-how-do-you-handle-identity-secrets-and-access-in-an-azure-solution).

---

### Q17. How do you handle security and compliance for regulated financial data?

**My answer.**

I have worked on regulated data for most of my career — asset management in the US, healthcare and public sector in the UK. The mindset I bring is that compliance is not a phase at the end; it is a set of constraints that shape the architecture from day one, exactly like latency.

Four things I design in from the start.

**Data classification and residency.** Before I draw a box, I ask what class of data flows through it and where it is allowed to live. In asset management, position and transaction data is confidential and often has residency expectations. That decides my region choice, my backup region, and whether a service is even eligible.

**Encryption everywhere, with the right key story.** TLS 1.2 minimum in transit, transparent encryption at rest, and for the most sensitive fields, column-level protection. The question auditors actually ask is not "is it encrypted" — everything is encrypted now — it is **"who holds the keys and who can use them"**. So keys in Key Vault, access by managed identity, and key access logged.

**Least privilege that is reviewed.** Separate identities for migration and runtime. No standing admin — just-in-time elevation with an approver. And crucially, an access review that a human actually performs, because permissions accumulate.

**Auditability.** Every meaningful action is traceable: who ran the report, who approved the certificate, what changed in the data and when. In the completion platform at Tengiz this was central — a commissioning certificate is a legal artefact, so the approval chain had to be provable, not just recorded. I designed the change history as append-only, because an audit trail you can edit is not an audit trail.

The judgement call I make often: **security controls must not make the safe path harder than the unsafe path**. If the compliant way to get data is painful, people will export to a spreadsheet, and now the data is somewhere with no controls at all. So I spend design time making the compliant path convenient — pre-built exports with entitlement baked in, rather than a blanket block on exporting.

**Result.** Audit questions get answered from the system rather than from an engineer's memory, and the security model survived client review at firms with serious oversight.

**Lesson.** *"Security that people route around is not security. Design the compliant path to be the easy path."*

**Follow-ups**

- *"How do you handle PII in logs?"* — Nothing identifying goes into logs. I log ids and correlation ids, and the redaction is enforced in the logging middleware so it cannot be forgotten.
- *"Third-party risk?"* — Documented data flow per integration, an agreed contract, and network restriction — private endpoints and firewall rules, so the integration only works from where it should.
- *"How do you prove it during an audit?"* — Architecture decision records, the IaC templates showing the enforced settings, role assignment exports, and the alert history. Evidence, not assertion.
- *"Have you failed a security review?"* — I have had findings. The common one is over-permissive role assignment that grew over time. The fix is the access review rhythm, not a one-off cleanup.

---

## Part E — DevOps & Observability (Q18–Q20)

### Q18. Describe the CI/CD design that halved your release cycle.

**My answer.**

At TengizChevroil, releases were slow and frightening. Manual steps, environments that had drifted apart, and a deployment that needed the one person who knew the sequence. The cost was not just time; it was that people batched changes to avoid the pain, which made every release bigger and riskier — the classic loop.

I established the Azure DevOps pipelines and the release strategy. Four changes did the work.

**One — build once, deploy many.** The artifact built from a commit is the artifact that goes to dev, test, UAT and production. No rebuild per environment. That alone removes a whole class of "it worked in test" problems.

**Two — infrastructure and configuration in the pipeline.** No manual portal changes. The environment is created and updated from templates, so promoting is repeatable. See [Q10](#q10-how-do-you-manage-infrastructure-and-environment-promotion).

**Three — quality gates that actually gate.** Unit tests, a build-breaking lint and analyzer pass, and a smoke test after each deploy. If the smoke test fails, the stage fails; there is no "carry on and check manually".

**Four — deployment slots with a warm-up and a swap.** Deploy to the staging slot, run the smoke test against it, then swap. Rollback is a swap back, which takes seconds. Once rollback became cheap, people stopped batching changes, and release size fell — which is where most of the risk reduction really came from.

```yaml
# azure-pipelines.yml — build once, then promote the same artifact.
stages:
- stage: Build
  jobs:
  - job: BuildAndTest
    steps:
    - task: DotNetCoreCLI@2
      inputs: { command: build, arguments: '-c Release' }
    - task: DotNetCoreCLI@2
      inputs: { command: test, arguments: '-c Release --collect:"XPlat Code Coverage"' }
    - task: PublishPipelineArtifact@1
      inputs: { targetPath: '$(Build.ArtifactStagingDirectory)', artifact: 'app' }

- stage: Test
  dependsOn: Build
  jobs:
  - deployment: DeployTest
    environment: 'reporting-test'
    strategy:
      runOnce:
        deploy:
          steps:
          - template: templates/deploy-and-smoke.yml
            parameters: { env: 'test' }

- stage: Prod
  dependsOn: Test
  jobs:
  - deployment: DeployProd
    environment: 'reporting-prod'      # manual approval gate is configured on the environment
    strategy:
      runOnce:
        deploy:
          steps:
          - template: templates/deploy-and-smoke.yml
            parameters: { env: 'prod', useSlot: true }   # deploy to slot, smoke, then swap
```

**Result.** Release cycle time **halved**. More importantly, releases became boring — smaller, more frequent, and reversible in seconds.

**Lesson.** *"Speed comes from making rollback cheap. When going back is safe, people stop batching, and small releases are what actually reduce risk."*

**Follow-ups**

- *"How do you handle database changes with slot swaps?"* — Expand-and-contract, so the old and new app versions both work against the same schema during the swap window. Never a breaking schema change in the same release as the code that needs it.
- *"Feature flags?"* — Yes, for anything user-visible or risky. Deploy is separate from release. A flag lets me turn a feature off without a deployment, which is the fastest rollback there is.
- *"Who approves production?"* — A named approver on the Azure DevOps environment, with the change record attached. The gate is in the tool, not in someone's inbox.
- *"Blue-green or canary?"* — Slot swap is my blue-green. Canary needs traffic-splitting and enough traffic to be meaningful; on these workloads slot swap plus flags gave the same safety with less machinery.

---

### Q19. What do you actually monitor? How do you know the system is healthy?

**My answer.**

My rule is that I monitor **the business promise first, and the components second**. Most monitoring is upside down: dashboards full of CPU graphs and nothing that says whether the thing the business paid for is happening.

For the TCW reporting platform, the business promise is "the reports are correct and ready before the market opens". So the top-level signals are:

- Did every feed land, and by when relative to the deadline?
- Did validation and reconciliation pass?
- How much slack is left in the pre-market window right now?
- Can users open reports, and how fast?

Underneath that sit the normal technical signals — API p95 latency and error rate, dependency latency to Aladdin and to the database, queue depth, and Function failures.

I use **Application Insights and Azure Monitor**, with structured logging and a **correlation id that follows a request or a pipeline run end to end**. That is the single most useful thing in the whole setup. When someone asks "what happened to Tuesday's equity load", I query one id and see every step across the API, the ETL and the orchestration.

```kusto
// Application Insights — the query I actually run first during an incident.
// One run id, every step, in order, with the failures marked.
let runId = "run-2026-08-04-equity-0412";
union traces, dependencies, exceptions, requests
| where customDimensions.RunId == runId
| project timestamp,
          step     = tostring(customDimensions.Step),
          feed     = tostring(customDimensions.Feed),
          status   = coalesce(tostring(customDimensions.Status), resultCode),
          rows     = toint(customDimensions.RowCount),
          durationMs = duration,
          message
| order by timestamp asc
```

```kusto
// The deadline alert — this is the one that pages someone.
// Fires when a required feed has not completed and slack is under 30 minutes.
let deadline = datetime_add('minute', 0, startofday(now()) + 13h);  // pre-market cut-off, IST-normalised
customEvents
| where name == "FeedCompleted"
| summarize lastCompleted = max(timestamp) by feed = tostring(customDimensions.Feed)
| where lastCompleted < deadline - 30m
```

On alerting I am strict: **an alert must be actionable and must have an owner**. If nobody would do anything at 3 a.m., it is a dashboard item, not an alert. Alert fatigue is the reason real incidents get missed, so I review the alert list monthly and delete the ones nobody acted on.

**Result.** Failures surface while there is still time to act, and incident investigation starts with one query rather than three consoles and a log hunt.

**Lesson.** *"Monitor the promise, not the plumbing. CPU at 90% might be fine. A feed that has not landed with 20 minutes of slack left is never fine."*

**Follow-ups**

- *"SLI and SLO?"* — Yes. The SLI is "reports available before the window with validation passed". The SLO is a target percentage of days, and the error budget drives whether we ship risky changes that week.
- *"Logs, metrics or traces?"* — All three, but distributed tracing with a shared correlation id is the one that saves the most time in a multi-hop pipeline.
- *"How do you avoid logging costs blowing up?"* — Sampling on high-volume success paths, full fidelity on errors, and retention tiered by value. Verbose logging on everything is a cost problem and a signal-to-noise problem.

---

### Q20. Walk me through an incident you led.

**My answer.**

**Situation.** A morning ingestion run failed part-way. The source feed had returned data in a shape we did not expect for a subset of portfolios, and the run stopped. We were inside the pre-market window with limited slack, and portfolio managers were going to look for their reports shortly.

**My role.** I own production governance for these business-critical processes, so I ran the incident: triage, decision, communication, and afterwards the root-cause analysis.

**What I did, in order.**

First, **stabilise before diagnosing**. I checked what had actually been promoted versus what was still in staging. The validation gate had done its job — the bad slice was quarantined, so nothing wrong had reached a report. That immediately changed the incident from "wrong data is live" to "data is late", which is a completely different severity and a different conversation.

Second, **buy time and tell people**. I sent one short message to the business contacts: what was affected, what was not, what I expected, and when the next update would come. Specific and early. In my experience the damage in an incident is usually done by silence, not by the fault.

Third, **fix forward with the safest option**. I had two choices. Patch the transformation to handle the new shape, or re-run the good portfolios and hold the affected ones. Patching under time pressure on financial data is how you turn a late report into a wrong report. So I re-ran the unaffected scope, published those reports on time, and held the affected subset with a clear, visible note about what was missing. Because the pipeline is idempotent and checkpointed, re-running the good slice was safe and quick.

Fourth, **fix the cause properly, afterwards**. The real fault was that we accepted a source-schema change without a contract check strong enough to distinguish "new optional field" from "changed meaning". I strengthened the ingest contract validation and added a specific alert for source-schema drift, so the next time this happens we know at ingest, not mid-transform.

**Result.** No incorrect data was published. Most reports landed on time. The affected scope was clearly communicated rather than silently missing. The post-incident action closed the actual gap instead of adding a retry.

**Lesson.** *"In an incident, correctness first, communication second, cleverness last. And the follow-up matters more than the fix — an incident you do not learn from is an incident you have booked for next quarter."*

**Follow-ups**

- *"How do you decide severity?"* — By business impact, not by component. Wrong data published is the highest. Late data is one below. A failed job with time still in the window is not an incident yet.
- *"Who did you tell, and when?"* — Business contacts and the support lead within minutes, with a stated next-update time. I keep the update rhythm even when there is no news, because silence gets filled with worse assumptions.
- *"Blameless post-mortem?"* — Yes. I write it in terms of what the system allowed, not who did what. You only get honest reports if reporting is safe.
- *"What is your standard for a good action item?"* — It has an owner, a date, and it must make the failure impossible or visible. "Be more careful" is not an action item.

---

## Part F — AI & LLM (Q21–Q22)

### Q21. You defined an AI/LLM reference architecture. Walk me through it.

**My answer.**

The problem I was solving was not technical. At TCW, teams wanted to use LLMs and there was no agreed way to do it. Left alone, we would have ended up with several different approaches, different data-handling decisions, and no way to tell whether any of them were accurate. In a regulated asset manager, that is a compliance issue as much as an engineering one.

So I defined a reference architecture and integration framework for connecting the firm's applications to AI capabilities. It has **four parts, deliberately named** so a conversation about an AI feature has a shared vocabulary: **retrieval, grounding, orchestration and evaluation**.

**Retrieval.** How we find the right context. Content is chunked with attention to structure, embedded, and stored in a vector store with metadata — the source, the permissions, the date. In the first implementation that is a Chroma vector database. Retrieval is hybrid: keyword plus vector, because pure semantic search is bad at exact identifiers, and finance is full of exact identifiers.

**Grounding.** The model answers only from retrieved context, and it cites the source. If retrieval returns nothing relevant, the correct answer is "I do not know" — and I treat a confident answer with no source as a defect, not a quirk. This is the part that makes it usable in a regulated firm: every answer is traceable to a document.

**Orchestration.** The multi-step flow — classify the question, retrieve, possibly retrieve again with a rewritten query, generate, check. I use LangGraph for this, because a real support question is not one call to a model; it is a small state machine with branches and retries.

**Evaluation.** This is the part most teams skip, and it is the reason I put it in the framework. Every change — a new prompt, a new chunking strategy, a model version — is measured against a fixed question set for groundedness, relevance and correctness. LangSmith gives me the tracing and the evaluation runs. Without this, you cannot tell an improvement from a regression, and model behaviour changes underneath you.

The other decisions in the framework: **the model is a swappable component behind an interface**, never called directly from business code; **nothing leaves the boundary the firm agreed**; and **permissions are applied at retrieval**, so a user cannot get an answer built from a document they are not allowed to read. That last one is subtle and it is where naive RAG implementations leak data.

**Result.** The framework is the firm's reference pattern, and I proved it by delivering the first end-to-end implementation on it — TCW's first production RAG application. See [Q22](#q22-how-do-you-evaluate-and-control-a-rag-system-in-production).

**Lesson.** *"With LLMs the model is the commodity. The architecture is retrieval quality, grounding, permissions and the evaluation loop. Get those right and you can swap models freely."*

**Follow-ups**

- *"Why a framework before an application?"* — Because the second and third teams were coming. A pattern written after three implementations is a cleanup project; written before, it is an architecture.
- *"Fine-tuning or RAG?"* — RAG, clearly. The knowledge changes weekly, it must be cited, and access control must apply per user. Fine-tuning bakes knowledge in with no citation and no permissions.
- *"How do you stop it leaking data between users?"* — Permission filtering at retrieval time, not in the prompt. The retriever only ever returns chunks the caller is entitled to.
- *"Which model?"* — Deliberately an implementation detail behind an interface. I select per task — a smaller, cheaper model for classification and routing, a stronger one for the final answer.

---

### Q22. How do you evaluate and control a RAG system in production?

**My answer.**

The RAG support assistant I built at TCW indexes support emails, Confluence runbooks and past response threads, and answers recurring support questions. The engineering risk with something like this is not that it fails loudly. It is that it **degrades quietly** — answers get slightly worse, nobody notices for a month, and trust is gone.

So I control it with three things: a fixed evaluation set, per-answer telemetry, and a cost budget.

**The evaluation set.** A curated set of real questions with known-good answers and known source documents. Every change runs against it and reports three scores: **groundedness** (is every claim supported by retrieved context), **relevance** (did retrieval fetch the right documents at all), and **correctness** (does it match the expected answer). I care most about groundedness, because a fluent unsupported answer is the dangerous failure in a support context — it sounds right and it is wrong.

I separate **retrieval failures from generation failures**, because they need different fixes. If retrieval did not find the runbook, no prompt change will save the answer. That distinction alone saves a lot of wasted tuning.

```python
# Evaluation gate in CI — a change that lowers groundedness does not ship.
BASELINE = {"groundedness": 0.92, "retrieval_recall": 0.88, "correctness": 0.85}
TOLERANCE = 0.02

def evaluate(candidate_chain, gold_set) -> dict:
    scores = {"groundedness": [], "retrieval_recall": [], "correctness": []}
    for case in gold_set:
        result = candidate_chain.invoke({"question": case.question})
        retrieved_ids = {d.metadata["doc_id"] for d in result["source_documents"]}

        scores["retrieval_recall"].append(
            len(retrieved_ids & case.expected_doc_ids) / len(case.expected_doc_ids))
        scores["groundedness"].append(judge_grounded(result["answer"], result["source_documents"]))
        scores["correctness"].append(judge_correct(result["answer"], case.expected_answer))

    return {k: sum(v) / len(v) for k, v in scores.items()}

def gate(scores: dict) -> None:
    regressions = [k for k, base in BASELINE.items() if scores[k] < base - TOLERANCE]
    if regressions:
        raise SystemExit(f"Blocked: regression in {regressions} -> {scores}")
```

**Per-answer telemetry.** Every answer logs the question, the retrieved document ids, the model, token counts, latency, and whether the user marked it useful. That gives me the two things I need: a live quality signal from real users, and the ability to reproduce any answer someone complains about. Traces go through LangSmith, so I can open an actual failing run rather than guess.

**Cost control.** Token spend is tracked per feature. Embeddings are cached — re-embedding unchanged documents is pure waste. Routing uses a small cheap model, final answers a stronger one. And there is a budget alert, because an AI feature with no cost ceiling is an incident waiting to happen.

The guardrail I insist on: **when retrieval confidence is low, the assistant says so and points to the human escalation path**. A support assistant that admits it does not know keeps its credibility. One that guesses loses it permanently after about three bad answers.

**Result.** Support engineers get grounded, cited answers to recurring issues instead of searching mail archives, and quality is a measured number that gates every change rather than an opinion.

**Lesson.** *"An LLM feature without an evaluation set is not a product, it is a demo. The evaluation loop is the architecture."*

**Follow-ups**

- *"How do you build the gold set?"* — From real support history, chosen with the people who answer those questions, and refreshed as new question types appear. About 100–200 cases is enough to catch regressions.
- *"How do you handle a model version change?"* — Same as any dependency upgrade. Run the evaluation set, compare, and only then roll forward. Model providers change behaviour; the gate is what protects you.
- *"What about hallucination in a financial context?"* — Strict grounding, mandatory citations, refusal when context is weak, and scope limits — this assistant answers support and process questions, not investment questions. Scope is a control.
- *"Would you let it take actions, not just answer?"* — Only with a human approval step and a full audit trail. Read-only first, actions later, and never both in the first release.

---

## Section index

| # | Question | Anchor project |
|---|----------|----------------|
| Q1 | Monolith vs modular monolith vs microservices | C |
| Q2 | Designing a REST API contract for many consumers | A |
| Q3 | API versioning and breaking changes | A |
| Q4 | ASP.NET Core solution structure | A |
| Q5 | Designing around a slow, flaky third-party API | A |
| Q6 | App Service vs Functions vs Container Apps | C |
| Q7 | Reliability and disaster recovery on Azure | A, C |
| Q8 | Controlling cloud cost | A, C |
| Q9 | Identity, secrets and access | A, C |
| Q10 | Infrastructure as code and promotion | C |
| Q11 | SQL Server and Snowflake together | A |
| Q12 | A serious database performance problem | A |
| Q13 | Idempotent, restartable ETL | A, C |
| Q14 | Orchestration across ADF, Tidal and Airflow | A |
| Q15 | Data quality in financial reporting | A, C |
| Q16 | Authentication and authorisation design | A |
| Q17 | Security and compliance for regulated data | A, C |
| Q18 | The CI/CD design that halved release time | C |
| Q19 | What I actually monitor | A |
| Q20 | An incident I led | A |
| Q21 | The AI/LLM reference architecture | B |
| Q22 | Evaluating and controlling RAG in production | B |

---

[← Overview](01-overview-positioning.md) · [Home](README.md) · [Next → System Design](03-system-design.md)
