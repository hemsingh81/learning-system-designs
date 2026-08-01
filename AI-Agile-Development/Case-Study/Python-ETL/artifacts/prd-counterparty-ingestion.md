# PRD — Counterparty Document Ingestion

| | |
|---|---|
| **Produced by** | Preetinka Sharma, Product Owner, Kestrel Software |
| **Using** | [P06 — Write a Full PRD](../../../AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) |
| **Date** | 2026-06-09 (v1.0) · 2026-07-20 (v1.1) |
| **Status** | Approved |
| **Version** | 1.1 |
| **Client** | Northwind Asset Management |
| **Approvers** | Atul(PM, 2026-06-10) · Hem Singh (Architect, 2026-06-10) · H. Okonkwo (Northwind, Head of Investment Operations, 2026-06-11) |

---

## 1. Problem statement

Northwind runs two sets of books that have to agree.

**Internal records** come out of BlackRock Aladdin, Northwind's portfolio management system, over a REST API. They are structured, typed, and arrive on a schedule. They are not the problem.

**External records** come from counterparties — prime brokers, custodians, and fund administrators. They arrive as PDFs. Every counterparty has its own layout. Some are scanned rather than native PDF. Some, for the EM book, are in Spanish or Portuguese.

Proving the two sides agree is **reconciliation**. Where they disagree, you have a **break**, and a break has to be investigated and cleared before the position is trusted for reporting.

Today, before reconciliation can run at all, an operations analyst opens each PDF and types the numbers into a spreadsheet. Three analysts do this, every morning, across roughly 200 documents a day. Preeti Singh is one of them.

That manual keying step is the reason breaks surface on **T+2** — two business days after the trade — instead of **T+1**. A break found on T+2 is a break that has already been reported to the client on a stale position.

Volumes make it worse rather than better over time. Northwind onboarded four new EM counterparties in the last eighteen months. Each one added another layout, another analyst learning where the account number sits on that particular page, and another half-hour to the morning.

## 2. Why now

Three things converged.

1. Northwind's own operating committee has committed to T+1 break detection for the EM book by the end of Q3 2026. That date is external to this project and is not moving.
2. Two of the three analysts doing the keying are on fixed-term contracts ending in October. Renewing them to keep typing PDFs is a decision Northwind does not want to make.
3. The counterparty layouts are now stable enough to train against. Historically they changed often enough that any rules-based extraction would have been rebuilt continuously. That has settled.

## 3. Who this is for

| User | Role | What changes for them |
|---|---|---|
| **Preeti Singh** | Operations analyst, Northwind (London) | Stops keying documents. Starts reviewing only the ones the system could not read confidently. Her morning goes from three and a half hours of typing to a review queue. |
| Two further operations analysts | Northwind (London, Los Angeles) | Same. The LA analyst covers the overnight EM arrivals. |
| Recs team lead | Northwind | Gets a break report at T+1 that does not contain artefacts of typing errors. |
| EM and EQ reporting | Northwind | Read positions out of Snowflake. Their queries do not change; the data arrives earlier and carries an audit trail. |

The person this PRD is written around is Preeti. If a decision in this document makes the pipeline more elegant and Preeti's morning worse, the decision is wrong.

## 4. Success metrics

These are operational metrics. **None of them is a model metric.** We do not report extraction accuracy, F1, precision, recall, or confidence distributions as success measures for this project. Those numbers are useful to Ravi when tuning a model and are meaningless to Northwind's operating committee.

