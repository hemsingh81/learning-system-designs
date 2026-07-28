# Chapter 7 — Testing and Iterating

← [Chapter 6 — Agents vs. Other Tools](06-agents-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)

---

## Where you left off

Your config-discrepancy agent has passed every case you've personally tried it on. You're ready to show the team. Rahul asks one question that stops you: "How do you know it'll work on a case you haven't tried yet?"

With a workflow, you'd know, because the workflow runs the same phases every time. Testing it once at a representative scale told you almost everything. Your agent doesn't take the same path twice. You genuinely don't know what "testing it" even means yet.

---

## What you'll learn

1. Why testing an agent is a genuinely different problem than testing a workflow.
2. How to test that an agent reaches the *correct* goal, across different real paths.
3. How to test the specific failure modes from Chapters 4 and 5 — wrong tool picks, ungrounded conclusions, circling, silent budget exhaustion.

---

## The lesson

### Why "run it once and check the output" isn't enough

A workflow's phases are fixed, so running it once on a realistic input tells you almost everything about how it'll behave on the next one — the *shape* of what happens doesn't change. An agent's path is decided turn by turn. That means **the exact same agent, given two genuinely similar inputs, can legitimately take two different routes to the same correct answer.** Testing only one route tells you nothing about whether the others also work.

This means agent testing has to check something different from workflow testing. Not "did it do exactly these steps," but **"did it reach the right goal, and did it do so honestly — grounded, without circling, and with a real stop if it genuinely couldn't."**

### Test 1 — goal-reached, across multiple real paths

Run the same agent against the same real scenario more than once — or against several genuinely different scenarios that should all resolve to the same *kind* of correct answer — and check the conclusion each time, not the path.

For your config-discrepancy agent: run it against three real past incidents where you already know the true cause (an env var override, a feature flag, a stale cache — three different real causes). Confirm it reaches the correct cause each time, **even though the number of turns and the specific tools tried along the way will differ.** If you find yourself checking "did it call `check_env_vars` on turn 2" — stop. That's testing a workflow's plan, not an agent's goal.

### Test 2 — the planted-overlap test (from Chapter 4)

Deliberately construct a case where two tools plausibly match — the way `check_env_vars` and `check_feature_flags` did before you fixed their descriptions. Confirm the agent picks correctly. This is the same discipline as AI-Skills' trigger-description testing: you don't trust a description is clear because it reads clearly to you — you test it against the specific confusion it's supposed to prevent.

### Test 3 — the planted-ungrounded-conclusion test (from Chapter 4)

Check that a `DONE` result with no real cited evidence gets rejected, the way [Chapter 4](04-tools-and-grounding.md)'s evidence check is supposed to do. The cleanest way: temporarily disable the evidence requirement, run a case, and confirm the agent *can* produce an ungrounded-sounding conclusion when nothing stops it. That proves the check, when re-enabled, is actually catching something real — not just adding overhead with nothing to catch.

### Test 4 — the planted-unsolvable test (from Chapter 5)

Give the agent a goal it genuinely cannot reach with its current tools — the way Rahul's third-party-outage case did. Confirm two things: it stops within its iteration budget (doesn't silently run past it), and it stops with the honest `"EXHAUSTED"` exit — not a fabricated-sounding conclusion, and not eight turns of quiet repetition first.

### Test 5 — the planted-repeat test (from Chapter 5)

Feed the agent a case specifically designed so its most obvious first two tool calls come back empty, and see whether it repeats either one without acknowledging it's a repeat. This is the direct test of the loop-detection fix from Chapter 5 — build a scenario where the naive version circles, and confirm the fixed version either tries something genuinely different or reports `"EXHAUSTED"` instead.

### Putting it together: the agent test suite

```javascript
test_suite = [
  { name: "known cause A (env var)", expect_conclusion: "env var override" },
  { name: "known cause B (feature flag)", expect_conclusion: "feature flag" },
  { name: "known cause C (stale cache)", expect_conclusion: "stale cache" },
  { name: "overlapping tools", expect_correct_tool: "check_feature_flags" },
  { name: "unsolvable (vendor outage)", expect_status: "EXHAUSTED",
    expect_max_turns: 4 },
  { name: "empty-first-two-checks", expect_no_repeat_without_ack: true }
]

for (test of test_suite) {
  result = run_agent(config_discrepancy_investigator, test.scenario)
  assert_matches(result, test)
}
```

Six tests, none of them checking an exact path — every one of them checking a property that should hold *regardless* of which specific path the agent takes to get there. That's the actual shift this chapter teaches: from "did it do the right steps" to "did it reach the right place, honestly, however it got there."

### When it's genuinely ready

An agent is ready to move past personal use once every test above passes. It's not ready just because it worked on the two or three cases you personally tried while building it. The gap between "worked when I tried it" and "tested against its actual failure modes" is exactly the gap between an agent that looks done and one that's actually done. It's the same gap AI-Workflows Chapter 7 taught you to close for verification stages.

---

## Try it yourself

Build the full six-test suite above (or the equivalent for your own agent) against something you've built in this tutorial. Run it. If anything fails, don't patch the specific failing case — go back to the relevant chapter (4 for tool/grounding failures, 5 for stopping failures) and fix the underlying pattern, then re-run the whole suite.

---

## What's still missing

Your agent is tested. It isn't shared yet — and an agent has a trust requirement a workflow never had: a teammate handing it real tool access needs to know exactly what it's allowed to do without asking first, not just what it's supposed to accomplish. [Chapter 8](08-packaging-and-sharing.md) is that.

---

← [Chapter 6 — Agents vs. Other Tools](06-agents-vs-other-tools.md) · [Learning path](../learning-path.md) · Next: [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md)
