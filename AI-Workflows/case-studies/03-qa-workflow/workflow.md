# `multi-angle-test-case-generation` — real, runnable workflow

← [Back to case study](README.md)

Copy the script below into your own workflow tool, adapting syntax as needed per the [note on accuracy](../../README.md#a-note-on-accuracy). The fan-out-then-verify shape is ready to use as-is.

**Inputs this workflow expects:** `feature_spec` (the feature's written description, as a string).
**Typical cost:** 4 parallel generation calls + up to 4 verification calls ≈ 8 pieces of work per run — roughly double the cost of generation alone, which is the deliberate trade [the case study](README.md#where-it-sits-on-the-sharing-ladder) documents up front.

```javascript
meta = {
  name: "multi-angle-test-case-generation",
  version: "1.0.0",
  description: "Generates test cases from 4 independent angles, then " +
    "verifies each one genuinely exercises its claimed edge case " +
    "before it's added to the suite.",
  phases: [
    { title: "Generate" },
    { title: "Verify" }
  ]
}

phase("Generate")

raw_cases = parallel([
  () => agent("Generate boundary-value test cases for: " + feature_spec),
  () => agent("Generate invalid-input test cases for: " + feature_spec),
  () => agent("Generate concurrency test cases for: " + feature_spec),
  () => agent("Generate permissions test cases for: " + feature_spec)
])

phase("Verify")

// A FRESH agent call per case — not the one that wrote it — asked to
// find a reason the case might be shallow, not to confirm it's good.
verified = pipeline(
  flatten(raw_cases),
  (test_case) => agent(
    "A test case was generated, claiming to exercise: '" +
    test_case.claimed_edge_case + "'. Here is the actual test case: " +
    test_case.body + ". Try to find a reason this DOESN'T genuinely " +
    "exercise that edge case — for example, does it actually use a " +
    "boundary value, or does it just look like it does? Report " +
    "GENUINE or SHALLOW, with a one-line reason."
  )
)

genuine_only = filter(verified, (c) => c.status == "GENUINE")

return genuine_only
```

---

← [Back to case study](README.md)
