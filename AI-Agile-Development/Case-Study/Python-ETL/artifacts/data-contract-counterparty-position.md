# Data Contract — `counterparty_position`

| | |
|---|---|
| **Produced by** | Hem Singh (Architect) with Ravi Mullick (Backend Engineer) |
| **Using** | [P13 — Design the Data Contract](../../../AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) |
| **Date** | 2026-06-19 |
| **Status** | Approved · in force from v1.0 |
| **Version** | 1.1 |
| **Governs** | `core/transform.py`, `sql/schema.sql`, `sinks/sql_sink.py`, `sinks/snowflake_sink.py`, `recon/reconcile.py` |

---

## 1. What this contract is

One row shape, crossing four boundaries: extraction → rules engine → Azure SQL silver → Snowflake gold.

Everything upstream of the transform is shaped by the counterparty. Everything downstream is shaped by this document. A counterparty position statement in English and a trade confirmation in Spanish both arrive here as the same row, differing only in which date columns are populated.

**One target shape means one reconciliation.** That is the entire reason the schema is canonical rather than per-broker, and it is the property that must not be traded away for convenience.

The canonical column order is declared once, in `core/transform.py::COLUMNS`. The DDL, both sinks and the reconciliation follow that list. It exists so a schema change is one edit rather than four that drift apart silently.

## 2. Column definitions

Types are given for both stores. Where they differ it is because the two systems spell the same thing differently, not because the data differs.

### 2.1 Identity and provenance

| Column | Azure SQL | Snowflake | Null | Units | Meaning | Source |
|---|---|---|---|---|---|---|
| `content_hash` | `CHAR(64)` | `VARCHAR(64)` | **NOT NULL** | hex | SHA-256 of the **document content**. The document's identity. Never derived from the filename. | `core/idempotency.py` |
| `source_key` | `VARCHAR(64)` | `VARCHAR(64)` | **NOT NULL** | — | Counterparty key, e.g. `broker_alpha`, `broker_beta_em`. Matches a block in `config/sources.yaml`. | `SourceConfig.key` |
| `doc_type` | `VARCHAR(32)` | `VARCHAR(32)` | **NOT NULL** | — | `position_statement` or `trade_confirmation`. Determines which date columns are populated. | `SourceConfig.doc_type` |
| `line_no` | `INT` | `NUMBER(9,0)` | **NOT NULL** | — | 1-based position of the line item within the document, in document order. Part of the natural key. | `core/transform.py` |

### 2.2 The business columns

| Column | Azure SQL | Snowflake | Null | Units | Meaning | Source |
|---|---|---|---|---|---|---|
| `account_number` | `VARCHAR(64)` | `VARCHAR(64)` | **NOT NULL** | — | Counterparty account identifier. The reconciliation key against Aladdin. Never translated, never redacted, masked to last four digits in the UI list view. | Header field `account_number` |
| `security_id` | `VARCHAR(64)` | `VARCHAR(64)` | **NOT NULL** | — | Instrument identifier as stated by the counterparty — ISIN, CUSIP, SEDOL, or the broker's own. Never translated. | Line-item field `security_id` |
| `security_name` | `NVARCHAR(256)` | `VARCHAR(256)` | NULL | — | Descriptive instrument name. Translated to English for EM sources. Not a matching key — this is the only business column the reconciliation ignores. | Line-item field `security_name` |
| `statement_date` | `DATE` | `DATE` | **NOT NULL** | — | The date the row is *as of*, in the counterparty's stated terms. For a `trade_confirmation` this is populated from the trade date — see §4. | Header, resolved by `_as_of_date` |
| `trade_date` | `DATE` | `DATE` | NULL | — | Trade date. Populated for trade confirmations; null for position statements. | Header field `trade_date` |
| `settlement_date` | `DATE` | `DATE` | NULL | — | Contractual settlement date. Must be on or after `trade_date` where both are present. | Header field `settlement_date` |
| `side` | `VARCHAR(4)` | `VARCHAR(4)` | NULL | — | `BUY` or `SELL`. Normalised from the counterparty's vocabulary — Spanish `COMPRA`/`VENTA` map here via configuration, not translation. Null for position statements. | Line-item field `side` |
| `quantity` | `DECIMAL(28,8)` | `NUMBER(28,8)` | **NOT NULL** | instrument units | Signed position or trade quantity. Negative means short. Eight decimal places because EM funds deal in fractional units. | Line-item field `quantity` |
| `price` | `DECIMAL(28,4)` | `NUMBER(28,4)` | NULL | currency units per instrument unit | Unit price in the row's `currency`. | Line-item field `price` |
| `market_value` | `DECIMAL(28,4)` | `NUMBER(28,4)` | NULL | currency units | Market value in the row's `currency`. **Not** converted to a base currency at this layer. | Line-item field `market_value` |
| `currency` | `CHAR(3)` | `VARCHAR(3)` | NULL | — | ISO 4217, upper case, exactly three characters. Applies to both `price` and `market_value` on the same row. Never translated. | Line-item field `currency` |

