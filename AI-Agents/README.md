# AI Agents — A Complete Tutorial for Software Teams

**Learn to design, build, test, and share AI Agents — the third and final rung on a ladder that starts with Skills and ends here.**

Written in very simple English. Every idea is explained before it is used. Every agent in this repo is real — you can copy it and adapt it today.

---

## What this is

A skill is one set of instructions, picked up automatically, followed in one continuous flow of reasoning. A workflow is a step up from that — a fixed, deterministic plan, written as a real script, that coordinates several pieces of work in a shape you decided in advance.

An **agent** is a different kind of tool, not just a bigger one. It has a goal instead of a fixed plan. It has tools it can choose to use. And it decides its *own* next step, based on what it just discovered — something a workflow's fixed plan structurally cannot do, no matter how many phases you give it.

This repo teaches you to build agents, through the same continuous story you've been following: you, a backend engineer at a made-up company called Kestrel Software, learning to build the tool your team reaches for when even a good workflow's fixed plan isn't enough — picking up right where the companion [AI-Workflows](../AI-Workflows/README.md) tutorial leaves off.

**New here, without having read AI-Skills or AI-Workflows first?** This tutorial still works standalone — [Chapter 1](tutorial/01-what-is-an-agent.md) gives you everything you need. But the three-way comparison in Chapter 6 will land harder if you've built a skill and a workflow first.

## Who this is for

- Engineers who've built a workflow and have hit *its* ceiling — a task where the right next step genuinely can't be planned in advance, because it depends on what gets discovered along the way.
- Tech leads who want an assistant that can genuinely investigate something — a bug, an incident, an open-ended question — not just run a fixed checklist against something that already exists.
- Anyone who has never built an agent before. Zero prior knowledge assumed, beyond basic comfort reading a script.

## What you will be able to do after this

- Explain, in plain words, what an agent actually is, and why it's genuinely different from a workflow — not just a workflow with more steps.
- Read and write a real agent — its goal, its tools, its loop, its stopping condition.
- Give an agent tools it can trust itself to pick correctly, and know when it picked the wrong one.
- Stop an agent that's looping, drifting off its goal, or burning cost without making progress.
- Know when an agent is the wrong tool, and a skill or a workflow is right instead.
- Test something that doesn't take the same path twice, on purpose.
- Package, version, and share an agent — and govern the one risk that's unique to agents: an irreversible action nobody explicitly approved.

---

## How to use this repo

1. Start with [`00-the-story.md`](00-the-story.md) — five minutes, sets up the whole journey.
2. Read [`learning-path.md`](learning-path.md) for the full chapter map with time estimates.
3. Work through the 9 tutorial chapters in order.
4. Read the [case studies](case-studies/) — four real agents, one each for frontend, backend, QA, and code review.
5. Keep [`templates/`](templates/AGENT-template.md) open once you start building your own.

**Quick start, if you only have 20 minutes:** read [Chapter 1](tutorial/01-what-is-an-agent.md) and [Chapter 5](tutorial/05-stopping-conditions-and-budgets.md). Chapter 1 tells you what an agent actually is. Chapter 5 tells you the one limit that makes it safe to give one real tool access.

---

## Table of contents

### Start here
| File | What's in it |
|---|---|
| [`00-the-story.md`](00-the-story.md) | Where this picks up from AI-Workflows, and the PR a fixed plan couldn't review |
| [`learning-path.md`](learning-path.md) | Every chapter, mapped with objectives and time estimates |

### Tutorial — minimal to advanced
| # | File | What it teaches |
|---|---|---|
| 1 | [`tutorial/01-what-is-an-agent.md`](tutorial/01-what-is-an-agent.md) | What an agent is, and why a fixed workflow plan can't do this job |
| 2 | [`tutorial/02-anatomy-of-an-agent.md`](tutorial/02-anatomy-of-an-agent.md) | The shape every agent has: goal, tools, loop, stopping condition |
| 3 | [`tutorial/03-your-first-agent.md`](tutorial/03-your-first-agent.md) | Build a real, tiny agent from nothing |
| 4 | [`tutorial/04-tools-and-grounding.md`](tutorial/04-tools-and-grounding.md) | Giving an agent tools it can choose correctly between |
| 5 | [`tutorial/05-stopping-conditions-and-budgets.md`](tutorial/05-stopping-conditions-and-budgets.md) | The limit that stops an agent from looping or drifting forever |
| 6 | [`tutorial/06-agents-vs-other-tools.md`](tutorial/06-agents-vs-other-tools.md) | Agent vs. workflow vs. skill vs. subagent vs. hook |
| 7 | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) | Proving an agent reaches its goal, across more than one real path |
| 8 | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) | Versioning, sharing, and the trust boundary a teammate shouldn't have to take on faith |
| 9 | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) | Irreversible-action governance, and the full "is this ready?" checklist |

