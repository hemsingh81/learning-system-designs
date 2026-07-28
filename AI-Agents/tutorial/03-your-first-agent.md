# Chapter 3 — Your First Agent

← [Chapter 2 — Anatomy of an Agent](02-anatomy-of-an-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Tools and Grounding](04-tools-and-grounding.md)

---

## Where you left off

You can read an agent now. Rahul says the same thing he's said at the start of your first build, twice before: "Stop reading examples. Build one."

You pick something small on purpose, exactly like you did with your first workflow — not trying to prove anything yet, just trying to see the whole loop run once, for real.

---

## What you'll learn

1. How to build a working agent with a real goal and a real loop.
2. How to notice when a task didn't actually need an agent at all.
3. The first real mistake almost everyone makes — and it's the mirror image of the one you made with your first workflow.

---

## The lesson

### Pick something small, on purpose

You choose this: **investigate why last night's CI build failed, and report the root cause.**

### Step 1 — The first draft

You build it as an agent, feeling good about finally using the loop from Chapter 2:

```javascript
meta = {
  name: "ci-failure-investigator",
  goal: "Find the root cause of last night's CI build failure.",
  tools: [
    { name: "read_ci_log", description: "Read the CI run's full log output" },
    { name: "read_code", description: "Read a named source file" }
  ],
  max_iterations: 5
}
```

You run it. Turn 1: `think()` picks `read_ci_log`. The log comes back and it's completely unambiguous — line 340 says, in plain text, `FAILED: test_discount_calculation — AssertionError: expected 12.50, got 12.00`. Turn 2: `think()` picks `read_code` on the one file that test covers, spots the off-by-one in a rounding function, and returns `DONE` with the root cause.

Two turns. It works. You feel good about it, for about five minutes.

### Step 2 — The honest question

Then you look back at what actually happened. `think()` never had a real decision to make. Turn 1 always reads the CI log — there was never another sensible first move. Turn 2 always reads whatever file the log already named — there was never another sensible second move either. **The entire "loop" ran exactly the two steps you could have written down before you ran it once.**

Compare that to just... writing those two steps as a plan:

```javascript
meta = {
  name: "ci-failure-report",
  phases: [{ title: "Diagnose" }]
}

phase("Diagnose")

log = agent("Read the CI log and report the first FAILED line, with its " +
  "exact assertion and the file/line it points to.")

root_cause = agent("Read the file and line named in this failure, and " +
  "explain the root cause: " + log)

return root_cause
```

Same two steps. No `think()` call deciding anything, because there was never anything to decide — the CI log always names the exact failing test and its exact assertion, every single time, for every build. **This is the actual, uncomfortable lesson of this chapter, and it's the mirror image of AI-Workflows Chapter 3's lesson: you just built an agent for a task that had a fixed plan the whole time.**

### Why this happens to almost everyone

Once you know agents exist, and you've just learned the loop, there's a real temptation to reach for it. It's the same trap as reaching for `parallel()` right after learning it. A CI failure investigation *sounds* like exploration. It has the word "investigate" in it. But a CI log that always names its own failing test isn't actually open-ended — every run's second step is knowable the moment you've read the log, because the log always tells you exactly where to look next, in the same fixed way, every time.

**An agent has real overhead.** A `think()` call that has to weigh several genuinely different next moves costs more than a plan that was already fully known. That overhead is worth it when the next step genuinely isn't knowable until you've seen the last result. It's pure cost, with nothing bought, when the "investigation" was always going to point at the same next step anyway.

### Step 3 — Find a task that actually earns it

You go back and pick something with a property the CI-log task didn't have. **A genuinely ambiguous first result, where different findings lead down different, unpredictable paths.**

You land on this: **a config value behaves differently in staging than in production, and nobody knows why.** Unlike the CI log, there's no single line anywhere that names the cause. The value could be overridden by an environment variable, a per-region config file, a feature flag, or a stale cache — and which of those it actually is can only be discovered by checking, one at a time, and letting what you find rule things in or out.

```javascript
meta = {
  name: "config-discrepancy-investigator",
  goal: "Find why config value DISCOUNT_CAP behaves differently in " +
    "staging vs. production, and confirm the real cause.",
  tools: [
    { name: "read_config_files", description: "Read config files for a " +
      "named environment" },
    { name: "check_env_vars", description: "List environment variables " +
      "set for a named environment" },
    { name: "check_feature_flags", description: "Check feature flag " +
      "state for a named environment" }
  ],
  max_iterations: 6
}
```

Run this on a real case, and the path genuinely isn't fixed. If `check_env_vars` on turn 1 finds an override, the agent is done in 2 turns. If it finds nothing, `think()` has a real decision — try config files next, or feature flags — and whichever one it tries, the *result* of that turn is what decides turn 3, not a plan anyone wrote in advance. Two different real bugs, run through this same agent, can take entirely different numbers of turns down entirely different real paths — and that's correct, not a flaw, because each path really was only discoverable by taking the step before it.

### The test you'll use from now on

Before writing an agent's `think()` loop around anything, ask honestly: **at each step, could you have written down the next action in advance, the same way every time, regardless of what the previous step found?**

If yes — you don't need an agent. A workflow, with the steps as a fixed plan, is not just simpler, it's genuinely *better*: less overhead, same result, and — bonus — fully auditable before you ever run it.

If no — because the next step genuinely depends on what the last one revealed, and that dependency isn't just "stage 2 needs stage 1's finished output" but "stage 2 doesn't even exist as a concept until stage 1 tells you it should" — that's a real agent, and it's about to earn the overhead it costs.

---

## Try it yourself

1. Build the config-discrepancy agent above, or a similar one from your own codebase — a real investigation where the second step genuinely can't be known before the first step's result comes back.
2. Also build the "obviously doesn't need it" version — a task, like the CI-log one, where every step could have been written down as a fixed plan from the start.
3. Run both. For the second one, honestly compare it against writing the same two steps as a plain workflow. Write down what, if anything, the agent's loop actually bought you.
4. State, in one sentence, the real test from this chapter, in your own words.

---

## What's still missing

You now know when an agent earns its overhead. What you haven't learned yet is how to make sure it picks the *right* tool once it decides to act — and what happens when two of its tools sound similar enough that it picks wrong, confidently, without anyone noticing until later. That's [Chapter 4](04-tools-and-grounding.md).

---

← [Chapter 2 — Anatomy of an Agent](02-anatomy-of-an-agent.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Tools and Grounding](04-tools-and-grounding.md)
