# Chapter 8 — Packaging and Sharing

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)

---

## Where you left off

Your five-angle review workflow is tested and working. Divya wants the same pattern for her own frontend checks. Before you hand it over, a question stops you that never came up with a skill: **should this run automatically, the way a skill does — recognised and triggered on its own — or should a person have to actually decide to run it, every time?**

You genuinely don't know the answer yet. This chapter is why the answer is different from what you'd assume.

---

## What you'll learn

1. Why workflows are run on purpose, not triggered automatically like a skill — and why that's the right default, not a missing feature.
2. How to version a workflow, and what counts as a real, breaking change for one.
3. The same three levels of sharing from AI-Skills, adapted for something that coordinates real cost.

---

## The lesson

### Why "automatic, like a skill" is the wrong default here

Think back to how a skill gets picked. Your assistant scans a list of short descriptions, and when your request matches one closely enough, it loads that skill in — automatically, without you deciding to invoke it by name. That's exactly the right behaviour for a skill, because a skill is cheap: one focused piece of work, following one set of instructions.

A workflow is a different kind of thing. Your five-angle review spins up five separate pieces of work, then a verification pass on top of that — potentially six, seven, eight real pieces of work for one request. **That has a real cost, in both time and in whatever your AI provider charges for each piece of work.**

Imagine a workflow like yours getting triggered automatically, the same way a skill is — every time someone's request loosely resembled "check this PR," it silently spins up eight pieces of work without anyone deciding that was worth it. That's not a convenience. That's an expensive surprise waiting to happen, and it's the specific reason **workflows are run deliberately, on purpose, not auto-triggered the way skills are.**

**The rule:** a skill earns automatic triggering because it's cheap and focused. A workflow, because it coordinates real cost across multiple pieces of work, should always require an explicit, on-purpose decision to run — a deliberate command, a clear request naming what you want, never a quiet background guess.

This isn't a limitation to work around. It's the correct, deliberate difference between the two tools, and it's worth explaining to anyone you hand a workflow to, so they understand why it doesn't "just happen" the way their skills do.

### Versioning a workflow

Same idea as versioning a skill, adapted for what actually changes in a workflow.

```
MAJOR.MINOR.PATCH

PATCH  →  Wording change inside one agent() call's instructions, no
          change to the workflow's actual shape
MINOR  →  A new stage added, or an existing stage improved, without
          changing how earlier stages' output is used
MAJOR  →  The orchestration shape itself changed — parallel became
          pipeline (or the reverse), a verification stage was
          removed, or the output's structure changed
```

Apply it to your review workflow's real history:

| Version | What changed | Why that category |
|---|---|---|
| 1.0.0 | First working version — 5 parallel checks, no verification | — |
| 1.1.0 | Added the verification stage from Chapter 5 | New stage, doesn't change how the 5 checks themselves work — **MINOR** |
| 1.1.1 | Reworded one reviewer's instructions for clarity | Wording only — **PATCH** |
| 2.0.0 | Changed verification from "one independent check" to "two independent checks, must both agree," for high-stakes findings | The actual decision logic changed — anyone relying on the old, single-check behaviour would see different results — **MAJOR** |

**Why this matters more for a workflow than it did for a skill:** a MAJOR change here isn't just "the wording is different." It can mean the cost profile changed too — 2.0.0 above roughly doubles the cost of verification for high-stakes findings. A version number that flags that honestly is doing real work, not just bookkeeping.

### The changelog, adapted

```markdown
# Changelog — pr-five-angle-review

## 2.0.0
High-stakes findings (anything that would block a release) now get
verified TWICE, independently, and must be confirmed by both before
being trusted. Roughly doubles the cost of verifying those specific
findings. Normal findings are unaffected — still one verification pass.

## 1.1.0
Added an independent verification stage after the 5 parallel reviews.
Catches plausible-but-wrong findings before they reach the PR — see
the line-84 false alarm this was built to prevent.

## 1.0.0
First version. 5 parallel reviewers, no verification.
```

Notice the 2.0.0 entry explicitly calls out the cost change. That's new compared to how you wrote skill changelogs — a skill's changelog rarely needed to mention cost, because skills are cheap by nature. A workflow's changelog should, whenever a change affects how much work actually gets spun up.

### The three levels, adapted

Same ladder as AI-Skills, same honest advice about not climbing further than you've earned — with one real difference at Level 3.

**Level 1 — Personal.** Still actively changing or testing it. Exactly the same as before.

**Level 2 — Project (shared through your repo).** Checked into your team's repo, so anyone working in it can run it deliberately, on purpose — never automatically. This is where your review workflow belongs once Divya's team wants it too, assuming it's specific enough to Kestrel's own review standards and diff format that it wouldn't transfer cleanly elsewhere.

**Level 3 — Company-wide.** For a workflow genuinely useful across many teams. The real difference from a Level 3 *skill*: because a workflow's whole cost is in how much work it coordinates, a company-wide workflow needs a genuinely clear, visible cost expectation attached to it — something like "this runs roughly 8 pieces of work per PR" stated plainly, not discovered by whoever runs it first. A skill rarely needs this. A workflow always should, once it's shared beyond your own team.

### Choosing the right level, honestly

| Question | If yes |
|---|---|
| Are you still actively changing or testing this? | **Level 1.** Don't share it yet. |
| Is it specific to your team's own conventions, and tested (Chapter 7)? | **Level 2.** Check it into your repo. |
| Would three or more genuinely separate teams want this, unmodified — and is its real cost clearly documented? | **Level 3.** |

Same honest note as before: **most workflows should stop at Level 2.** A workflow that makes your specific team's reviews better, living in your specific repo, is a complete success on its own.

---

## Try it yourself

1. Take your tested workflow from Chapter 7. Give it a real version number.
2. Write its first changelog entry. If it has any cost-affecting change in its history — like adding a verification stage — call that out explicitly in the entry, the way the 2.0.0 example above does.
3. Write one sentence explaining, to someone who's only used skills before, why this workflow won't trigger automatically the way their skills do. Make it genuinely clear, not just "because that's the rule."
4. Using the honest table above, decide which level your workflow actually belongs at right now.

---

## What's still missing

You know how to version, changelog, and share a workflow properly — and you understand why it needs a deliberate decision to run, not automatic triggering.

There's one more thing you haven't been forced to confront yet: what actually stops a workflow from *quietly growing* — one team adds "just one more check" to a fan-out, another team nests a workflow inside a workflow, and suddenly a small PR is spinning up far more work than anyone intended, with nobody having made a single bad decision on purpose.

Rahul is about to show you exactly that happening on another team. That's the last chapter.

---

← [Chapter 7 — Testing and Iterating](07-testing-and-iterating.md) · [Learning path](../learning-path.md) · Next: [Chapter 9 — Governance and Capstone](09-governance-and-capstone.md)
