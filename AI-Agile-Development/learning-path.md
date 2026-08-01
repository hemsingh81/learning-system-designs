# Learning Path

← [The cast](the-cast.md) · [README](README.md) · Next: [Prompt analysis](prompt-analysis.md)

The full map, plus four ways through it depending on why you're here.

---

## How this book is built

Two halves that mirror each other.

```
AI-Agile-Development/
│
├── 00-the-story.md          ← why this book exists
├── the-cast.md              ← seven roles, and why role assignment matters
├── learning-path.md         ← you are here
├── prompt-analysis.md       ← what was wrong with the original fifteen
│
├── AI-Prompts-Library/      ← HOW each prompt works
│   ├── 00-how-to-use-this-library.md
│   ├── 01-anatomy-of-a-good-prompt.md
│   ├── 02-the-handoff-contract.md      ← the core idea
│   ├── 03-the-rework-loop.md           ← the other core idea
│   └── phase-0 … phase-8/              ← P01–P36
│
└── Case-Study/Python-ETL/   ← WATCHING it happen
    ├── 00-the-brief.md … 10-retrospective.md
    ├── artifacts/           ← every document the prompts produced
    └── code/                ← the actual working Python
```

**The library teaches the prompt. The case study shows a human getting it slightly wrong first.** Read a prompt file, then read the case study chapter it links to at the bottom — that pairing is how the book is designed to work.

---

## Four routes through

### Route 1 — The full read (about 12 hours)

Straight through. Story → cast → library front matter → all thirty-six prompts in order → the case study end to end.

This is the right route if you're setting up a team to work this way, because the ordering is the argument: each phase's prompts only make sense once you've seen what the previous phase hands over.

### Route 2 — "I just need to fix this bug" (40 minutes)

You have code that QA says is wrong and you want to know what to do right now.

1. [The rework loop](AI-Prompts-Library/03-the-rework-loop.md) — the shape of the problem
2. [P27 — Fix from a QA bug report](AI-Prompts-Library/phase-6-rework/P27-fix-from-a-qa-bug-report.md) — the prompt
3. [Sprint 3 — Rework](Case-Study/Python-ETL/08-sprint-3-rework.md) — watch it happen on bug NWD-142

If nothing threw and the tests pass but the answer is wrong, that's P27. If something threw and you have a stack trace, jump to [P26](AI-Prompts-Library/phase-6-rework/P26-debug-an-error-fast.md) instead — they're different problems and the wrong one wastes an hour.

### Route 3 — By role (2–3 hours)

