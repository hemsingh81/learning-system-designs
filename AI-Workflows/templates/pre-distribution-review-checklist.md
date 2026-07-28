# Pre-Distribution Review Checklist

← [Back to README](../README.md) · See it explained: [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md)

Run this before any workflow moves beyond Level 1 (personal) sharing — see [Chapter 8](../tutorial/08-packaging-and-sharing.md) for the three levels. This extends the AI-Skills checklist with the risk that's specific to workflows: cost and runaway scale.

---

## Part 1 — Does this genuinely need to be a workflow?

- [ ] **Does the task have genuinely separate parts, real stages, or need an independent check?** If a single focused piece of work would do just as well, this should be a skill, not a workflow. ([Chapter 3](../tutorial/03-your-first-workflow.md))

---

## Part 2 — Is the orchestration shape actually correct?

- [ ] **For every `parallel()` barrier — can you name the specific cross-item reason it's needed?** Deduplication, an early-exit decision, or a genuine comparison across all items. If not, it should be a pipeline. ([Chapter 4](../tutorial/04-parallel-vs-pipeline.md))
- [ ] **Has the pipeline actually been tested with an uneven mix of fast and slow items**, to confirm it behaves like a real pipeline and not a barrier in disguise? ([Chapter 7](../tutorial/07-testing-and-iterating.md))

---

## Part 3 — Can findings be trusted?

- [ ] **If this workflow produces findings that will be trusted or acted on, is there a genuinely independent verification stage?** A fresh `agent()` call, not the same one that produced the finding. ([Chapter 5](../tutorial/05-fan-out-and-verify.md))
- [ ] **Is verification worded to look for reasons a claim might be WRONG**, not to confirm it's right?
- [ ] **Has the verification stage been tested on BOTH sides** — planted false findings that should be rejected, and genuinely real findings that should be confirmed?

---

## Part 4 — The risk unique to workflows: cost and scale

- [ ] **Does any stage contain orchestration inside orchestration** — a fan-out inside a pipeline, or the reverse?
- [ ] **If yes, has the real multiplication been calculated and written down** — the actual "N items × M pieces of work per item" arithmetic, not a guess?
- [ ] **Is there an explicit, checkable cap** on how large this can grow?
- [ ] **Does exceeding that cap fail loudly, with an explanation of what was avoided and why** — rather than silently running at whatever size the input happens to be?
- [ ] **Is the workflow's typical real-world cost stated somewhere visible** — in its description or documentation — before anyone runs it for the first time?

---

## Part 5 — Is it packaged and controlled properly?

- [ ] **Does it have a real version number**, where MAJOR genuinely means the orchestration shape changed, not just the wording?
- [ ] **Is there a changelog entry**, explicitly calling out any change to cost or scale?
- [ ] **Does running this workflow require a deliberate, on-purpose decision** — never automatic triggering the way a skill works? ([Chapter 8](../tutorial/08-packaging-and-sharing.md))
- [ ] **Have you honestly picked the right sharing level** — not further than the evidence supports?

---

## The honest outcome

If anything in Part 4 is unresolved and this workflow contains nested orchestration, **it is not ready for Level 2 or Level 3 sharing.** An unbounded multiplication is not a hypothetical risk — it's the exact mistake the [Chapter 9](../tutorial/09-governance-and-capstone.md) near-miss walks through. It happens by nesting two individually-reasonable patterns together, not by anyone making an obviously bad decision.

If everything passes: you have real, written-down evidence — not a feeling — that this workflow is ready. Move it to the sharing level that actually fits.

---

← [Back to README](../README.md) · Full context: [Chapter 9](../tutorial/09-governance-and-capstone.md)
