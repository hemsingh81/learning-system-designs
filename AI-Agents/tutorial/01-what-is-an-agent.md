# Chapter 1 — What Is an Agent?

← [Back to README](../README.md) · [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of an Agent](02-anatomy-of-an-agent.md)

---

## Where you left off

Yesterday, per [`00-the-story.md`](../00-the-story.md), you tracked down an intermittent reporting bug yourself — ninety minutes, no workflow, no fixed plan. You looked at the aggregation code, formed a guess, checked it, and let what you found decide what to check next.

Rahul called that an agent. Today you find out what he actually meant.

---

## What you'll learn

1. What an agent actually is — not a bigger workflow, a genuinely different kind of tool.
2. The one thing an agent can do that a workflow's fixed plan structurally cannot.
3. A real software engineering use case where only an agent's shape actually fits.

---

## The lesson

### Start with what you already know

A skill is one set of instructions, followed in one continuous flow of reasoning, picked up automatically when it matches.

A workflow is a **fixed plan**, written out in advance, as an actual script. It might run several things in parallel, or in a pipeline, or check its own findings — but the *plan itself* is decided before anything runs. Every phase, every stage, every branch — you wrote all of it down before the workflow ever saw its first real input.

That fixed plan is exactly what made a workflow trustworthy. You could read it, audit it, know exactly what it would do on any input, before running it once.

### The shape workflow can't cover

Go back to yesterday's bug. Before you looked at anything, could you have written down the five steps you'd take, in order, the way you wrote Chapter 1 of AI-Workflows' five-angle review?

No. Genuinely no — not "you didn't bother," but **you could not have known step 2 until you saw the result of step 1.** You looked at the aggregation code first because that seemed like the most likely place. You only decided to check the cache *because* the aggregation code led you there. You only picked those three specific customers to check logs for *because* the cache theory pointed at them specifically.

Every step depended on the step before it — not in the "stage 2 needs stage 1's finished output" sense a pipeline handles fine, but in the sense that **you didn't know stage 2 would happen at all until stage 1 told you it should.**

### The actual definition

An **agent** is something with a goal, a set of tools, and a loop — instead of a fixed plan. On each turn of the loop, it looks at what it currently knows, decides what to do next *based on that*, does it, and looks again. It keeps going until it reaches its goal, runs out of budget, or hits a condition that tells it to stop.

Written as a shape, not code yet — that's [Chapter 2](02-anatomy-of-an-agent.md)'s job:

```
GOAL: find out why report totals are sometimes wrong for some customers

LOOP:
  1. Look at what you currently know
  2. Decide the single most useful next thing to check
  3. Check it (read a file, run a query, check a log — a real tool call)
  4. Add what you learned to what you know
  5. Is the goal reached? If yes, stop. If no, go back to step 1.
```

Nobody wrote "check the cache" anywhere in that loop in advance. The loop *decided* to check the cache, on its own, because of what step 3 turned up two iterations earlier. That's the entire difference, and it's not a small one.

### The analogy that actually holds up

A workflow is a recipe. Every step is decided in advance — chop the onions, then heat the oil, then add the onions — and the order doesn't change no matter what the onions look like when you chop them.

An agent is a detective. There's a goal — find out who did it — and a set of tools — question a witness, examine evidence, check an alibi. But *which* witness gets questioned next depends entirely on what the last piece of evidence turned up. Nobody could have written the interview order in advance, because the order only makes sense in light of what's already been discovered.

Both are legitimate, useful shapes. Neither is a worse or incomplete version of the other. A recipe is exactly right when you already know the steps. A detective's open loop is exactly right when you genuinely don't, yet.

### A real software engineering use case

This is the shape behind:

- **Debugging an intermittent, hard-to-reproduce bug** — exactly yesterday's story. You don't know the cause going in, so you can't write the steps in advance.
- **Triaging a production incident** — the first alert tells you almost nothing about the real cause. Each thing you check narrows or redirects the investigation.
- **Exploring an unfamiliar part of a codebase** to answer a question like "everywhere this config value is actually used, including indirectly" — you don't know the full set of places to look until you've followed the first few references.
- **Root-causing a flaky test** — [Case Study 2](../case-studies/02-backend-agent/README.md) walks through exactly this, hypothesis by hypothesis.

What these all share: **the right next step is genuinely unknown until you've taken the step before it.** That's the test. Keep it — you'll use it constantly from here on, the same way you kept Chapter 3 of AI-Workflows' "would one focused piece of work do just as well" test.

### What an agent is *not*

An agent is not "a workflow with more phases." A workflow with ten phases is still a fixed plan — you could still draw the whole thing out before running it once. An agent with one single tool call is still an agent, if that one call's target genuinely couldn't have been chosen in advance.

The difference isn't size. It's whether the plan exists before the first observation, or gets built one step at a time *because of* what each observation reveals.

---

## Try it yourself

Think of a real, open-ended task you've done recently — a bug you tracked down, an unfamiliar error you had to chase, an incident you triaged. Write down, honestly, in one or two sentences: **at the point you started, could you have written out your exact steps in order? Or did each step genuinely depend on what the last one told you?**

If you can write the steps in advance — that's a workflow's job, not an agent's. If you genuinely can't — you've just found a real candidate for this whole tutorial.

---

## What's still missing

You know what makes something an agent in principle. You don't yet know what one actually looks like written down — what a "goal" is in practice, what a "tool" really is, what decides when the loop stops. That's [Chapter 2](02-anatomy-of-an-agent.md).

---

← [Back to README](../README.md) · [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of an Agent](02-anatomy-of-an-agent.md)
