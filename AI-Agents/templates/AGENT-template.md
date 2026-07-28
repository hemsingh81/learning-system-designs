# Agent Template

← [Back to README](../README.md) · See it explained: [Chapter 2 — Anatomy of an Agent](../tutorial/02-anatomy-of-an-agent.md)

Copy the block below to start a new agent. Every `[LIKE THIS]` is a placeholder. Delete the comments once you've filled a section in for real.

---

```javascript
meta = {
  name: "[your-agent-name-in-lowercase-with-hyphens]",
  version: "1.0.0",
  goal: "[WHAT counts as DONE — a description of a destination, NOT a
    plan. If you can write out the exact steps in order, this should be
    a workflow instead. See Chapter 1.]",
  tools: [
    { name: "[tool_name]", description: "[WHEN to use this — be
      specific enough to rule out anything it could be confused with.
      See Chapter 4.]", access: "READ_ONLY" },
    { name: "[another_tool]", description: "[...]",
      access: "ACTION_TAKING", reversible: false,
      requires_approval: true }
    // access is READ_ONLY or ACTION_TAKING. Any ACTION_TAKING tool
    // that isn't cheaply reversible needs requires_approval: true.
    // See Chapter 9 before adding any action-taking tool.
  ],
  max_iterations: [N]   // a real, checked number — see Chapter 5
}

// ── BEFORE YOU WRITE ANY CODE ──
// Run Chapter 3's test: at each step, could you have written down the
// next action in advance, the same way every time, regardless of what
// the previous step found? If yes, this doesn't need to be an agent.
// Build a workflow instead.

history = []
iteration = 0

while (iteration < meta.max_iterations) {
  observation = summarize(history)
  decision = think(meta.goal, observation, meta.tools)

  // Loop-detection guard — see Chapter 5. Don't allow a silent repeat.
  if (decision.status == "CONTINUE" && is_repeat(decision, history)) {
    decision = think(meta.goal, observation, meta.tools,
      "You already tried this exact action and got: " +
      find_result(decision, history) + ". Pick something genuinely " +
      "different, or report EXHAUSTED.")
  }

  if (decision.status == "DONE") {
    // Grounding guard — see Chapter 4. Reject conclusions with no
    // real cited evidence.
    if (!decision.evidence || decision.evidence.length == 0) {
      history.push({ note: "Conclusion rejected: no evidence cited." })
      iteration++
      continue
    }

    // Approval-gate guard — see Chapter 9. Any non-reversible,
    // action-taking tool stops here instead of executing itself.
    if (decision.action) {
      tool_def = find_tool(meta.tools, decision.action.tool)
      if (tool_def.requires_approval) {
        return { status: "PENDING_APPROVAL", proposed_action: decision.action,
          evidence: decision.evidence }
      }
    }

    return decision.conclusion + "\n\nEvidence: " + decision.evidence
  }

  if (decision.status == "EXHAUSTED") {
    return "Investigated using every available tool: " +
      summarize(history) + ". No conclusion reached within what these " +
      "tools can see."
  }

  result = call_tool(decision.tool, decision.args)
  history.push({ tool: decision.tool, args: decision.args, result: result })
  iteration++
}

return "Stopped: reached the " + meta.max_iterations + "-iteration " +
  "budget without reaching the goal. Investigated: " + summarize(history)
```

---

## The checklist to run before you consider this "done"

Pulled from [Chapter 9](../tutorial/09-governance-and-capstone.md) — the short version.

- [ ] Does the right next step genuinely depend on what gets discovered along the way? ([Chapter 1](../tutorial/01-what-is-an-agent.md))
- [ ] Would a fixed plan (a workflow) do just as well? If so, build one instead. ([Chapter 3](../tutorial/03-your-first-agent.md))
- [ ] Do tool descriptions rule out anything they could be confused with? ([Chapter 4](../tutorial/04-tools-and-grounding.md))
- [ ] Does every conclusion require real cited evidence? ([Chapter 4](../tutorial/04-tools-and-grounding.md))
- [ ] Is there a real iteration budget, a repeat-detection guard, and an honest `EXHAUSTED` exit? ([Chapter 5](../tutorial/05-stopping-conditions-and-budgets.md))
- [ ] Tested across multiple real, genuinely different paths — not one lucky run? ([Chapter 7](../tutorial/07-testing-and-iterating.md))
- [ ] Are all tools labeled `READ_ONLY` / `ACTION_TAKING`, visibly? ([Chapter 8](../tutorial/08-packaging-and-sharing.md))
- [ ] Does every non-reversible action require human approval, with evidence attached? ([Chapter 9](../tutorial/09-governance-and-capstone.md))

---

## A filled-in example, for reference

The config-discrepancy investigator, built across Chapters 2 through 5, shown complete.

```javascript
meta = {
  name: "config-discrepancy-investigator",
  version: "1.0.0",
  goal: "Find why config value DISCOUNT_CAP behaves differently in " +
    "staging vs. production, and confirm the real cause.",
  tools: [
    { name: "read_config_files", description: "Read config files for a " +
      "named environment.", access: "READ_ONLY" },
    { name: "check_env_vars", description: "List OS-level environment " +
      "variables for a named environment. Does NOT include feature " +
      "flags — use check_feature_flags for those.", access: "READ_ONLY" },
    { name: "check_feature_flags", description: "Check feature flag " +
      "state for a named environment, including flags whose own " +
      "description mentions 'environment' or 'override.'",
      access: "READ_ONLY" }
  ],
  max_iterations: 6
}
```

Every tool here is `READ_ONLY`, so this specific agent skips the approval-gate branch entirely — a clean example of an agent that never needed [Chapter 9](../tutorial/09-governance-and-capstone.md)'s hardest requirement in the first place.

---

← [Back to README](../README.md)
