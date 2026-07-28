# Chapter 3 — Your First Workflow

← [Chapter 2 — Anatomy of a Workflow](02-anatomy-of-a-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Parallel vs. Pipeline](04-parallel-vs-pipeline.md)

---

## Where you left off

You can read a workflow now. Rahul says the same thing he said back when you built your first skill: "Stop reading examples. Build one."

You pick something small on purpose, exactly like you did in AI-Skills — you're not trying to prove anything yet, you're trying to see the whole loop work once.

---

## What you'll learn

1. How to build a working workflow with more than one stage.
2. How to notice when a workflow isn't actually buying you anything.
3. The first real mistake almost everyone makes — and it's not the one you'd expect.

---

## The lesson

### Pick something small, on purpose

You choose this: **a workflow that checks whether a PR's description mentions testing, and separately checks whether it mentions any breaking changes** — two small, genuinely separate checks, combined into one short summary.

### Step 1 — The first draft

Here's what you write in your first ten minutes, feeling rather pleased with yourself for using `parallel()`:

```javascript
meta = {
  name: "pr-description-check",
  description: "Checks a PR description for testing notes and breaking changes",
  phases: [{ title: "Check" }]
}

phase("Check")

results = parallel([
  () => agent("Does this PR description mention how it was tested? " + pr_description),
  () => agent("Does this PR description mention any breaking changes? " + pr_description)
])

return results
```

You run it. It works. Two findings come back. You feel good about it, for about five minutes.

### Step 2 — The honest question

Then you time it against just... asking both questions directly, one after another, without any workflow at all:

```
"Does this PR description mention testing? Also, does it mention any
breaking changes? Here's the description: [pr_description]"
```

One plain request. One assistant, answering both questions in a single response.

**It's not slower. If anything, it's a little faster** — no overhead of spinning up two separate pieces of work and combining them afterward. The answer quality is about the same, too. These two questions don't actually benefit from being looked at with different focus, different context, or independent judgement. They're both just "read this short paragraph and answer a yes/no question about it."

This is the actual, uncomfortable lesson of this chapter, and it's more important than any syntax: **you just built a workflow for a task that didn't need one.**

### Why this happens to almost everyone

Once you know workflows exist, and you've just learned the pattern for running things `parallel()`, there's a real temptation to reach for it. It's the same way, right after learning a new tool, you look for excuses to use it. You built one, it worked, and "it worked" quietly got mistaken for "it helped."

**A workflow has real overhead.** Spinning up separate, focused pieces of work costs actual time and actual cost — genuinely more than one plain request, if that plain request was already going to do a fine job. That overhead is *worth it* when the pieces of work genuinely benefit from separate focus, independent judgement, or a real check on each other. It's pure cost, with nothing bought, when they don't.

Go back to Chapter 1's five-specialist analogy for a second. Hiring five specialists for a 600-line PR touching five different concerns is obviously worth it. Hiring five specialists to answer "does this two-line PR description mention tests?" is not. One person can read two lines and answer both questions perfectly well. You've just paid for four extra people who added nothing.

### Step 3 — Find a task that actually earns it

You go back to your team's real work. You look for something with a property your PR-description example didn't have: **the pieces need genuinely different context, or genuinely different focus, to do a good job.**

You land on this: **checking a small utility function for both correctness and for whether its name actually describes what it does.** These sound similar. They're not. Checking correctness means tracing the logic against test cases. Checking the name means deliberately *ignoring* the implementation and asking "if I only read this name, what would I assume it does?" Doing both well, in one continuous pass, is genuinely harder than doing them as two separately-focused looks. The naming check specifically wants to *not* be influenced by having just read the implementation closely.

```javascript
meta = {
  name: "function-review-check",
  description: "Checks a function for correctness and for whether its name is accurate",
  phases: [{ title: "Check" }]
}

phase("Check")

results = parallel([
  () => agent("Trace through this function's logic against these test cases. Does it behave correctly? " + function_code + test_cases),
  () => agent("Read ONLY this function's name and signature — not its body. What would you assume it does? " + function_signature)
])

return results
```

Notice the second `agent()` call is deliberately given *less* information than the first — only the name and signature, not the body. That's not an accident. It's also not something you could do inside one continuous skill pass, where the reasoning naturally has access to everything at once. **This is what a real, earned parallel split looks like: each piece needs its own, different slice of context to do its specific job well.**

### The test you'll use from now on

Before writing `parallel([...])` around anything, ask honestly: **would one focused piece of work, given all the same information, do just as good a job as several separate pieces?**

If yes — you don't need a workflow. A skill, or a plain request, is not just simpler, it's genuinely *better*: less overhead, same quality.

If no — because the pieces need different focus, different context, or a genuine second opinion — that's a real workflow, and it's about to earn the overhead it costs.

---

## Try it yourself

1. Build the function-review workflow above, or a similar one from your own codebase — two checks that genuinely benefit from *different* context or focus, not just two questions that happen to be about the same thing.
2. Also build the "obviously doesn't need it" version — two questions that could just as well be one plain request.
3. Run both. For the second one, honestly compare it against just asking directly. Write down what, if anything, the workflow actually bought you.
4. State, in one sentence, the real test from this chapter, in your own words.

---

## What's still missing

You now know when a workflow earns its overhead. What you haven't learned yet is the deeper version of the same question. Even when several pieces of work genuinely are independent, should they *all* run at the exact same time? Or does the shape of the actual task call for something else, where work flows through stages instead of waiting in a single batch?

That's [Chapter 4](04-parallel-vs-pipeline.md), and it's the most important chapter in this tutorial.

---

← [Chapter 2 — Anatomy of a Workflow](02-anatomy-of-a-workflow.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Parallel vs. Pipeline](04-parallel-vs-pipeline.md)
