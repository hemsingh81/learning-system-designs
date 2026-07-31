# Acceptance Criteria — NWD-103, Gate every extracted field on its confidence score

| | |
|---|---|
| **Produced by** | Amara Osei (Product Owner) and Ananya Iyer (QA Engineer), jointly |
| **Using** | [P08 — Write Acceptance Criteria](../../../AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) |
| **Date** | 2026-06-12 (Revision 1) · 2026-07-31 (Revision 2) |
| **Status** | Approved · Revision 2 approved |
| **Version** | 2.0 |
| **Story** | [NWD-103](stories/NWD-103.md) |
| **Behaviour spec** | [`spec-confidence-gate.md`](spec-confidence-gate.md) |

---

## How to read this

Each criterion is Given / When / Then and is written so that it can be turned into a test without a conversation. Where a number appears it is the number, not a placeholder. Where a criterion says "the document goes to review" it means a row is written to `etl.extraction_exception` and nothing is written to `silver.counterparty_position`.

Criteria are grouped: happy paths first, then failure paths, then the paths that are neither — the ones where the pipeline itself is having a bad day.

Ananya's rule for this document: **if a criterion cannot fail, it is not a criterion.** Two lines were cut in review for that reason.

---

## A. Happy paths

### AC-01 — A clean document passes

> **Given** a `broker_alpha` position statement with fourteen line items
> **And** every header field has confidence ≥ its type's threshold
> **And** every line-item field has confidence ≥ its type's threshold
> **When** the confidence gate evaluates the document
> **Then** the gate returns `passed = true`
> **And** `failures` is empty
> **And** `straight_through = true`
> **And** no row is written to `etl.extraction_exception`.

### AC-02 — Thresholds are chosen by field type, not globally

> **Given** an extracted document containing a `date` field at confidence 0.87 and a `currency` field at confidence 0.87
> **When** the gate evaluates it under the default configuration
> **Then** the `date` field passes, because the date threshold is 0.85
> **And** the `currency` field fails, because the currency threshold is 0.90.

### AC-03 — A counterparty can raise a threshold

> **Given** a `broker_alpha` document with a `currency`-typed field at confidence 0.91
> **When** the gate evaluates it
> **Then** the field fails, because `broker_alpha` overrides the currency threshold to 0.92
> **And** the reported `threshold` on the failure is 0.92, not 0.90.

### AC-04 — An unmapped field type falls back to the default

> **Given** an extracted field whose Document Intelligence type is not one of `currency`, `number`, `date`, `string`
> **And** the type is not covered by an alias
> **When** the gate evaluates it
> **Then** the threshold applied is 0.80, the configured default
> **And** the applied threshold appears on any resulting failure so it can be audited.

### AC-05 — Field-type aliases collapse onto the four maintained types

> **Given** an extracted field of Document Intelligence type `integer`
> **When** the gate resolves its threshold
> **Then** it uses the `number` threshold of 0.90
> **And** the same holds for `time` → `date`, and for `address`, `phoneNumber`, `countryRegion`, `selectionMark`, `signature` → `string`.

### AC-06 — A passing document records its weakest field

> **Given** a document that passes the gate
> **And** whose lowest field confidence anywhere is 0.913
> **When** the document is transformed and loaded
> **Then** every row it produced carries `min_confidence = 0.9130`
> **And** that value reaches both `silver.counterparty_position` and `GOLD.COUNTERPARTY_POSITION`.

### AC-07 — Boundary: exactly at the threshold passes

> **Given** a `number`-typed field at confidence exactly 0.90
> **When** the gate evaluates it
> **Then** it passes.
> **And given** the same field at 0.8999999
> **Then** it fails.

*(Ananya added AC-07. The original draft said "below the threshold fails", which leaves the boundary itself undefined, and undefined boundaries are where the arguments happen.)*

---

## B. Failure paths

### AC-08 — A single low-confidence field rejects the whole document

> **Given** a `broker_alpha` position statement with fourteen line items
> **And** thirteen line items are entirely above threshold
> **And** line item 7's `quantity` is at confidence 0.71 against a threshold of 0.90
> **When** the gate evaluates the document
> **Then** `passed = false`
> **And** **no row at all** is written to `silver.counterparty_position` — not the thirteen good ones, not any of them
> **And** one row is written to `etl.extraction_exception`.

### AC-09 — Every failure is reported, not just the first

> **Given** a document with four fields below threshold, on line items 2, 7, 7 and 11
> **When** the gate evaluates it
> **Then** `failures` contains four entries
> **And** each entry carries `field`, `row`, `value`, `confidence`, `threshold`, and `why`
> **And** the row index is present on line-item failures and absent on header failures.

*Rationale, stated because it will be questioned: an analyst who fixes one field, resubmits, and discovers a second failure has been made to do the job twice. Priya works forty documents in a morning. Four round trips per document is the difference between this project working and not.*

