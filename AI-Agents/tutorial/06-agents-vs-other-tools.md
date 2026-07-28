# Chapter 6 — Agents vs. Other Tools

← [Chapter 5 — Stopping Conditions and Budgets](05-stopping-conditions-and-budgets.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)

---

## Where you left off

Your config-discrepancy agent is solid now — picks the right tool, grounds its answers, stops honestly. You show it to Rahul, proud of it. His response isn't "nice work." It's a question:

> "Why isn't this just a workflow with more phases? You could write a phase for 'check env vars,' a phase for 'check feature flags,' a phase for 'check config files' — run them all, look at whichever one found something. What does the loop actually buy you that a longer workflow doesn't?"

It's a fair question, and it's the same kind of question he asked at the end of AI-Skills ("why isn't this just five separate skills?") and AI-Workflows ("why isn't this just calling skills by hand?"). You need a real answer, not a feeling.

---

## What you'll learn

1. The real, precise difference between an agent and "a workflow with more phases."
2. A complete decision framework covering hooks, subagents, skills, workflows, and agents.
3. How to choose correctly, for a real task, in under a minute.

---

## The lesson

### Answering Rahul's question directly

Here's the honest answer: **you could, in fact, write your config-discrepancy check as a workflow with three phases** — one for each tool — run all three, and combine whatever they find. For *this specific task*, that would even work, because the three checks don't actually block each other; they could all run and you'd pick whichever came back with a real answer.

But that's not the same as claiming a workflow can always replace an agent. The difference isn't the *number* of phases — you could give a workflow fifty phases and it would still be exactly as fixed and auditable as one with two. The difference is **when the decision about what to do next gets made.**

A workflow's phases — all of them, however many there are — are decided before the workflow ever sees its first real input. You could print out the whole plan and hand it to someone before running it once, and it would be completely accurate. An agent's next action is decided *during* the run, using a result that didn't exist until the previous action produced it. You cannot print out an agent's full path in advance, because it doesn't exist yet — it's built one turn at a time, out of things that haven't happened.

**Your specific config-discrepancy task genuinely could go either way**, and that's a fair thing for Rahul to notice — the three checks happen not to depend on each other. [Case Study 2](../case-studies/02-backend-agent/README.md) shows a task where they genuinely can't be pre-planned: each hypothesis is only worth testing *because* the previous one came back negative, and a fixed "try all four theories and see which one works" plan would waste real effort checking things a smarter, adaptive investigation would have already ruled out.

### The complete decision framework

Extending the framework from AI-Skills and AI-Workflows with the one new branch:

```
Must this happen every time, with zero exceptions, no judgement call?
  → YES: Hook

Does this need a separate workspace — big or parallel work?
  → YES: Subagent

Do you already know every step, in the order (or overlap) it needs to
run, before you've looked at anything?
  → YES: Is it one continuous focused task, or several coordinated ones?
      ONE: Skill
      SEVERAL: Workflow

Does the right next step genuinely depend on what gets discovered along
the way — not knowable until the step before it runs?
  → YES: Agent

None of the above cleanly fits?
  → Rethink — this might not need automating
```

Walk through it on a few real cases.

**"Write a commit message from this diff."** One continuous, recognizable, repeated task. Skill.

**"Review this PR from five focused angles, then verify each finding."** Several coordinated pieces, all knowable in advance — you always run the same five angles, always verify the same way. Workflow.

**"Find out why this report has wrong totals for some customers."** The very first move might turn up nothing, and *what you try next depends entirely on what it did turn up.* Agent.

**"Run this exact linter on every file before commit."** Zero exceptions, no judgement, every single time. Hook.

**"Refactor this 40-file module, safely isolated from the rest of my work."** Large, needs its own workspace so it doesn't collide with what else is happening. Subagent.

### The line that actually separates workflow from agent

State it once, plainly, because it's the one sentence worth remembering from this whole chapter: **a workflow's plan is fixed before the first observation. An agent's plan is built one step at a time, using each observation to decide the next one.** Everything else in this tutorial — the loop, the tools, the stopping condition — exists to support that one distinction.

This also means the same real task can sometimes honestly go either way, the way your config-discrepancy check did. When that happens, prefer the workflow. It's more predictable, easier to test, easier to audit, and cheaper to run — an agent's flexibility is a real cost, not a free upgrade, and you should only pay for it when the task genuinely can't be pre-planned. That's the same discipline as Chapter 3's "would one focused piece of work do just as well" test, one level up the ladder.

### What an agent still can't replace

An agent doesn't replace a hook's guarantee — nothing about a goal-driven loop can promise "this runs every single time, no exceptions," because deciding *whether* to act is part of what the loop does. It doesn't replace a workflow's auditability — you genuinely cannot read an agent's exact path in advance the way you can read a workflow's phases. And it doesn't replace a skill's simplicity for a task that was never actually open-ended in the first place, as your CI-log story from [Chapter 3](03-your-first-agent.md) already showed.

---

## Try it yourself

Take three real, open-ended-*sounding* tasks from your own team. For each one, run it through the decision framework above, honestly. For at least one of them, check specifically: could every step actually have been planned in advance, the way your CI-log agent turned out not to need a loop at all? If so, it's a workflow wearing an agent's clothes — rebuild it as one, and notice what got simpler.

---

## What's still missing

You can choose the right tool now. What you haven't done is prove your agent actually works, reliably, across more than one lucky run — and testing something that takes a different path every time is a genuinely different problem than testing a workflow's fixed phases. [Chapter 7](07-testing-and-iterating.md) is that.

---

← [Chapter 5 — Stopping Conditions and Budgets](05-stopping-conditions-and-budgets.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)
