# 68 · Concept: Azure Services — What's New (Version Evolution) (30 questions)

[← SQL Server What's New](67-concept-sqlserver-whats-new.md) · [Home](README.md) · [Next → React What's New](69-concept-react-whats-new.md)

This file explains **what is new in Azure** — the services and shifts that matter to me as an architect, in simple English, with the *why it matters* and *how it replaces the old way*. Projects B and C run on Azure, so I track new compute, AI, identity and infra-as-code services and choose them deliberately.

> Simple one-liner: *"Azure changes constantly, so I track the *shifts*, not every button: serverless containers (Container Apps), managed AI (Azure OpenAI / AI Foundry), the Entra ID rename, Bicep replacing raw ARM, and always-newer data/AI SKUs. I pick managed-first, and I read the retirement notices as carefully as the launch ones."*

**Jump to (how Azure evolves):** [AW1 How Azure ships](#aw1--how-azure-releases-features) · [AW2 Preview vs GA](#aw2--preview-vs-ga) · [AW3 Regions & AZs](#aw3--regions-and-availability-zones) · [AW4 Retirements](#aw4--service-retirements-matter) · [AW5 Well-Architected](#aw5--the-well-architected-framework)
> **Compute:** [AW6 Container Apps](#aw6--azure-container-apps) · [AW7 AKS updates](#aw7--aks-evolution) · [AW8 Functions Flex](#aw8--azure-functions-flex-consumption) · [AW9 App Service updates](#aw9--app-service-updates)
> **AI:** [AW10 Azure OpenAI](#aw10--azure-openai-service) · [AW11 AI Foundry](#aw11--ai-foundry-and-ai-studio) · [AW12 AI Search](#aw12--ai-search-vector) · [AW13 Prompt flow/agents](#aw13--prompt-flow-and-agents)
> **Identity:** [AW14 Entra rename](#aw14--azure-ad--microsoft-entra-id) · [AW15 Managed identity](#aw15--managed-identities) · [AW16 Workload identity](#aw16--workload-identity-federation)
> **Data:** [AW17 Cosmos DB new](#aw17--cosmos-db-updates) · [AW18 Azure SQL evergreen](#aw18--azure-sql-evergreen) · [AW19 Fabric](#aw19--microsoft-fabric)
> **Infra & DevOps:** [AW20 Bicep](#aw20--bicep-vs-arm) · [AW21 Deployment stacks](#aw21--deployment-stacks) · [AW22 GitHub Actions](#aw22--github-actions-for-azure)
> **Integration & observability:** [AW23 Service Bus/Event Grid](#aw23--messaging-updates) · [AW24 API Management](#aw24--api-management-updates) · [AW25 Monitor/App Insights](#aw25--monitor-and-workspace-based-app-insights)
> **Security & cost:** [AW26 Defender/Key Vault](#aw26--security-updates) · [AW27 Cost tools](#aw27--cost-management-updates)
> **Decisions:** [AW28 Managed vs self-run](#aw28--how-i-choose-a-new-service) · [AW29 Migration/retirement risks](#aw29--migration-and-retirement-risks) · [AW30 My approach](#aw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in Azure" in plain English. Hold these ideas and every question below hangs off one of them.

**1. Azure changes weekly, so I track *shifts*, not buttons.** I don't memorise every SKU. I watch the big movements: serverless containers, managed AI, the identity rename, infra-as-code maturing. Those change how I *design*, which is what an architect cares about.

**2. Everything trends toward "more managed".** The direction of travel is always: less server, more platform. VMs → AKS → Container Apps → Functions. Each step hands more operations to Azure so my team ships features, not patches. Managed-first is my default.

**3. AI became a first-class Azure pillar.** Azure OpenAI, AI Search (vector), and AI Foundry turned "build your own ML platform" into "consume managed AI with enterprise security." On Project B this is exactly the stack I use for RAG.

**4. Preview vs GA is a governance decision.** New features arrive in *preview* (no SLA, may change) then reach *GA* (production-ready). I only put GA services on the critical path; previews go on internal/experimental work.

**5. Names and services get renamed/retired — read the notices.** Azure AD became **Microsoft Entra ID**; services get deprecated with retirement dates. Missing a retirement notice is how production breaks. I treat retirements as first-class planning items.

**6. Infra-as-code matured from ARM to Bicep.** Hand-writing giant ARM JSON is the old way; **Bicep** (clean DSL) and now deployment stacks are the new way. Same underlying engine, far better authoring.

**7. Old way vs new way is the interview gold.** For each area I can say the before/after: raw ARM → Bicep; self-hosted Kubernetes → Container Apps; secrets in config → managed identity + Key Vault; roll-your-own vector store → AI Search.

**8. I choose for fit, cost and support — not hype.** A new service earns its place if it reduces ops, improves security/cost, and is GA with a real SLA on my workload. Newest loses to proven-and-managed on the critical path.

**The full-stack / architect lens:** the later Q&As walk the pillars — compute (Container Apps, AKS, Functions Flex), AI (OpenAI, AI Foundry, AI Search), identity (Entra rename, managed/workload identity), data (Cosmos, evergreen Azure SQL, Fabric), infra/DevOps (Bicep, deployment stacks, GitHub Actions), integration and observability, security and cost — with old-vs-new for each, plus how I choose services and handle retirements. They all trace back to the core: managed-first, GA on the critical path, and watch the retirement calendar.

**One rule I never break:** *managed-first and GA-on-the-critical-path — I only run production on generally-available services and I plan for every retirement date before it arrives.*

---

## AW1 · How Azure releases features

**Simple explanation.** Azure ships continuously — new features land almost weekly, announced at Build/Ignite and via the Azure Updates feed. There's no "version" like SQL Server; services just gain capabilities.

**Architect's view:** I follow the Azure Updates and roadmap feeds, not every blog. I care about changes that alter *design choices* — a new managed service, a retirement, a pricing shift.

**Follow-ups**
- *How do you keep current?* — Azure Updates RSS, Ignite/Build recaps, and the retirements page.
- *Do you chase every new service?* — No — only ones that fit a real need and are GA.

---

## AW2 · Preview vs GA

**Simple explanation.** **Preview** = early access, **no SLA**, may change or be pulled. **GA (General Availability)** = production-ready, backed by an SLA and support.

**Old vs new.** The pattern is constant: features arrive in preview, mature, then GA. What's "new" is often still in preview.

**Architect's view:** GA only on the critical path. I'll trial a preview on internal tools to learn it, but production waits for GA and an SLA.

**Follow-ups**
- *Public vs private preview?* — Private = invite/limited; public = anyone can try.
- *Support during preview?* — Best-effort, not guaranteed.

---

## AW3 · Regions and Availability Zones

**Simple explanation.** Azure keeps adding **regions** and **Availability Zones (AZs)** — physically separate datacentres within a region for resilience. Zone-redundant SKUs of many services are now common.

**Old vs new.** Older designs relied on a single region + geo-replica. Now I get in-region resilience "free" by choosing zone-redundant tiers.

**Architect's view:** for Project C I pick zone-redundant tiers for HA and pair regions for DR — the newer AZ options improve availability without a full second region.

**Follow-ups**
- *Data residency?* — Region choice governs where data lives — important for TCW compliance.
- *Cost of AZ redundancy?* — A premium, but cheaper than a full second region.

---

## AW4 · Service retirements matter

**Simple explanation.** Azure regularly **retires** services/SKUs with a published date (e.g. classic resources, older API versions, some monitoring agents). After the date they stop working.

**Old vs new.** New features get headlines; retirements are the quiet risk. Missing one breaks production.

**Architect's view:** I subscribe to retirement notices and keep a register with dates and migration owners — same discipline as software EOL.

**Follow-ups**
- *A recent example?* — The classic Application Insights (non-workspace) and older Log Analytics agent were retired in favour of workspace-based/Azure Monitor Agent.
- *How much notice?* — Usually ~12+ months; I don't wait until the end.

---

## AW5 · The Well-Architected Framework

**Simple explanation.** The **Azure Well-Architected Framework (WAF)** — five pillars: Reliability, Security, Cost, Operational Excellence, Performance — is Microsoft's evolving guidance for good design and reviews.

**Architect's view:** I run WAF reviews on Projects B/C. "What's new" often maps to a pillar (e.g. a new managed service improves Operational Excellence and Cost at once).

**Follow-ups**
- *How do you use it?* — As a review checklist and a shared vocabulary with stakeholders.
- *Related?* — The Cloud Adoption Framework (CAF) for the broader org journey.

---

## AW6 · Azure Container Apps

**Simple explanation.** **Azure Container Apps (ACA)** is **serverless containers** — run containers with autoscaling (including scale-to-zero) and built-in microservice features (Dapr, revisions, ingress) **without managing Kubernetes**.

**Old vs new.** Before, running containers meant AKS (you manage the cluster) or a single container instance. ACA gives Kubernetes-grade scaling with none of the cluster ops.

**Architect's view:** for most microservices I now reach for ACA over AKS — far less operational burden. I keep AKS for when I need full control or specific K8s ecosystem tools.

**Follow-ups**
- *ACA vs AKS?* — ACA = managed/serverless, less control; AKS = full Kubernetes, more control and ops.
- *Scale to zero?* — Yes — great for spiky or event-driven workloads and cost.

---

## AW7 · AKS evolution

**Simple explanation.** **Azure Kubernetes Service** keeps gaining managed features: automatic upgrades, node auto-provisioning (Karpenter-style), better add-on management, and AKS Automatic (opinionated, production-ready defaults).

**Old vs new.** Managing K8s used to be heavy. AKS increasingly automates upgrades, scaling and security config.

**Architect's view:** if I'm on AKS I lean into the managed add-ons and auto-upgrade to cut toil — but for greenfield microservices I still start with ACA.

**Follow-ups**
- *AKS Automatic?* — A mode with best-practice defaults so teams don't hand-tune everything.
- *Why still choose AKS?* — Ecosystem tooling, custom networking, portability.

---

## AW8 · Azure Functions Flex Consumption

**Simple explanation.** **Flex Consumption** is a newer Functions plan: serverless scale with **fast, controllable scaling**, per-instance concurrency, VNet integration, and no cold-start pain of the old Consumption plan.

**Old vs new.** The classic Consumption plan had cold starts and limited networking. Flex fixes both while staying pay-per-use.

**Architect's view:** for event-driven glue (queue processors, webhooks) Flex Consumption gives serverless economics without the cold-start tax.

**Follow-ups**
- *Premium plan still needed?* — Less often — Flex covers many former Premium reasons (VNet, warm instances).
- *Language support?* — The isolated worker model (works cleanly with modern .NET).

---

## AW9 · App Service updates

**Simple explanation.** **App Service** keeps modernising: better Linux/container support, sidecar containers, native support for the latest .NET/Node, and improved autoscaling.

**Old vs new.** App Service remains the simplest PaaS for web apps; newer container/sidecar support blurs the line with ACA for simple cases.

**Architect's view:** for a straightforward web app or API, App Service is still the lowest-effort choice; for many small services, ACA wins.

**Follow-ups**
- *App Service vs Container Apps?* — App Service = simplest single web app; ACA = many scaling microservices.
- *Sidecars?* — Add a companion container (e.g. for a local model or proxy).

---

## AW10 · Azure OpenAI Service

**Simple explanation.** **Azure OpenAI** provides OpenAI models (GPT-4/4o, embeddings, etc.) with **enterprise security, networking, and data-residency** — my data isn't used to train the models.

**Old vs new.** Before, using powerful LLMs meant public APIs with data-handling worries. Azure OpenAI brings them inside my Azure boundary with RBAC, VNet and compliance.

**Architect's view:** on Project B this is the LLM backbone — I get the models plus the governance a regulated firm needs.

**Follow-ups**
- *Data privacy?* — Prompts/outputs aren't used to train models; stays in my tenant/region.
- *Provisioned throughput?* — PTUs give reserved capacity for predictable latency/cost.

---

## AW11 · AI Foundry and AI Studio

**Simple explanation.** **Azure AI Foundry** (formerly Azure AI Studio) is the unified place to build, evaluate and deploy AI apps — model catalog, prompt orchestration, evaluation, and an **Agent Service**.

**Old vs new.** Before, AI pieces (models, search, eval, deployment) were separate. Foundry brings them under one roof.

**Architect's view:** it standardises how the team builds and *evaluates* AI apps — evaluation and safety tooling matter as much as the model.

**Follow-ups**
- *Model catalog?* — Choose from OpenAI, Meta, Mistral, etc. — not locked to one vendor.
- *Why evaluation tools?* — To measure quality/groundedness before shipping RAG.

---

## AW12 · AI Search (vector)

**Simple explanation.** **Azure AI Search** (formerly Cognitive Search) added **vector search** and **hybrid (keyword + vector)** retrieval — the retrieval engine for RAG.

**Old vs new.** It used to be keyword/full-text only. Now it stores embeddings and does semantic + hybrid search, so I don't need a separate vector DB for many cases.

**Architect's view:** on Project B, AI Search is the managed vector store for RAG — hybrid search plus semantic ranking beats pure vector for enterprise docs.

**Follow-ups**
- *vs a dedicated vector DB (Chroma/Pinecone)?* — AI Search is managed and does hybrid + security trimming; I choose it for enterprise RAG.
- *Security trimming?* — Filter results by the user's permissions.

---

## AW13 · Prompt flow and agents

**Simple explanation.** **Prompt flow** (in Foundry) is a visual/code way to build and evaluate LLM pipelines; the **Agent Service** runs tool-using agents as a managed service.

**Old vs new.** Before, I wired orchestration (LangChain-style) and agent loops myself. Azure now offers managed orchestration and agent hosting.

**Architect's view:** I weigh managed agents vs my own LangGraph orchestration — managed for speed and governance, custom for control.

**Follow-ups**
- *Does this replace LangChain?* — It's an alternative; I choose per project's control/governance needs.
- *Evaluation built in?* — Yes — groundedness/relevance metrics on flows.

---

## AW14 · Azure AD → Microsoft Entra ID

**Simple explanation.** **Azure Active Directory was renamed to Microsoft Entra ID** (2023). Same service, new name; Entra is now the broader identity family (Entra ID, Entra Permissions Management, Entra Verified ID, Entra Internet Access).

**Old vs new.** Only the branding changed for the core directory — but interview-relevant, and "Entra" now spans more identity products.

**Architect's view:** I use Entra ID for app auth (OIDC/OAuth), RBAC, Conditional Access and managed identities — the identity backbone for Projects B/C.

**Follow-ups**
- *Do app registrations change?* — No — same concepts, new portal name.
- *What's Conditional Access?* — Policy-based access (device/location/risk) — core to zero-trust.

---

## AW15 · Managed identities

**Simple explanation.** **Managed identities** give an Azure resource an Entra identity so it can call other Azure services (Key Vault, SQL, Storage) **without any secret** in config.

```csharp
// New: no connection secret — DefaultAzureCredential uses the managed identity
var client = new SecretClient(new Uri(vaultUri), new DefaultAzureCredential());
```

**Old vs new.** Before, apps stored connection strings/keys in config — a leak risk. Managed identity removes secrets entirely.

**Architect's view:** my default — no secrets in app config; Key Vault for what's left, accessed via managed identity. Huge security win.

**Follow-ups**
- *System vs user-assigned?* — System = tied to one resource's lifecycle; user-assigned = shared across resources.
- *SQL with managed identity?* — Azure SQL supports Entra token auth — no password.

---

## AW16 · Workload identity federation

**Simple explanation.** **Workload identity federation** lets external workloads (GitHub Actions, other clouds, Kubernetes) get Azure tokens **without storing a secret**, by trusting their identity provider.

**Old vs new.** Before, my CI stored an Azure service-principal secret (rotation pain, leak risk). Federation removes the secret — GitHub gets a short-lived token.

**Architect's view:** I use OIDC federation for GitHub Actions → Azure deployments — no long-lived credentials in the pipeline.

**Follow-ups**
- *Why better than a secret?* — No secret to leak or rotate; tokens are short-lived.
- *Works for AKS?* — Yes — pods get federated identities.

---

## AW17 · Cosmos DB updates

**Simple explanation.** **Cosmos DB** keeps evolving: **vector search** (for AI), **serverless** and **autoscale** throughput, better analytical store (Synapse Link), and burst capacity.

**Old vs new.** Before, Cosmos was provisioned-RU only (over-provision or throttle). Serverless/autoscale match cost to load, and vector search adds AI use cases.

**Architect's view:** for globally-distributed, low-latency documents Cosmos is my pick; autoscale controls cost, and native vector search simplifies some AI designs.

**Follow-ups**
- *Consistency levels?* — Five levels (strong → eventual); I tune per use case.
- *Vector search in Cosmos vs AI Search?* — Cosmos if data already lives there; AI Search for document RAG with hybrid.

---

## AW18 · Azure SQL evergreen

**Simple explanation.** **Azure SQL Database / Managed Instance** are **evergreen** — always the latest engine, patched and HA-managed by Azure, with **serverless** auto-pause/scale options.

**Old vs new.** No version upgrades like the boxed product — features (IQP, PSP, ADR) arrive continuously and first.

**Architect's view:** for new relational workloads I default to Managed Instance (compatibility + managed ops) or serverless SQL DB (spiky/dev cost).

**Follow-ups**
- *Serverless benefit?* — Auto-pause when idle = pay near-zero for dev/test.
- *Hyperscale?* — A tier for very large DBs with fast backups/scaling.

---

## AW19 · Microsoft Fabric

**Simple explanation.** **Microsoft Fabric** is a unified analytics platform — data engineering, warehouse, real-time, and Power BI — over a single storage layer (**OneLake**), replacing a stitched-together stack.

**Old vs new.** Before, analytics meant assembling Synapse + Data Factory + Power BI + storage. Fabric unifies them with one lake and SaaS billing.

**Architect's view:** I evaluate Fabric against my current Snowflake/ADF setup (Project A) — Fabric's appeal is unification and Power BI integration; the decision is workload and cost.

**Follow-ups**
- *OneLake?* — One logical data lake for the whole org (Delta/Parquet).
- *Replaces Synapse?* — Fabric is the successor direction for many Synapse scenarios.

---

## AW20 · Bicep vs ARM

**Simple explanation.** **Bicep** is a clean domain-specific language that compiles to ARM JSON — same deployments, far more readable authoring.

**Old vs new.**

```bicep
// NEW (Bicep): readable
resource sa 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: storageName
  location: location
  sku: { name: 'Standard_LRS' }
  kind: 'StorageV2'
}
```
```json
// OLD (ARM JSON): verbose, brackets everywhere — same result, harder to write
```

**Architect's view:** all new infra-as-code is Bicep (or Terraform where multi-cloud). Raw ARM JSON is legacy.

**Follow-ups**
- *Bicep vs Terraform?* — Bicep = Azure-native, day-one feature support; Terraform = multi-cloud, mature state model.
- *Do I need to learn ARM?* — Enough to debug; author in Bicep.

---

## AW21 · Deployment stacks

**Simple explanation.** **Deployment stacks** manage a group of resources as a single unit with a lifecycle — including **deny settings** (lock resources) and clean **deletion** of everything in the stack.

**Old vs new.** Before, cleaning up all resources for an app was manual/error-prone. Stacks give managed lifecycle and guardrails.

**Architect's view:** good for environment lifecycle (spin up/tear down a whole app's resources reliably) and preventing drift via deny settings.

**Follow-ups**
- *vs resource groups?* — Stacks add lifecycle/deny controls on top of a set of resources.
- *Drift protection?* — Deny settings stop out-of-band changes.

---

## AW22 · GitHub Actions for Azure

**Simple explanation.** Deploying to Azure from **GitHub Actions** (with OIDC federation) is the modern CI/CD path — no stored secrets, first-class Azure login/deploy actions.

**Old vs new.** Before, Azure DevOps pipelines with stored service-principal secrets. Now GitHub Actions + workload identity federation = secretless deploys.

**Architect's view:** I standardise on GitHub Actions + OIDC + Bicep for Azure deployments — secretless, reviewable, repeatable.

**Follow-ups**
- *Azure DevOps dead?* — No — still supported and used; GitHub is the strategic direction.
- *Environments/approvals?* — GitHub Environments give gated deploys.

---

## AW23 · Messaging updates

**Simple explanation.** **Service Bus** (enterprise queues/topics), **Event Grid** (event routing, now with MQTT/pub-sub), and **Event Hubs** (streaming) keep gaining features — Event Grid namespaces added MQTT and pull delivery.

**Old vs new.** Event Grid grew from simple event routing to a fuller pub/sub and IoT messaging broker.

**Architect's view:** I pick by pattern — Service Bus for reliable commands/ordering, Event Grid for reactive events, Event Hubs for high-volume streams (like the Kafka role).

**Follow-ups**
- *Event Grid vs Service Bus?* — Grid = lightweight event notifications; Bus = reliable, ordered, transactional messaging.
- *Event Hubs vs Kafka?* — Event Hubs has a Kafka-compatible endpoint.

---

## AW24 · API Management updates

**Simple explanation.** **API Management (APIM)** added consumption/serverless and **Standard v2** tiers (faster provisioning, VNet), plus an **AI Gateway** for governing LLM calls (token limits, semantic caching).

**Old vs new.** APIM used to be a heavier deploy; v2 tiers are faster/cheaper, and the AI Gateway is brand-new for controlling LLM usage.

**Architect's view:** I front public APIs with APIM for auth, throttling and versioning; the AI Gateway is compelling for governing Azure OpenAI spend and caching.

**Follow-ups**
- *AI Gateway features?* — Token rate limits, semantic caching, load-balancing across OpenAI deployments.
- *Why front APIs with APIM?* — Central policy, keys, throttling, analytics.

---

## AW25 · Monitor and workspace-based App Insights

**Simple explanation.** **Application Insights** moved to **workspace-based** (data in Log Analytics), the **Azure Monitor Agent** replaced legacy agents, and OpenTelemetry is the recommended instrumentation.

**Old vs new.** Classic (non-workspace) App Insights and the old Log Analytics agent are **retired** — I must be on workspace-based + AMA.

**Architect's view:** I instrument with OpenTelemetry into workspace-based App Insights — one query surface (KQL) for logs, metrics and traces across services.

**Follow-ups**
- *Why OpenTelemetry?* — Vendor-neutral instrumentation; portable if I change backends.
- *KQL?* — The query language for Log Analytics — powerful for cross-service diagnosis.

---

## AW26 · Security updates

**Simple explanation.** **Microsoft Defender for Cloud** (CSPM + workload protection), **Key Vault** (secrets/keys/certs, with managed HSM), and **Entra Conditional Access** keep evolving toward zero-trust and posture management.

**Old vs new.** Security moved from point tools to an integrated posture-management + threat-protection platform.

**Architect's view:** baseline for Projects B/C — Defender for posture/alerts, Key Vault for secrets, managed identity so there are few secrets to hold, Conditional Access for access policy.

**Follow-ups**
- *CSPM?* — Cloud Security Posture Management — finds misconfigurations continuously.
- *Key Vault vs App Configuration?* — Vault for secrets/keys; App Config for feature flags/settings.

---

## AW27 · Cost Management updates

**Simple explanation.** **Microsoft Cost Management** keeps adding budgets, anomaly alerts, and recommendations (via Advisor), plus **savings plans** and reservations for compute discounts.

**Old vs new.** Cost visibility improved from raw bills to budgets, anomaly detection and rightsizing advice.

**Architect's view:** I set budgets + anomaly alerts per environment and use savings plans/reservations for steady workloads — cost is a WAF pillar I review continuously.

**Follow-ups**
- *Reservation vs savings plan?* — Reservation = specific SKU commitment; savings plan = flexible compute commitment.
- *Scale-to-zero services?* — ACA/Functions Flex/serverless SQL cut idle cost.

---

## AW28 · How I choose a new service

**Simple explanation.** My filter: is it **GA** with an SLA? Does it **reduce operations** or **improve security/cost** for my workload? Does it fit the **Well-Architected** pillars? Is there **exit/portability** if I need it?

**Architect's view:** managed-first, GA-on-the-critical-path. I trial previews on the side, standardise on proven services, and avoid lock-in where it's cheap to do so.

**Follow-ups**
- *Lock-in worry?* — I accept managed lock-in when the ops savings are big and exit is feasible; I avoid it for core data portability.
- *First question you ask?* — "What operational burden does this remove, and is it GA?"

---

## AW29 · Migration and retirement risks

**Simple explanation.** Risks: **service retirements** (dated), **API version deprecations**, **preview features changing**, **region/SKU availability**, and **cost surprises** from new tiers. Each needs a plan and an owner.

**Architect's view:** I keep a retirement register with dates, run cost reviews before adopting new SKUs, and never build critical paths on preview features. I test migrations in a non-prod subscription first.

**Follow-ups**
- *Biggest real risk?* — Ignoring a retirement notice until it's live.
- *Cost surprise example?* — A new tier priced differently — I model it before switching.

---

## AW30 · My approach

**Simple explanation.** I track Azure's **shifts** (managed compute, managed AI, identity rename, Bicep, evergreen data), choose **managed-first** and **GA-on-the-critical-path**, secure everything with **managed identity + Key Vault + Entra**, deploy via **Bicep + GitHub Actions (OIDC)**, and watch the **retirement calendar** as closely as the launch feed.

**Architect's view:** Azure's direction is always "more managed, more secure, more AI-native." On Projects B/C I ride that direction to cut ops and improve security, while governing adoption through Well-Architected reviews, GA gates, and a retirement register. New service, same discipline: fit, cost, support, exit.

**Follow-ups**
- *One-sentence philosophy?* — "Managed-first, GA on the critical path, and never miss a retirement date."
- *How do you keep the team aligned?* — Short "what's new and where we'll use it" notes plus WAF reviews.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| AW1 | How Azure ships | Continuous; track design-changing shifts |
| AW2 | Preview vs GA | GA only on the critical path |
| AW3 | Regions & AZs | Zone-redundant tiers for in-region HA |
| AW4 | Retirements | Dated; keep a register with owners |
| AW5 | Well-Architected | Five pillars as review checklist |
| AW6 | Container Apps | Serverless containers, no K8s ops |
| AW7 | AKS evolution | More managed (auto-upgrade, AKS Automatic) |
| AW8 | Functions Flex | Serverless without cold-start pain |
| AW9 | App Service | Simplest PaaS; sidecars/containers added |
| AW10 | Azure OpenAI | Enterprise-governed LLMs in my tenant |
| AW11 | AI Foundry | Unified build/evaluate/deploy AI + agents |
| AW12 | AI Search vector | Managed hybrid (keyword+vector) RAG store |
| AW13 | Prompt flow/agents | Managed orchestration/agents vs custom |
| AW14 | Entra ID | Azure AD renamed; broader identity family |
| AW15 | Managed identity | No secrets — resource-to-service auth |
| AW16 | Workload identity | Secretless CI/external workload auth (OIDC) |
| AW17 | Cosmos DB | Serverless/autoscale + vector search |
| AW18 | Azure SQL evergreen | Always-current, serverless, managed HA |
| AW19 | Microsoft Fabric | Unified analytics over OneLake |
| AW20 | Bicep | Clean IaC replacing raw ARM JSON |
| AW21 | Deployment stacks | Group lifecycle + deny settings |
| AW22 | GitHub Actions | Secretless Azure deploys via OIDC |
| AW23 | Messaging | Service Bus / Event Grid / Event Hubs by pattern |
| AW24 | API Management | v2 tiers + AI Gateway for LLM governance |
| AW25 | Monitor/App Insights | Workspace-based + AMA + OpenTelemetry |
| AW26 | Security | Defender + Key Vault + Conditional Access |
| AW27 | Cost Management | Budgets, anomalies, savings plans |
| AW28 | Choosing services | GA, managed, WAF-fit, exit strategy |
| AW29 | Migration/retirement | Register dates; no critical path on preview |
| AW30 | My approach | Managed-first, GA critical path, watch retirements |

---

[← SQL Server What's New](67-concept-sqlserver-whats-new.md) · [Home](README.md) · [Next → React What's New](69-concept-react-whats-new.md)
