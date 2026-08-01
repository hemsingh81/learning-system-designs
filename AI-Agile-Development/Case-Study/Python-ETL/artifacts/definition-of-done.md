# Definition of Done — Northwind counterparty ingestion

| | |
|---|---|
| **Produced by** | Gautam , Team Lead · Pankaj , QA Engineer |
| **Using** | [P17 — Definition of Done](../../../AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) |
| **Date** | 2026-06-08 (v1.0) · 2026-06-30 (v1.1, after [NWD-142](bug-NWD-142.md)) |
| **Status** | Agreed by the whole team, 2026-06-09 · v1.1 agreed 2026-06-30 |
| **Version** | 1.1 |
| **Applies to** | Every story in the epic, every bug fix, every configuration change that reaches an environment |

---

## 0. What this is for

A story is Done when the team would be comfortable being asked about it six months from now with nobody available to explain it.

This is one list, applied identically to an eight-point story and a one-line fix. Sections are not optional depending on who is busy. Where an item genuinely does not apply — a config-only change has no UI — the pull request says so in one line and says why. "N/A" without a reason is not an answer.

Preetinka owns whether a story met its acceptance criteria. Gautam owns whether it met this list. Those are different questions and they are asked separately.

---

## 1. Code

| # | Condition |
|---|---|
| 1.1 | The acceptance criteria in the story are all satisfied, checked one by one against the criteria file, not from memory. |
| 1.2 | The behaviour matches the governing spec. Where it does not, §5 applies. |
| 1.3 | No secrets, connection strings, keys or tokens in source, config, tests or logs. Authentication is managed identity via `DefaultAzureCredential`; Snowflake is key-pair. |
| 1.4 | Every threshold, tolerance, path and model ID is configuration. No numeric literal that a business person could argue about lives in Python. |
| 1.5 | Structured logging on every branch that swallows or transforms an error. A log line carries `content_hash` and `source_key` so a document can be traced end to end. |
| 1.6 | The change is idempotent, or the pull request explains why it cannot be. Re-running the pipeline over the same document produces the same rows. |
| 1.7 | No commented-out code, no `TODO` without a ticket ID, no debug print. |
| 1.8 | Type hints on every public function. `mypy` and `ruff` clean. |

## 2. Tests

| # | Condition |
|---|---|
| 2.1 | Unit tests cover every branch of the new logic, including each failure branch. A branch that only exists to handle an error is the branch most likely to be wrong. |
| 2.2 | Boundary values are tested explicitly: exactly at a threshold, one step below, one step above. Not "around" the boundary — **on** it. |
| 2.3 | Every `None` case in the input dataclasses is tested, and the test asserts which *kind* of null it is. |
| 2.4 | At least one test uses a real anonymised counterparty document, not only hand-constructed objects. |
| 2.5 | Tests fail for the right reason. Before it passes, each new test has been seen to fail with the fix reverted. |
| 2.6 | Test names read as sentences describing behaviour. `test_one_bad_line_item_fails_whole_document`, not `test_gate_2`. |
| 2.7 | Every bug fix ships with a regression test that reproduces the original report. The test is committed **before** the fix, in its own commit. |
| 2.8 | Fixtures cover the shape of the input, not only its content — multi-page, multi-table, zero-line-item, and translated variants where the source has them. |

## 3. Review

| # | Condition |
|---|---|
| 3.1 | Reviewed by someone who did not write it. Gautam reviews backend; Dzmitry and Gautam cross-review frontend. |
| 3.2 | Every review finding is answered: fixed, or declined with a reason recorded in the thread. Silence is not an answer. |
| 3.3 | Findings are labelled **defect** or **preference**. A preference never blocks a merge; a defect always does. |
| 3.4 | A clarity question — "why does this return `None` here?" — is resolved. Often the resolution is a comment rather than a code change, and that is a legitimate outcome. See [`code-review-NWD-103.md`](code-review-NWD-103.md). |
| 3.5 | Commits are clean and separated: test, fix, docs. Not one commit called "fixes". |

## 4. Documentation

| # | Condition |
|---|---|
| 4.1 | The governing spec, story, and acceptance criteria are consistent with what was actually built. |
| 4.2 | Any new configuration key is documented in `config/sources.yaml` with a comment saying what it is for, not what it is called. |
| 4.3 | Any new failure mode is in [`runbook-doc-ingestion.md`](runbook-doc-ingestion.md) with the exact remediation command. A failure mode with no runbook entry is a 3am phone call. |
| 4.4 | A decision that is expensive to reverse has an ADR. If two people argued about it for more than an hour, it needs one. |
| 4.5 | `CLAUDE.md` is updated when a convention, path or command changes. It is the context every prompt in this project runs with; stale context produces confidently wrong output. |

## 5. AI-specific

These four exist because the rest of this document was written for a team where a human typed every line. That is no longer the case here, and the failure modes are different.

