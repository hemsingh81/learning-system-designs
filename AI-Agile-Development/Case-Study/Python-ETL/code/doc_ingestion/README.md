# `doc_ingestion` — Northwind counterparty document ingestion

This is the working code behind the *Python ETL* case study. It is the pipeline
Ravi Mullick builds across Sprints 2 and 3, including the fixes that come out of
Pankaj 's bug reports in the rework chapter.

**What it does in one paragraph.** Northwind Asset Management runs two sets of
books that must agree. Internal records come out of BlackRock Aladdin over REST —
structured, easy. External records arrive as PDFs from prime brokers, custodians
and fund administrators, every one in a different layout, some scanned, some in
Spanish or Portuguese for the EM book. Proving the two agree is **reconciliation**;
where they disagree you have a **break**. Until this pipeline existed, an
operations analyst opened each PDF and typed the numbers into a spreadsheet
first, which is why breaks surfaced on **T+2** instead of **T+1**. This package
removes that step: PDFs land immutably in blob storage, Azure AI Document
Intelligence classifies and extracts them, every field is gated on its confidence
score, a rules engine checks the document is coherent, and only what passes
reaches the warehouse. Everything else goes to an analyst with the reason
attached.

---

## How to read this tree

Read it in pipeline order. Each file's module docstring explains what it does and
why it exists, so the code is the primary text and this README is the map.

```
doc_ingestion/
├── function_app.py            the orchestrator — read this first, it is the spine
├── config/
│   ├── sources.yaml           per-counterparty config: broker_alpha, broker_beta_em
│   └── settings.py            pydantic models + get_settings() with deep-merged defaults
├── core/
│   ├── clients.py             Azure client factory: managed identity, retry policy   [NWD-141]
│   ├── classify.py            route a PDF to the right model; below 0.75 goes to review
│   ├── extract.py             Document Intelligence wrapper + the internal dataclasses
│   ├── confidence.py          THE GATE — pure logic, zero Azure imports
│   ├── rules.py               THE RULES ENGINE — config-driven validation             [NWD-142]
│   ├── transform.py           map extracted fields to the canonical position schema
│   ├── redact.py              AI Language PII redaction, fails closed
│   ├── translate.py           AI Translator for EM docs; descriptive fields only      [NWD-138]
│   ├── idempotency.py         SHA-256 of CONTENT + the processed-document ledger      [NWD-140]
│   └── logging_config.py      structured JSON logging with a correlation id
├── sources/aladdin_api.py     the internal feed: paged positions + trades
├── sinks/
│   ├── blob_sink.py           bronze JSON persistence
│   ├── sql_sink.py            Azure SQL staging (silver) + exception queue writes
│   └── snowflake_sink.py      Snowflake gold: stage then MERGE, never INSERT
├── recon/reconcile.py         full outer join vs Aladdin; four break classes
├── sql/schema.sql             ledger, exception queue, silver table, Snowflake DDL
└── tests/                     pytest — no Azure account required
```

If you only read three files, read `core/confidence.py`, `core/rules.py` and
`function_app.py`. The first is the control, the second is what the first cannot
see, and the third is the order they run in.

### The flow

```
Email / SFTP
     │
     ▼
raw/{broker}/{yyyy-mm-dd}/{file}.pdf        immutable landing zone (ADLS Gen2)
     │  blob trigger  →  enqueue
     ▼
doc-analysis queue                          the trigger never analyses inline
     │  queue trigger
     ▼
classify ──► extract ──► BRONZE (raw JSON, before any parsing)
                              │
                              ▼
                         translate (EM only)
                              │
                              ▼
                       rules engine  =  confidence gate
                                      + field validation
                                      + normalisation
                                      + COMPLETENESS
                         pass │            │ fail
                  ┌───────────┘            └──────────────┐
                  ▼                                        ▼
              redact PII                          etl.extraction_exception
                  │                                (analyst review screen)
                  ▼
        silver.counterparty_position  ──►  GOLD.COUNTERPARTY_POSITION (Snowflake)
                  │
                  ▼
        recon/reconcile.py  ◄──  Aladdin REST positions
                  │
                  ▼
            break report  →  EM / EQ reporting modules
```

### The design invariants

These recur throughout the book. Nothing in this tree contradicts them.

