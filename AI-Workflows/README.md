# AI Workflows — A Complete Tutorial for Software Teams

**Learn to design, build, test, and share AI Workflows — the second rung on a ladder that starts with Skills and ends with Agents.**

Written in very simple English. Every idea is explained before it is used. Every workflow in this repo is real — you can copy it and adapt it today.

---

## What this is

A skill is one set of instructions, picked up automatically when relevant, followed in one continuous flow of reasoning. A **workflow** is a step up from that: a real, deterministic plan — written as an actual script, not prose — that coordinates *multiple* pieces of work. Some run at the same time. Some run in stages. Some check each other's results before anything gets trusted.

This repo teaches you to build them, through one continuous story: you, a backend engineer at a made-up company called Kestrel Software, learning to build workflows your team will actually use — picking up right where the companion [AI-Skills](../AI-Skills/README.md) tutorial leaves off.

**New here, without having read AI-Skills first?** This tutorial still works standalone — [Chapter 1](tutorial/01-what-is-a-workflow.md) gives you everything you need. But the skill vs. workflow distinction in Chapter 6 will land harder if you've built a skill first.

## Who this is for

- Engineers who've used (or built) an AI skill and have hit its ceiling — a task that genuinely needs several things done at once, or in a checked sequence.
- Tech leads who want a bigger, more thorough automated check — a full review, a full test pass — done reliably, not just a quick single-pass answer.
- Anyone who has never built a workflow before. Zero prior knowledge assumed, beyond basic comfort reading a script.

## What you will be able to do after this

- Explain, in plain words, what a workflow is and how it's different from a skill.
- Read and write a real workflow script — phases, stages, structured output.
- Make the single most important orchestration decision correctly: parallel, or pipeline.
- Build a "check from several angles, then verify the findings" review — the pattern behind most serious automated reviews.
- Know when a workflow is the wrong tool, and a skill (or something else) is right instead.
- Test a workflow properly before anyone else relies on it.
- Package, version, and share a workflow — and govern the one risk that's unique to workflows: cost and runaway scale.

---

## How to use this repo

1. Start with [`00-the-story.md`](00-the-story.md) — five minutes, sets up the whole journey.
2. Read [`learning-path.md`](learning-path.md) for the full chapter map with time estimates.
3. Work through the 9 tutorial chapters in order.
4. Read the [case studies](case-studies/) — four real workflows, one each for frontend, backend, QA, and code review.
5. Keep [`templates/`](templates/WORKFLOW-template.md) open once you start building your own.

**Quick start, if you only have 20 minutes:** read [Chapter 1](tutorial/01-what-is-a-workflow.md) and [Chapter 4](tutorial/04-parallel-vs-pipeline.md). Chapter 1 tells you what a workflow is. Chapter 4 tells you the one decision that decides whether it's actually worth building.

---

## Table of contents

### Start here
| File | What's in it |
|---|---|
| [`00-the-story.md`](00-the-story.md) | Where this picks up from AI-Skills, and what's different this time |
| [`learning-path.md`](learning-path.md) | Every chapter, mapped with objectives and time estimates |

### Tutorial — minimal to advanced
| # | File | What it teaches |
|---|---|---|
| 1 | [`tutorial/01-what-is-a-workflow.md`](tutorial/01-what-is-a-workflow.md) | What a workflow is, and why a skill alone can't do this job |
| 2 | [`tutorial/02-anatomy-of-a-workflow.md`](tutorial/02-anatomy-of-a-workflow.md) | The shape every workflow has |
| 3 | [`tutorial/03-your-first-workflow.md`](tutorial/03-your-first-workflow.md) | Build a real, tiny workflow from nothing |
| 4 | [`tutorial/04-parallel-vs-pipeline.md`](tutorial/04-parallel-vs-pipeline.md) | The single most important orchestration decision |
| 5 | [`tutorial/05-fan-out-and-verify.md`](tutorial/05-fan-out-and-verify.md) | Checking from several angles, then verifying what you found |
| 6 | [`tutorial/06-workflows-vs-other-tools.md`](tutorial/06-workflows-vs-other-tools.md) | Workflow vs. skill vs. subagent — and where Agents fit next |
| 7 | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) | Proving a workflow actually works, before anyone relies on it |
| 8 | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) | Versioning, sharing, and why workflows need explicit consent to run |
| 9 | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) | Cost governance, and the full "is this ready?" checklist |

