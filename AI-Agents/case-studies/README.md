# Case Studies — Same Process, Four Investigations

← [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md) · [Back to README](../README.md)

Same nine chapters. Four different people at Kestrel, four different jobs — and this time, four genuinely different **investigations**, chosen deliberately so the contrast teaches something the tutorial chapters alone can't.

---

## The four

| # | Team | Who built it | The agent | Investigation pattern | File |
|---|---|---|---|---|---|
| 1 | Frontend | Divya | Investigates an intermittent visual regression | Explore, narrow, confirm | [`01-frontend-agent/README.md`](01-frontend-agent/README.md) |
| 2 | Backend | Vikram | Triages a flaky integration test to its real cause | Hypothesize, test, revise | [`02-backend-agent/README.md`](02-backend-agent/README.md) |
| 3 | QA | Ananya | Explores a feature for edge cases nobody wrote down | Bounded autonomous exploration | [`03-qa-agent/README.md`](03-qa-agent/README.md) |
| 4 | Code review | Rahul | Decides which review angles a PR actually needs | A workflow's fixed plan, made adaptive | [`04-code-review-agent/README.md`](04-code-review-agent/README.md) |

---

## What each case study contains

1. **The problem** — what this person was doing, by hand or with a workflow's fixed plan, before the agent.
2. **The thought process** — how they decided an agent was the right tool, and what its goal, tools, and stopping condition needed to be.
3. **The real agent**, in pseudocode — copy-paste-adaptable.
4. **What went wrong the first time** — every one of these either looped, drifted, or picked a wrong tool on the first draft. Included on purpose.
5. **How it was tested**, before anyone else used it.
6. **Where it sits on the sharing ladder**, and what its irreversible-action boundary looks like.

---

## Why these four investigations, specifically

- **Frontend (Divya) — explore, narrow, confirm.** The bug is intermittent and unreproducible on demand. There is no fixed checklist that finds it — the agent has to look at something, form a guess, and let that guess decide what it checks next.
- **Backend (Vikram) — hypothesize, test, revise.** A flaky test could have several real causes. The agent's first hypothesis is often wrong, and the case study shows what "revise" actually looks like when a check comes back negative.
- **QA (Ananya) — bounded autonomous exploration.** Carrying over her exact lesson from AI-Skills and AI-Workflows: a false sense of coverage is worse than an honest gap. Here, that lesson becomes a hard boundary on what the agent is allowed to explore and report, not just a verification step.
- **Code review (Rahul) — a workflow's fixed plan, made adaptive.** This is the concrete answer to "so was the workflow wasted effort?" No — the same five angles are still there, but the agent now decides *which* of them actually apply to a given PR, instead of always running all five. Nothing from AI-Skills or AI-Workflows gets thrown away.

---

← [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md) · [Back to README](../README.md)
