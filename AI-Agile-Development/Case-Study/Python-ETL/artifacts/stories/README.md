# Stories — Counterparty Document Ingestion

← [Artifacts index](../README.md) · [PRD](../prd-counterparty-ingestion.md) · [Ranked backlog](../backlog-ranked.md)

The eight stories Preetinka sliced out of the PRD using [P07 — Slice the PRD into Stories](../../../../AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md).

---

## The eight

| ID | Story | Pts | Owner | Sprint |
|---|---|---|---|---|
| [NWD-101](NWD-101.md) | Land counterparty PDFs immutably in the raw zone | 2 | Ravi | 2 |
| [NWD-102](NWD-102.md) | Classify an incoming PDF to its counterparty layout | 5 | Ravi | 2 |
| [NWD-103](NWD-103.md) | **Gate every extracted field on its confidence score** | 8 | Ravi | 2 |
| [NWD-104](NWD-104.md) | Translate EM documents to English before matching | 5 | Ravi | 3 |
| [NWD-105](NWD-105.md) | Redact PII before anything is persisted | 3 | Ravi | 3 |
| [NWD-106](NWD-106.md) | Transform extracted fields into the canonical position schema | 3 | Ravi | 2 |
| [NWD-107](NWD-107.md) | Load positions into Azure SQL and Snowflake idempotently | 5 | Ravi | 2 |
| [NWD-108](NWD-108.md) | Exception queue screen for analyst review | 8 | Dzmitry | 2 |

**39 points total.** Ranking, estimation basis and dependencies are in [`backlog-ranked.md`](../backlog-ranked.md).

---

## How these were sliced, and why it matters

The obvious way to cut this work is by **layer**: one story for the blob storage, one for the Azure AI calls, one for the database, one for the UI. Four tidy stories, each owned by whoever knows that layer.

Preetinka refused, and the reason is worth understanding.

**A layer story cannot be demonstrated.** "Build the blob landing zone" is finished when… what? Nobody outside the team can look at it and say yes or no. It produces no outcome anyone at Northwind can see, so it produces no feedback, so you find out whether the whole thing works only when the last layer lands — which is the week you have no time left to be wrong.

Every story here is a **vertical slice**: it goes all the way through the stack and changes something an outsider could observe.

- **NWD-101** — a PDF arrives and is provably retained, immutably, at a known path. Preeti could watch it happen.
- **NWD-103** — a document with a low-confidence figure does not reach the warehouse. That is a *behaviour*, and Pankaj can write a test for it that fails today.
- **NWD-108** — Preeti opens a screen and fixes a value. She can tell you in five seconds whether it works.

### The one that was nearly missed

[NWD-108](NWD-108.md) did not exist in the first pass.

The design at that point rejected low-confidence documents and logged the rejection, which satisfied every line of the PRD except one. Preetinka's question — *"rejected to where? Preeti still has to do something with it"* — is what created this story.

Without it the system does 80% of the analyst's job and hands her the remaining 20% in a worse format than she had before. That is not a partial win. It is a regression with better logging.

The full account is in [chapter 02](../../02-sprint-1-discovery.md), and the reason it nearly evaporated is in [the handoff contract](../../../../AI-Prompts-Library/02-the-handoff-contract.md).

---

## What each story file contains

| Section | Why it's there |
|---|---|
| Narrative — As a / I want / So that | Keeps the *who* and the *why* attached to the work |
| Acceptance criteria summary | The checkable conditions. Full Given/When/Then for the flagship story is in [`acceptance-criteria-NWD-103.md`](../acceptance-criteria-NWD-103.md) |
| Size and risk | Points, plus what specifically is uncertain |
| Dependencies | What must exist first, and what breaks if it doesn't |
| Owner and sprint | |
| Notes | Decisions made during refinement that would otherwise be lost |

---

## What Sprint 3 added to the template

After [NWD-142](../bug-NWD-142.md), every story that produces rows in the warehouse carries one more line:

> **What does "complete" mean for this input, and how do we detect incompleteness?**

If that question has no answer, the story is not ready for a sprint.

NWD-103 is the story that gap came through. It had thorough acceptance criteria — nine scenarios, covering the happy path and the failure paths — and not one of them asked whether all the data that should have arrived actually did. Everyone was thinking about whether a number could be *trusted*. Nobody was thinking about whether it was *there*.

Hem owns that template change. See the [retrospective](../retrospective-sprint-3.md).

---

← [Artifacts index](../README.md) · [PRD](../prd-counterparty-ingestion.md) · [Ranked backlog](../backlog-ranked.md)
