# 51 · Concept: .NET Core (30 questions)

[← Data Design](50-concept-data-design.md) · [Home](README.md) · [Next → Case Studies & Decision-Making](52-concept-case-studies-decision-making.md)

This file explains **.NET (Core)** — the modern, cross-platform framework I build backend services and APIs with — in simple English and real depth. I answer from projects A–E, where I built .NET Core APIs and services for TCW's finance platforms.

> Simple one-liner: *".NET Core (now just .NET) is Microsoft's fast, cross-platform, open-source framework. I use it to build high-performance, secure Web APIs and services — with built-in dependency injection, async, and first-class Azure integration."*

**Jump to:** [DN1 What is .NET Core](#dn1--what-is-net-core) · [DN2 vs .NET Framework](#dn2--net-core-vs-net-framework) · [DN3 Cross-platform](#dn3--cross-platform) · [DN4 CLR & runtime](#dn4--clr-and-runtime) · [DN5 C#](#dn5--c-language) · [DN6 Web API](#dn6--aspnet-core-web-api) · [DN7 Middleware](#dn7--middleware-pipeline) · [DN8 DI](#dn8--dependency-injection) · [DN9 Service lifetimes](#dn9--service-lifetimes) · [DN10 Config](#dn10--configuration)
> [DN11 Async/await](#dn11--async-and-await) · [DN12 Minimal APIs](#dn12--minimal-apis-vs-controllers) · [DN13 Model binding](#dn13--model-binding-and-validation) · [DN14 Auth](#dn14--authentication-and-authorization) · [DN15 Error handling](#dn15--error-handling) · [DN16 Logging](#dn16--logging) · [DN17 Hosting](#dn17--hosting-and-kestrel) · [DN18 Health/resilience](#dn18--health-checks-and-resilience) · [DN19 Background work](#dn19--background-services) · [DN20 Options pattern](#dn20--options-pattern)
> [DN21 EF Core basics](#dn21--entity-framework-core) · [DN22 EF transactions](#dn22--ef-transactions-and-migrations) · [DN23 Testing](#dn23--testing) · [DN24 Performance](#dn24--performance) · [DN25 Security](#dn25--security) · [DN26 Docker](#dn26--containers-and-docker) · [DN27 Azure](#dn27--net-on-azure) · [DN28 gRPC/SignalR](#dn28--grpc-and-signalr) · [DN29 Pitfalls](#dn29--common-pitfalls) · [DN30 My approach](#dn30--my-approach) · [Section index](#section-index)

---

## DN1 · What is .NET Core?

**Simple explanation.** **.NET Core** (from .NET 5 onward just **.NET**) is Microsoft's modern, **open-source, cross-platform** framework for building apps — especially high-performance web APIs and services. It runs on Windows, Linux and macOS, and it's fast, modular and cloud-ready.

**Architect's view:** It's my default backend platform in the Microsoft/Azure ecosystem — fast, secure, well-tooled, with excellent Azure integration.

**Follow-ups**
- *"One-line?"* — Modern cross-platform .NET for fast, cloud-ready services.
- *"Still 'Core'?"* — Rebranded to just ".NET" from v5; same lineage.

---

## DN2 · .NET Core vs .NET Framework

**Simple explanation.** **.NET Framework** is the old, Windows-only platform. **.NET (Core)** is the new, **cross-platform, open-source, faster** rewrite — the future. For new work I always use modern .NET; Framework is legacy/maintenance only.

**Follow-ups**
- *"New projects?"* — Modern .NET — never .NET Framework.
- *"Migrate?"* — Yes, over time — for performance, cross-platform and support.

---

## DN3 · Cross-platform

**Simple explanation.** The same .NET code runs on **Windows, Linux and macOS**, so I can develop on any OS and deploy to cheap **Linux containers** on Azure. This flexibility and container-friendliness is a big reason it's cloud-first.

**Follow-ups**
- *"Why Linux matters?"* — Cheaper, lighter containers for cloud/Kubernetes.
- *"Write once?"* — Same codebase across OSes — no rewrite.

---

## DN4 · CLR and runtime

**Simple explanation.** .NET code compiles to **IL** (intermediate language) that the **CLR** (Common Language Runtime) runs via **JIT** compilation, with **garbage collection** managing memory automatically. I can also **AOT**-compile for faster startup in some scenarios.

**Follow-ups**
- *"Managed memory?"* — Yes — GC handles allocation/cleanup; I still avoid leaks (events, unmanaged handles).
- *"AOT?"* — Ahead-of-time compile for fast startup/small footprint (e.g. serverless).

---

## DN5 · C# language

**Simple explanation.** **C#** is the main .NET language — strongly typed, object-oriented, with modern features (async/await, LINQ, records, pattern matching, nullable reference types). Strong typing catches errors at compile time, which I value for reliable finance code.

**Follow-ups**
- *"Why strong typing?"* — Catches bugs early — safer for critical systems.
- *"LINQ?"* — Readable, type-safe queries over collections/data.

---

## DN6 · ASP.NET Core Web API

**Simple explanation.** **ASP.NET Core** is the web framework I use to build **REST APIs** and services. It's high-performance, has built-in **DI**, middleware, model binding, and hosts anywhere. It's how I expose backend functionality to clients ([file 47 SD17](47-concept-system-design.md#sd17--api-design)).

**Follow-ups**
- *"Main use?"* — REST APIs/microservices for web and mobile clients.
- *"Why fast?"* — Lean pipeline, Kestrel server, async throughout.

---

## DN7 · Middleware pipeline

**Simple explanation.** A request flows through a **middleware pipeline** — ordered components each handling cross-cutting concerns (auth, logging, error handling, CORS) before/after the endpoint. I compose the pipeline to control exactly how requests are processed.

**Follow-ups**
- *"Order matters?"* — Yes — e.g. exception handling first, auth before endpoints.
- *"Custom middleware?"* — Yes — for shared logic like request logging/correlation ids.

---

## DN8 · Dependency injection

**Simple explanation.** .NET has **built-in dependency injection**: I register services in the container and they're **injected** where needed. This decouples code, makes it testable (swap real for mocks), and is the backbone of .NET app structure.

**Follow-ups**
- *"Why DI?"* — Loose coupling + testability — no hard-wired dependencies.
- *"Built-in?"* — Yes — no external library needed for standard DI.

---

## DN9 · Service lifetimes

**Simple explanation.** DI services have **lifetimes**: **Singleton** (one for the app), **Scoped** (one per request), **Transient** (new each time). Choosing right matters — e.g. never inject a Scoped (like a DbContext) into a Singleton.

**Follow-ups**
- *"DbContext lifetime?"* — Scoped — per request.
- *"Common bug?"* — Captive dependency: Scoped/Transient trapped inside a Singleton.

---

## DN10 · Configuration

**Simple explanation.** .NET has a layered **configuration** system — appsettings.json, environment variables, and secrets — merged by environment. In production I pull secrets from **Azure Key Vault**, never from files ([file 37 Z12](37-concept-azure-services.md#z12--key-vault)).

**Follow-ups**
- *"Per-environment config?"* — appsettings.{Environment}.json overrides base.
- *"Secrets?"* — Key Vault + managed identity — not in appsettings.

---

## DN11 · Async and await

**Simple explanation.** **async/await** lets a service handle many requests without blocking threads while waiting on I/O (DB, HTTP). This gives high **throughput** and **scalability** — I use async for all I/O-bound work, which is most API code.

**Follow-ups**
- *"Why async everywhere for I/O?"* — Frees threads during waits → handles more concurrent requests.
- *"async for CPU work?"* — No benefit for pure CPU — async is for I/O.

---

## DN12 · Minimal APIs vs controllers

**Simple explanation.** **Controllers** organise endpoints in classes (good for larger, structured APIs). **Minimal APIs** define endpoints in a few lines (great for small services/microservices). I pick by size — minimal for lean services, controllers for bigger domains.

**Follow-ups**
- *"Minimal API when?"* — Small, focused microservices — less ceremony.
- *"Controllers when?"* — Large APIs needing structure, filters, conventions.

---

## DN13 · Model binding and validation

**Simple explanation.** ASP.NET Core **binds** request data (JSON, query, route) to C# objects automatically and **validates** them (data annotations / FluentValidation). I validate input at the boundary so bad data never reaches business logic.

**Follow-ups**
- *"Validate where?"* — At the API boundary — reject invalid input early.
- *"FluentValidation?"* — For complex rules beyond simple annotations.

---

## DN14 · Authentication and authorization

**Simple explanation.** **AuthN** (who you are) via **JWT/OAuth/OIDC** (Azure AD/Entra ID); **AuthZ** (what you can do) via roles/policies. I secure APIs with tokens and **policy-based** authorization — essential for finance access control ([file 47 SD22](47-concept-system-design.md#sd22--security)).

**Follow-ups**
- *"AuthN vs AuthZ?"* — Identity vs permissions — both enforced.
- *"Enterprise identity?"* — Entra ID (Azure AD) with JWT bearer tokens.

---

## DN15 · Error handling

**Simple explanation.** I use **global exception-handling middleware** to catch errors, log them, and return consistent, safe responses (**ProblemDetails**) — never leaking stack traces. Predictable errors improve reliability and security.

**Follow-ups**
- *"Global handler why?"* — One place for consistent, safe error responses.
- *"ProblemDetails?"* — Standard structured error format for APIs.

---

## DN16 · Logging

**Simple explanation.** .NET has built-in **structured logging** (ILogger) with providers. I log to **Application Insights** with **correlation ids** so I can trace a request across services ([file 47 SD21](47-concept-system-design.md#sd21--observability)) — without logging secrets/PII.

**Follow-ups**
- *"Structured logging?"* — Log key-value data, not just strings — queryable.
- *"Trace requests?"* — Correlation ids flow through logs and services.

---

## DN17 · Hosting and Kestrel

**Simple explanation.** .NET apps run on **Kestrel**, a fast cross-platform web server, usually behind a reverse proxy/gateway. The **generic host** wires up DI, config, logging and lifetime. I host on App Service, Container Apps, or AKS.

**Follow-ups**
- *"Kestrel alone?"* — Often behind Front Door/App Gateway for TLS, routing, WAF.
- *"Generic host?"* — Bootstraps DI/config/logging/graceful shutdown.

---

## DN18 · Health checks and resilience

**Simple explanation.** I add **health check** endpoints (liveness/readiness) so the platform knows if the app is healthy, and use **Polly** (or built-in resilience) for **retries, timeouts, circuit breakers** on outbound calls ([file 47 SD20](47-concept-system-design.md#sd20--resilience-patterns)).

**Follow-ups**
- *"Liveness vs readiness?"* — Alive vs ready-to-serve — orchestrators use both.
- *"Polly?"* — Resilience policies for transient failures.

---

## DN19 · Background services

**Simple explanation.** For work outside a request — processing queues, scheduled jobs — I use **BackgroundService / IHostedService** or worker services. This is where I consume Kafka/queues ([file 49](49-concept-kafka.md)) or run periodic tasks reliably.

**Follow-ups**
- *"Use case?"* — Queue consumers, scheduled jobs, long-running processors.
- *"Graceful shutdown?"* — Honour cancellation tokens to stop cleanly.

---

## DN20 · Options pattern

**Simple explanation.** The **Options pattern** binds configuration sections to strongly-typed classes injected via `IOptions<T>`. It keeps config clean, typed and testable instead of reading raw strings everywhere.

**Follow-ups**
- *"Why typed options?"* — Compile-time safety and easy injection/testing.
- *"Reload?"* — `IOptionsMonitor` supports config changes at runtime.

---

## DN21 · Entity Framework Core

**Simple explanation.** **EF Core** is .NET's **ORM** — I work with C# objects and it generates SQL, mapping classes to tables. It speeds development with LINQ queries, change tracking and migrations, while still allowing raw SQL when needed ([file 50](50-concept-data-design.md)).

**Follow-ups**
- *"ORM benefit?"* — Productivity + type-safe queries; less boilerplate SQL.
- *"Raw SQL?"* — Supported for hot/complex queries where I need control.

---

## DN22 · EF transactions and migrations

**Simple explanation.** EF Core wraps `SaveChanges` in a **transaction** (all-or-nothing) and supports explicit transactions across operations ([file 50 DD21](50-concept-data-design.md#dd21--transactions)). **Migrations** version schema changes in code, applied safely through CI/CD.

**Follow-ups**
- *"Transfer safely?"* — Debit + credit in one transaction — commit or roll back together.
- *"Schema changes?"* — Code-first migrations, reviewed and version-controlled.

---

## DN23 · Testing

**Simple explanation.** I test with **xUnit/NUnit**, **Moq** for mocking dependencies (easy thanks to DI), and **WebApplicationFactory** for integration tests against an in-memory host. I aim for fast unit tests plus key integration tests in CI.

**Follow-ups**
- *"DI helps testing?"* — Yes — swap real services for mocks cleanly.
- *"Integration tests?"* — Spin up the API in-memory and hit real endpoints.

---

## DN24 · Performance

**Simple explanation.** .NET is very fast, and I keep it that way: **async I/O**, efficient LINQ/EF (avoid N+1), caching with **Redis** ([file 48](48-concept-redis-cache.md)), response compression, and pooling. I profile and measure rather than guess.

**Follow-ups**
- *"EF N+1?"* — Use eager loading/projections to avoid many small queries.
- *"Caching?"* — Redis/in-memory for hot reads — cut DB load.

---

## DN25 · Security

**Simple explanation.** I apply **HTTPS everywhere**, JWT/OAuth auth, input validation, protection from injection (parameterised EF queries), secrets in **Key Vault**, and keep dependencies patched. Security is built into the pipeline, crucial for finance ([file 37 Z12](37-concept-azure-services.md#z12--key-vault)).

**Follow-ups**
- *"SQL injection?"* — EF parameterises queries — avoid string concatenation.
- *"Secrets?"* — Key Vault + managed identity — never in code.

---

## DN26 · Containers and Docker

**Simple explanation.** .NET apps containerise cleanly with small **Linux images**, so I build once and run consistently anywhere — App Service, **Container Apps** or **AKS** ([file 37](37-concept-azure-services.md)). Containers make deployment portable and scalable.

**Follow-ups**
- *"Why containers?"* — Consistency dev-to-prod + easy scaling/orchestration.
- *"Small images?"* — Use runtime-only base images and multi-stage builds.

---

## DN27 · .NET on Azure

**Simple explanation.** .NET is first-class on Azure: I host on **App Service / Container Apps / AKS / Functions**, authenticate to services with **managed identity**, store secrets in **Key Vault**, and monitor with **Application Insights** ([file 37](37-concept-azure-services.md)). It's the smoothest cloud fit for .NET.

**Follow-ups**
- *"Serverless .NET?"* — **Azure Functions** for event-driven/spiky work.
- *"Passwordless?"* — Managed identity → no connection secrets in code.

---

## DN28 · gRPC and SignalR

**Simple explanation.** Beyond REST, .NET offers **gRPC** (fast, contract-based service-to-service calls) and **SignalR** (real-time websockets for live updates). I use gRPC for internal high-performance APIs and SignalR for real-time features like live dashboards.

**Follow-ups**
- *"gRPC when?"* — Internal, high-throughput, strongly-typed service calls.
- *"SignalR when?"* — Real-time push (notifications, live data) to clients.

---

## DN29 · Common pitfalls

**Simple explanation.** Pitfalls: blocking on async (`.Result`/`.Wait()` → deadlocks), wrong DI lifetimes (captive dependencies), EF **N+1** queries, leaking secrets in config, no global error handling, and not using async for I/O. I design against each from the start.

**Follow-ups**
- *"Worst async mistake?"* — Blocking on async code → thread-pool starvation/deadlocks.
- *"Common EF mistake?"* — N+1 queries — fix with eager loading/projections.

---

## DN30 · My approach

**How I answer (the whole picture).** *".NET (Core) is my default backend platform in the Azure ecosystem — fast, cross-platform and cloud-ready. I build **ASP.NET Core Web APIs** using **dependency injection**, a well-ordered **middleware pipeline**, and **async/await** everywhere for I/O so services scale under load. I validate input at the boundary, secure APIs with **JWT/OAuth via Entra ID** and policy-based authorization, handle errors globally with **ProblemDetails**, and log structured data with correlation ids into **Application Insights**. Data access is **EF Core** with transactions and code-first migrations (decimal money, constraints), hot reads cached in **Redis**, and background/worker services consuming **Kafka** for async work. I add **health checks** and **Polly** resilience, keep secrets in **Key Vault** via managed identity, containerise to small Linux images, and deploy to **App Service / Container Apps / AKS** with CI/CD. I test with xUnit + Moq + integration tests. That's exactly how I built the secure, high-performance services behind TCW's finance platforms."*

**Follow-ups**
- *"One sentence?"* — Async ASP.NET Core APIs with DI, EF Core, resilience, Key Vault secrets, containers and Azure hosting.
- *"Why .NET for finance?"* — Strong typing, performance, security and first-class Azure integration.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| DN1 | .NET Core | Modern cross-platform .NET |
| DN2 | vs Framework | Use modern .NET, not legacy Framework |
| DN3 | Cross-platform | Runs on Windows/Linux/macOS |
| DN4 | CLR/runtime | IL + JIT + GC; AOT optional |
| DN5 | C# | Strongly typed, modern features |
| DN6 | Web API | ASP.NET Core REST services |
| DN7 | Middleware | Ordered request pipeline |
| DN8 | DI | Built-in; decouples + testable |
| DN9 | Lifetimes | Singleton/Scoped/Transient |
| DN10 | Config | Layered; secrets in Key Vault |
| DN11 | Async | async/await for scalable I/O |
| DN12 | Minimal vs controllers | Lean vs structured APIs |
| DN13 | Binding/validation | Validate at the boundary |
| DN14 | Auth | JWT/OAuth + policy authorization |
| DN15 | Error handling | Global handler + ProblemDetails |
| DN16 | Logging | Structured; correlation ids to App Insights |
| DN17 | Hosting | Kestrel + generic host |
| DN18 | Health/resilience | Health checks + Polly |
| DN19 | Background | Worker/hosted services for async |
| DN20 | Options | Strongly-typed config |
| DN21 | EF Core | ORM: objects → SQL |
| DN22 | EF transactions | ACID + code-first migrations |
| DN23 | Testing | xUnit + Moq + integration |
| DN24 | Performance | Async, avoid N+1, cache |
| DN25 | Security | HTTPS, auth, Key Vault, patched deps |
| DN26 | Containers | Small Linux images, portable |
| DN27 | Azure | App Service/AKS/Functions + managed identity |
| DN28 | gRPC/SignalR | Fast internal calls / real-time |
| DN29 | Pitfalls | Blocking async, DI lifetimes, N+1 |
| DN30 | My approach | Async APIs, DI, EF, resilience, Azure |

---

[← Data Design](50-concept-data-design.md) · [Home](README.md) · [Next → Case Studies & Decision-Making](52-concept-case-studies-decision-making.md)