### 2.3 Audit columns

These three are not debugging aids. They are how a number in a report is defended when somebody questions it, and they are the reason this pipeline can survive an audit rather than merely be explained in one.

| Column | Azure SQL | Snowflake | Null | Meaning |
|---|---|---|---|---|
| `content_hash` | `CHAR(64)` | `VARCHAR(64)` | **NOT NULL** | Also an audit column. Resolves a row to the exact bytes of the document it came from. |
| `min_confidence` | `DECIMAL(5,4)` | `NUMBER(5,4)` | **NOT NULL** | The **lowest** confidence of any field anywhere in the source document, 0.0000–1.0000. One value per document, carried onto every row it produced, because a document is accepted or rejected as a unit. A field the model returned unscored contributes 0.0. |
| `bronze_path` | `VARCHAR(512)` | `VARCHAR(512)` | **NOT NULL** | Blob path of the complete raw extraction response, persisted before any parsing ([ADR-0002](adr/0002-persist-bronze-before-parsing.md)). Answers "what did the model actually read". |
| `blob_path` | `VARCHAR(512)` | `VARCHAR(512)` | **NOT NULL** | Blob path of the original PDF in the immutable raw zone, `raw/{broker}/{yyyy-mm-dd}/{file}.pdf`. |
| `model_id` | `VARCHAR(64)` | `VARCHAR(64)` | **NOT NULL** | The pinned extraction model that produced the row, e.g. `broker-alpha-position-v3`. A retrain changes this value, which is how a model change becomes visible in the data rather than only in a deployment log. |

> **These five columns are never dropped to tidy the schema.** If a future change removes any of them, the pipeline stops being auditable and the control stops being defensible. That sentence is in the contract deliberately, because the request will come from someone with good intentions.

### 2.4 Timestamps

| Column | Azure SQL | Snowflake | Null | Timezone | Meaning |
|---|---|---|---|---|---|
| `extracted_utc` | `DATETIME2(3)` | `TIMESTAMP_NTZ(3)` | **NOT NULL** | **UTC**, always | When the pipeline transformed the document. Set by the application, timezone-aware, converted to UTC before write. A naive datetime is rejected by `core/transform.py`. |
| `created_utc` | `DATETIME2(3)` | `TIMESTAMP_NTZ(3)` | **NOT NULL** | **UTC** | When the row was first written. Set by the database (`SYSUTCDATETIME()` / `SYSDATE()`). Never by the application. |
| `updated_utc` | `DATETIME2(3)` | `TIMESTAMP_NTZ(3)` | NULL | **UTC** | When the row was last updated by a MERGE. Null on a row never re-merged. |

**Every timestamp in this contract is UTC. There are no exceptions and no local-time columns.** Northwind runs London and Los Angeles. The moment a break report is generated in one office about a row written in the other, an ambiguous timestamp becomes an argument nobody can settle. Dates (`statement_date`, `trade_date`, `settlement_date`) are calendar dates with no time component and no timezone — they are what the document said, not an instant.

## 3. Numeric precision — the rule and the reason

**Money and quantity are `DECIMAL`. Never `float`. Never `REAL`. Never `DOUBLE`.**

