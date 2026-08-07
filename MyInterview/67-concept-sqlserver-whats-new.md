# 67 · Concept: SQL Server — What's New (Version Evolution) (30 questions)

[← .NET & C# What's New](66-concept-dotnet-whats-new.md) · [Home](README.md) · [Next → Azure Services What's New](68-concept-azure-whats-new.md)

This file explains **what is new in SQL Server** — version by version (2016 → 2017 → 2019 → 2022) — in simple English, with the *why it matters* and *how it beats the old way*. On the TCW reporting platform (Project A) SQL Server is the operational store, so version features directly affect performance, security and cost. Code is T-SQL.

> Simple one-liner: *"SQL Server ships every 2–3 years. The last decade's theme is: the engine tunes itself (Intelligent Query Processing), it reaches out to other data (PolyBase, Azure), and it hardens security (Always Encrypted, Ledger). I adopt features that fix a real pain, and I always check the compatibility level."*

**Jump to (the model):** [SW1 Release history](#sw1--sql-server-release-history) · [SW2 Editions](#sw2--editions-and-what-changed) · [SW3 Compatibility level](#sw3--compatibility-level--the-key-upgrade-lever) · [SW4 How I upgrade](#sw4--how-i-upgrade-safely) · [SW5 Support lifecycle](#sw5--support-and-end-of-life)
> **2016:** [SW6 Query Store](#sw6--query-store-2016) · [SW7 Always Encrypted](#sw7--always-encrypted-2016) · [SW8 Temporal tables](#sw8--temporal-tables-2016) · [SW9 JSON](#sw9--json-support-2016) · [SW10 Row-level security](#sw10--row-level-security--dynamic-data-masking-2016)
> **2017:** [SW11 Linux](#sw11--sql-server-on-linux-2017) · [SW12 Adaptive QP](#sw12--adaptive-query-processing-2017) · [SW13 Auto plan correction](#sw13--automatic-plan-correction-2017)
> **2019:** [SW14 Intelligent QP](#sw14--intelligent-query-processing-2019) · [SW15 Big Data Clusters/PolyBase](#sw15--polybase-and-data-virtualisation-2019) · [SW16 Accelerated DB recovery](#sw16--accelerated-database-recovery-2019) · [SW17 Memory-optimized tempdb](#sw17--tempdb-improvements-2019)
> **2022:** [SW18 Ledger](#sw18--ledger-2022) · [SW19 Azure Synapse Link](#sw19--azure-synapse-link-2022) · [SW20 Managed Instance link](#sw20--managed-instance-link-2022) · [SW21 Parameter-sensitive plans](#sw21--parameter-sensitive-plan-optimization-2022) · [SW22 Contained AGs](#sw22--contained-availability-groups-2022)
> **Cross-cutting:** [SW23 Columnstore evolution](#sw23--columnstore-index-evolution) · [SW24 In-memory OLTP](#sw24--in-memory-oltp) · [SW25 Security features](#sw25--the-security-story-over-time) · [SW26 HA/DR features](#sw26--hadr-features-over-time) · [SW27 Azure SQL vs box](#sw27--azure-sql-vs-boxed-sql-server)
> **Decisions:** [SW28 When to adopt a feature](#sw28--when-i-adopt-a-new-feature) · [SW29 Upgrade risks](#sw29--upgrade-risks-and-known-issues) · [SW30 My approach](#sw30--my-approach) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of "what's new in SQL Server" in plain English. Hold these ideas and every question below is a detail hanging off one of them.

**1. SQL Server ships every 2–3 years, and the version matters.** 2016, 2017, 2019, 2022 are the recent ones. Each adds engine, security and integration features. Knowing which version *and compatibility level* I'm on is the first fact — features and the query optimizer behave differently across them.

**2. The biggest theme is "the engine tunes itself".** From 2016's Query Store to 2017's Adaptive Query Processing to 2019's Intelligent Query Processing, SQL Server increasingly *fixes bad plans automatically*. Much of what a DBA did by hand is now built in.

**3. The second theme is "reach other data".** PolyBase and data virtualisation (2019) let SQL Server query external sources; Synapse Link and Managed Instance link (2022) connect the box to Azure analytics and the cloud without moving data.

**4. The third theme is "security hardening".** Always Encrypted (2016), Row-Level Security, Dynamic Data Masking, and Ledger (2022, tamper-evidence) turn the database into a much stronger control point — which matters enormously in a regulated firm like TCW.

**5. Compatibility level is the safe upgrade lever.** I can move a database to a new SQL Server but keep the *old* compatibility level so the query optimizer behaves as before — then raise it later, with Query Store watching for regressions. This decouples "install" from "change behaviour".

**6. Old way vs new way is the interview gold.** For each feature I can say the *before*: hand-tuning plans, encrypting in the app, home-grown history tables, big-bang failover; and the *after*: automatic plan correction, Always Encrypted, temporal tables, accelerated recovery.

**7. Azure SQL is the fastest-moving edition.** Azure SQL Database and Managed Instance get features *before* the boxed product. So "what's new" is really two tracks — the box (2016→2022) and the always-current cloud.

**8. I adopt for a real pain, not a checkbox.** A feature earns its place when it removes hand-tuning, closes a security gap, or cuts cost/latency on *my* workload. I test with Query Store before and after.

**The full-stack / architect lens:** the later Q&As go version-by-version (Query Store, Always Encrypted, temporal, JSON, Linux, Adaptive/Intelligent QP, PolyBase, Accelerated DB Recovery, Ledger, Synapse Link, parameter-sensitive plans) with old-vs-new T-SQL, plus columnstore and in-memory OLTP evolution, the security and HA/DR stories over time, Azure SQL vs box, and how I decide to adopt. They all trace back to the core: let the engine self-tune, keep data secure, and upgrade via compatibility level with Query Store as the safety net.

**One rule I never break:** *upgrade the engine and the compatibility level as separate steps, with Query Store watching — so a bad plan is caught and reverted, not shipped.*

---

## SW1 · SQL Server release history

**Simple explanation.** Recent versions: **2016, 2017, 2019, 2022**, each roughly two years apart, with cumulative updates in between. Each brings optimizer, security and integration features.

**Architect's view:** I track version + latest CU + compatibility level as a standing fact. On the reporting platform I stay on a modern, supported version so I get the self-tuning features.

**Follow-ups**
- *How do I check my version?* — I run a couple of `SERVERPROPERTY` queries — `@@VERSION` gives the friendly banner, but `ProductVersion`, `ProductLevel` and `Edition` are the machine-readable facts I record in the architecture register. The major number tells me the release (13=2016, 14=2017, 15=2019, 16=2022) and the level tells me the CU/patch state.
  ```sql
  SELECT @@VERSION;
  SELECT SERVERPROPERTY('ProductVersion')  AS Version,   -- e.g. 16.0.4120.1
         SERVERPROPERTY('ProductLevel')    AS Level,     -- e.g. RTM-CU12
         SERVERPROPERTY('Edition')         AS Edition;
  ```
- *Is 2022 the newest box release?* — Yes, 2022 is the newest boxed (installed) release at the time of writing. The important nuance is that Azure SQL Database and Managed Instance are *evergreen* — they get new engine features continuously, ahead of the box, so the cloud is effectively always "newer" than whatever the latest boxed version is. That is why I track the box on a version+CU cadence but treat Azure SQL as always-current.

---

## SW2 · Editions and what changed

**Simple explanation.** Editions: **Express** (free, small), **Standard** (mainstream), **Enterprise** (all features, scale/HA). A big shift in **2016 SP1** made many former Enterprise-only programmability features (columnstore, in-memory OLTP, partitioning) available in Standard — same code across editions.

**Architect's view:** that change let me write one set of features and choose the edition by scale/HA needs, not by which T-SQL I could use.

**Follow-ups**
- *Enterprise-only now?* — After 2016 SP1 the split is mostly about *scale and availability* rather than *which T-SQL you can write*. Enterprise unlocks more cores and memory, online index rebuilds, resource governor, and advanced Always On HA (multiple synchronous replicas, read-scale), while Standard is capped (e.g. lower memory/core limits and fewer replicas). So my code is portable across editions — I choose the edition by how big and how highly-available the workload must be.
- *Developer edition?* — Developer edition is free and has the *full* Enterprise feature set, but it is licensed for non-production (dev/test) use only. That is what I install locally and in CI so I can validate Enterprise-only features (like online operations or partitioning) before they ship to a licensed production server — no surprises at deploy time.

---

## SW3 · Compatibility level — the key upgrade lever

**Simple explanation.** **Compatibility level** controls which optimizer/behaviour a *database* uses, independent of the server version. I can run a DB on SQL 2022 but at compat level 140 (2017 behaviour), then raise it deliberately.

```sql
ALTER DATABASE Reporting SET COMPATIBILITY_LEVEL = 160; -- 2022 behaviour
```

**Old vs new.** Before, upgrading the server changed the optimizer immediately — risky. Now install and behaviour-change are separate steps.

**Architect's view:** my safe path: upgrade the engine, keep the old compat level, enable Query Store, then raise compat level and watch for regressed plans.

**Follow-ups**
- *What if a plan regresses after raising it?* — Query Store lets me force the old good plan, or I drop compat level back.
- *Levels?* — 130=2016, 140=2017, 150=2019, 160=2022.

---

## SW4 · How I upgrade safely

**Simple explanation.** My steps: back up; run the **Data Migration Assistant** to find breaking changes; upgrade the engine; keep the old compatibility level; turn on **Query Store**; raise compatibility level; watch Query Store for regressions and force plans if needed.

**Architect's view:** Query Store is the safety net — it records every plan and lets me revert a bad one in seconds. I never raise compat level without it on.

**Follow-ups**
- *Downtime?* — Minimised with an Availability Group rolling upgrade or a Managed Instance.
- *Rollback?* — Restore from backup, or drop compat level for behavioural issues.

---

## SW5 · Support and end of life

**Simple explanation.** Each version has ~5 years mainstream + ~5 years extended support. Running past end of support means no security patches — a compliance risk. (SQL Server 2012/2014 are already out of mainstream support.)

**Architect's view:** in a regulated firm, an out-of-support database engine is an audit finding. I plan upgrades before the deadline, not after.

**Follow-ups**
- *Option if I can't upgrade in time?* — Azure Extended Security Updates, or lift-and-shift to Azure SQL Managed Instance (which stays current).
- *How do I track it?* — A lifecycle date in the architecture register.

---

## SW6 · Query Store (2016)

**Simple explanation.** **Query Store** (2016) is a "flight recorder" for queries — it stores query text, execution plans and runtime stats over time, so I can see when a plan changed and **force** a known-good plan.

**Old vs new.** Before, diagnosing "it was fast yesterday, slow today" meant guesswork. Query Store shows the plan history and lets me pin the good one.

**Architect's view:** I turn Query Store on everywhere — it's the single best troubleshooting and upgrade-safety feature added in a decade.

**Follow-ups**
- *How to force a plan?* — `sp_query_store_force_plan`, or via SSMS reports.
- *Overhead?* — Small and configurable; well worth it.

---

## SW7 · Always Encrypted (2016)

**Simple explanation.** **Always Encrypted** keeps sensitive columns encrypted **end to end** — the data is encrypted in the client driver, so the SQL Server engine (and any DBA) never sees plaintext.

**Old vs new.** Older TDE encrypts data *at rest* on disk, but the engine sees plaintext in memory. Always Encrypted protects against the DBA and the server itself.

**Architect's view:** for regulated PII/financial columns this is the strongest option — the trade-off is limited querying on encrypted columns (equality only, unless using the enclave feature).

**Follow-ups**
- *TDE vs Always Encrypted?* — TDE = at-rest disk encryption; Always Encrypted = column-level, engine can't decrypt.
- *Can I range-query encrypted columns?* — Only with secure enclaves (2019+).

---

## SW8 · Temporal tables (2016)

**Simple explanation.** **System-versioned temporal tables** automatically keep a full history of row changes, so I can query data "as of" any past time.

```sql
SELECT * FROM Positions
FOR SYSTEM_TIME AS OF '2025-01-01T09:00:00';
```

**Old vs new.** Before, teams built history/audit tables with triggers by hand — error-prone. Temporal tables do it in the engine.

**Architect's view:** ideal for audit, point-in-time reporting and "who changed what when" in finance data.

**Follow-ups**
- *Where's the history stored?* — A linked history table the engine maintains.
- *Can I clean old history?* — Yes, with a retention policy.

---

## SW9 · JSON support (2016)

**Simple explanation.** 2016 added **JSON functions** — `FOR JSON`, `OPENJSON`, `JSON_VALUE`, `ISJSON` — to produce and shred JSON in T-SQL.

```sql
SELECT Id, Name FROM Customers FOR JSON PATH;
SELECT * FROM OPENJSON(@json) WITH (Id int, Name nvarchar(50));
```

**Old vs new.** Before, apps parsed/serialised JSON themselves. Now the DB can, which simplifies API shaping.

**Architect's view:** handy for flexible fields and API payloads, but I keep core relational data relational — JSON isn't a schema replacement.

**Follow-ups**
- *Is there a JSON data type?* — Historically stored as `nvarchar`; a native `json` type arrived in Azure SQL / 2025-era engines.
- *Can I index JSON?* — Yes, via computed columns on `JSON_VALUE`.

---

## SW10 · Row-Level Security & Dynamic Data Masking (2016)

**Simple explanation.** **Row-Level Security (RLS)** filters which rows a user can see via a security predicate. **Dynamic Data Masking (DDM)** masks column values (e.g. show `XXXX1234`) for non-privileged users.

**Old vs new.** Before, row filtering lived in application queries (easy to bypass); masking was manual. Now both are enforced in the engine.

**Architect's view:** RLS centralises "who sees which rows" (e.g. a fund manager sees only their funds). DDM is presentation-level, not real encryption — I pair it with proper access control.

**Follow-ups**
- *Is DDM secure against a determined user?* — No — it's obfuscation; use RLS/encryption for real protection.
- *RLS performance?* — The predicate joins into every query; I keep it index-friendly.

---

## SW11 · SQL Server on Linux (2017)

**Simple explanation.** **2017** brought SQL Server to **Linux** and **containers** — the same engine, now cross-platform.

**Old vs new.** SQL Server was Windows-only for two decades. Linux/containers cut licensing/hosting cost and fit DevOps pipelines.

**Architect's view:** running SQL Server in a container makes local dev and CI trivial — spin up a fresh DB per test run.

**Follow-ups**
- *Feature parity?* — Very high; a few Windows-specific features differ.
- *Do you run prod on Linux?* — It's viable; for TCW I often use Azure SQL instead of self-managing.

---

## SW12 · Adaptive Query Processing (2017)

**Simple explanation.** **Adaptive Query Processing (2017)** lets the optimizer adjust at runtime: **batch-mode memory grant feedback**, **adaptive joins** (pick hash vs nested loop based on actual rows), and **interleaved execution** for multi-statement functions.

**Old vs new.** Before, a bad row estimate baked a bad plan for the whole run. Now the engine can correct during/after execution.

**Architect's view:** fixes a classic pain — skewed data causing wrong join choices — with no code change once compat level is right.

**Follow-ups**
- *Do I have to enable it?* — It comes with the right compatibility level (140+).
- *Adaptive joins — which mode?* — Defers hash vs nested-loop until it knows the actual row count.

---

## SW13 · Automatic plan correction (2017)

**Simple explanation.** Using Query Store, **automatic tuning** can detect a plan **regression** and automatically revert to the last good plan.

```sql
ALTER DATABASE Reporting SET AUTOMATIC_TUNING (FORCE_LAST_GOOD_PLAN = ON);
```

**Old vs new.** Before, a DBA manually spotted and forced plans. Now the engine can self-heal common regressions.

**Architect's view:** I enable this on the reporting DB — it catches plan regressions after stats/data changes automatically.

**Follow-ups**
- *Does it override my forced plans?* — It complements Query Store; I can still force manually.
- *Is it safe?* — It reverts *to a previously good plan*, so it's conservative.

---

## SW14 · Intelligent Query Processing (2019)

**Simple explanation.** **Intelligent Query Processing (IQP, 2019)** expanded self-tuning: **batch mode on rowstore**, **table variable deferred compilation**, **scalar UDF inlining** (a huge win — slow scalar functions run set-based), and **approximate count distinct**.

**Old vs new.** Scalar UDFs were notorious performance killers (row-by-row). 2019 inlines them into the query so they run fast — often a massive speedup with zero rewrite.

**Architect's view:** IQP is the headline reason to move to 2019+ compat level — real speed on existing code. I test with Query Store to confirm.

**Follow-ups**
- *Table variable deferred compilation?* — The optimizer waits to see actual row counts instead of assuming 1 row.
- *Do all UDFs inline?* — Most scalar ones; some patterns are excluded.

---

## SW15 · PolyBase and data virtualisation (2019)

**Simple explanation.** **PolyBase** (expanded in 2019) lets SQL Server **query external data** — other SQL Servers, Oracle, MongoDB, Azure Storage — as if it were local tables, without copying it.

**Old vs new.** Before, integrating external data meant an ETL copy. Data virtualisation queries it in place.

**Architect's view:** useful for occasional cross-source queries; for heavy analytics I still land data in Snowflake (Project A) rather than virtualise everything.

**Follow-ups**
- *Big Data Clusters?* — The 2019 BDC feature is retired; PolyBase data virtualisation lives on.
- *Performance of virtualised queries?* — Depends on the source; not a replacement for a proper warehouse.

---

## SW16 · Accelerated Database Recovery (2019)

**Simple explanation.** **Accelerated Database Recovery (ADR, 2019)** makes crash recovery and long-transaction rollback **near-instant**, using a persisted version store instead of replaying the whole log.

**Old vs new.** Before, rolling back a huge transaction or recovering after a crash could take a very long time (log replay). ADR makes it fast and predictable.

**Architect's view:** for a platform with a hard daily deadline, predictable fast recovery is a reliability feature I value highly.

**Follow-ups**
- *Cost of ADR?* — Extra version-store storage; usually well worth it.
- *Enabled by default?* — On by default in Azure SQL; opt-in on the box.

---

## SW17 · tempdb improvements (2019)

**Simple explanation.** 2019 reduced tempdb contention with **memory-optimized tempdb metadata** and better default file handling — a common bottleneck on busy servers.

**Architect's view:** tempdb contention used to need manual trace flags and file tuning. 2019 addresses the metadata hotspots directly.

**Follow-ups**
- *Still need multiple tempdb files?* — Yes, setup now configures sensible defaults automatically.
- *When does this help most?* — High-concurrency workloads hammering temp objects.

---

## SW18 · Ledger (2022)

**Simple explanation.** **Ledger** (2022) adds **tamper-evidence** — cryptographic hashing (blockchain-style) so you can prove data hasn't been altered. Updatable ledger tables keep a verifiable history.

**Old vs new.** Before, proving "this record was never tampered with" needed external systems. Now it's built into the engine.

**Architect's view:** valuable for audit/compliance in finance — a provable trail without a separate blockchain platform.

**Follow-ups**
- *Is it a blockchain?* — It uses similar hashing/Merkle-tree ideas but stays a relational DB.
- *Performance impact?* — Some overhead for the hashing; I apply it to the tables that need proof, not everything.

---

## SW19 · Azure Synapse Link (2022)

**Simple explanation.** **Synapse Link for SQL** (2022) streams operational data to **Azure Synapse** for analytics in near real time — no custom ETL.

**Old vs new.** Before, moving OLTP data to analytics meant a scheduled ETL pipeline. Synapse Link keeps analytics fresh automatically.

**Architect's view:** conceptually similar to my SQL→Snowflake split (Project A), but native to Azure — I'd weigh it against my existing ADF/Airflow pipeline.

**Follow-ups**
- *Real-time?* — Near real-time change feed.
- *Replaces my warehouse?* — It feeds one (Synapse); I still choose the right analytics store.

---

## SW20 · Managed Instance link (2022)

**Simple explanation.** **Managed Instance link** (2022) creates a near-real-time replica between on-prem SQL Server and **Azure SQL Managed Instance** — for migration, DR, or offloading reads to Azure.

**Old vs new.** Before, hybrid replication to Azure was complex. This gives a clean, supported link.

**Architect's view:** a low-risk migration path — replicate to Azure, validate, then cut over.

**Follow-ups**
- *Direction?* — Originally one-way (box→MI), with failback capabilities added.
- *Use for DR?* — Yes — a warm standby in Azure.

---

## SW21 · Parameter Sensitive Plan optimization (2022)

**Simple explanation.** **Parameter Sensitive Plan (PSP) optimization** (2022) lets one parameterised query keep **multiple plans** for different parameter value ranges — fixing the classic "parameter sniffing" problem.

**Old vs new.** Before, a query cached one plan based on the first parameter value — great for that value, terrible for skewed ones. PSP keeps several plans.

**Architect's view:** a big automatic win for skewed data (e.g. one huge customer among many small ones) — previously I used `OPTIMIZE FOR` or `RECOMPILE` hints by hand.

**Follow-ups**
- *Do I still need query hints?* — Less often; PSP handles many cases automatically at compat 160.
- *How many plans does it keep?* — A small bounded set based on value distribution.

---

## SW22 · Contained Availability Groups (2022)

**Simple explanation.** **Contained AGs** (2022) include system objects (logins, jobs, permissions) *inside* the availability group, so they fail over with the databases — no more manually syncing logins across replicas.

**Old vs new.** Before, a failover could break because a login or SQL Agent job existed on the primary but not the secondary. Contained AGs fix that.

**Architect's view:** removes a common operational footgun in HA setups — fewer "it failed over but nothing works" incidents.

**Follow-ups**
- *Does it replace normal AGs?* — It's an option that adds the contained system DB.
- *Migration?* — Plan it; converting existing AGs needs care.

---

## SW23 · Columnstore index evolution

**Simple explanation.** Columnstore indexes (analytics-oriented, compressed, batch-mode) have improved every release: updatable clustered columnstore (2016), better batch mode, and batch mode extended to rowstore (2019). Great for large aggregations.

**Old vs new.** Before columnstore, big aggregate queries scanned row-by-row. Columnstore + batch mode process thousands of rows at once, hugely faster for reporting.

**Architect's view:** on reporting tables with millions of rows, a columnstore index can turn a minutes-long aggregation into seconds.

**Follow-ups**
- *OLTP or OLAP?* — Columnstore is for analytics/aggregations; rowstore for point lookups. Hybrids exist.
- *Can a table have both?* — Yes — a rowstore table with a nonclustered columnstore index for reporting.

---

## SW24 · In-Memory OLTP

**Simple explanation.** **In-Memory OLTP** (memory-optimized tables + natively compiled procedures, since 2014, improved since) removes locking/latching for extreme write throughput on hot tables.

**Old vs new.** Before, high-contention tables hit lock bottlenecks. Memory-optimized tables use optimistic concurrency — no locks.

**Architect's view:** a specialist tool for hot spots (session state, staging, high-ingest). I don't make everything memory-optimized — I target the bottleneck.

**Follow-ups**
- *Durability?* — Can be fully durable or schema-only (fast, non-persistent).
- *Memory cost?* — The table lives in RAM; I size for it.

---

## SW25 · The security story over time

**Simple explanation.** Security features accumulated: **TDE** (at-rest), **Always Encrypted** (2016, end-to-end columns), **RLS + DDM** (2016), **secure enclaves** (2019, richer queries on encrypted data), **Ledger** (2022, tamper-evidence). Together they make SQL Server a strong control point.

**Architect's view:** in a regulated firm I layer these — TDE for the disk, Always Encrypted for the most sensitive columns, RLS for access scoping, Ledger for provable audit.

**Follow-ups**
- *Where do you start?* — TDE + least-privilege + auditing as the baseline, then add column encryption/RLS by data sensitivity.
- *Key management?* — Azure Key Vault / HSM-backed keys.

---

## SW26 · HA/DR features over time

**Simple explanation.** High-availability/disaster-recovery evolved: **Always On Availability Groups** (2012, matured since), read-scale replicas, **distributed AGs**, **Accelerated DB Recovery** (2019), **Contained AGs** (2022), and cloud links (2022).

**Architect's view:** I pick HA by RTO/RPO — AGs for automatic failover and read offload, ADR for fast recovery, and an Azure link/replica for DR.

**Follow-ups**
- *AG vs Failover Cluster Instance?* — AG replicates databases (can read secondaries); FCI shares storage. AGs are more flexible.
- *Read offload?* — Route reporting reads to a readable secondary.

---

## SW27 · Azure SQL vs boxed SQL Server

**Simple explanation.** **Azure SQL Database** (fully managed, serverless options), **Azure SQL Managed Instance** (near-full engine, managed), and **SQL on a VM** (full control) are the cloud forms. Azure SQL gets features **first** and handles patching/HA for me.

**Old vs new.** The boxed product is versioned (2016→2022); Azure SQL is **evergreen** — always current, no version to upgrade.

**Architect's view:** for new TCW workloads I lean to Managed Instance (compatibility + managed ops) unless I need OS-level control (then SQL on a VM).

**Follow-ups**
- *Which is closest to the box?* — Managed Instance (highest compatibility).
- *Serverless?* — Azure SQL DB can auto-pause/scale — great for spiky/dev workloads and cost.

---

## SW28 · When I adopt a new feature

**Simple explanation.** My rule: adopt a feature when it **removes hand-tuning**, **closes a security gap**, or **cuts cost/latency** on my actual workload — and I prove it with Query Store before/after.

**Architect's view:** many 2019+ features (IQP, PSP, ADR) are "free wins" gated by compatibility level, so adopting them is mostly a safe compat-level raise with monitoring.

**Follow-ups**
- *First thing you turn on after an upgrade?* — Query Store, then automatic plan correction.
- *A feature you skip often?* — In-memory OLTP unless there's a genuine contention hot spot.

---

## SW29 · Upgrade risks and known issues

**Simple explanation.** Risks: **plan regressions** when raising compatibility level, **deprecated features/syntax**, **cardinality estimator changes** (the 2014+ CE can help or hurt), and **collation/edition** mismatches. The **Data Migration Assistant** flags most of these.

**Architect's view:** I mitigate with DMA analysis, staged compat-level raises, Query Store forcing, and a tested rollback (restore/backup). The cardinality estimator is the classic surprise — Query Store catches it.

**Follow-ups**
- *The CE issue specifically?* — If the new estimator regresses a query, I force the old plan or use the legacy CE hint while I tune.
- *Deprecated T-SQL?* — DMA lists it; I fix before upgrading.

---

## SW30 · My approach

**Simple explanation.** I keep SQL Server (or Azure SQL) **supported and modern**, upgrade the engine and compatibility level as **separate, monitored steps**, turn on **Query Store** as the safety net, and adopt features (IQP, PSP, ADR, Ledger, encryption) when they fix a real pain on my workload. For every feature I know the old way and the new way.

**Architect's view:** the last decade of SQL Server is about the engine tuning itself, reaching other data, and hardening security — all of which reduce manual DBA toil and risk. On the TCW platform I lean on these to keep the reporting store fast, auditable and reliable inside the daily deadline.

**Follow-ups**
- *One-sentence philosophy?* — "Let the engine self-tune, keep the data provably secure, and upgrade behind Query Store."
- *Box or cloud going forward?* — New workloads default to Azure SQL/Managed Instance for evergreen features and managed ops.

---

## Section index

| ID | Topic | Core message |
|----|-------|--------------|
| SW1 | Release history | 2016/2017/2019/2022, ~2 yrs apart |
| SW2 | Editions | 2016 SP1 opened programmability features to Standard |
| SW3 | Compatibility level | The safe lever: install ≠ behaviour change |
| SW4 | Upgrade safely | DMA → upgrade → Query Store → raise compat → watch |
| SW5 | Support/EOL | Out-of-support = security/compliance risk |
| SW6 | Query Store | Plan flight-recorder; force good plans |
| SW7 | Always Encrypted | End-to-end column encryption; engine can't see it |
| SW8 | Temporal tables | Automatic row history; query "as of" |
| SW9 | JSON | FOR JSON / OPENJSON in T-SQL |
| SW10 | RLS & DDM | Row filtering + column masking in the engine |
| SW11 | Linux (2017) | Cross-platform + containers |
| SW12 | Adaptive QP | Runtime plan adjustments (adaptive joins) |
| SW13 | Auto plan correction | Self-heal plan regressions via Query Store |
| SW14 | Intelligent QP (2019) | Scalar UDF inlining + batch mode = free speed |
| SW15 | PolyBase | Query external data without copying |
| SW16 | Accelerated DB Recovery | Near-instant recovery/rollback |
| SW17 | tempdb (2019) | Reduced metadata contention |
| SW18 | Ledger (2022) | Tamper-evident, provable history |
| SW19 | Synapse Link | Near-real-time OLTP→analytics, no ETL |
| SW20 | Managed Instance link | Hybrid replica to Azure for migrate/DR |
| SW21 | PSP optimization (2022) | Multiple plans fix parameter sniffing |
| SW22 | Contained AGs | Logins/jobs fail over with the databases |
| SW23 | Columnstore | Compressed, batch-mode analytics speed |
| SW24 | In-Memory OLTP | Lock-free extreme write throughput (targeted) |
| SW25 | Security over time | TDE + Always Encrypted + RLS + Ledger layered |
| SW26 | HA/DR over time | AGs, ADR, contained AGs, cloud links |
| SW27 | Azure SQL vs box | Cloud is evergreen; MI closest to the box |
| SW28 | When to adopt | Fix real pain; prove with Query Store |
| SW29 | Upgrade risks | Plan/CE regressions; DMA + Query Store mitigate |
| SW30 | My approach | Self-tune, secure, upgrade behind Query Store |

---

[← .NET & C# What's New](66-concept-dotnet-whats-new.md) · [Home](README.md) · [Next → Azure Services What's New](68-concept-azure-whats-new.md)
