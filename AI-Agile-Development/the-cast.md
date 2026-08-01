# The Cast

← [The story so far](00-the-story.md) · [README](README.md) · Next: [Learning path](learning-path.md)

Seven people at Kestrel Software, one client, and one operations analyst who is the reason any of this exists.

You don't have to memorise them. But the whole library is organised by **who runs which prompt**, so it helps to know who's who — and more importantly, **what each of them is actually accountable for**, because that's what decides which prompt is theirs.

---

## Why the book is organised by role at all

Here's the thing that's easy to miss.

A prompt is not just a set of instructions. A prompt carries an **assumption about what the person running it already knows and already has.**

"Write a spec for this feature" assumes you know what the feature is for and have the business context to judge a tradeoff. A product owner has that. A backend engineer three days into the project does not — so when *they* run it, the AI fills the gap by inventing business context, confidently, and nobody notices for two weeks.

That's not a prompting failure. It's a **role** failure. The prompt was fine; it was pointed at the wrong person.

So every prompt in this library declares four things up front:

| Field | What it means |
|---|---|
| **Who runs it** | The role whose knowledge the prompt assumes |
| **Takes in** | The artifacts that must already exist — not "context", actual files |
| **Produces** | The one artifact it creates, at a real path |
| **Hands off to** | The next role, and the exact prompt they'll run |

Get those four right and a seven-person team can move fast without diverging. Get them wrong and you get what happened to Northwind in week six.

---

## The seven

### Atul— Project Manager

**Accountable for:** dates, risk, sequencing, and the ceremonies that keep seven people pointed the same way.

Atul isn't technical and doesn't pretend to be. What he's genuinely good at is dependencies — noticing that Dzmitry's exception queue screen has nothing to display until Ravi's confidence gate exists, three weeks before that becomes a problem.

His recurring question is **"what happens if that takes twice as long?"** He asks it about everything, which is mildly irritating and has saved the project twice.

He is the one who says the uncomfortable thing in the retro.

> **His prompts:** [P09 Estimate and rank the backlog](AI-Prompts-Library/phase-1-discovery/P09-estimate-and-rank-the-backlog.md) · [P16 Sprint plan and assignment](AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md) · [P21 Daily standup summary](AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md) · [P32 Release readiness check](AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) · [P35 Run the retrospective](AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md)

---

### Preetinka Sharma — Product Owner

**Accountable for:** the backlog, and what "done" means to the business.

Preetinka spent six years on the operations floor at a custodian bank before moving into product. That matters more than it sounds: she has personally chased a reconciliation break at 7pm on a settlement date, so when she says a wrong number is worse than a missing number, she is not speaking theoretically.

She will not accept a story without acceptance criteria. She says "that's a nice-to-have" often enough that the team says it back to her.

Her contribution to the design is the one nobody expected: she's the reason the exception queue exists at all. The first design just rejected low-confidence documents. Preetinka asked what Preeti was supposed to do with a rejection.

> **Her prompts:** [P06 Write a full PRD](AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) · [P07 Slice the PRD into stories](AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md) · [P08 Write acceptance criteria](AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) (with Pankaj) · [P14 UI/UX design brief](AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) (with Dzmitry)

---

### Hem Singh — Architect

**Accountable for:** the shape of the system, and specifically the decisions that are expensive to reverse.

Hem's whole job is telling the difference between a decision you can change next sprint and one you'll be living with in four years. She writes those down — every one of them — as an ADR, a short numbered record of the decision and why.

She distrusts anything that can't produce an audit trail. Her recurring line, asked of every design anyone brings her:

> **"What does this look like when it's wrong?"**

That question is the origin of the confidence gate, the bronze layer, and the argument in [ADR-0003](Case-Study/Python-ETL/artifacts/adr/) that one bad field should reject a whole document — which several people, including Ravi, think is too strict right up until the moment it isn't.

