# Case Studies — Same Process, Four Orchestration Shapes

← [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md) · [Back to README](../README.md)

Same nine chapters. Four different people at Kestrel, four different jobs — and this time, four genuinely different **orchestration shapes**, chosen deliberately so the contrast teaches something the tutorial chapters alone can't.

---

## The four

| # | Team | Who built it | The workflow | Orchestration pattern | File |
|---|---|---|---|---|---|
| 1 | Frontend | Divya | Checks a component across screen sizes | Parallel fan-out with a barrier | [`01-frontend-workflow/README.md`](01-frontend-workflow/README.md) |
| 2 | Backend | Vikram | Scaffolds, tests, and documents endpoints | Pipeline with overlapping stages | [`02-backend-workflow/README.md`](02-backend-workflow/README.md) |
| 3 | QA | Ananya | Generates and verifies test coverage | Fan-out plus adversarial verification | [`03-qa-workflow/README.md`](03-qa-workflow/README.md) |
| 4 | Code review | Rahul | The five-angle PR review from Chapter 1 | A skill, running as one stage inside a workflow | [`04-code-review-workflow/README.md`](04-code-review-workflow/README.md) |

---

## What each case study contains

1. **The problem** — what this person was doing, by hand or with a single skill, before the workflow.
2. **The thought process** — how they decided a workflow was the right tool, and which orchestration shape fit.
3. **The real workflow**, in pseudocode — copy-paste-adaptable.
4. **What went wrong the first time** — every one of these got the parallel-vs-pipeline decision wrong on the first draft. Included on purpose.
5. **How it was tested**, before anyone else used it.
6. **Where it sits on the sharing ladder**, and what its cost profile looks like.
7. **References & assets** — the real, standalone workflow script, a case-study-specific diagram in its own `assets/` folder, and links to the same team member's counterpart in AI-Skills and AI-Agents.

---

## Why these four orchestration shapes, specifically

- **Frontend (Divya) — parallel, with a barrier.** The three screen-size checks are genuinely independent, and you need *all of them* before you can write one combined report. The textbook case for a barrier.
- **Backend (Vikram) — pipeline.** Each endpoint goes through scaffold → test → document, in that fixed order — but multiple endpoints can be at *different stages* at the same time. The textbook case for a pipeline, not a barrier.
- **QA (Ananya) — fan-out, then verify.** Several independent testing "lenses" run at once, and — carrying over her exact lesson from AI-Skills — a false sense of coverage is worse than an honest gap. Verification isn't optional here.
- **Code review (Rahul) — a skill inside a workflow.** This is the concrete answer to "so did I waste my time building that skill?" No — the skill becomes one well-tested stage inside something bigger. Nothing from AI-Skills gets thrown away.

---

← [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md) · [Back to README](../README.md)
