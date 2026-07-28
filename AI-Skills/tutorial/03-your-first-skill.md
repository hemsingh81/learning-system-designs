# Chapter 3 — Your First Skill

← [Chapter 2 — Anatomy of a Skill](02-anatomy-of-a-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Writing Trigger Descriptions](04-writing-trigger-descriptions.md)

---

## Where you left off

You can read a skill now. Rahul catches you at your desk. "Stop reading examples," he says. "Build one. Something small. You'll learn more in twenty minutes of building than another hour of reading."

He's right, and you know it. Time to build your first skill.

---

## What you'll learn

1. How to create a working skill from an empty folder.
2. How to test that it actually triggers.
3. The first mistake almost everyone makes — and what it teaches you.

---

## The lesson

### Pick something small, on purpose

Your instinct will be to build something impressive. Resist it.

Pick the smallest possible real task. You're not trying to prove anything yet — you're trying to see the whole loop work once: write it, trigger it, watch it work, watch it fail, fix it. That loop is the actual lesson. The task itself barely matters.

You pick this: **a skill that writes a commit message in Kestrel's format**, using the example from Chapter 2 as a starting point, but written by you, from scratch, understanding every line.

### Step 1 — Make the folder

```bash
mkdir kestrel-commit-message
cd kestrel-commit-message
```

One folder, named after the skill. Nothing clever yet.

### Step 2 — Write a first draft, badly

Here is the version you write in your first two minutes, without thinking too hard:

```markdown
---
name: kestrel-commit-message
description: Helps with commits
---

Write a good commit message.
```

Stop and look at this. It's genuinely bad, and you'll fix it in a moment — but first, notice exactly *why* it's bad. This matters more than the fix.

**The description is nearly useless.** "Helps with commits" could mean writing a message, reverting a commit, explaining what `git commit` does, or something else entirely. Your assistant has no real signal here about when to actually use this over just answering normally.

**The instructions are vague.** "Write a good commit message" — good by what standard? There's no format specified. Two different engineers running this skill would get two different message styles, which defeats the entire purpose of having a team convention in the first place.

This is not a hypothetical mistake. It is the mistake almost every new skill-builder makes on their first try — writing a description and instructions that feel obviously clear *to the person who just wrote them*, because the format is sitting fresh in their head, and completely underspecified to anyone — or anything — reading it cold.

### Step 3 — Fix it properly

```markdown
---
name: kestrel-commit-message
description: Writes a commit message following Kestrel's format
  (type(scope): description). Use when the user asks for a commit
  message, or asks to commit their changes.
---

You are writing a commit message for the Kestrel Software codebase.

Format: `type(scope): short description`

Allowed types: feat, fix, docs, refactor, test, chore.

Before writing the message:
1. Look at the actual code changes. Do not guess what changed.
2. Identify which type applies. If more than one seems to fit, pick
   the one that best describes the PRIMARY change.
3. Identify the scope — usually the folder or module that changed.

Rules for the description:
- Use the imperative mood: "add", not "added" or "adds"
- Keep it under 72 characters
- Do not end with a period
- Do not restate the type or scope in the description text

Output only the commit message. No explanation, no extra commentary.
```

Compare this to your first draft. Every vague word has been replaced with something checkable. "A good commit message" became six specific, checkable rules. "Helps with commits" became a description that states exactly what it does and exactly when to use it.

This is the actual work of skill-building. Not creativity — precision.

### Step 4 — Test that it triggers

Now try it. Ask your assistant something that should trigger this skill — a request like "write a commit message for these changes" — with the skill available to it.

**What you're checking for:**

1. Did it actually reach for your skill, or did it just answer from general knowledge?
2. Did the output follow your format exactly?
3. Did it look at the real code changes, or did it write something generic?

If your assistant used the skill correctly, you'll see output that matches your format exactly — a real type, a real scope pulled from the actual files that changed, a description under 72 characters, no period at the end.

### Step 5 — Watch it fail, on purpose

Now try a request that's related, but shouldn't trigger this specific skill. Something like "what does a good commit message look like in general?" — a question *about* commit messages, not a request to *write* one.

Pay close attention to what happens here. This is the mistake almost everyone hits on their first skill, and it's worth seeing happen to you directly rather than just being told about it.

Two things can go wrong, and they're opposite problems:

**It triggers when it shouldn't.** Your skill fires even though the user just wanted general advice, not an actual commit message for actual changes. This happens when your description is too broad — it matches more requests than it should.

**It doesn't trigger when it should.** You ask in a slightly different way than your test phrase — "can you help me commit this?" instead of "write a commit message" — and it doesn't fire at all. This happens when your description is too narrow, tied too closely to one exact phrasing.

Both problems come from the same root cause: **the description doesn't accurately capture the real boundary of when this skill is useful.** You will fix this properly in the next chapter — it's important enough to deserve its own.

For now, just notice it happened. That's the whole point of this exercise.

---

## Try it yourself

1. Build the commit-message skill above, or a similarly small skill for your own team's convention — a PR title format, a branch naming rule, anything small and repeated.
2. Test it with three different phrasings of a request that *should* trigger it. Note which ones actually did.
3. Test it with one request that's related but *shouldn't* trigger it. Note whether it correctly stayed out of the way.
4. Write down, in one sentence, what you'd change about your description based on what you just saw.

---

## What's still missing

You have a working skill. You've also just seen it misfire — either triggering too often, or not often enough, depending on exactly how you phrased your test.

You know *that* it happened. You don't yet know precisely *why*, or how to fix it in a way that generalises — not just patch this one skill, but understand the actual rule that makes any description reliable.

That's the next chapter, and it's the most important one in this whole tutorial.

---

← [Chapter 2 — Anatomy of a Skill](02-anatomy-of-a-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 4 — Writing Trigger Descriptions](04-writing-trigger-descriptions.md)
