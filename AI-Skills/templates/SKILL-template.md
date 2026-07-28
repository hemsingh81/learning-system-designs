# SKILL.md Template

← [Back to README](../README.md) · See it explained: [Chapter 2 — Anatomy of a Skill](../tutorial/02-anatomy-of-a-skill.md)

Copy the block below to start a new skill. Every `[LIKE THIS]` is a placeholder — replace it, don't leave it in. The comments explain what belongs in each spot; delete them once you've filled the section in for real.

---

```markdown
---
name: [your-skill-name-in-lowercase-with-hyphens]
version: 1.0.0
description: [WHAT it does, one sentence]. Use when [WHEN to reach for
  it — describe the CATEGORY of request, in at least 2-3 different
  real phrasings, not just one exact quote]. Does NOT cover
  [ANYTHING NEARBY THAT SOUNDS SIMILAR BUT ISN'T THIS SKILL — only
  include this sentence if something genuinely overlaps].
---

[ONE SENTENCE OF CONTEXT: what this skill is for, and who it's for.]

[THE ACTUAL RULES. Be specific and checkable, not vague. "Follow our
format" is vague. "Use type(scope): description, under 72 characters,
imperative mood" is checkable. Write it the way you'd explain it to a
new team member who has never seen this before and can't ask you a
follow-up question.]

[IF THIS SKILL NEEDS TO CHECK A REAL, CURRENT FACT — not just reason
from what's already in the conversation — tell it to run a real
script instead of guessing. Example:
"Run scripts/check.sh. Do NOT guess or assume — always run the
script and report its actual output."]

[WHAT TO OUTPUT, and in what shape. Be explicit if the shape matters:
"output only the commit message, no explanation" is very different
from leaving that unstated.]
```

---

## The checklist to run before you consider this "done"

Pulled straight from [Chapter 9](../tutorial/09-governance-and-capstone.md) — the short version. Use the full checklist there when you're about to share something, not just build it for yourself.

- [ ] Is this task repeated, well-defined, and recognisable? ([Chapter 1](../tutorial/01-what-is-a-skill.md))
- [ ] Did you check it against the decision framework — skill, or actually a hook / subagent / slash command? ([Chapter 6](../tutorial/06-skills-vs-other-tools.md))
- [ ] Are the instructions specific and checkable, not vague? ([Chapter 3](../tutorial/03-your-first-skill.md))
- [ ] Does the description use the two-sentence shape, tested against real "should" and "should not" phrasings? ([Chapter 4](../tutorial/04-writing-trigger-descriptions.md))
- [ ] If it needs to check something real, does it run a real script instead of guessing? ([Chapter 5](../tutorial/05-tools-and-scripts.md))
- [ ] Has it been through trigger and output testing, more than once? ([Chapter 7](../tutorial/07-testing-and-iterating.md))
- [ ] Does it have a version number and a first changelog entry? ([Chapter 8](../tutorial/08-packaging-and-sharing.md))
- [ ] If it can act on something real — is that action reversible, or does a human confirm first? ([Chapter 9](../tutorial/09-governance-and-capstone.md))

---

## A filled-in example, for reference

This is the commit-message skill built across Chapters 3 and 4, shown complete, so you can see the template actually filled in rather than just described.

```markdown
---
name: kestrel-commit-message
version: 1.1.0
description: Writes a commit message following Kestrel's format
  (type(scope): description), based on the actual code changes. Use
  when the user asks you to write, draft, or describe a commit
  message, or asks to commit their changes. Does NOT cover
  reverting, squashing, or amending existing commits.
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

---

← [Back to README](../README.md)
