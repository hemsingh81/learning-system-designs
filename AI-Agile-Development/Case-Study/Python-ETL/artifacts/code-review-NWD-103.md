# Code Review — NWD-103, the confidence gate

| | |
|---|---|
| **Produced by** | Rahul Nair, Team Lead |
| **Using** | [P23 — Review Someone Else's Code](../../../AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md) |
| **Date** | 2026-06-22 |
| **Status** | Changes requested → all findings answered 2026-07-24 → **Approved and merged 2026-07-24** |
| **Version** | 1.0 |
| **Story** | [NWD-103](stories/NWD-103.md) |
| **Author of the code** | Tomas Vargas |
| **Branch / PR** | `feature/NWD-103-confidence-gate` · PR #47 · head `4a1c9e2` |
| **Reviewed against** | [`spec-confidence-gate.md`](spec-confidence-gate.md) v1.1, [`acceptance-criteria-NWD-103.md`](acceptance-criteria-NWD-103.md) v1.1, [`definition-of-done.md`](definition-of-done.md) v1.0 |

---

## 1. Verdict

**Changes requested.** One defect, which must be fixed before merge. Two preferences, which are yours to take or decline. One question, which is a question and not a disguised instruction.

The shape is right. `core/confidence.py` imports nothing from `azure.*`, opens no connection and reads no clock, which is exactly what [spec §1](spec-confidence-gate.md#1-scope) asks for and is the reason `tests/test_confidence.py` can construct documents by hand and test this thing exhaustively without a single mock. Failures are collected rather than short-circuited. The applied threshold is recorded on every failure record. Per-source override resolution is correct and the deep merge does not clobber the field types the source did not mention — I checked that specifically because it is the failure that looks fine in the happy case and silently disables three gates in the case that matters.

Diff size 312 added, 4 removed, across 5 files. I read all of it. Section 5 records what I could not verify by reading.

**Severity key:** **defect** blocks the merge · **preference** never blocks it · **question** blocks the merge only until it is answered, and the answer may well be that nothing changes.

---

## 2. Findings

### F1 — `core/confidence.py:94` — the threshold comparison rejects a field sitting exactly on the threshold · **defect**

```python
92	    # Above the bar: the field is trustworthy.
93	    threshold = source.confidence.threshold_for(f.field_type)
94	    if f.confidence > threshold:
95	        return None
96	
97	    return {
98	        "field": f.name,
99	        ...
100	        "why": WHY_BELOW_THRESHOLD,
101	    }
```

A field whose confidence is **exactly** the threshold takes the fall-through and is recorded as `below_threshold`. It is not below the threshold. It is on it.

[Spec §4.2](spec-confidence-gate.md#42-per-field-evaluation) is explicit and I think it is explicit because Sofia expected this to be got wrong:

> Confidence exactly equal to the threshold **passes**. The comparison is `confidence < threshold`, not `<=`.

So `>` here should be `>=` — or, better, invert it and write the failure condition the way the spec writes it, `if f.confidence < threshold:`, which removes the reader's need to do the negation in their head at all.

**Why this matters more than an off-by-one usually does.** Document Intelligence returns confidences quantised to three decimal places and the values cluster on round numbers. A `date` field reporting exactly `0.850` is not a rare event — it is roughly 1 in 90 date fields on our labelled set. Under [ADR-0003](adr/0003-one-failing-field-rejects-the-document.md) one failing field rejects the whole document, so each of those sends an entire statement to Priya's queue for a field that the spec says was fine. That is straight-through rate lost, and it is lost in the direction that looks like the system being careful, which is the direction nobody investigates.

**Why the tests did not catch it.** `tests/test_confidence.py::test_below_threshold_fails` uses `0.71` against `0.90`. `test_above_threshold_passes` uses `0.94`. Neither goes anywhere near the boundary. [DoD §2.2](definition-of-done.md#2-tests) asks for exactly at, one step below, one step above — the boundary test is missing, not just failing.

**Required:** fix the comparison, and add `test_confidence_exactly_at_threshold_passes` for all four field types plus the `broker_alpha` 0.92 override. Write the test first and watch it fail against the current code.

---

### F2 — `core/confidence.py:62` — `_check` is a weak name for the function that makes the decision · **preference**

```python
62	def _check(
63	    f: ExtractedField,
64	    source: SourceConfig,
65	    row: int | None = None,
66	) -> dict | None:
```

`_check` says nothing. Everything in this module checks something. Reading `evaluate()` you hit `_check(f, source)` and have to jump to the definition to learn whether it returns a bool, a failure, or a mutated field.

`_evaluate_field` would say it. It also parallels `evaluate` at document level, so the pair reads as one idea at two scales.

The parameter `f` I would leave alone, incidentally — it is one character in a six-line function where the type annotation is right there, and renaming it to `extracted_field` would make the failure-record literals wrap. Short names are fine in short scopes.

Take it or leave it. It does not block.

---

### F3 — `core/confidence.py:72–102` — the six-key failure record is written out three times · **preference**

The three failure branches each build the same dict literal with the same six keys, differing only in `value`, `confidence` and `why`. A fourth `why` value is coming when the completeness work lands, and the shape is also the exception queue's JSON contract and Ji-woo's input contract — three copies of a contract is three places to forget to update.

```python
def _failure(f, *, row, threshold, why, value=..., confidence=...) -> dict:
    ...
```

Then each branch is two lines and the key set exists once.

Two honest counter-arguments, which is why this is a preference and not a defect. The literals are visible: you can read the failure shape straight out of the function without following a call, and [spec §5](spec-confidence-gate.md#5-failure-output-shape) is a document you want to be able to diff against code by eye. And a helper with two defaulted keyword-only arguments is not obviously simpler than what it replaces.

Your call. If you leave it, leave it deliberately rather than by not deciding.

---

## 3. Question

### Q1 — `core/confidence.py:104` — why does this return `None` here?

```python
104	    return None
```

A function that returns either a failure dictionary or `None` is a function whose return value has two meanings, and at the call site `None` reads as "nothing happened" rather than "this field is fine". I expected either a `FieldResult` with a boolean, or an empty list.

Not an instruction. I want to know the reasoning, because there may be one I am not seeing.

**Tomas's answer, 2026-06-22:**

> It is deliberate and it is for the call site. `evaluate()` walks header fields and line-item fields with a walrus in a comprehension:
>
> ```python
> failures = [c for f in doc.header.values() if (c := _check(f, source)) is not None]
> ```
>
> `None`-means-passed lets one expression both filter and collect. With a `FieldResult` object I would build a result for every field in the document and throw away the 95% that passed, and the comprehension becomes a loop with an `if result.failed` inside it. Roughly 40 fields on a 14-line statement, so it is not a performance argument — it is that the passing case produces nothing, which is what the code then says.

That is a good reason and I would not have reconstructed it from the code.

**Resolution: a comment, not a code change.** The reasoning is now three lines in the docstring:

```python
    """Evaluate one field against its type's threshold.

    Returns the failure record, or ``None`` when the field passed. ``None``
    rather than a result object because ``evaluate()`` filters and collects in
    one comprehension — a passing field produces nothing, and the code says so.
    """
```

Worth being explicit about what happened here, because it is the most common thing a review gets wrong in both directions. I did not know why the code was shaped that way. The two available bad moves were to say nothing and stay confused, or to write "change this to return a result object" and have Tomas either comply with a worse design or spend a day arguing. Asking cost one line and bought a comment that stops the next reader — including the next model reading this file as context — asking the same thing.

A review finding that resolves to a comment is a successful finding.

---

## 4. Checked and correct

Recorded so nobody re-reviews it.

| Area | Result |
|---|---|
| Purity — no `azure.*`, no I/O, no clock, no randomness | Correct. Spec §1 and §9. |
| Failure collection, not short-circuit; header first, then line items in row order | Correct. Spec §4.3. |
| `threshold` recorded post-alias and post-override on every failure | Correct, and the `broker_alpha` currency case shows 0.92. Spec §9 auditability. |
| Three-null semantics: `missing` / `no_confidence` / `page_number` not a failure | Correct and tested. Spec §6. |
| `min_confidence` — `None` contributes 0.0, empty document 0.0 | Correct. Spec §4.4. |
| `reason` string — distinct field names, sorted | Correct. Spec §5. |
| No thresholds hard-coded in Python | Correct. All in `config/sources.yaml`. DoD §1.4. |
| No secrets, keys or connection strings | None present. DoD §1.3. |
| Deep merge preserves unmentioned field types | Correct, and tested directly. |

## 5. Not verified by this review

- End-to-end behaviour against a real document. That is Ananya's, [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md).
- Exception-row writing. Different file, plan step 8, not in this diff.
- Whether the spec is *right*. I reviewed the code against the spec. Both being wrong together is a failure mode this review cannot detect, and two days later it turned out to be the failure mode we had — see [NWD-142](bug-NWD-142.md) and [`retrospective-sprint-3.md`](retrospective-sprint-3.md).

## 6. Outcome

| Finding | Severity | Outcome |
|---|---|---|
| F1 — threshold boundary comparison | defect | Fixed. `if f.confidence < threshold:` at `core/confidence.py:94`. Boundary tests added for four field types plus the override, committed before the fix. |
| F2 — `_check` naming | preference | Declined, then reconsidered. Renamed to `_evaluate_field` in a follow-up. |
| F3 — extract a `_failure` helper | preference | Declined, deliberately: the literals keep the failure shape diffable against spec §5 by eye. Recorded in the PR thread so it is a decision and not an oversight. |
| Q1 — why return `None` | question | Resolved with a docstring comment. No code change. |

Merged `4a1c9e2..b7d3f10`, 2026-07-24. Tomas's responses were written with [P28 — Respond to Code Review Feedback](../../../AI-Prompts-Library/phase-6-rework/P28-respond-to-code-review-feedback.md); this file is the worked example that prompt reads from.

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/code-review-NWD-103.md`**
>
> Produced by: Team Lead (Rahul Nair) using P23 — Review Someone Else's Code
> Reviewed code by: Tomas Vargas · PR #47 · merged 2026-07-24
>
> Anyone consuming this file can rely on finding:
> - Every finding carrying a `file:line` reference, a severity, and the reasoning for the severity
> - Defects and preferences labelled separately, with an explicit rule for which of them blocks a merge
> - For a defect: why it matters in operational terms, and why the existing tests did not catch it
> - Questions kept as questions, with the author's answer and the resolution recorded — including when the resolution is a comment rather than a code change
> - A "checked and correct" list, so no one re-reviews ground already covered
> - A "not verified" list, so nobody mistakes this review for a guarantee it never made
> - A closing table of every finding and what actually happened to it
>
> This file does **not** contain: the fixes themselves, end-to-end test results, or a judgement on whether the spec is correct.
> Those live in: PR #47, `bug-NWD-142.md` and the E2E run (P22), and `spec-confidence-gate.md` Revision 2 (P29).
>
> **If any guarantee above is missing, this review is not ready to act on.** Send it back.
>
> Changing this file: Rahul Nair, until Outcome is filled in; then it is closed. Findings are never deleted after the fact — a declined preference is part of the record.
