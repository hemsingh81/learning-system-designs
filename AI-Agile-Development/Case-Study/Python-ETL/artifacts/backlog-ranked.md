# Ranked Backlog — Counterparty Document Ingestion

| | |
|---|---|
| **Produced by** | Atul(Project Manager) with Gautam  (Team Lead) |
| **Using** | [P09 — Estimate and Rank the Backlog](../../../AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md) |
| **Date** | 2026-04-28 · **Revised** 2026-08-13 after Sprint 3 |
| **Status** | Active |
| **Version** | 2.0 |

---

## 1. Estimation basis

Points are **relative size**, not hours. The reference story is **NWD-101** (land PDFs immutably in the raw zone) at **2 points** — a known shape, no unknowns, one afternoon for one person.

Scale used: 1, 2, 3, 5, 8, 13. Anything estimated 13 is not an estimate, it is a signal to slice further.

### What changed because of AI, and what didn't

This is the part we got wrong in the first pass and corrected.

| Story shape | AI effect | Why |
|---|---|---|
| Boilerplate with a known pattern (blob I/O, a REST client, a MERGE) | **Collapses.** Often 60–70% off | The pattern is well-represented and verification is cheap — it either round-trips or it doesn't |
| Config plumbing, schema mapping | **Collapses** | Same |
| Anything requiring a **domain judgement call** | **No change.** Sometimes worse | The AI will produce a confident answer to "what threshold is safe for a monetary field" and it has no basis for it |
| Anything requiring **agreement between people** | **No change** | The bottleneck is a conversation, not typing |
| Anything where **being wrong is expensive and hard to detect** | **No change**, and needs more verification time | Speed of production increases; speed of *checking* does not |

**The trap we fell into:** we discounted NWD-103 from 8 to 5 because "the gate is just comparison logic." The comparison logic took ninety minutes. Deciding *what* to compare against, and proving the thresholds were safe against a labelled ground-truth set, took the rest of the week. The code was never the work.

> **Rule adopted:** discount a story for AI only when a competent reviewer can verify the result in minutes. If verification is slow or requires judgement, the estimate stands.

---

## 2. The ranked backlog

Ranked by value ÷ effort, then adjusted for dependency order and risk.

| Rank | ID | Story | Pts | Value | Risk | Depends on |
|---|---|---|---|---|---|---|
| 1 | [NWD-101](stories/NWD-101.md) | Land counterparty PDFs immutably in the raw zone | 2 | High | Low | — |
| 2 | [NWD-102](stories/NWD-102.md) | Classify an incoming PDF to its counterparty layout | 5 | High | **High** | NWD-101 |
| 3 | [NWD-103](stories/NWD-103.md) | **Gate every extracted field on its confidence score** | **8** | **Critical** | **High** | NWD-102 |
| 4 | [NWD-106](stories/NWD-106.md) | Transform extracted fields into the canonical position schema | 3 | High | Low | NWD-103 |
| 5 | [NWD-107](stories/NWD-107.md) | Load positions into Azure SQL and Snowflake idempotently | 5 | High | Medium | NWD-106 |
| 6 | [NWD-108](stories/NWD-108.md) | Exception queue screen for analyst review | 8 | **Critical** | Medium | NWD-103 |
| 7 | [NWD-105](stories/NWD-105.md) | Redact PII before anything is persisted | 3 | High | Low | NWD-103 |
| 8 | [NWD-104](stories/NWD-104.md) | Translate EM documents to English before matching | 5 | Medium | Medium | NWD-102 |

**Total: 39 points.**

### Why the order is not purely value ÷ effort

**NWD-103 is ranked third despite being the largest and riskiest**, because it is the story everything else attaches to. The transform has nothing to transform, the sinks have nothing to load, and the exception queue has nothing to display until the gate exists and emits its failure shape. Doing the risky, central thing early is deliberate — if the approach is wrong, we want to know in week two, not week six.

**NWD-108 outranks NWD-105 and NWD-104 despite being 8 points**, because without it the system does 80% of Preeti's job and hands her the other 20% in a worse format than she had before. Preetinka's position, and she is right: a rejection with nowhere to go is not a feature, it is a regression.

**NWD-104 is last** because it only affects the EM book, and the EM book is roughly 18% of volume. It is the one story we could ship v1 without.

---

## 3. Risk notes

| ID | The risk | What we did about it |
|---|---|---|
| NWD-102 | Classifier accuracy on unseen layouts is unknown until we have labelled data | Discovery produced a labelled ground-truth set before this was estimated. Unknown layouts route to review rather than being guessed |
| NWD-103 | **The thresholds are a judgement call with real money behind them** | Threshold sweep against ground truth, per field type. Not "it felt about right" |
| NWD-107 | A re-run must be idempotent at row level as well as document level | Stage then MERGE, never INSERT |
| NWD-108 | Design depends on NWD-103's failure output shape, which does not exist yet | Atul flagged this at sprint planning. Dzmitry builds against a frozen contract, not the live code |

---

## 4. Revision 2 — what Sprint 3 changed

Added 2026-08-13, after [NWD-142](bug-NWD-142.md) and the [retrospective](retrospective-sprint-3.md).

**Every estimate now carries an explicit rework line.** Sprint 3 ran 4 days build, 2 days test and **6 days rework**, against a plan that had one day for bug fixing. Rework was not a named activity, so it had no place in the estimate and happened invisibly. The sprint was late for reasons nobody could point at.

Going forward, a story's estimate is **build + verify + rework**, with rework sized from the story's own risk rating rather than from optimism:

| Risk | Rework allowance |
|---|---|
| Low | +10% |
| Medium | +25% |
| High | **+50%** |

Under that rule NWD-103 would have been estimated at 12, not 8. It took roughly 12.

**Second change:** any story that produces rows in the warehouse now carries an explicit line — *what does "complete" mean for this input, and how do we detect incompleteness?* If that question has no answer, the story is not ready for sprint. That is the gap NWD-142 came through and it was a gap in the estimate as much as in the code.

---

> **Artifact contract — `artifacts/backlog-ranked.md`**
>
> Produced by: Atul(PM) with Gautam  (Team Lead), using [P09](../../../AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md)
> Approved by: Preetinka Sharma (Product Owner), 2026-04-29
>
> Anyone planning a sprint from this can rely on finding:
> - A stated reference story and scale, so the numbers mean something
> - A point estimate and risk rating per story
> - The dependency between every pair of stories
> - The rank order, **and the reasons rank departs from value ÷ effort**
> - The rework allowance by risk band
>
> This backlog does **not** contain: sprint assignment, capacity, or dates.
> Those are the [sprint plan](sprint-2-plan.md) — see [P16](../../../AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md).
>
> **If a story has no risk rating or no dependency line, it is not ready to plan with.**
>
> Changing this file: PM and Product Owner together. Re-estimating a story mid-sprint requires
> the Team Lead as well.
