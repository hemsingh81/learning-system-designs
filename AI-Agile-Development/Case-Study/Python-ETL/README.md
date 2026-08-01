# The Northwind Case Study

← [Book README](../../README.md) · [The story so far](../../00-the-story.md) · Next: [00 — The brief](00-the-brief.md)

> **One line:** Seven people, five sprints, one pipeline that reads broker statements badly, and every prompt in the library shown in use by a named person at a real moment.

This is the other half of the book. [The prompts library](../../AI-Prompts-Library/README.md) tells you how a prompt works. This tells you what happened when somebody ran it.

---

## What you're about to read

Kestrel Software is building a document ingestion pipeline for Northwind Asset Management. The pipeline reads counterparty PDFs, decides which numbers on them can be trusted, and loads the trustworthy ones into a warehouse so that reconciliation can run a day earlier than it does today.

That is the whole project. It is not a large project. It is roughly ten weeks of work for two engineers.

**What makes it worth eleven chapters is that it goes wrong in the specific ways AI-assisted teams go wrong**, and every one of those ways is preserved rather than tidied up. The design that quietly dropped a requirement. The estimate that was wrong in a new direction. The code that was built in three days, worked perfectly, passed every test, and lost half the rows on a page boundary.

Every artifact the team produced is in [`artifacts/`](artifacts/). Every line of code is in [`code/doc_ingestion/`](code/doc_ingestion/). You can open them while you read.

---

## How to read it

Three ways, depending on why you're here.

**Straight through, in order.** Ten to twelve hours if you read the artifacts too, about four if you don't. This is the way to read it if you want the arc — because the arc is the point, and the bug in Sprint 3 only lands if you watched it get written in Sprint 2.

**Chapter by chapter, alongside the library.** Each chapter names the prompts it uses and links to them. Read the chapter for the story, open the prompt file when you want the mechanics. The library files are self-contained; the chapters are not, deliberately.

**Straight to Sprint 3.** If you arrived at this book because something you built with an AI turned out to be wrong and you wanted to know what to do next, start at [Chapter 7](07-sprint-3-verify.md) and [Chapter 8](08-sprint-3-rework.md). They are the heart of it. Come back for the setup afterwards.

**One thing to know before you start.** Nothing in this case study is presented as a success story. The team ships. The client is happy. And the retrospective in [Chapter 10](10-retrospective.md) is largely a list of things that should have been caught earlier, written by the people who didn't catch them.

---

## The sprints