1. **A wrong number is worse than no number.** Every extracted field carries a
   confidence score, and low confidence never silently enters the warehouse.
2. **One failing field sends the whole document to review.** Partial ingestion of
   a statement creates a reconciliation break that looks real.
3. **Bronze is immutable and comes before parsing.** A parsing bug next month is
   reprocessed for free instead of re-paying per page.
4. **Idempotency is by SHA-256 of content, not filename.** Counterparties resend
   the same statement under new filenames constantly.
5. **Redaction fails closed.** If the PII call errors, the raw text is not
   persisted — a marker is.
6. **No API keys anywhere.** Managed identity via `DefaultAzureCredential`; roles
   are `Cognitive Services User`, `Storage Blob Data Contributor`,
   `Key Vault Secrets User`. Snowflake uses key-pair (JWT) auth.
7. **The confidence gate sits upstream of reconciliation.** If low-confidence rows
   flowed through, the break report fills with false positives and operations
   stops trusting it.
8. **Adding a counterparty is a YAML change plus a trained model — never a code
   change.**

### The thresholds

Set by sweeping a labelled ground-truth set from 0.5 to 0.99 per field type and
picking the point where auto-accepted errors on monetary fields hit zero, then
one step up for margin. Never "it felt right".

| Field type | Threshold | Why |
|---|---|---|
| currency | **0.90** (0.92 for `broker_alpha`) | money gets the tightest gate; Alpha's scan quality is weaker |
| number / quantity | **0.90** | a quantity is money by another name |
| date | **0.85** | |
| string / descriptive | **0.75** | a slightly wrong security *name* does not break a reconciliation keyed on identifier and quantity |
| classifier | **0.75** | below this the layout is not guessed at |

Reconciliation tolerances: **0.0001** on quantity (float noise, not a real break)
and **0.005** — 50 basis points — on market value (pricing source differences).

---

## The four bug fixes made visible

Pankaj files five defects in Sprint 3. Four of them live in this code, and each
fix is commented at the site so the reason survives the sprint.

| Bug | What happened | Where the fix lives |
|---|---|---|
| **NWD-142** | A Broker Alpha statement whose positions table spanned a page boundary silently dropped the page-2 line items. It passed the confidence gate — every field it *did* extract was high confidence — and loaded with half the positions. Reconciliation then reported `MISSING_EXTERNAL` breaks that looked like genuine settlement failures. | `core/rules.py`: the `line_item_count` and `page_continuation` completeness rules, plus the page provenance `core/extract.py` records to feed them. Tests: `tests/test_rules.py`, bottom section. |
| **NWD-138** | A Spanish confirmation failed to match because translation ran on the identifier field as well as the descriptive one. | `core/translate.py` — the allow-list via `SourceConfig.is_translatable_field`. Translate prose, never keys. |
| **NWD-140** | A resent statement under a new filename created a duplicate row; one code path was hashing the filename. | `core/idempotency.py` — `content_hash()` takes `bytes` and nothing else. |
| **NWD-141** | A 429 from Document Intelligence at month-end killed the run instead of backing off. | `core/clients.py` — the shared `_RETRY` policy plus `retry_on_transport_error`. |

NWD-139 (the exception queue showing `0.8234567` instead of `82%`) is a
one-line formatting fix in Dzmitry's React screen, which is not in this package.

**Why NWD-142 is the one that teaches.** The code worked. The tests passed. The
confidence gate did not catch it, because confidence is a statement about the
values you *have* and says nothing about the values you do not. It is a missing
data bug, which is the hardest class to see, and the fix is not only code — it
changed the spec (a table continuation rule) and added a new test class.

---

## Running it locally

You do not need an Azure subscription to run the tests. You do need one to run
the pipeline.

### Tests

```bash
python -m venv .venv && . .venv/Scripts/activate   # or: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest tests -q
```

The tests need Python 3.11+ and pass with no Azure account, no network and no
credentials. That is not luck — it is the payoff for keeping `core/confidence.py`
free of Azure imports and deferring the SDK imports in `core/extract.py` into the
call path. `tests/test_extract.py` stubs exactly two SDK symbols, and if that stub
ever needs to grow, the Azure surface has leaked further into the code than it
should have.

### The pipeline

