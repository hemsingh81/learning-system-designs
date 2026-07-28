# Chapter 6 — Skills vs. Other Tools

← [Chapter 5 — Tools and Scripts](05-tools-and-scripts.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)

---

## Where you left off

Rahul asked a fair question: why build this as a skill, and not something else? He lists three alternatives off the top of his head — a slash command, a subagent, a hook. You realise you've been using all four words loosely, without a clear line between them.

This chapter draws that line.

**A note before we start:** different AI coding tools use slightly different names for some of these ideas. This chapter uses the names from Claude Code, since it's the concrete example throughout this tutorial — but the underlying ideas transfer to any tool with similar building blocks. If your tool calls something differently, look for the *mental model*, not the exact word.

---

## What you'll learn

1. The one-sentence mental model for a skill, a slash command, a subagent, and a hook.
2. How to choose correctly between them for a real task.
3. What actually goes wrong when you pick the wrong one.

---

## The lesson

### Four tools, four mental models

Just like choosing between different message brokers or different database types, the trick isn't memorising features — it's understanding the *shape* of each tool well enough that the right choice becomes obvious.

**Skill — "a reference card your assistant reaches for on its own."**

You've spent five chapters building one. It sits quietly until a request matches its description, then it loads in and guides the response. Nobody has to remember it exists or type anything special — that's the whole point.

**Slash command — "a button you press yourself."**

You type `/something` and it runs. No guessing about whether it will trigger — you decided, directly, in the moment. Some slash commands are actually built from skills under the hood (you can type a skill's name directly instead of waiting for it to trigger automatically) — but the *experience* is different. A skill is passive, waiting to be recognised. A slash command is active, chosen by you.

**Subagent — "a separate assistant with its own desk."**

A subagent has its own workspace and its own job description, separate from your main conversation. You hand it a task, it goes off and works — sometimes it comes back with an answer while your main conversation carries on with something else entirely. Think of delegating a task to a colleague, rather than consulting a reference card yourself.

**Hook — "a rule that runs no matter what, every time, automatically."**

A hook isn't something your assistant decides to use. It's configured to fire on a specific event — every time a file is saved, say. It runs a fixed check or command, guaranteed, every time. No judgement call involved at all.

### The comparison, side by side

| | Skill | Slash command | Subagent | Hook |
|---|---|---|---|---|
| Who decides to use it? | The assistant, automatically | You, by typing it | The assistant, or you, delegating a task | Nobody — it's configured to always fire |
| Does it need judgement to trigger? | Yes — matching your request to its description | No — you chose it directly | Some — deciding what to delegate | No — it's a fixed rule |
| Has its own separate workspace? | No — loads into the current conversation | No | Yes — runs somewhat independently | No — it's just a command that runs |
| Best for | Repeated, recognisable requests | A task you always want to run yourself, on demand | Big or parallel work you want kept separate from the main conversation | Rules that must hold every single time, no exceptions |

### Working through Rahul's actual question

He asked three specific things. Let's answer them properly, one at a time, using your commit-message and environment-check skills as the real examples.

**"Why not a subagent instead of your commit-message skill?"**

Because the task doesn't need a separate workspace. Writing a commit message needs to see the current diff, which is already right there in your main conversation. Handing it off to a separate subagent would mean handing over that context too, for no real benefit.

A subagent earns its keep when the work is big enough, or independent enough, that keeping it *out* of your main conversation actually helps. A large research task you want running in the background while you keep working on something else — that's a genuine fit.

**"Why not a hook for the environment check?"**

This is actually the sharpest question of the three, and it's worth sitting with. A hook genuinely *could* run your `check-env.sh` script automatically — say, every time you open the project. That's not a wrong idea.

Here's the real difference: **a hook has no judgement.** It fires every time, unconditionally, and does exactly one fixed thing. Your skill, by contrast, decides *when it's relevant*. It might notice a related but differently-worded request — "why isn't my app connecting to the database?" — and run the same check as part of a broader, more flexible response.

The honest answer: **for a fixed, always-true rule with no reasoning involved, a hook is often the simpler choice.** For something that needs recognising across a range of phrasings, a skill fits better. Chapter 9's checklist will help you make this call for real.

**"Why is this a skill and not a slash command?"**

Because you want it to work without anyone having to remember its exact name. A new hire, on day one, doesn't know your team has a `/check-env` command. They *will*, naturally, type something like "why isn't my local setup working?" A skill can catch that. A slash command only fires if someone already knows it exists and types it correctly.

That's the general-purpose reason to prefer a skill over a slash command: **skills are for when you can't rely on people remembering the exact trigger.** Slash commands are for when you, personally, want a fast, deliberate, on-demand action — and don't mind remembering it.

### A simple decision framework

Ask these in order. Stop at the first one that gives you a clear answer.

**1. Does this need to happen every single time, with zero exceptions, no judgement call?**
→ **Hook.** A fixed rule doesn't need an assistant deciding whether to apply it.

**2. Does this need a separate workspace — big, independent, or parallel work?**
→ **Subagent.** Keep it out of the main conversation.

**3. Will you personally always know exactly when you want this, and are happy to type its name?**
→ **Slash command.** No need for it to guess — you're deciding directly.

**4. Otherwise — is it a repeated, recognisable request that different people will phrase differently?**
→ **Skill.** This is the case your whole tutorial so far has been building for.

Run your commit-message skill through this. It's not a fixed unconditional rule — only when someone actually asks. It doesn't need a separate workspace. And different engineers will phrase the request differently, rather than all memorising one exact command. Question 4 fits. Skill is correct.

### What goes wrong when you pick the wrong one

**Picking a skill when you needed a hook.** You'll get inconsistent enforcement. Sometimes your assistant recognises the situation and applies the rule. Sometimes the phrasing doesn't quite match, and it doesn't. For a rule that truly must always hold, that inconsistency is a real problem, not a minor one.

**Picking a hook when you needed a skill.** You'll get a rule that fires constantly, even when it's not relevant. People find a way to turn it off entirely — and now you've lost the enforcement you were trying to guarantee.

**Picking a subagent when a skill would do.** You'll pay for a separate workspace and the overhead of handing off context, for a task that didn't actually need to leave the main conversation. Usually just slower, not wrong.

**Picking a slash command when you needed a skill.** People simply won't remember it exists, especially new hires. The convention you tried to enforce quietly stops being followed — which is the exact problem skills exist to solve in the first place.

---

## Try it yourself

Take three things your own team does repeatedly — pick real ones, not hypothetical.

1. Run each one through the four-question decision framework above.
2. For each, write one sentence explaining *why* it landed where it did — not just the answer, the reasoning.
3. Pick the one that landed on "skill." Sketch its description, using the two-sentence shape from Chapter 4.

---

## What's still missing

You now know which tool to reach for, and you've built a real skill using the right one. Before you hand it to anyone else, there's one honest question left: **is it actually reliable, or does it just seem to work because you've only tried the phrasings that feel natural to you?**

That's the next chapter.

---

← [Chapter 5 — Tools and Scripts](05-tools-and-scripts.md) · [Learning path](../learning-path.md) · Next: [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md)
