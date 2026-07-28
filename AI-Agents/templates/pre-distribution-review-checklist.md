# Pre-Distribution Review Checklist

← [Back to README](../README.md) · See it explained: [Chapter 9 — Governance and Capstone](../tutorial/09-governance-and-capstone.md)

Run this before any agent moves beyond Level 1 (personal) sharing — see [Chapter 8](../tutorial/08-packaging-and-sharing.md) for the three levels. This extends the AI-Skills and AI-Workflows checklists with the risk that's specific to agents: an irreversible action nobody explicitly approved.

---

## Part 1 — Does this genuinely need to be an agent?

- [ ] **At each step, does the right next action genuinely depend on what gets discovered along the way** — not knowable in advance? If every step could have been planned up front, this should be a workflow, not an agent. ([Chapter 3](../tutorial/03-your-first-agent.md))

---

## Part 2 — Is the agent built correctly?

- [ ] **Is the goal written as a description of "done," not a plan?** ([Chapter 1](../tutorial/01-what-is-an-agent.md))
- [ ] **Does every tool description rule out anything it could plausibly be confused with?** ([Chapter 4](../tutorial/04-tools-and-grounding.md))
- [ ] **Does every conclusion require real cited evidence**, not an ungrounded guess? ([Chapter 4](../tutorial/04-tools-and-grounding.md))
- [ ] **Is there a real, checked iteration budget?** ([Chapter 5](../tutorial/05-stopping-conditions-and-budgets.md))
- [ ] **Does the loop detect and refuse silent exact repeats?** ([Chapter 5](../tutorial/05-stopping-conditions-and-budgets.md))
- [ ] **Is there an honest "couldn't find this" exit**, separate from silently exhausting the budget? ([Chapter 5](../tutorial/05-stopping-conditions-and-budgets.md))

---

## Part 3 — Has it actually been tested?

- [ ] **Tested for goal-reached across multiple real, genuinely different paths** — not one lucky run? ([Chapter 7](../tutorial/07-testing-and-iterating.md))
- [ ] **Tested the planted-overlap case** — two tools that could plausibly be confused, confirmed it picks correctly?
- [ ] **Tested the planted-unsolvable case** — confirmed it stops honestly, within budget, instead of circling?
- [ ] **Tested the planted-repeat case** — confirmed it doesn't silently retry an identical action?

---

## Part 4 — The risk unique to agents: irreversible action

- [ ] **Is every tool labeled `READ_ONLY` or `ACTION_TAKING`**, visibly, in the agent's own definition?
- [ ] **Does every `ACTION_TAKING` tool have an honest `reversible` flag** — actually thought through, not assumed?
- [ ] **Does every non-reversible action require human approval before it executes**, with the evidence attached — not just a bare yes/no prompt?
- [ ] **Has the approval gate itself been tested** — confirmed the agent actually stops and waits, rather than proceeding past it?
- [ ] **Is the agent's full tool access documented somewhere visible**, so a teammate can answer "what can this do without asking me" without reading the source?

---

## Part 5 — Is it packaged and controlled properly?

- [ ] **Does it have a real version number**, where adding any tool bumps it correctly, and adding an action-taking tool is always MAJOR?
- [ ] **Is there a changelog entry**, explicitly calling out any change to what the agent is allowed to do?
- [ ] **Have you honestly picked the right sharing level** — not further than the evidence supports?

---

## The honest outcome

If anything in Part 4 is unresolved and this agent has any action-taking, non-reversible tool, **it is not ready for Level 2 or Level 3 sharing.** An unapproved irreversible action is not a hypothetical risk — it's the exact mistake the [Chapter 9](../tutorial/09-governance-and-capstone.md) near-miss walks through. It happens through correct, grounded reasoning reaching a wrong conclusion, not through anyone making an obviously bad decision.

If everything passes: you have real, written-down evidence — not a feeling — that this agent is ready. Move it to the sharing level that actually fits.

---

← [Back to README](../README.md) · Full context: [Chapter 9](../tutorial/09-governance-and-capstone.md)
