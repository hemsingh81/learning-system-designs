# Implementation Plan — NWD-103, the confidence gate

| | |
|---|---|
| **Produced by** | Rahul Nair, Team Lead |
| **Using** | [P15 — Implementation Plan](../../../AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) |
| **Date** | 2026-06-19 |
| **Status** | Approved · steps 1–9 complete 2026-07-02 · step 10 added 2026-07-31 after [NWD-142](bug-NWD-142.md) |
| **Version** | 1.1 |
| **Story** | [NWD-103](stories/NWD-103.md) · size L, 8 points |
| **Builds from** | [`spec-confidence-gate.md`](spec-confidence-gate.md), [`acceptance-criteria-NWD-103.md`](acceptance-criteria-NWD-103.md) |
| **Assigned** | Tomas Vargas |

---

## 1. How to use this plan

Ten steps. Do them in order.

**The repository compiles and the full test suite passes after every step.** Not after every third step, not at the end of the day. If a step leaves the tree broken, the step is too big and needs splitting — tell me rather than pushing through.

Each step names the files it touches, what changes in them, how to verify it, and a size. S is under an hour. M is up to half a day. L is a day and should make you suspicious; there is one L here and it is deliberate.

**The riskiest unknowns are first.** Steps 1 and 2 exist to find out whether the shape we designed survives contact with a real Document Intelligence response, because if it does not, everything after step 3 changes and I would rather know on Monday morning than Thursday afternoon. Nothing in steps 1–2 produces business value. That is fine. They de-risk the eight steps that do.

Do not write the gate first. It is the most interesting part and it is also the part that depends on everything else being the right shape.

Read [`definition-of-done.md`](definition-of-done.md) before you start and again before you raise the pull request.

---

## 2. The steps

### Step 1 — Pin the real extraction response shape

**Size:** M
**Risk this retires:** the whole plan assumes `ExtractedField` can carry `name`, `value`, `confidence`, `field_type`, `page_number` from a real response. If Document Intelligence does not give us a usable `field_type` per field, the per-type threshold table in the spec has nothing to key on and §3 of the spec needs rewriting before any code is worth typing.

**Files touched**
- `tests/fixtures/broker_alpha_single_page.json` — new
- `tests/fixtures/broker_beta_em_confirm.json` — new

**What changes**
Run one real `broker_alpha` statement and one real `broker_beta_em` confirmation through the deployed custom models. Save the raw responses verbatim as fixtures. Do not hand-edit them; anonymise account numbers and security names only, and record in the file header exactly what was changed.

Then write down, in the pull request description, the answer to three questions:
1. Does every field carry a `type`? Which types actually appear?
2. Does every field carry a `boundingRegions` with a page number?
3. What does the response look like when a table spans two pages?

**How to verify**
Both fixtures load with `json.load` and the three questions are answered with quotes from the response, not from documentation.

**Stop condition.** If question 1 or 2 answers "no", stop and bring it to me and Sofia the same day. The spec changes before the code does.

> **Note added 2026-07-31.** Question 3 was asked here and answered "we will find out". Nobody came back to it. That omission is [NWD-142](bug-NWD-142.md) in its entirety, and it was visible on day one of the build in this document. See step 10.

---

### Step 2 — The input dataclasses

**Size:** S
**Risk this retires:** whether the gate can genuinely be pure. If `ExtractedDocument` cannot be constructed by hand in a test, the exhaustive testing the spec requires is not achievable and the design is wrong.

**Files touched**
- `core/extract.py` — add `ExtractedField` and `ExtractedDocument` dataclasses only. No Azure calls yet, no mapping logic.

