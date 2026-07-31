# Retrospective — Sprint 3, Verify and Rework

| | |
|---|---|
| **Produced by** | Farhan Qureshi, Project Manager |
| **Using** | [P35 — Run the Retrospective](../../../AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md) |
| **Date** | 2026-06-30 |
| **Status** | Complete · action items tracked to closure |
| **Version** | 1.0 |
| **Sprint** | Sprint 3, 2026-06-15 → 2026-06-30 |
| **Present** | Farhan Qureshi, Amara Osei, Sofia Marchetti, Rahul Nair, Tomas Vargas, Ji-woo Park, Ananya Iyer |

---

## 1. The numbers

| | Estimated | Actual |
|---|---|---|
| Build | 4 days | **4 days** |
| Test | 2 days | **2 days** |
| Bug fixing | **1 day** | **6 days** |
| **Total** | **7 days** | **12 days** |

Build was on the money. Test was on the money. Rework was out by a factor of six, and it is the only line that was wrong.

Five defects, [NWD-138](bug-NWD-138.md) through [NWD-142](bug-NWD-142.md), of which NWD-142 alone consumed three of the six days — one to understand, one to fix properly, one to revise the spec, the acceptance criteria and the fixture set behind it.

I want to be precise about what that one-day estimate was. It was not a guess at how long five bugs would take, because we did not know there would be five bugs. It was a placeholder I put in because a sprint plan with no rework line looks optimistic, and one day was the number that did not make the plan look bad. That is not estimating. That is decorating.

---

## 2. What went well

**The bug reports were good enough to prompt with.** Ananya's reports carry numbers rather than adjectives, a reproduction that runs, a ruled-out table, and a statement of business impact. Tomas fixed four of the five without asking her a single question. NWD-141 took ten minutes from report to root cause because the report contained the stack trace and the `grep` that finds it in three places. That is not luck; it is the format.

**The rework loop held.** Every fix went test-first: the failing test committed before the fix, in its own commit. Nobody edited a test to make it pass. That clause in the [Definition of Done](definition-of-done.md) got exercised under real time pressure in week two, and it held.

**Bronze paid for itself.** Every reprocess during the sprint was free. NWD-138's identifier corruption was recovered from stored responses without re-extracting a single page. [ADR-0002](adr/0002-persist-bronze-before-parsing.md) was argued about for an hour in Sprint 1 and it repaid that hour many times over in this one.

**Rahul's code review found the boundary defect before QA did.** `>` where the spec says the comparison must let a field sitting exactly on the threshold pass — [`code-review-NWD-103.md`](code-review-NWD-103.md) F1. That defect would have quietly cost straight-through rate in the direction nobody investigates, because it looks like the system being careful.

**Priya was in the room.** She reviewed the exception queue on day 8 and found two things Ji-woo would not have found from the brief. Having the actual user available cost her an hour and saved a release.

---

## 3. The honest finding

Everyone came into this retrospective ready to talk about NWD-142 as Tomas's bug. I want to close that off before we start, because it is wrong and it is the comfortable kind of wrong.

Tomas wrote code that took the first document from a list and mapped its fields. That code satisfied [`spec-confidence-gate.md`](spec-confidence-gate.md) Revision 1 completely. It satisfied every acceptance criterion in [`acceptance-criteria-NWD-103.md`](acceptance-criteria-NWD-103.md). It passed code review, including a careful one. It passed 60 unit tests. Sofia has read the implementation against her own spec and confirmed it does exactly what the spec says.

**A defect that passes the spec, the criteria, the review and the tests is not a defect in the engineer. It is a defect in the process, and we all built the process.**

So here is the actual finding.

### 3.1 We had no data-completeness check anywhere

Not in the code. Not in the spec. Not in the acceptance criteria. Not in the test suite. Not in the Definition of Done. Not in the data-quality suite. Not in QA's E2E plan.

Nowhere in twelve days of work, across seven people and five documents, did anyone write down: **how would we know if some of the rows were missing?**

Every single control we built answers a question about the data that is present. Is this number trustworthy? Is this field in range? Is this date before that one? Does this currency exist in our list? Every one of them is a filter over rows we have. Not one of them is a check on rows we do not.

