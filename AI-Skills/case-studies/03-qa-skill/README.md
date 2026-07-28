# Case Study 3 — QA: Test Case Generation

← [Backend](../02-backend-skill/README.md) · [All case studies](../README.md) · Next: [Code Review — Team Standards](../04-code-review-skill/README.md)

Built by **Ananya**, QA lead at Kestrel.

---

## The problem

Every new feature needs test cases written from its user story — the happy path, obviously, but also the edge cases people forget under deadline pressure: empty input, the maximum allowed value, what happens on a duplicate submission, what happens when a dependency is down.

Ananya spends a real chunk of every sprint just generating this list by hand, from scratch, for every story.

---

## The thought process

Through [Chapter 6](../../tutorial/06-skills-vs-other-tools.md)'s framework: not a fixed rule (every story is different), doesn't need a separate workspace (the user story is right there), and it's exactly the kind of repeated, differently-phrased request a skill is built for — "write test cases for this," "what edge cases am I missing," "generate a test plan for this story."

Skill. But this case study's real lesson isn't the trigger decision — it's what Ananya discovered about a different kind of mistake, one that doesn't show up in Chapter 4's trigger testing at all.

---

## The skill

```markdown
---
name: kestrel-test-case-gen
description: Generates test cases from a user story, covering the
  happy path and realistic edge cases. Use when the user asks to
  write test cases, generate a test plan, or asks what edge cases
  they might be missing for a feature. Does NOT write the actual
  test CODE — only the test cases and scenarios, in plain language,
  for a human to implement or review.
version: 1.1.0
---

You are generating test cases from a user story for Kestrel's QA
process.

For the user story provided, generate test cases covering:

1. HAPPY PATH — the feature working exactly as described.
2. EMPTY / MISSING INPUT — what happens when required input isn't
   provided.
3. BOUNDARY VALUES — the smallest and largest values the system is
   meant to accept, and one value just outside that range.
4. DUPLICATE / REPEATED ACTION — what should happen if the same
   action is submitted twice (this has caught real bugs before —
   never skip this category).
5. DEPENDENCY FAILURE — what should happen if something this
   feature depends on (a database, an external API) is unavailable.

For EACH test case, state:
- The exact input or situation
- The EXPECTED result — specific enough that a real person could
  check pass or fail against it. "It should work correctly" is NOT
  an acceptable expected result. "The form shows an error: 'Email is
  required'" is.

If the user story doesn't say what SHOULD happen in a given edge
case, do not invent an answer. Say clearly: "The story doesn't
specify this — needs a decision before this can be tested," and
list it as an open question instead of a test case.
```

---

## What went wrong the first time — and why it mattered more here

Ananya's first draft didn't include the "expected result specific enough to check pass or fail against" rule, or the instruction not to invent an answer for unspecified behaviour.

The early output looked complete. It had a line for every category — happy path, empty input, boundary values, duplicates, dependency failure. All five boxes ticked. It looked like real, thorough coverage.

But several of the "expected results" were things like *"the system should handle this gracefully"* — which isn't actually a testable statement. Nobody could look at that line and say pass or fail, because it doesn't say what "gracefully" means. And for a genuinely unspecified edge case, the skill had quietly guessed at a reasonable-sounding behaviour instead of flagging that nobody had actually decided what should happen.

This is the specific danger this case study is built around, and it's different from anything in the earlier chapters. **A test case list that looks complete but isn't testable is worse than a short list that's honestly incomplete.** A short list gets noticed and finished by hand. A long list of vague-sounding coverage gets trusted, checked off, and shipped — and the actual gap only surfaces later, in production, when a real user hits the exact case nobody actually pinned down.

Compare this to your commit-message skill, back in Chapter 7: there, missing a trigger was mildly annoying — you'd just ask again. Here, a **false sense of coverage** is the expensive mistake, not a missed one. Ananya's fix — every expected result must be specific enough to check, and any genuinely unspecified case gets flagged as an open question instead of a guess — directly targets that specific, more expensive failure mode.

---

## How it was tested

Trigger tests, as usual:

| Should trigger | Result |
|---|---|
| "write test cases for this story" | ✅ |
| "what edge cases am I missing here" | ✅ |
| "generate a test plan for this feature" | ✅ |
| "help me think through how to test this" | ✅ |

| Should NOT trigger | Result |
|---|---|
| "write the actual test code for this" (code, not cases — explicitly excluded) | ✅ correctly ignored |
| "is this feature done?" (a status question, not a test request) | ✅ correctly ignored |

But the output testing here needed an extra layer beyond Chapter 7's usual line-by-line rule check: Ananya specifically checked **every "expected result" line for whether a real person, with no other context, could mark it pass or fail.** Any line that couldn't — "handles it correctly," "works as expected," "shows an appropriate message" — was treated as a failure of the skill, not just a stylistic nitpick. That extra check is the direct fix for the false-coverage problem above, and it's now a permanent part of how she reviews any change to this skill.

---

## Where it sits on the sharing ladder

**Level 2 — Project**, for now. Ananya suspects this one could genuinely reach Level 3 eventually — the categories (empty input, boundaries, duplicates, dependency failure) aren't Kestrel-specific, they're just good testing practice. But per [Chapter 8](../../tutorial/08-packaging-and-sharing.md)'s honest rule, she's holding it at Level 2 until at least two other teams have actually asked for it unmodified — not before.

---

← [Backend](../02-backend-skill/README.md) · [All case studies](../README.md) · Next: [Code Review — Team Standards](../04-code-review-skill/README.md)
