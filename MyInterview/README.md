# Solution Architect (Hands-On Full-Stack) Interview Kit — Hem Singh

**Position:** Solution Architect (Azure & .NET) who still writes production code · 7 years as an architect, 19 years in software
**Built for:** interviews, client panels, pre-sales conversations, and deep-technical / coding rounds
**Tone of this kit:** simple English, short sentences, real numbers, my own projects

> **My positioning in one line:** *I am a hands-on Solution Architect — I own the design end to end, and I still write production code myself across the full stack (React/Angular front end, ASP.NET Core Web API and C#, and Python/FastAPI ETL, with the SQL underneath).*

---

## How to use this kit

1. Read [Overview & Positioning](01-overview-positioning.md) first. It holds my **story bank** — four projects I keep coming back to in every answer.
2. Then pick the section that matches your interview round.
3. Every question follows the same shape:
   - **The question** — short, as an interviewer would ask it.
   - **My answer** — a story. Context → what I did → the trade-off → the number → the lesson.
   - **Follow-ups** — what they usually ask next, with a short reply.
4. Before the interview, read [Cheat Sheets](08-cheatsheets.md) and the [Pitches](10-pitch-and-resume.md). That is 20 minutes of work and it covers 80% of the opening.

> **Rule I follow in every answer:** never give theory alone. Always attach it to a project, a decision, and a number.

---

## Quick index by interview round

Under pressure, jump straight to the round you are in:

| If the round is… | Go to |
|---|---|
| **Intro / "tell me about yourself"** | [01 Overview](01-overview-positioning.md) · [10 Pitches](10-pitch-and-resume.md) |
| **Behavioural / leadership** | [04 Team](04-team-management.md) · [05 Client](05-client-engagement.md) · [06 RFP](06-rfp-presales.md) · [07 Support](07-support-post-delivery.md) |
| **Technical breadth** | [02 Technical Q&A](02-technical-qa.md) |
| **System design** | [03 System Design](03-system-design.md) |
| **Deep-technical (per stack)** | [15 .NET](15-deepdive-dotnet.md) · [16 React/TS](16-deepdive-react-typescript.md) · [17 Python/Data](17-deepdive-python-data.md) |
| **Hands-on coding** | [14 Full-Stack Hands-On](14-fullstack-hands-on.md) · [18 Coding-Round Prep](18-coding-round-prep.md) |
| **Performance / optimisation** | [19 Performance Deep Dive](19-performance-deep-dive.md) |
| **AI / ways-of-working leadership** | [20 AI-Assisted Development](20-ai-assisted-development.md) |
| **Tough / challenge questions** | [21 Objections & Tough Questions](21-objections-and-tough-questions.md) |
| **Concept deep-dives (30 Q&As each)** | [28 React](28-concept-reactjs.md) · [29 Angular](29-concept-angular.md) · [30 React vs Angular](30-concept-react-vs-angular.md) · [31 Web API](31-concept-aspnet-webapi.md) · [32 FastAPI](32-concept-fastapi.md) · [33 Web API vs FastAPI](33-concept-webapi-vs-fastapi.md) · [34 SQL Server](34-concept-sql-server.md) · [35 Snowflake](35-concept-snowflake.md) · [36 SQL vs Snowflake](36-concept-sqlserver-vs-snowflake.md) · [37 Azure Services](37-concept-azure-services.md) |
| **AI & platform deep-dives (30 Q&As each)** | [38 AI Skills & Workflow](38-concept-ai-skills-workflow.md) · [39 AI Agents & Agentic AI](39-concept-ai-agents-agentic.md) · [40 RAG](40-concept-rag.md) · [41 LangChain](41-concept-langchain.md) · [42 LangGraph](42-concept-langgraph.md) · [43 LangSmith](43-concept-langsmith.md) · [44 Vector DBs & Chroma](44-concept-vector-databases-chroma.md) · [45 Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md) · [46 LLM App Integration](46-concept-llm-application-integration.md) · [47 System Design](47-concept-system-design.md) · [48 Redis Cache](48-concept-redis-cache.md) · [49 Kafka](49-concept-kafka.md) · [50 Data Design](50-concept-data-design.md) · [51 .NET Core](51-concept-dotnet-core.md) |
| **Case studies & decision-making (why I chose what I built)** | [52 Hub](52-concept-case-studies-decision-making.md) · [53 A: Investment Reporting](53-case-study-a-investment-reporting.md) · [54 B: AI/RAG](54-case-study-b-ai-rag-assistant.md) · [55 C: Completion Platform](55-case-study-c-completion-platform.md) · [56 D: AM Reporting](56-case-study-d-asset-management-reporting.md) · [57 E: UK Web](57-case-study-e-uk-web-platforms.md) · [58 Decision-Making](58-case-study-decision-making.md) |
| **Principles & performance deep-dives (30 Q&As each)** | [59 SOLID Principles](59-concept-solid-principles.md) · [60 Design Principles & Patterns](60-concept-design-principles.md) · [61 React Performance](61-concept-react-performance.md) · [62 Angular Performance](62-concept-angular-performance.md) · [63 Web API / C# Performance](63-concept-webapi-performance.md) · [64 SQL Performance](64-concept-sql-performance.md) · [65 Microservices Performance](65-concept-microservices-performance.md) |
| **What's new / version evolution (30 Q&As each)** | [66 .NET & C#](66-concept-dotnet-whats-new.md) · [67 SQL Server](67-concept-sqlserver-whats-new.md) · [68 Azure Services](68-concept-azure-whats-new.md) · [69 React](69-concept-react-whats-new.md) · [70 Angular](70-concept-angular-whats-new.md) · [71 TypeScript & Tooling](71-concept-typescript-tooling-whats-new.md) |
| **Behavioural / "tell me about a time"** | [25 STAR Story Bank](25-star-story-bank.md) |
| **Questions to ask them** | [26 Reverse-Interview Questions](26-reverse-interview-questions.md) |
| **"First 90 days?" question** | [27 My First 90 Days](27-first-90-days.md) |
| **Salary / offer negotiation** | [23 Offer & Salary Negotiation](23-offer-negotiation.md) |
| **Tailoring to a specific job** | [24 Role-Tailoring Guide](24-role-tailoring-guide.md) |
| **Last 2 minutes before** | [22 Panic Sheet](22-panic-sheet.md) |
| **Last 20 minutes before** | [08 Cheat Sheets](08-cheatsheets.md) · [09 Study Plan → night before](09-study-plan.md) |

---

## Contents

| # | Section | What is inside | Questions |
|---|---------|----------------|-----------|
| 01 | [Overview & Positioning](01-overview-positioning.md) | Who I am, my 4 anchor projects, answer frameworks | — |
| 02 | [Technical Q&A](02-technical-qa.md) | .NET, Azure, APIs, data, security, DevOps, observability, AI/RAG | 22 |
| 03 | [System Design](03-system-design.md) | 8 full design scenarios with diagrams | 8 |
| 04 | [Team Management](04-team-management.md) | Hiring, mentoring, conflict, scope change, hard messages | 10 |
| 05 | [Client Engagement](05-client-engagement.md) | Proposals, negotiation, PoCs, change requests, follow-ups | 8 |
| 06 | [RFP & Pre-Sales](06-rfp-presales.md) | Leading responses, solution outlines, estimates, win themes | 7 |
| 07 | [Support & Post-Delivery](07-support-post-delivery.md) | Runbooks, SLAs, escalation, knowledge transfer, upsell | 8 |
| 08 | [Cheat Sheets](08-cheatsheets.md) | One-page recall: patterns, Azure services, numbers, phrases | — |
| 09 | [Study Plan](09-study-plan.md) | 2-week and 1-week plans + mock interview scripts | — |
| 10 | [Pitch & Resume Summary](10-pitch-and-resume.md) | 30-second, 2-minute pitch, one-page resume | — |
| 11 | [Email Templates](11-email-templates.md) | Proposal, demo follow-up, scope change, support handover | — |
| 12 | [Checklists](12-checklists.md) | RFP, pre-sales, design review, go-live, handover | — |
| 13 | [Reproduce Prompt](13-reproduce-prompt.md) | One paragraph to regenerate or extend this kit | — |
| 14 | [Full-Stack Hands-On](14-fullstack-hands-on.md) | Code-backed answers: C#, Web API, EF, FastAPI, React, Angular, SQL, auth, testing, debugging | 12 |
| 15 | [Deep Dive: .NET & C#](15-deepdive-dotnet.md) | DI/lifetimes, middleware, LINQ, Span/GC, concurrency, Polly, caching, EF advanced, gRPC, secrets | 10 |
| 16 | [Deep Dive: React & TypeScript](16-deepdive-react-typescript.md) | Generics, typed components, hooks internals, effects, performance, forms, error boundaries, testing, a11y | 10 |
| 17 | [Deep Dive: Python & Data](17-deepdive-python-data.md) | Async, Pydantic, Pandas, idempotent ETL, SQL tuning, Snowflake, orchestration, RAG code, quality, testing | 10 |
| 18 | [Coding-Round Prep](18-coding-round-prep.md) | Both formats: DSA patterns + worked examples (C#/TS/Python) and a feature-building playbook | — |
| 19 | [Performance Deep Dive](19-performance-deep-dive.md) | Front-end, backend & database performance with project stories, metrics and tools | 12 |
| 20 | [AI-Assisted Development](20-ai-assisted-development.md) | End-to-end team playbook: pilot, roles, guardrails, QA, security, metrics, PRDs, rollout | 4 |
| 21 | [Objections & Tough Questions](21-objections-and-tough-questions.md) | Crisp rebuttals to the hardest challenges about being a hands-on architect | 10 |
| 22 | [Panic Sheet](22-panic-sheet.md) | One page for the last 2 minutes: opening line, projects, numbers, phrases, reset routine | — |
| 23 | [Offer & Salary Negotiation](23-offer-negotiation.md) | Calm, evidence-based answers to the compensation conversation | 8 |
| 24 | [Role-Tailoring Guide](24-role-tailoring-guide.md) | 20-minute routine to adapt the kit to any job description | — |
| 25 | [STAR Story Bank](25-star-story-bank.md) | 10 fully-written behavioural stories in STAR-D form (failure, conflict, influence, deadline, crisis…) | 10 |
| 26 | [Reverse-Interview Questions](26-reverse-interview-questions.md) | Sharp questions to ask them, grouped by interviewer, with a signal-reading table | — |
| 27 | [My First 90 Days](27-first-90-days.md) | Ready answer to "what would you do in your first 90 days?" — Listen → Plan → Deliver | — |
| 28 | [Concept: ReactJS](28-concept-reactjs.md) | React from the ground up: components, hooks, state, VDOM, performance, architecture, SSR, security, testing | 30 |
| 29 | [Concept: Angular](29-concept-angular.md) | Modern Angular: components, DI, RxJS, signals, change detection, forms, guards, i18n, architecture | 30 |
| 30 | [Concept: React vs Angular](30-concept-react-vs-angular.md) | Fair, feature-by-feature comparison + a one-minute decision framework | 30 |
| 31 | [Concept: ASP.NET Core Web API](31-concept-aspnet-webapi.md) | Controllers, DI, middleware, EF, auth, versioning, performance, testing, hosting | 30 |
| 32 | [Concept: FastAPI](32-concept-fastapi.md) | Async Python API: Pydantic, dependency injection, auth, background tasks, testing, deployment | 30 |
| 33 | [Concept: Web API vs FastAPI](33-concept-webapi-vs-fastapi.md) | When I pick .NET vs Python, side-by-side, with a decision framework | 30 |
| 34 | [Concept: SQL Server](34-concept-sql-server.md) | Indexes, execution plans, transactions, tuning, concurrency, security, HA, T-SQL | 30 |
| 35 | [Concept: Snowflake](35-concept-snowflake.md) | Architecture, virtual warehouses, micro-partitions, cost, sharing, performance | 30 |
| 36 | [Concept: SQL Server vs Snowflake](36-concept-sqlserver-vs-snowflake.md) | OLTP vs analytics, cost model, when to use each, with a decision framework | 30 |
| 37 | [Concept: Azure Core Services](37-concept-azure-services.md) | Blob, Key Vault, App Service, Service Bus, Functions, AI Foundry and more | 30 |
| 38 | [Concept: AI Skills & AI Workflow](38-concept-ai-skills-workflow.md) | The AI skills an architect needs and how AI workflows are designed end to end | 30 |
| 39 | [Concept: AI Agents & Agentic AI](39-concept-ai-agents-agentic.md) | Agents, tools, planning, multi-agent systems, autonomy, guardrails | 30 |
| 40 | [Concept: RAG](40-concept-rag.md) | Retrieval-Augmented Generation: chunking, retrieval, grounding, evaluation | 30 |
| 41 | [Concept: LangChain](41-concept-langchain.md) | Chains, prompts, retrievers, tools, memory, output parsing | 30 |
| 42 | [Concept: LangGraph](42-concept-langgraph.md) | Stateful graphs, nodes/edges, cycles, human-in-the-loop, agent orchestration | 30 |
| 43 | [Concept: LangSmith](43-concept-langsmith.md) | Tracing, evaluation, datasets, monitoring for LLM apps | 30 |
| 44 | [Concept: Vector Databases & Chroma](44-concept-vector-databases-chroma.md) | Embeddings storage, ANN/HNSW, metadata filters, Chroma, Azure AI Search | 30 |
| 45 | [Concept: Embeddings & Semantic Search](45-concept-embeddings-semantic-search.md) | Embeddings, similarity, hybrid search, re-ranking, model choice | 30 |
| 46 | [Concept: LLM Application Integration](46-concept-llm-application-integration.md) | Production engineering: reliability, safety, cost, streaming, monitoring | 30 |
| 47 | [Concept: System Design](47-concept-system-design.md) | Scalability, caching, data, CAP, resilience, trade-offs | 30 |
| 48 | [Concept: Redis Cache](48-concept-redis-cache.md) | Caching, cache-aside, TTL/invalidation, sessions, rate limiting, HA | 30 |
| 49 | [Concept: Kafka](49-concept-kafka.md) | Topics, partitions, consumer groups, delivery guarantees, event-driven | 30 |
| 50 | [Concept: Data Design (Data Modeling)](50-concept-data-design.md) | Normalization, keys, indexing, NoSQL modeling, transactions, warehousing | 30 |
| 51 | [Concept: .NET Core](51-concept-dotnet-core.md) | ASP.NET Core, DI, async, EF Core, resilience, security, Azure hosting | 30 |
| 52 | [Case Studies Hub](52-concept-case-studies-decision-making.md) | The hub: the 8-beat case-study template, the 5-filter decision lens, and links to every case study | — |
| 53 | [Case Study A: Investment Reporting](53-case-study-a-investment-reporting.md) | TCW investment reporting end to end — how it started, why SQL+Snowflake, FastAPI ETL, who was involved, decision log + Q&As | 6 |
| 54 | [Case Study B: AI/RAG Assistant](54-case-study-b-ai-rag-assistant.md) | TCW's AI reference architecture + first production RAG app — RAG vs fine-tuning, the four pillars, decision log + Q&As | 6 |
| 55 | [Case Study C: Completion Platform](55-case-study-c-completion-platform.md) | TengizChevroil microservices on managed Azure — why microservices, adoption, integration contracts, decision log + Q&As | 6 |
| 56 | [Case Study D: Asset-Management Reporting](56-case-study-d-asset-management-reporting.md) | Sculptor & Bain ETL + delivery — +20% velocity/−15% defects by killing rework, ADF ETL, decision log + Q&As | 5 |
| 57 | [Case Study E: UK Web Platforms](57-case-study-e-uk-web-platforms.md) | Bupa/NHS/Unilever — PoC-led direction, owned code standards, regulated delivery, decision log + Q&As | 5 |
| 58 | [Cross-cutting Decision-Making](58-case-study-decision-making.md) | The reusable how-I-decide playbook — the decision lens, ADR habit, reversibility, buy-in, wrong decisions | 7 |
| 59 | [Concept: SOLID Principles](59-concept-solid-principles.md) | The five principles for changeable code — SRP, OCP, LSP, ISP, DIP — with real examples, smells, refactoring and when not to over-apply | 30 |
| 60 | [Concept: Design Principles & Patterns](60-concept-design-principles.md) | Beyond SOLID — DRY/KISS/YAGNI/SoC + the patterns I actually use (Strategy, Factory, Adapter, Decorator, Repository, CQRS, Circuit Breaker) | 30 |
| 61 | [Concept: React Performance Tuning](61-concept-react-performance.md) | Measure-first React speed — bundle/code-splitting, re-renders, memoisation, virtualisation, caching, Web Vitals, real fix story | 30 |
| 62 | [Concept: Angular Performance Tuning](62-concept-angular-performance.md) | Change detection (OnPush/Signals/zoneless), trackBy, lazy loading, virtual scroll, RxJS pitfalls, @defer, real fix story | 30 |
| 63 | [Concept: Web API / C# Performance Tuning](63-concept-webapi-performance.md) | Async I/O, N+1/EF tuning, caching/Redis, payloads, resilience, memory/GC, load testing — stop doing needless work | 30 |
| 64 | [Concept: SQL Database Performance Tuning](64-concept-sql-performance.md) | Execution plans, indexing (covering/composite/SARGable), locking/isolation, partitioning, OLTP vs OLAP, Snowflake tuning | 30 |
| 65 | [Concept: Microservices / System Architecture Performance](65-concept-microservices-performance.md) | Distributed tracing, cutting hops, independent scaling, caching, async, circuit breakers/bulkheads, CQRS, managed Azure | 30 |
| 66 | [Concept: .NET & C# — What's New](66-concept-dotnet-whats-new.md) | Release cadence/LTS, net6→9, minimal APIs, Native AOT, keyed DI, records, nullable refs, primary constructors, EF Core — old-vs-new code | 30 |
| 67 | [Concept: SQL Server — What's New](67-concept-sqlserver-whats-new.md) | 2016→2022, Query Store, Always Encrypted, Intelligent QP, Ledger, PSP, compatibility level, Azure SQL evergreen — old-vs-new T-SQL | 30 |
| 68 | [Concept: Azure Services — What's New](68-concept-azure-whats-new.md) | Container Apps, Azure OpenAI/AI Foundry, Entra ID rename, managed identity, Bicep, Fabric, retirements — shifts not buttons | 30 |
| 69 | [Concept: React — What's New](69-concept-react-whats-new.md) | Hooks 16.8 → concurrent/batching 18 → Server Components/Actions/use 19, compiler, Next.js/Vite — old-vs-new JSX | 30 |
| 70 | [Concept: Angular — What's New](70-concept-angular-whats-new.md) | Standalone, Signals, @if/@for control flow, @defer, zoneless, SSR/hydration, esbuild, `ng update` migrations — old-vs-new | 30 |
| 71 | [Concept: TypeScript & Frontend Tooling — What's New](71-concept-typescript-tooling-whats-new.md) | TS 4.x→5.x (satisfies, const params, decorators, using), ESM, Vite/esbuild/SWC, pnpm, Vitest — safer types, faster tools | 30 |

**Total: 1294 questions with full answers and follow-ups.**

---

## My four anchor projects (memorise these)

![Four anchor projects I use in every interview answer: TCW investment reporting, TCW AI and RAG framework, TengizChevroil completion platform, and Sculptor and Bain asset-management reporting](assets/anchor-projects.svg)

*Figure 1 — My story bank. Nearly every question in this kit maps back to one of these four.*

| Code | Project | Client & years | Use it for |
|------|---------|----------------|-----------|
| **A** | Investment Reporting Platform + Aladdin ingestion | TCW Group, Los Angeles · 2025→now | Data platform, orchestration, SLA, API design, performance |
| **B** | AI/LLM integration framework + RAG support assistant | TCW Group · 2025→now | AI architecture, innovation, governance, cost, evaluation |
| **C** | Construction completion platform (4 cloud apps) | TengizChevroil, Kazakhstan · 2021–2025 | Microservices, Azure hosting, CI/CD, integration, stakeholders |
| **D** | Asset-management reporting & ETL | Sculptor Capital NY, Bain Capital Boston · 2016–2022 | ETL, reporting, Agile leadership, delivery metrics |
| **E** | UK enterprise web platforms | Bupa, NHS e-Contracting, Unilever · 2012–2016 | PoCs, pre-sales, code standards, regulated/public sector |

---

## Quick numbers I never forget

These come up in almost every answer. Learn them cold.

| Number | Where it comes from |
|--------|--------------------|
| **60%** less manual effort | Four completion apps automated the paper workflow (Project C) |
| **25%** fewer processing errors | Validation layer added in the ADF/Functions ETL (Project C) |
| **50%** shorter release cycle | Azure DevOps CI/CD pipelines and release strategy (Project C) |
| **30%** less manual processing | ADF ingestion + transformation + validation (Project D) |
| **20%** faster decision turnaround | Power BI and Cognos reporting (Project D) |
| **+20%** team velocity, **−15%** post-deploy defects | Sprint discipline and review gates (Project D) |
| **Pre-market window met daily** | Dependency-aware ADF + Tidal + Airflow orchestration (Project A) |
| **First production RAG app** at the firm | AI/LLM reference architecture (Project B) |
| **19 years** total, **7 years** as architect | My career line |

---

## The three sentences I open with

> "I am a solution architect on the Microsoft stack. Nineteen years in software, the last seven owning solutions end to end — architecture, integration design, build, release and production governance.
>
> Right now I architect the investment-reporting platform for TCW Group in Los Angeles: the .NET application tier, the Web API layer, and the data pipeline that ingests BlackRock Aladdin data into SQL Server and Snowflake.
>
> I also wrote the firm's reference architecture for AI/LLM integration and shipped its first production RAG application."

Full versions are in [Pitch & Resume Summary](10-pitch-and-resume.md).

---

[Start here → Overview & Positioning](01-overview-positioning.md)
