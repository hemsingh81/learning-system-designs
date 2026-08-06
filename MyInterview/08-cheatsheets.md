# 08 · Cheat Sheets

[← Support & Post-Delivery](07-support-post-delivery.md) · [Home](README.md) · [Next → Study Plan](09-study-plan.md)

This is the page I read in the 20 minutes before an interview. No stories here — just fast recall. Everything below is real: my stack, my numbers, my projects.

**Jump to:** [Numbers](#numbers-i-never-forget) · [Anchor projects](#anchor-projects-in-one-line-each) · [My stack](#my-stack-at-a-glance) · [Azure services](#azure-services-what-and-when) · [Patterns](#patterns-i-actually-used) · [AI / RAG](#ai--rag-recall) · [Data & orchestration](#data--orchestration-recall) · [Hands-on code recall](#hands-on-code-recall) · [NFR checklist](#the-nfr-checklist) · [Phrases](#phrases-that-land) · [Frameworks](#answer-frameworks)

---

## Numbers I never forget

Say these with the project attached. A number without a project is just a claim.

| Number | What | Project |
|--------|------|---------|
| **60%** | less manual effort | Four completion apps automated the paper workflow (**C**) |
| **25%** | fewer processing errors | Validation layer in ADF/Functions ETL (**C**) |
| **50%** | shorter release cycle | Azure DevOps CI/CD & release strategy (**C**) |
| **30%** | less manual processing | ADF ingestion + transform + validation (**D**) |
| **20%** | faster decision turnaround | Power BI & IBM Cognos reporting (**D**) |
| **+20% / −15%** | team velocity up / post-deploy defects down | Sprint discipline & review gates (**D**) |
| **Pre-market window, daily** | reporting always lands on time | ADF + Tidal + Airflow orchestration (**A**) |
| **First production RAG app** | at the firm | AI/LLM reference architecture (**B**) |
| **4** | cloud apps designed & delivered | Completion platform (**C**) |
| **19 / 7** | years total / years as architect | My career line |

---

## Anchor projects in one line each

| Code | One-liner | Reach for it when they ask about… |
|------|-----------|-----------------------------------|
| **A** | Own the TCW investment-reporting platform end to end — .NET app tier, Web API, and the data pipeline ingesting BlackRock Aladdin into SQL Server & Snowflake, landing daily inside the pre-market window. | data platforms, orchestration, SLA/deadline, API design, performance, reuse |
| **B** | Authored TCW's AI/LLM reference architecture and shipped its first production RAG support assistant (LangChain/LangGraph/LangSmith, Chroma). | AI architecture, innovation, governance, evaluation, grounding |
| **C** | Solution architect for TengizChevroil's construction-completion platform — 4 cloud apps on ASP.NET Core & Azure Functions, microservices, CI/CD. | microservices, Azure hosting, integration, CI/CD, stakeholders, on-site delivery |
| **D** | Architected & delivered reporting/ETL for two US alternative-investment managers (Sculptor, Bain). | ETL, reporting, Agile leadership, delivery metrics |
| **E** | Delivered content-managed & transactional web platforms for UK enterprise clients (Bupa, NHS, Unilever). | PoCs, pre-sales, code standards, regulated/public sector |

---

## My stack at a glance

| Layer | What I use |
|-------|-----------|
| **Backend** | ASP.NET Core, ASP.NET MVC, .NET 5+, C#, Web API / REST, microservices, EF, ADO.NET; Python + FastAPI for ETL services |
| **Frontend** | React JS, Angular, JavaScript, jQuery, Knockout JS, HTML5, CSS3 |
| **Azure** | App Services, Functions, Azure SQL, Blob Storage, Cosmos DB, Entra ID (Azure AD), Data Factory, DevOps, Boards |
| **Data** | SQL Server, T-SQL, stored procs, query tuning; Snowflake; ADF, Tidal, Apache Airflow; BlackRock Aladdin API; Power BI, IBM Cognos |
| **AI / LLM** | RAG, LangChain, LangGraph, LangSmith, Chroma DB, embeddings/semantic search, prompt design, GitHub Copilot |
| **Ways of working** | Agile/Scrum, Kanban, design & code review, technical mentoring, production governance, offshore team leadership |
| **Domains** | Asset/investment management, financial services, energy, healthcare, public sector |

---

## Azure services — what and when

One sentence each. Enough to place the service and say when *I* reach for it.

| Service | Use it for | My usage |
|---------|-----------|----------|
| **App Services** | Host web apps / APIs with scaling & slots | .NET app + Web API tiers (A, C) |
| **Functions** | Event-driven / serverless compute | ETL steps & workflow automation (C) |
| **Azure SQL** | Managed relational OLTP store | Operational reporting store (A, C) |
| **Snowflake** | Analytical / historical store at scale | Analytical tier alongside Azure SQL (A) |
| **Data Factory (ADF)** | Orchestrated ETL/ELT pipelines | Daily ingestion & transform (A, C, D) |
| **Blob Storage** | Cheap durable object/document store | Secure document management (C) |
| **Cosmos DB** | Low-latency global NoSQL | Where the access pattern is key/document, not relational |
| **Entra ID (Azure AD)** | Identity, SSO, app registrations | Auth across apps |
| **Azure DevOps / Boards** | CI/CD pipelines, work tracking | Release strategy that halved cycle time (C) |

**One-liner on the data split:** *"I land data into an operational store (Azure SQL) and a separate analytical store (Snowflake), so a heavy historical query can never slow the report that has the morning deadline."*

---

## Patterns I actually used

| Pattern | One-line why | Where |
|---------|-------------|-------|
| **Microservices decomposition** | Independent apps for independent workflows | 4 completion apps (C) |
| **N-tier (app / API / data)** | Clear seams, testable, reusable API layer | Reporting platform (A) |
| **Event-driven / serverless** | React to events, pay per use, scale to zero | Functions-based ETL (C) |
| **Reusable controller + Web API pattern** | Replace per-report bespoke code, shorten build | Every reporting module (A) |
| **Operational + analytical store split** | Protect the deadline query from heavy history | Reporting platform (A) |
| **Dependency-aware orchestration** | Sequence pipelines so failures surface early | ADF + Tidal + Airflow (A) |
| **Validation + retry + reconciliation** | Bad/partial loads never reach a report | FastAPI ETL from Aladdin (A) |
| **Strangler-fig migration** | Replace a legacy system piece by piece, safely | migration scenarios (see [03](03-system-design.md)) |
| **RAG (retrieve → ground → orchestrate → evaluate)** | Grounded AI answers, no free-floating generation | RAG support assistant (B) |
| **CI/CD + release strategy** | Ship faster and safer | Azure DevOps (C) |

---

## AI / RAG recall

The four pillars of my AI/LLM reference architecture — memorise the order:

> **Retrieval → Grounding → Orchestration → Evaluation**

| Piece | Tool I used | One-liner |
|-------|-------------|-----------|
| **Retrieval** | Chroma DB, embeddings | Search knowledge by meaning, not keyword |
| **Grounding** | LangChain | Answer only from retrieved firm documents |
| **Orchestration** | LangGraph | Control the multi-step flow / agentic steps |
| **Evaluation** | LangSmith | Trace and measure responses — no blind trust |
| **Sources indexed** | — | Support emails, Confluence runbooks, past response threads |

**RAG vs fine-tuning (one line):** *"RAG, because the knowledge changes constantly and must trace back to a source — in a regulated firm I have to show where an answer came from."*

**Anti-hallucination (one line):** *"Ground strictly in retrieved context, evaluate with LangSmith, and if retrieval finds nothing relevant the right answer is to say so — not to improvise."*

---

## Data & orchestration recall

| Tool | What it does for me |
|------|---------------------|
| **Azure Data Factory** | Pipeline orchestration for ingestion & transform |
| **Tidal Workload Automation** | Enterprise scheduling / cross-system job dependencies |
| **Apache Airflow** | DAG-based orchestration with dependency-aware sequencing |
| **FastAPI ETL** | Python services ingesting Aladdin → SQL Server & Snowflake, with validation/retry/reconciliation |
| **BlackRock Aladdin API** | Source of portfolio, position & transaction data |

**Slow-query tuning order (say it as a list):** measure the plan → check the cheap causes (missing index, stale stats, non-sargable predicate, over-broad query) → rewrite before re-indexing → add indexes deliberately (they cost on writes) → model for growth up front.

---

## Hands-on code recall

For the deep-technical / coding rounds. Full code in [Full-Stack Hands-On](14-fullstack-hands-on.md); go deeper per stack in [.NET & C#](15-deepdive-dotnet.md), [React & TypeScript](16-deepdive-react-typescript.md), [Python & Data](17-deepdive-python-data.md); prep both interview coding formats in [Coding-Round Prep](18-coding-round-prep.md). One line each:

| Topic | The one thing to say |
|-------|----------------------|
| **ASP.NET Core controller** | Thin controller — bind input, call the service, map to a status code. Logic lives in the service. |
| **Async C#** | Async frees the thread on I/O; never `.Result`/`.Wait()`; bound concurrency with `SemaphoreSlim` against a rate-limited API. |
| **EF vs Dapper** | EF for domain/writes, hand-tuned SQL for hot reads; always project to a DTO; watch for N+1. |
| **FastAPI ETL** | Pydantic validation + tenacity retry/backoff + reconciliation — the three that make it production-grade. |
| **React data screen** | Four states: loading, error, empty, data — all rendered deliberately; `AbortController` to kill stale fetches. |
| **React state** | Server data is a cache (React Query), not app state (Redux). |
| **Angular** | Data in a service, `async` pipe to auto-unsubscribe, thin components. |
| **T-SQL** | Set-based, sargable predicates (no function on an indexed column), select only needed columns. |
| **Auth** | Validate the JWT (Entra ID) server-side every request; least privilege; secrets in Key Vault; token in memory not localStorage. |
| **Error handling** | One place per layer (middleware); log detail server-side, return a safe message. |
| **Testing** | Test the service hardest; always one edge case; review every AI-generated test. |
| **Debugging** | Reproduce → split the stack in half (data wrong or code wrong?) → keep halving → fix the class with a test. |

**Sargable one-liner:** *"Keep the column bare — `WHERE d >= @x AND d < @x+1`, never `WHERE CONVERT(date, d) = @x` — or the index cannot be used."*

**N+1 one-liner:** *"One screen firing fifty queries is an N+1 — project to a DTO in a single query instead."*

---

## The NFR checklist

When asked "how do you make it robust?", walk these — with a number, not an adjective.

| NFR | The specific answer, not the adjective |
|-----|----------------------------------------|
| **Availability** | Recovers from a failed load by replaying from the last checkpoint, without duplicating data |
| **Recovery (DR)** | Named RPO/RTO the architecture actually supports — not a number legal invented |
| **Performance** | Operational/analytical store split; query tuning; report inside its time budget as volume grows |
| **Deadline** | Dependency-aware orchestration + time-budget alerting = lands in the pre-market window daily |
| **Security** | Entra ID auth, least privilege, data residency honoured in the design |
| **Data integrity** | Validation + retry + reconciliation at ingestion; lineage traceable to source |
| **Observability** | Structured logging, row counts per stage, automated failure alerting mapped to runbooks |
| **Maintainability** | Reusable API pattern, standardised script/data-access generation, one path from schema change to release |

---

## Phrases that land

Say these near-verbatim. They compress a lot of credibility into one line.

- *"I own solutions end to end — architecture, integration design, build, release and production governance."*
- *"Never theory alone — I attach every point to a project, a decision, and a number."*
- *"I land data into an operational store and a separate analytical store, so a heavy historical query can never slow the report that has your morning deadline."*
- *"For a deadline-driven system, support is a clock, not a queue."*
- *"'The system is up' is not the same as 'the system is right' — so I build lineage and reconciliation in from day one."*
- *"In an incident: stabilise, communicate, contain, then diagnose."*
- *"An estimate without assumptions is a guess with a decimal point."*
- *"I never let a commitment be signed that I have not read."*
- *"AI in a regulated firm has to be grounded and evaluated — a confident wrong answer is worse than no answer."*
- *"The best pre-sales I do is running production well."*
- *"I design top-down and I still build bottom-up — nineteen years of writing code is why my architecture survives contact with it."*
- *"Open the hood and I will write the endpoint, the query, or the component with you — I am not a diagram-only architect."*

---

## Answer frameworks

Two I lean on. Full versions in [Overview & Positioning](01-overview-positioning.md).

**STAR-D** — for experience questions:

> **S**ituation → **T**ask → **A**ction → **R**esult → **D** = the lesson (the decision I would carry forward).

**C-QUAD** — for design questions:

> **C**larify (what are we optimising for?) → **Q**ualities (the NFRs that matter) → **U**nknowns (assumptions & risks) → **A**rchitecture (one diagram) → **D**ecisions (chosen vs rejected, with the trade-off).

**The opening (say it in your sleep):**

> "I am a solution architect on the Microsoft stack. Nineteen years in software, the last seven owning solutions end to end. Right now I architect the investment-reporting platform for TCW Group — the .NET app tier, the Web API layer, and the pipeline ingesting BlackRock Aladdin into SQL Server and Snowflake. I also wrote the firm's reference architecture for AI/LLM integration and shipped its first production RAG application."

---

[← Support & Post-Delivery](07-support-post-delivery.md) · [Home](README.md) · [Next → Study Plan](09-study-plan.md)
