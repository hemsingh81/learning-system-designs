# `discount-combination-explorer` — real, runnable agent

← [Back to case study](README.md)

Copy the script below into your own agent tool, adapting syntax per the [note on accuracy](../../README.md#a-note-on-accuracy). `compute_expected_total` must genuinely be a separate code path from whatever `simulate_checkout` uses internally — see ["What went wrong the first time"](README.md#what-went-wrong-the-first-time) for why that separation is the entire point.

**All 4 tools are `READ_ONLY` and staging-only** — the `boundary` field is part of `meta`, not just documentation, so it's checkable the same way `access` is.

```javascript
meta = {
  name: "discount-combination-explorer",
  version: "1.0.0",
  goal: "Find combinations of discount code + bundle price + currency " +
    "rounding that produce an incorrect final price. Every finding " +
    "must be reproduced against the staging environment before it " +
    "counts.",
  tools: [
    { name: "list_active_discount_codes", description: "List discount " +
      "codes currently configured in staging.", access: "READ_ONLY" },
    { name: "list_bundle_products", description: "List bundle products " +
      "and their component pricing in staging.", access: "READ_ONLY" },
    { name: "simulate_checkout", description: "Run a real checkout " +
      "simulation in staging with a given discount code, bundle, and " +
      "currency, and return the actual computed total.", access: "READ_ONLY" },
    { name: "compute_expected_total", description: "Independently " +
      "compute what the total SHOULD be, using the documented pricing " +
      "rules — not the same code path as simulate_checkout.", access: "READ_ONLY" }
  ],
  max_iterations: 10,
  boundary: "Staging environment only. No tool in this agent's set can " +
    "touch production data or real customer accounts."
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
    // Grounding is stricter here than the template default: a finding
    // only counts if BOTH simulate_checkout AND the independent
    // compute_expected_total were called and disagree.
    has_simulated = history.some(h => h.tool == "simulate_checkout")
    has_computed = history.some(h => h.tool == "compute_expected_total")
    if (!has_simulated || !has_computed) {
      history.push({ note: "Conclusion rejected: needs BOTH an actual " +
        "checkout simulation and an independent expected-value " +
        "computation before it counts as a finding." })
      iteration++
      continue
    }
    return decision.conclusion + "\n\nEvidence: " + decision.evidence
  }

  if (decision.status == "EXHAUSTED") {
    return "Explored using every available tool: " + summarize(history) +
      ". No incorrect-total combination found within this scope."
  }

  result = call_tool(decision.tool, decision.args)
  history.push({ tool: decision.tool, args: decision.args, result: result })
  iteration++
}

return "Stopped: reached the " + meta.max_iterations + "-iteration " +
  "budget. Explored: " + summarize(history)
```

---

← [Back to case study](README.md)
