# `adaptive-pr-review-agent` — real, runnable agent

← [Back to case study](README.md)

Copy the script below into your own agent tool, adapting syntax per the [note on accuracy](../../README.md#a-note-on-accuracy). `run_five_angle_review` should call the exact same workflow as [AI-Workflows Case Study 4's `workflow.md`](../../../AI-Workflows/case-studies/04-code-review-workflow/workflow.md) — this agent does not reimplement the five-angle review, it decides which subset of it to run.

**Both tools are `READ_ONLY`** — deciding scope and calling an already-governed workflow takes no action itself, so this clears [Chapter 9](../../tutorial/09-governance-and-capstone.md) without needing an approval gate.

```javascript
meta = {
  name: "adaptive-pr-review-agent",
  version: "1.0.0",
  goal: "Review this PR using only the angles that genuinely apply to " +
    "what it actually changes — grounded in the diff's real content, " +
    "not its file names.",
  tools: [
    { name: "read_full_diff", description: "Read the complete diff, " +
      "not just file names or a summary.", access: "READ_ONLY" },
    { name: "run_five_angle_review", description: "Runs the existing, " +
      "tested five-angle review workflow (security, tests, style, " +
      "data access, docs) for a given SUBSET of angles against the " +
      "diff. This is the same workflow from AI-Workflows Case Study " +
      "4 — not reimplemented here.", access: "READ_ONLY" }
  ],
  max_iterations: 3
}

history = []
iteration = 0

while (iteration < meta.max_iterations) {
  observation = summarize(history)
  decision = think(meta.goal, observation, meta.tools)

  // Scope decisions must be grounded in the diff's real content, not
  // file names — see "What went wrong the first time." This check is
  // stricter than the template default: it rejects an angle-selection
  // decision that never actually called read_full_diff first.
  if (decision.status == "CONTINUE" &&
      decision.tool == "run_five_angle_review" &&
      !history.some(h => h.tool == "read_full_diff")) {
    decision = think(meta.goal, observation, meta.tools,
      "You must call read_full_diff before selecting angles — file " +
      "names and extensions are not a grounded basis for scope.")
  }

  if (decision.status == "CONTINUE" && is_repeat(decision, history)) {
    decision = think(meta.goal, observation, meta.tools,
      "You already tried this exact action and got: " +
      find_result(decision, history) + ". Pick something genuinely " +
      "different, or report EXHAUSTED.")
  }

  if (decision.status == "DONE") {
    if (!decision.evidence || decision.evidence.length == 0) {
      history.push({ note: "Conclusion rejected: no evidence cited — " +
        "must cite specific diff lines for the angle selection." })
      iteration++
      continue
    }
    return decision.conclusion + "\n\nEvidence: " + decision.evidence
  }

  if (decision.status == "EXHAUSTED") {
    return "Could not determine PR scope: " + summarize(history)
  }

  result = call_tool(decision.tool, decision.args)
  history.push({ tool: decision.tool, args: decision.args, result: result })
  iteration++
}

return "Stopped: reached the " + meta.max_iterations + "-iteration " +
  "budget. Investigated: " + summarize(history)
```

---

← [Back to case study](README.md)
