# Case Study 1 — Frontend: The Intermittent Regression

← [All case studies](../README.md) · Next: [Backend — The Flaky Test](../02-backend-agent/README.md)

Built by **Divya**, frontend engineer at Kestrel. Pattern: **explore, narrow, confirm.**

---

## The problem

A customer reports that a specific dashboard chart occasionally renders with the legend overlapping the plot — but only sometimes, and only for some customers. Divya's cross-size workflow from [AI-Workflows](../../../AI-Workflows/case-studies/01-frontend-workflow/README.md) checks a component at three fixed widths, every time, the same way, on demand. It runs clean. The bug doesn't show up in any of the three checks, because it isn't a screen-size problem at all — and a fixed three-width check was never going to find something that isn't about screen size.

---

## The thought process

Run [Chapter 3](../../tutorial/03-your-first-agent.md)'s honest test: could Divya have written down, in advance, the exact sequence of things to check? No — she genuinely doesn't know yet whether this is a data-shape issue, a CSS timing issue, a stale cache, or something about specific customers' data. The right second thing to check depends entirely on what the first thing turns up.

That's the shape [Chapter 1](../../tutorial/01-what-is-an-agent.md) calls a real agent case. Divya defines the goal as a destination — "find what causes the legend overlap, and confirm it" — not a plan. She gives it read-only tools that let it look at real data without being able to change anything.

---

## The agent

The full, ready-to-run definition also lives at [`agent.md`](agent.md) in this folder.

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
```

A real run: turn 1, `read_component_code` shows the legend's width is calculated from the longest label, with a fixed maximum. Turn 2, `think()` — genuinely deciding this, not following a plan — picks `fetch_customer_data_shape` for one affected customer, and finds a label 40 characters long, well past what the fixed maximum was designed for. Turn 3, `render_with_data` on that exact customer confirms the legend's calculated width exceeds the plot's remaining space, producing the overlap. `DONE`, with all three turns cited as evidence.

---

## What went wrong the first time

Divya's first version had only two tools — `read_component_code` and `render_with_data` — and no way to look at data shape without a full render. On several affected customers, the agent would render, see the overlap, and correctly report "confirmed" — but it never explained *why*, because it had no tool that let it isolate the specific data property causing it. Every conclusion technically had evidence, per [Chapter 4](../../tutorial/04-tools-and-grounding.md)'s rule, but the evidence was "it happens," not "here's the specific cause."

The fix was adding `fetch_customer_data_shape` — a lighter-weight, more targeted tool. It let the agent isolate the *specific* property (label length) responsible, instead of only being able to confirm the symptom existed. This is the agent-specific version of a lesson you'd recognise from AI-Workflows: a tool set that's too narrow doesn't make an agent wrong, it makes its conclusions shallow.

---

## How it was tested

Per [Chapter 7](../../tutorial/07-testing-and-iterating.md): run against three real historical cases with three different true causes (long label, high series count, and one that turned out to be a genuine CSS timing bug unrelated to data at all). Confirmed the agent reached the correct cause each time, via three different real paths. The label case resolved in 3 turns. The CSS timing case took all 6 and ended in an honest `EXHAUSTED`, correctly, because none of this agent's tools could see rendering timing. That gap became a known, documented limitation rather than a silent miss.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Entirely read-only tools, so it skips [Chapter 9](../../tutorial/09-governance-and-capstone.md)'s approval-gate requirement. Checked into the frontend repo, documented with its known blind spot (CSS timing issues) so the next person who reaches for it knows exactly when to trust an `EXHAUSTED` result versus dig further by hand.

---

## References & assets

- **[`agent.md`](agent.md)** — the complete, real definition. Copy it into your own agent tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, tracing the 3-turn resolved path.
- **Chapters used:** [Chapter 2](../../tutorial/02-anatomy-of-an-agent.md), [Chapter 4](../../tutorial/04-tools-and-grounding.md) (the tool-selection fix), [Chapter 5](../../tutorial/05-stopping-conditions-and-budgets.md) (the honest `EXHAUSTED` exit), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where this started:** built on Divya's [AI-Skills accessibility skill](../../../AI-Skills/case-studies/01-frontend-skill/README.md) and [AI-Workflows cross-size check](../../../AI-Workflows/case-studies/01-frontend-workflow/README.md) — same team, same growing problem, three genuinely different tools.

---

← [All case studies](../README.md) · Next: [Backend — The Flaky Test](../02-backend-agent/README.md)