| # | Metric | Baseline | v1.0 target | How it is measured |
|---|---|---|---|---|
| M1 | **Break detection latency** for counterparty positions | T+2 | **T+1** | Timestamp of the first break report containing a given trade date, minus that trade date, in business days. Measured from `GOLD.COUNTERPARTY_POSITION.CREATED_UTC`. |
| M2 | **Straight-through rate** — % of documents needing zero human touch | **61%** (first measured, parallel run week of 2026-07-20) | **85%** | Documents that cleared every rule with `severity: error` ÷ documents received, per business day, from `etl.extraction_exception` against the ingestion ledger. |
| M3 | **Analyst hours spent on counterparty documents** | 10.5 hours/business day across three analysts (~220 hours/month) | **≤1.5 hours/business day** (~32 hours/month) | Exception queue rows worked × median handling time, from UI telemetry. |
| M4 | **Manual keying eliminated** | 100% of documents keyed by hand | **0%** of documents keyed by hand | Binary. No document reaches the warehouse via a spreadsheet. |
| M5 | **False breaks caused by data entry** | 14 in the last full month, by the recs team lead's count | **0** | Break report entries later closed with reason code `KEYING_ERROR`. |
| M6 | **Monthly Azure AI spend** | n/a | **≤$500/month at 12,600 pages** | Azure cost analysis, filtered to the resource group. Current modelled figure is ~$420/month. |

**M2 is the headline.** It is the number Atul reads out at the client steering call, it is the number the runbook tells the on-call engineer to check first, and it is the number that decides whether the analyst headcount question has an answer. Everything else in this document is in service of it.

> **On M2's baseline.** v1.0 of this PRD carried no baseline for M2, because the manual process has no straight-through rate — it is 0% by definition. The 61% recorded above is the first measurement taken from the running system during the parallel run, added in v1.1 on 2026-07-20. That is the number we improve from, not the number we launched against.

## 5. User stories

These are the stories as they were sliced. Full narratives and acceptance criteria live in `stories/`.

| ID | Title | Owner | Size |
|---|---|---|---|
| [NWD-101](stories/NWD-101.md) | Land counterparty PDFs immutably in the raw zone | Ravi | M |
| [NWD-102](stories/NWD-102.md) | Classify an incoming PDF to its counterparty layout | Ravi | M |
| [NWD-103](stories/NWD-103.md) | **Gate every extracted field on its confidence score** | Ravi | L |
| [NWD-104](stories/NWD-104.md) | Translate EM documents to English before matching | Ravi | M |
| [NWD-105](stories/NWD-105.md) | Redact PII before anything is persisted | Ravi | M |
| [NWD-106](stories/NWD-106.md) | Transform extracted fields into the canonical position schema | Ravi | M |
| [NWD-107](stories/NWD-107.md) | Load positions into Azure SQL and Snowflake idempotently | Ravi | L |
| [NWD-108](stories/NWD-108.md) | Exception queue screen for analyst review | Dzmitry | L |

NWD-103 and NWD-108 are the same requirement seen from two ends. NWD-103 decides that a document cannot be trusted. NWD-108 is what a human does about it. Neither is worth building without the other, and they must ship in the same release.

## 6. Scope — v1

**In scope.**

1. Ingestion of PDFs from two counterparties: `broker_alpha` (Broker Alpha, Daily Position Statement, English) and `broker_beta_em` (Broker Beta, EM Trade Confirmations, Spanish).
2. Automatic classification of an arriving document to its counterparty layout, with a minimum classifier confidence of 0.75 below which the layout is never guessed.
3. Field and line-item extraction using a custom model trained per layout family.
4. Translation of EM documents to English before matching, restricted to descriptive fields.
5. A confidence gate applied per field type, with per-counterparty overrides.
6. PII redaction before anything is persisted downstream.
7. Transformation to a single canonical position schema.
8. Idempotent load into Azure SQL (silver) and Snowflake (gold), carrying audit columns.
9. An exception queue screen where an analyst reviews, corrects, and releases or rejects a document.
10. Reconciliation of counterparty positions against the Aladdin feed, producing a classified break report.
11. Onboarding a third counterparty must be a configuration change plus a trained model — never a code change. This is a v1 requirement, not a v2 aspiration, because it is the difference between a pipeline and a product.

**Explicitly out of scope for v1.**

