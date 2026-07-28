# Case Study 4 — Code Review: Team Standards

← [QA](../03-qa-skill/README.md) · [All case studies](../README.md) · [Back to README](../../README.md)

Built by **Rahul**, tech lead at Kestrel. This is the `/code-review` skill you watched a teammate use in your very first week — [`00-the-story.md`](../../00-the-story.md), the moment this whole tutorial started.

---

## The problem

Kestrel has a real, written code review standard. Error handling should follow specific patterns. Public functions need doc comments. Database queries need to go through the repository layer, never called directly from a route or a component. Nothing here is a secret — it's written down in a doc that, honestly, most engineers read once, during onboarding, and never open again.

Reviews still miss things. Not because reviewers don't know the standard — because remembering fifteen rules, consistently, on every single PR, for every engineer, every time, is genuinely hard. Different reviewers catch different things. The same mistake gets caught by one reviewer and missed by another, depending on who happened to review that particular PR.

---

## The thought process

This case study is different from the first three in one important way: it's not really about deciding skill-vs-something-else. Rahul already knew this needed to be a skill — the whole reason he wants it is exactly the property a skill has that a person doesn't: **applying the same rules, the same way, every single time, regardless of who's asking or how busy they are.**

The real thinking here went into something [Chapter 6](../../tutorial/06-skills-vs-other-tools.md) doesn't fully cover: **how do you keep a skill's rules in sync with the actual, evolving team standard**, without editing a wall of prose inside the skill file every time the standard changes?

---

## The skill

Rahul's answer: separate the skill's *instructions* from the *actual rules*, the same way your commit-message skill's format could, in principle, live in a separate file instead of being typed directly into the instructions. Here, with fifteen real rules instead of six, that separation stops being optional.

The full pair also lives at [`SKILL.md`](SKILL.md) and [`review-standards.md`](review-standards.md) in this folder — copy both into your own skills directory to use it as-is.

```markdown
---
name: kestrel-code-review
version: 2.1.0
description: Reviews a pull request against Kestrel's written code
  review standards — error handling, documentation, data access
  patterns, and testing requirements. Use when the user asks to
  review a PR, check a diff against our standards, or asks if their
  code follows our conventions. Does NOT approve or merge anything —
  only reports findings for a human to act on.
---

You are reviewing a pull request against Kestrel's code review
standards, defined in review-standards.md (bundled with this skill).

Read review-standards.md FIRST, in full, before reviewing any code.
Do not review from memory or general best practice — this skill
exists specifically because Kestrel's standards are sometimes
stricter, and sometimes different, from general best practice.

For each rule in review-standards.md, check the diff against it. For
each finding:
- Quote the exact line
- Name the SPECIFIC rule from review-standards.md that applies —
  not a general principle, the actual numbered rule
- Explain the fix

Group findings by severity: MUST FIX (breaks a hard rule), SHOULD
FIX (a real but minor issue), CONSIDER (a suggestion, not a rule).

If review-standards.md has been updated more recently than this
skill's own version number below, tell the user the standards may
have changed since this skill was last reviewed, and to double check
anything unusual.

Never approve, merge, or claim a PR is "ready" — only report
findings. The decision belongs to a human reviewer, always.
```

```markdown
# review-standards.md (bundled reference — the actual policy)

## 1. Error handling
Every external call (database, API, file system) must be wrapped
with explicit error handling. Silent failures are not acceptable —
every caught error must be logged or surfaced, not swallowed.

## 2. Documentation
Every exported function needs a doc comment stating what it does,
its parameters, and what it returns. Internal (non-exported)
functions do not require this.

## 3. Data access
Database queries must go through the repository layer. Never query
the database directly from a route handler or a frontend component.

## 4. Testing
Every new function with a conditional (an if/else, a switch) needs
at least one test per branch. A function with no conditionals needs
at least one happy-path test.

## 5. Naming
Boolean variables and functions start with is/has/can/should
(isValid, hasPermission) — never a bare noun or verb.

[... continues with the team's full, real list ...]
```

