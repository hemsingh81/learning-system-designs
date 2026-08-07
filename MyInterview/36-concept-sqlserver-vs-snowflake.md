# 36 · Concept: SQL Server vs Snowflake (30 questions)

[← Concept: Snowflake](35-concept-snowflake.md) · [Home](README.md) · [Next → Concept: Azure Core Services](37-concept-azure-services.md)

This file compares **SQL Server** and **Snowflake** fairly. On TCW (Project A) I use **both, on purpose** — SQL Server for operational reads, Snowflake for analytics — so I answer as someone who designed the split, not as a fan of either.

> Simple one-liner: *"They're built for different jobs. SQL Server is an OLTP database — fast, consistent live transactions. Snowflake is an OLAP data warehouse — huge analytical queries over history. It's not either/or; the best designs use each for what it's best at."*

**Jump to (core):** [D1 Core difference](#d1--the-core-difference-oltp-vs-olap) · [D2 Side-by-side](#d2--side-by-side-comparison) · [D3 Architecture](#d3--architecture-and-scaling) · [D4 Cost](#d4--cost-model) · [D5 When to use which](#d5--when-to-use-which) · [D6 The two-store design](#d6--the-two-store-design-i-actually-built)
> **Feature-by-feature:** [D7 Storage model](#d7--storage-model) · [D8 Compute & concurrency](#d8--compute-and-concurrency) · [D9 Indexing & tuning](#d9--indexing-and-tuning) · [D10 Transactions](#d10--transactions-and-consistency) · [D11 Data types](#d11--data-types-and-semi-structured) · [D12 Scaling](#d12--scaling-models) · [D13 Latency](#d13--latency-and-throughput)
> **Ops & architecture:** [D14 Management](#d14--management-effort) · [D15 HA/DR](#d15--high-availability-and-dr) · [D16 Security](#d16--security-and-governance) · [D17 Backup/recovery](#d17--backup-and-recovery) · [D18 Monitoring](#d18--monitoring) · [D19 Data modelling](#d19--data-modelling) · [D20 ETL/ELT](#d20--etl-vs-elt-between-them)
> **Decision & full-stack lens:** [D21 App integration](#d21--app-integration) · [D22 Azure fit](#d22--azure-ecosystem-fit) · [D23 Migration](#d23--migration-considerations) · [D24 Cost deep](#d24--cost-deep-dive) · [D25 Team skills](#d25--team-and-skills) · [D26 Real-time analytics](#d26--real-time-analytics) · [D27 AI/ML](#d27--ai-and-ml-workloads) · [D28 One-store risk](#d28--why-not-just-one-store) · [D29 Keeping in sync](#d29--keeping-the-two-stores-in-sync) · [D30 Your recommendation](#d30--your-one-paragraph-recommendation) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of SQL Server vs Snowflake in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. They are built for two different jobs, not one race.** SQL Server is an OLTP database — its job is many small, fast, correct reads and writes of live data. Snowflake is an OLAP data warehouse — its job is a few huge queries scanning years of history. On TCW (Project A) I run both on purpose, so I never pick a "winner" — I pick the right tool per workload.

**2. The shape of the work decides the store.** If the pattern is "grab one record, update one record, do it thousands of times a second" that is OLTP and SQL Server wins. If the pattern is "scan millions of rows, group and aggregate for a dashboard" that is OLAP and Snowflake wins. I look at the query shape first, brand second.

**3. Snowflake separates storage from compute — that is its superpower.** In Snowflake the data sits in cheap cloud storage and you spin up independent compute "warehouses" that scale up or out per team, then switch off. SQL Server ties storage and compute together on a server you size and keep running. That single design choice explains most of the cost and scaling differences.

**4. The cost models are opposite, so you optimise them opposite ways.** SQL Server costs money whether busy or idle — you pay for the provisioned server, so you keep it well-sized and always-on. Snowflake bills per second of compute you use, so I make queries efficient, auto-suspend idle warehouses, and watch that nobody leaves a big warehouse running.

**5. Tuning is a different craft on each.** On SQL Server I earn performance with indexes, statistics and query plans. On Snowflake there are no traditional indexes — I get speed from micro-partitions, clustering keys and right-sizing the warehouse. Skills do not transfer one-for-one; the mental model must switch with the engine.

**6. Semi-structured and scale-out favour Snowflake; low-latency single-row work favours SQL Server.** Snowflake ingests JSON natively and scales analytical concurrency by adding warehouses. SQL Server gives millisecond single-row transactions and strong consistency for an app. Knowing which strength you need is the whole decision.

**7. The best design uses both and keeps them in sync.** My real answer is rarely "one store". It is SQL Server for the operational app, Snowflake for reporting and AI, and a clean pipeline (CDC/ELT) moving data from one to the other — so each store does only what it is best at.

**The full-stack / architect lens:** the later Q&As go deeper — HA/DR, security and governance, backup, monitoring, ETL vs ELT between the two, migration, real-time analytics, AI/ML workloads, and how both fit the Azure ecosystem. They all trace back to the seven ideas above: match the workload to the engine, respect the cost model, and keep the two stores in sync.

**One rule I never break:** *never run heavy analytics on the database your live app depends on — separate the operational store from the analytical store.*

---

## D1 · The core difference: OLTP vs OLAP

**Simple explanation.** The single most important point:
- **SQL Server = OLTP** (*transactions*). Built for many small, fast, reliable reads and writes of live data — an app saving and fetching records. Correctness and low latency per operation.
- **Snowflake = OLAP** (*analytics*). Built for a few very large queries scanning lots of history for reporting and dashboards.

*"Asking which is 'better' is like asking whether a sports car or a truck is better — it depends what you're carrying."*

**Follow-ups**
- *"Can SQL Server do analytics?"* — Yes, but big historical queries can hurt its live-transaction performance — which is exactly the problem the split solves.
- *"Can Snowflake handle live app writes?"* — It's not designed for high-frequency small transactions; it shines on bulk loads and big reads.

---

## D2 · Side-by-side comparison

| Aspect | SQL Server | Snowflake |
|---|---|---|
| Type | Relational DB (OLTP) | Cloud data warehouse (OLAP) |
| Best for | Live app data, transactions | Analytics, reporting, history |
| Hosting | Self-managed or Azure SQL | Fully-managed SaaS (on Azure/AWS/GCP) |
| Storage & compute | Coupled | **Separated** |
| Scaling | Scale up; some scale-out | Elastic; scale up *and* out instantly |
| Indexes/tuning | You manage indexes & plans | Automatic (micro-partitions), no indexes |
| Concurrency | Limited by the server | Many workloads, isolated compute |
| Cost | License / Azure tier | Pay per-use (storage + compute credits) |
| Data types | Structured | Structured + semi-structured (VARIANT) |

**Follow-ups**
- *"Biggest structural difference?"* — Snowflake separates storage from compute; SQL Server couples them — that's why concurrency and elastic scaling differ so much.
- *"Do I tune Snowflake like SQL Server?"* — No manual indexes — I tune cost/warehouse sizing and write efficient SQL instead.

---

## D3 · Architecture and scaling

**Simple explanation.** SQL Server runs on a server (or managed Azure SQL) where storage and compute live together — so a heavy query competes with everything else, and scaling usually means a bigger machine. Snowflake separates storage from compute, so different workloads use **separate compute** on the **same data**, and it scales up (bigger) and out (more clusters) elastically and instantly.

**Follow-ups**
- *"Why does the split help concurrency?"* — The BI team's huge query runs on its own warehouse and can't slow the ETL or another team — no contention.
- *"SQL Server scale-out options?"* — Read replicas and partitioning help, but it's not as effortless as Snowflake's elastic model.

---

## D4 · Cost model

**Simple explanation.** SQL Server costs are mostly **fixed** — licences or an Azure SQL tier you pay for whether busy or idle. Snowflake is **pay-for-use** — cheap storage plus compute credits consumed only while a warehouse runs (and it auto-suspends when idle).

**Implication:** Snowflake can be very cost-efficient for spiky analytical workloads (pay only when querying), while a steadily-busy OLTP system fits SQL Server's fixed model well.

**Follow-ups**
- *"Which is cheaper?"* — Depends on the pattern: bursty analytics → Snowflake's per-use wins; constant transactional load → fixed SQL Server can be more predictable.
- *"Cost as a design decision?"* — Yes — I size warehouses and set auto-suspend precisely because compute = money in Snowflake.

---

## D5 · When to use which

**Simple explanation.**
- **Use SQL Server when:** you're storing and updating live application data, need ACID transactions, low-latency single-row reads/writes, and strong integrity — the operational heart of an app.
- **Use Snowflake when:** you're analysing large volumes of historical data, running reports/dashboards/BI, need many teams querying concurrently, or handling semi-structured data at scale.

**Follow-ups**
- *"Real rule of thumb?"* — If it's *running the business right now* (transactions) → SQL Server. If it's *understanding the business over time* (analytics) → Snowflake.
- *"Where does the data move between them?"* — An ETL/ELT pipeline copies operational data into the warehouse for analytics — exactly my TCW flow.

---

## D6 · The two-store design I actually built

**How I answer (from real work).** *"On TCW I deliberately run both. SQL Server is the operational store the time-critical reports read — fast, consistent, transactional. Snowflake is the analytical store for heavy historical and cross-portfolio analysis."*

**Why the split matters:** a big historical query on the same box as the deadline-critical reads could push reporting past the **pre-market window**. By separating operational (SQL Server) from analytical (Snowflake), a heavy analytics query **can never threaten the daily deadline**. My FastAPI ETL and the ADF/Tidal/Airflow orchestration move validated data from the operational store into Snowflake for analytics.

*"That's the mature architect answer: not 'which is better', but 'use each for its strength and protect the critical path'."*

**Follow-ups**
- *"Isn't running two stores more complex?"* — Yes, and I own that cost — but protecting a hard daily deadline in a regulated firm is worth it.
- *"How do you keep them in sync?"* — A validated, reconciled ETL pipeline with retry and checks, so the analytical store faithfully reflects the operational one.

---

## D7 · Storage model

**Simple explanation.** SQL Server stores data in **row-based** pages on disk you manage (files, filegroups), tuned for reading/writing whole rows fast. Snowflake stores data as **columnar micro-partitions** in cloud object storage, compressed and pruned automatically — tuned for scanning a few columns across billions of rows.

**Follow-ups**
- *"Row vs columnar — why it matters?"* — Row storage is great for "get this one record"; columnar is great for "sum this column over millions of rows".
- *"Who manages storage?"* — I manage SQL Server files; Snowflake manages storage entirely for me.

---

## D8 · Compute and concurrency

**Simple explanation.** SQL Server's compute is the server — all queries share it, so a heavy report can starve live transactions. Snowflake gives each workload its **own virtual warehouse** over shared storage, so many teams run big queries at once without contention.

**Follow-ups**
- *"The concurrency killer in SQL Server?"* — One big analytical query competing with OLTP — exactly why I offload analytics to Snowflake.
- *"How does Snowflake isolate?"* — Separate compute clusters read one data copy — no workload blocks another.

---

## D9 · Indexing and tuning

**Simple explanation.** SQL Server performance is largely **my job**: indexes, statistics, execution plans, isolation levels. Snowflake has **no manual indexes** — micro-partition pruning is automatic; I tune warehouse size, clustering keys, and efficient SQL/cost instead.

**Follow-ups**
- *"Less tuning in Snowflake?"* — Different tuning — no indexes, but I optimise cost and scan volume.
- *"Which needs a DBA more?"* — SQL Server needs classic DBA tuning; Snowflake shifts effort to cost governance and modelling.

---

## D10 · Transactions and consistency

**Simple explanation.** SQL Server is built for **ACID transactions** — fine-grained, high-rate, strongly consistent writes with locking/isolation. Snowflake supports transactions too, but is optimised for **bulk** loads and analytical reads, not high-frequency small writes.

**Follow-ups**
- *"Does Snowflake have ACID?"* — Yes for its operations, but it's not the tool for many tiny concurrent OLTP writes.
- *"Where do live app writes go?"* — SQL Server — then ETL moves data to Snowflake for analytics.

---

## D11 · Data types and semi-structured

**Simple explanation.** SQL Server is strongest with **structured** relational data (it does have JSON functions, but it's not its core). Snowflake natively handles **semi-structured** (JSON/Parquet/Avro) via `VARIANT` and queries it with SQL — a big advantage for evolving source feeds.

**Follow-ups**
- *"JSON in SQL Server?"* — Possible via JSON functions, but Snowflake's VARIANT + FLATTEN is far more natural at scale.
- *"Why does this matter for TCW?"* — Aladdin/source feeds evolve — Snowflake ingests them flexibly for analytics.

---

## D12 · Scaling models

**Simple explanation.** SQL Server scales **up** (bigger box) and adds **read replicas**; true write scale-out is hard. Snowflake scales **up and out elastically and instantly** — bigger warehouse for one heavy query, more clusters for many users — with no hardware to provision.

**Follow-ups**
- *"Elastic scaling advantage?"* — Snowflake handles spiky analytical demand without pre-buying capacity.
- *"SQL Server write scale-out?"* — Limited — partitioning/sharding help but it's not effortless — a reason to split OLTP/OLAP.

---

## D13 · Latency and throughput

**Simple explanation.** SQL Server gives **low latency** on single-row operations (milliseconds) — ideal for an app. Snowflake has higher per-query startup (warehouse resume) but massive **throughput** on big scans. Different shapes: fast small vs powerful big.

**Follow-ups**
- *"Snowflake for a per-click app query?"* — No — latency/cost per query is wrong for that; SQL Server or a cache serves it.
- *"Snowflake throughput win?"* — It chews through billions of rows for reporting that would cripple an OLTP box.

---

## D14 · Management effort

**Simple explanation.** SQL Server (self-managed) means patching, backups, HA, index maintenance — Azure SQL reduces this. Snowflake is **fully managed SaaS**: no servers, patching or index upkeep — I focus on modelling, SQL and cost.

**Follow-ups**
- *"Least ops?"* — Snowflake — near-zero infrastructure management.
- *"Azure SQL narrows the gap?"* — Yes — managed Azure SQL removes much SQL Server ops, though indexing/tuning remain mine.

---

## D15 · High availability and DR

**Simple explanation.** SQL Server HA/DR I design — Always On replicas, failover, cross-region async (RPO/RTO). Snowflake builds resilience in (multi-AZ, automatic replication options, cross-region/cloud replication for DR) with far less for me to configure.

**Follow-ups**
- *"Who owns HA design?"* — Me for SQL Server; largely Snowflake for its platform (I configure replication where needed).
- *"Cross-region DR?"* — Snowflake offers database replication/failover across regions/clouds as a managed feature.

---

## D16 · Security and governance

**Simple explanation.** Both are strong: SQL Server has TDE, Always Encrypted, roles; Snowflake has RBAC role hierarchy, dynamic masking, row access policies, SSO. Both integrate with **Entra ID**. Governance features (masking/row policies) are especially slick in Snowflake for analytics.

**Follow-ups**
- *"Column masking in each?"* — SQL Server dynamic data masking; Snowflake masking policies — both exist, Snowflake's are policy-driven and role-aware.
- *"Single sign-on?"* — Both federate through Entra ID for central identity.

---

## D17 · Backup and recovery

**Simple explanation.** SQL Server: full/diff/log backups and point-in-time restore I manage. Snowflake: **Time Travel** (query/restore recent past) plus **Fail-safe** (extra recovery window) built in — recovery without managing backup files.

**Follow-ups**
- *"Snowflake's version of point-in-time?"* — Time Travel — query or restore data as of a past moment, then Fail-safe as a last resort.
- *"Do I still test restores?"* — For SQL Server yes; for Snowflake I still validate Time Travel/recovery expectations.

---

## D18 · Monitoring

**Simple explanation.** SQL Server: DMVs, Query Store, Azure SQL Insights. Snowflake: Query Profile, `ACCOUNT_USAGE` views, resource monitors for credits. Both let me find slow queries — Snowflake adds first-class **cost** monitoring.

**Follow-ups**
- *"Find a slow query in each?"* — DMVs/Query Store vs Query Profile/ACCOUNT_USAGE — same goal, different tools.
- *"Cost monitoring?"* — Uniquely important in Snowflake — resource monitors cap runaway credits.

---

## D19 · Data modelling

**Simple explanation.** SQL Server (OLTP) is **normalised** (3NF) for write integrity. Snowflake (OLAP) uses **star schemas** (denormalised facts + dimensions) for fast analytical reads. Same data, modelled oppositely for its purpose.

**Follow-ups**
- *"Why opposite models?"* — Normalise to write safely (OLTP); denormalise to read fast (OLAP).
- *"Who transforms between them?"* — The ETL/ELT pipeline reshapes normalised operational data into analytical star schemas.

---

## D20 · ETL vs ELT between them

**Simple explanation.** Moving data from SQL Server to Snowflake I favour **ELT**: extract, **load raw** into Snowflake, then **transform** with Snowflake's elastic compute (often via dbt). Classic ETL transforms before load; ELT is more flexible and re-runnable at warehouse scale.

**Follow-ups**
- *"Why ELT into Snowflake?"* — Load cheap, transform with elastic power, keep raw for re-processing.
- *"My TCW flow?"* — FastAPI validates, ADF/orchestration stages, COPY/Snowpipe loads Snowflake, dbt/SQL transforms.

---

## D21 · App integration

**Simple explanation (full-stack lens).** The app writes/reads live data on **SQL Server** (via EF Core, low latency). It does **not** query Snowflake per click; instead reports/dashboards and precomputed aggregates come from Snowflake asynchronously or through a serving layer/cache.

**Follow-ups**
- *"Why not point the UI at Snowflake?"* — Per-request latency/cost is wrong for interactive UI — SQL Server/cache serves the app; Snowflake serves analytics.
- *"How does a dashboard get Snowflake data?"* — BI tool (Power BI) or an API that queries Snowflake for heavy analytics, often cached.

---

## D22 · Azure ecosystem fit

**Simple explanation.** Both run in Azure. **Azure SQL** is the native, tightly-integrated relational option. **Snowflake** runs on Azure and integrates via Blob/ADLS, ADF, Entra ID and Power BI. If staying 100% Microsoft mattered, I'd also weigh **Azure Synapse** against Snowflake.

**Follow-ups**
- *"Most native to Azure?"* — Azure SQL (relational) and Synapse (analytics) are first-party; Snowflake is a strong third-party analytics choice on Azure.
- *"Why choose Snowflake over Synapse?"* — Its clean storage/compute separation and low ops — decided per project.

---

## D23 · Migration considerations

**Simple explanation.** You don't "migrate SQL Server to Snowflake" — they do different jobs. You **add** Snowflake for analytics and keep SQL Server for OLTP. If moving analytical workloads off SQL Server, I pipe data via ELT and rebuild analytical models as star schemas.

**Follow-ups**
- *"Replace SQL Server with Snowflake?"* — Only the analytical part — OLTP stays on SQL Server; it's augmentation, not replacement.
- *"Biggest migration effort?"* — Re-modelling normalised data into analytical schemas and rebuilding the pipeline.

---

## D24 · Cost deep dive

**Simple explanation.** SQL Server = mostly **fixed** (licence/Azure tier) — predictable, paid even when idle. Snowflake = **variable** (storage + compute credits) — near-zero when idle, but needs governance (auto-suspend, right-sizing, resource monitors) so it doesn't surprise you.

**Follow-ups**
- *"Which is cheaper?"* — Constant OLTP load → fixed SQL Server is predictable; bursty analytics → Snowflake pay-per-use wins.
- *"Snowflake cost risk?"* — A warehouse left running/oversized — controlled by auto-suspend and monitors.

---

## D25 · Team and skills

**Simple explanation.** SQL Server needs classic **DBA/T-SQL** skills (indexing, plans, HA). Snowflake needs **SQL + cloud data engineering** (warehouse sizing, cost, dbt/ELT). Both use SQL, so a strong SQL team adapts — the platform skills differ.

**Follow-ups**
- *"Reuse SQL skills?"* — Largely yes — SQL transfers; the ops/cost mindset is what shifts.
- *"New skill for Snowflake?"* — Cost governance and warehouse management — there's no DBA index tuning.

---

## D26 · Real-time analytics

**Simple explanation.** For near-real-time, SQL Server can serve fresh operational reads directly; Snowflake reaches near-real-time via **Snowpipe/streaming**. True sub-second live analytics on fresh app data usually leans on SQL Server (or a streaming layer) rather than a warehouse.

**Follow-ups**
- *"How fresh is Snowflake data?"* — As fresh as the load cadence — Snowpipe/streaming brings it to near-real-time.
- *"Sub-second on live data?"* — SQL Server or a purpose-built streaming store — not a warehouse's sweet spot.

---

## D27 · AI and ML workloads

**Simple explanation.** For analytics-scale AI/ML, Snowflake wins — **Snowpark** and **Cortex** run ML/LLM and vector search next to governed data. SQL Server has some ML integration but isn't the analytics/AI platform. My app-level RAG uses Azure OpenAI/AI Foundry (file 37); in-warehouse AI uses Snowflake.

**Follow-ups**
- *"ML on which?"* — Snowflake (Snowpark/Cortex) for data-scale ML/AI; SQL Server for transactional data, not model training.
- *"Vector search?"* — Snowflake supports it near the data; app RAG uses Azure AI services.

---

## D28 · Why not just one store?

**Simple explanation (the trade-off).** One store is simpler and cheaper to run — tempting. But mixing heavy analytics with time-critical OLTP on one system risks the deadline (my TCW pre-market window). Two stores add complexity but **protect the critical path** and let each workload scale independently.

**Follow-ups**
- *"When is one store fine?"* — Small scale, no hard deadline, light analytics — don't over-engineer.
- *"Why did TCW need two?"* — A hard pre-market deadline plus heavy historical analytics — separation guarantees the deadline is safe.

---

## D29 · Keeping the two stores in sync

**Simple explanation.** A **validated, reconciled pipeline**: FastAPI validates at the boundary, orchestration (ADF/Tidal/Airflow) moves and stages data, idempotent loads (upsert/MERGE) prevent duplicates, and reconciliation checks confirm the analytical store matches the operational one. Retries and alerts handle failures.

**Follow-ups**
- *"How do you avoid duplicates on retry?"* — Idempotent upserts keyed by natural id — a re-run is safe.
- *"How do you know they match?"* — Reconciliation counts/checksums between source and warehouse, with alerts on drift.

---

## D30 · Your one-paragraph recommendation

**How I answer (the mature take).** *"They're not competitors — they're partners for different jobs. SQL Server is my OLTP heart: fast, consistent, transactional live data with the tuning and integrity an app needs. Snowflake is my OLAP brain: elastic, separated storage/compute for huge analytical queries over history, with automatic tuning and pay-per-use cost. On TCW I deliberately run both, connected by a validated ELT pipeline, precisely so a heavy analytics query can never threaten the pre-market reporting deadline. The architect's answer isn't 'which is better' — it's 'use each for its strength and protect the critical path'."*

**Follow-ups**
- *"If forced to pick one?"* — Depends on the dominant workload — transactional app → SQL Server; analytics platform → Snowflake — but I'd resist forcing one to do both.
- *"Biggest mistake teams make?"* — Running heavy analytics on their OLTP database and then wondering why the app slows down.

---

## Section index

| # | Question | The key point |
|---|---|---|
| D1 | Core difference | SQL Server = OLTP (transactions); Snowflake = OLAP (analytics) |
| D2 | Side-by-side | Coupled vs separated storage/compute; managed vs self-managed |
| D3 | Architecture | Snowflake's split enables isolated, elastic concurrency |
| D4 | Cost | SQL Server fixed; Snowflake pay-per-use with auto-suspend |
| D5 | When to use | Running the business → SQL Server; understanding it → Snowflake |
| D6 | Two-store design | Split protects the pre-market deadline; ETL moves data across |
| D7 | Storage model | Row pages (SQL) vs columnar micro-partitions (Snowflake) |
| D8 | Compute & concurrency | Shared server vs isolated virtual warehouses |
| D9 | Indexing & tuning | Manual indexes/plans vs auto pruning + cost tuning |
| D10 | Transactions | High-rate ACID (SQL) vs bulk + analytics (Snowflake) |
| D11 | Data types | Structured (SQL) vs native semi-structured VARIANT |
| D12 | Scaling | Scale-up + replicas vs elastic up-and-out |
| D13 | Latency | Low-latency rows (SQL) vs high-throughput scans (Snowflake) |
| D14 | Management | Self/Azure-managed vs fully-managed SaaS |
| D15 | HA/DR | I design Always On vs mostly built-in resilience |
| D16 | Security | Both strong + Entra ID; Snowflake policy-driven masking |
| D17 | Backup | Backups/PITR vs Time Travel + Fail-safe |
| D18 | Monitoring | DMVs/Query Store vs Query Profile + cost monitors |
| D19 | Data modelling | Normalised OLTP vs star-schema OLAP |
| D20 | ETL/ELT | ELT into Snowflake; transform with elastic compute |
| D21 | App integration | App on SQL Server; Snowflake serves analytics, not clicks |
| D22 | Azure fit | Azure SQL/Synapse native; Snowflake strong on Azure |
| D23 | Migration | Add Snowflake for analytics; OLTP stays on SQL Server |
| D24 | Cost deep | Fixed (SQL) vs variable pay-per-use with governance |
| D25 | Team skills | DBA/T-SQL vs SQL + cloud data engineering |
| D26 | Real-time | SQL for live; Snowflake near-real-time via Snowpipe |
| D27 | AI/ML | Snowpark/Cortex on Snowflake; app RAG on Azure |
| D28 | One-store risk | One store risks the deadline; two protect the critical path |
| D29 | Keeping in sync | Validated idempotent ELT + reconciliation checks |
| D30 | Recommendation | Partners not rivals; use each strength, protect critical path |

---

[← Concept: Snowflake](35-concept-snowflake.md) · [Home](README.md) · [Next → Concept: Azure Core Services](37-concept-azure-services.md)
