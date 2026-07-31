# NWD-139 — Exception queue shows raw confidence, `0.8234567`, instead of `82%`

| | |
|---|---|
| **Raised by** | Ananya Iyer, QA Engineer |
| **Date raised** | 2026-06-22 |
| **Severity** | **Low** |
| **Priority** | P4 — cosmetic, does not block release |
| **Component** | Exception queue UI — `ExceptionRow.tsx` |
| **Affects story** | [NWD-108](stories/NWD-108.md) (exception queue screen) |
| **Environment** | `dev`, UI build `2026.06.22-a` |
| **Status** | Open → Fixed 2026-07-24 → Verified 2026-07-24 |

---

## 1. Summary

The confidence column renders the raw float. Priya sees `0.8234567` where the design says `82%`.

---

## 2. Expected vs actual

| | Expected | Actual |
|---|---|---|
| Confidence column | `82%` | `0.8234567` |
| Threshold column | `90%` | `0.9` |
| Column alignment | right | left |

[`ui-brief-exception-queue.md`](ui-brief-exception-queue.md) §4 specifies a whole-number percentage, right-aligned, so a column of them can be scanned vertically.

## 3. Steps to reproduce

1. Process any document that fails the gate. `broker_alpha/2026-06-19/BA-POS-20260619.pdf` in the fixture set does.
2. Open the exception queue in `dev` and look at the confidence column.

## 4. Impact

Priya reads about forty of these a day and has to compare each one against a threshold rendered in the same unhelpful form. Seven decimal places of a number that is meaningful to two.

No data is wrong. Nothing is at risk. Filed because it is in the brief and it is not in the build, and a small thing that stays broken teaches everyone that the brief is optional.

## 5. Suggested area to investigate

The value arrives from `failures_json` as a float and reaches the cell unformatted. There is already a `formatPercent` helper in the codebase used by the metrics tile.

---

## 6. Resolution

**Fixed** 2026-07-24 by Ji-woo Park. One commit, one line: `ExceptionRow.tsx:41` now calls the existing `formatPercent(value)` for both the confidence and threshold cells, and the column class becomes `text-right`.

Rounding is to the nearest whole percent. `0.8234567` → `82%`. No test added; the existing `formatPercent` unit tests cover the behaviour and this is a call site, not new logic.

**Verified** 2026-07-24 by Ananya Iyer.

---

> **Artifact contract — `artifacts/bug-NWD-139.md`**
>
> Produced by: Ananya Iyer (QA Engineer), using the bug-report standard in [P22](../../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md)
>
> Anyone fixing from this report can rely on finding:
> - Exact reproduction steps
> - Expected vs actual as values
> - The document the expectation comes from, with a section reference
> - Why a cosmetic defect was worth filing at all
>
> This report does **not** contain: evidence sections, a ruled-out table, or a root cause. It does not need them.
> A one-line defect gets a one-page report. Padding a small bug to look like a serious one wastes the reader's time and devalues the reports that are serious — compare [NWD-142](bug-NWD-142.md), which needed every section it has.
>
> **If any guarantee above is missing, this report is not ready to prompt with.** Send it back.
>
> Changing this file: QA only, until Resolution is filled in; then it is closed.