### Case studies — the same process, four teams
| # | File | The agent it builds | The pattern it teaches |
|---|---|---|---|
| 1 | [`case-studies/01-frontend-agent/`](case-studies/01-frontend-agent/README.md) | Investigates an intermittent visual regression | Explore, narrow, confirm — an open-ended investigation loop |
| 2 | [`case-studies/02-backend-agent/`](case-studies/02-backend-agent/README.md) | Triages a flaky integration test to its real cause | Hypothesize, test, revise — self-correction inside the loop |
| 3 | [`case-studies/03-qa-agent/`](case-studies/03-qa-agent/README.md) | Explores a feature for edge cases nobody wrote down | Autonomous exploration with a hard boundary |
| 4 | [`case-studies/04-code-review-agent/`](case-studies/04-code-review-agent/README.md) | Decides which review angles a PR actually needs | A workflow's fixed plan, promoted to an adaptive one |

### Templates and visuals
| File | What's in it |
|---|---|
| [`templates/AGENT-template.md`](templates/AGENT-template.md) | A blank agent skeleton — copy this to start a new one |
| [`templates/goal-and-boundary-worksheet.md`](templates/goal-and-boundary-worksheet.md) | A worksheet for defining a goal, tools, and limits before you write any script |
| [`templates/pre-distribution-review-checklist.md`](templates/pre-distribution-review-checklist.md) | What to check before sharing an agent, including its irreversible-action boundary |
| [`assets/visuals.md`](assets/visuals.md) | Diagrams you can see right now, plus prompts for illustrative art |

---

## Repo structure

```
AI-Agents/
├── README.md                                  ← you are here
├── 00-the-story.md                            ← where this picks up from AI-Workflows
├── learning-path.md                           ← full chapter map with time estimates
│
├── tutorial/                                  ← 9 chapters, minimal to advanced
│   ├── 01-what-is-an-agent.md
│   ├── 02-anatomy-of-an-agent.md
│   ├── 03-your-first-agent.md
│   ├── 04-tools-and-grounding.md
│   ├── 05-stopping-conditions-and-budgets.md
│   ├── 06-agents-vs-other-tools.md
│   ├── 07-testing-and-iterating.md
│   ├── 08-packaging-and-sharing.md
│   └── 09-governance-and-capstone.md
│
├── case-studies/                               ← four real agents, four teams
│   ├── 01-frontend-agent/
│   ├── 02-backend-agent/
│   ├── 03-qa-agent/
│   └── 04-code-review-agent/
│
├── templates/                                  ← copy-paste starting points
│   ├── AGENT-template.md
│   ├── goal-and-boundary-worksheet.md
│   └── pre-distribution-review-checklist.md
│
└── assets/
    └── visuals.md                              ← real diagrams + image-generation prompts
```

---

## A note on accuracy

The exact syntax your AI coding tool uses for agent loops, tool definitions, and stopping conditions can differ between tools. This tutorial teaches the **underlying ideas** — goal-driven loops, tool grounding, stopping conditions, irreversible-action governance — which hold true regardless of exact syntax. Pseudocode in this repo is written to be read and understood, not copy-pasted into a specific tool without adaptation. Where a detail is specific to one tool's current implementation, this repo says so.

---

## Where this series ends — and how it connects

This is the last of three tutorials: [AI-Skills](../AI-Skills/README.md) → [AI-Workflows](../AI-Workflows/README.md) → **AI-Agents**. One continuous story, one growing toolbox. A skill for one focused, recognisable request. A workflow for a fixed plan that coordinates several. An agent for a goal where the right steps can't be known until you start looking.

**Finished all three?** See [`docs/how-the-three-connect.md`](../docs/how-the-three-connect.md) for how Skills, Workflows, and Agents fit together as one ladder — including the direct line from Rahul's original `/code-review` skill, through the five-angle review workflow, to the adaptive review agent in this repo's own [Case Study 4](case-studies/04-code-review-agent/README.md).

---

## Where to go next

Start with [`00-the-story.md`](00-the-story.md), then [`learning-path.md`](learning-path.md).
