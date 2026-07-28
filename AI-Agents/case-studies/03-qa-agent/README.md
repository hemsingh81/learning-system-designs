# Case Study 3 — QA: The Edge Cases Nobody Wrote Down

← [Case Study 2 — Backend](../02-backend-agent/README.md) · [All case studies](../README.md) · Next: [Code Review — A Workflow's Fixed Plan, Made Adaptive](../04-code-review-agent/README.md)

Built by **Ananya**, QA engineer at Kestrel. Pattern: **bounded autonomous exploration.**

---

## The problem

A new discount-code feature ships. Ananya's multi-angle test-generation workflow from [AI-Workflows](../../../AI-Workflows/case-studies/03-qa-workflow/README.md) generates cases from four fixed lenses — boundary, invalid input, concurrency, permissions — and verifies each one. It's thorough, and it's exactly right for a feature whose edge cases are knowable in advance. This feature's riskiest edge cases aren't any of those four categories. They come from **combinations**: what happens when a discount code, an already-discounted bundle price, and a currency-rounding rule interact in a way nobody specifically thought to write a test-generation lens for.

---

## The thought process

Ananya's exact lesson from AI-Skills and AI-Workflows carries over here, sharpened: **a false sense of coverage is worse than an honest gap.** Applied to an agent, that lesson becomes something new. It's not just about verifying findings anymore. It's about **bounding what the agent is allowed to explore and report as a finding in the first place.** An agent free to wander anywhere and report anything it finds "interesting" produces the exact same false-confidence risk as a shallow test case — a long list of "explored" areas that sounds thorough but wasn't actually checked with real evidence.

So the goal is deliberately narrow — not "explore this feature," but "find combinations of discount code, bundle pricing, and currency rounding that produce an incorrect final price, and reproduce each one." A destination, not an open invitation.

---

## The agent

The full, ready-to-run definition also lives at [`agent.md`](agent.md) in this folder.

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
```

Notice `compute_expected_total` is deliberately built as an *independent* calculation, not a second call into the same pricing code `simulate_checkout` already exercises. That's the direct agent-shaped version of AI-Workflows' verification lesson: a finding only counts when a genuinely separate check confirms it, not when the same code path agrees with itself.

---

## What went wrong the first time

Ananya's first version had a single tool, `explore_checkout_scenarios`. It let the agent freely construct and try any combination it wanted, and report anything where the total "looked wrong" based on its own judgement of what seemed reasonable. It found real issues. It also reported two "findings" that turned out to be correct behavior, because the agent's own sense of what a total "should" be was informed guessing, not a real independent calculation.

This is the exact ungrounded-conclusion failure from [Chapter 4](../../tutorial/04-tools-and-grounding.md), specific to exploration: **a finding based on "this looks wrong to me" isn't grounded, even when the agent sounds confident.** The fix was splitting the single freeform tool into the four above. Now every finding has to clear an independent, code-separate expected-value check — not the agent's own judgement — before it's reported at all.

---

## How it was tested

Per [Chapter 7](../../tutorial/07-testing-and-iterating.md): planted three real historical pricing bugs (already fixed, re-introduced on a throwaway staging branch) and confirmed the agent found and correctly reproduced all three. Separately, planted a scenario with **no actual bug** — a case that looks unusual (a 100% discount code on a single-item bundle) but is, by the documented rules, correctly priced at zero. The agent's independent `compute_expected_total` check correctly matched `simulate_checkout`'s result, and did *not* report a false finding.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Entirely read-only, staging-only by its explicit `boundary`, so no approval gate is needed — but the boundary itself is written into the agent's own definition, not left as an assumption. Checked into the QA repo. Ananya's honest note in its documentation: this agent explores *this specific* interaction — discounts × bundles × currency — not "the feature" broadly. A new feature needs a new, equally narrow goal, not a request to "explore everything."

---

## References & assets

- **[`agent.md`](agent.md)** — the complete, real definition, including the stricter dual-tool grounding check. Copy it into your own agent tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, showing the independent-calculation check explicitly.
- **Chapters used:** [Chapter 4](../../tutorial/04-tools-and-grounding.md) (independent evidence, not the same code path agreeing with itself), [Chapter 9](../../tutorial/09-governance-and-capstone.md) (the explicit `boundary` field), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where this started:** built on Ananya's [AI-Skills test-case-generation skill](../../../AI-Skills/case-studies/03-qa-skill/README.md) and [AI-Workflows generate-and-verify pipeline](../../../AI-Workflows/case-studies/03-qa-workflow/README.md) — the same false-coverage lesson, carried into a hard exploration boundary.

---

← [Case Study 2 — Backend](../02-backend-agent/README.md) · [All case studies](../README.md) · Next: [Code Review — A Workflow's Fixed Plan, Made Adaptive](../04-code-review-agent/README.md)
