# `cross-size-component-check` — real, runnable workflow

← [Back to case study](README.md)

Copy the script below into your own workflow tool, adapting `agent()`/`parallel()`/`phase()` to your tool's exact syntax per the [note on accuracy](../../README.md#a-note-on-accuracy). Everything else — the shape, the two phases, the barrier — is ready to use as-is.

**Inputs this workflow expects:** `component_code` (the component's source, as a string).
**Typical cost:** 3 parallel `agent()` calls + 1 combine call = 4 pieces of work per run.

```javascript
meta = {
  name: "cross-size-component-check",
  version: "1.0.0",
  description: "Checks a component's rendering at desktop, tablet, and " +
    "mobile widths, and combines findings into one report.",
  phases: [
    { title: "Check" },
    { title: "Combine" }
  ]
}

phase("Check")

// Genuinely independent — nothing here needs to run in order.
results = parallel([
  () => agent("Render this component at 1440px width (desktop). Check " +
    "for layout issues: overlapping elements, overflow, misalignment. " +
    "Component: " + component_code),
  () => agent("Render this component at 768px width (tablet). Check for " +
    "the same layout issues. Component: " + component_code),
  () => agent("Render this component at 375px width (mobile). Check for " +
    "the same layout issues, plus: is anything critical pushed below " +
    "the visible fold? Component: " + component_code)
])

phase("Combine")

// A real barrier — this step genuinely needs all three results together
// to say anything meaningful about the component as a whole.
report = agent(
  "Combine these 3 findings (desktop, tablet, mobile) into one report. " +
  "State clearly which sizes have issues and which don't — don't bury " +
  "a mobile-only issue under general commentary. " + results
)

return report
```

---

← [Back to case study](README.md)
