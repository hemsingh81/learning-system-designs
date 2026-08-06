# 03 · System Design (8 scenarios)

[← Technical Q&A](02-technical-qa.md) · [Home](README.md) · [Next → Team Management](04-team-management.md)

Every scenario below follows the same shape, which is also how I answer live:

> **1. Clarify** (2 questions max) → **2. Name the qualities** that drive the design → **3. Draw the boxes** → **4. Walk the data** → **5. Name the alternative I rejected** → **6. Name my own design's weakness**

Interviewers score steps 5 and 6 highest. Most candidates never get there.

**Jump to:**
[D1 Investment reporting](#d1--design-a-daily-investment-reporting-platform-with-a-hard-deadline) ·
[D2 Third-party ingestion](#d2--design-the-ingestion-and-orchestration-for-a-third-party-data-source) ·
[D3 Workflow microservices](#d3--design-a-workflow-platform-for-a-large-construction-programme) ·
[D4 RAG assistant](#d4--design-a-retrieval-augmented-assistant-for-a-regulated-firm) ·
[D5 Multi-tenant API](#d5--design-a-multi-tenant-reporting-api-that-must-scale) ·
[D6 Event-driven notifications](#d6--design-a-near-real-time-notification-and-event-platform) ·
[D7 Legacy modernisation](#d7--modernise-a-legacy-on-premises-monolith-onto-azure) ·
[D8 HA & DR on a budget](#d8--design-high-availability-and-disaster-recovery-on-a-fixed-budget)

---

## D1 · Design a daily investment reporting platform with a hard deadline

> *"Portfolio managers need Emerging Markets and Equity reports before the US market opens. Source data comes from a third-party investment platform. Design it."*

This is my day job at TCW, so I answer it from the real system.

### Step 1 — Clarify

I ask exactly two questions:

1. **"What is the deadline and what happens if we miss it?"** — This tells me whether I am designing for latency or for schedule reliability. Here the answer is a fixed pre-market window, and missing it means portfolio managers trade without their reports. Schedule reliability wins.
2. **"Is stale-but-labelled acceptable, or is missing better than stale?"** — This is the single most important design input, and almost nobody asks it. The answer here: stale is acceptable **if it is clearly marked**. That unlocks a fallback strategy.

### Step 2 — Qualities that drive the design

| Quality | Target | Why it shapes the design |
|---|---|---|
| **Schedule reliability** | Reports ready inside the pre-market window, every trading day | Drives the dependency-aware orchestration and the deadline alerting |
| **Correctness** | Every published number reconciles to the source | Drives the validation gate and reconciliation checks |
| **Read latency** | Report opens in about a second | Drives the read-model separation and server-side paging |
| **Recoverability** | Any run re-runnable without double counting | Drives idempotency, watermarks and checkpoints |
| **Auditability** | Prove what was published, from what data, when | Drives run ids and append-only audit |

Note what is *not* on this list: massive concurrent user scale. A few hundred professional users, not a million. Saying that out loud shows judgement.

### Step 3 — The architecture

![Investment reporting platform: React front end and ASP.NET Core Web API reading a curated store, fed by FastAPI ETL services that pull the third-party investment platform, validated in staging, landed into SQL Server and Snowflake, and orchestrated by a dependency-aware layer over Azure Data Factory, Tidal and Airflow](assets/investment-reporting-architecture.svg)

*Figure 3.1 — The reporting platform. The user-facing read path never touches the third party.*

### Step 4 — Walk the data

1. **Pull.** FastAPI ETL services call the third-party API on a schedule, from a watermark, with retry, backoff and a circuit breaker. Bounded concurrency so we respect rate limits.
2. **Land in staging.** Raw data lands tagged with a run id. Nothing downstream can see it yet.
3. **Validate.** Contract checks, business rules, control totals against the source. Failures quarantine and alert — they do not proceed.
4. **Promote.** `MERGE` on the natural key into SQL Server (operational) and Snowflake (analytical). Idempotent, so a re-run is safe.
5. **Reconcile.** Compare our totals to the source's totals. A break alerts with the specific portfolio and field.
6. **Publish signal.** The feed publishes "complete" with row counts. Downstream steps wait on this signal, not on a clock.
7. **Serve.** The ASP.NET Core Web API reads only our curated store. React renders with server-side paging.

### Step 5 — The alternative I rejected

**Call the third-party API live from the reporting API, with a cache.** It looks simpler — no pipeline, no staging, fewer moving parts.

I rejected it for three reasons. It puts someone else's uptime directly in my user-facing path. It gives me no place to validate or reconcile before a number reaches a portfolio manager. And it makes the deadline unmanageable — I cannot pre-compute at 4 a.m. what I only fetch at 9 a.m. The pipeline is more machinery, and it buys the two things the business actually needs: a deadline I can manage and numbers I can prove.

### Step 6 — My design's weakness, and how I watch it

The weakness is **the orchestration layer is now a critical dependency of its own**. If the signal layer breaks, the chain stalls even when the data is fine.

So: every step fails safe — a missing signal means "wait and alert", never "assume success". The orchestration itself is monitored with a heartbeat. And the deadline alert is independent of the orchestration, so if the orchestrator dies silently, the deadline monitor still pages someone.

### Scaling story

More portfolios → widen the parallelism inside the bounded pool, and partition by feed. More history → that is Snowflake's problem, not SQL Server's, which is exactly why they are split. More users → the API is stateless, so scale out; the read model is already pre-computed.

---

## D2 · Design the ingestion and orchestration for a third-party data source

> *"You depend on an external system's API for critical daily data. Design the ingestion, and tell me how you keep it on schedule."*

### Step 1 — Clarify

1. **"What is the source's rate limit and typical availability window?"**
2. **"Can the source send corrections for past dates?"** — If yes, the design must handle restatement, not just append. In finance the answer is always yes.

### Step 2 — Qualities

Idempotency, checkpointing, deadline awareness, and restatement support. Throughput matters less than being restartable.

### Step 3 — The sequence

![Sequence: the orchestrator triggers the ETL service, which reads its watermark, pulls pages from the third-party API with retry and circuit breaker, writes to staging, runs validation, merges into SQL Server and Snowflake, reconciles, advances the watermark and publishes a completion signal; failures quarantine and alert with remaining slack against the deadline](assets/aladdin-ingestion-sequence.svg)

*Figure 3.2 — One ingestion run, end to end. Note the watermark only advances after a successful promote.*

### Step 4 — The four rules I build every ingestion on

| Rule | What it means in code | What it buys me |
|---|---|---|
| **Watermark** | Store the last processed point; advance only after commit | Restart from the failure, not from zero |
| **Merge, never insert** | Upsert on the natural key | Re-runs are safe; corrections just work |
| **Validate before promote** | Staging → checks → curated | Bad data cannot reach a user |
| **Signal, do not schedule** | Downstream waits on a completion event | The chain survives a late upstream |

That fourth rule is the one that separates a working pipeline from a fragile one. "Airflow runs at 04:15 and hopes ADF finished" fails silently the first day ADF runs ten minutes late.

### Step 5 — The alternative I rejected

**Streaming / change-data-capture instead of a scheduled pull.** Attractive — lower latency, more elegant. Rejected because the source exposes a request/response API, not a change stream, and because the business need is a daily reporting cycle, not sub-second freshness. Building streaming infrastructure for a daily deadline is complexity with no buyer.

### Step 6 — Weakness

**Restatements are the hard case.** When the source corrects a figure for last month, a naive merge silently changes a number someone has already reported on. So corrections are detected, versioned and logged with an audit entry — "this value changed on this date because the source restated it". In regulated reporting, an unexplained changed number is a bigger problem than a wrong one.

### If they push on scale

Partition by feed and by portfolio range, run partitions in parallel inside a bounded pool, and keep per-partition watermarks. That gives horizontal scale without losing restartability.

---

## D3 · Design a workflow platform for a large construction programme

> *"Thousands of pieces of equipment must be built, tested, certified and handed over. It runs on paper and spreadsheets across many contractors. Design the system."*

This is TengizChevroil.

### Step 1 — Clarify

1. **"Who signs, and is the signature legally meaningful?"** — Here yes; a commissioning certificate is a legal artefact. That makes the audit trail a first-class requirement, not a nice-to-have.
2. **"Do all users have reliable connectivity?"** — On an industrial site, partially. That shapes how much I depend on live calls.

### Step 2 — Qualities

Auditability (append-only history), workflow correctness, **usability by non-office staff**, independent release per business capability, and integration with existing construction systems.

I always name usability out loud here. In heavy industry the architecture risk is adoption. A perfect design that a commissioning engineer will not use is a failed project.

### Step 3 — The decomposition

![Four services split by business capability — commissioning certificates, contract transfer, exception handling, change notice — each an ASP.NET Core app on Azure App Services with its own schema in Azure SQL, sharing Azure Functions for document generation and notifications, Blob Storage and SharePoint Online for documents, Azure Data Factory for ETL, and Power BI for phase dashboards](assets/completion-platform-microservices.svg)

*Figure 3.3 — Split by business capability and release rhythm, not by technical layer.*

### Step 4 — Key decisions

**Split by capability, not by layer.** Four services because they have four different owners, four approval chains and four release rhythms. I explain the test I use: *if two services always change together, they are one service.*

**Schema per service, no cross-service reads.** Enforced by database permissions, not by a code-review convention. If the permission model allows it, someone eventually does it.

**Outbox for cross-service consistency.** State change and outgoing message committed in the same local transaction; an Azure Function delivers it with retry and a dead-letter path. I accepted eventual consistency plus a visible reconciliation report over a distributed transaction, because I can explain the former to an auditor.

**Documents in Blob Storage and SharePoint Online, not in the database.** Certificates are files, some of them large. The database holds metadata and the approval chain.

**Power BI on top of a modelled reporting schema**, covering Workdown, Mechanical Completion, RFO and Commissioning — so leadership sees real-time completion instead of a weekly spreadsheet.

### Step 5 — The alternative I rejected

**One application with four modules.** Genuinely simpler to build and operate, and I considered it seriously. I rejected it because a change-notice tweak would have forced regression testing of the certificate workflow, and in a live construction programme a blocked release blocks crews. The deployment independence was worth the network hops.

I say the counterfactual too: *if all four had shared one owner and one release train, I would have built the monolith.*

### Step 6 — Weakness

Four services means four pipelines, four sets of alerts, and a distributed failure mode. I mitigated with a shared pipeline template, a common logging and correlation-id standard, and one operational dashboard across all four — so the on-site team looks at one screen, not four.

### Outcome

Manual effort **−60%**, processing errors **−25%**, release cycle **halved**.

---

## D4 · Design a retrieval-augmented assistant for a regulated firm

> *"Support engineers waste time searching old emails and runbooks. Build them an assistant. It is a regulated firm."*

### Step 1 — Clarify

1. **"Can a wrong answer cause harm, and is there a human in the loop?"** — This sets how hard I clamp grounding and refusal.
2. **"Does every user have the same access to the source documents?"** — Almost always no. This is the question that decides whether the design is safe or leaky.

### Step 2 — Qualities

Groundedness above fluency. Per-user permission at retrieval. Traceability of every answer. Measurable quality over time. Bounded cost.

### Step 3 — The architecture

![RAG architecture: documents from support mail, Confluence runbooks and past threads are chunked, embedded and stored with permission metadata in a vector store; at query time the question is embedded, hybrid retrieval is filtered by the caller's entitlements, a LangGraph flow retrieves, optionally rewrites and re-retrieves, generates a grounded cited answer, and every run is traced and scored for groundedness, relevance and correctness](assets/rag-architecture.svg)

*Figure 3.4 — The four named parts: retrieval, grounding, orchestration, evaluation.*

### Step 4 — The four parts, and why each exists

**Retrieval.** Chunk with respect to document structure — a runbook step split in half retrieves badly. Embed, store with metadata: source, date, and **the permissions of the source document**. Hybrid search — keyword plus vector — because pure semantic search is weak on exact identifiers, and enterprise content is full of them.

**Grounding.** Answer only from retrieved context. Cite the source. If retrieval is weak, say "I do not know" and point at the human escalation path. I treat a confident answer with no citation as a defect.

**Orchestration.** A real support question is a small state machine, not one model call: classify → retrieve → check sufficiency → maybe rewrite and retrieve again → generate → verify. LangGraph models that honestly.

**Evaluation.** A fixed gold set of real questions with known answers and known source documents. Every change is scored on groundedness, relevance and correctness, and a regression blocks the release. This is the part teams skip and it is the reason their assistant quietly rots.

### Step 5 — The alternative I rejected

**Fine-tune a model on the support corpus.** Rejected on three counts: the knowledge changes weekly, so I would be retraining constantly; a fine-tuned model cannot cite its source, and in a regulated firm citation is the whole point; and fine-tuning bakes in content with no per-user permission, so one model would happily tell any user what is in a restricted document.

### Step 6 — Weakness

**Retrieval quality is the ceiling on everything.** If the right runbook is not retrieved, no prompt engineering rescues the answer. So I measure retrieval recall *separately* from answer quality, and when quality drops I know immediately which half to fix. I also watch for corpus drift — new runbooks arriving in a format the chunker handles badly.

### Cost control

Cache embeddings — re-embedding unchanged documents is pure waste. Small cheap model for classification and routing, stronger model only for the final answer. Token spend tracked per feature with a budget alert.

---

## D5 · Design a multi-tenant reporting API that must scale

> *"Same reporting product, many client firms. One tenant must never see another's data, and one heavy tenant must not slow everyone down."*

### Step 1 — Clarify

1. **"How many tenants, and how uneven are they?"** — Tens of similar tenants is a very different design from three tenants where one is 80% of the load.
2. **"Do any tenants have data-residency or single-tenant contractual requirements?"** — In asset management, some always do.

### Step 2 — Qualities

Isolation (the hard one), predictable performance under a noisy neighbour, per-tenant cost visibility, and the ability to onboard a tenant without a code change.

### Step 3 — The design

**Tenant identity comes from the token, never from a request parameter.** The tenant id is a claim, resolved server-side into a tenant context at the start of the request. If the tenant can be chosen by the caller, you have built a data-breach feature.

**Data isolation: schema or database per tenant, not a shared table with a `TenantId` column** — for regulated financial clients. A shared table means one missing `WHERE TenantId = @x` is a cross-client data leak, and that is a business-ending event in asset management. A separate schema makes the isolation structural.

```csharp
// Tenant context resolved once, from the token, and enforced in the data layer.
public sealed class TenantContext
{
    public string TenantId { get; }
    public TenantContext(IHttpContextAccessor http)
    {
        TenantId = http.HttpContext?.User.FindFirst("tid")?.Value
                   ?? throw new UnauthorizedAccessException("No tenant claim on the token.");
    }
}

// The connection is chosen by the resolved tenant — callers cannot influence it.
public sealed class TenantConnectionFactory(TenantContext tenant, IOptions<TenantMap> map)
{
    public SqlConnection Create() => new(map.Value.ConnectionStringFor(tenant.TenantId));
}
```

**Noisy neighbour control: quotas and bulkheads.** Per-tenant rate limits at the gateway, and a bounded concurrency pool per tenant inside the service so one tenant's heavy export cannot consume every worker thread. Heavy exports are asynchronous and queued per tenant.

**Onboarding is data, not code.** A new tenant is a row in the tenant map plus a provisioned schema from the same IaC template. If onboarding needs a deployment, the design has failed.

### Step 4 — The alternative I rejected

**Shared tables with a tenant discriminator column.** Cheapest to run and easiest to operate. I have used it for non-sensitive workloads. I reject it here purely on blast radius: the failure mode is a cross-tenant leak of financial data caused by one forgotten predicate. For this client type, structural isolation is worth the extra cost.

### Step 5 — Weakness

**Schema-per-tenant makes schema change expensive** — a migration must run everywhere, and one failed tenant migration leaves the estate inconsistent. So migrations are versioned, run through the pipeline per tenant with per-tenant status tracking, and the application supports N and N−1 schema versions during rollout (expand-and-contract).

---

## D6 · Design a near-real-time notification and event platform

> *"When something meaningful happens — an approval, a data break, a threshold crossed — the right people must know within seconds, on the right channel, without being spammed."*

### Step 1 — Clarify

1. **"Is delivery guaranteed, or best-effort?"** — "The certificate was approved" is guaranteed. "CPU is high" is best-effort. They are different systems.
2. **"Who decides who gets notified — the publisher or the subscriber?"** — Subscriber-controlled preferences, always. Publisher-controlled routing is how you build spam.

### Step 2 — Qualities

At-least-once delivery for business events, ordering only where it matters, deduplication, subscriber preferences, and a hard rule against alert fatigue.

### Step 3 — The design

**Publish events, not notifications.** Services publish domain facts — `CertificateApproved`, `DataBreakDetected`, `FeedCompleted` — to a topic. They do not know or care who is listening. This is the decision that keeps the system extensible: adding a new consumer never touches the publisher.

**Azure Service Bus topics with subscriptions and filters** for business events that must not be lost, because it gives me sessions for ordering where I need it, dead-lettering, and duplicate detection. Event Grid for the high-volume, best-effort operational signals.

**A notification service consumes events and applies preferences.** It decides channel (mail, Teams, in-app), applies quiet hours, and — the important part — **aggregates**. Fifty data breaks in one feed produce one grouped notification, not fifty. Aggregation is a design feature, not a nice-to-have; without it people mute the channel and then miss the real one.

**Idempotency at the consumer.** Every event has an id; consumers record what they have processed. At-least-once delivery plus an idempotent consumer equals effectively-once behaviour, which is achievable, unlike true exactly-once.

**Outbox at the publisher.** The state change and the event are written in the same local transaction, then relayed. Otherwise you get the classic bug: the certificate is approved but the notification never went, or worse, the notification went and the approval rolled back.

### Step 4 — The alternative I rejected

**Direct calls or database polling.** Polling is simple and I have used it for low-stakes cases. Rejected here because it does not scale with consumers, adds latency, and every new consumer means changing the publisher or adding another poller against the operational database.

### Step 5 — Weakness

**A poison message can stall a subscription.** Mitigated with a max delivery count, dead-lettering, and an alert when the dead-letter queue is non-empty — because a silent dead-letter queue is the classic failure where everything looks green and nobody has been notified for a week.

---

## D7 · Modernise a legacy on-premises monolith onto Azure

> *"An old ASP.NET application, a single large SQL Server, no tests, and the business cannot stop for a rewrite. Move it to Azure."*

### Step 1 — Clarify

1. **"What is the business driver — cost, capability, or an end-of-life deadline?"** — The driver decides the strategy. Cost pressure means lift-and-shift first. New capability means strangler. A hardware end-of-life date means the migration is a schedule problem before it is an architecture problem.
2. **"How much of the code is actually exercised?"** — Every legacy estate has features nobody uses. Retiring them is the cheapest modernisation available.

### Step 2 — Qualities

No big-bang cutover. Reversible at every step. Business change continues during migration. Measurable progress that a sponsor can see monthly.

### Step 3 — The strategy

![Strangler fig migration: a routing façade sits in front of the legacy monolith; capabilities are extracted one at a time into ASP.NET Core services on Azure App Services with their own data, the façade routes each capability to the new service once it is proven, the monolith shrinks over successive releases, and each step is independently reversible](assets/strangler-fig-migration.svg)

*Figure 3.5 — Strangler fig. The façade lets me move one capability at a time, and roll back by changing a route.*

**Phase 0 — Make it measurable.** Before moving anything, add logging and telemetry to the legacy app. You cannot migrate safely what you cannot observe, and the telemetry tells you which features are actually used.

**Phase 1 — Put a façade in front.** Azure Front Door or Application Gateway routes all traffic. Nothing changes functionally, but now I have a seam.

**Phase 2 — Strangle by capability, highest value first.** Extract one capability into a new ASP.NET Core service. Route that path to the new service. Keep the old code in place, disabled, for one release — so rollback is a route change, not a redeployment.

**Phase 3 — Split the data last.** Data is always the hard part. Start with dual-write plus reconciliation for the extracted capability, verify the two agree over real traffic, then cut reads over, then retire the old path.

**Phase 4 — Retire.** Delete the strangled code. This phase gets skipped by everyone and it is the one that pays off; a half-migrated estate is more expensive than either end state.

### Step 4 — The alternative I rejected

**Big-bang rewrite.** I have seen these run for two years and get cancelled. The fatal flaw is that the business keeps changing the legacy system while you rewrite it, so you are aiming at a moving target with no delivery in between. I would only accept a rewrite for a small, well-understood, low-change system.

**Pure lift-and-shift to VMs** is a legitimate first step when the driver is a data-centre exit deadline, and I say so — but I would call it a relocation, not a modernisation, and I would insist on a follow-on plan so it does not become the permanent state.

### Step 5 — Weakness

**Strangler runs slower than a rewrite looks on a plan**, and it needs sustained sponsorship across many months. Mitigation: sequence the highest-visibility capability first so the sponsor sees value early, and publish a simple "percentage of traffic on the new platform" metric monthly. Momentum is a real architectural concern on multi-year migrations.

---

## D8 · Design high availability and disaster recovery on a fixed budget

> *"The business wants 'no downtime'. Finance has given you a budget that will not buy it. Design it."*

### Step 1 — Clarify

I do not accept "no downtime" as a requirement. I convert it into two numbers:

1. **"How long can we be down before it hurts, and what does an hour cost?"** → RTO
2. **"How much data can we afford to lose?"** → RPO

This is a real conversation I have had. Everyone says "zero" until they see the price of zero. Then they give you a real number.

### Step 2 — Tiering, which is the actual answer

The trick is that **not everything needs the same tier**, and paying for one uniform high tier is where the money goes. On the reporting platform, the read path and the ingestion path have genuinely different numbers.

| Component | RTO | RPO | What I buy |
|---|---|---|---|
| Reporting read path (API + UI) | Minutes | Not applicable (stateless) | Zone-redundant compute, multi-instance, health-probed routing |
| Operational database | Under an hour | Minutes | Zone redundancy + geo-replica + point-in-time restore |
| Ingestion pipeline | Hours | Near zero | Idempotent replay from source, checkpoints, backups |
| Analytical store | Longer | Rebuildable | It is derived — rebuild from the pipeline rather than restore |

That last row is the money-saver, and it is an architecture decision, not a cost trick: because the analytical store is derived from a source of truth through a repeatable pipeline, its disaster recovery plan is "run the pipeline". No expensive replication needed.

![High availability and disaster recovery topology: zone-redundant primary region with stateless API instances behind Front Door, geo-replicated operational database to a secondary region, derived analytical store rebuilt from pipeline rather than replicated, and a documented, timed failover runbook](assets/ha-dr-topology.svg)

*Figure 3.6 — Tiered HA/DR. Each component gets the tier its RTO/RPO justifies, not a uniform expensive one.*

### Step 3 — Active-passive, and I say why

I choose **active-passive** for these workloads. Active-active across regions on a financial data store means solving write conflicts, and the business did not value the extra nines enough to pay for that complexity. Naming the trade-off explicitly is the answer they are looking for; jumping straight to active-active shows you have not costed it.

### Step 4 — The part that matters most

**A DR plan that is never tested does not exist.**

I run a documented failover exercise and I time it. The first time I did this on a client platform, the documented RTO was two hours and the real number was much longer — because nobody had written down the DNS and connection-string steps, and the person who knew them was on leave. The architecture was fine. The runbook was fiction.

So the deliverable is not a diagram. It is: a runbook with named owners, a tested and timed failover, and a scheduled re-test. That is what I hand to the business as "disaster recovery".

### Step 5 — Weakness

**Failback is harder than failover** and gets far less attention. Coming back to the primary means reconciling anything written to the secondary. So the runbook covers both directions, and the failover drill includes a failback.

---

## Scenario index

| # | Scenario | Anchor | Central lesson |
|---|---|---|---|
| D1 | Daily investment reporting with a hard deadline | A | Keep the third party out of the user-facing path |
| D2 | Third-party ingestion and orchestration | A | Signal, do not schedule |
| D3 | Construction workflow platform | C | Split by release rhythm, not by layer |
| D4 | RAG assistant in a regulated firm | B | Retrieval quality is the ceiling |
| D5 | Multi-tenant reporting API | — | Isolation is structural, not a `WHERE` clause |
| D6 | Event-driven notifications | — | Publish facts; aggregate before you notify |
| D7 | Legacy modernisation | — | Reversible steps beat a big-bang plan |
| D8 | HA and DR on a budget | A, C | Tier by RTO/RPO; test the failover or it is fiction |

---

[← Technical Q&A](02-technical-qa.md) · [Home](README.md) · [Next → Team Management](04-team-management.md)
