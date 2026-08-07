# 64 · Concept: SQL Database Performance Tuning (30 questions)

[← Web API / C# Performance Tuning](63-concept-webapi-performance.md) · [Home](README.md) · [Next → Microservices / System Architecture Performance](65-concept-microservices-performance.md)

This file explains **how I make SQL databases fast** — in simple English and real depth. I answer from project A, where TCW's reporting queries on SQL Server (and analytics on Snowflake) had to hit a hard deadline: *"the report is ready before the US market opens."* A slow query there is a missed deadline.

> Simple one-liner: *"Database speed is mostly **indexing** (help the engine find rows fast), **good queries** (ask for less, in a way the engine can optimise), and **reading the execution plan** to see what's actually slow. I measure with the plan first — I never guess at indexes."*

## Concepts first — the whole idea before the questions

**Why queries get slow.** Almost always one of: (1) **missing or wrong indexes** (the engine scans the whole table instead of seeking), (2) **badly written queries** (SELECT *, functions on columns, over-fetching, N+1 from the app), (3) **locking/blocking** under concurrency, or (4) **too much data** with no partitioning/archiving strategy. Fix the right one and it flies.

**The mental model — how the engine runs a query.** SQL is *declarative*: you say *what* you want, the **query optimizer** decides *how* (the **execution plan**) using **statistics** about your data. An **index** is like a book's index — it lets the engine **seek** straight to rows instead of **scanning** every page. Reading the plan tells you whether you got a fast **seek** or a slow **scan**.

```
SQL query → optimizer (+ statistics) → execution plan → seek (fast) or scan (slow)
            good indexes + good SQL make the optimizer pick a seek
```

**The golden method (never changes):** **measure the execution plan → find the biggest operator (scan, sort, spill) → fix it (index/rewrite) → re-check the plan.** I read the actual plan and query stats before adding any index — wrong indexes cost writes and space for no gain.

**OLTP vs OLAP — different tuning.** **OLTP** (transactional, many small reads/writes — SQL Server operational DB) tunes for point lookups, narrow indexes, short transactions. **OLAP** (analytics, big aggregations — Snowflake) tunes for scanning large sets efficiently (columnar storage, clustering, MPP). On TCW I deliberately split the two.

**Jump to:** [QP1 What makes a query slow](#qp1--what-makes-a-query-slow) · [QP2 Execution plan](#qp2--the-execution-plan) · [QP3 Indexes](#qp3--how-indexes-work) · [QP4 Clustered vs non-clustered](#qp4--clustered-vs-non-clustered) · [QP5 Covering index](#qp5--covering-indexes) · [QP6 Composite index order](#qp6--composite-index-column-order) · [QP7 Seek vs scan](#qp7--seek-vs-scan) · [QP8 SARGability](#qp8--sargable-queries) · [QP9 Statistics](#qp9--statistics) · [QP10 SELECT *](#qp10--avoid-select-star)
> [QP11 Joins](#qp11--join-performance) · [QP12 N+1 from app](#qp12--n1-from-the-application) · [QP13 Pagination](#qp13--efficient-pagination) · [QP14 Parameter sniffing](#qp14--parameter-sniffing) · [QP15 Locking/blocking](#qp15--locking-and-blocking) · [QP16 Isolation levels](#qp16--isolation-levels) · [QP17 Deadlocks](#qp17--deadlocks) · [QP18 Batching writes](#qp18--batching-and-bulk-operations) · [QP19 Temp tables/CTEs](#qp19--temp-tables-vs-ctes) · [QP20 Stored procedures](#qp20--stored-procedures)
> [QP21 Partitioning](#qp21--partitioning-large-tables) · [QP22 Archiving](#qp22--archiving-and-data-growth) · [QP23 Caching](#qp23--caching-and-materialised-views) · [QP24 Index maintenance](#qp24--index-maintenance) · [QP25 Read replicas](#qp25--read-replicas-and-scaling) · [QP26 OLTP vs OLAP](#qp26--oltp-vs-olap-tuning) · [QP27 Snowflake tuning](#qp27--snowflake-warehouse-tuning) · [QP28 Anti-patterns](#qp28--performance-anti-patterns) · [QP29 A real fix](#qp29--a-real-fix-story) · [QP30 My approach](#qp30--my-approach) · [Section index](#section-index)

---

## QP1 · What makes a query slow?

**Simple explanation.** Usually: **missing/wrong indexes** (full-table scans), **bad SQL** (SELECT *, functions on indexed columns, over-fetching), **locking/blocking** under load, or **too much data** with no partitioning. I read the **execution plan** to see which one — the plan doesn't lie.

**Follow-ups**
- *"First move?"* — Look at the actual execution plan and query stats — never guess.
- *"Most common?"* — A missing index causing a table scan, or a non-SARGable predicate.

---

## QP2 · The execution plan

**Simple explanation.** The **execution plan** is the engine's step-by-step recipe for running a query — which indexes it used, seeks vs scans, joins, sorts. I read the **actual** plan to find the most expensive operator (a big scan, a sort spilling to disk) and target *that*.

**Follow-ups**
- *"Estimated vs actual?"* — Actual has real row counts — mismatches hint at stale statistics.
- *"What screams 'fix me'?"* — A table/clustered-index scan on a big table; a sort/hash spill.

---

## QP3 · How indexes work

**Simple explanation.** An **index** is a sorted structure (usually a B-tree) that lets the engine **seek** to rows fast, like a book's index — instead of reading every page (a scan). The right index turns a slow scan into a fast seek. But each index costs storage and slows writes, so I add them deliberately.

**Follow-ups**
- *"Cost of an index?"* — Extra storage + slower inserts/updates (index must be maintained).
- *"How many?"* — Enough to cover key queries — not one per column "just in case."

---

## QP4 · Clustered vs non-clustered

**Simple explanation.** A **clustered index** *is* the table sorted by that key (one per table — usually the primary key). A **non-clustered index** is a separate structure pointing back to rows. I choose the clustered key carefully (narrow, increasing, common range key) because everything hangs off it.

**Follow-ups**
- *"Good clustered key?"* — Narrow, unique, ever-increasing (avoids fragmentation/page splits).
- *"Non-clustered use?"* — For other common search/join/sort columns.

---

## QP5 · Covering indexes

**Simple explanation.** A **covering index** includes all columns a query needs (key + `INCLUDE` columns), so the engine answers the query **from the index alone** — no extra lookup back to the table. Huge win for hot read queries. On TCW I covered the report's key filter+select columns.

**Follow-ups**
- *"Key vs INCLUDE?"* — Key columns for filtering/ordering; INCLUDE for extra output columns.
- *"Trade-off?"* — Wider index = more storage/write cost; cover the queries that matter.

---

## QP6 · Composite index column order

**Simple explanation.** In a **multi-column index**, order matters. Put the **most selective / equality-filtered** columns first, then range/sort columns. The engine can only use the index efficiently left-to-right (leftmost-prefix rule). Wrong order = the index isn't used.

**Follow-ups**
- *"Rule of thumb?"* — Equality columns first, then range, then sort/output.
- *"Leftmost prefix?"* — An index on (A,B) helps queries on A or A+B, not B alone.

---

## QP7 · Seek vs scan

**Simple explanation.** A **seek** jumps straight to the rows it needs (fast, uses an index); a **scan** reads the whole table/index (slow on big tables). My goal is to turn scans into seeks with the right index and a SARGable query. Small tables scan fine — it's big-table scans that hurt.

**Follow-ups**
- *"Always avoid scans?"* — No — for small tables or when reading most rows, a scan is fine.
- *"Turn scan into seek?"* — Add a matching index + write a SARGable predicate.

---

## QP8 · SARGable queries

**Simple explanation.** **SARGable** (Search-ARGument-able) means the engine can use an index for the predicate. Wrapping a column in a **function** (`WHERE YEAR(date)=2024`) or leading wildcard (`LIKE '%x'`) breaks index use. I rewrite to keep the column bare (`WHERE date >= '2024-01-01' AND date < '2025-01-01'`).

**Follow-ups**
- *"Classic non-SARGable?"* — Function on the column, implicit type conversion, leading `%`.
- *"Fix?"* — Move logic off the column; use range predicates; match types.

---

## QP9 · Statistics

**Simple explanation.** The optimizer uses **statistics** (data distribution) to estimate rows and pick a plan. **Stale statistics** → bad estimates → bad plans (e.g. choosing a scan). I keep statistics updated (auto-update on, or manual after big data changes) so plans stay good.

**Follow-ups**
- *"Symptom of stale stats?"* — Big gap between estimated and actual rows in the plan.
- *"Fix?"* — `UPDATE STATISTICS` / rebuild; ensure auto-update is on.

---

## QP10 · Avoid SELECT *

**Simple explanation.** `SELECT *` fetches every column — more I/O, more network, and it prevents **covering indexes** from working. I select only the columns I need, which shrinks payloads and lets narrow indexes cover the query.

**Follow-ups**
- *"Why it hurts indexes?"* — A covering index can't include every column cheaply.
- *"Also app impact?"* — More data serialised/transferred than needed.

---

## QP11 · Join performance

**Simple explanation.** Joins are fast when **join columns are indexed** and types match. The engine picks a join type (nested loop for small, hash for large, merge for sorted). I make sure foreign-key/join columns are indexed and avoid joining on computed/converted values.

**Follow-ups**
- *"Slow join cause?"* — Unindexed join column → scan; type mismatch → conversion.
- *"Join types?"* — Nested loop (small), hash (large unsorted), merge (both sorted).

---

## QP12 · N+1 from the application

**Simple explanation.** The app-side **N+1** (one query then one per row) floods the DB with tiny queries. The database *looks* fine per query but is overwhelmed by volume. I fix it at the app (eager load/one query) — the DB's job is to serve one efficient query, not hundreds ([file 63 WP5](63-concept-webapi-performance.md#wp5--the-n1-problem)).

**Follow-ups**
- *"See it in DB?"* — Query store shows the same tiny query executed thousands of times.
- *"Fix side?"* — Application (Include/join/projection), not more indexes.

---

## QP13 · Efficient pagination

**Simple explanation.** `OFFSET`/`FETCH` gets slow on deep pages because the engine still reads and skips all prior rows. **Keyset (seek) pagination** — `WHERE id > @lastId ORDER BY id` — stays fast because it seeks to the next page directly using an index.

**Follow-ups**
- *"When offset is fine?"* — Shallow pages / small tables.
- *"Keyset requirement?"* — A stable, indexed ordering key.

---

## QP14 · Parameter sniffing

**Simple explanation.** SQL Server caches a plan based on the **first parameter value** it sees. If that value is atypical, later executions with different values get a bad plan. Fixes: `OPTIMIZE FOR`, `RECOMPILE`, or restructuring — used carefully after confirming it's the cause.

**Follow-ups**
- *"Symptom?"* — A proc fast for some inputs, slow for others, unpredictably.
- *"Fix options?"* — `OPTION (RECOMPILE)`, `OPTIMIZE FOR UNKNOWN`, or local variables — measure trade-offs.

---

## QP15 · Locking and blocking

**Simple explanation.** Databases use **locks** to keep data consistent. Under load, one transaction can **block** others (they wait), causing slowness that looks like a "slow query." I keep transactions **short**, touch rows in a consistent order, and use the right isolation level to reduce blocking.

**Follow-ups**
- *"Diagnose?"* — Look at blocking chains / wait stats — lock waits, not CPU.
- *"Reduce it?"* — Short transactions; proper indexes (less to lock); appropriate isolation.

---

## QP16 · Isolation levels

**Simple explanation.** **Isolation levels** trade consistency vs concurrency. Higher (Serializable) = more locking/blocking; lower (Read Committed Snapshot / RCSI) lets readers not block writers using **row versioning**. For read-heavy reporting I often use **RCSI** so reports don't block or get blocked.

**Follow-ups**
- *"RCSI benefit?"* — Readers see a consistent snapshot without blocking writers.
- *"Cost?"* — Version store in tempdb — monitor it.

---

## QP17 · Deadlocks

**Simple explanation.** A **deadlock** is two transactions each waiting on a lock the other holds — the engine kills one. I prevent them by accessing objects in a **consistent order**, keeping transactions short, and using the right indexes so less is locked. I read the deadlock graph to find the cycle.

**Follow-ups**
- *"Prevent?"* — Consistent access order; short transactions; appropriate isolation.
- *"Handle in app?"* — Retry the deadlock victim (transient) with backoff.

---

## QP18 · Batching and bulk operations

**Simple explanation.** Row-by-row inserts/updates are slow (per-statement overhead + logging). I **batch** them (multi-row inserts, `MERGE`, table-valued parameters) or use **bulk copy** (`SqlBulkCopy`) for large loads — my ETL loads to Snowflake use bulk/staged loads, not row-by-row.

**Follow-ups**
- *"Bulk tool?"* — `SqlBulkCopy` / bulk insert / staged loads for big volumes.
- *"Batch size?"* — Tune it — too big bloats the log; too small keeps overhead.

---

## QP19 · Temp tables vs CTEs

**Simple explanation.** A **CTE** is a named subquery (readability), not a stored result — it can be re-evaluated. A **temp table** materialises intermediate results (with statistics), which can be faster for large, reused intermediate sets. I choose based on size and reuse, checking the plan.

**Follow-ups**
- *"CTE performance myth?"* — A CTE isn't automatically cached — don't assume it's faster.
- *"When temp table?"* — Large intermediate set reused multiple times — stats help the optimizer.

---

## QP20 · Stored procedures

**Simple explanation.** **Stored procedures** can help performance via cached, reusable plans and by keeping set-based logic close to the data (less round-trips). I use them for heavy set-based operations, but keep business logic in the app where it belongs — the DB does data work well.

**Follow-ups**
- *"Benefit?"* — Plan reuse, set-based efficiency, fewer round-trips.
- *"Overuse risk?"* — Business logic buried in SQL is hard to test/maintain — balance.

---

## QP21 · Partitioning large tables

**Simple explanation.** **Partitioning** splits a huge table by a key (usually **date**) into physical chunks. Queries filtered by that key touch only relevant partitions (**partition elimination**), and old partitions can be archived/switched out fast. Essential as reporting data grows.

**Follow-ups**
- *"Partition key?"* — Usually date — matches how reports filter.
- *"Benefit beyond reads?"* — Fast archival via partition switching; easier maintenance.

---

## QP22 · Archiving and data growth

**Simple explanation.** Queries slow as tables grow forever. I **archive** cold data (move old rows to an archive table/store), keep the hot table lean, and use partitioning to make archival cheap. Keeping working data small keeps queries fast — the report only needs recent data hot.

**Follow-ups**
- *"Where archive?"* — Cheaper storage / a separate DB / the data lake (Snowflake).
- *"Why it helps?"* — Smaller hot table → smaller indexes → faster seeks.

---

## QP23 · Caching and materialised views

**Simple explanation.** For expensive, repeated aggregations I precompute: **indexed/materialised views** store the result so reads are instant, or I cache results in **Redis** at the app layer. Compute once, read many. On TCW, pre-aggregating heavy report figures beat recomputing per request.

**Follow-ups**
- *"Indexed view cost?"* — Maintained on write — use for read-heavy, aggregate-heavy data.
- *"App cache vs DB view?"* — App cache (Redis) for cross-request; DB view for query-time reuse.

---

## QP24 · Index maintenance

**Simple explanation.** Indexes **fragment** over time (inserts/updates), slowing seeks. I **rebuild/reorganise** fragmented indexes and keep **statistics** fresh on a maintenance schedule. Neglected maintenance is a silent, gradual slowdown.

**Follow-ups**
- *"Rebuild vs reorganise?"* — Rebuild for heavy fragmentation; reorganise for light — by thresholds.
- *"Automate?"* — Yes — scheduled jobs (or managed features on Azure SQL).

---

## QP25 · Read replicas and scaling

**Simple explanation.** When reads dominate (like reporting), I offload them to **read replicas** so heavy report queries don't slow the write workload. This scales reads horizontally. For true analytics scale I move to a columnar/MPP store (Snowflake) rather than straining the OLTP DB.

**Follow-ups**
- *"Replica lag?"* — Slightly stale reads — fine for most reporting.
- *"When Snowflake instead?"* — Large-scale analytics/aggregation over history ([QP27](#qp27--snowflake-warehouse-tuning)).

---

## QP26 · OLTP vs OLAP tuning

**Simple explanation.** **OLTP** (operational, many small txns) tunes for point seeks, narrow indexes, short transactions. **OLAP** (analytics, big scans/aggregations) tunes for columnar storage and parallel scans. They fight each other on one DB — which is exactly why I split **SQL Server (OLTP)** and **Snowflake (OLAP)** on TCW.

**Follow-ups**
- *"Why split?"* — Row-store point lookups vs column-store big aggregations need opposite designs.
- *"Cross-link?"* — The SQL/Snowflake decision ([CA1](53-case-study-a-investment-reporting.md)).

---

## QP27 · Snowflake / warehouse tuning

**Simple explanation.** In **Snowflake** (columnar, MPP) I tune differently: choose the right **warehouse size** (compute) for the workload, use **clustering keys** on huge tables, prune with partition-friendly filters, avoid `SELECT *`, and let **result caching** serve repeated queries. Scale compute up for a heavy batch, then down to save cost.

**Follow-ups**
- *"No indexes?"* — Snowflake uses micro-partitions + clustering, not classic indexes.
- *"Cost lever?"* — Right-size the warehouse and auto-suspend — performance *and* cost.

---

## QP28 · Performance anti-patterns

**Simple explanation.** Common traps: **no index on a filter/join column**, **functions on columns** (non-SARGable), **SELECT ***, **app-side N+1**, **long transactions** (blocking), **OFFSET on deep pages**, and **stale statistics**. Each has a known fix; the plan reveals which you've hit.

**Follow-ups**
- *"Most common?"* — Missing index + non-SARGable predicate → table scan.
- *"Quick check?"* — Read the actual plan; look for scans and estimate/actual mismatches.

---

## QP29 · A real fix story

**The story.** On TCW (A), a report query kept **missing the pre-market deadline**. I pulled the **actual execution plan** — a big **table scan** and a costly **sort spilling to disk**. Fixes, in order: added a **covering index** on the filter+select columns (scan → seek), rewrote a **non-SARGable** `WHERE YEAR(date)=` into a **range** predicate, replaced `SELECT *` with the needed columns, and moved the heavy history aggregation to **Snowflake** (OLAP) instead of straining SQL Server. Re-checked the plan and timed it — the query went from minutes to seconds and comfortably beat the deadline.

**Lesson.** *"I read the plan first, fixed the exact operator that hurt, and split OLTP/OLAP so each database did what it's good at."*

**Follow-ups**
- *"Single biggest win?"* — The covering index turning the scan into a seek.
- *"Cross-link?"* — Same discipline as the DB deep dive ([PD1–PD2](19-performance-deep-dive.md)).

---

## QP30 · My approach

**How I answer (the whole picture).** *"I tune databases with evidence, not guesses. I start by reading the **actual execution plan** and query stats to find the expensive operator — usually a **scan** that should be a **seek**. Then I add the right **index** (often a **covering** one, with correct **composite column order**), make the query **SARGable** (no functions on columns), stop **`SELECT *`**, and fix any app-side **N+1**. For concurrency I keep transactions short, pick the right **isolation level** (RCSI for reporting), and prevent **deadlocks** with consistent access order. As data grows I **partition** by date, **archive** cold data, and **pre-aggregate** hot report figures (indexed views or Redis). And I match the **store to the workload** — which is exactly why TCW runs **OLTP on SQL Server and OLAP on Snowflake**. On the reporting deadline, reading the plan and adding one covering index took a query from minutes to seconds. I always **re-check the plan** to prove the fix."*

**Follow-ups**
- *"One lever if forced?"* — The right index guided by the execution plan.
- *"Index everything?"* — No — indexes cost writes/space; add only what the plan and real queries justify.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| QP1 | What's slow | Missing index, bad SQL, blocking, too much data |
| QP2 | Execution plan | Read the actual plan; find the costly operator |
| QP3 | Indexes | Seek vs scan; indexes cost writes/space |
| QP4 | Clustered vs non | Clustered = table order; choose key well |
| QP5 | Covering index | Answer query from the index alone |
| QP6 | Composite order | Equality first, then range/sort |
| QP7 | Seek vs scan | Turn big-table scans into seeks |
| QP8 | SARGable | No functions/leading wildcard on columns |
| QP9 | Statistics | Stale stats → bad plans; keep fresh |
| QP10 | SELECT * | Fetch only needed columns |
| QP11 | Joins | Index join columns; match types |
| QP12 | App N+1 | Fix in app; DB serves one good query |
| QP13 | Pagination | Keyset over deep OFFSET |
| QP14 | Param sniffing | Cached plan for atypical value |
| QP15 | Locking/blocking | Short txns; right isolation |
| QP16 | Isolation | RCSI so readers don't block |
| QP17 | Deadlocks | Consistent order; retry victim |
| QP18 | Batching | Bulk/batched writes, not row-by-row |
| QP19 | Temp vs CTE | Temp materialises with stats |
| QP20 | Stored procs | Plan reuse + set-based; balance logic |
| QP21 | Partitioning | By date; partition elimination |
| QP22 | Archiving | Keep hot table lean |
| QP23 | Materialised views | Precompute expensive aggregations |
| QP24 | Index maintenance | Rebuild/reorganise; fresh stats |
| QP25 | Read replicas | Offload heavy reads |
| QP26 | OLTP vs OLAP | Opposite tuning; split the stores |
| QP27 | Snowflake | Warehouse size, clustering, result cache |
| QP28 | Anti-patterns | No index, non-SARGable, SELECT *, N+1 |
| QP29 | Real fix | Covering index + SARGable + OLAP split |
| QP30 | My approach | Read plan → index/rewrite → re-check plan |

---

[← Web API / C# Performance Tuning](63-concept-webapi-performance.md) · [Home](README.md) · [Next → Microservices / System Architecture Performance](65-concept-microservices-performance.md)
