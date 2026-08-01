# Behaviour Spec — The Confidence Gate (NWD-103)

| | |
|---|---|
| **Produced by** | Hem Singh, Architect |
| **Using** | [P11 — Write the Technical Spec](../../../AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md) |
| **Date** | 2026-06-18 (Revision 1) · 2026-07-31 (Revision 2) |
| **Status** | Approved · Revision 2 approved |
| **Version** | 2.0 |
| **Story** | [NWD-103](stories/NWD-103.md) |
| **Governed by** | [ADR-0001](adr/0001-extraction-approach.md), [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md) |
| **Implements** | [`acceptance-criteria-NWD-103.md`](acceptance-criteria-NWD-103.md) |

---

## 1. Scope

This spec defines the behaviour of the confidence gate: the component that decides whether an extracted document is trustworthy enough to enter the warehouse.

It covers: threshold resolution, the pass/fail decision, the shape of the failure output, exception routing, and error cases.

It does not cover: extraction itself, classification, translation, redaction, transformation, or the analyst UI. Those are separate components with their own specs and stories.

**Implementation boundary.** The gate is `core/confidence.py`. It imports nothing from Azure, opens no connection, and reads no clock. It takes dataclasses in and returns a dataclass out. This is not a style preference — it is the reason the gate can be tested exhaustively without mocks, and the gate is the one component in this pipeline that has to be exhaustively tested.

## 2. Inputs

| Input | Type | Source |
|---|---|---|
| `doc` | `ExtractedDocument` | `core/extract.py`, after field mapping and (for EM sources) translation |
| `source` | `SourceConfig` | `config/settings.py`, resolved from `config/sources.yaml` |

`ExtractedDocument` carries a header field dictionary, a list of line-item field dictionaries, the model ID, the page count, and — from Revision 2 — page provenance and the document's declared line-item count.

Each `ExtractedField` carries `name`, `value`, `confidence`, `field_type`, `page_number`. Any of `value`, `confidence`, `page_number` may be `None`, and each `None` means something different. Section 6 defines what.

## 3. Threshold resolution

### 3.1 The table

Thresholds are per **field type**, not global. A misread security *name* does not break a reconciliation keyed on identifier and quantity; a misread *quantity* does. Gating both at the same number would either let bad money through or reject good documents over cosmetics.

| Field type | Threshold | Applies to | Why this number |
|---|---|---|---|
| `currency` | **0.90** | Price, market value, any monetary amount | The tightest gate in the system. A wrong monetary value produces a market-value break that looks real and costs an investigation. |
| `number` | **0.90** | Quantity, position count, any numeric | Quantity is money by another name. Gated identically to currency. |
| `date` | **0.85** | Statement date, trade date, settlement date | Dates are structurally constrained — a misread date usually fails validation anyway (future date, settlement before trade), so the gate is the second line of defence rather than the first. |
| `string` | **0.75** | Security name, notes, descriptive text | The loosest gate, deliberately. Under [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md) a descriptive failure rejects the whole document, so this threshold is the mitigation for that rule's main cost. |
| *anything else* | **0.80** | The configured default | Applies to field types not in the table and not covered by an alias. |

**Where these numbers came from.** For each field type, the threshold was swept from 0.50 to 0.99 in steps of 0.01 against a labelled ground-truth set of 60 documents (40 `broker_alpha`, 20 `broker_beta_em`). The chosen point is where auto-accepted errors on monetary fields reach zero, then one step up for margin. Sweep run 2026-06-16 by Hem Singh and Ravi Mullick. This is the justification if a threshold is ever questioned; it is not intuition.

### 3.2 Per-counterparty overrides

A source may raise or lower any threshold. In v1 there is exactly one override:

| Source | Field type | Default | Override | Reason |
|---|---|---|---|---|
| `broker_alpha` | `currency` | 0.90 | **0.92** | Scan quality is poor. Their statements are printed, signed and re-scanned, and the sweep showed monetary errors surviving at 0.90 for this source alone. |

