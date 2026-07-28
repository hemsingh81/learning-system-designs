# Chapter 9 — Governance and Capstone

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Case Studies →](../case-studies/README.md)

---

## Where you left off

Rahul asks you to sit in on a review. Someone on another team built a "cleanup" skill — it deletes old temporary branches, based on a naming pattern, to keep the repo tidy. Reasonable idea. Nobody had used it in production yet.

He pulls up the skill's instructions. Buried in them: "delete any branch matching the pattern, unless it looks important." *Unless it looks important* — decided by the assistant, in the moment, with no second check.

Someone in the review asks the obvious question: what happens the day the pattern accidentally matches a branch that actually mattered? Nobody has a good answer. The skill goes back for changes before it ever ships.

This is the chapter about catching that, on purpose, every time — not by luck.

---

## What you'll learn

1. What specifically makes a skill riskier than a normal script or a normal chat message.
2. How to run a real safety review before sharing a skill beyond yourself.
3. The complete checklist — thought process to sharing — tying together everything from Chapters 1 through 8.

---

## The lesson

### Why skills carry a different kind of risk

You touched on this in Chapter 5, briefly. Here it is properly.

A normal script does exactly what its code says, every time, with no variation. You can read it once and know exactly what it will do in every situation, because there's no judgement involved — just fixed logic.

A skill is different by design. It's built to use judgement, to handle situations you didn't spell out word for word, to adapt. **That flexibility is the entire reason skills are useful — and it's also exactly where the risk lives.** A skill that can decide a branch "looks important" enough to keep can also, some other day, decide wrong.

This isn't a reason to avoid building skills that act on real things. It's a reason to treat "this skill can take a real action" as a specific, named category — one that gets more scrutiny than a skill that only produces text, the same way a database migration gets more scrutiny than a comment fix.

### The three questions that decide how much scrutiny a skill needs

**1. Can this skill only produce text, or can it actually do something?**

Your commit-message skill only produces text — a human still has to choose to use it. Your environment-check skill only reads, never writes. The cleanup skill above deletes branches — a real, and in this case irreversible, action.

**2. If it acts, can that action be undone?**

Writing a file you can overwrite again is one thing. Deleting a branch, sending a message externally, or calling a payment API is a different category — because getting it wrong isn't a quick fix, it's already happened.

**3. Does it ever touch something sensitive — secrets, credentials, personal data?**

You saw this in Chapter 5: `check-env.sh` correctly reports *whether* a variable is set, never *what* it's set to. Any skill that could expose a secret, even accidentally, needs a much closer look before anyone else uses it.

**The honest rule:** the more "yes" answers, the more scrutiny it needs before it goes anywhere near Level 2 or Level 3 sharing from Chapter 8. A text-only skill can move fast. A skill that deletes things, cannot be undone, or touches secrets needs a real, deliberate review — every time, no exceptions, regardless of how confident you feel about it.

### Fixing the cleanup skill, properly

Go back to the near-miss. Here's what actually changed after the review — and why each change matters.

**Before:**
```
Delete any branch matching the pattern `tmp-*`, unless it looks
important.
```

**After:**
```
Find branches matching the pattern `tmp-*` that have had no commits
in the last 30 days. List them for the user, with the last commit
date for each. Do NOT delete anything automatically. Wait for the
user to confirm which branches to delete, then delete only those.
```

Three real changes, each one closing a specific gap:

- **"Unless it looks important" is gone entirely.** That was a judgement call with no real check behind it — replaced with an actual, checkable rule: no commits in 30 days.
- **Deletion is no longer automatic.** The skill now lists candidates and waits for a human to confirm. This is the single most important change — it turns an irreversible action into a reversible decision point, by putting a real person in the loop before anything actually happens.
- **The list includes the evidence** — last commit date for each branch — so the human confirming isn't just trusting the skill blindly. They can actually check the reasoning themselves before agreeing.

Notice the pattern here, because it generalises far beyond this one skill: **when a skill's action can't be undone, the fix is almost never "make the judgement call smarter." It's removing the judgement call from the irreversible step entirely, and putting a human there instead.**