| Not doing | Why not | When |
|---|---|---|
| Any counterparty beyond the two named | We prove the onboarding path with the third one, we do not prove it by doing five | v1.1, one per fortnight |
| Portuguese-language documents | Translator supports it; we have four labelled documents, which is not enough to train | v1.2 |
| Corporate actions, cash statements, fee schedules | Different documents, different schema, different reconciliation | Not scoped |
| Automatic correction of a low-confidence field | A machine guessing at a number a machine already said it was unsure about is the exact failure mode this project exists to prevent | Never |
| Writing anything back to Aladdin | Northwind's change control on Aladdin is a separate programme | Not scoped |
| Email ingestion directly from an inbox | Documents arrive via the existing SFTP drop and mail-rule landing folder. Building an inbox reader is a distraction | v2 |
| A mobile view of the exception queue | Preeti works at a desk with two monitors and a PDF open. That's a nice-to-have | Not scoped |
| Real-time processing | Documents arrive overnight and in the morning. Minutes are fine; seconds buy nothing | Not scoped |

## 7. What happens when the system is not confident

This section is a requirement, not a description. It is the part of this PRD I care about most, and it is the part most likely to be dropped when this document is summarised.

Everything the extraction model returns comes with a **confidence score** — a number between 0 and 1 saying how sure the model was about that specific field. A confidence gate is a checkpoint that compares that score against a limit. Above the limit, the value proceeds. Below it, the document does not enter the warehouse.

**It goes to a person instead.** That is the requirement. Not "is rejected". Not "is logged". Goes to a person, in a form they can act on.

### 7.1 Who sees it

The document appears in the **exception queue**, a screen owned by the Northwind operations analyst team. In v1 that is three named people: Preeti Singh and two colleagues, one of whom works Los Angeles hours to cover overnight EM arrivals.

Nobody else is notified. No email goes to a distribution list. An analyst opens one screen at the start of the morning and sees everything that needs them. If a document needs a human and a human never opens that screen, we have failed — so the queue depth is monitored and alerts at the thresholds in the runbook.

### 7.2 In what form

The analyst must be able to fix the document without opening anything else. Specifically, the queue row must carry:

1. **The rendered PDF**, at the page the failure was found on, not at page one.
2. **The reason it was refused**, in ordinary words — "quantity on line 7 was read at 71% confidence, we require 90%" — not a rule ID and not a stack trace.
3. **Every failing field at once**, not the first one. An analyst who fixes one field, resubmits, and discovers a second failure has been made to do the job twice.
4. **The value the model read**, editable, next to the field it belongs to.
5. **The confidence, as a percentage**, so the analyst can tell "the model nearly had it" from "the model was guessing".
6. **Which counterparty and which document date**, so the analyst can prioritise a month-end statement over a routine one.

The measure of success here is one pass. Preeti opens the document, sees what is wrong, fixes it, releases it, and does not come back to it.

### 7.3 By when

| Document arrives | Must be visible in the exception queue by |
|---|---|
| Any time | **Within 15 minutes of landing in the raw zone** |
| Before 16:00 London on a business day | **Same business day**, without exception |
| After 16:00 London | By 09:00 London the next business day |

"Same day" is the contractual line. A document that cannot be read confidently and is not in front of a human on the day it arrived has already cost Northwind the T+1 target for that position.

### 7.4 What must not happen

- A low-confidence value must never be written to silver or gold, in any form, including "written with a flag".
- A document must never be partially ingested. If one field fails, the whole document goes to review. Half a statement in the warehouse produces a reconciliation break that is indistinguishable from a genuine settlement failure, and the recs team cannot tell them apart. (See [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md).)
- The system must never fill in, infer, or default a value it could not read.
- A document must never disappear. If it cannot be classified, cannot be extracted, or the pipeline errors, it still lands in the exception queue with whatever reason we have.

## 8. Data model impact

