# 50 · Concept: Data Design (Data Modeling) (30 questions)

[← Kafka](49-concept-kafka.md) · [Home](README.md) · [Next → .NET Core](51-concept-dotnet-core.md)

This file explains **data design / data modeling** — how I structure data so systems are correct, fast and maintainable — in simple English and real depth. I answer from projects A–E, where I designed the data models behind TCW's finance platforms.

> Simple one-liner: *"Data design is deciding how to structure and store data — entities, relationships, keys, and whether to normalise or denormalise — driven by the access patterns and consistency needs. Get the model right and everything downstream gets easier."*

**Jump to:** [DD1 What it is](#dd1--what-is-data-design) · [DD2 Why it matters](#dd2--why-it-matters) · [DD3 Three levels](#dd3--conceptual-logical-physical) · [DD4 Entities](#dd4--entities-and-relationships) · [DD5 Keys](#dd5--primary-and-foreign-keys) · [DD6 Normalization](#dd6--normalization) · [DD7 Normal forms](#dd7--normal-forms) · [DD8 Denormalization](#dd8--denormalization) · [DD9 Access patterns](#dd9--design-for-access-patterns) · [DD10 Relational modeling](#dd10--relational-modeling)
> [DD11 NoSQL modeling](#dd11--nosql-modeling) · [DD12 Document](#dd12--document-modeling) · [DD13 Key-value](#dd13--key-value-and-wide-column) · [DD14 Indexing](#dd14--indexing) · [DD15 Relationships in NoSQL](#dd15--relationships-embed-vs-reference) · [DD16 IDs](#dd16--choosing-identifiers) · [DD17 Data types](#dd17--data-types-and-precision) · [DD18 Time & audit](#dd18--time-and-audit-fields) · [DD19 Soft delete](#dd19--soft-delete-and-history) · [DD20 Constraints](#dd20--constraints-and-integrity)
> [DD21 Transactions](#dd21--transactions) · [DD22 Schema evolution](#dd22--schema-evolution-and-migrations) · [DD23 Partitioning](#dd23--partitioning-and-sharding) · [DD24 OLTP vs OLAP](#dd24--oltp-vs-olap) · [DD25 Warehouse](#dd25--star-schema-and-warehousing) · [DD26 Security](#dd26--data-security-and-privacy) · [DD27 Performance](#dd27--performance) · [DD28 Governance](#dd28--data-governance) · [DD29 Pitfalls](#dd29--common-pitfalls) · [DD30 My approach](#dd30--my-approach) · [Section index](#section-index)

---

## DD1 · What is data design?

**Simple explanation.** **Data design (data modeling)** is deciding how to **structure data**: what the entities are, how they relate, what the keys and types are, and how it's physically stored. It's the blueprint for how data lives in the system.

**Architect's view:** The data model is the foundation — it shapes performance, correctness and how easy the system is to change. I design it from the **access patterns**, not in isolation.

**Follow-ups**
- *"One-line?"* — Structuring entities, relationships, keys and storage to fit how data is used.
- *"Driven by what?"* — Access patterns and consistency needs first.

---

## DD2 · Why it matters

**Simple explanation.** A good model makes queries fast, keeps data **consistent**, and lets the system evolve. A bad model causes slow queries, duplicated/contradictory data, and painful changes later. Data outlives code, so the model is the most expensive thing to get wrong.

**Follow-ups**
- *"Cost of a bad model?"* — Migrations, bugs, performance debt — hard to fix once live.
- *"Data vs code?"* — Data lasts longer; a good model pays off for years.

---

## DD3 · Conceptual, logical, physical

**Simple explanation.** Three levels: **conceptual** (high-level entities and relationships, no tech), **logical** (attributes, keys, normalization — still tech-neutral), **physical** (actual tables/collections, indexes, types for a specific DB). I move from business meaning to implementation.

**Follow-ups**
- *"Why three?"* — Separate business meaning from implementation — clearer and portable.
- *"Start where?"* — Conceptual, with the business — then refine down.

---

## DD4 · Entities and relationships

**Simple explanation.** **Entities** are the things (Customer, Account, Trade); **relationships** connect them (a Customer *has many* Accounts). I identify entities, their attributes, and cardinality (one-to-one, one-to-many, many-to-many) — the core of any model.

**Follow-ups**
- *"Many-to-many?"* — Resolved with a join/associative table.
- *"Cardinality matters?"* — Yes — it drives keys, tables and query shape.

---

## DD5 · Primary and foreign keys

**Simple explanation.** A **primary key** uniquely identifies a row; a **foreign key** links a row to another table's key, enforcing relationships and integrity. Good keys are stable and unique — the backbone of relational integrity.

**Follow-ups**
- *"Natural vs surrogate key?"* — Surrogate (generated id) is usually safer — stable, not business-dependent.
- *"FK role?"* — Enforces valid references — no orphan records.

---

## DD6 · Normalization

**Simple explanation.** **Normalization** organises data to **remove redundancy** — each fact stored once — so updates are consistent and anomalies are avoided. It splits data into related tables. It's my default for transactional (OLTP) systems like finance.

**Follow-ups**
- *"Why normalise?"* — One source of truth per fact → no update anomalies.
- *"Downside?"* — More joins → can be slower for read-heavy queries.

---

## DD7 · Normal forms

**Simple explanation.** **Normal forms** are rules: **1NF** (atomic values, no repeating groups), **2NF** (no partial-key dependencies), **3NF** (no transitive dependencies). I usually design to **3NF** for OLTP, then denormalise selectively for performance.

**Follow-ups**
- *"How far?"* — 3NF is the practical sweet spot for most transactional data.
- *"BCNF+?"* — Rarely needed — 3NF covers most real cases.

---

## DD8 · Denormalization

**Simple explanation.** **Denormalization** deliberately **duplicates data** to speed reads (fewer joins). I do it when read performance demands it — accepting the cost of keeping copies in sync. It's a trade-off, not a default.

**Follow-ups**
- *"When denormalise?"* — Read-heavy paths where joins are too slow.
- *"Cost?"* — Duplicated data must be kept consistent — more write logic.

---

## DD9 · Design for access patterns

**Simple explanation.** I model around **how data will be queried**, not just how it's structured on paper. In relational I can be flexible; in **NoSQL** access patterns *dictate* the model — you design tables around your queries.

**Follow-ups**
- *"NoSQL rule?"* — Know the queries first — model to serve them.
- *"Relational too?"* — Yes — access patterns guide indexes and denormalization.

---

## DD10 · Relational modeling

**Simple explanation.** In relational DBs I model **normalised tables** with keys and constraints, use **joins** to combine data, and rely on **ACID transactions** for correctness. This is my default for finance where integrity and relationships are paramount ([file 47 SD10](47-concept-system-design.md#sd10--sql-vs-nosql)).

**Follow-ups**
- *"Why relational for finance?"* — Strong integrity, transactions, complex relationships.
- *"Joins cost?"* — Managed with indexes and selective denormalization.

---

## DD11 · NoSQL modeling

**Simple explanation.** In **NoSQL** I model for **scale and access patterns**: denormalise, embed related data, and often duplicate to avoid joins. There's no one-size model — document, key-value, wide-column and graph each need different thinking.

**Follow-ups**
- *"Biggest mindset shift?"* — From normalised relations to query-shaped, denormalised data.
- *"Joins in NoSQL?"* — Usually avoided — embed or duplicate instead.

---

## DD12 · Document modeling

**Simple explanation.** In document DBs (Cosmos DB, MongoDB) I store **JSON documents** that group related data together as it's read — e.g. an order with its line items in one document. This makes reads fast (one fetch) at the cost of some duplication.

**Follow-ups**
- *"Embed everything?"* — No — embed what's read together; reference what's large/shared ([DD15](#dd15--relationships-embed-vs-reference)).
- *"Doc size limit?"* — Yes — don't embed unbounded growing lists.

---

## DD13 · Key-value and wide-column

**Simple explanation.** **Key-value** (Redis, DynamoDB) stores a value by key — ultra-fast lookups by key, minimal query flexibility. **Wide-column** (Cassandra) stores rows with flexible columns, modeled tightly around query patterns for massive scale.

**Follow-ups**
- *"Key-value use?"* — Caching, sessions, lookups by a known key.
- *"Wide-column use?"* — Huge write/read scale with known access patterns.

---

## DD14 · Indexing

**Simple explanation.** **Indexes** speed reads by letting the DB find rows without scanning everything — like a book's index. I index columns used in filters/joins/sorts, but not too many, because each index **slows writes** and uses space.

**Follow-ups**
- *"Index everything?"* — No — indexes cost write speed and storage; index for real queries.
- *"Composite index?"* — Multi-column for combined filters — order matters.

---

## DD15 · Relationships: embed vs reference

**Simple explanation.** In NoSQL I **embed** related data when it's read together and bounded (order + items), and **reference** (store an id) when data is large, shared, or grows unbounded. It's the core document-modeling decision.

**Follow-ups**
- *"Embed when?"* — Read together, small, owned by the parent.
- *"Reference when?"* — Shared across parents, large, or unbounded growth.

---

## DD16 · Choosing identifiers

**Simple explanation.** I prefer **surrogate keys** (auto-increment, UUID, or partition-friendly ids) over business fields that can change. **UUIDs** suit distributed systems (no coordination); sequential ids are compact but can hotspot at scale.

**Follow-ups**
- *"UUID vs sequential?"* — UUID for distributed uniqueness; sequential for compactness — trade-off.
- *"Business key as PK?"* — Avoid — business values change; surrogate keys stay stable.

---

## DD17 · Data types and precision

**Simple explanation.** I pick correct types: **decimal (not float)** for money to avoid rounding errors, proper date/time with time zones, and right-sized numeric/text types. In finance, using float for currency is a classic, costly bug.

**Follow-ups**
- *"Money type?"* — Decimal/numeric — exact; never binary float.
- *"Dates?"* — Store UTC with time zone awareness — avoid ambiguity.

---

## DD18 · Time and audit fields

**Simple explanation.** I add **created_at / updated_at** and often **created_by / updated_by** to key entities for traceability. In regulated finance, audit fields (and sometimes full history) are required for compliance.

**Follow-ups**
- *"Why audit fields?"* — Traceability, debugging, compliance.
- *"Full history?"* — Use history tables/temporal tables when change tracking is required.

---

## DD19 · Soft delete and history

**Simple explanation.** **Soft delete** marks a row inactive (`is_deleted`) instead of removing it — preserving history and enabling recovery/audit. For full change history I use **temporal/history tables**. In finance, hard-deleting records is often not allowed.

**Follow-ups**
- *"Soft vs hard delete?"* — Soft keeps data for audit/recovery; hard truly removes.
- *"Cost of soft delete?"* — Every query must filter deleted rows — enforce it consistently.

---

## DD20 · Constraints and integrity

**Simple explanation.** I enforce correctness in the DB with **constraints**: NOT NULL, UNIQUE, CHECK, and **foreign keys**. The database guarding integrity is far safer than relying on application code alone — vital for financial data.

**Follow-ups**
- *"Why DB constraints?"* — Last line of defence — app bugs can't corrupt data.
- *"CHECK use?"* — Enforce rules (e.g. amount >= 0) at the data layer.

---

## DD21 · Transactions

**Simple explanation.** A **transaction** groups operations so they all succeed or all fail (**ACID**), keeping data consistent — e.g. debit one account and credit another together. Essential in finance where partial updates are unacceptable ([file 51 DN22](51-concept-dotnet-core.md#dn22--entity-framework-core)).

**Follow-ups**
- *"ACID?"* — Atomic, Consistent, Isolated, Durable.
- *"Money example?"* — Transfer = debit + credit in one transaction — never half.

---

## DD22 · Schema evolution and migrations

**Simple explanation.** Schemas change over time, so I use **versioned migrations** (scripts/EF migrations) applied in a controlled, reversible way, and design **backward-compatible** changes (add before remove) to avoid breaking running apps.

**Follow-ups**
- *"Zero-downtime change?"* — Add new, migrate data, switch code, then remove old — expand/contract.
- *"Track migrations?"* — Version-controlled scripts run in CI/CD.

---

## DD23 · Partitioning and sharding

**Simple explanation.** For large tables I **partition** (split by range/hash — e.g. by date) to keep queries fast and maintenance easy, and **shard** across nodes for scale ([file 47 SD12](47-concept-system-design.md#sd12--sharding)). A good **partition key** aligns with query patterns and spreads load evenly.

**Follow-ups**
- *"Partition key choice?"* — Even distribution + matches common queries — avoid hotspots.
- *"Partition vs shard?"* — Partition within a DB; shard across servers.

---

## DD24 · OLTP vs OLAP

**Simple explanation.** **OLTP** = transactional (many small reads/writes, normalised — the app database). **OLAP** = analytical (big aggregations over history, denormalised — the warehouse). I keep them **separate** so heavy analytics don't slow the live app.

**Follow-ups**
- *"Same DB for both?"* — Avoid — different shapes; separate OLTP and OLAP stores.
- *"Move data across?"* — ETL/streaming (CDC via Kafka) into the warehouse.

---

## DD25 · Star schema and warehousing

**Simple explanation.** For analytics I use a **star schema**: a central **fact** table (measurable events, e.g. trades) linked to **dimension** tables (date, client, product). It's denormalised for fast aggregation and easy reporting.

**Follow-ups**
- *"Fact vs dimension?"* — Facts = numbers/events; dimensions = descriptive context.
- *"Why star?"* — Simple, fast joins for BI queries.

---

## DD26 · Data security and privacy

**Simple explanation.** I protect data with **encryption** (at rest/in transit), **access control** (least privilege), **masking** of sensitive fields, and **PII classification**. In finance I also honour **retention/GDPR** rules — privacy is designed into the model.

**Follow-ups**
- *"PII handling?"* — Classify, encrypt, mask, restrict, and set retention.
- *"Design-time?"* — Yes — decide sensitivity/retention when modeling, not later.

---

## DD27 · Performance

**Simple explanation.** I make data fast with **right indexes**, **selective denormalization**, **partitioning**, avoiding **N+1 queries**, and caching hot reads in **Redis** ([file 48](48-concept-redis-cache.md)). I measure with query plans — optimise the real slow queries, not guesses.

**Follow-ups**
- *"First tuning step?"* — Read the query plan; add the missing index.
- *"N+1?"* — Many small queries in a loop — batch/join instead.

---

## DD28 · Data governance

**Simple explanation.** **Governance** = clear ownership, definitions, quality rules, lineage and cataloguing so data is trustworthy and consistent across teams. In a regulated firm this is essential — everyone must agree what "client balance" means and where it comes from.

**Follow-ups**
- *"Why governance?"* — Trust, consistency, compliance across the org.
- *"Lineage?"* — Knowing where data came from and how it transformed.

---

## DD29 · Common pitfalls

**Simple explanation.** Pitfalls: modeling without knowing access patterns, float for money, no constraints, over- or under-normalizing, missing indexes (or too many), no migration strategy, and ignoring audit/security. I design against each — they're expensive to fix in production.

**Follow-ups**
- *"Most costly?"* — Wrong money type or missing constraints → corrupt financial data.
- *"Most common?"* — Modeling before understanding the queries.

---

## DD30 · My approach

**How I answer (the whole picture).** *"I design data from the **access patterns and consistency needs**, moving conceptual → logical → physical. For transactional finance systems I use **normalised relational models (to 3NF)** with **surrogate keys, foreign keys and constraints**, **decimal for money**, proper UTC dates, and **audit/soft-delete** for compliance — all wrapped in **ACID transactions** so operations like transfers are all-or-nothing. I **denormalise selectively** and add **indexes** for read-heavy paths, cache hot data in Redis, and **partition/shard** large tables by a query-aligned key. For NoSQL I flip the mindset — model around queries, embedding what's read together and referencing what's shared. I keep **OLTP and OLAP separate**, feeding a **star-schema warehouse** for analytics, and I bake in **security, PII handling and governance** from the start. Schema changes go through **versioned, backward-compatible migrations**. That disciplined modeling is what kept TCW's financial data correct, fast and auditable."*

**Follow-ups**
- *"One sentence?"* — Model to access patterns; normalise for integrity, denormalise for speed, enforce constraints, and design in audit/security.
- *"Golden rule for finance?"* — Decimal money, DB constraints, transactions, and audit — never compromise on correctness.

---

## Section index

| # | Topic | Core message |
|---|---|---|
| DD1 | Data design | Structure entities/relationships/keys/storage |
| DD2 | Why it matters | Data outlives code; model is foundational |
| DD3 | Three levels | Conceptual → logical → physical |
| DD4 | Entities | Things + relationships + cardinality |
| DD5 | Keys | PK identifies; FK enforces links |
| DD6 | Normalization | Remove redundancy; one fact once |
| DD7 | Normal forms | Design to 3NF for OLTP |
| DD8 | Denormalization | Duplicate for read speed, deliberately |
| DD9 | Access patterns | Model to how data is queried |
| DD10 | Relational | Normalised + joins + ACID for finance |
| DD11 | NoSQL | Query-shaped, denormalised, scalable |
| DD12 | Document | Group data read together as JSON |
| DD13 | Key-value/wide-column | Fast key lookups / massive scale |
| DD14 | Indexing | Speed reads; costs write speed |
| DD15 | Embed vs reference | Embed if read together, else reference |
| DD16 | Identifiers | Prefer stable surrogate keys |
| DD17 | Data types | Decimal for money; UTC dates |
| DD18 | Audit fields | created/updated for traceability |
| DD19 | Soft delete | Keep history; avoid hard delete in finance |
| DD20 | Constraints | DB enforces integrity |
| DD21 | Transactions | ACID; all-or-nothing operations |
| DD22 | Migrations | Versioned, backward-compatible |
| DD23 | Partition/shard | Split by query-aligned key |
| DD24 | OLTP vs OLAP | Separate transactional and analytical |
| DD25 | Star schema | Facts + dimensions for analytics |
| DD26 | Security | Encrypt, mask, classify PII, retention |
| DD27 | Performance | Indexes, denorm, partition, cache |
| DD28 | Governance | Ownership, definitions, lineage |
| DD29 | Pitfalls | Float money, no constraints, no patterns |
| DD30 | My approach | Access-pattern-driven, correct, auditable |

---

[← Kafka](49-concept-kafka.md) · [Home](README.md) · [Next → .NET Core](51-concept-dotnet-core.md)