### The pre-distribution safety review

Before any skill moves to Level 2 or Level 3 sharing, run through this. It takes ten minutes and it's the difference between "someone caught this in review" and "someone found out in production."

- [ ] **Can this skill only produce text, or can it act?** If it can act, every remaining question matters more.
- [ ] **If it acts, is the action reversible?** If not, does a real human confirm before it happens — not just "the assistant decided it was fine"?
- [ ] **Does it ever touch secrets, credentials, or personal data?** If yes, confirm it only checks *whether* something exists, never reports the actual value.
- [ ] **Has someone other than the author actually read the instructions?** The same blind-spot problem from Chapter 2 — instructions that feel obvious to the person who wrote them can hide real gaps to anyone else.
- [ ] **Does the description honestly match what the instructions do?** Chapter 2's mismatch check, one more time, right before it ships.
- [ ] **Has it been through the trigger and output testing from Chapter 7** — not just "I tried it twice and it seemed fine"?
- [ ] **Is there a version number and a first changelog entry**, per Chapter 8, so the next change to this skill has a real starting point to compare against?

You'll find the full version of this list, ready to copy, in [`templates/pre-distribution-review-checklist.md`](../templates/pre-distribution-review-checklist.md).

### The full journey, in one checklist

This is the complete arc of this tutorial, condensed. Use it the next time you build a skill from nothing — you won't need to reread all nine chapters, just this.

**Thought process (Chapters 1, 6)**
- [ ] Is this task repeated, well-defined, and recognisable? (Chapter 1)
- [ ] Did you check it against the decision framework — is a skill actually the right tool, or does this belong to a hook, a subagent, or a slash command instead? (Chapter 6)

**Writing (Chapters 2, 3, 4, 5)**
- [ ] Does it follow the standard shape — name, description, instructions? (Chapter 2)
- [ ] Are the instructions specific and checkable, not vague? (Chapter 3)
- [ ] Does the description use the two-sentence shape, tested against real "should" and "should not" phrasings? (Chapter 4)
- [ ] If it needs to check a real, current fact — does it use a real script instead of guessing? (Chapter 5)

**Testing (Chapter 7)**
- [ ] Trigger tests pass, consistently, across repeated runs?
- [ ] Output tests pass your actual rules, on more than one real input?

**Sharing (Chapter 8)**
- [ ] Does it have a real version number?
- [ ] Is there a first changelog entry?
- [ ] Have you honestly picked the right sharing level — not further than it's earned, not held back if it's genuinely ready?

**Safety (Chapter 9)**
- [ ] Run the pre-distribution safety review above, every time it can act on something real.

### Closing the loop

Go back to [`00-the-story.md`](../00-the-story.md) for a second, to the "what done looks like" section from the very start.

You have now built a real skill from nothing. You watched it fail to trigger, and learned exactly why. You gave it a real script instead of a guess. You chose it over a subagent and a hook, for real reasons, not by accident. You tested it properly, versioned it, and know exactly where it belongs on the sharing ladder. And you now know what to check before anything you build goes anywhere near the rest of the company.

That's the whole loop. Everything from here is the same loop, again, in a different domain.

---

## Try it yourself

Run your own skill — the one you've been building since Chapter 3 — through the complete checklist above, top to bottom, honestly. Don't skip a box because you're confident you already know the answer. Write the answer down for each one.

Anything that fails is real, useful information: it's the specific thing standing between where your skill is now and actually being ready to share.

---

## What's still missing

Nothing, for this one skill. You've done the whole thing, start to end.

What you haven't seen yet is this exact process, run by someone else, on a completely different kind of problem — a frontend accessibility check instead of a commit message, a database migration helper instead of an environment check.

The four case studies are that. Same nine chapters. Four different jobs. Read the one closest to your own work first.

**Then, when you're ready:** [AI-Workflows](../../AI-Workflows/README.md) picks up exactly where a single skill's fixed, linear instructions stop being enough — when a task genuinely needs several coordinated pieces of work, not just one focused pass.

---

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Case Studies →](../case-studies/README.md)
