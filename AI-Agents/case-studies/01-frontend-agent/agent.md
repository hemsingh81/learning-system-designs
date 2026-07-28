# `chart-overlap-investigator` — real, runnable agent

← [Back to case study](README.md)

Copy the script below into your own agent tool, adapting `agent()`/tool-calling syntax to your tool's exact primitives per the [note on accuracy](../../README.md#a-note-on-accuracy). The loop shape — observe, think, repeat-guard, grounding-guard, act — is ready to use as-is; only the 3 tool implementations (`read_component_code`, `fetch_customer_data_shape`, `render_with_data`) need wiring to your real component-rendering setup.

**All 3 tools are `READ_ONLY`** — this agent never reaches the approval-gate branch, so it's a clean Level 2 case per [Chapter 8](../../tutorial/08-packaging-and-sharing.md).

```javascript
meta = {
  name: "chart-overlap-investigator",
  version: "1.0.0",
  goal: "Find why the dashboard legend sometimes overlaps the chart " +
    "plot for some customers, and confirm the real cause.",
  tools: [
    { name: "read_component_code", description: "Read the chart " +
      "component's source, including its layout logic.",
      access: "READ_ONLY" },
    { name: "fetch_customer_data_shape", description: "Fetch the shape " +
      "(series count, label lengths, data point count) of a named " +
      "customer's chart data, without rendering it.", access: "READ_ONLY" },
    { name: "render_with_data", description: "Render the chart " +
      "component using a specific customer's real data, and report " +
      "the resulting legend and plot bounding boxes.", access: "READ_ONLY" }
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
    // No tool here is ACTION_TAKING, so this branch never fires for
    // this particular agent — included so the shape stays identical
    // to every other agent in this tutorial.
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
      "tools can see — may need a tool that can inspect rendering " +
      "timing, which this agent doesn't have."
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
