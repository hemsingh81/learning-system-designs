# 35 · Concept: Snowflake (30 questions)

[← Concept: SQL Server](34-concept-sql-server.md) · [Home](README.md) · [Next → SQL Server vs Snowflake](36-concept-sqlserver-vs-snowflake.md)

This file explains **Snowflake** simply and in depth. On TCW (Project A) Snowflake is my **analytical/historical** store, sitting alongside SQL Server, so I answer from real design decisions.

> Simple one-liner: *"Snowflake is a cloud data platform (a data warehouse) built for big analytics. Its key trick is separating storage from compute — so you can run huge queries on massive history without slowing anyone else down, and pay only for what you use."*

**Jump to (fundamentals):** [K1 What it is](#k1--what-is-snowflake) · [K2 Storage vs compute](#k2--separation-of-storage-and-compute) · [K3 Virtual warehouses](#k3--virtual-warehouses) · [K4 Architecture](#k4--the-three-layer-architecture) · [K5 Scaling](#k5--scaling-up-and-out) · [K6 Cost model](#k6--the-pay-for-use-cost-model) · [K7 Loading & semi-structured](#k7--loading-data-and-semi-structured-support) · [K8 Time Travel & sharing](#k8--time-travel-cloning-and-sharing)
> **Internals & performance:** [K9 Micro-partitions](#k9--micro-partitions-and-pruning) · [K10 Clustering keys](#k10--clustering-keys) · [K11 Caching](#k11--caching-layers) · [K12 Query tuning](#k12--query-tuning-in-snowflake) · [K13 Cost tuning](#k13--cost-optimisation-deep-dive) · [K14 Concurrency](#k14--concurrency-and-multi-cluster)
> **Data engineering:** [K15 Loading options](#k15--loading-options-copy-snowpipe-streaming) · [K16 Streams & Tasks](#k16--streams-and-tasks) · [K17 Transformation](#k17--transformation-elt-and-dbt) · [K18 Semi-structured deep](#k18--semi-structured-data-deep-dive) · [K19 Data modelling](#k19--data-modelling-for-analytics) · [K20 External tables](#k20--external-tables-and-the-lake)
> **Architecture & governance:** [K21 Security](#k21--security-and-rbac) · [K22 Data sharing](#k22--data-sharing-and-marketplace) · [K23 Governance](#k23--governance-masking-and-row-access) · [K24 Azure integration](#k24--integration-with-azure) · [K25 Snowpark](#k25--snowpark-and-in-database-code) · [K26 Cortex/AI](#k26--snowflake-cortex-and-ai)
> **Full-stack & decision lens:** [K27 App access](#k27--accessing-snowflake-from-an-app) · [K28 Warehouse vs lakehouse](#k28--warehouse-vs-lakehouse) · [K29 vs Synapse/Databricks](#k29--snowflake-vs-synapse-and-databricks) · [K30 When not to use it](#k30--when-not-to-use-snowflake) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of Snowflake in plain English. On TCW (A) Snowflake is my **analytical/historical** store, sitting alongside SQL Server, so this is how I actually reason about it. Hold these ideas and every question below is a detail hanging off one of them.

**1. It's a cloud data warehouse for OLAP.** Snowflake is built to store and analyse very large amounts of data — big queries over history for reporting and analytics (**OLAP**), not many small live transactions. It's fully managed SaaS on top of Azure/AWS/GCP, and you talk to it purely through SQL — no servers, indexes or tuning to babysit.

**2. Separating storage from compute is the whole trick.** Storage sits in cheap cloud object storage; **compute** runs on separate, on-demand engines. This split is why huge queries don't slow anyone else down and why I pay only for what I use. Almost every other Snowflake advantage flows from this one idea.

**3. Virtual warehouses are the compute.** A virtual warehouse is a cluster I size (XS→4XL) and spin up per workload. I can give ETL, dashboards and ad-hoc analysts their own warehouses so they never contend. They auto-suspend when idle and auto-resume on demand — no idle cost.

**4. Three-layer architecture.** Storage (the data), Compute (virtual warehouses), and a Cloud Services layer (the brain — metadata, security, query planning, optimisation). Knowing which layer does what explains caching, scaling and how queries actually run.

**5. Micro-partitions and pruning make it fast.** Snowflake automatically stores data in small immutable **micro-partitions** and keeps metadata on each. When a query has a filter, it **prunes** — skips partitions that can't match — so it reads a fraction of the data. Clustering keys help pruning on huge tables.

**6. Scaling up vs out.** Scale **up** (bigger warehouse) for a single heavy query; scale **out** (multi-cluster) for many concurrent users. They solve different problems — size for query weight, cluster count for concurrency — and mixing them up wastes money.

**7. The cost model is pay-for-use — so cost is a design concern.** You pay for compute per second a warehouse runs, plus storage. Auto-suspend, right-sizing, avoiding runaway queries and using caching are all cost decisions. On A, splitting stores by purpose keeps heavy analysis off SQL Server *and* keeps Snowflake spend honest.

**The full-stack / architect lens:** the later Q&As go deeper — clustering keys, caching layers, query and cost tuning, concurrency and multi-cluster, loading (COPY/Snowpipe/streaming), Streams and Tasks, ELT and dbt, semi-structured data, data modelling, security and RBAC, data sharing, governance and masking, Azure integration, Snowpark and Cortex/AI — plus decision calls: accessing it from an app, warehouse vs lakehouse, versus Synapse/Databricks, and when *not* to use it. That's warehouse ownership, not just running SQL.

**One rule I never break:** *right-size and auto-suspend every warehouse — in Snowflake, idle compute is money burning, so cost is part of the design, not an afterthought.*

---

## K1 · What is Snowflake?

**Simple explanation.** Snowflake is a **cloud-native data warehouse** — a system built to store and analyse very large amounts of data. It's designed for **OLAP** (*Online Analytical Processing*): big queries over history for reporting, dashboards and analytics.

Unlike SQL Server, which you (or Azure) run on servers, Snowflake is **fully managed SaaS** — no servers, indexes or tuning to manage. It runs on top of Azure, AWS or GCP, and you interact with it purely through SQL.

*"On TCW I use Snowflake for analytical and historical work — heavy queries that would slow the deadline-critical reports if they ran on SQL Server. Splitting the stores by purpose protects the pre-market window."*

**Follow-ups**
- *"Warehouse vs database?"* — A regular database (SQL Server) is tuned for many small live transactions; a data warehouse (Snowflake) is tuned for a few huge analytical queries over lots of history.
- *"Do you manage indexes in Snowflake?"* — No — Snowflake handles storage and micro-partitioning automatically; there are no manual indexes to tune.

---

## K2 · Separation of storage and compute

**Simple explanation.** This is Snowflake's headline idea. In a traditional database, storage and processing are joined — a big query competes with everyone else for the same machine. Snowflake **separates** them:
- **Storage** — all data sits once in cloud storage.
- **Compute** — independent clusters ("virtual warehouses") that read that storage.

So the finance team and the data-science team can run huge queries **at the same time on the same data** using *separate* compute, and neither slows the other. You also scale (and pay for) each independently.

**Follow-ups**
- *"Why is this a big deal?"* — No more "the big report is running, everything's slow." Each workload gets its own compute over shared storage.
- *"Does data get copied per team?"* — No — one copy of storage; many compute clusters read it.

---

## K3 · Virtual warehouses

**Simple explanation.** A **virtual warehouse** is a compute cluster that runs your queries. You size it (X-Small → 4X-Large) for the job, and you can have many, each for a different team or workload. Crucially, a warehouse can **auto-suspend** when idle (so you stop paying) and **auto-resume** when a query arrives.

```sql
CREATE WAREHOUSE reporting_wh
  WAREHOUSE_SIZE = 'MEDIUM'
  AUTO_SUSPEND = 60      -- pause after 60s idle (save money)
  AUTO_RESUME = TRUE;    -- wake instantly on next query
```

**Follow-ups**
- *"Separate warehouses — why?"* — To isolate workloads (ETL vs BI vs ad-hoc) so they never compete, and to size/bill each appropriately.
- *"Auto-suspend value?"* — You pay for compute only while queries run — idle warehouses cost nothing.

---

## K4 · The three-layer architecture

**Simple explanation.** Snowflake has three separate layers, which is why it scales so well:
1. **Storage layer** — your data, compressed and stored once in cloud storage as micro-partitions.
2. **Compute layer** — the virtual warehouses that process queries.
3. **Cloud services layer** — the "brain": authentication, query optimization, metadata, transactions.

Each layer scales independently — the secret behind concurrent big queries without contention.

**Follow-ups**
- *"What are micro-partitions?"* — Snowflake automatically splits data into small compressed chunks with metadata, so it can skip chunks that don't match a query — fast, with no manual indexing.
- *"What does the services layer do for me?"* — It optimises queries and manages metadata so I don't tune the engine — I just write SQL.

---

## K5 · Scaling up and out

**Simple explanation.** Two kinds of scaling:
- **Scale up** — make a warehouse *bigger* (more power) for a single heavy/complex query.
- **Scale out** — add more clusters (multi-cluster warehouse) to handle *more concurrent users* automatically.

```sql
ALTER WAREHOUSE reporting_wh SET
  MIN_CLUSTER_COUNT = 1
  MAX_CLUSTER_COUNT = 3;   -- adds clusters automatically under heavy concurrency
```

**Follow-ups**
- *"Up vs out — which when?"* — Scale *up* for one big slow query; scale *out* when many users hit it at once.
- *"Is scaling instant?"* — Near-instant and elastic — a huge advantage over provisioning traditional hardware.

---

## K6 · The pay-for-use cost model

**Simple explanation.** You pay separately for **storage** (cheap, per TB) and **compute** (credits consumed *only while a warehouse runs*). Because warehouses auto-suspend, an idle system costs almost nothing for compute.

**Why an architect cares:** cost is a design lever. I control it by right-sizing warehouses, aggressive auto-suspend, separating workloads, and writing efficient SQL (less scanned = fewer credits).

**Follow-ups**
- *"How do you keep Snowflake costs down?"* — Short auto-suspend, correctly-sized warehouses, prune queries to scan less data, and monitor credit usage per workload.
- *"Biggest cost surprise?"* — A warehouse left running or oversized — governance and auto-suspend prevent it.

---

## K7 · Loading data and semi-structured support

**Simple explanation.** You load data into Snowflake with `COPY INTO` from cloud storage (or tools like Azure Data Factory — which I use on TCW). Snowflake also handles **semi-structured data** (JSON, Parquet, Avro) natively with the `VARIANT` type — you can query JSON with SQL directly.

```sql
SELECT raw:portfolio.id::string AS portfolio_id   -- query JSON stored in a VARIANT column
FROM staged_positions;
```

**Follow-ups**
- *"How does data get in on TCW?"* — My FastAPI ETL validates Aladdin data; orchestration (ADF/Tidal/Airflow) lands it, and `COPY INTO` loads Snowflake for analytics.
- *"Why is VARIANT useful?"* — I can store raw JSON as-is and query it with SQL without a rigid schema up front — great for evolving source data.

---

## K8 · Time Travel, cloning, and sharing

**Simple explanation.** Three features people love:
- **Time Travel** — query data *as it was* up to N days ago, or restore a dropped table. A safety net.
- **Zero-copy cloning** — instantly clone a huge table/database for testing without duplicating storage (it shares data until changed).
- **Secure data sharing** — share live data with another account without copying or moving it.

```sql
SELECT * FROM Position AT (OFFSET => -3600);   -- data as of one hour ago
CREATE TABLE Position_test CLONE Position;      -- instant, no storage copy
```

**Follow-ups**
- *"Time Travel use case?"* — Recover from a bad load or accidental delete, or compare today vs yesterday — without restoring a backup.
- *"Why is zero-copy cloning great?"* — Instant, storage-free test environments from production-size data.

---

## K9 · Micro-partitions and pruning

**Simple explanation.** Snowflake automatically stores data in **micro-partitions** — small, compressed, columnar chunks (~50–500MB) each with metadata (min/max values per column). When you query with a filter, Snowflake reads only the partitions whose metadata could match — called **pruning** — so it scans far less data. This replaces manual indexes.

**Follow-ups**
- *"Why no manual indexes?"* — Micro-partition metadata + columnar storage give index-like skipping automatically — nothing to tune.
- *"How do you help pruning?"* — Filter on well-clustered columns (often a date) so fewer partitions match.

---

## K10 · Clustering keys

**Simple explanation.** On very large tables, data can become spread across many partitions, hurting pruning. A **clustering key** tells Snowflake to keep related rows physically together (usually by date or a common filter column) so pruning stays effective. Snowflake can auto-recluster in the background.

**Follow-ups**
- *"When add a clustering key?"* — Only on big tables where query pruning has degraded — not by default (it costs credits to maintain).
- *"What column?"* — The one you filter on most (typically a date) — mirror the query pattern.

---

## K11 · Caching layers

**Simple explanation.** Snowflake caches at three levels: **result cache** (identical query → instant, free result for 24h), **local disk cache** (data a warehouse recently read), and **metadata cache**. Repeated dashboard queries often hit the result cache and cost nothing.

**Follow-ups**
- *"Why can the same query be free the second time?"* — The result cache returns the stored result without spinning up compute — if data and query are unchanged.
- *"Does resizing a warehouse lose cache?"* — The local disk cache is per-warehouse; resizing/suspending can clear it — a cost/perf trade-off.

---

## K12 · Query tuning in Snowflake

**Simple explanation.** No indexes to tune, so I tune differently: read the **Query Profile** to find the heaviest step, reduce data scanned (filter early, select fewer columns), avoid exploding joins and spilling to disk, right-size the warehouse, and lean on clustering for huge tables.

**Follow-ups**
- *"What is 'spilling'?"* — When a query runs out of memory and writes to disk (slow) — a bigger warehouse or a leaner query fixes it.
- *"First thing you check?"* — The Query Profile — it shows bytes scanned and the most expensive operator, just like an execution plan.

---

## K13 · Cost optimisation deep dive

**Simple explanation (architect lens).** Compute is the main cost. My levers: short **auto-suspend**, right-sized warehouses (bigger isn't always cheaper — it finishes faster but costs more per second), separate warehouses per workload, **resource monitors** to cap credits, result caching, and writing queries that scan less.

**Follow-ups**
- *"Resource monitor?"* — A guardrail that alerts or suspends a warehouse when it hits a credit budget — prevents runaway cost.
- *"Bigger warehouse = more cost?"* — Per second yes, but it may finish 4× faster, so total cost can be similar — I test which wins per workload.

---

## K14 · Concurrency and multi-cluster

**Simple explanation.** A single warehouse handles limited concurrent queries; beyond that, queries queue. A **multi-cluster warehouse** automatically adds clusters under load (scale out) and removes them when quiet — so a busy dashboard with many users stays fast without me babysitting it.

**Follow-ups**
- *"Scale up vs multi-cluster?"* — Scale up for one heavy query; multi-cluster (scale out) for many concurrent users.
- *"How does it save money?"* — Extra clusters spin up only during peaks, then shut down — elastic concurrency.

---

## K15 · Loading options: COPY, Snowpipe, streaming

**Simple explanation.** Three main paths: **`COPY INTO`** for batch loads from stages; **Snowpipe** for continuous, near-real-time file loads (auto-triggered as files arrive); and the **Streaming API** for row-level low-latency ingestion. I pick by latency need — batch for daily, Snowpipe for continuous.

**Follow-ups**
- *"Snowpipe vs COPY?"* — COPY is manual/scheduled batch; Snowpipe auto-loads new files with a serverless, pay-per-file model.
- *"How does TCW load?"* — FastAPI validates, orchestration (ADF) stages files, then COPY/Snowpipe loads Snowflake for analytics.

---

## K16 · Streams and Tasks

**Simple explanation.** A **Stream** tracks changes (CDC) on a table — what's new/changed since last read. A **Task** runs SQL on a schedule or after another task. Together they build in-Snowflake pipelines: a Task consumes a Stream to incrementally transform only changed rows.

**Follow-ups**
- *"What's a Stream for?"* — Change data capture — process just the delta instead of the whole table each run.
- *"Tasks vs external orchestrator?"* — Tasks for in-Snowflake steps; an external orchestrator (ADF/Airflow) for cross-system pipelines.

---

## K17 · Transformation: ELT and dbt

**Simple explanation.** Snowflake favours **ELT** (load raw, then transform inside Snowflake with SQL) over classic ETL, because compute is elastic. **dbt** is the popular tool: it manages SQL transformations, dependencies, tests and docs as version-controlled code — the analytics equivalent of application CI/CD.

**Follow-ups**
- *"ETL vs ELT here?"* — ELT: land raw data first, transform with Snowflake's power — more flexible and re-runnable than transforming before load.
- *"Why dbt?"* — It brings software discipline (version control, tests, lineage) to SQL transformations.

---

## K18 · Semi-structured data deep dive

**Simple explanation.** The **VARIANT** type stores JSON/Avro/Parquet as-is; you query nested fields with `:` and `[]` and flatten arrays with `LATERAL FLATTEN`. This lets me ingest evolving source data without a rigid schema and shape it later.

```sql
SELECT f.value:ticker::string AS ticker
FROM raw_positions, LATERAL FLATTEN(input => raw:holdings) f;
```

**Follow-ups**
- *"Why store raw JSON?"* — Source schemas change; VARIANT keeps me flexible and I transform on read.
- *"Performance of VARIANT?"* — Good — Snowflake still columnarises and prunes; for hot fields I materialise them into typed columns.

---

## K19 · Data modelling for analytics

**Simple explanation.** For a warehouse I model with **star schemas** — a central fact table (measures like market value) surrounded by dimension tables (portfolio, security, date). It's optimised for analytical reads and easy for BI tools, unlike the highly-normalised OLTP model in SQL Server.

**Follow-ups**
- *"Star vs snowflake schema?"* — Star keeps dimensions flat (simpler, faster); snowflake schema normalises dimensions (less redundancy, more joins).
- *"Why denormalise for analytics?"* — Fewer joins = faster big aggregations — the opposite priority to OLTP.

---

## K20 · External tables and the lake

**Simple explanation.** An **external table** lets Snowflake query files sitting in cloud storage (Azure Blob/ADLS) **without loading them in** — useful for querying a data lake or cold data cheaply. You trade some performance for not duplicating storage.

**Follow-ups**
- *"External vs internal table?"* — Internal = data loaded into Snowflake (fast); external = query files in place (flexible, cheaper storage, slower).
- *"Use case?"* — Query archived/lake data occasionally without paying to ingest it all.

---

## K21 · Security and RBAC

**Simple explanation.** Snowflake uses **role-based access control**: privileges are granted to roles, roles to users, and roles form a hierarchy. Add **network policies**, SSO (Entra ID), MFA, and encryption everywhere (at rest and in transit) by default.

**Follow-ups**
- *"Why role hierarchy?"* — Grant privileges to roles once, assign roles to people — clean, auditable least-privilege access.
- *"SSO with Azure?"* — Yes — federate Snowflake login through Entra ID for central identity and MFA.

---

## K22 · Data sharing and Marketplace

**Simple explanation.** **Secure Data Sharing** lets me share live, read-only data with another Snowflake account — no copying, no ETL; they see updates instantly. The **Marketplace** extends this to third-party datasets you can query directly.

**Follow-ups**
- *"How is sharing 'zero-copy'?"* — The consumer queries my storage via their own compute — no data moves or duplicates.
- *"Business value?"* — Share data with partners/teams instantly and safely instead of emailing extracts.

---

## K23 · Governance: masking and row access

**Simple explanation.** For sensitive financial data I use **dynamic data masking** (mask a column unless the role is authorised) and **row access policies** (a role sees only its permitted rows). **Object tagging** and access history support audit/compliance.

**Follow-ups**
- *"Dynamic masking example?"* — Analysts see masked account numbers; a privileged role sees the real value — same query, different result by role.
- *"Row-level security?"* — Row access policies filter rows per role — e.g. a region only sees its own portfolios.

---

## K24 · Integration with Azure

**Simple explanation (my stack).** On TCW, Snowflake runs on Azure. Data lands in **Azure Blob/ADLS**, orchestration is **Azure Data Factory** (plus my FastAPI ETL), identity via **Entra ID**, secrets in **Key Vault**, and BI on top (Power BI). Snowflake slots cleanly into the Azure estate.

**Follow-ups**
- *"How does ADF fit?"* — ADF orchestrates movement and staging; Snowflake does the heavy transformation and analytics.
- *"Why Snowflake over Azure Synapse then?"* — Chosen for its clean storage/compute separation and low ops — but I'd weigh Synapse if staying all-Microsoft mattered (see K29).

---

## K25 · Snowpark and in-database code

**Simple explanation.** **Snowpark** lets me run Python/Java/Scala **inside** Snowflake (DataFrame API and UDFs) so transformation and even ML run next to the data — no moving huge datasets out. Great for data-heavy Python logic that would be slow to export.

**Follow-ups**
- *"Snowpark vs my FastAPI ETL?"* — FastAPI for ingestion/validation and app-facing APIs; Snowpark for heavy in-warehouse transforms where moving data out is wasteful.
- *"Language?"* — Python is common — familiar to my data stack, running server-side in Snowflake.

---

## K26 · Snowflake Cortex and AI

**Simple explanation.** **Cortex** brings LLM and ML functions into Snowflake SQL (summarise, classify, embed, and vector search) so you can do AI on governed data without exporting it. It complements my Azure OpenAI / AI Foundry RAG work when the data already lives in Snowflake.

**Follow-ups**
- *"When Cortex vs Azure OpenAI?"* — Cortex when the data is in Snowflake and I want AI in-place with governance; Azure OpenAI/Foundry for the broader app-level RAG (see file 37).
- *"Vector search in Snowflake?"* — Yes — store embeddings and query them, keeping retrieval close to the governed data.

---

## K27 · Accessing Snowflake from an app

**Simple explanation (full-stack lens).** My apps reach Snowflake via connectors/drivers (Python connector, .NET/ODBC). For a user-facing app I don't hit Snowflake per click (latency/cost) — I precompute/aggregate into a serving store or cache, and use Snowflake for the heavy analytical queries behind reports.

**Follow-ups**
- *"Query Snowflake directly from the UI?"* — Rarely — too slow/costly per request; I serve aggregates from a fast store and reserve Snowflake for analytics.
- *"How from .NET/Python?"* — Official connectors with pooled connections and parameterised SQL — same discipline as any DB.

---

## K28 · Warehouse vs lakehouse

**Simple explanation.** A **data warehouse** (Snowflake) stores structured, curated data for fast SQL analytics. A **data lake** stores raw files cheaply. A **lakehouse** blends both (query lake files with warehouse-like features). Snowflake increasingly spans this with external tables and Iceberg support.

**Follow-ups**
- *"Warehouse, lake, lakehouse in one line?"* — Warehouse = curated & fast; lake = raw & cheap; lakehouse = both in one.
- *"Where does Snowflake sit?"* — A warehouse at heart, now reaching into lake/lakehouse territory via external/Iceberg tables.

---

## K29 · Snowflake vs Synapse and Databricks

**Simple explanation (decision lens).** **Snowflake** — simplest to run, great SQL analytics, clean storage/compute split. **Azure Synapse** — tight Azure integration, good if all-Microsoft. **Databricks** — strongest for big-data/Spark and ML/data-science. I choose by workload and ecosystem, not hype.

**Follow-ups**
- *"When Databricks over Snowflake?"* — Heavy Spark/ML and data-science pipelines — Databricks' sweet spot.
- *"When Synapse?"* — When staying fully in the Microsoft/Azure ecosystem and its integration outweigh Snowflake's simplicity.

---

## K30 · When NOT to use Snowflake

**Simple explanation (mature take).** Snowflake is for analytics, not everything. **Don't** use it as an OLTP database (many tiny fast writes — that's SQL Server), for low-latency single-row app lookups, or for tiny datasets where its cost/complexity isn't justified. Right tool for the workload.

**Follow-ups**
- *"Why not OLTP on Snowflake?"* — It's built for big analytical scans, not high-rate small transactions — SQL Server wins there (see file 36).
- *"Smallest sensible use?"* — If data and analytics are small, a relational DB is simpler and cheaper — don't over-engineer.

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| K1 | What it is | Managed cloud data warehouse for big OLAP analytics |
| K2 | Storage vs compute | Separated — many workloads on one data copy, no contention |
| K3 | Virtual warehouses | Sized compute clusters; auto-suspend saves money |
| K4 | Three layers | Storage + compute + services, each scales independently |
| K5 | Scaling | Scale up for big queries, out for many users |
| K6 | Cost model | Pay per-use; cost is a design lever architects control |
| K7 | Loading & JSON | COPY INTO + native semi-structured (VARIANT) support |
| K8 | Time Travel & cloning | Query the past, instant zero-copy clones, live sharing |
| K9 | Micro-partitions | Auto columnar chunks + metadata pruning (no indexes) |
| K10 | Clustering keys | Keep related rows together on huge tables for pruning |
| K11 | Caching | Result + local disk + metadata caches; repeats are free |
| K12 | Query tuning | Read Query Profile; scan less; avoid spilling |
| K13 | Cost tuning | Auto-suspend, right-size, resource monitors, scan less |
| K14 | Concurrency | Multi-cluster scales out for many users automatically |
| K15 | Loading options | COPY (batch), Snowpipe (continuous), streaming (rows) |
| K16 | Streams & Tasks | CDC + scheduled SQL = in-Snowflake pipelines |
| K17 | ELT & dbt | Load raw, transform in-Snowflake; dbt adds discipline |
| K18 | Semi-structured | VARIANT + FLATTEN query evolving JSON with SQL |
| K19 | Data modelling | Star schema (fact + dimensions) for fast analytics |
| K20 | External tables | Query lake files in place without loading them |
| K21 | Security & RBAC | Role hierarchy, SSO (Entra ID), encryption default |
| K22 | Data sharing | Zero-copy live sharing + Marketplace datasets |
| K23 | Governance | Dynamic masking + row access policies for compliance |
| K24 | Azure integration | Blob/ADLS + ADF + Entra ID + Key Vault + Power BI |
| K25 | Snowpark | Run Python/Java in-database next to the data |
| K26 | Cortex/AI | LLM/ML + vector search on governed data in SQL |
| K27 | App access | Connectors; serve aggregates, don't query per click |
| K28 | Warehouse vs lakehouse | Curated vs raw vs both; Snowflake spans via external/Iceberg |
| K29 | vs Synapse/Databricks | Snowflake simple; Synapse all-MS; Databricks big-data/ML |
| K30 | When not to use | Not OLTP, not low-latency lookups, not tiny data |

---

[← Concept: SQL Server](34-concept-sql-server.md) · [Home](README.md) · [Next → SQL Server vs Snowflake](36-concept-sqlserver-vs-snowflake.md)
