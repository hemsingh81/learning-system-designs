# CLAUDE.md

| | |
|---|---|
| **Produced by** | Rahul Nair, Team Lead |
| **Using** | [P01 — Generate the Project Context File](../../../AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) |
| **Date** | 2026-04-14 (Sprint 0) · **Revised** 2026-08-03 after NWD-142 |
| **Status** | Active |
| **Version** | 1.3 |

> This is the real project context file from the Northwind engagement. It lives at the repo root
> and is read at the start of every AI session. Everything below is written as instructions to
> the AI, not as documentation for humans — that is the point of the file.

---

## What this project is

Counterparty document ingestion for Northwind Asset Management. Broker statements and trade confirmations arrive as PDFs; this pipeline reads them with Azure AI, decides whether the reading can be trusted, and loads what survives into Azure SQL and Snowflake alongside the BlackRock Aladdin feed so the two can be reconciled.

**A wrong number is worse than no number.** Every design decision here follows from that sentence.

---

## Tech stack

| | Version | Notes |
|---|---|---|
| Python | 3.11+ | `match` statements, `X \| None` unions, `Decimal` for all money |
| Azure Functions | `azure-functions==1.21.*` | Blob trigger enqueues; a queue worker does the analysis |
| Document Intelligence | `azure-ai-documentintelligence==1.0.*` | **Not** `azure-ai-formrecognizer` — that is the old v3 package |
| AI Language | `azure-ai-textanalytics==5.3.*` | PII redaction |
| AI Translator | `azure-ai-translation-text==1.0.*` | EM documents only |
| Snowflake | `snowflake-connector-python==3.12.*` | Key-pair JWT auth, never a password |
| SQL Server | `pyodbc==5.2.*` | Azure SQL, silver layer |
| Validation | `pydantic==2.9.*` | Config models, validated at import |
| Retry | `tenacity==9.0.*` | Transport-level errors only; the SDK handles 429s |

---

## Commands

```bash
pytest tests -q                    # full suite, ~16s, must be green before any commit
pytest tests/test_rules.py -q      # rules engine only
ruff check . && ruff format --check .
mypy core sinks sources recon
func start                         # local Functions host
```

---

## Architecture — where things live and why

```
doc_ingestion/
├── function_app.py        Entry points. Blob trigger ENQUEUES; queue worker analyses.
├── config/
│   ├── sources.yaml       Per-counterparty config. Adding a broker is a change HERE, not in code.
│   └── settings.py        Pydantic models. Deep-merges defaults under each source.
├── core/
│   ├── clients.py         Azure client factory. Managed identity, shared retry policy.
│   ├── classify.py        Which counterparty layout is this? Below 0.75 → review, never guessed.
│   ├── extract.py         Document Intelligence wrapper. Header fields + line items + provenance.
│   ├── confidence.py      THE GATE. Pure logic. Zero Azure imports. See the hard rules below.
│   ├── rules.py           THE RULES ENGINE. Config-driven: normalise, then validate.
│   ├── transform.py       Map to the canonical schema. COLUMNS here is the single source of truth.
│   ├── redact.py          PII redaction. Fails closed.
│   ├── translate.py       EM documents. Descriptive fields ONLY.
│   ├── idempotency.py     SHA-256 of CONTENT. Never the filename.
│   └── logging_config.py  Structured JSON, correlation id per document.
├── sources/aladdin_api.py Aladdin REST pull. Paged — read every page.
├── sinks/                 blob (bronze) · sql (silver) · snowflake (gold)
├── recon/reconcile.py     Full outer join vs Aladdin. Four break classes.
├── sql/schema.sql         Must match core/transform.COLUMNS.
└── tests/
```

### The medallion layers

**bronze** — the full raw API response JSON, persisted *before* anything is parsed. Immutable.
**silver** — typed rows in Azure SQL staging.
**gold** — Snowflake, MERGEd, carrying `min_confidence` and `bronze_path` for audit.

If you find a parsing bug next month, reprocess from bronze. Extraction is billed per page; storage is not.

---

## Hard rules — do not change these without asking