| Sprint | Chapter | What happens | Prompts | Who leads |
|---|---|---|---|---|
| — | [00 — The brief](00-the-brief.md) | The Northwind problem. Two sets of books, a person typing PDFs, and why this is not an AI project. | — | — |
| **0** | [01 — Foundations](01-sprint-0-foundations.md) | Gautam spends a sprint shipping nothing. Repo, project context file, database, MCP server, hooks, one team skill. | [P01–P05](../../AI-Prompts-Library/README.md#phase-0--foundation) | Gautam  |
| **1** | [02 — Discovery](02-sprint-1-discovery.md) | Preetinka writes the PRD, slices it into NWD-101…108, writes acceptance criteria with Pankaj. Atul and Gautam estimate. | [P06–P09](../../AI-Prompts-Library/README.md#phase-1--discovery) | Preetinka Sharma |
| **1** | [03 — Design](03-sprint-1-design.md) | Hem picks the extraction approach, writes three ADRs, the spec, the data contract, and Dzmitry's UI brief. The handoff nearly fails. | [P10–P14](../../AI-Prompts-Library/README.md#phase-2--design) | Hem Singh |
| **2** | [04 — Planning](04-sprint-2-planning.md) | Gautam turns the spec into a build sequence. Atul plans the sprint and finds the dependency early. The Definition of Done gets three AI-specific clauses. | [P15–P17](../../AI-Prompts-Library/README.md#phase-3--planning) | Gautam + Atul |
| **2** | [05 — Build: backend](05-sprint-2-build-backend.md) | Ravi builds the confidence gate in three days against a two-week estimate. It works. | [P18](../../AI-Prompts-Library/phase-4-build/P18-implement-a-story.md) · [P20](../../AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) · [P21](../../AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md) | Ravi Mullick |
| **2** | [06 — Build: frontend](06-sprint-2-build-frontend.md) | Dzmitry builds the exception queue from the brief, against a fixture, for a person she has met. | [P19](../../AI-Prompts-Library/phase-4-build/P19-build-the-ui-from-the-brief.md) · [P20](../../AI-Prompts-Library/phase-4-build/P20-write-tests-alongside-the-code.md) | Dzmitry  |
| **3** | [07 — Verify](07-sprint-3-verify.md) | Pankaj tests it. Fourteen positions on the PDF, nine rows in the warehouse, no error anywhere. | [P22–P25](../../AI-Prompts-Library/README.md#phase-5--verify) | Pankaj  |
| **3** | [08 — Rework](08-sprint-3-rework.md) | **The heart of the book.** Bug report → diagnosis → fix → the spec was wrong → review → done. | [P26–P30](../../AI-Prompts-Library/README.md#phase-6--rework) | Ravi + Hem |
| **4** | [09 — Release](09-sprint-4-release.md) | Commits, release readiness, the runbook the on-call person reads at 3am. | [P31–P33](../../AI-Prompts-Library/README.md#phase-7--release) | Atul + Ravi |
| **4** | [10 — Retrospective](10-retrospective.md) | Dead code, tech debt, and the honest conversation about what the AI made faster and what it made worse. | [P34–P36](../../AI-Prompts-Library/README.md#phase-8--improve) | Atul + Hem |

---

## The people

Seven at Kestrel, one at Northwind. Full versions in [the cast](../../the-cast.md); this is the reminder card.

| Name | Role | The one thing to remember |
|---|---|---|
| **Atul** | Project Manager | Asks "what happens if that takes twice as long." Finds the dependency three weeks early. |
| **Preetinka Sharma** | Product Owner | Came off an operations floor. Asks "rejected to where?" — and that question creates the exception queue. |
| **Hem Singh** | Architect | Asks "what does this look like when it's wrong?" Writes the ADRs. Distrusts anything with no audit trail. |
| **Gautam ** | Team Lead | Returning from the earlier books. Owns Sprint 0, code review, and the team's AI tooling. |
| **Ravi Mullick** | Backend Engineer | Fast. Builds in three days what was estimated at two weeks. That speed is the whole point of his arc. |
| **Dzmitry ** | Frontend Engineer | Builds the exception queue. Treats the user as a person having a working day, not a set of components. |
| **Pankaj ** | QA Engineer | Returning. Finds NWD-142 by counting rows on a PDF by hand. Writes bug reports good enough to prompt with. |
| **Preeti Singh** | Operations Analyst, Northwind | Not on the team. The reason there is a team. Currently types PDFs into a spreadsheet. |

---

## The stories

| ID | Title | Owner |
|---|---|---|
| [NWD-101](artifacts/stories/NWD-101.md) | Land counterparty PDFs immutably in the raw zone | Ravi |
| [NWD-102](artifacts/stories/NWD-102.md) | Classify an incoming PDF to its counterparty layout | Ravi |
| [NWD-103](artifacts/stories/NWD-103.md) | **Gate every extracted field on its confidence score** | Ravi |
| [NWD-104](artifacts/stories/NWD-104.md) | Translate EM documents to English before matching | Ravi |
| [NWD-105](artifacts/stories/NWD-105.md) | Redact PII before anything is persisted | Ravi |
| [NWD-106](artifacts/stories/NWD-106.md) | Transform extracted fields into the canonical position schema | Ravi |
| [NWD-107](artifacts/stories/NWD-107.md) | Load positions into Azure SQL and Snowflake idempotently | Ravi |
| [NWD-108](artifacts/stories/NWD-108.md) | Exception queue screen for analyst review | Dzmitry |

NWD-103 is the flagship. It is the story the spec is written for, the story the implementation plan sequences, the story the code review argues about, and the story the bug lives in. If you follow one thread through the whole case study, follow that one.

Bugs start at [NWD-138](artifacts/bug-NWD-142.md). There are five. One of them matters.

---

## The artifacts

Everything the team produced, in the order it was produced.

| Artifact | Produced by | Prompt |
|---|---|---|
| [`CLAUDE.md`](artifacts/CLAUDE.md) | Gautam, Sprint 0 | [P01](../../AI-Prompts-Library/phase-0-foundation/P01-generate-the-project-context-file.md) |
| [`prd-counterparty-ingestion.md`](artifacts/prd-counterparty-ingestion.md) | Preetinka, Sprint 1 | [P06](../../AI-Prompts-Library/phase-1-discovery/P06-write-a-full-prd.md) |
| [`stories/NWD-101…108`](artifacts/stories/) | Preetinka, Sprint 1 | [P07](../../AI-Prompts-Library/phase-1-discovery/P07-slice-the-prd-into-stories.md) |
| [`acceptance-criteria-NWD-103.md`](artifacts/acceptance-criteria-NWD-103.md) | Preetinka + Pankaj, Sprint 1 | [P08](../../AI-Prompts-Library/phase-1-discovery/P08-write-acceptance-criteria.md) |
| [`adr/0001…0003`](artifacts/adr/) | Hem, Sprint 1 | [P12](../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| [`spec-confidence-gate.md`](artifacts/spec-confidence-gate.md) | Hem, Sprint 1 | [P11](../../AI-Prompts-Library/phase-2-design/P11-write-the-technical-spec.md) |
| [`data-contract-counterparty-position.md`](artifacts/data-contract-counterparty-position.md) | Hem + Ravi, Sprint 1 | [P13](../../AI-Prompts-Library/phase-2-design/P13-design-the-data-contract.md) |
| [`ui-brief-exception-queue.md`](artifacts/ui-brief-exception-queue.md) | Preetinka + Dzmitry, Sprint 1 | [P14](../../AI-Prompts-Library/phase-2-design/P14-ui-ux-design-brief.md) |
| [`implementation-plan-NWD-103.md`](artifacts/implementation-plan-NWD-103.md) | Gautam, Sprint 2 | [P15](../../AI-Prompts-Library/phase-3-planning/P15-implementation-plan.md) |
| [`sprint-2-plan.md`](artifacts/sprint-2-plan.md) | Atul, Sprint 2 | [P16](../../AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md) |
| [`definition-of-done.md`](artifacts/definition-of-done.md) | Gautam + Pankaj, Sprint 2 | [P17](../../AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md) |
| [`bug-NWD-142.md`](artifacts/bug-NWD-142.md) | Pankaj, Sprint 3 | [P22](../../AI-Prompts-Library/phase-5-verify/P22-e2e-test-the-application.md) |
| [`code-review-NWD-103.md`](artifacts/code-review-NWD-103.md) | Gautam, Sprint 3 | [P23](../../AI-Prompts-Library/phase-5-verify/P23-review-someone-elses-code.md) |
| [`release-readiness-v1.0.md`](artifacts/release-readiness-v1.0.md) | Atul, Sprint 4 | [P32](../../AI-Prompts-Library/phase-7-release/P32-release-readiness-check.md) |
| [`runbook-doc-ingestion.md`](artifacts/runbook-doc-ingestion.md) | Ravi, Sprint 4 | [P33](../../AI-Prompts-Library/phase-7-release/P33-write-the-runbook.md) |
| [`retrospective-sprint-3.md`](artifacts/retrospective-sprint-3.md) | Atul, Sprint 4 | [P35](../../AI-Prompts-Library/phase-8-improve/P35-run-the-retrospective.md) |

---

## A note on what's fictional and what isn't

**Northwind Asset Management is invented.** So is Kestrel Software, and so are all eight people. No real client and no real consultancy is named anywhere in this book, and no real person's work is described.

**The technology is real and the numbers are checked.** BlackRock Aladdin, Azure AI Document Intelligence, Azure AI Language, Azure AI Translator, Azure Blob Storage, Azure Functions, Azure Key Vault, Azure SQL, Snowflake, Application Insights. The per-page pricing, the confidence-score behaviour, the free-tier traps, the training-data volumes — those are the real properties of the real services, because a case study built on invented technical behaviour teaches you nothing you can use on Monday.

**The domain is real.** Reconciliation breaks, T+1 settlement pressure, prime brokers who change their statement layout without telling anybody, statements that arrive as a scan of a fax: all of that is exactly how this corner of asset management works. If it sounds like a problem nobody would still have in the 2020s, that is the point of the project.

---

## Start here

[**00 — The brief**](00-the-brief.md). It explains the problem, the domain vocabulary, and the five constraints that shape every decision the team makes afterwards. Nothing in the rest of the case study assumes you knew any of it beforehand.

---

← [Book README](../../README.md) · [The story so far](../../00-the-story.md) · Next: [00 — The brief](00-the-brief.md)
