# How to Use This Library

← [Library index](README.md) · Next: [Anatomy of a good prompt](01-anatomy-of-a-good-prompt.md)

> **One line:** what's inside each prompt file, which parts to read when you're in a hurry, and how to pick the right prompt.

---

## 1. What a prompt file contains

Thirty-six files, all with the same eleven sections. Once you've read one, you know where everything is in all of them.

| § | Section | What it's for |
|---|---|---|
| — | **The header table** | Who runs it, what it needs, what it produces, who's next, how long it takes |
| 1 | **The scene** | A named person at a real moment with a real problem. This is how you learn *when* to reach for it |
| 2 | **What this prompt actually does** | The explanation. Plain language, every term defined. Usually the longest section |
| 3 | **The prompt** | The copy-paste block |
| 4 | **Every placeholder, explained** | A table — what to put in, an example, and what breaks if you get it wrong |
| 5 | **The filled-in example** | The same prompt with real values, ready to read alongside §3 |
| 6 | **What comes back** | The actual output. Not a description of it — the thing itself |
| 7 | **Why this is the final prompt** | The exit criteria and a checklist. **When to stop** |
| 8 | **When it is not done** | The follow-up prompts. **What to run instead** |
| 9 | **How this goes wrong** | Named failure modes and their fixes |
| 10 | **The handoff** | What the artifact guarantees, and who picks it up |
| 11 | **In the case study** | Where this happened at Northwind, and what went slightly wrong |

### Reading it in three minutes

You will not always want 700 lines. When you're mid-sprint and just need the thing:

**Header table → §3 (the prompt) → §4 (placeholders) → §7 (when to stop).**

That's the working set. Come back for §2 when you want to understand *why* it's shaped that way, and §8 the moment the output isn't right.

### Reading it properly

First time through a prompt, or when you're teaching it to someone: **§1 → §2 → §5 → §6 → §8 → §11.**

That order gives you the situation, the reasoning, a worked example, the real output, the recovery path, and then the story of a real person getting it slightly wrong. §11 is short and it's the bit people remember.

---

## 2. Picking the right prompt

Three ways in, depending on what you know.

### By where you are in the sprint

If you know the phase, the [index](README.md) is organised that way — nine phases, Sprint 0 through Improve. This is the default route and it's the one to use if you're following the whole method.

### By role