### AC-10 — A field the model did not return is a failure, not a pass

> **Given** a document where the extraction response contains no value for `security_id` on line item 3
> **When** the gate evaluates it
> **Then** that field fails with `why = "missing"`
> **And** the document goes to review.

*Absence is not evidence of correctness. A model that returns nothing has not told you the field was empty; it has told you nothing.*

### AC-11 — A field with no confidence score is a failure

> **Given** a field with a value present and `confidence = null`
> **When** the gate evaluates it
> **Then** it fails with `why = "no_confidence"`
> **And** the document goes to review.

*Custom models return no confidence for some field types. Auto-accepting a value nobody scored is precisely the failure the gate exists to prevent.*

### AC-12 — Below threshold is reported with both numbers

> **Given** a `currency` field at confidence 0.86 on a `broker_alpha` document
> **When** the gate evaluates it
> **Then** it fails with `why = "below_threshold"`
> **And** the failure carries `confidence = 0.86` and `threshold = 0.92`
> **And** the exception queue can render "read at 86%, we require 92%" from those two values alone.

### AC-13 — The exception row is actionable

> **Given** a document rejected by the gate
> **When** the exception row is written
> **Then** it carries `content_hash`, `blob_path`, `bronze_path`, `source_key`, a human-readable `reason`, and `failures_json` containing the structured failure list
> **And** `reason` names the failing fields, e.g. `low_confidence: currency, quantity`
> **And** the row is visible in the exception queue within 15 minutes of the document landing.

### AC-14 — Nothing partial reaches the warehouse

> **Given** any document for which `passed = false`
> **When** the pipeline completes processing it
> **Then** `SELECT COUNT(*) FROM silver.counterparty_position WHERE content_hash = @hash` returns 0
> **And** `SELECT COUNT(*) FROM GOLD.COUNTERPARTY_POSITION WHERE CONTENT_HASH = @hash` returns 0
> **And** the ingestion ledger records the document as processed-and-rejected, so a resend of the same content does not reprocess.

### AC-15 — The classifier gate is separate and comes first

> **Given** a document the classifier scores at 0.68
> **When** the pipeline processes it
> **Then** extraction is never attempted
> **And** the document goes to review with reason `unrecognised_layout`
> **And** no per-page extraction charge is incurred.

### AC-16 — A rejected document is never silently retried into acceptance

> **Given** a document rejected by the gate
> **When** the same content arrives again under a different filename
> **Then** it is recognised as the same document by content hash
> **And** it does not create a second exception queue row
> **And** the existing exception row remains the one Priya works.

---

## C. The pipeline having a bad day

### AC-17 — An empty document does not pass by default

> **Given** an extraction response with no header fields and no line items
> **When** the gate evaluates it
> **Then** the document does not reach the warehouse
> **And** `min_confidence` for such a document is 0.0, which is the honest reading of "we do not know".

*Ananya's note: a naive gate returns `passed = true` here, because "no failures" and "nothing checked" look identical from inside the gate. The `min_line_items` rule is what actually catches it. Tested at the pipeline level, not the gate level.*

### AC-18 — The gate is deterministic and has no I/O

> **Given** the same extracted document and the same source configuration
> **When** the gate is evaluated one hundred times
> **Then** the result is identical every time
> **And** the gate module imports nothing from Azure, opens no connection, and reads no clock
> **And** its unit tests construct documents by hand with no mocks.

### AC-19 — A gate failure is not an extraction failure

> **Given** a document that extracted successfully but failed the gate
> **When** the run completes
> **Then** the run is reported as successful
> **And** the document is counted against the straight-through rate as a non-straight-through document
> **And** no alert fires for a single rejection. Alerts are on queue depth and on the straight-through rate, not on individual documents.

### AC-20 — Threshold configuration is validated at startup

> **Given** a `sources.yaml` containing a threshold outside the range 0.0 to 1.0, or a rule of an unknown type
> **When** configuration is loaded
> **Then** loading fails loudly at startup
> **And** the pipeline does not start with a control silently disabled.

---

## D. Traceability

| Criterion | Test | Where |
|---|---|---|
| AC-01, AC-07, AC-08, AC-09 | `test_confidence.py::test_gate_*` | Unit |
| AC-02, AC-03, AC-04, AC-05 | `test_confidence.py::test_threshold_resolution_*` | Unit |
| AC-06 | `test_transform.py::test_min_confidence_on_every_row` | Unit |
| AC-10, AC-11, AC-12 | `test_confidence.py::test_failure_reasons` | Unit |
| AC-13, AC-14, AC-16 | `test_rules.py`, plus E2E fixture run | Unit + E2E |
| AC-15 | `test_extract.py::test_low_classifier_confidence_short_circuits` | Unit |
| AC-17 | `test_rules.py::test_empty_document_rejected` | Unit |
| AC-18 | `test_confidence.py` imports — asserted by the module having no Azure import | Unit |
| AC-19, AC-20 | `test_rules.py::test_config_validation` + operational check | Unit + Ops |
| AC-21, AC-22, AC-23 | `test_rules.py::test_completeness_*` | Unit + E2E |