| Concept | Python | Azure SQL | Snowflake | Places |
|---|---|---|---|---|
| Quantity | `Decimal`, quantized to `0.00000001` | `DECIMAL(28,8)` | `NUMBER(28,8)` | 8 |
| Money (price, market value) | `Decimal`, quantized to `0.0001` | `DECIMAL(28,4)` | `NUMBER(28,4)` | 4 |
| Confidence | `Decimal`, quantized to `0.0001` | `DECIMAL(5,4)` | `NUMBER(5,4)` | 4 |

The reason is arithmetic, not taste. `0.1 + 0.2` is not `0.3` in binary floating point. The reconciliation's quantity tolerance is **0.0001** and its market-value tolerance is **0.005** (50 basis points, to absorb pricing-source differences between Aladdin and the counterparty). A pipeline whose representation error is within an order of magnitude of its tolerance produces breaks that appear and disappear depending on which machine ran the job, and there is no worse property for a financial control to have.

Conversion from the extracted value goes **through `str`**. `Decimal(0.1)` captures the binary approximation; `Decimal(str(0.1))` captures the decimal the model reported. The digits stored are the digits read.

Money is four places rather than two because that is what the statements state, and rounding at this layer throws away information the reconciliation needs. Rounding for presentation happens in the report, not in the warehouse.

## 4. Natural key

| Store | Key | Why |
|---|---|---|
| **Azure SQL silver** | `(content_hash, line_no)` | Content hash identifies the document uniquely; line number identifies the position within it. `security_id` alone is not a key — the same security legitimately appears twice on one statement across two settlement dates. |
| **Snowflake gold** | `(CONTENT_HASH, LINE_NO, ACCOUNT_NUMBER, SECURITY_ID, STATEMENT_DATE)` | The same identity, with the business columns included so a human reading the MERGE can see what identity means here without opening this document. The extra columns are functionally dependent on the first two and are not narrowing the key. |

**Both stores are loaded by MERGE, never INSERT.** A re-run — after a transient failure, after an analyst correction, after a reprocess from bronze — converges on the same rows. A direct INSERT would make every retry a data quality incident.

`statement_date` is in the gold key and is **NOT NULL** for every document type. A trade confirmation has no statement date of its own, so it is populated from the trade date. That is not a fudge; it is the deliberate choice that keeps a non-null anchor in the key that both document types populate. Without it the MERGE key contains a NULL and stops matching, silently, producing duplicates. This behaviour lives in `core/transform.py::_as_of_date` and is the kind of detail that gets lost between documents, which is why it is stated in three places.

## 5. Indexes and constraints

| Store | Object | Definition |
|---|---|---|
| Azure SQL | Primary key | `PK_counterparty_position (content_hash, line_no)`, clustered |
| Azure SQL | Index | `IX_position_recon (account_number, statement_date) INCLUDE (security_id, quantity, market_value, currency)` — the reconciliation's read path, covered so it does no lookups |
| Azure SQL | Check | `CK_quantity_range`: `quantity BETWEEN -1000000000 AND 1000000000` |
| Azure SQL | Check | `CK_min_confidence`: `min_confidence BETWEEN 0 AND 1` |
| Azure SQL | Check | `CK_currency_iso`: `currency IS NULL OR LEN(currency) = 3` |
| Snowflake | Clustering | `CLUSTER BY (STATEMENT_DATE, ACCOUNT_NUMBER)` — reporting reads by date and account |
| Snowflake | — | No enforced constraints. Snowflake does not enforce them; validity is guaranteed upstream by the rules engine and by silver's checks. Stated here so nobody assumes gold is self-defending. |

## 6. What is deliberately absent

| Not here | Why | Where it lives |
|---|---|---|
| A surrogate integer ID | The natural key is meaningful and stable. A surrogate would add a second identity that can disagree with the first. | — |
| Base-currency converted values | FX conversion belongs to reporting, with a rate as of a date that reporting chooses. Converting here bakes in one answer forever. | Snowflake reporting views |
| Per-row confidence | A document is accepted or rejected as a unit. A per-row confidence would imply a per-row decision the design does not make. See [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md). | `min_confidence` |
| Break status or classification | Reconciliation output, not ingestion output. Writing it here would couple the two. | `recon/reconcile.py` and its own tables |
| Analyst correction history | Belongs to the exception queue, which owns the correction workflow. | `etl.extraction_exception` |
| Raw counterparty field names | Mapped away at the transform boundary. Downstream never sees a broker's vocabulary. | `field_map` / `line_item_map` in `config/sources.yaml` |
| Soft-delete flags | Rows are never deleted. A superseded document produces a new content hash and new rows. | — |