If you only want the prompts that are yours, use the [role → prompt map](../the-cast.md#the-role--prompt-map).

Four are everybody's regardless of role: [P17 Definition of Done](phase-3-planning/P17-definition-of-done.md), [P21 Daily Standup](phase-4-build/P21-daily-standup-summary.md), [P30 When the AI Is Stuck](phase-6-rework/P30-when-the-ai-is-stuck.md), and [P31 Clean Commits](phase-7-release/P31-write-clean-git-commits.md).

### By symptom

Most common in practice — you have a problem right now.

| What's happening | Go to |
|---|---|
| We don't really know what we're building | [P06 Write a full PRD](phase-1-discovery/P06-write-a-full-prd.md) |
| The stories are too big to estimate | [P07 Slice the PRD into stories](phase-1-discovery/P07-slice-the-prd-into-stories.md) |
| Two engineers disagree about what "done" means | [P08 Acceptance criteria](phase-1-discovery/P08-write-acceptance-criteria.md) |
| We're about to pick a technology and it feels risky | [P10 Ultra plan mode](phase-2-design/P10-ultra-plan-mode.md) |
| Nobody remembers why we chose this | [P12 Record an architecture decision](phase-2-design/P12-record-an-architecture-decision.md) |
| The data changes shape between two systems | [P13 Design the data contract](phase-2-design/P13-design-the-data-contract.md) |
| The AI wrote 900 lines and I can't review it | [P15 Implementation plan](phase-3-planning/P15-implementation-plan.md) |
| The code runs but I can't tell if it's right | [P20 Write tests alongside](phase-4-build/P20-write-tests-alongside-the-code.md) |
| Everything passes and the numbers are still wrong | [P25 Data quality validation](phase-5-verify/P25-data-quality-validation.md) |
| Something threw an exception | [P26 Debug an error fast](phase-6-rework/P26-debug-an-error-fast.md) |
| **QA says it's broken and nothing threw** | **[P27 Fix from a QA bug report](phase-6-rework/P27-fix-from-a-qa-bug-report.md)** |
| The code is right, the spec was wrong | [P29 The spec was wrong](phase-6-rework/P29-the-spec-was-wrong.md) |
| Two fix attempts failed and I'm about to try a third | [P30 When the AI is stuck](phase-6-rework/P30-when-the-ai-is-stuck.md) |
| One session touched eight files for three reasons | [P31 Write clean git commits](phase-7-release/P31-write-clean-git-commits.md) |
| We keep shipping the same class of bug | [P35 Run the retrospective](phase-8-improve/P35-run-the-retrospective.md) |

---

## 3. Four rules for actually using these

### Rule 1 — Paste the artifact, don't describe it

The single highest-value habit in the book, explained properly in [the handoff contract](02-the-handoff-contract.md).

When a prompt says *"Takes in: `docs/spec-confidence-gate.md`"*, paste the whole file. Not a summary. Your summary is 90% complete, feels 100% complete, and the AI will silently invent the missing 10%.

### Rule 2 — One prompt, one artifact

Don't combine. "Write the spec and then implement it" gets you a spec reverse-engineered to justify an implementation the AI already decided on.

Two prompts, two files, and a human decision in the middle. That middle is where the value is.

### Rule 3 — Respect the stop gates

Some prompts end with *stop and wait*. When you hit one, actually stop. The temptation is always to say "yes, looks good, carry on" without reading properly — and a stop gate you rubber-stamp is worse than no stop gate, because now you believe it was reviewed.

### Rule 4 — Read §7 before you re-prompt

The most expensive mistake in AI-assisted work isn't a bad prompt. It's a good prompt run eleven more times on something that was already finished, while the thing that's actually missing stays missing.

Every file's §7 tells you when to stop. Every file's §8 tells you what to do instead of just running it again.

---

## 4. What you need to have set up

The prompts assume a coding-agent environment — Claude Code, or something comparable that can read your repo, edit files, and run commands.

Most of them work in a plain chat window too, with two costs: you paste files by hand, and you copy output back by hand. Fine for the discovery and design phases (P06–P14, which produce documents). Painful for the build and rework phases (P18–P30), where the AI needs to actually read the code it's changing.

[Phase 0](README.md#phase-0--foundation) sets up the environment properly, and it's worth the sprint. In particular:

- **[P01](phase-0-foundation/P01-generate-the-project-context-file.md)** — the project context file. Every later prompt is better because this exists, and it's the cheapest one to skip and regret.
- **[P04](phase-0-foundation/P04-hooks-as-guardrails.md)** — hooks. The only mechanism that makes something happen *every* time rather than when the AI remembers.

---

## 5. Conventions

**`[SQUARE BRACKETS IN CAPS]`** — you replace this. Every one is explained in §4 of its file.

**`**Bold verbs**` inside a prompt** — the load-bearing instruction. If you're trimming a prompt down, keep these.

**Blockquote callouts** — a thing that will bite you:

> **Watch out.** The free tier only analyses the first two pages of a document and raises no error about the rest.

**File paths** are real and relative to the case study repo. `core/confidence.py` means [`Case-Study/Python-ETL/code/doc_ingestion/core/confidence.py`](../Case-Study/Python-ETL/code/doc_ingestion/).

**Story IDs** are `NWD-1xx`. Bug IDs start at `NWD-138`. The one that matters most is [NWD-142](../Case-Study/Python-ETL/artifacts/bug-NWD-142.md).

---

## 6. If you only read four files

1. **[The handoff contract](02-the-handoff-contract.md)** — why AI-assisted teams break at the seams rather than the prompts
2. **[The rework loop](03-the-rework-loop.md)** — the map of the part nobody writes prompts for
3. **[P27 — Fix from a QA bug report](phase-6-rework/P27-fix-from-a-qa-bug-report.md)** — the flagship
4. **[Sprint 3 — Rework](../Case-Study/Python-ETL/08-sprint-3-rework.md)** — all of the above, happening to real people

---

← [Library index](README.md) · Next: [Anatomy of a good prompt](01-anatomy-of-a-good-prompt.md)
