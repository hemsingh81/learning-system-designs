# `flaky-test-triage-agent` — real, runnable agent

← [Back to case study](README.md)

Copy the script below into your own agent tool, adapting syntax per the [note on accuracy](../../README.md#a-note-on-accuracy). Deliberately **diagnosis-only** — the original draft's auto-edit tool was removed after the near-miss in ["What went wrong the first time"](README.md#what-went-wrong-the-first-time); this version proposes a fix in plain language and stops.

**All 4 tools are `READ_ONLY`.** No approval gate needed — the human decision this agent defers to is "is the proposed fix correct," not "should an action execute."

```javascript
meta = {
  name: "flaky-test-triage-agent",
  version: "1.0.0",
  goal: "Find the real root cause of the intermittent failure in the " +
    "named test, and confirm it with reproducible evidence. Propose a " +
    "fix in plain language — do not modify any file.",
  tools: [
    { name: "run_test_isolated", description: "Run the named test " +
      "alone, with no other tests in the same process.", access: "READ_ONLY" },
    { name: "run_test_n_times", description: "Run the named test N " +
      "times in a row and report the pass/fail pattern.", access: "READ_ONLY" },
    { name: "inspect_shared_fixtures", description: "List fixtures " +
      "this test shares with other tests in its file.", access: "READ_ONLY" },
    { name: "read_test_code", description: "Read the test's own source, " +
      "including any timing-sensitive assertions.", access: "READ_ONLY" }
  ],
  max_iterations: 6
}

history = []
iteration = 0

while (iteration < meta.max_iterations) {
  observation = summarize(history)
  decision = think(meta.goal, observation, meta.tools)

  if (decision.status == "CONTINUE" && is_repeat(decision, history)) {
    decision = think(meta.goal, observation, meta.tools,
      "You already tried this exact action and got: " +
      find_result(decision, history) + ". Pick something genuinely " +
      "different, or report EXHAUSTED.")
  }

  if (decision.status == "DONE") {
    if (!decision.evidence || decision.evidence.length == 0) {
      history.push({ note: "Conclusion rejected: no evidence cited." })
      iteration++
      continue
    }
    // Every tool here is READ_ONLY — no approval gate branch fires.
    // The conclusion includes a PROPOSED fix; a human decides whether
    // it's the real fix or a tolerance-widening band-aid.
    return decision.conclusion + "\n\nEvidence: " + decision.evidence +
      "\n\nProposed fix (human review required before applying): " +
      decision.proposed_fix
  }

  if (decision.status == "EXHAUSTED") {
    return "Investigated using every available tool: " +
      summarize(history) + ". No conclusive root cause found."
  }

  result = call_tool(decision.tool, decision.args)
  history.push({ tool: decision.tool, args: decision.args, result: result })
  iteration++
}

return "Stopped: reached the " + meta.max_iterations + "-iteration " +
  "budget without reaching the goal. Investigated: " + summarize(history)
```

---

← [Back to case study](README.md)