That is not five people forgetting. It is a whole class of error that was invisible to the way we were thinking, and it stayed invisible from the PRD all the way through to production-candidate code.

### 3.2 The confidence gate made it worse, not better

This is the part I found genuinely uncomfortable and it is the part worth taking to the next project.

We had a control. We built it carefully, we swept its thresholds against a labelled ground-truth set, we gave it a spec of its own and the flagship story in the epic, and we all talked about it for three sprints as the thing that stops bad data reaching the warehouse.

**It gave us false confidence that a whole class of error was covered when it wasn't.**

Ananya put it better than I can, in [NWD-142](bug-NWD-142.md) §4.3:

> The gate answers **"can I trust this number?"**
> The failure here is **"is this number even here?"**
> Those are different questions and we only ever implemented the first one.

Nobody in this team would have said out loud "the confidence gate detects missing rows." Ask any of us directly and we would have said no, obviously not. But nobody asked, because the gate occupied the mental slot marked *data quality is handled*, and a slot that feels occupied does not get examined.

A partial control is more dangerous than no control at the same coverage, because no control leaves the worry in place. Ours removed the worry and kept the gap.

And it went further than the code. The story, the acceptance criteria and the spec were written in the same week from the same mental model, so all three had the identical hole and each one appeared to corroborate the other two. We had three documents agreeing with each other and none of them was checking anything.

### 3.3 The fixture set could never have found it

Every extraction fixture in the suite was a single-page document. Not one multi-page fixture existed anywhere.

Ananya's line, which I am quoting because it generalises: **a fixture built to prove a feature works is not a fixture that can find out where it does harm.** We had fixtures for the content of a document and none for its shape.

NWD-138 has the same shape. Every EM fixture had descriptive security names that translate harmlessly, because they were written to prove translation happened. None had a real Brazilian ticker with a share-class suffix, which is where translation does damage.

Two of five defects came from the same fixture blind spot. That is a pattern, not a coincidence.

---

## 4. What we are changing

Three action items. Each has one name against it, and one date. Not "the team", not "we should" — a person and a day.

### Action 1 — Row-count reconciliation in the data-quality suite

| | |
|---|---|
| **Owner** | **Ananya Iyer** |
| **Due** | **2026-07-10** |
| **Done when** | The data-quality suite asserts, for every processed document, that rows landed in gold equals line items extracted equals the document's declared count where one exists — and that a shortfall fails the suite, not merely logs |

The completeness rules Tomas added in `core/rules.py` stop a bad document at ingest. This is the check that runs afterwards and would have caught it even if those rules were wrong, missing, or misconfigured for a counterparty.

Two independent mechanisms, because the failure we are guarding against is precisely the one where a mechanism silently does nothing and everyone believes it is running.

Ananya's scope note: it must report per counterparty, so a source with no declared count field is visibly *not covered* rather than invisibly *passing*.

**Closed 2026-07-10.** Shipped and running daily. [`release-readiness-v1.0.md`](release-readiness-v1.0.md) §3.5.

### Action 2 — Add the completeness question to the spec template

| | |
|---|---|
| **Owner** | **Sofia Marchetti** |
| **Due** | **2026-07-07** |
| **Done when** | The spec template carries a mandatory section, the artifact contract for specs guarantees an answer to it, and every existing spec in the project has been swept and answered |

The question, in these words:

> **What does silently-missing data look like here, and how would the system detect it?**

Sofia's reasoning at the retro, recorded because the wording was argued over for twenty minutes:

> My standing question has always been "what does this look like when it's wrong?" It was not enough, and NWD-142 is why. That question assumes something *looks* like something. This one had no appearance at all — no exception, no failed test, no log line, a document marked `loaded`, a confidence of 0.9412, and a complete audit trail for data that was incomplete. It looked exactly like success.
>
> So the question has to name the specific case. Not "what if this is wrong" but "what if some of it is simply not here, and nothing tells us". If the honest answer is "this input cannot be partial", write that sentence and say why. Thirty seconds. That sentence is what would have caught this.

The corresponding clause in the [Definition of Done](definition-of-done.md) is §5.4: every story that produces rows states what "complete" means for its input and how incompleteness is detected. Rahul and Ananya added it on 2026-06-30.