| Change | Where | Notes |
|---|---|---|
| New table `silver.counterparty_position` | Azure SQL | Canonical typed rows, one per line item. Natural key `(content_hash, line_no)`. |
| New table `etl.extraction_exception` | Azure SQL | The exception queue's backing store. Carries `failures_json` — the structured list of what failed, which the UI renders directly. |
| New table `etl.ingestion_ledger` | Azure SQL | Content-hash ledger for idempotency. |
| New table `GOLD.COUNTERPARTY_POSITION` | Snowflake | Loaded by MERGE from a staging table, never by INSERT. |
| New audit columns on every position row | Both | `CONTENT_HASH`, `BRONZE_PATH`, `MIN_CONFIDENCE`. These are not optional and are not "nice to have for debugging" — they are how any number in any report is defended. |
| New blob containers `raw/`, `bronze/`, `review/` | ADLS Gen2 | `raw/` and `bronze/` are immutable. |
| No change to Aladdin | — | Read-only. |
| No change to existing recs tables | — | The break report gains a new source, not a new shape. |

Full column-level definitions, types, precision and nullability are in [`data-contract-counterparty-position.md`](data-contract-counterparty-position.md). This PRD does not define them.

## 9. Edge cases and failure states

Written from the operations floor, not from the code.

| # | Situation | Required behaviour |
|---|---|---|
| E1 | The same statement is resent under a different filename | Recognised as the same document. No duplicate rows. Identity is the content, not the name. Counterparties do this constantly. |
| E2 | A statement is resent with a genuine correction | The corrected values replace the originals for that document. The original raw PDF and bronze response are retained. |
| E3 | The positions table runs across a page break | **All** line items are captured, or the document goes to review. Nine rows out of fourteen is the worst possible outcome, because it looks like a real break. |
| E4 | The document is a layout we have never seen | Classifier confidence below 0.75. Goes to review as "unrecognised layout". Never guessed at. |
| E5 | The document is in Spanish | Translated to English before matching — descriptive fields only. Identifiers, account numbers, ISINs and currency codes are never translated. |
| E6 | The PII detection call fails | Nothing is persisted. Fails closed. A marker is written instead of the text. |
| E7 | Document Intelligence returns 429 (throttling) at month-end | Backs off and retries. Does not fail the run. Month-end is exactly when we can least afford a dropped batch. |
| E8 | The PDF is corrupt or password-protected | Exception queue, reason `unreadable_document`. Not a crash, not a silent skip. |
| E9 | A field is absent from the extraction response entirely | Treated as a failure, not a pass. Absence is not evidence of correctness. |
| E10 | The model returns a value with no confidence score at all | Treated as a failure. A value nobody scored is a value nobody checked. |
| E11 | Quantity × price does not agree with the stated market value | Review, even where all three fields individually cleared the gate. One of the three was misread. |
| E12 | A document arrives dated in the future | Review. One day of grace for counterparty clocks and time zones. |
| E13 | Snowflake is unavailable when silver has already loaded | Silver rows stand; the gold load retries. Re-running must converge, not duplicate. |
| E14 | An analyst corrects a document and the correction is itself wrong | The correction is attributed to the analyst and is auditable. We do not prevent it; we make it visible. |
| E15 | A counterparty changes their layout without telling us | Extraction confidence drops across the board, straight-through rate falls, and the queue fills. This is detectable and is the runbook's first diagnostic. |

## 10. Constraints and assumptions

**Constraints.**

- Break detection must reach T+1 for the EM book by end of Q3 2026. Not moving.
- No API keys anywhere. Authentication to Azure services is by managed identity. Snowflake is key-pair. This is Northwind's security standard and predates the project.
- All data stays in the UK South and West US 2 regions. No document leaves Azure for processing.
- The pipeline runs on consumption-billed Azure Functions. It is not permitted to run a always-on cluster for 200 documents a day.

**Assumptions.**

