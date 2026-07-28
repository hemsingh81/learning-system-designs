# AI Skills — A Complete Tutorial for Software Teams

**Learn to design, build, test, and share AI Skills — told as one story, from your first day at a fictional company to shipping a skill your whole team uses.**

Written in very simple English. Every idea is explained before it is used. Every skill in this repo is real — you can copy it and use it today.

---

## What this is

A skill is a packaged set of instructions that an AI coding assistant can pick up and use, on its own, when it recognises your request matches what the skill is for. Think of it as teaching your AI assistant a new, repeatable habit — once, properly — instead of re-explaining the same thing every single day.

This repo teaches you to build them. Not by reading a reference page, but by following one story: you, a new engineer at a made-up company called Kestrel Software, learning to build skills your team will actually use.

## Who this is for

- Software engineers who use an AI coding assistant daily and are tired of re-typing the same instructions.
- Tech leads who want their team's conventions enforced automatically, not explained in a wiki page nobody reads.
- Anyone who has never built a skill before. This tutorial assumes zero prior knowledge of skills — only that you can write code and use git.

## What you will be able to do after this

- Explain, in plain words, what a skill is and when to reach for one.
- Write a skill's most important part — its trigger description — so it activates when it should and stays quiet when it shouldn't.
- Bundle real scripts into a skill, not just prose instructions.
- Know when a skill is the wrong tool, and reach for a subagent, a hook, or a slash command instead.
- Test a skill properly before anyone else relies on it.
- Package, version, and share a skill with your team — and know what to check before sharing it wider than that.

---

## How to use this repo

1. Start with [`00-the-story.md`](00-the-story.md). It sets up the whole journey in five minutes.
2. Read [`learning-path.md`](learning-path.md) for the full chapter map, with time estimates.
3. Work through the 9 tutorial chapters in order.
4. Read the [case studies](case-studies/) — four real skills, one each for frontend, backend, QA, and code review.
5. Keep [`templates/`](templates/SKILL-template.md) open once you start building your own.

**Quick start, if you only have 20 minutes:** read [Chapter 1](tutorial/01-what-is-a-skill.md) and [Chapter 4](tutorial/04-writing-trigger-descriptions.md). Chapter 1 tells you what a skill is. Chapter 4 tells you the one thing that decides whether it actually works.

---

## Table of contents

### Start here
| File | What's in it |
|---|---|
| [`00-the-story.md`](00-the-story.md) | The protagonist, the company, the cast — read this first |
| [`learning-path.md`](learning-path.md) | Every chapter, mapped with objectives and time estimates |

### Tutorial — minimal to advanced
| # | File | What it teaches |
|---|---|---|
| 1 | [`tutorial/01-what-is-a-skill.md`](tutorial/01-what-is-a-skill.md) | What a skill is, in plain words, with real engineering use cases |
| 2 | [`tutorial/02-anatomy-of-a-skill.md`](tutorial/02-anatomy-of-a-skill.md) | The shape every skill has, so you can read any skill on sight |
| 3 | [`tutorial/03-your-first-skill.md`](tutorial/03-your-first-skill.md) | Build a real, tiny skill from nothing |
| 4 | [`tutorial/04-writing-trigger-descriptions.md`](tutorial/04-writing-trigger-descriptions.md) | The single hardest, most important part of any skill |
| 5 | [`tutorial/05-tools-and-scripts.md`](tutorial/05-tools-and-scripts.md) | Bundling real scripts, not just instructions |
| 6 | [`tutorial/06-skills-vs-other-tools.md`](tutorial/06-skills-vs-other-tools.md) | Skill vs. slash command vs. subagent vs. hook — the decision framework |
| 7 | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) | Proving a skill actually works, before anyone relies on it |
| 8 | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) | Versioning, and three levels of sharing — you, your team, your company |
| 9 | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) | Safety review, and the full checklist for "is this ready?" |

### Case studies — the same process, four teams
| # | File | The skill it builds |
|---|---|---|
| 1 | [`case-studies/01-frontend-skill/`](case-studies/01-frontend-skill/README.md) | An accessibility-review skill for the frontend team |
| 2 | [`case-studies/02-backend-skill/`](case-studies/02-backend-skill/README.md) | An API-endpoint scaffolding skill for the backend team |
| 3 | [`case-studies/03-qa-skill/`](case-studies/03-qa-skill/README.md) | A test-case generation skill for QA |
| 4 | [`case-studies/04-code-review-skill/`](case-studies/04-code-review-skill/README.md) | A team-standards code review skill |

### Templates and visuals
| File | What's in it |
|---|---|
| [`templates/SKILL-template.md`](templates/SKILL-template.md) | A blank skill skeleton — copy this to start a new skill |
| [`templates/description-writing-checklist.md`](templates/description-writing-checklist.md) | A checklist for writing a good trigger description |
| [`templates/pre-distribution-review-checklist.md`](templates/pre-distribution-review-checklist.md) | What to check before sharing a skill beyond yourself |
| [`assets/visuals.md`](assets/visuals.md) | Diagrams you can see right now, plus prompts for illustrative art |

---

## Repo structure

```
AI-Skills/
├── README.md                              ← you are here
├── 00-the-story.md                        ← the protagonist and cast
├── learning-path.md                       ← full chapter map with time estimates
│
├── tutorial/                              ← 9 chapters, minimal to advanced
│   ├── 01-what-is-a-skill.md
│   ├── 02-anatomy-of-a-skill.md
│   ├── 03-your-first-skill.md
│   ├── 04-writing-trigger-descriptions.md
│   ├── 05-tools-and-scripts.md
│   ├── 06-skills-vs-other-tools.md
│   ├── 07-testing-and-iterating.md
│   ├── 08-packaging-and-sharing.md
│   └── 09-governance-and-capstone.md
│
├── case-studies/                          ← four real skills, four teams
│   ├── 01-frontend-skill/
│   ├── 02-backend-skill/
│   ├── 03-qa-skill/
│   └── 04-code-review-skill/
│
├── templates/                             ← copy-paste starting points
│   ├── SKILL-template.md
│   ├── description-writing-checklist.md
│   └── pre-distribution-review-checklist.md
│
└── assets/
    └── visuals.md                         ← real diagrams + image-generation prompts
```

---

## A note on accuracy

The exact file paths and commands your AI coding tool uses for skills can differ slightly between tools and between versions of the same tool. This tutorial teaches you the **underlying ideas** — what a skill is, how triggering works, how to test it, how to share it — which stay true regardless of the exact syntax. Where a detail is specific to one tool's current implementation, this repo says so, and tells you to check your own tool's documentation for the exact syntax.

Do not skip that caveat. It is the difference between a tutorial you can trust and one that quietly goes stale.

---

## Where to go next

Start with [`00-the-story.md`](00-the-story.md), then [`learning-path.md`](learning-path.md).

**Finished this whole repo?** The next rung is [AI-Workflows](../AI-Workflows/README.md) — for when a task genuinely needs several coordinated pieces of work, not just one focused skill. After that, [AI-Agents](../AI-Agents/README.md) — for when even a fixed workflow plan isn't flexible enough. See [`docs/how-the-three-connect.md`](../docs/how-the-three-connect.md) for how all three fit together as one ladder.