> **Her prompts:** [P10 Ultra plan mode](AI-Prompts-Library/phase-2-design/P10-ultra-plan-mode.md) · [P11 Write the technical spec](AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md) · [P12 Record an architecture decision](AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) · [P13 Design the data contract](AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) · [P24 Find security gaps](AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) · [P29 The spec was wrong](AI-Prompts-Library/phase-6-rework/P29-the-spec-was-wrong.md) · [P36 Tech debt triage](AI-Prompts-Library/phase-8-improve/P36-tech-debt-triage.md)

---

### Gautam  — Team Lead

**Returning from [AI-Skills](../AI-Skills/README.md), [AI-Workflows](../AI-Workflows/README.md) and [AI-Agents](../AI-Agents/README.md).**

**Accountable for:** the build sequence, code review, and how the team uses AI tooling.

If you read the first three books, Gautam is the one who kept saying *"that's not a workflow, that's an agent"* — and he's still doing the same thing here, one level up. His new version is **"that's not a prompting problem, that's a handoff problem,"** which he says roughly once a week for the first month.

He owns Sprint 0, which is the sprint where nothing ships and everyone is impatient. He is right to insist on it and everyone agrees so afterwards.

He is also, quietly, the person who reads every line the AI writes before it merges — and the Definition of Done says so out loud, which was his idea.

