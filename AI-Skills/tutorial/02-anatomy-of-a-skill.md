# Chapter 2 — Anatomy of a Skill

← [Chapter 1 — What Is a Skill?](01-what-is-a-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Skill](03-your-first-skill.md)

---

## Where you left off

You now know what a skill is, in plain words. Rahul sends you a link to a real skill file used on another team — a code-review skill — and says "have a read, it'll make more sense once you see one."

You open it. It's a folder with one main file inside. You read it top to bottom.

It half makes sense. You can tell it's instructions. You can't tell why it's organised the way it is, or what each part is actually for.

This chapter fixes that.

---

## What you'll learn

1. The shape every skill has — the parts that are always there.
2. What the "name" and "description" actually do, mechanically.
3. How to read any skill's file, cold, and understand every part of it.

---

## The lesson

### The shape, at a glance

Nearly every skill is built from the same three pieces, arranged the same way.

```
your-skill-name/
├── SKILL.md          ← the main file. Name, description, instructions.
└── (optional extras)  ← scripts, reference data, templates. Chapter 5 covers these.
```

That's it. One folder. One main file inside. Everything else is optional, and you add it only when plain instructions aren't enough — which is [Chapter 5](05-tools-and-scripts.md)'s whole topic.

Let's open that main file and go through it piece by piece.

### The three parts of a skill file

```markdown
---
name: kestrel-commit-message
description: Writes a commit message following Kestrel's format. Use when
  the user asks for a commit message, or asks you to commit changes.
---

You are writing a commit message for the Kestrel Software codebase.

Kestrel's format is: `type(scope): short description`

Types: feat, fix, docs, refactor, test, chore.

Look at the actual code changes before writing the message. Do not
guess at what changed — read the diff.

Keep the description under 72 characters. Use the imperative mood:
"add", not "added" or "adds".
```

Three parts, and each one has a completely different job.

### Part 1 — The name

```
name: kestrel-commit-message
```

This is just an identifier. Short, specific, usually matches the folder name. Nothing clever happens here — it's how the skill is referred to internally, and sometimes how a person types it directly if they want to call it by name instead of waiting for it to trigger automatically.

Not much to explain. The next part is where all the real thinking goes.

### Part 2 — The description

```
description: Writes a commit message following Kestrel's format. Use when
  the user asks for a commit message, or asks you to commit changes.
```

This is the single most important line in the entire file.

Remember the company-directory idea from Chapter 1? This description is the one-line summary your assistant sees *before* it decides to open the full instructions. If ten different skills are available, your assistant is scanning ten of these one-liners, deciding which — if any — actually matches what you just asked for.

Notice this description does two jobs in two sentences:

- **Sentence one says what it does.** "Writes a commit message following Kestrel's format."
- **Sentence two says when to use it.** "Use when the user asks for a commit message, or asks you to commit changes."

Both matter. A description that only says what the skill does, without saying when to reach for it, tends to get missed. A description that's too vague gets grabbed for the wrong requests. You'll spend the whole of [Chapter 4](04-writing-trigger-descriptions.md) on this one field, because it's genuinely the hardest part to get right — but for now, just notice the two-sentence shape. It's a good default to copy.

### Part 3 — The instructions

```
You are writing a commit message for the Kestrel Software codebase.

Kestrel's format is: `type(scope): short description`
...
```

Everything after the two dashed lines is the actual instructions — what to do, once the skill has been picked. This is the part that does the real work, and it reads very differently from the description above it.

Notice a few things about how these instructions are written:

**They're specific, not vague.** "Keep the description under 72 characters" is checkable. "Write a good commit message" is not — good by whose standard?

**They tell it what to look at, not just what to produce.** "Look at the actual code changes before writing the message. Do not guess" — this line exists because, without it, an assistant might write a plausible-sounding message based on the request alone, without actually checking the diff. You are telling it exactly where to get its information from.

**They read like instructions to a new team member**, not like a casual chat message. That's deliberate. Anyone can write "make a good commit message" into a chat box. Writing instructions precise enough that they work the same way every time, for every engineer on the team — that's the actual skill in "skill-building."

### Reading a skill you didn't write

Here's a habit worth building right now, before you write your first skill: whenever you see a skill you didn't write, read it in this order.

1. **Read the description first, alone.** Before reading the instructions, ask yourself: what request would this match? Write your guess down.
2. **Read the instructions.** Does the skill actually do what you predicted from the description?
3. **Check for a mismatch.** If the instructions do something the description didn't hint at, that's a real problem — one you'll learn to spot and fix in Chapter 4. It means the skill might not trigger when it should, because the description doesn't accurately represent what's inside.

This three-step habit is how experienced skill-builders review each other's work. It costs you thirty seconds and catches a huge share of skill problems before they ever reach production.

---

## Try it yourself

Here is a real skill file, with its name changed. Read it using the three-step habit above.

```markdown
---
name: standup-summary
description: Turns rough notes into a 3-line daily standup update —
  what was done, what's next, and any blockers.
---

Summarize the notes below into exactly 3 lines:
1. What was done (yesterday or since the last update)
2. What's planned next
3. Any blockers — write "none" if there aren't any

Keep each line under 20 words. Do not add commentary or a greeting.
Output only the 3 lines.
```

1. Before reading the instructions again, write down: what kind of request would trigger this?
2. Now check — do the instructions match what you predicted?
3. Spot one instruction that's specific and checkable (like "under 72 characters" in the earlier example), and explain why it's better than a vaguer version of the same idea.

---

## What's still missing

You can now read a skill. You still haven't written one.

Reading and writing are genuinely different skills — you'll find that out the moment you try. The next chapter is where you stop reading examples and build a real one, from an empty folder, for your own team.

---

← [Chapter 1 — What Is a Skill?](01-what-is-a-skill.md) · [Learning path](../learning-path.md) · Next: [Chapter 3 — Your First Skill](03-your-first-skill.md)
