# Case Study 3 — QA: Fan-Out and Verify

← [Case Study 2 — Backend](../02-backend-workflow/README.md) · [All case studies](../README.md) · Next: [Code Review — A Skill Inside a Workflow](../04-code-review-workflow/README.md)

Built by **Ananya**, QA engineer at Kestrel. Pattern: **fan-out plus adversarial verification.**

---

## The problem

Ananya's AI-Skills [test-case skill](../../../AI-Skills/case-studies/03-qa-skill/README.md) taught her something that stuck. A test case that *looks* thorough but doesn't actually exercise a real edge case is worse than an honest gap, because it creates false confidence. Someone sees "12 test cases written" and stops worrying about that feature — even if half of those 12 are shallow restatements of the happy path wearing a different label.

That risk gets bigger, not smaller, when generating test cases from several angles at once (boundary values, invalid input, concurrency, permissions). More angles means more raw output, and more raw output means more room for a plausible-looking-but-shallow case to slip through unnoticed.

---

## The thought process

The fan-out itself is an easy call — four genuinely different lenses (boundary, invalid input, concurrency, permissions) on the same feature. Nothing about generating boundary-value cases depends on what the concurrency lens finds. Textbook parallel, per [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md).

The verification stage is where Ananya's AI-Skills lesson actually mattered. Following [Chapter 5](../../tutorial/05-fan-out-and-verify.md), each generated test case gets checked by a **fresh** `agent()` call — not the one that wrote it. It's worded specifically to ask: *does this test case actually exercise the edge case it claims to, or does it just restate the happy path with a different name?* That's the QA-specific version of "look for a reason this might be WRONG."

---

## The workflow

The full, ready-to-run script also lives at [`workflow.md`](workflow.md) in this folder.

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

## What went wrong the first time

Ananya's first draft skipped verification entirely — fan out, combine, done. Output looked great: 40+ test cases across 4 angles. On closer inspection, roughly a third of the "concurrency" cases were the happy-path test with two requests fired instead of one. None had a real assertion about ordering, locking, or a race condition — shallow cases wearing a concurrency label.

This is precisely why [Chapter 5](../../tutorial/05-fan-out-and-verify.md) treats verification as non-optional whenever a workflow's output will be trusted, not a nice-to-have. Ananya's first verification attempt also under-delivered at first. She worded it "confirm this test case is good," which produced confirmation bias exactly like the false-positive story in Chapter 5 — the shallow cases sailed through unverified. Rewording to "find a reason this DOESN'T genuinely exercise the edge case" is what actually caught them.

---

## How it was tested

Planted-case test, per [Chapter 7](../../tutorial/07-testing-and-iterating.md): Ananya hand-wrote 5 deliberately shallow "concurrency" cases (happy path, two requests, no real assertion) and 5 genuinely good ones, and ran verification against all 10 blind. All 5 shallow cases were caught and rejected; all 5 genuine cases were confirmed. Only after both sides passed did she trust the verification stage on real generated output.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Checked into the QA repo, used on every feature that reaches test-planning. Ananya's honest note in the workflow's own description: verification roughly doubles the cost of generation. That's the deliberate trade — a smaller, trustworthy set of test cases beats a larger set nobody can rely on.

---

## References & assets

- **[`workflow.md`](workflow.md)** — the complete, real script. Copy it into your own workflow tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, showing the GENUINE/SHALLOW verification branch explicitly.
- **Chapters used:** [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md), [Chapter 5](../../tutorial/05-fan-out-and-verify.md) (the wording fix that actually catches shallow findings), [Chapter 7](../../tutorial/07-testing-and-iterating.md), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where this started, and where it goes next:** built on Ananya's [AI-Skills test-case-generation skill](../../../AI-Skills/case-studies/03-qa-skill/README.md); the same false-coverage risk becomes a hard exploration boundary in [AI-Agents Case Study 3](../../../AI-Agents/case-studies/03-qa-agent/README.md) (bounded autonomous exploration).

---

← [Case Study 2 — Backend](../02-backend-workflow/README.md) · [All case studies](../README.md) · Next: [Code Review — A Skill Inside a Workflow](../04-code-review-workflow/README.md)