---

## What went wrong the first time

Rahul's very first version had all fifteen rules typed directly into the skill's instructions — no separate `review-standards.md` at all. It worked. For about three weeks.

Then the team changed rule 3 — data access — to allow a specific, narrow exception for a caching layer that had just been introduced. Updating the rule meant editing the skill's instructions directly, which meant re-testing the whole skill's triggering and output behaviour again, for a change that had nothing to do with triggering or format — only the underlying policy.

Worse: two engineers had, in the meantime, copied the skill into their own personal setups to experiment with tweaks. When the standard changed, those copies didn't get the update, and for a few weeks there were three different versions of "the real rule" floating around, quietly disagreeing with each other.

Splitting the rules into their own file fixed both problems at once. The **instructions** — how to read the rules, how to check them, how to report findings — rarely change, so the skill itself stays stable. The **rules** — the actual policy — can be updated on their own, by whoever owns that decision (often not the same person who wrote the skill), without touching the skill's tested triggering or output behaviour at all. And because it's one real file with one real owner, there's no more room for three silently-different copies to drift apart.

This is the direct, practical version of something [Chapter 8](../../tutorial/08-packaging-and-sharing.md) only touched on briefly: **a shared skill needs one real home.** For a skill like this one, that means the *policy* needs one real home too — not just the skill file itself.

---

## How it was tested

| Should trigger | Result |
|---|---|
| "review this PR" | ✅ |
| "check this diff against our standards" | ✅ |
| "does this follow our conventions?" | ✅ |
| "can you review my changes before I request review?" | ✅ |

| Should NOT trigger | Result |
|---|---|
| "approve this PR" (the skill explicitly never approves — this should surface that boundary, not silently act) | ✅ correctly declines to approve, reports findings instead |
| "what are our code review standards?" (a question about the doc, not a request to apply it) | ✅ correctly ignored, or answered directly without invoking the review flow |

Output testing included a deliberate check specific to this skill: Rahul updated `review-standards.md` alone, without touching the skill's instructions, and confirmed the very next review correctly picked up the new rule. That's the exact property the redesign was built to guarantee, so it's the one test that matters most here — more than any single trigger phrasing.

---

## Where it sits on the sharing ladder

**Level 2 — Project**, checked into the main repo, where every engineer at Kestrel already works. This is the skill your very first week started with — and now you know exactly how it's built, why it's shaped the way it is, and what almost went wrong before it got there.

---

## References & assets

- **[`SKILL.md`](SKILL.md)** + **[`review-standards.md`](review-standards.md)** — the complete, real files, kept deliberately separate. Copy both into your own skills directory to use it exactly as built here.
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, including the staleness check between the policy file and the skill's own version number.
- **Chapters used:** [Chapter 6](../../tutorial/06-skills-vs-other-tools.md), [Chapter 7](../../tutorial/07-testing-and-iterating.md), [Chapter 8](../../tutorial/08-packaging-and-sharing.md) (one real home for shared state), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).

---

## You've now read all four

Same nine chapters. Four different jobs. If you've read all four case studies, you've seen the process bend to fit a judgement-heavy check (frontend), a structural code generator (backend), a false-coverage risk (QA), and a policy that has to stay consistent and stay in sync with real, ongoing change (code review).

That's the actual range of problems skills are good for. Go build one for something real on your own team.

**Curious where this specific skill goes next?** This exact `/code-review` skill becomes one stage inside a bigger review in [AI-Workflows Case Study 4](../../../AI-Workflows/case-studies/04-code-review-workflow/README.md) — and that workflow's fixed five angles later become one agent's adaptive choice in [AI-Agents Case Study 4](../../../AI-Agents/case-studies/04-code-review-agent/README.md). Nothing you built here gets thrown away.

---

← [QA](../03-qa-skill/README.md) · [All case studies](../README.md) · [Back to README](../../README.md)