- Roughly 200 documents a day, 3 pages average, spiking at month-end. That is 12,600 pages a month.
- Approximately 50 labelled documents per layout are available for production model training. Fifteen is enough to prove the approach.
- Model training is free. We pay only for analysis. Retraining a layout is therefore an operational decision, not a budget one.
- Counterparty layouts are stable over the v1 period. If this assumption fails, M2 falls and the runbook diagnostic in E15 fires.

## 11. Open questions

| # | Question | Owner | Needed by | Status |
|---|---|---|---|---|
| Q1 | Who signs off a corrected document — the analyst who fixed it, or a second pair of eyes? | Preetinka → Northwind ops | Before NWD-108 build | **Resolved 2026-06-16.** Single analyst for v1. Second-approval is a v2 control and Northwind's audit function agreed. |
| Q2 | What is the retention period on `raw/` and `bronze/`? | Hem → Northwind compliance | Before v1.0 release | **Resolved 2026-07-06.** Seven years, lifecycle to cool at 90 days, archive at 365. |
| Q3 | Does the LA analyst need a separate queue view, or is one shared queue enough? | Dzmitry → Preeti | Before NWD-108 build | **Resolved 2026-06-18.** One queue, filterable by counterparty. Preeti's words: "I'd rather see everything and choose." |
| Q4 | Should a document that fails only on a descriptive field (security name) still go to full review? | Preetinka → Hem | Before NWD-103 build | **Resolved 2026-06-17.** Yes. See [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md). Ravi objected; the objection is recorded there. |
| Q5 | What happens to the exception queue if straight-through rate stalls below 70%? | Atul | Before parallel-run exit | **Open.** Parallel run is at 81% as of 2026-07-29. Revisit at the release gate if it has not reached 85%. |
| Q6 | Does the third counterparty onboarding count as v1 acceptance or v1.1? | Atul → Northwind | Before release readiness | **Open.** Atul's position is that "config change, no code change" is only proven when someone other than Ravi does it. |

## 12. Change log

| Version | Date | Change | By |
|---|---|---|---|
| 1.0 | 2026-06-09 | Initial | Preetinka |
| 1.0 | 2026-06-11 | Approved by Northwind | Preetinka |
| 1.1 | 2026-07-20 | M2 baseline recorded at 61% from the first parallel-run measurement. Q1–Q4 marked resolved. E3 wording strengthened after [NWD-142](bug-NWD-142.md) — it previously said "should be captured", which was not a requirement anybody could test. | Preetinka |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/prd-counterparty-ingestion.md`**
>
> Produced by: Product Owner (Preetinka Sharma) using P06 — Write a Full PRD
> Approved by: Atul(PM) 2026-06-10 · Hem Singh (Architect) 2026-06-10 · Northwind Head of Investment Operations 2026-06-11
>
> Anyone consuming this file can rely on finding:
> - The business problem, who has it, and why it needs solving now
> - Success metrics in operational terms, each with a baseline, a target, and a stated measurement source — and an explicit statement that no model metric is a success metric
> - **What must happen when the system is not confident** — §7 — naming who sees it, in what form, by when, and what must not happen
> - What is in scope for v1 and what is explicitly out, with a reason for each exclusion
> - The named users and what their working day looks like
> - Edge cases and failure states expressed as required behaviour, not as descriptions
> - Data model impact at the table level, and open questions with owners and dates
>
> This file does **not** contain: technology choices, service selection, data schemas, column types, API shapes, thresholds, or sequencing.
> Those live in: `adr/0001-extraction-approach.md` (P12), `spec-confidence-gate.md` (P11), `data-contract-counterparty-position.md` (P13), and `implementation-plan-NWD-103.md` (P15).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Preetinka Sharma approves, countersigned by Atulif the change touches scope or a date. Any change to §4 or §7 requires re-checking `stories/NWD-103.md`, `acceptance-criteria-NWD-103.md`, `spec-confidence-gate.md`, and `ui-brief-exception-queue.md`, because all four are derived from those two sections.