**What changes**
`ExtractedField`: `name`, `value`, `confidence`, `field_type`, `page_number`. Every one of `value`, `confidence`, `page_number` is nullable and they mean three different things — [spec §6](spec-confidence-gate.md#6-the-three-nulls) is the reference and the docstring should point at it rather than restating it.

`ExtractedDocument`: `header` dict, `line_items` list of dicts, `model_id`, `page_count`, plus an `all_fields()` iterator that yields every field in the document, header first, then line items in row order.

**How to verify**
```bash
python -c "from core.extract import ExtractedDocument, ExtractedField; \
d = ExtractedDocument(header={}, line_items=[], model_id='m', page_count=1); \
print(list(d.all_fields()))"
```
Prints `[]` and imports nothing from `azure.*`.

---

### Step 3 — Configuration and threshold resolution

**Size:** M
**Risk this retires:** deep-merge semantics. `broker_alpha` overriding `currency` to 0.92 must not wipe out `number`, `date` and `string`. This is the kind of thing that works in the happy case and silently disables three gates in the case that matters.

**Files touched**
- `config/sources.yaml` — the `defaults.confidence` block and `broker_alpha`'s override
- `config/settings.py` — `SourceConfig`, `ConfidenceConfig`, `threshold_for(field_type)`, and the loader's deep merge
- `tests/test_confidence.py` — new file, threshold-resolution tests only

**What changes**
`defaults.confidence.default: 0.80`, `by_field_type: {currency: 0.90, number: 0.90, date: 0.85, string: 0.75}`. `broker_alpha.confidence.by_field_type.currency: 0.92` and nothing else.

`threshold_for` applies the alias map from [spec §3.3](spec-confidence-gate.md#33-field-type-aliases) — `integer`→`number`, `time`→`date`, `countryRegion`/`phoneNumber`/`selectionMark`/`address`/`signature`→`string` — then the table, then the 0.80 default.

Validation at load: any threshold outside 0.0–1.0 fails startup. Spec error case X8. The pipeline does not start with a control silently disabled.

**How to verify**
```bash
pytest tests/test_confidence.py -k threshold -q
```
Tests assert: `broker_alpha` currency is 0.92 **and** its number is still 0.90; `broker_beta_em` currency is 0.90; an unknown type resolves to 0.80; `integer` resolves to 0.90; a YAML with `currency: 1.4` raises at load.

---

### Step 4 — The gate: single-field evaluation

**Size:** M
**Files touched**
- `core/confidence.py` — new. `_check(field, source, row=None) -> dict | None`
- `tests/test_confidence.py` — per-field tests

**What changes**
Three failure conditions in this exact order, per [spec §4.2](spec-confidence-gate.md#42-per-field-evaluation): `value is None` → `missing`; `confidence is None` → `no_confidence`; confidence below threshold → `below_threshold`. Returns `None` on pass.

The failure record is the flat shape from [spec §5](spec-confidence-gate.md#5-failure-output-shape): `field`, `row`, `value`, `confidence`, `threshold`, `why`. Flat because it round-trips through the exception queue's JSON column and Ji-woo renders it directly. `threshold` is the threshold **actually applied**, post-alias and post-override, so an audit does not have to re-derive it from configuration as it stands today.

**Read the boundary sentence in spec §4.2 before you write the comparison.** Confidence exactly equal to the threshold **passes**. The comparison is `confidence < threshold`. Write the test for `confidence == threshold` first.

**How to verify**
```bash
pytest tests/test_confidence.py -q
```
Six tests minimum: below threshold fails; exactly at threshold passes; one step above passes; `value=None` fails with `missing`; `confidence=None` fails with `no_confidence`; the recorded `threshold` on a `broker_alpha` currency failure is 0.92, not 0.90.

---

### Step 5 — The gate: whole-document evaluation

**Size:** S
**Files touched**
- `core/confidence.py` — `evaluate(doc, source) -> GateResult`
- `tests/test_confidence.py`

**What changes**
Walk `doc.header`, then `doc.line_items` in row order, collecting every failure. **Do not short-circuit** — [spec §4.3](spec-confidence-gate.md#43-failures-are-collected-never-short-circuited). Priya needs everything wrong with the document in one pass, not four round trips.

`GateResult` carries `passed`, `failures`, `straight_through`, and a `reason` property producing `low_confidence: currency, quantity` — distinct failing field names, sorted. `passed` is true if and only if `failures` is empty.

**How to verify**
A document with three failing fields returns three failures, header first then line items in row order. A clean document returns `passed=True, failures=[], straight_through=True`.

---

### Step 6 — Minimum confidence

**Size:** S
**Files touched**
- `core/confidence.py` — `min_confidence(doc) -> float`
- `tests/test_confidence.py`

**What changes**
The lowest confidence anywhere in the document. One number per document, not per row — a document is accepted or rejected as a unit, so the weakest field in it is the honest confidence for every row it produced. A field with no reported confidence contributes 0.0. An empty document is 0.0.

**How to verify**
Three tests: mixed confidences return the minimum; a `None` confidence anywhere returns 0.0; an empty document returns 0.0.

---

### Step 7 — Wire the gate into the rules engine

**Size:** L
**Files touched**
- `core/rules.py` — the `confidence_gate` rule type, and the ordered rule runner
- `config/sources.yaml` — the `rules:` list
- `tests/test_rules.py` — new

**What changes**
This is the L and it is where the plan is most likely to slip. The rules engine is config-driven: rules are declared in YAML in order, each with a `type`, an `id`, a `severity` and a `params` block, and the engine dispatches by type. `confidence_gate` becomes one rule type among several, `severity: error`.

Order is: normalisation → `confidence_gate` → `required_fields` → range and value checks → `min_line_items`. Normalisation runs first because gating a quantity of `"1,250"` on a numeric rule before the thousands separator is stripped fails a document for a formatting artefact.

An unknown rule type fails at configuration load, not at runtime. Spec X8 again.

**How to verify**
```bash
pytest tests/test_rules.py -q
```
And a manual read: `config/sources.yaml` must be sufficient to add a counterparty. If adding one would require editing `rules.py`, the rule schema is missing something — extend the schema, not the pipeline.

---

### Step 8 — Exception routing

**Size:** M
**Files touched**
- `sinks/sql_sink.py` — `write_exception(...)`
- `sql/schema.sql` — `etl.extraction_exception`
- `tests/test_rules.py`

**What changes**
A rejected document writes exactly one row to `etl.extraction_exception` carrying `content_hash`, `blob_path`, `bronze_path`, `review_path`, `source_key`, `reason` truncated to 400 characters, `failures_json`, and a database-set `created_utc`. Zero rows to silver. Zero rows to gold. [Spec §7](spec-confidence-gate.md#7-exception-routing).

Re-arrival of the same content hash does not create a second row. The existing row is the one the analyst is working.

If the exception row cannot be written, the pipeline must **not** report success for that document — spec X9. A rejected document that never reached the queue is the worst outcome in the error table.

**How to verify**
Rejected document in `dev`, then:
```sql
SELECT content_hash, source_key, reason FROM etl.extraction_exception
WHERE content_hash = '<hash>';
SELECT COUNT(*) FROM silver.counterparty_position WHERE content_hash = '<hash>';
```
One row, then zero. Upload the same file again under a different name; still one row.

---

### Step 9 — The straight-through metric

**Size:** S
**Files touched**
- `core/logging_config.py` — the custom event
- `core/rules.py` — emit it

**What changes**
Emit one Application Insights custom event per document carrying `source_key`, `straight_through`, `min_confidence`, `page_count`, `model_id`. The straight-through rate is PRD metric M2 — 61% today, 85% the target — and it is simultaneously the business metric, the model-health metric, and the early warning that a counterparty changed their template. It cannot be an afterthought and it is a step in this plan for that reason.

**How to verify**
Process ten documents in `dev` and run the Application Insights query in [`runbook-doc-ingestion.md`](runbook-doc-ingestion.md) §3. Ten events, rate computable.

---

### Step 10 — Completeness rules

**Size:** M
**Added:** 2026-07-31, after [NWD-142](bug-NWD-142.md). Not in v1.0 of this plan, which is the point.

**Files touched**
- `core/extract.py` — record per-field `page_number`, document-level `table_pages`, and `declared_line_item_count`
- `core/rules.py` — two new rule types: `line_item_count`, `page_continuation`
- `config/sources.yaml` — `line_item_count_field` on both sources; the two rules appended to `defaults.rules`
- `tests/test_rules.py` — the `test_completeness_*` class
- `tests/fixtures/broker_alpha_2page.json` — the NWD-142 fixture, retained

**What changes**
`line_item_count`: declared *n* versus extracted *m*; on mismatch the document fails with `why = "line_item_count_mismatch"` carrying both numbers. Where no count field is configured or present, the rule does not fail the document and the run log records `line_item_count_not_declared`. That second half is not optional — a completeness rule that silently does nothing on half the counterparties is worse than no rule, because everybody believes it is running.

`page_continuation`: pages where the layout reported a table, versus pages the extracted line items actually came from. A page in the first set and not the second fails with `why = "page_continuation"`, naming the pages. Where no line item carries page provenance, the rule does not fail and the log records `page_continuation_not_evaluable`.

Both run **after** the confidence gate, so the analyst sees both classes of failure at once.

**How to verify**
```bash
pytest tests/test_rules.py -k completeness -q
```
The load-bearing test is `test_the_gate_alone_would_have_missed_nwd_142`: the two-page fixture **passes the confidence gate and fails the completeness rules**. That assertion is the distinction the bug was made of, and it is the one test in the suite I would not let anyone delete.

---

## 3. What this plan does not cover

| Not here | Where |
|---|---|
| Extraction itself — the Document Intelligence call, the field mapping | NWD-102, NWD-106 |
| Translation of EM documents | NWD-104 |
| Redaction | NWD-105 |
| The MERGE into silver and gold | NWD-107 |
| The analyst UI that renders the failure shape | NWD-108, Ji-woo |

Step 4 produces the failure shape that NWD-108 consumes. Ji-woo cannot start rendering it before step 4 lands, and he should not be asked to guess it. Tell him the day it merges.

## 4. Changelog

| Version | Date | Change | By |
|---|---|---|---|
| 1.0 | 2026-06-19 | Initial, steps 1–9 | Rahul |
| 1.1 | 2026-07-31 | Step 10 added after NWD-142. Step 1's unanswered question 3 annotated rather than deleted — it is the evidence of how the defect got in. | Rahul |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/implementation-plan-NWD-103.md`**
>
> Produced by: Team Lead (Rahul Nair) using P15 — Implementation Plan
> Approved by: Sofia Marchetti (Architect) 2026-06-19 · accepted by Tomas Vargas 2026-06-19
>
> Anyone consuming this file can rely on finding:
> - A numbered build sequence with the riskiest unknowns first and a stated stop condition on each risk step
> - For every step: the exact files touched, what changes in them, a runnable verification, and a size of S, M or L
> - The guarantee that the tree compiles and the suite passes after every step, and what to do when a step breaks that
> - An explicit statement of what is out of scope and which story owns it instead
> - A changelog recording steps added after the fact and why
>
> This file does **not** contain: the behaviour being built, the acceptance criteria, or the code.
> Those live in: `spec-confidence-gate.md` (P11), `acceptance-criteria-NWD-103.md` (P08), `code/doc_ingestion/`.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Rahul Nair. A step added or resized mid-build is recorded in the changelog with the reason, never edited in silently — the shape of the plan is evidence at the retrospective.