```bash
# Azure resources: a Document Intelligence resource, an AI Language resource,
# an AI Translator resource, a storage account with raw/ bronze/ review/
# containers and a doc-analysis queue, an Azure SQL database, a Snowflake account.

az login          # DefaultAzureCredential picks this up locally

export DOC_INTEL_ENDPOINT="https://<resource>.cognitiveservices.azure.com/"
export LANGUAGE_ENDPOINT="https://<resource>.cognitiveservices.azure.com/"
export TRANSLATOR_ENDPOINT="https://api.cognitive.microsofttranslator.com/"
export STORAGE_ACCOUNT_URL="https://<account>.blob.core.windows.net"
export SQL_CONNECTION_STRING="Driver={ODBC Driver 18 for SQL Server};Server=...;Authentication=ActiveDirectoryMsi;"
export SNOWFLAKE_ACCOUNT="..." SNOWFLAKE_USER="..." SNOWFLAKE_KEY_PATH="..." SNOWFLAKE_WAREHOUSE="..."
export ALADDIN_BASE_URL="https://..." KEY_VAULT_URL="https://<vault>.vault.azure.net/"

# apply the schema first
sqlcmd -S <server> -d <database> -G -i sql/schema.sql

func start        # Azure Functions Core Tools
```

Assign your own account `Cognitive Services User` and `Storage Blob Data
Contributor` so `DefaultAzureCredential` works locally exactly as the Function's
managed identity does in Azure. There is no key-based fallback, deliberately.

### The free tier will lie to you

If you build the sandbox on the F0 tier, know its three traps before you conclude
the model is broken: only the **first 2 pages** of any request are analysed (with
no error raised), files are capped at **4 MB**, and throughput is roughly **1
transaction per second**. Hit all three on purpose once — it is worth more than
reading about them.

---

## What is real and what is illustrative

**Real, and would work as written given the resources:**

- The whole control flow in `function_app.py`, and the ordering of its steps.
- `core/confidence.py` and `core/rules.py` — complete, tested, no stubs. These are
  the two modules the book actually teaches from.
- `core/transform.py`, `recon/reconcile.py`, `core/idempotency.py` — pure logic,
  fully exercised by the test suite.
- `sql/schema.sql` — the Azure SQL half runs as written. The Snowflake half is
  commented out because it targets a different engine, not because it is a sketch.
- The Azure SDK call shapes: `begin_analyze_document` returning a poller you must
  `.result()`, the typed-union field unwrapping, `recognize_pii_entities` with a
  `categories_filter`, `write_pandas` then `MERGE`.

**Illustrative — correct in shape, but pointed at a fictional client:**

- **Northwind Asset Management is fictional**, as are `broker_alpha` and
  `broker_beta_em` and the model ids `broker-alpha-position-v3` /
  `broker-beta-confirm-v1`. The Azure services, BlackRock Aladdin and Snowflake
  are real products named accurately.
- The Aladdin REST endpoints and field names in `sources/aladdin_api.py` follow
  the shape of the real API but are not a substitute for BlackRock's own
  documentation. Check the paths and the header name against it.
- The `field_map` / `line_item_map` entries in `sources.yaml` correspond to labels
  you would define yourself in Document Intelligence Studio when training the
  custom model. They are not fixed by the service.
- The volumes and costs (~200 documents/day, 3 pages average, 12,600 pages/month,
  roughly $420/month) are the case study's worked example. Azure pricing moves —
  verify before quoting it.
- There is no `host.json`, `local.settings.json` or Bicep in this tree. Retry caps
  and the poison-queue routing described in `function_app.py` would be configured
  there.

**Deliberately absent:** the React exception queue screen (Dzmitry's story,
NWD-108), the model training and labelling workflow (that happens in Document
Intelligence Studio, and training is free — you pay only for analysis), and any
path that sends an order anywhere. Nothing in this package writes to a broker.

---

## The metric to watch

**Straight-through rate** — the percentage of documents needing zero human touch.
It started at 61% and the target is 85%. It is simultaneously the business metric
(how much manual work was removed), the model health metric, and the earliest
warning that a counterparty changed their template. `RuleResult.straight_through`
is where the pipeline computes it and `etl.vw_straight_through_rate` is where
operations reads it.