---

## Revision 2 — completeness (2026-07-31)

**Added after [NWD-142](bug-NWD-142.md).** Amara Osei and Ananya Iyer, countersigned Sofia Marchetti.

### What this revision is fixing, stated plainly

Revision 1 of this document is, as far as it goes, correct. Twenty criteria, every one of them testable, every one of them passing. And a Broker Alpha statement with a positions table spanning a page boundary loaded into Snowflake with nine of its fourteen positions, and not one criterion above was violated.

Every field that was extracted was high confidence. The gate did exactly what it was written to do. The reconciliation then reported five `MISSING_EXTERNAL` breaks that looked identical to a genuine settlement failure, and Priya spent an afternoon on them.

The criteria above answer the question *"is this number trustworthy?"* — thoroughly. Nobody wrote a criterion answering *"is this number here?"* AC-10 comes closest and does not cover it: AC-10 is about a **field** the model did not return within a line item it did return. It has nothing to say about a line item the model never returned at all.

That gap was in the story, the spec, and this document simultaneously, because all three were written from the same mental model. That is what makes it worth recording rather than quietly fixing.

### AC-21 — Declared line-item count must match extracted line-item count

> **Given** a `broker_alpha` position statement whose header field `PositionCount` reads 14
> **And** the extraction returned 9 line items
> **When** the rules engine evaluates the document
> **Then** the document fails with reason `line_item_count_mismatch`
> **And** the failure states both numbers: declared 14, extracted 9
> **And** no row reaches silver or gold
> **And** the exception queue row opens the PDF at the first page whose line items are missing.

### AC-22 — A table page that contributed no line items is a failure

> **Given** an extraction response whose layout result reports a table on pages 1 and 2
> **And** every extracted line item has page provenance of page 1
> **When** the rules engine evaluates the document
> **Then** the document fails with reason `page_continuation`
> **And** the failure names the page that contributed nothing, i.e. page 2.

*This is the cover for layouts that do not state a count. `broker_beta_em` states `TradeCount`; a counterparty onboarded next quarter may state nothing, and AC-21 would then be unenforceable. AC-22 does not depend on the document telling us anything.*

### AC-23 — A document that states no count and shows one table page still passes

> **Given** a document from a source with no `line_item_count_field` configured
> **And** whose layout reports a table on page 1 only
> **And** whose line items all came from page 1
> **When** the rules engine evaluates it
> **Then** the completeness rules do not fail it
> **And** the reason is recorded in the run log as `line_item_count_not_declared`, so the coverage gap is visible rather than assumed away.

*Included because Rahul asked the right question in review: "what does this rule do when it cannot do anything?" A completeness check that silently no-ops on half the counterparties is worse than no check, because everyone believes it is running.*

### Consequences of Revision 2

- Three counterparty layouts must be checked for whether they state a line-item count. `broker_alpha` and `broker_beta_em` do; that is recorded in `config/sources.yaml` as `line_item_count_field`.
- The straight-through rate will fall when these rules are enabled, because documents that previously loaded incorrectly will now go to review. That is a correct fall, not a regression, and Farhan was warned before the parallel-run numbers moved.
- Every acceptance criteria document written before 2026-07-31 needs the same question asked of it: *does this cover completeness, or only correctness?* Rahul owns that sweep. See [`retrospective-sprint-3.md`](retrospective-sprint-3.md), action item 1.

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/acceptance-criteria-NWD-103.md`**
>
> Produced by: Product Owner (Amara Osei) and QA (Ananya Iyer) using P08 — Write Acceptance Criteria
> Approved by: Rahul Nair (Team Lead) 2026-06-13 · Sofia Marchetti (Architect) 2026-07-31 for Revision 2
>
> Anyone consuming this file can rely on finding:
> - Given/When/Then criteria for the happy paths, with every threshold stated numerically and boundary behaviour defined
> - Given/When/Then criteria for the failure paths, including what must **not** be written when a document is rejected
> - Criteria covering the pipeline's own failure modes, not only the document's
> - **Criteria covering completeness — whether all the data that should have been extracted was** (Revision 2)
> - A traceability table mapping every criterion to the test that proves it
>
> This file does **not** contain: the threshold table's justification, the failure output's JSON shape, exception routing mechanics, or UI behaviour.
> Those live in: `spec-confidence-gate.md` (P11) and `ui-brief-exception-queue.md` (P14).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Amara Osei and Ananya Iyer jointly; Sofia Marchetti countersigns any change touching thresholds or completeness. Adding or changing a criterion requires re-checking `spec-confidence-gate.md`, `tests/test_confidence.py`, `tests/test_rules.py`, and the traceability table in §D.
