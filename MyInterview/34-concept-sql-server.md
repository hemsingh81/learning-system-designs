# 34 · Concept: SQL Server (30 questions)

[← Web API vs FastAPI](33-concept-webapi-vs-fastapi.md) · [Home](README.md) · [Next → Concept: Snowflake](35-concept-snowflake.md)

This file explains **Microsoft SQL Server** simply and in depth. On TCW (Project A) SQL Server is my **operational/transactional** store for time-critical reporting reads, and I do the query tuning myself, so I answer from real work.

> Simple one-liner: *"SQL Server is Microsoft's relational database. It stores data in tables with strict rules (a schema), guarantees correctness through transactions (ACID), and is built for fast, reliable reads and writes of live application data — an OLTP system."*

**Jump to (fundamentals):** [S1 What it is](#s1--what-is-sql-server) · [S2 Relational & keys](#s2--relational-model-and-keys) · [S3 Indexes](#s3--indexes-clustered-vs-non-clustered) · [S4 ACID & transactions](#s4--acid-and-transactions) · [S5 Joins](#s5--joins-explained-simply) · [S6 Query tuning](#s6--query-tuning-and-execution-plans) · [S7 SPs & T-SQL](#s7--stored-procedures-and-t-sql) · [S8 Normalization](#s8--normalization-and-when-to-break-it)
> **Query & T-SQL:** [S9 GROUP BY & aggregates](#s9--group-by-having-and-aggregates) · [S10 Subqueries & CTEs](#s10--subqueries-and-ctes) · [S11 Window functions](#s11--window-functions) · [S12 Views](#s12--views-and-indexed-views) · [S13 Functions](#s13--functions-scalar-vs-table-valued) · [S14 Triggers](#s14--triggers)
> **Performance & internals:** [S15 Index design](#s15--index-design-decisions) · [S16 Stats & parameter sniffing](#s16--statistics-and-parameter-sniffing) · [S17 Isolation & locking](#s17--isolation-levels-and-locking) · [S18 Deadlocks](#s18--deadlocks) · [S19 Execution plan reading](#s19--reading-execution-plans-deeper) · [S20 Partitioning](#s20--partitioning-large-tables)
> **Architecture & ops:** [S21 HA/DR](#s21--high-availability-and-disaster-recovery) · [S22 Backups](#s22--backups-and-recovery-models) · [S23 Security](#s23--security-and-encryption) · [S24 Azure SQL](#s24--azure-sql-options) · [S25 Scaling reads](#s25--scaling-reads-and-replicas) · [S26 Monitoring](#s26--monitoring-and-dmvs)
> **Full-stack lens:** [S27 EF Core & app](#s27--working-with-ef-core-from-the-app) · [S28 Migrations](#s28--schema-migrations) · [S29 Bulk & ETL](#s29--bulk-loading-and-etl) · [S30 Common mistakes](#s30--common-mistakes-i-watch-for) · [Section index](#section-index)

---

## Concepts first — the whole idea before the questions

Before the Q&As, here is the whole mental model of SQL Server in plain English. On TCW (A) SQL Server is my **operational/transactional** store for time-critical reporting reads, and I do the query tuning myself, so this is how I actually think about it. Hold these ideas and every question below is a detail hanging off one of them.

**1. It's a relational database for OLTP.** Data lives in **tables** (rows and columns) that relate to each other, queried with **T-SQL**. It's built for **OLTP** — lots of small, fast, correct reads and writes of live application data. Correctness and consistency come first. Heavy history goes to Snowflake instead.

**2. Keys and the relational model.** Primary keys identify rows, foreign keys enforce relationships, and a schema sets the rules. This structure is what lets the engine guarantee integrity and join tables reliably — it's the foundation everything else sits on.

**3. Indexes are how the engine finds data fast.** A **clustered** index *is* the table's physical order; **non-clustered** indexes are side lookups. The right index turns a table scan into a seek. Wrong or missing indexes are the number-one cause of slow queries I fix on A.

**4. ACID and transactions guarantee correctness.** A transaction is all-or-nothing — Atomic, Consistent, Isolated, Durable. It's why money never half-moves. Isolation levels and locking control how concurrent transactions see each other, and that trade-off is where correctness meets concurrency.

**5. Execution plans tell the truth.** When a query is slow, I read the **execution plan** — it shows whether the engine is seeking or scanning, where time and rows go, and whether statistics are stale or a parameter got sniffed wrong. Tuning is reading the plan, then giving the engine what it needs (an index, better stats, a rewrite).

**6. T-SQL is the language of the data tier.** Stored procedures, views, functions, CTEs, window functions and set-based thinking let me push work to where the data lives instead of dragging rows to the app. Set-based beats row-by-row almost every time.

**7. Normalization — and when to break it.** Normalize to remove duplication and protect integrity; denormalize deliberately when read performance demands it. Knowing *why* and *when* to bend the rule is the mark of someone who's tuned real systems, not just read the theory.

**The full-stack / architect lens:** the later Q&As go deeper — index design decisions, statistics and parameter sniffing, isolation and deadlocks, partitioning, HA/DR, backups and recovery models, security and encryption, Azure SQL options, read scaling and replicas, monitoring with DMVs — plus the full-stack side: EF Core from the app, schema migrations, and bulk loading/ETL. That's the difference between writing SQL and *owning* a database in production.

**One rule I never break:** *never ship a query without checking its execution plan — a seek instead of a scan is usually one well-chosen index away.*

---

## S1 · What is SQL Server?

**Simple explanation.** SQL Server is a **relational database management system (RDBMS)** from Microsoft. "Relational" means data lives in **tables** (rows and columns) that relate to each other. It uses **T-SQL** (Microsoft's SQL dialect) to query and change data.

It's designed for **OLTP** — *Online Transaction Processing* — lots of small, fast, reliable reads and writes: an app saving an order, updating a record, fetching a customer. Correctness and consistency come first.

*"On TCW, SQL Server holds the operational data the time-critical reports read — fast, consistent, transactional. Heavy historical analysis goes to Snowflake instead, so it never slows the deadline-critical reads."*

**Follow-ups**
- *"Azure SQL vs SQL Server?"* — Azure SQL is the managed cloud version (Microsoft runs the servers, patching, backups); same engine, less operational burden. I use both.
- *"OLTP vs OLAP?"* — OLTP = many small live transactions (SQL Server); OLAP = big analytical queries over history (Snowflake). Different jobs.

---

## S2 · Relational model and keys

**Simple explanation.** Data is split into related tables to avoid duplication. **Keys** connect them:
- **Primary key (PK)** — uniquely identifies each row (e.g. `PortfolioId`).
- **Foreign key (FK)** — a column pointing to another table's PK, enforcing a valid relationship.

```sql
CREATE TABLE Portfolio (
    PortfolioId INT PRIMARY KEY,
    Name        NVARCHAR(100) NOT NULL
);
CREATE TABLE Position (
    PositionId  INT PRIMARY KEY,
    PortfolioId INT NOT NULL REFERENCES Portfolio(PortfolioId),  -- FK
    Ticker      NVARCHAR(10) NOT NULL,
    MarketValue DECIMAL(18,2) NOT NULL
);
```

The FK guarantees you can't insert a Position for a Portfolio that doesn't exist — the database protects data integrity.

**Follow-ups**
- *"Why not put everything in one big table?"* — Duplication and update anomalies. Splitting (normalization, [S8](#s8--normalization-and-when-to-break-it)) keeps data consistent.
- *"Composite key?"* — A PK made of two+ columns when no single column is unique.

---

## S3 · Indexes (clustered vs non-clustered)

**Simple explanation.** An **index** is like a book's index — it lets the database *find* rows fast instead of scanning every row. This is the single most important performance topic.

- **Clustered index** — defines the physical order of the table's rows. **One per table** (usually the PK). Like a phone book sorted by surname.
- **Non-clustered index** — a separate structure pointing to the rows. **Many allowed.** Like a separate index at the back of a book.

```sql
CREATE NONCLUSTERED INDEX IX_Position_Ticker ON Position(Ticker) INCLUDE (MarketValue);
```

**Trade-off:** indexes speed up reads but slow down writes (each insert/update must maintain them), so I index what's queried, not everything.

**Follow-ups**
- *"How many clustered indexes per table?"* — Exactly one — because it *is* the row order.
- *"What's a covering index?"* — One that `INCLUDE`s all columns a query needs, so it never touches the table — very fast.

---

## S4 · ACID and transactions

**Simple explanation.** A **transaction** is a group of operations that must all succeed or all fail together. **ACID** is the guarantee:
- **Atomicity** — all or nothing.
- **Consistency** — the database moves from one valid state to another.
- **Isolation** — concurrent transactions don't corrupt each other.
- **Durability** — once committed, it survives a crash.

```sql
BEGIN TRANSACTION;
    UPDATE Account SET Balance = Balance - 100 WHERE Id = 1;
    UPDATE Account SET Balance = Balance + 100 WHERE Id = 2;
COMMIT;   -- both happen, or ROLLBACK undoes both
```

This is why relational databases are trusted for money and financial data — you never lose half a transfer.

**Follow-ups**
- *"Why does ACID matter for TCW?"* — Financial data must be correct and reconcilable — ACID guarantees a write is complete and durable.
- *"What's an isolation level?"* — How strictly transactions are separated (e.g. Read Committed vs Serializable) — a trade-off between consistency and concurrency.

---

## S5 · Joins explained simply

**Simple explanation.** A **join** combines rows from two tables using a related column. The common ones:
- **INNER JOIN** — only rows that match in both.
- **LEFT JOIN** — all rows from the left table, plus matches from the right (NULLs where none).
- **RIGHT / FULL** — the mirror / both sides.

```sql
SELECT p.Name, pos.Ticker, pos.MarketValue
FROM Portfolio p
INNER JOIN Position pos ON pos.PortfolioId = p.PortfolioId;
```

**Follow-ups**
- *"INNER vs LEFT — when?"* — INNER when I only want matched data; LEFT when I want everything from the main table even without a match (e.g. portfolios with zero positions).
- *"Do joins hurt performance?"* — Not if the join columns are indexed — that's usually the fix for a slow join.

---

## S6 · Query tuning and execution plans

**Simple explanation.** When a query is slow, I look at its **execution plan** — SQL Server's step-by-step strategy for running it. The plan shows whether it used an index (**seek**, fast) or scanned the whole table (**scan**, slow).

My tuning checklist (real work on TCW):
1. Read the execution plan — find scans, expensive sorts, key lookups.
2. Add or fix an **index** on the filtered/joined columns.
3. Make the `WHERE` clause **sargable** — don't wrap the column in a function (e.g. `WHERE Date >= @d` not `WHERE CONVERT(date, Date) = @d`), so the index can be used.
4. Return only needed columns (avoid `SELECT *`).
5. Update statistics so the optimizer has good estimates.

**Follow-ups**
- *"What does 'sargable' mean?"* — A predicate the index can use. Wrapping a column in a function makes it non-sargable and forces a scan — a common cause of slow reports.
- *"A real example?"* — On TCW a slow report threatened the pre-market window; I traced it to a non-sargable predicate + missing index, fixed both, and the deadline held.

---

## S7 · Stored procedures and T-SQL

**Simple explanation.** A **stored procedure** is saved, reusable SQL logic that lives in the database. **T-SQL** is SQL Server's language, adding variables, loops and error handling to standard SQL.

```sql
CREATE PROCEDURE GetPositions @PortfolioId INT AS
BEGIN
    SET NOCOUNT ON;
    SELECT Ticker, MarketValue
    FROM Position
    WHERE PortfolioId = @PortfolioId;
END;
```

**Benefits:** performance (a cached plan), security (grant execute without table access), and one place for logic. **Trade-off:** business logic in the DB can be harder to version/test than app code — I keep heavy logic in the app and use SPs for data-close operations.

**Follow-ups**
- *"SP vs raw query from the app?"* — SPs for reusable, performance-sensitive, or security-scoped data logic; app-side queries (EF Core) for ordinary CRUD.
- *"How do you prevent SQL injection?"* — Always use **parameters** (`@PortfolioId`), never string-concatenate user input.

---

## S8 · Normalization and when to break it

**Simple explanation.** **Normalization** is organising tables to remove duplication (each fact stored once), which keeps data consistent — the default for OLTP. **Denormalization** deliberately adds some duplication to make reads faster — useful for reporting/analytics.

**My rule:** normalize the operational store (SQL Server) for correctness; denormalize in the analytical store (Snowflake) for fast reporting.

**Follow-ups**
- *"3rd normal form in one line?"* — Every non-key column depends on the key, the whole key, and nothing but the key.
- *"When denormalize?"* — When read speed for reporting matters more than write simplicity — which is exactly why analytical stores exist.

---

## S9 · GROUP BY, HAVING, and aggregates

**Simple explanation.** Aggregates (`SUM`, `COUNT`, `AVG`, `MIN`, `MAX`) summarise many rows into one. `GROUP BY` makes one summary row per group; `HAVING` filters those groups (like `WHERE` but after aggregation).

```sql
SELECT PortfolioId, SUM(MarketValue) AS Total
FROM Position
GROUP BY PortfolioId
HAVING SUM(MarketValue) > 1000000;   -- filter groups after aggregating
```

**Follow-ups**
- *"WHERE vs HAVING?"* — `WHERE` filters rows *before* grouping; `HAVING` filters groups *after* aggregation.
- *"Can you SELECT a non-aggregated column not in GROUP BY?"* — No — every selected non-aggregate column must be in `GROUP BY`.

---

## S10 · Subqueries and CTEs

**Simple explanation.** A **subquery** is a query inside another. A **CTE** (Common Table Expression, `WITH`) is a named temporary result that makes complex queries readable and supports recursion.

```sql
WITH Ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY PortfolioId ORDER BY MarketValue DESC) AS rn
    FROM Position
)
SELECT * FROM Ranked WHERE rn <= 3;   -- top 3 positions per portfolio
```

**Follow-ups**
- *"CTE vs subquery vs temp table?"* — CTE for readability/recursion (scoped to one statement); temp table when you reuse the result across statements or it's large.
- *"Are CTEs faster?"* — Not inherently — they're mainly readability; the optimizer often treats them like inline subqueries.

---

## S11 · Window functions

**Simple explanation.** Window functions compute across a set of rows **related to the current row** without collapsing them (unlike GROUP BY). Great for running totals, rankings and "top N per group".

```sql
SELECT Ticker, MarketValue,
       SUM(MarketValue) OVER (ORDER BY AsOf) AS RunningTotal,
       RANK() OVER (PARTITION BY PortfolioId ORDER BY MarketValue DESC) AS Rank
FROM Position;
```

**Follow-ups**
- *"OVER + PARTITION BY meaning?"* — `PARTITION BY` splits rows into groups; the function computes within each group, keeping every row.
- *"ROW_NUMBER vs RANK vs DENSE_RANK?"* — ROW_NUMBER is always unique; RANK leaves gaps after ties; DENSE_RANK doesn't.

---

## S12 · Views and indexed views

**Simple explanation.** A **view** is a saved query you treat like a table — great for simplifying complex joins and controlling access. An **indexed (materialized) view** physically stores the result and stays up to date, speeding up expensive aggregations at a write cost.

**Follow-ups**
- *"View vs table?"* — A normal view stores no data (it runs its query each time); an indexed view stores results.
- *"When indexed view?"* — For heavy, frequently-read aggregations where the extra write cost is worth the read speed.

---

## S13 · Functions: scalar vs table-valued

**Simple explanation.** A **scalar function** returns one value; a **table-valued function (TVF)** returns a table you can join to. Watch out: row-by-row scalar functions in a query can kill performance — **inline TVFs** are usually far faster.

**Follow-ups**
- *"Why can scalar UDFs be slow?"* — They can execute per row and block parallelism. Modern SQL Server can inline some; I still prefer set-based logic.
- *"Inline vs multi-statement TVF?"* — Inline TVFs are optimised into the query (fast); multi-statement ones are more like a black box (often slower).

---

## S14 · Triggers

**Simple explanation.** A **trigger** is code that runs automatically on INSERT/UPDATE/DELETE — useful for auditing or enforcing rules. Use sparingly: they add hidden work and can complicate debugging.

**Follow-ups**
- *"When use a trigger?"* — Audit trails or cross-table integrity that can't be done with constraints — not for business logic better placed in the app.
- *"Downside?"* — Hidden side effects and performance cost on every write — I keep them minimal and well-documented.

---

## S15 · Index design decisions

**Simple explanation (architect lens).** Good indexing is the biggest performance lever. I design indexes around the actual queries: put the most selective, most-filtered columns first in the key, add `INCLUDE` columns to make a **covering index**, and avoid over-indexing (each index slows writes and uses space).

**Follow-ups**
- *"Column order in a composite index?"* — Most-filtered/equality columns first, then range columns — order matters for whether the index is usable.
- *"How do you find missing indexes?"* — The execution plan and DMVs suggest them — I validate rather than blindly add, because too many hurt writes.
- *"Filtered index?"* — An index with a `WHERE` clause — smaller and faster for queries that always filter the same way (e.g. `IsActive = 1`).

---

## S16 · Statistics and parameter sniffing

**Simple explanation.** SQL Server uses **statistics** (data distribution estimates) to pick a plan. Stale stats → bad plans — keep them updated. **Parameter sniffing** is when a cached plan built for one parameter value is reused for a very different value and performs badly.

**Follow-ups**
- *"How do you fix parameter sniffing?"* — `OPTIMIZE FOR`, `RECOMPILE` on the problem query, or splitting the query — after confirming it's the cause via plans.
- *"Why update statistics?"* — So the optimizer's row estimates match reality and it chooses seeks over scans.

---

## S17 · Isolation levels and locking

**Simple explanation.** Isolation levels balance **consistency vs concurrency**: `READ COMMITTED` (default), `REPEATABLE READ`, `SERIALIZABLE` (strictest), and `SNAPSHOT` (readers see a consistent version without blocking writers). Higher isolation = more correctness but more blocking.

**Follow-ups**
- *"What problems do they prevent?"* — Dirty reads, non-repeatable reads, phantoms — each level prevents more, at a concurrency cost.
- *"Why SNAPSHOT / RCSI?"* — Read Committed Snapshot lets reads use row versions so they don't block writes — great for read-heavy OLTP.

---

## S18 · Deadlocks

**Simple explanation.** A **deadlock** is when two transactions each hold a lock the other needs, so neither can proceed — SQL Server kills one as the "victim". I prevent them by accessing tables in a **consistent order**, keeping transactions **short**, and using the right isolation level.

**Follow-ups**
- *"How do you diagnose one?"* — The deadlock graph (Extended Events / SQL trace) shows the two processes and resources — then I fix the access order or index.
- *"Deadlock vs blocking?"* — Blocking is one waiting for another (resolves); deadlock is mutual and unresolvable without killing a victim.

---

## S19 · Reading execution plans deeper

**Simple explanation.** Beyond seek-vs-scan, I read plans for: **key lookups** (add covering columns), **expensive sorts/hashes** (memory pressure), **implicit conversions** (a type mismatch that disables an index), and **estimated vs actual rows** (a big gap means bad stats).

**Follow-ups**
- *"What's a key lookup and why bad?"* — The index found the row but had to jump to the table for extra columns — fix with an `INCLUDE` covering index.
- *"Implicit conversion warning?"* — Comparing an `nvarchar` column to a `varchar` param can force a scan — match types to keep the index usable.

---

## S20 · Partitioning large tables

**Simple explanation.** **Partitioning** splits one big table into pieces (usually by date) so queries scan only relevant partitions and old data is easy to archive/switch out. It helps manageability and can help performance on huge tables.

**Follow-ups**
- *"Partitioning vs sharding?"* — Partitioning splits within one database; sharding spreads across multiple databases/servers.
- *"Does partitioning always speed queries?"* — Only when queries filter on the partition key (partition elimination) — otherwise it mainly aids maintenance.

---

## S21 · High availability and disaster recovery

**Simple explanation (architect lens).** For uptime I use **Always On Availability Groups** — synchronous replicas for zero-data-loss failover within a region, asynchronous replicas to another region for DR. I design to meet the agreed **RPO** (how much data loss is acceptable) and **RTO** (how fast to recover).

**Follow-ups**
- *"RPO vs RTO?"* — RPO = max acceptable data loss; RTO = max acceptable downtime — these drive the HA/DR design and cost.
- *"Sync vs async replica?"* — Sync = no data loss but latency cost (same region); async = some lag, used cross-region for DR.

---

## S22 · Backups and recovery models

**Simple explanation.** Backups are the last line of defence: **full**, **differential**, and **transaction log** backups. The **recovery model** (Simple / Full) controls point-in-time restore. For critical financial data I use Full recovery + regular log backups so I can restore to a specific moment.

**Follow-ups**
- *"Point-in-time restore needs what?"* — Full recovery model + a chain of log backups — restore full + diffs + logs up to the target time.
- *"Do you test restores?"* — Yes — an untested backup isn't a backup; I verify restores regularly.

---

## S23 · Security and encryption

**Simple explanation.** Layers: authentication (Entra ID / SQL logins), authorization (roles, least privilege), **encryption at rest** (TDE), **encryption in transit** (TLS), and **Always Encrypted** / column-level for the most sensitive fields. Never string-concatenate SQL — parameterise to stop injection.

**Follow-ups**
- *"TDE vs Always Encrypted?"* — TDE encrypts the whole database files at rest; Always Encrypted keeps specific columns encrypted even from the DBA (client-side keys).
- *"Least privilege in practice?"* — App accounts get only the rights they need (often execute on specific procedures), not `db_owner`.

---

## S24 · Azure SQL options

**Simple explanation.** In Azure I choose between **Azure SQL Database** (fully-managed single DB / elastic pool, great default), **SQL Managed Instance** (near-full SQL Server compatibility for lift-and-shift), and **SQL Server on a VM** (full control, most ops). Managed options handle patching, backups and HA for me.

**Follow-ups**
- *"When Managed Instance over SQL Database?"* — When I need instance-level features (SQL Agent, cross-DB queries, CLR) for a migration.
- *"DTU vs vCore?"* — Two pricing models — vCore gives clearer CPU/memory sizing and is my usual choice.

---

## S25 · Scaling reads and replicas

**Simple explanation.** SQL Server scales up (bigger box) easily and scales reads with **read-only replicas** (route reporting reads to a replica so they don't slow writes). For write scale beyond one node you look at partitioning/sharding or a different store — which is why heavy analytics on TCW go to Snowflake, not SQL Server.

**Follow-ups**
- *"How do you offload reporting load?"* — Read replicas for near-real-time reads, and a separate analytical store (Snowflake) for heavy historical queries.
- *"Vertical vs horizontal scaling?"* — SQL Server favours vertical (scale up) + read replicas; true horizontal write scaling is hard — a reason to split OLTP/OLAP.

---

## S26 · Monitoring and DMVs

**Simple explanation.** I monitor with **Dynamic Management Views (DMVs)** (`sys.dm_exec_query_stats` for the slowest queries, `sys.dm_os_wait_stats` for what the server waits on), Query Store (plan history/regressions), and Azure SQL Insights.

**Follow-ups**
- *"How do you find the slowest queries?"* — `sys.dm_exec_query_stats` ranked by total/avg CPU or duration — then tune the top offenders.
- *"What is Query Store?"* — It records query plans and runtimes over time so I can spot and force-fix a plan regression.

---

## S27 · Working with EF Core from the app

**Simple explanation (full-stack lens).** From my ASP.NET Core API, EF Core maps C# to SQL Server. I keep it fast: `AsNoTracking()` for reads, projections (`.Select`) to fetch only needed columns, `.Include()`/split queries to avoid N+1, and I check the generated SQL for hot paths, dropping to Dapper/raw SQL when needed.

**Follow-ups**
- *"How do you see EF's SQL?"* — Log it (EF Core logging) or profile it — then read the execution plan like any query.
- *"When abandon EF for raw SQL?"* — On performance-critical or complex queries where I want full control — EF for productivity, SQL for hot paths.

---

## S28 · Schema migrations

**Simple explanation.** I evolve the schema with **EF Core Migrations** (or DACPAC/Flyway) versioned in source control and applied by CI/CD. For zero-downtime I use **expand-then-contract**: add the new column, deploy code that writes both, backfill, then remove the old — never a breaking change in one step.

**Follow-ups**
- *"How do you change a column without downtime?"* — Expand/contract: additive change first, migrate data, switch reads, then drop the old — always backward-compatible mid-flight.
- *"Who runs migrations in prod?"* — The CI/CD pipeline with a reviewed script — never ad-hoc by hand.

---

## S29 · Bulk loading and ETL

**Simple explanation.** For loading lots of rows I use **bulk operations** (`SqlBulkCopy`, `BULK INSERT`, table-valued parameters) instead of row-by-row inserts — orders of magnitude faster. On TCW my FastAPI ETL lands validated data efficiently, and heavy analytics flow onward to Snowflake.

**Follow-ups**
- *"Why not loop single INSERTs?"* — Each is a round-trip and transaction overhead; bulk copy streams thousands at once.
- *"Idempotent loads?"* — Upsert (`MERGE`) keyed by natural id so a retried ETL run doesn't duplicate rows.

---

## S30 · Common mistakes I watch for

**Simple explanation.** The recurring SQL Server mistakes I catch in reviews: `SELECT *` (fetches too much, breaks covering indexes), non-sargable `WHERE` (function on a column disables the index), N+1 from the ORM, missing indexes on join/filter columns, huge unpaged result sets, string-built SQL (injection), and long transactions holding locks.

**Follow-ups**
- *"The single most common cause of a slow query?"* — A missing or unusable index (often from a non-sargable predicate) — exactly what I fixed to protect the TCW deadline.
- *"How do you prevent these on a team?"* — Query reviews, execution-plan checks in PRs, and standards (no `SELECT *`, always parameterise, always paginate).

---

## Section index

| # | Concept | One-line takeaway |
|---|---|---|
| S1 | What it is | Microsoft RDBMS for fast, consistent OLTP (live app data) |
| S2 | Relational & keys | Tables related by primary/foreign keys protect integrity |
| S3 | Indexes | Find rows fast; one clustered, many non-clustered |
| S4 | ACID & transactions | All-or-nothing, durable — why it's trusted for money |
| S5 | Joins | Combine tables on related columns; index the join column |
| S6 | Query tuning | Read the plan; add indexes; keep predicates sargable |
| S7 | Stored procedures | Reusable DB logic; always parameterise against injection |
| S8 | Normalization | Normalize OLTP for correctness; denormalize analytics for speed |
| S9 | GROUP BY & aggregates | Summarise rows; HAVING filters groups after aggregation |
| S10 | Subqueries & CTEs | CTE (WITH) for readable/recursive queries |
| S11 | Window functions | Compute over related rows without collapsing them |
| S12 | Views | Saved query; indexed view materialises results |
| S13 | Functions | Scalar vs TVF; inline TVFs are far faster |
| S14 | Triggers | Auto-run on writes; use sparingly (hidden cost) |
| S15 | Index design | Design to the query; covering indexes; don't over-index |
| S16 | Stats & sniffing | Keep stats fresh; fix bad cached plans |
| S17 | Isolation & locking | Consistency vs concurrency; SNAPSHOT/RCSI for read-heavy |
| S18 | Deadlocks | Consistent lock order + short transactions |
| S19 | Plan reading | Key lookups, sorts, implicit conversions, est vs actual |
| S20 | Partitioning | Split big tables (by date) for elimination & archiving |
| S21 | HA/DR | Always On replicas; design to RPO/RTO |
| S22 | Backups | Full/diff/log; Full recovery for point-in-time restore |
| S23 | Security | Least privilege, TDE, TLS, Always Encrypted, parameterise |
| S24 | Azure SQL | SQL Database vs Managed Instance vs VM |
| S25 | Scaling reads | Read replicas; offload heavy analytics to Snowflake |
| S26 | Monitoring | DMVs + Query Store find slow queries & regressions |
| S27 | EF Core | AsNoTracking, projections, avoid N+1; SQL for hot paths |
| S28 | Migrations | EF migrations in CI/CD; expand-contract for zero downtime |
| S29 | Bulk & ETL | Bulk copy/TVPs, not row-by-row; idempotent upserts |
| S30 | Common mistakes | SELECT *, non-sargable WHERE, N+1, missing indexes |

---

[← Web API vs FastAPI](33-concept-webapi-vs-fastapi.md) · [Home](README.md) · [Next → Concept: Snowflake](35-concept-snowflake.md)