## 7. Schema evolution

### 7.1 The classification

| Change | Class | Approval needed |
|---|---|---|
| Add a nullable column | **Compatible** | Hem Singh (Architect). Notify downstream consumers. |
| Widen a `VARCHAR` | **Compatible** | Hem Singh. |
| Increase decimal scale without losing places | **Compatible** | Hem Singh + Ravi Mullick, with a data check that no existing value loses precision. |
| Add a non-null column with a default | **Compatible with care** | Hem Singh + backfill plan for existing rows. |
| Rename a column | **Breaking** | Hem Singh **and** Preetinka Sharma **and** Northwind's data owner. |
| Change a type or reduce precision | **Breaking** | As above, plus a migration plan and a dated cutover. |
| Make a nullable column non-null | **Breaking** | As above. |
| Change the natural key | **Breaking, highest severity** | As above, plus Atul, because it is a release-level event. |
| Remove any audit column | **Not permitted** | Requires superseding [ADR-0002](adr/0002-persist-bronze-before-parsing.md) and a written statement from Northwind's audit function. |

### 7.2 The rules

1. **The column list in `core/transform.py::COLUMNS` is the single source of truth.** A change starts there. If the DDL and the code disagree, the code is wrong and the deploy is rolled back — because the sinks build their statements from that list and a mismatch fails loudly rather than writing the wrong column.
2. **Silver and gold change in the same release.** They are the same contract expressed twice, and letting them drift for "just one sprint" is how a warehouse acquires two truths.
3. **Any breaking change requires re-checking, in this order:** `core/transform.py`, `sql/schema.sql`, `sinks/sql_sink.py`, `sinks/snowflake_sink.py`, `recon/reconcile.py`, the Snowflake reporting views owned by Northwind, and the exception queue UI where it displays a changed field.
4. **Downstream consumers get two weeks' notice** of a breaking change, in writing, naming the cutover date. Northwind's EM and EQ reporting modules read this table.
5. **Additive changes still get announced.** A new column nobody knows about is a new column nobody uses.
6. **Nothing changes during a parallel run.** The point of a parallel run is comparing two systems, and changing one of them mid-comparison invalidates it.

### 7.3 Change log

| Version | Date | Change | Class | Approved by |
|---|---|---|---|---|
| 1.0 | 2026-06-19 | Initial | — | Hem, Preetinka, Northwind data owner |
| 1.1 | 2026-07-09 | `model_id` widened `VARCHAR(32)` → `VARCHAR(64)`. Model names with a counterparty prefix and a version suffix were within two characters of the limit. | Compatible | Hem |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/data-contract-counterparty-position.md`**
>
> Produced by: Architect (Hem Singh) with Backend Engineer (Ravi Mullick) using P13 — Design the Data Contract
> Approved by: Preetinka Sharma (PO) 2026-06-19 · Northwind data owner 2026-06-22
>
> Anyone consuming this file can rely on finding:
> - Every column with its type in both stores, nullability, units, meaning, and the upstream field it comes from
> - The decimal precision rule for money and quantity, with the reconciliation tolerances that justify it
> - The timezone rule, stated once and without exceptions
> - The natural key for each store, and why the key is what it is
> - The audit columns and an explicit statement that they are not removable
> - What is deliberately absent from this schema and where each of those things lives instead
> - Schema evolution rules classifying every change as compatible or breaking, naming who approves and what must be re-checked
>
> This file does **not** contain: DDL, MERGE statements, the reconciliation's break classification, or the exception queue's schema.
> Those live in: `sql/schema.sql`, `sinks/sql_sink.py`, `sinks/snowflake_sink.py`, `recon/reconcile.py`.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: per §7.1 — compatible changes need Hem Singh; breaking changes need Hem Singh, Preetinka Sharma, and Northwind's data owner, with Atuladded for a natural-key change. Any change requires re-checking the six artefacts listed in §7.2 rule 3.