Overrides are configuration (`sources.<key>.confidence.by_field_type`), deep-merged over the defaults. A source states only what differs.

### 3.3 Field-type aliases

Document Intelligence reports a longer list of field types than the four the business reasoned about. The long tail collapses onto the four rather than each acquiring its own unmaintained threshold:

| Reported type | Treated as |
|---|---|
| `integer` | `number` |
| `time` | `date` |
| `countryRegion`, `phoneNumber`, `selectionMark`, `address`, `signature` | `string` |

Anything not aliased and not in the table takes the 0.80 default and the applied threshold is recorded on any failure, so an unrecognised type is visible in the exception queue rather than silent.

## 4. Behaviour

### 4.1 The decision

> **Given** an extracted document and its source configuration
> **When** the gate evaluates it
> **Then** it returns a single verdict for the whole document — `passed`, a list of `failures`, and `straight_through`
> **And** `passed` is true if and only if `failures` is empty.

There is no partial verdict, no per-row verdict, and no "pass with warnings" at gate level. [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md) is the reasoning.

### 4.2 Per-field evaluation

Each header field and each field of each line item is evaluated independently against its type's resolved threshold. The three failure conditions, in evaluation order:

> **Given** a field whose `value` is `None`
> **When** it is evaluated
> **Then** it fails with `why = "missing"`.
>
> **Given** a field with a value and `confidence = None`
> **When** it is evaluated
> **Then** it fails with `why = "no_confidence"`.
>
> **Given** a field with a value and a confidence strictly below its threshold
> **When** it is evaluated
> **Then** it fails with `why = "below_threshold"`.
>
> **Otherwise** the field passes.

Confidence exactly equal to the threshold **passes**. The comparison is `confidence < threshold`, not `<=`.

### 4.3 Failures are collected, never short-circuited

> **Given** a document with more than one failing field
> **When** the gate evaluates it
> **Then** every failure appears in the result, header failures first, then line-item failures in row order.

The analyst working the exception queue needs to see everything wrong with the document at once. Short-circuiting on the first failure would make Preeti fix one field, resubmit, and discover the next — four round trips on a document that should take one.

### 4.4 Minimum confidence

> **Given** a document that passed
> **When** it is transformed
> **Then** the lowest confidence anywhere in the document is recorded as `min_confidence` on every row it produces
> **And** a field with no reported confidence contributes 0.0
> **And** a document with no fields at all yields 0.0.

One value for the whole document, not per row. A document is accepted or rejected as a unit, so the weakest field in it is the honest confidence for every row it produced.

## 5. Failure output shape

One failure is a flat record. Flat, not nested, because it round-trips through the exception queue's JSON column and is rendered directly by the UI.

```json
{
  "field": "quantity",
  "row": 6,
  "value": "1250",
  "confidence": 0.71,
  "threshold": 0.90,
  "why": "below_threshold"
}
```

| Key | Type | Meaning |
|---|---|---|
| `field` | string | Canonical field name, post `field_map`. Never the counterparty's name for it. |
| `row` | integer or null | Zero-based line-item index. `null` for a header field. |
| `value` | any or null | What the model read. `null` when `why = "missing"`. |
| `confidence` | float or null | What the model reported. `null` when `why = "no_confidence"`. |
| `threshold` | float | The threshold actually applied, after aliasing and after any per-source override. Recorded so an audit does not have to re-derive it. |
| `why` | string | One of `missing`, `no_confidence`, `below_threshold` — and, from Revision 2, `line_item_count_mismatch`, `page_continuation`. |

`why` values are string literals rather than an enum so the value survives the round trip through JSON storage and back into the UI unchanged.

The gate also produces a short human-readable reason for the queue row: `low_confidence: currency, quantity` — the distinct failing field names, sorted. The UI does not parse it; it displays it in the list view so Preeti can triage without opening every document.