Read the front matter, then only your column of the [role map](the-cast.md#the-role--prompt-map).

Everyone should still read [P17 Definition of Done](AI-Prompts-Library/phase-3-planning/P17-definition-of-done.md), [P21 Daily Standup](AI-Prompts-Library/phase-4-build/P21-daily-standup-summary.md), [P30 When the AI Is Stuck](AI-Prompts-Library/phase-6-rework/P30-when-the-ai-is-stuck.md) and [P31 Clean Commits](AI-Prompts-Library/phase-7-release/P31-write-clean-git-commits.md), because those four are everybody's.

### Route 4 — The case study only (3 hours)

Skip the library. Read [the brief](Case-Study/Python-ETL/00-the-brief.md) then the ten sprint chapters as a narrative, following the prompt links only when you're curious.

This is the route if you're evaluating whether the approach is worth adopting, or if you want the Azure ETL architecture more than the prompting method.

---

## The chapter arc — Prompts Library

### Front matter — read these four first

| | What it does |
|---|---|
| [How to use this library](AI-Prompts-Library/00-how-to-use-this-library.md) | The eleven sections every prompt file has, and which ones to read when you're in a hurry |
| [Anatomy of a good prompt](AI-Prompts-Library/01-anatomy-of-a-good-prompt.md) | The seven parts. Why the "Do not" list is the highest-leverage one |
| [The handoff contract](AI-Prompts-Library/02-the-handoff-contract.md) | **The core idea.** Why AI-assisted teams break at the seams, not at the prompts |
| [The rework loop](AI-Prompts-Library/03-the-rework-loop.md) | **The other core idea.** The map of Phase 6 and how to pick an entry point |

### The thirty-six

| Phase | Prompts | You'll be able to |
|---|---|---|
| **0 Foundation** | [P01–P05](AI-Prompts-Library/README.md#phase-0--foundation) | Set up a repo where the AI knows your conventions, can read your real schema, and cannot silently edit production config |
| **1 Discovery** | [P06–P09](AI-Prompts-Library/README.md#phase-1--discovery) | Turn a vague business problem into stories small enough to estimate and specific enough to test |
| **2 Design** | [P10–P14](AI-Prompts-Library/README.md#phase-2--design) | Choose an approach with real tradeoffs, write down why, and define the data contract before anyone writes a line |
| **3 Planning** | [P15–P17](AI-Prompts-Library/README.md#phase-3--planning) | Sequence work so it's shippable after every step, and agree what "done" means before you need it |
| **4 Build** | [P18–P21](AI-Prompts-Library/README.md#phase-4--build) | Implement a story one verifiable step at a time, with tests that describe behaviour rather than restate code |
| **5 Verify** | [P22–P25](AI-Prompts-Library/README.md#phase-5--verify) | Find the defects tests structurally cannot — including silently missing data |
| **6 Rework** | [P26–P30](AI-Prompts-Library/README.md#phase-6--rework) | Work a bug report back to a fix, know when the spec is the thing that's wrong, and recognise a stuck session |
| **7 Release** | [P31–P33](AI-Prompts-Library/README.md#phase-7--release) | Ship a control process safely, with commits someone can read and a runbook someone can use at 3am |
| **8 Improve** | [P34–P36](AI-Prompts-Library/README.md#phase-8--improve) | Run a retro that produces owned action items, and rank debt by what it will actually cost you |

---

## The chapter arc — Case Study

The Northwind project across five sprints.

| Chapter | Sprint | What happens |
|---|---|---|
| [00 — The brief](Case-Study/Python-ETL/00-the-brief.md) | — | The problem, the domain vocabulary, and why this isn't an AI project |
| [01 — Foundations](Case-Study/Python-ETL/01-sprint-0-foundations.md) | 0 | Gautam spends a sprint shipping nothing, and is right to |
| [02 — Discovery](Case-Study/Python-ETL/02-sprint-1-discovery.md) | 1 | Preetinka's PRD, and the question that creates the exception queue |
| [03 — Design](Case-Study/Python-ETL/03-sprint-1-design.md) | 1 | Hem rejects the LLM, writes three ADRs, and picks a fight about ADR-0003 |
| [04 — Planning](Case-Study/Python-ETL/04-sprint-2-planning.md) | 2 | Atul finds the dependency three weeks early |
| [05 — Build: backend](Case-Study/Python-ETL/05-sprint-2-build-backend.md) | 2 | Ravi builds in three days what was estimated at two weeks |
| [06 — Build: frontend](Case-Study/Python-ETL/06-sprint-2-build-frontend.md) | 2 | Dzmitry builds for Preeti's morning, not for the component library |
| [07 — Verify](Case-Study/Python-ETL/07-sprint-3-verify.md) | 3 | Pankaj counts fourteen positions on a PDF and finds nine rows in Snowflake |
| [08 — Rework](Case-Study/Python-ETL/08-sprint-3-rework.md) | 3 | **The heart of the book.** NWD-142, end to end |
| [09 — Release](Case-Study/Python-ETL/09-sprint-4-release.md) | 4 | Parallel run, and the argument about whether to skip it |
| [10 — Retrospective](Case-Study/Python-ETL/10-retrospective.md) | 4 | The honest version of what went wrong |

---

## What you'll have built by the end

If you follow the case study with your hands rather than just your eyes:

- A **project context file** the AI actually respects, plus hooks that make lint, types and tests non-optional
- A **PRD → stories → acceptance criteria** chain where each link states what the next one can rely on
- Three **ADRs** capturing decisions whose reasons will otherwise evaporate in six months
- A **data contract** for a position record, with decimal precision, nullability, timezone and audit columns pinned down
- A working **Python ETL pipeline** on Azure Functions: classify, translate, extract, gate, transform, load — with the confidence gate as pure testable logic and a genuine config-driven **rules engine**
- An **exception queue UI** designed around forty corrections in a morning
- A **data-quality suite** that catches the class of bug unit tests structurally cannot
- A **runbook**, a **release readiness pack** built on a parallel run, and a **retro** with owned action items

---

## Two honest warnings

**This book is messier than the first three.** Those each taught one clean idea you could finish feeling like you'd understood something completely. This one is seven people disagreeing about a system that reads PDFs badly. The middle — Sprint 3 — is the messiest part and the part worth reading twice.

**Phase 6 is longer than it "should" be.** Five prompts for fixing things, versus four for building them. That ratio is deliberate and it's roughly honest about where a sprint actually goes. If it feels disproportionate, that feeling is the point.

---

← [The cast](the-cast.md) · [README](README.md) · Next: [Prompt analysis](prompt-analysis.md)