| # | Condition |
|---|---|
| **5.1** | **A human has read every line the AI wrote, and can explain why it is there.** Not skimmed, not approved on the strength of passing tests. If you cannot explain a line in review, it does not merge. Generated code that nobody understands is a liability that compounds — it is reviewed by nobody, maintained by nobody, and trusted by everybody. |
| **5.2** | **No test was modified to make it pass.** If a test fails, the code is wrong until proven otherwise. Changing an assertion to match the behaviour you just wrote deletes the only evidence you had. Where a test genuinely encoded the wrong expectation, the change is a separate commit with a separate justification, reviewed on its own. |
| **5.3** | **If behaviour diverged from the spec, the spec was updated — or the behaviour was changed back.** Both are acceptable. Leaving the two disagreeing is not. A spec that describes a system nobody built is worse than no spec, because the next person reads it and believes it. |
| **5.4** | **Every story that produces rows states what "complete" means for its input, and how incompleteness is detected.** Added 2026-06-30 after [NWD-142](bug-NWD-142.md). |

### On 5.4

NWD-142 was a document that produced nine rows where fourteen were correct. Nothing failed. No exception, no failing test, no log line, and a confidence gate that returned `passed = true` and was right to — every field it was handed was above threshold.

We had a control that answered *"can I trust this number?"* and we had all quietly assumed it also answered *"is this number here?"*. It never did. Neither did the story, the acceptance criteria, or the spec, because all three were written from the same mental model on the same afternoon.

So the condition is now explicit, and it has two halves that must both be answered in the story:

1. **What does complete look like for this input?** Fourteen positions because the header says `PositionCount = 14`. Every page carrying a table contributes at least one row. Every account in the Aladdin pull is present, across every page of a paged response.
2. **How would the system know it was incomplete?** Name the mechanism. A declared-count comparison, a page-provenance comparison, a row-count reconciliation against the source. "The confidence gate covers it" is not a mechanism, and is the specific wrong answer this clause exists to prevent.

Applies to any story that reads a paged, chunked, or tabular source. If the answer is honestly "this input cannot be partial", write that sentence down and say why. That takes thirty seconds and it is the sentence that would have caught NWD-142.

## 6. Data quality

| # | Condition |
|---|---|
| 6.1 | Row counts reconcile: rows out equals rows in, or the difference is explained by a named, logged rule. Owned end to end by [`tests/test_rules.py`](../code/doc_ingestion/tests/test_rules.py) and the data-quality suite. |
| 6.2 | Every canonical column in [`data-contract-counterparty-position.md`](data-contract-counterparty-position.md) is populated or explicitly nullable. No column silently becomes "always null in practice". |
| 6.3 | `min_confidence` and `bronze_path` are carried onto every row that reaches gold. Without them a number in a report cannot be defended. |
| 6.4 | Idempotency is by SHA-256 of content, never filename, in **every** code path. See [NWD-140](bug-NWD-140.md) for what happens when one path drifts. |
| 6.5 | Rejected documents produce exactly one exception queue row and zero silver rows and zero gold rows. |
| 6.6 | The straight-through rate is measured for the change and reported. A change that moves it is worth knowing about in either direction. |

## 7. Release

| # | Condition |
|---|---|
| 7.1 | Deployed and exercised in `dev` against real counterparty documents, not fixtures alone. |
| 7.2 | Alerts exist for the new failure modes, and each alert has a runbook entry it links to. |
| 7.3 | Rollback is a documented single step, and it has been performed at least once in `dev`. |
| 7.4 | Application Insights shows the change: a dashboard tile, a new custom event, or a query saved in the runbook. |
| 7.5 | Preetinka has accepted it. Not "seen a demo" — accepted, against the criteria file. |
| 7.6 | Nothing goes to production without the parallel run in [`release-readiness-v1.0.md`](release-readiness-v1.0.md). That gate is not part of a story and no story can satisfy it. |

---

## 8. Changelog

| Version | Date | Change | By |
|---|---|---|---|
| 1.0 | 2026-06-08 | Initial. Sections 1–3, 4, 6, 7, and the first three AI clauses. | Gautam, Pankaj |
| 1.1 | 2026-06-30 | §5.4 added after NWD-142. §2.8 (fixture shape) and §6.1 (row-count reconciliation) added with it — the same gap seen from the test side and the data side. | Gautam, Pankaj |

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/definition-of-done.md`**
>
> Produced by: Team Lead (Gautam ) and QA Engineer (Pankaj ) using P17 — Definition of Done
> Agreed by: the whole team, 2026-06-09 · v1.1 agreed 2026-06-30 · Preetinka Sharma countersigned §6
>
> Anyone consuming this file can rely on finding:
> - Completion conditions across code, tests, review, documentation, data quality and release
> - The four AI-specific clauses stated as conditions, not aspirations, with the reasoning for the fourth
> - A rule for what to do when a condition does not apply, so "N/A" is never a silent skip
> - A named owner for the two different questions: criteria met (Preetinka) and standard met (Gautam)
> - A dated changelog, so a change to the standard can be traced to the event that caused it
>
> This file does **not** contain: story-level acceptance criteria, the release gate itself, or the test strategy.
> Those live in: `acceptance-criteria-NWD-103.md` (P08), `release-readiness-v1.0.md` (P32), and the test suite.
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: Gautam  and Pankaj  jointly, and only at a retrospective. A DoD amended mid-sprint by the person it is inconvenient for is not a standard.