## 6. The three nulls

This is the part of the spec people skim and then get wrong. Each null means something different and each has a different consequence.

| Null | Means | Gate behaviour |
|---|---|---|
| `value is None` | The model returned no value for a field we expected | **Fail.** Absence is not evidence of correctness. A model that returned nothing has not told you the field was empty. |
| `confidence is None` | The model returned a value it did not score | **Fail.** A value nobody scored is a value nobody checked. Custom models do this for some field types. |
| `page_number is None` | The response carried no bounding region for this field | **Not a failure by itself.** Affects Revision 2's completeness rules only, and is handled there explicitly. |

## 7. Exception routing

> **Given** a document the gate rejected
> **When** the pipeline completes processing it
> **Then** one row is written to `etl.extraction_exception`
> **And** zero rows are written to `silver.counterparty_position`
> **And** zero rows are written to `GOLD.COUNTERPARTY_POSITION`
> **And** the ingestion ledger records the document as processed-and-rejected.

The exception row carries:

| Column | Source |
|---|---|
| `content_hash` | SHA-256 of the document content — never the filename |
| `blob_path` | The immutable `raw/` path |
| `bronze_path` | The immutable `bronze/` path, so the raw extraction response is one click away |
| `review_path` | Rendered artefact for the UI, where one exists |
| `source_key` | The counterparty |
| `reason` | The human-readable summary, truncated to 400 characters |
| `failures_json` | The complete failure list from §5, serialised |
| `created_utc` | Set by the database |