**Closed 2026-07-07.** Template updated; five existing specs swept, one further gap found in the Aladdin pull and ticketed. [`spec-confidence-gate.md`](spec-confidence-gate.md) Revision 2 was drafted 2026-07-31 and formally approved 2026-07-31.

### Action 3 — Estimates carry an explicit rework line

| | |
|---|---|
| **Owner** | **Farhan Qureshi** |
| **Due** | **2026-07-03**, in time for Sprint 4 planning |
| **Done when** | Every sprint plan from Sprint 4 onward shows rework as its own line item, sized from actuals, and the sprint is not committed if build plus test plus rework exceeds capacity |

My own change, and I am putting it in writing because I am the one who put "1 day" in the plan.

What changes:

1. **Rework is a line item**, sized and visible, never absorbed into a build estimate.
2. **It is sized from actuals.** Sprint 3 ran 6 rework days against 6 build-and-test days — a ratio of 1.0. I will not carry 1.0 forward as a rule, because Sprint 3 was the first sprint QA had a full system to attack and I expect it to fall. Sprint 4 carries **0.4**, and the ratio is re-derived from actuals every sprint.
3. **Rework capacity is not a buffer to be raided.** If it is unused, the sprint finishes early. It does not become room for another story on day 9.
4. **The plan states the assumption out loud**: "this assumes N days of rework; if defects run heavier, scope moves, not the date." Amara and Northwind see that sentence before the sprint starts, not after.

The honest version of this: a plan with no rework line is not an optimistic plan, it is an incomplete one. Rework is not an accident that happens to bad teams. It is where the design gets correct, and Sprint 3 is the proof — the spec is better, the criteria are better, the fixture set is better, and none of that would exist without the six days.

I would rather commit to less and hit it.

---

## 5. Deliberately not changed

| Proposal | Decision |
|---|---|
| Add a QA gate before code review | No. Ananya found four of five defects in E2E, which is where they should be found. The one review would not have caught was NWD-142, and no review catches a defect the spec permits |
| Slow the build to write more tests up front | No. Test coverage was not the problem. 60 passing tests could not catch NWD-142 because they all tested the same idea. More of the same tests is more of the same blind spot |
| Have Sofia review every implementation against her specs | No — it does not scale and it puts the same mental model on both sides of the check. The template question in Action 2 achieves the goal without the bottleneck |
| Treat NWD-142 as an individual performance matter | **No.** See §3. The process permitted the defect. Two of us reviewed the code and neither of us caught it either |

---

## 6. Carried into Sprint 4

- Fixture coverage is now a first-class concern: multi-page, multi-table, translated, zero-line-item, and oversized variants for every source. Ananya, ongoing.
- Rahul's sweep of every spec written under the old contract. Action 2, and the Aladdin gap it found.
- The parallel run is non-negotiable and Sprint 4 planning is built around it. [`release-readiness-v1.0.md`](release-readiness-v1.0.md) §6.

---

> **Artifact contract — `Case-Study/Python-ETL/artifacts/retrospective-sprint-3.md`**
>
> Produced by: Project Manager (Farhan Qureshi) using P35 — Run the Retrospective
> Attended by: all seven team members, 2026-06-30
>
> Anyone consuming this file can rely on finding:
> - Estimated versus actual as numbers, including the line that was wrong and by how much
> - What went well, stated specifically enough to repeat
> - An honest primary finding located in the process rather than in a person, with the reasoning shown
> - Owned action items — one name and one date each, with a testable "done when", tracked to closure
> - Proposals that were considered and rejected, with the reason, so they are not re-proposed next sprint
> - The facilitator's own change, where the facilitator contributed to the problem
>
> This file does **not** contain: the defect reports, the spec change, or the sprint plan.
> Those live in: `bug-NWD-138.md`…`bug-NWD-142.md` (P22), `spec-confidence-gate.md` Revision 2 (P29), and the Sprint 4 plan (P16).
>
> **If any guarantee above is missing, this retrospective is not done.**
> A retrospective without owned, dated actions is a conversation — send it back.
>
> Changing this file: Farhan Qureshi, to record closure of an action item. Findings are never softened after the fact.
