# 37 · Concept: Azure Core Services & Azure AI Foundry (30 questions)

[← SQL Server vs Snowflake](36-concept-sqlserver-vs-snowflake.md) · [Home](README.md) · [Next → AI Skills & Workflow](38-concept-ai-skills-workflow.md)

This file explains the **main Azure services** an architect must know, plus **Azure AI Foundry**, in simple English and real depth. My platforms run on Azure, so I answer from real use (Projects A, B, C).

> Simple one-liner: *"Azure is Microsoft's cloud. As an architect I don't memorise all 200+ services — I know the core building blocks (storage, secrets, hosting, messaging) and how to wire them into a secure, scalable system."*

**Jump to (core services):** [Z1 What is Azure](#z1--what-is-azure) · [Z2 Blob Storage](#z2--azure-blob-storage) · [Z3 Key Vault](#z3--azure-key-vault) · [Z4 App Service](#z4--azure-app-service) · [Z5 Functions](#z5--azure-functions-serverless) · [Z6 Service Bus](#z6--azure-service-bus-messaging) · [Z7 Data & DB services](#z7--data-and-database-services) · [Z8 Networking & identity](#z8--identity-and-networking) · [Z9 Monitoring & DevOps](#z9--monitoring-and-devops) · [Z10 Azure AI Foundry](#z10--azure-ai-foundry)
> **Compute & hosting:** [Z11 Containers](#z11--containers-aci-aca-and-aks) · [Z12 API Management](#z12--api-management) · [Z13 Front Door/CDN](#z13--front-door-app-gateway-and-cdn) · [Z14 Static Web Apps](#z14--static-web-apps-for-the-front-end) · [Z15 Event-driven](#z15--event-grid-vs-service-bus-vs-event-hubs)
> **Data & caching:** [Z16 Redis Cache](#z16--azure-cache-for-redis) · [Z17 Cosmos deep](#z17--cosmos-db-in-depth) · [Z18 Storage deep](#z18--storage-accounts-in-depth) · [Z19 Data pipeline](#z19--the-data-pipeline-on-azure)
> **Governance & reliability:** [Z20 Landing zones](#z20--governance-and-landing-zones) · [Z21 IaC](#z21--infrastructure-as-code) · [Z22 Cost management](#z22--cost-management) · [Z23 Well-Architected](#z23--the-well-architected-framework) · [Z24 Resilience/HA](#z24--resilience-regions-and-availability-zones) · [Z25 Security posture](#z25--security-posture-and-defender)
> **AI & full-stack lens:** [Z26 Azure OpenAI](#z26--azure-openai-service) · [Z27 AI Search](#z27--ai-search-for-rag) · [Z28 Full-stack on Azure](#z28--a-full-stack-app-on-azure) · [Z29 Choosing compute](#z29--how-i-choose-a-compute-service) · [Z30 Reference architecture](#z30--my-reference-architecture) · [Section index](#section-index)

---

## Z1 · What is Azure?

**Simple explanation.** Azure is Microsoft's **cloud platform** — you rent computing (servers, storage, databases, AI) instead of buying hardware. It offers three service models: **IaaS** (you manage the VM), **PaaS** (Microsoft manages the platform, you deploy code — my usual choice), and **SaaS** (ready-to-use software).

**Architect's view:** I favour **PaaS** — App Service, Functions, Azure SQL — so my team ships features instead of patching servers.

**Follow-ups**
- *"IaaS vs PaaS vs SaaS?"* — IaaS = rent the machine; PaaS = rent the platform (deploy code); SaaS = rent the finished app. More managed = less ops burden.
- *"Why PaaS by default?"* — Less to operate, built-in scaling and patching — more time on business value.

---

## Z2 · Azure Blob Storage

**Simple explanation.** **Blob Storage** stores large amounts of **unstructured** data — files, images, backups, logs, documents, data-lake files ("blob" = Binary Large OBject). It's cheap, massively scalable, and accessed over HTTP.

**Access tiers** control cost: **Hot** (frequent access), **Cool** (infrequent), **Archive** (rarely, cheapest). I move old data to cooler tiers to save money.

*"I use Blob Storage as the landing zone for raw data files before the ETL loads them, and for storing documents the RAG app indexes."*

**Follow-ups**
- *"Blob vs a database?"* — Blobs for big files/unstructured data; a database for structured, queryable records. Different jobs.
- *"How is it secured?"* — Private access by default; I use Entra ID / SAS tokens and encryption at rest — never public unless required.

---

## Z3 · Azure Key Vault

**Simple explanation.** **Key Vault** safely stores **secrets** — passwords, connection strings, API keys, certificates, encryption keys. Apps read them at runtime, so secrets are **never hard-coded** in source or config files.

```csharp
// App reads the secret at runtime from Key Vault — not from code
var secret = await keyVaultClient.GetSecretAsync("AladdinApiKey");
```

**Why it's essential:** a leaked connection string in code is a security incident. Key Vault centralises secrets, controls access via identity, and logs every access.

**Follow-ups**
- *"How does the app authenticate to Key Vault?"* — With a **Managed Identity** (see [Z8](#z8--identity-and-networking)) — no secret needed to fetch secrets, breaking the chicken-and-egg problem.
- *"Secrets vs keys vs certificates?"* — Secrets = strings (passwords/keys); keys = cryptographic keys for encryption; certificates = TLS/identity certs. Key Vault holds all three.

---

## Z4 · Azure App Service

**Simple explanation.** **App Service** is a fully-managed **PaaS for hosting web apps and APIs**. You deploy your code (like an ASP.NET Core Web API) and Azure handles the servers, patching, scaling and load balancing. No VM to manage.

**Key features:** easy scaling (up/out), **deployment slots** (deploy to a *staging* slot, test, then swap to production with zero downtime), and built-in auth.

*"On TengizChevroil the cloud apps ran on App Service — deployment slots let us release with zero downtime and roll back instantly by swapping back."*

**Follow-ups**
- *"App Service vs a VM?"* — App Service is managed (no OS to patch); a VM gives full control but more ops work. I default to App Service.
- *"What are deployment slots?"* — Parallel environments (e.g. staging) you warm up and *swap* into production instantly — safe releases and instant rollback.

---

## Z5 · Azure Functions (serverless)

**Simple explanation.** **Functions** is **serverless** compute — small pieces of code that run **in response to an event** (a timer, a file landing in Blob, a message on a queue, an HTTP call). You don't manage servers, and you pay only when it runs.

```csharp
[Function("ProcessFile")]
public void Run([BlobTrigger("incoming/{name}")] Stream file, string name)
{
    // runs automatically whenever a file lands in the 'incoming' container
}
```

*"On TengizChevroil I used Functions for event-driven work — processing triggered by events rather than a constantly-running service."*

**Follow-ups**
- *"Functions vs App Service?"* — App Service for always-on web apps/APIs; Functions for short, event-driven, bursty tasks where you pay per execution.
- *"What's a cold start?"* — A brief delay when a function wakes from idle; the Premium plan keeps instances warm to avoid it.

---

## Z6 · Azure Service Bus (messaging)

**Simple explanation.** **Service Bus** is enterprise **messaging** — it lets services talk **asynchronously** by passing messages, so they're **decoupled**. The sender drops a message and moves on; the receiver processes it when ready. If the receiver is down, the message waits safely in the queue.

- **Queues** — one-to-one (one consumer processes each message).
- **Topics/subscriptions** — one-to-many (publish once, many subscribers get it).

**Why it matters:** reliability and scale. A traffic spike queues up instead of crashing the receiver; a failed message can retry or go to a **dead-letter queue** for inspection.

**Follow-ups**
- *"Service Bus vs Storage Queue?"* — Storage Queues are simple/cheap; Service Bus adds enterprise features (topics, ordering, transactions, dead-lettering) for complex systems.
- *"Why decouple with messaging?"* — Services scale and fail independently; the system stays resilient under load — core to microservices like TengizChevroil.

---

## Z7 · Data and database services

**Simple explanation.** The Azure data services I reach for:
- **Azure SQL Database** — managed SQL Server in the cloud (my operational store).
- **Azure Cosmos DB** — globally-distributed NoSQL for massive scale and low latency.
- **Azure Data Factory (ADF)** — cloud **ETL/orchestration** — moves and transforms data on a schedule (I use it in the TCW pipeline).
- **Azure Data Lake Storage** — Blob-based storage optimised for big-data analytics.

*"On TCW, ADF is part of the orchestration that lands Aladdin data; Azure SQL is the operational store; and analytics flow to Snowflake."*

**Follow-ups**
- *"SQL vs Cosmos DB?"* — SQL for relational/structured with transactions; Cosmos for globally-distributed, high-scale NoSQL with flexible schemas.
- *"What does ADF do exactly?"* — Orchestrates data movement/transformation with pipelines, triggers and monitoring — cloud-native ETL.

---

## Z8 · Identity and networking

**Simple explanation.** Two foundations:
- **Microsoft Entra ID** (formerly Azure AD) — the **identity** service. It handles sign-in and issues tokens; my APIs validate them and authorise with roles.
- **Managed Identity** — gives an Azure resource its *own* identity so it can call other services (Key Vault, SQL) **without any stored secret**. This is the secure, modern pattern.
- **Networking** — **VNets** isolate resources; **Private Endpoints** keep traffic off the public internet.

**Follow-ups**
- *"Why Managed Identity over a connection string?"* — No secret to leak or rotate — Azure manages it. It's how my App Service reads Key Vault safely.
- *"How do you secure service-to-service traffic?"* — Private Endpoints + VNet so data never traverses the public internet.

---

## Z9 · Monitoring and DevOps

**Simple explanation.** You can't run what you can't see:
- **Azure Monitor + Application Insights** — collects logs, metrics, traces; I use them to catch slow queries and failures (my production governance on TCW).
- **Azure DevOps / GitHub Actions** — **CI/CD** pipelines that build, test and deploy automatically.

*"On TengizChevroil, Azure DevOps CI/CD halved release-cycle time; on TCW, structured logging + alerts let me triage a slow query before it breaks the deadline."*

**Follow-ups**
- *"What does Application Insights give you?"* — Request timings, dependency calls, exceptions and custom traces — the data to find and fix performance issues fast.
- *"Why CI/CD?"* — Automated, repeatable, low-risk releases — faster delivery with fewer errors.

---

## Z10 · Azure AI Foundry

**Simple explanation.** **Azure AI Foundry** is Microsoft's unified **platform for building, deploying and managing AI applications** — especially generative-AI and LLM apps — in an enterprise-safe way. (It brings together and expands what was Azure AI Studio / parts of Azure OpenAI.)

What it gives an architect:
- A **model catalog** — access many models (Azure OpenAI GPT models, plus open models) in one place.
- **Building blocks for RAG** — connect your data, do retrieval/grounding, and orchestrate prompts.
- **Evaluation & safety** — tools to test quality, and **content safety** filters — essential in regulated firms.
- **Deployment & monitoring** — deploy models as endpoints with security, quotas and observability.

*"This maps exactly to the AI/LLM reference architecture I authored on TCW (Project B) — retrieval, grounding, orchestration and evaluation. Foundry is the managed platform to do that safely; I delivered our first production RAG app on those same principles."*

**Follow-ups**
- *"Foundry vs Azure OpenAI?"* — Azure OpenAI provides the models; AI Foundry is the broader platform to *build, evaluate, secure and operate* full AI apps around those models.
- *"Why does an enterprise use Foundry instead of calling an LLM directly?"* — Governance — security, content safety, evaluation, monitoring and data grounding in one managed place, which is exactly what a regulated firm needs.
- *"How does it help with hallucinations?"* — Through grounding (RAG on your own data) plus evaluation and content-safety tooling — the same discipline as my reference architecture.

---

## Z11 · Containers: ACI, ACA, and AKS

**Simple explanation.** Three ways to run containers: **ACI** (Container Instances) for a single quick container; **ACA** (Container Apps) — serverless containers with autoscaling and scale-to-zero (my default for microservices/APIs); **AKS** (Kubernetes) for full control at large scale. More power = more ops.

**Follow-ups**
- *"ACA vs AKS?"* — ACA is managed and simple (great for most services); AKS when I need full Kubernetes control and complex orchestration.
- *"Where do your FastAPI/.NET services run?"* — Containerised on Container Apps or App Service — both host either language identically.

---

## Z12 · API Management

**Simple explanation.** **Azure API Management (APIM)** is a gateway in front of my APIs. It handles auth, **rate limiting/throttling**, caching, request/response transformation, versioning, and a developer portal — one consistent front door for many backend APIs.

**Follow-ups**
- *"Why put APIM in front?"* — Centralise cross-cutting concerns (auth, throttling, keys) so each backend doesn't reinvent them.
- *"Rate limiting where?"* — At APIM/gateway rather than in every service — consistent protection against abuse and spikes.

---

## Z13 · Front Door, App Gateway, and CDN

**Simple explanation.** Edge/routing services: **Azure Front Door** — global entry point with routing, TLS, WAF and CDN; **Application Gateway** — regional layer-7 load balancer with WAF; **CDN** — caches static content near users. I use Front Door for global apps and a WAF to block common attacks.

**Follow-ups**
- *"Front Door vs App Gateway?"* — Front Door is global (multi-region routing/CDN); App Gateway is regional — often used together.
- *"What's a WAF?"* — Web Application Firewall — blocks common attacks (SQLi, XSS) at the edge before they reach the app.

---

## Z14 · Static Web Apps for the front end

**Simple explanation.** **Azure Static Web Apps** hosts my React/Angular front end globally with built-in CI/CD from GitHub, free SSL, custom domains and integrated (optional) Functions API. Perfect for a SPA where the heavy logic lives in separate APIs.

**Follow-ups**
- *"Where does the React build go?"* — To Static Web Apps (or Blob + CDN) — served fast globally; the app calls my ASP.NET/FastAPI APIs.
- *"Static Web Apps vs App Service for the UI?"* — Static Web Apps is purpose-built and cheaper for a SPA's static bundle + global CDN.

---

## Z15 · Event Grid vs Service Bus vs Event Hubs

**Simple explanation.** Three messaging tools for different jobs: **Service Bus** — enterprise commands/queues (reliable, ordered, dead-letter); **Event Grid** — lightweight reactive event routing ("a blob was created"); **Event Hubs** — high-throughput streaming/telemetry ingestion (millions of events). I pick by pattern: command vs reaction vs stream.

**Follow-ups**
- *"One-line each?"* — Service Bus = do this task; Event Grid = react to this event; Event Hubs = ingest this firehose.
- *"Which for IoT/telemetry?"* — Event Hubs — built for massive streaming ingestion.

---

## Z16 · Azure Cache for Redis

**Simple explanation.** **Azure Cache for Redis** is a managed, in-memory cache shared across app instances. I use it to store hot data, session state, and computed results so I don't hit the database on every request — the shared cache that keeps a scaled-out app consistent (matches file 15/16 caching answers).

**Follow-ups**
- *"Why Redis over in-memory cache?"* — In-memory is per-instance (inconsistent when scaled out); Redis is shared and consistent across all instances.
- *"What do you cache?"* — Slow, read-heavy, slow-changing data with an expiry — never sensitive data without care.

---

## Z17 · Cosmos DB in depth

**Simple explanation.** **Cosmos DB** is Azure's globally-distributed NoSQL database — single-digit-millisecond reads worldwide, elastic scale, multiple APIs (Core/SQL, MongoDB, Cassandra). You choose a **partition key** (critical for scale) and a **consistency level** (strong → eventual) trading latency vs consistency.

**Follow-ups**
- *"When Cosmos over Azure SQL?"* — Global scale, flexible schema, huge throughput with low latency — not for complex relational transactions.
- *"Why does the partition key matter?"* — A bad key creates hot partitions and throttling — pick one that spreads load evenly.

---

## Z18 · Storage accounts in depth

**Simple explanation.** A **Storage Account** holds Blobs, Files, Queues and Tables. Key choices: **redundancy** (LRS local → GRS geo-redundant), **access tiers** (Hot/Cool/Archive), **lifecycle rules** (auto-move old data to cheaper tiers), and secure access (Entra ID/SAS, private endpoints). It's the backbone for files and the data lake.

**Follow-ups**
- *"LRS vs GRS?"* — LRS copies within one datacentre; GRS also replicates to another region for disaster resilience.
- *"How do you cut storage cost?"* — Lifecycle rules move stale blobs to Cool/Archive automatically.

---

## Z19 · The data pipeline on Azure

**Simple explanation (from real TCW work).** My pipeline: raw files land in **Blob/ADLS** → **Data Factory** (plus my **FastAPI** ETL) validates and moves data → **Azure SQL** as the operational store → **Snowflake** for analytics → **Power BI** for dashboards. Secrets in **Key Vault**, identity via **Entra ID/Managed Identity**, monitored by **Azure Monitor**.

**Follow-ups**
- *"Where does orchestration sit?"* — ADF (and Tidal/Airflow) schedule and monitor the movement; my FastAPI does validation/transform.
- *"How is it secured end to end?"* — Managed Identity + Key Vault + private endpoints — no secrets in code, no public traffic.

---

## Z20 · Governance and landing zones

**Simple explanation (architect lens).** For enterprises I use **Management Groups → Subscriptions → Resource Groups** to organise, **Azure Policy** to enforce rules (e.g. "no public storage", "encryption on"), **RBAC** for least-privilege access, and **Landing Zones** — a pre-governed, secure foundation new workloads deploy into.

**Follow-ups**
- *"What is Azure Policy?"* — Rules automatically enforced/audited across resources — governance at scale, not manual checks.
- *"Why a landing zone?"* — New teams inherit security, networking and governance by default — safe and fast onboarding.

---

## Z21 · Infrastructure as Code

**Simple explanation.** I define Azure infrastructure as code with **Bicep** (or Terraform) so environments are repeatable, versioned and reviewed — no clicking in the portal. CI/CD deploys the same templates to dev/test/prod, eliminating drift.

```bicep
resource kv 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: 'tcw-kv'
  location: location
  properties: { sku: { family: 'A', name: 'standard' }, tenantId: tenantId }
}
```

**Follow-ups**
- *"Bicep vs Terraform?"* — Bicep is Azure-native and clean for Azure-only; Terraform for multi-cloud. Both give repeatable infra.
- *"Why IaC?"* — Consistent environments, peer-reviewed changes, instant rebuild — the same discipline as app code.

---

## Z22 · Cost management

**Simple explanation.** I control cloud spend with **Cost Management + budgets/alerts**, right-sizing, autoscaling (scale to zero where possible), reserved instances/savings plans for steady workloads, and tagging resources by team/project for chargeback. Cost is a first-class design constraint.

**Follow-ups**
- *"Biggest cost lever?"* — Right-sizing + autoscale + turning off idle resources — pay for what you use.
- *"Reserved vs pay-as-you-go?"* — Reserved/savings plans for predictable steady load; pay-as-you-go for variable/spiky.

---

## Z23 · The Well-Architected Framework

**Simple explanation.** Microsoft's **Well-Architected Framework** has five pillars I design against: **Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency**. I use it as a checklist to review any architecture for gaps.

**Follow-ups**
- *"Name the pillars."* — Reliability, Security, Cost, Operational Excellence, Performance — balanced trade-offs, not maxing one.
- *"How do you use it?"* — As a structured review of a design (and Azure Advisor automates some checks).

---

## Z24 · Resilience: regions and availability zones

**Simple explanation.** For uptime I design across **Availability Zones** (physically separate datacentres in one region — survives a datacentre failure) and, for critical systems, **multiple regions** (survives a region outage) with a defined **RPO/RTO**. Front Door routes traffic to a healthy region.

**Follow-ups**
- *"AZ vs region redundancy?"* — Zones protect within a region; multi-region protects against a whole-region outage — more cost, more resilience.
- *"How do you fail over regions?"* — Front Door/Traffic Manager routes to the healthy region; data replicated per RPO.

---

## Z25 · Security posture and Defender

**Simple explanation.** Beyond identity and secrets I use **Microsoft Defender for Cloud** (security posture + threat alerts), **Azure Policy** for guardrails, private networking, encryption everywhere, and least-privilege RBAC. Security is layered (defence in depth), not a single control.

**Follow-ups**
- *"What does Defender for Cloud do?"* — Scores my security posture, flags misconfigurations, and alerts on threats across resources.
- *"Defence in depth?"* — Multiple layers (identity, network, app, data) so one failure isn't a breach.

---

## Z26 · Azure OpenAI Service

**Simple explanation.** **Azure OpenAI** provides the GPT/embedding models with enterprise controls — private networking, data privacy (your prompts aren't used to train), content filters, and regional hosting. It's the model layer my RAG apps call; AI Foundry (Z10) is the broader platform around it.

**Follow-ups**
- *"Why Azure OpenAI over public OpenAI?"* — Enterprise data privacy, networking, compliance and SLAs — essential in a regulated firm.
- *"What do you use embeddings for?"* — To turn text into vectors for retrieval in RAG (see Z27).

---

## Z27 · AI Search for RAG

**Simple explanation.** **Azure AI Search** (formerly Cognitive Search) is the **retrieval** engine in my RAG apps — it indexes documents (keyword + **vector** search) so I fetch the most relevant chunks to ground the LLM's answer, cutting hallucinations. It pairs with Azure OpenAI and AI Foundry.

**Follow-ups**
- *"Its role in RAG?"* — The 'R' — retrieve relevant grounded context before the model answers.
- *"Vector vs keyword search?"* — Vector finds meaning-similar text; hybrid (both) usually gives the best retrieval quality.

---

## Z28 · A full-stack app on Azure

**Simple explanation (full-stack lens).** A typical app I build end to end: **React/Angular** front end on **Static Web Apps**, behind **Front Door** (WAF/CDN); **ASP.NET Core Web API** on **App Service/Container Apps** behind **APIM**; **FastAPI** ETL/AI service alongside; **Azure SQL** operational store, **Snowflake** analytics, **Redis** cache; **Service Bus** for async; **Entra ID** auth, **Key Vault** secrets, **App Insights** monitoring, deployed by **CI/CD + Bicep**.

**Follow-ups**
- *"Do you actually wire all this yourself?"* — Yes — I design it and write code across the tiers (front end, both APIs, SQL) — hands-on Solution Architect.
- *"How do the pieces stay secure?"* — Managed Identity + Key Vault + private endpoints + WAF — no secrets in code, minimal public surface.

---

## Z29 · How I choose a compute service

**Simple explanation.** My decision path: **always-on web app/API → App Service or Container Apps**; **short event-driven task → Functions**; **microservices needing autoscale → Container Apps**; **full Kubernetes control at scale → AKS**; **static SPA → Static Web Apps**. Default to the most managed option that fits.

**Follow-ups**
- *"Rule of thumb?"* — Pick the most-managed service that meets the need — less ops, more delivery.
- *"When AKS?"* — Only when I genuinely need Kubernetes' control/scale — otherwise Container Apps is simpler.

---

## Z30 · My reference architecture

**How I answer (the whole picture).** *"I compose Azure from a small set of building blocks: PaaS compute (App Service/Container Apps/Functions), Blob/ADLS for files, Azure SQL for OLTP and Snowflake for analytics, Service Bus/Event Grid for async, Redis for caching, and APIM/Front Door at the edge. Everything is secured with Entra ID, Managed Identity and Key Vault, networked with private endpoints, defined as code in Bicep, shipped via CI/CD, and observed with App Insights. For AI, Azure OpenAI + AI Search + AI Foundry give me governed, grounded RAG. I design this end to end and still write the code across the front end, both APIs and the database — that's what 'hands-on Solution Architect' means."*

**Follow-ups**
- *"How do you keep it from becoming a sprawl of services?"* — A small, repeatable reference set + landing zones + Well-Architected reviews — governance over ad-hoc growth.
- *"Where did you prove this?"* — On TCW (investment reporting + first production RAG app) and TengizChevroil (completion platform on App Service/Functions/Service Bus with CI/CD).

---

## Section index

| # | Service | What it's for |
|---|---|---|
| Z1 | Azure | Microsoft's cloud; IaaS/PaaS/SaaS — I favour PaaS |
| Z2 | Blob Storage | Cheap, scalable storage for unstructured files |
| Z3 | Key Vault | Central, secure store for secrets/keys/certs |
| Z4 | App Service | Managed hosting for web apps/APIs; deployment slots |
| Z5 | Functions | Serverless, event-driven code; pay per run |
| Z6 | Service Bus | Async messaging; decouples & protects services |
| Z7 | Data services | Azure SQL, Cosmos DB, Data Factory, Data Lake |
| Z8 | Identity & networking | Entra ID, Managed Identity, VNet/Private Endpoints |
| Z9 | Monitoring & DevOps | App Insights + CI/CD (Azure DevOps/GitHub Actions) |
| Z10 | Azure AI Foundry | Managed platform to build/evaluate/secure AI & RAG apps |
| Z11 | Containers | ACI/ACA/AKS; Container Apps is my default |
| Z12 | API Management | Gateway: auth, throttling, caching, versioning |
| Z13 | Front Door/CDN | Global routing + WAF + CDN at the edge |
| Z14 | Static Web Apps | Host React/Angular SPA globally with CI/CD |
| Z15 | Event-driven | Service Bus (task) / Event Grid (react) / Event Hubs (stream) |
| Z16 | Redis Cache | Shared in-memory cache for scaled-out apps |
| Z17 | Cosmos DB | Global NoSQL; partition key & consistency matter |
| Z18 | Storage deep | Redundancy, tiers, lifecycle rules, secure access |
| Z19 | Data pipeline | Blob→ADF/FastAPI→Azure SQL→Snowflake→Power BI |
| Z20 | Governance | Mgmt groups, Policy, RBAC, landing zones |
| Z21 | IaC | Bicep/Terraform for repeatable, reviewed infra |
| Z22 | Cost management | Budgets, right-size, autoscale, reservations, tags |
| Z23 | Well-Architected | Reliability/Security/Cost/OpEx/Performance pillars |
| Z24 | Resilience | Availability zones + multi-region to RPO/RTO |
| Z25 | Security posture | Defender for Cloud, defence in depth, least privilege |
| Z26 | Azure OpenAI | Enterprise GPT/embedding models with privacy & filters |
| Z27 | AI Search | Retrieval (vector+keyword) that grounds RAG |
| Z28 | Full-stack on Azure | End-to-end app: SPA + APIs + data + security |
| Z29 | Choosing compute | Pick the most-managed service that fits |
| Z30 | Reference architecture | Small reusable building-block set, secured & coded end to end |

---

[← SQL Server vs Snowflake](36-concept-sqlserver-vs-snowflake.md) · [Home](README.md) · [Next → AI Skills & Workflow](38-concept-ai-skills-workflow.md)