### Case studies — the same process, four teams
| # | File | The workflow it builds | The pattern it teaches |
|---|---|---|---|
| 1 | [`case-studies/01-frontend-workflow/`](case-studies/01-frontend-workflow/README.md) | Checks a component across screen sizes | Parallel fan-out with a barrier |
| 2 | [`case-studies/02-backend-workflow/`](case-studies/02-backend-workflow/README.md) | Scaffolds, tests, and documents endpoints | Pipeline with overlapping stages |
| 3 | [`case-studies/03-qa-workflow/`](case-studies/03-qa-workflow/README.md) | Generates and verifies test coverage | Fan-out plus adversarial verification |
| 4 | [`case-studies/04-code-review-workflow/`](case-studies/04-code-review-workflow/README.md) | The five-angle PR review from Chapter 1 | Combining a skill *inside* a workflow stage |

### Templates and visuals
| File | What's in it |
|---|---|
| [`templates/WORKFLOW-template.md`](templates/WORKFLOW-template.md) | A blank workflow skeleton — copy this to start a new one |
| [`templates/phase-planning-checklist.md`](templates/phase-planning-checklist.md) | A worksheet for planning phases before you write any script |
| [`templates/pre-distribution-review-checklist.md`](templates/pre-distribution-review-checklist.md) | What to check before sharing a workflow, including cost |
| [`assets/visuals.md`](assets/visuals.md) | Diagrams you can see right now, plus prompts for illustrative art |

---

## Repo structure

```
AI-Workflows/
├── README.md                                  ← you are here
├── 00-the-story.md                            ← where this picks up from AI-Skills
├── learning-path.md                           ← full chapter map with time estimates
│
├── tutorial/                                  ← 9 chapters, minimal to advanced
│   ├── 01-what-is-a-workflow.md
│   ├── 02-anatomy-of-a-workflow.md
│   ├── 03-your-first-workflow.md
│   ├── 04-parallel-vs-pipeline.md
│   ├── 05-fan-out-and-verify.md
│   ├── 06-workflows-vs-other-tools.md
│   ├── 07-testing-and-iterating.md
│   ├── 08-packaging-and-sharing.md
│   └── 09-governance-and-capstone.md
│
├── case-studies/                               ← four real workflows, four teams
│   ├── 01-frontend-workflow/
│   ├── 02-backend-workflow/
│   ├── 03-qa-workflow/
│   └── 04-code-review-workflow/
│
├── templates/                                  ← copy-paste starting points
│   ├── WORKFLOW-template.md
│   ├── phase-planning-checklist.md
│   └── pre-distribution-review-checklist.md
│
└── assets/
    └── visuals.md                              ← real diagrams + image-generation prompts
```

---

## A note on accuracy

The exact scripting syntax your AI coding tool uses for workflows can differ between tools. This tutorial teaches the **underlying ideas** — phases, parallel vs. pipeline, fan-out and verification, cost governance — which hold true regardless of exact syntax. Pseudocode in this repo is written to be read and understood, not copy-pasted into a specific tool without adaptation. Where a detail is specific to one tool's current implementation, this repo says so.

---

## Where to go next

Start with [`00-the-story.md`](00-the-story.md), then [`learning-path.md`](learning-path.md).

**Finished this whole repo?** The next rung is [AI-Agents](../AI-Agents/README.md) — for when even a fixed, deterministic workflow script isn't flexible enough, and the task needs something that can decide its own steps toward a goal.
