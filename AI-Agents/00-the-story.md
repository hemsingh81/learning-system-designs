# The Story So Far

← [AI-Workflows](../AI-Workflows/README.md) · [README](README.md) →

If you're arriving here from [AI-Skills](../AI-Skills/00-the-story.md) and [AI-Workflows](../AI-Workflows/00-the-story.md), you already know Kestrel Software, and you already know this cast. If you're arriving here fresh — welcome. This tutorial still works on its own, but it's the third and final chapter of one continuous story, and it's worth twenty minutes to read the first two.

---

## Where you left off

You built a skill — one focused set of instructions, triggered automatically when a request matched it. Then you built a workflow — several of those focused pieces, coordinated on purpose, running in a fixed plan you wrote out in advance.

Both worked. Both are still running at Kestrel, every day. Rahul's five-angle review workflow — the one that closed out AI-Workflows — has reviewed something like three hundred PRs since you built it, and it still runs the same five angles, every single time, exactly as written.

That's where today's story starts: with a PR the five-angle workflow couldn't actually help with.

---

## The PR nobody could review with a fixed plan

A customer reports a bug: sometimes, not always, a specific report on the dashboard shows numbers that don't add up. Not every time. Not for every customer. Divya spends an afternoon trying to reproduce it and can't, on her machine, at her desk, in the normal course of testing.

Someone suggests running Rahul's five-angle review workflow against the reporting code, just in case it catches something. It doesn't — not because the workflow is broken, but because the workflow was never built for this. Five fixed angles — security, tests, style, data access, docs — checked against a diff that already exists. This isn't a diff. Nobody has written a fix yet. Nobody even knows what's wrong yet.

What this actually needs is investigation: look at the reporting code, form a guess about what might cause an intermittent, customer-specific miscalculation, check that guess against the logs, and — this is the part a workflow's fixed plan can't do — **decide what to look at next based on what you just found**, not based on a plan someone wrote before looking at anything.

You spend the rest of the afternoon doing exactly that yourself. Look at the aggregation code. Notice it depends on a cache. Check whether the cache could be stale for some customers and not others. Find that it can, under a specific, narrow timing condition. Confirm it against three of the affected customers' logs. Total time: about ninety minutes, almost all of it spent following one finding to the next.

Rahul watches you do this and says the same kind of thing he's said twice before, at the end of your last two stories:

> "That's not a workflow either. You didn't run five checks and combine them. You ran one check, decided what it told you, and picked the next check *because of* what the last one found. That's not a fixed plan. That's an agent."

---

## What "done" will look like

By the end of this tutorial, you'll understand:

- What actually makes something an **agent**, and why it's a genuinely different tool from a skill or a workflow — not a fancier version of either.
- How to build one, from the smallest possible version to something that can investigate a real, open-ended problem.
- The one thing an agent can do that a workflow structurally cannot: **decide its own next step, based on what it just discovered**, instead of following a plan written in advance.
- Why that same freedom is also the risk that's unique to agents, and the one deliberate limit that makes it safe to hand one real tool access.
- How to package an agent so a teammate can point it at their own investigation, and trust the boundary around what it's allowed to do without asking first.

You'll build this the same way you built the last two: starting small, on purpose, with a task that's genuinely too small to need an agent — so you can feel, honestly, the difference between "this worked" and "this was worth it."

---

## The chapter arc

| # | Chapter | What you'll be able to do after |
|---|---------|----------------------------------|
| 1 | What Is an Agent? | Explain the real difference between a skill, a workflow, and an agent — in one sentence each |
| 2 | Anatomy of an Agent | Read any agent and identify its goal, its tools, its loop, and its stopping condition |
| 3 | Your First Agent | Build a working agent, and correctly judge when a task doesn't actually need one |
| 4 | Tools and Grounding | Give an agent tools it can trust itself to use correctly, and know when it picked the wrong one |
| 5 | Stopping Conditions and Budgets | Stop an agent that's looping, drifting, or burning cost without progress |
| 6 | Agents vs. Other Tools | Choose correctly between a skill, a workflow, a subagent, a hook, and an agent |
| 7 | Testing and Iterating | Test something that doesn't take the same path twice, on purpose |
| 8 | Packaging and Sharing | Share an agent a teammate can trust, with a boundary they don't have to take on faith |
| 9 | Governance and Capstone | Prevent the one mistake unique to agents: an irreversible action nobody explicitly approved |

Four case studies close it out — the same four teammates, the same four disciplines, now each facing a problem that genuinely needed to be investigated, not just checked.

---

## Ready?

Start with [Chapter 1 — What Is an Agent?](tutorial/01-what-is-an-agent.md), or skim the [learning path](learning-path.md) first if you want the full map before you start walking it.

---

← [AI-Workflows](../AI-Workflows/README.md) · [README](README.md) →