**Timing.** The row must be visible in the exception queue within **15 minutes** of the document landing in the raw zone, and for documents arriving before 16:00 London, on the same business day. That is a PRD-level requirement ([§7.3](prd-counterparty-ingestion.md#73-by-when)), not an aspiration, and it is monitored.

**Re-arrival.** A rejected document arriving again with the same content hash does not create a second exception row. The existing row is the one the analyst works.

## 8. Error cases

| # | Case | Required behaviour |
|---|---|---|
| X1 | Classifier confidence below 0.75 | Extraction is never attempted. Exception row with reason `unrecognised_layout`. No per-page extraction charge. |
| X2 | Extraction call fails (5xx, timeout) | Retry with backoff. On exhaustion, exception row with reason `extraction_failed`. The document is never lost. |
| X3 | Extraction returns 429 (throttled) | Exponential backoff with jitter, then retry. Must not fail the run. Month-end is exactly when this happens and exactly when it matters. See [NWD-141](bug-NWD-141.md). |
| X4 | PDF corrupt, encrypted, or unreadable | Exception row with reason `unreadable_document`. Not a crash, not a silent skip. |
| X5 | Redaction (PII detection) fails | Fails closed. Nothing persisted downstream; a marker is written. Document goes to review. |
| X6 | Translation fails on an EM document | Document goes to review. It never proceeds untranslated. |
| X7 | Document has zero line items | Caught by the `min_line_items` rule, not by the gate. The gate on an empty document has nothing to fail, which is why the rule exists. |
| X8 | Configuration invalid — threshold outside 0.0–1.0, or an unknown rule type | Configuration load fails at startup. The pipeline does not start with a control silently disabled. |
| X9 | Azure SQL unavailable when writing the exception row | Retry. If it cannot be written, the pipeline must not report success for that document — a rejected document that never reached the queue is the worst outcome in this table. |
| X10 | Snowflake unavailable after silver has loaded | Silver stands. Gold retries and converges. Not a gate concern; recorded here because people look for it. |

## 9. Non-functional

| Property | Requirement |
|---|---|
| Determinism | Same document, same config, same result, every time. No clock, no randomness, no network. |
| Latency | Gate evaluation is in-memory over an already-parsed document. Sub-millisecond for a 14-line statement; it is not a performance concern and must not be optimised at the cost of clarity. |
| Testability | Unit tests construct `ExtractedDocument` by hand. No mocks, no fixtures requiring Azure. |
| Auditability | The applied threshold is recorded on every failure, so a decision can be reconstructed from stored data without re-reading configuration as it stands today. |
| Configuration | Every threshold is configuration. No threshold is a literal in Python. |

## 10. Changelog

| Version | Date | Change | By |
|---|---|---|---|
| 1.0 | 2026-06-18 | Initial | Hem |
| 1.1 | 2026-06-20 | §3.1 gained the "where these numbers came from" note after Gautam pointed out the spec asserted five numbers with no provenance | Hem |
| **2.0** | **2026-07-31** | **Revision 2 — completeness. See below.** | Hem |

---

# Revision 2 — completeness

**Added 2026-07-31, after [NWD-142](bug-NWD-142.md).** Hem Singh, countersigned Gautam  and Preetinka Sharma.

## R2.1 Why this revision exists

Revision 1 of this spec is correct. Every threshold in it is right, every failure path in it works, and the gate implemented from it passed every acceptance criterion written against it.

On 2026-07-24 Pankaj loaded a Broker Alpha statement carrying fourteen positions across two pages. Nine positions reached Snowflake. Five did not. The gate returned `passed = true` with an empty failure list, and it was correct to: every field it was given was above threshold. The five missing positions were never in the extraction result the gate was handed, so there was nothing for it to fail.

Reconciliation then raised five `MISSING_EXTERNAL` breaks. Those are the breaks that mean a settlement may have failed. Preeti spent an afternoon on them.

**The spec asked whether every number present was trustworthy. It never asked whether every number was present.** The contract on Revision 1 guaranteed thresholds, per-field-type rules, the failure output shape, and exception routing. All four were delivered. Completeness was not on the list, so nobody checked for it, so nobody noticed it was absent — in the story, the acceptance criteria, and this spec, simultaneously, because all three were written from the same mental model.

That is the failure this revision fixes, and the reason it is written up rather than quietly patched.

## R2.2 New inputs

`ExtractedDocument` now carries two things Revision 1 did not use:

| Input | Type | Meaning |
|---|---|---|
| `declared_line_item_count` | int or null | The count the document states about itself, read from the header field named by `source.line_item_count_field`. Null where the layout does not state one. |
| `table_pages` | list of int | Pages on which the layout model reported a table. Compare against the pages the extracted line items actually came from. |

Both come from the raw extraction response, which was already being persisted to `bronze/` under [ADR-0002](adr/0002-persist-bronze-before-parsing.md). No new Azure call and no new cost. The data was there the whole time; nothing was reading it.

## R2.3 Rule — declared vs extracted line-item count

> **Given** a source configured with `line_item_count_field`
> **And** a document whose declared count is *n*
> **And** an extraction that produced *m* line items
> **When** the rules engine evaluates the document
> **And** *n* ≠ *m*
> **Then** the document fails with `why = "line_item_count_mismatch"`
> **And** the failure carries both numbers: `{"declared": n, "extracted": m}`
> **And** no row reaches silver or gold.

> **Given** a source with no `line_item_count_field` configured, or a document where the count field is absent
> **When** the rules engine evaluates the document
> **Then** this rule does not fail the document
> **And** the run log records `line_item_count_not_declared` for that document.

That second clause matters as much as the first. A completeness rule that silently does nothing on half the counterparties is worse than no rule, because everybody believes it is running. Gautam asked for it in review; it is the reason the log line exists.

## R2.4 Rule — table continuation across a page boundary

> **Given** an extraction whose layout result reports a table on pages *P*
> **And** whose extracted line items carry page provenance covering pages *Q*
> **When** the rules engine evaluates the document
> **And** some page in *P* is not in *Q*
> **Then** the document fails with `why = "page_continuation"`
> **And** the failure names the pages that contributed no line items
> **And** no row reaches silver or gold.

> **Given** an extraction where no line item carries page provenance at all
> **When** the rules engine evaluates the document
> **Then** this rule does not fail the document — there is nothing to compare
> **And** the run log records `page_continuation_not_evaluable`
> **And** `min_line_items` and `line_item_count` remain the cover for that case.

This rule is the general one. R2.3 depends on the counterparty telling us how many rows there should be, and a counterparty onboarded next quarter may tell us nothing. R2.4 depends only on the model's own view of where the tables are, which every layout produces.

Both rules run. Neither is a substitute for the other.

## R2.5 Ordering

Completeness runs **after** normalisation and **after** the confidence gate, in `core/rules.py`'s declared order:

```text
normalisation → confidence_gate → required_fields → range/value checks
              → min_line_items → declared_line_item_count → page_continuation
```

Completeness last, because a document failing the confidence gate is going to review anyway and the analyst benefits from seeing both classes of failure together — Revision 1 §4.3 applies to the whole rules engine, not only to the gate.

## R2.6 New `why` values

Added to the §5 vocabulary:

| Value | Meaning | Extra keys on the failure record |
|---|---|---|
| `line_item_count_mismatch` | The document says *n*, we extracted *m* | `declared`, `extracted` |
| `page_continuation` | The model saw a table on a page that yielded no line items | `table_pages`, `line_item_pages`, `missing_pages` |

Both carry `row: null` — they are document-level, not row-level, findings.

## R2.7 Consequences

- **The straight-through rate falls.** Documents that previously loaded incorrectly now go to review. That is a correct fall, not a regression, and it is why M2 moved down before it moved up during the parallel run. Atul told Northwind before the number changed, not after.
- **Two counterparty configurations gained `line_item_count_field`.** `broker_alpha` uses `PositionCount`, `broker_beta_em` uses `TradeCount`. Any new counterparty must be checked for whether one exists at onboarding.
- **A new test class exists.** `tests/test_rules.py::test_completeness_*`, built on multi-page fixtures. Pankaj's position, which is correct: single-page fixtures cannot catch a page-boundary bug, and the fixture set was the real gap.
- **The spec contract itself changed**, gaining a guaranteed line about completeness. Every spec written under the old contract needs the same question asked of it. Gautam owns that sweep — [`retrospective-sprint-3.md`](retrospective-sprint-3.md), action item 1.

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/spec-confidence-gate.md`**
>
> Produced by: Architect (Hem Singh) using P11 — Write the Technical Spec
> Approved by: Gautam  (Team Lead) 2026-06-19 · Preetinka Sharma (PO) 2026-06-19 · Revision 2 countersigned by Gautam  and Preetinka Sharma 2026-07-31
>
> Anyone consuming this file can rely on finding:
> - The per-field-type threshold table with every number stated, plus where those numbers were measured
> - Per-counterparty override rules and the field-type alias map
> - Given/When/Then behaviour for the pass/fail decision, including boundary behaviour at exactly the threshold
> - The exact failure output shape, key by key, with types and null semantics
> - Exception routing: which table, which columns, what must not be written, and by when the row must be visible
> - Error cases including service failures, throttling, invalid configuration, and unreadable documents
> - **What "complete" means for this document type, and how the system detects incompleteness** (Revision 2)
>
> This file does **not** contain: the extraction implementation, the classifier, the canonical schema, or the analyst UI.
> Those live in: `core/extract.py`, `core/classify.py`, `data-contract-counterparty-position.md` (P13), `ui-brief-exception-queue.md` (P14).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Hem Singh approves; Preetinka Sharma countersigns any threshold change. A change here requires re-checking `acceptance-criteria-NWD-103.md`, `config/sources.yaml`, `core/confidence.py`, `core/rules.py`, `tests/test_confidence.py`, `tests/test_rules.py`, and `ui-brief-exception-queue.md` — the failure shape in §5 is the UI's input contract.
