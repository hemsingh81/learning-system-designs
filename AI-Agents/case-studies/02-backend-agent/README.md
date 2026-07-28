# Case Study 2 — Backend: The Flaky Test

← [Case Study 1 — Frontend](../01-frontend-agent/README.md) · [All case studies](../README.md) · Next: [QA — The Edge Cases Nobody Wrote Down](../03-qa-agent/README.md)

Built by **Vikram**, backend engineer at Kestrel. Pattern: **hypothesize, test, revise.**

---

## The problem

A test in the orders service fails roughly one run in twenty, always the same test, never with a consistent error. Vikram's scaffold-test-document workflow from [AI-Workflows](../../../AI-Workflows/case-studies/02-backend-workflow/README.md) is a fixed pipeline — great for building new endpoints, useless here, because there's no fixed sequence of steps that root-causes an intermittent failure. The cause could be test ordering, a shared fixture, a real race condition, or timing sensitivity in the test itself. Which one it actually is can only be narrowed down by checking, one at a time, letting each result rule things in or out.

---

## The thought process

This is the case that answers [Chapter 6](../../tutorial/06-agents-vs-other-tools.md)'s question directly: could Vikram write this as a workflow with four phases, one per theory, and just run all four? He could — but it would waste real effort. If turn 1 reveals the test always fails alone, in isolation, that instantly rules out both "test ordering" and "shared fixture." There's no reason to spend real time checking either. A fixed four-phase workflow would check them anyway, every time, regardless of what the first phase found.

---

## The agent

The full, ready-to-run definition also lives at [`agent.md`](agent.md) in this folder.

```javascript
meta = {
  name: "flaky-test-triage-agent",
  version: "1.0.0",
  goal: "Find the real root cause of the intermittent failure in " +
    "test_order_total_calculation, and confirm it with reproducible " +
    "evidence.",
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
```

A real run: turn 1, `run_test_isolated` — the test still fails intermittently even completely alone. That single result rules out both "test ordering" and "shared fixture with another test" in one step — a fixed four-theory workflow would have run both of those checks anyway. Turn 2, `think()` — genuinely revising its own working theory based on turn 1 — moves to `read_test_code`, and finds an assertion comparing a timestamp with no tolerance for clock drift. Turn 3, `run_test_n_times` shows the failure rate rises under system load, consistent with a race condition against real clock time. `DONE`, root cause confirmed: timing-sensitive assertion, no tolerance, fails under load-dependent timing drift.

---

## What went wrong the first time

Vikram's first version had `think()` propose a fix directly — "add a 50ms tolerance to the timestamp comparison" — as part of its `DONE` conclusion, with a tool that could edit the test file automatically. It worked, technically. It also nearly shipped a masking fix. A wider tolerance would have made the test pass more often, without actually addressing why the timing was drifting that much under load in the first place — the kind of fix that hides a real problem instead of solving it.

This is exactly the concern [Chapter 9](../../tutorial/09-governance-and-capstone.md) walks through: an action-taking tool, even a well-intentioned one, executing on the agent's own conclusion without a human checking it first. Not just whether the root cause was correctly identified — whether that conclusion's *recommended fix* was actually the right one. Vikram removed the auto-edit tool entirely and made the agent's job strictly diagnosis: find and confirm the cause, propose a fix in plain language, and stop. A human decides whether the proposed fix is the right one or just a tolerance-widening band-aid.

---

## How it was tested

Per [Chapter 7](../../tutorial/07-testing-and-iterating.md): four planted scenarios, one per real cause (test ordering, shared fixture, timing sensitivity, genuine race condition), built by deliberately reproducing each on a throwaway branch. The agent correctly identified the true cause in all four, taking between 2 and 5 turns depending on how quickly the first check ruled out the wrong theories. The planted-repeat test caught a real early bug: the first draft re-ran `run_test_isolated` twice on one scenario without acknowledging it already had that result — fixed with [Chapter 5](../../tutorial/05-stopping-conditions-and-budgets.md)'s repeat-detection guard.

---

## Where it sits on the sharing ladder

**Level 2 — Project.** Entirely read-only after removing the auto-edit tool — diagnosis only, proposed fixes reviewed by a human before anything changes. Checked into the backend repo; Vikram's team runs it as the first step on any newly-reported flaky test, before anyone spends their own time chasing it by hand.

---

## References & assets

- **[`agent.md`](agent.md)** — the complete, real definition, diagnosis-only by design. Copy it into your own agent tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, showing how turn 1 rules out two theories at once.
- **Chapters used:** [Chapter 3](../../tutorial/03-your-first-agent.md) (why this genuinely needed an agent, not a 4-phase workflow), [Chapter 9](../../tutorial/09-governance-and-capstone.md) (why the auto-edit tool was removed), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where this started:** built on Vikram's [AI-Skills endpoint-scaffolding skill](../../../AI-Skills/case-studies/02-backend-skill/README.md) and [AI-Workflows scaffold-test-document pipeline](../../../AI-Workflows/case-studies/02-backend-workflow/README.md).

---

← [Case Study 1 — Frontend](../01-frontend-agent/README.md) · [All case studies](../README.md) · Next: [QA — The Edge Cases Nobody Wrote Down](../03-qa-agent/README.md)