1. **`core/confidence.py` imports nothing from Azure.** It is pure logic over dataclasses. This is deliberate — it is why the gate is unit-testable with no mocking. If you need an Azure type there, you are solving the problem in the wrong module.
2. **One failing field rejects the whole document.** Partial ingestion of a statement creates a reconciliation break that looks real. See [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md). This gets challenged regularly; the answer is still no.
3. **Money and quantity are `Decimal`. Never `float`.** Quantity carries 8 decimal places, money 4.
4. **Idempotency hashes content, not filename.** Counterparties resend the same statement under new filenames constantly.
5. **Redaction fails closed.** If the PII call errors, persist a marker — never the raw text.
6. **No API keys anywhere.** `DefaultAzureCredential` only. Roles: `Cognitive Services User`, `Storage Blob Data Contributor`, `Key Vault Secrets User`. Snowflake uses key-pair JWT.
7. **Adding a counterparty is a YAML change plus a trained model.** If onboarding a broker requires a code change, the design has drifted — stop and say so.
8. **Never modify a test to make it pass.** See the [Definition of Done](definition-of-done.md).
9. **`sql/schema.sql` and `config/sources.yaml` are protected.** A hook blocks edits. Ask first — those are production config and the DBA owns the schema.

### Added 2026-08-03, after NWD-142

10. **Completeness is not confidence.** The gate answers *"can I trust this number?"* It does **not** answer *"is this number even here?"* Anything that reads a table, a paged API response, or an array must check what it got against what was declared. `core/rules.py` has `line_item_count` and `page_continuation` for exactly this. See [bug-NWD-142](bug-NWD-142.md).
11. **Never take `result.documents[0]` and move on.** That single line cost a sprint. If a response can contain more than one of something, handle more than one or fail loudly.

---

## Conventions actually used in this repo

- **Docstrings explain why, not what.** The module docstring says why the module exists at all.
- **Comments mark decisions, not mechanics.** `# fail closed: redaction errors must not fall back to raw text` is useful. `# loop over fields` is noise.
- **Config keys are `snake_case`; warehouse columns are `UPPER_SNAKE`; the boundary is `core/transform.COLUMNS`.**
- **Errors carry the correlation id.** Every log line does. Without it a failure at 200 documents a day is unfindable.
- **One structured violation object per rule**, never a bare `bool` — the exception queue shows the analyst *which field and why*.

---

## Gotchas a new engineer hits in week one

| | |
|---|---|
| `begin_analyze_document` returns a **poller**, not a result | Call `.result()`. This is the single most common integration mistake |
| The free tier (F0) analyses **only the first 2 pages** | And raises no error about the rest. Use S0 for anything real |
| F0 also caps files at 4 MB and ~1 transaction/second | Month-end will hit both |
| Document Intelligence was renamed from Form Recognizer | `azure-ai-formrecognizer` is the old package. Do not import it |
| Custom model **training is free** | You are billed only for analysis. Iterating on the model costs labelling time, not money |
| A 50-page scan can outrun the Function timeout | Hence the trigger/worker split. Do not put analysis back in the blob trigger |
| `sources.yaml` deep-merges `defaults` under each source | A partial `confidence` block overrides only the keys it names |

---

## What to ask about rather than decide

- Any change to a confidence threshold. Those numbers came from a threshold sweep against a labelled ground-truth set, not from judgement. Ask Sofia.
- Any change to what reaches the warehouse vs the exception queue. Ask Amara — it changes Priya's working day.
- Anything touching `sql/schema.sql`, Snowflake DDL, or `config/sources.yaml`.
- Adding a dependency.

---

> **Artifact contract — `CLAUDE.md`**
>
> Produced by: Rahul Nair (Team Lead), using [P01](../../../AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md)
> Approved by: Sofia Marchetti, 2026-04-15
>
> Any AI session opening in this repo can rely on finding:
> - The stack with the versions that actually matter
> - Where every module lives and why it exists
> - The hard rules, stated as imperatives, that must not be changed without asking
> - The conventions genuinely present in this code, not generic best practice
> - The week-one gotchas
> - What to ask about rather than decide alone
>
> This file does **not** contain: business requirements, story detail, or design rationale.
> Those are the [PRD](prd-counterparty-ingestion.md), the [stories](stories/), and the [ADRs](adr/).
>
> **If a hard rule here is contradicted by the code, one of them is wrong — stop and say so.**
>
> Changing this file: Team Lead approves. A new hard rule needs the Architect too.
