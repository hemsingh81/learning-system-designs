# Chapter 1 — What Is a Skill?

← [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of a Skill](02-anatomy-of-a-skill.md)

---

## Where you left off

It is your first week at Kestrel Software. You watched a teammate type `/code-review` into their AI coding assistant. It came back with a structured review, following rules specific to Kestrel's codebase. You had never seen those rules written down anywhere.

"What was that?" you asked.

"A skill," they said, and moved on to their next task like it was nothing special.

To you, it was very special. You want to know what a skill actually is.

---

## What you'll learn

1. What a skill is, in plain words, using something you already understand.
2. Why a skill is different from just asking a good question.
3. Three real examples of skills a software team would actually use.

---

## The lesson

### Start with something you already know

You have trained new engineers before. Think about how you do it.

You do not re-explain everything from scratch every single day. You write it down once — a wiki page, a checklist, an onboarding doc — and you point people at it when it's relevant. Nobody re-teaches "how to set up your laptop" every Monday morning.

A skill does the same thing, but for your AI assistant.

**A skill is a written-down set of instructions that your AI assistant picks up on its own, exactly when it's relevant, without you having to explain it again.**

That's the whole idea. Everything else in this tutorial is detail on top of that one sentence.

### Why not just... ask well?

Here is the honest question: if you can just type good instructions into the chat, why do you need a "skill" at all?

Two reasons.

**First: you'd have to type those good instructions every single time.** Imagine writing out your team's entire code review checklist, by hand, in the chat window, every time you wanted a review. You wouldn't. You'd get lazy after the third time, and the checklist would quietly stop being followed.

**Second: you have to remember it exists.** A skill's whole job is to notice, on its own, "this request matches something I know how to do" — and step in. You don't have to remember to ask for it. It recognises the moment.

Think about the difference between a junior engineer who needs the checklist re-explained every time, and a senior engineer who has internalised it and applies it automatically, without being asked. A skill is how you get that second behaviour from your AI assistant — reliably, and for the whole team at once.

### A closer look at "picks it up on its own"

This part surprises people the first time they see it.

You do not usually type a skill's name to use it. You just ask for what you want, in your own words. Somewhere behind the scenes, your assistant is holding a short list of every skill available to it — just a name and a one-line description for each, not the full instructions yet. When your request matches one of those descriptions closely enough, it reaches for that skill and loads the full instructions.

This is exactly like a company directory. You don't memorise everyone's full job description. You see a short list — name and role — and when you have a payroll question, you know to go find the person whose one-line description says "payroll." You don't read their full job description until you actually need them.

That's what a skill's description does. It's the one-line summary that decides whether the skill gets picked, out of everything else available.

You'll spend a whole chapter on that description later — [Chapter 4](04-writing-trigger-descriptions.md) — because getting it right is the hardest part of building a skill that actually works. For now, just remember: **the description is what decides whether the skill gets used at all.**

### What a skill is not

A few things people confuse it with, cleared up early:

**A skill is not a macro.** A macro replays the exact same steps every time. A skill reasons about your specific situation and adapts, the same way a person following a checklist adapts it to what's actually in front of them.

**A skill is not a plugin in the traditional sense.** It doesn't add a new button or a new menu. It adds a new *habit* your assistant can reach for.

**A skill is not the same as a subagent.** A subagent is a separate assistant with its own job and its own workspace. A skill is more like handing your current assistant a reference card mid-conversation. [Chapter 6](06-skills-vs-other-tools.md) covers this difference properly — for now, just know they are not the same thing, even though they can look similar from the outside.

### Real examples, from a software team

Here is what makes this concrete. Three things Kestrel's engineers do by hand, every week, that are good candidates for a skill:

| What people do by hand today | What a skill would do instead |
|---|---|
| Explain the commit message format to every new hire, individually | Recognise "write me a commit message" and apply the format automatically |
| Manually check a PR against a review checklist, from memory | Recognise "review this PR" and check it against the written checklist every time, the same way |
| Re-explain how to set up a local dev environment | Recognise "help me set up my environment" and walk through the real, current steps |

Notice what these three have in common. Each one is:

- **Repeated.** Not a one-off request.
- **Well-defined.** You could write the correct process down, if you had to.
- **Recognisable.** You can describe, in one sentence, what kind of request should trigger it.

Those three properties are the actual test for "should this be a skill?" You'll come back to this test in [Chapter 9](09-governance-and-capstone.md), once you've built a few and have real experience to check it against.

---

## Try it yourself

1. Think of one thing you personally explain to teammates or new hires more than twice a month. Write it down in one sentence.
2. Check it against the three properties above: is it repeated, well-defined, and recognisable? If any answer is no, say specifically why.
3. Write one sentence describing exactly what kind of request should trigger this — before you've built anything. You'll need this sentence again in Chapter 4, so keep it.

---

## What's still missing

You now know what a skill *is*. You don't yet know what one *looks like* — the actual file, the actual shape, the actual words inside it.

Right now, if someone handed you a real skill file, you wouldn't know how to read it.

That's the next chapter.

---

← [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of a Skill](02-anatomy-of-a-skill.md)