> **His prompts:** [P01–P05](AI-Prompts-Library/README.md#phase-0--foundation) (all of Sprint 0) · [P15 Implementation plan](AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) · [P17 Definition of done](AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) (with Pankaj) · [P23 Review someone else's code](AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md) · [P34 Clean up dead code](AI-Prompts-Library/phase-8-improve/P34-clean-up-dead-code.md)

---

### Ravi Mullick — Backend Engineer

**Accountable for:** the pipeline. Python, Azure Functions, the rules engine, the sinks.

Ravi is fast. Genuinely, unusually fast — with an AI he built in three days what the estimate said was two weeks, and it worked.

That speed is the point of his whole arc in this book, because **being fast is what let him produce a serious defect without anyone catching it.** The code was clean. The tests passed. The confidence gate said everything was fine. And a Broker Alpha statement whose positions table crossed a page boundary quietly lost half its rows on the way into Snowflake.

He's the one who has to learn the loop in [Phase 6](AI-Prompts-Library/03-the-rework-loop.md). By the retro he's the one arguing hardest for the data-quality checks that would have caught it.

> **His prompts:** [P02 Connect the database](AI-Prompts-Library/phase-0-foundation/P02-connect-the-database.md) · [P13 Design the data contract](AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) (with Hem) · [P18 Implement a story](AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) · [P20 Write tests alongside the code](AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) · [P25 Data quality validation](AI-Prompts-Library/phase-5-verify/P25-data-quality-validation.md) · [P26–P28](AI-Prompts-Library/README.md#phase-6--rework) · [P33 Write the runbook](AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md)

---

### Dzmitry  — Frontend Engineer

**Accountable for:** the exception queue — the screen where a human fixes what the machine got wrong.

Dzmitry works in React and TypeScript, and has one strong opinion that shapes the whole screen: **the user is a person having a working day, not a set of components.**

Preeti clears around forty exceptions in a morning. So every extra click in the design isn't one click — it's forty. Every time the PDF viewer loses its scroll position, that's forty times Preeti has to find her place again. That framing is why the exception queue ends up keyboard-first, with the PDF and the field list locked in sync, and why the confidence value renders as `82%` rather than `0.8234567`.

(It didn't, at first. That's bug [NWD-139](Case-Study/Python-ETL/artifacts/), and it's the smallest bug in the book on purpose — not everything is a crisis.)

> **Their prompts:** [P14 UI/UX design brief](AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) · [P19 Build the UI from the brief](AI-Prompts-Library/phase-4-build/P19-build-the-ui-from-the-brief.md) · [P20 Write tests alongside the code](AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) · [P26–P28](AI-Prompts-Library/README.md#phase-6--rework)

---

### Pankaj  — QA Engineer

**Returning from [AI-Skills](../AI-Skills/README.md), [AI-Workflows](../AI-Workflows/README.md) and [AI-Agents](../AI-Agents/README.md).**

**Accountable for:** finding out what's actually true.

Pankaj's arc in this book is the most quietly important one. She finds bug **NWD-142** — the page-boundary defect — and the way she finds it matters: not by running the test suite, which passed, but by opening a real Broker Alpha statement, counting the positions on it by hand, and comparing that number to the rows in Snowflake.

Fourteen positions on the PDF. Nine rows in the warehouse. No error anywhere.

Then she writes it up. And her bug report is good enough to paste directly into a prompt — which turns out to be a whole technique, and is why [P27](AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md) exists.

> **Her prompts:** [P08 Write acceptance criteria](AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) (with Preetinka) · [P17 Definition of done](AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) (with Gautam) · [P22 E2E test the application](AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md) · [P24 Find security gaps](AI-Prompts-Library/phase-5-verify/P24-find-security-gaps.md) · [P25 Data quality validation](AI-Prompts-Library/phase-5-verify/P25-data-quality-validation.md)

---

## And the one who isn't at Kestrel

### Preeti Singh — Operations Analyst, Northwind

Preeti is not on the delivery team. She is the reason there is a delivery team.

Right now, every morning, she opens PDFs and types numbers into a spreadsheet. Broker statements, trade confirmations, corporate action notices. Several hours a day. More at month-end. She is careful and she is fast and she still makes the occasional transcription error, because she is a human being reading a scanned fax at 8:40am.

**Whenever a design decision in this book seems abstract, check it against Preeti.** That's what Preetinka does, and it's why the exception queue exists: the first cut of the design simply rejected documents the machine wasn't sure about, and Preetinka asked the obvious question nobody had asked.

> "Rejected to where? Preeti still has to do something with it. Right now you've built her a system that does 80% of her job and gives her the other 20% in a worse format than she had before."

The exception queue is that 20%, handed back in a *better* format than she had before — with the PDF on one side, the extracted fields on the other, and the specific field the machine wasn't sure about highlighted with the reason why.

Her job changes from **transcribing every document** to **adjudicating the hard ones**. That's the higher-value part, and her corrections become the training data for the next model version. She ends up owning the accuracy of the system rather than being replaced by it.

That's not a nice sentiment tacked on the end. It's a design constraint, and it shows up in the [PRD](Case-Study/Python-ETL/artifacts/prd-counterparty-ingestion.md), the [UI brief](Case-Study/Python-ETL/artifacts/ui-brief-exception-queue.md) and the [runbook](Case-Study/Python-ETL/artifacts/runbook-doc-ingestion.md).

---

## The role → prompt map

If you only want the prompts that are yours, start here.

| Role | Sprint 0 | Discovery | Design | Planning | Build | Verify | Rework | Release | Improve |
|---|---|---|---|---|---|---|---|---|---|
| **Project Manager** | | P09 | | P16 | P21 | | | P32 | P35 |
| **Product Owner** | | P06 P07 P08 | P14 | | | | | | |
| **Architect** | | | P10 P11 P12 P13 | | | P24 | P29 | | P36 |
| **Team Lead** | P01–P05 | P09 | | P15 P17 | P21 | P23 | P29 P30 | P31 P32 | P34 P36 |
| **Backend Engineer** | P02 | | P13 | | P18 P20 P21 | P25 | P26 P27 P28 P30 | P31 P33 | |
| **Frontend Engineer** | | | P14 | | P19 P20 P21 | | P26 P27 P28 P30 | P31 | |
| **QA Engineer** | | P08 | | P17 | P21 | P22 P24 P25 | | | P35 |

Two things worth noticing about that table.

**Phase 6 is the widest row.** Four of the seven roles have prompts in the rework loop, and everyone has P30. That's not an accident of layout — it's the actual distribution of where sprint time goes.

**P21 is in almost every row.** Standup is the one ceremony where the whole team's separate AI sessions get reconciled against each other. Skip it and you're back to week six.

---

← [The story so far](00-the-story.md) · [README](README.md) · Next: [Learning path](learning-path.md)
