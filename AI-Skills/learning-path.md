# The Learning Path

← [The Story](00-the-story.md) · [Back to README](README.md)

Nine chapters. Read them in order — each one needs the last. Then four case studies, which you can read in any order, or skip to the one closest to your own job.

---

## The shape of every chapter

Every chapter has the same five parts, so you always know where you are:

1. **Where you left off** — one paragraph, so you can start any chapter cold.
2. **What you'll learn** — two or three plain sentences.
3. **The lesson** — explained slowly, with analogies and examples.
4. **Try it yourself** — a real, small exercise. Not "read and nod along."
5. **What's still missing** — the exact gap the next chapter fills.

---

## The full path

| # | Chapter | Time | Where the story is | File |
|---|---|---|---|---|
| 1 | What Is a Skill? | 20 min | You watch a teammate use one and don't know what it was | [`tutorial/01-what-is-a-skill.md`](tutorial/01-what-is-a-skill.md) |
| 2 | Anatomy of a Skill | 25 min | You open a real skill folder and can't read it yet | [`tutorial/02-anatomy-of-a-skill.md`](tutorial/02-anatomy-of-a-skill.md) |
| 3 | Your First Skill | 40 min | You build one, badly, then fix it | [`tutorial/03-your-first-skill.md`](tutorial/03-your-first-skill.md) |
| 4 | Writing Trigger Descriptions | 35 min | Your skill only works sometimes | [`tutorial/04-writing-trigger-descriptions.md`](tutorial/04-writing-trigger-descriptions.md) |
| 5 | Tools and Scripts | 30 min | Instructions alone aren't enough for this job | [`tutorial/05-tools-and-scripts.md`](tutorial/05-tools-and-scripts.md) |
| 6 | Skills vs. Other Tools | 30 min | Rahul asks why this isn't a subagent instead | [`tutorial/06-skills-vs-other-tools.md`](tutorial/06-skills-vs-other-tools.md) |
| 7 | Testing and Iterating | 30 min | You're about to share this — is it actually reliable? | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) |
| 8 | Packaging and Sharing | 35 min | Divya wants your skill for her own team | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) |
| 9 | Governance and Capstone | 30 min | A teammate's skill almost does something risky | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) |

**Total: about 4.5 hours**, including every exercise.

---

## Chapter details

### Chapter 1 — What Is a Skill?
**File:** [`tutorial/01-what-is-a-skill.md`](tutorial/01-what-is-a-skill.md)

**You'll be able to:**
1. Explain what a skill is, using a plain analogy — not jargon.
2. Name three things your own team does repeatedly that a skill could handle.
3. Tell the difference between "a skill" and "just a good prompt."

**You'll try:** Watch (or imagine) an AI assistant handle one of your team's repeated tasks. Write down, in one sentence, what made it different from a normal question.

---

### Chapter 2 — Anatomy of a Skill
**File:** [`tutorial/02-anatomy-of-a-skill.md`](tutorial/02-anatomy-of-a-skill.md)

**You'll be able to:**
1. Read any skill's file and understand every part of it.
2. Explain what the "name" and "description" fields actually do.
3. Say why the instructions inside a skill are different from a normal chat message.

**You'll try:** Read a real skill file (one is included) and, without looking at the answer, guess what request would trigger it.

---

### Chapter 3 — Your First Skill
**File:** [`tutorial/03-your-first-skill.md`](tutorial/03-your-first-skill.md)

**You'll be able to:**
1. Create a working skill from an empty folder.
2. Test that it triggers on a request it should handle.
3. Notice, and name, the first mistake almost everyone makes.

**You'll try:** Build a tiny commit-message skill for your own team's conventions. Run it. Watch it fail once, on purpose, before you fix it.

---

### Chapter 4 — Writing Trigger Descriptions
**File:** [`tutorial/04-writing-trigger-descriptions.md`](tutorial/04-writing-trigger-descriptions.md)

**You'll be able to:**
1. Explain why a skill triggers on some requests and not others.
2. Spot a vague description and say exactly why it's vague.
3. Rewrite a bad description into a good one.

**You'll try:** Take your Chapter 3 skill's description and test it against five different phrasings of the same request. Find the ones that fail.

---

### Chapter 5 — Tools and Scripts
**File:** [`tutorial/05-tools-and-scripts.md`](tutorial/05-tools-and-scripts.md)

**You'll be able to:**
1. Decide when a skill needs a bundled script instead of just instructions.
2. Reference a script from inside a skill correctly.
3. Explain the risk of a skill that can run arbitrary commands.

**You'll try:** Add one small, real script to your Chapter 3 skill — something instructions alone couldn't reliably do.

---

### Chapter 6 — Skills vs. Other Tools
**File:** [`tutorial/06-skills-vs-other-tools.md`](tutorial/06-skills-vs-other-tools.md)

**You'll be able to:**
1. Choose correctly between a skill, a slash command, a subagent, and a hook.
2. Explain the one-sentence mental model for each.
3. Say why using the wrong one causes a specific, predictable problem.

**You'll try:** Take three of your own team's repeated tasks. Assign each one to the right tool, and say why.

---

### Chapter 7 — Testing and Iterating
**File:** [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md)

**You'll be able to:**
1. Write a small test set for a skill's triggering behaviour.
2. Tell a false positive apart from a false negative, and know which is worse for your case.
3. Decide when a skill is "good enough to share" versus "needs another pass."

**You'll try:** Write 10 test phrasings for your skill — 5 that should trigger it, 5 that should not. Run them. Fix what fails.

---

### Chapter 8 — Packaging and Sharing
**File:** [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md)

**You'll be able to:**
1. Version a skill so a breaking change doesn't surprise anyone using it.
2. Explain the three levels of sharing: just you, your project, your whole company.
3. Write a short changelog entry for a skill update.

**You'll try:** Move your skill from "just on your machine" to "shared with your project," and write its first changelog entry.

---

### Chapter 9 — Governance and Capstone
**File:** [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md)

**You'll be able to:**
1. Spot the specific risks a skill introduces that a normal script doesn't.
2. Run a pre-distribution safety review on a skill.
3. Use the full "is this ready?" checklist from thought process to sharing.

**You'll try:** Run the pre-distribution checklist against your own skill. Fix whatever it flags.

---

## Then, the case studies

Same nine chapters. Four different people, four different jobs, four different skills.

- [Frontend — accessibility review](case-studies/01-frontend-skill/README.md) — Divya
- [Backend — API endpoint scaffolding](case-studies/02-backend-skill/README.md) — Vikram
- [QA — test case generation](case-studies/03-qa-skill/README.md) — Ananya
- [Code review — team standards](case-studies/04-code-review-skill/README.md) — Rahul

Read the one closest to your own role first. The pattern is what matters — once you've seen it work in a domain you know, it's obvious how to apply it to your own.

---

← [The Story](00-the-story.md) · [Back to README](README.md) · Start: [Chapter 1 →](tutorial/01-what-is-a-skill.md)
