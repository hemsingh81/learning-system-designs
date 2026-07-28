# The Story — Read This First

← [Back to README](README.md) · Next: [The Learning Path](learning-path.md)

---

## Why a story

You could read a list of facts about AI Skills. You would forget most of it in a week.

Instead, this whole tutorial follows **one journey** — yours. Every chapter has a small problem, a fix, and a new problem the fix creates. That is not a teaching trick. It is how you actually learn to build anything real: you try it, it breaks in a specific way, you learn why, you fix it properly.

By the end, you will have built and shared a real skill with your team. Not read about one. Built one.

---

## The setup

You have just joined **Kestrel Software** as a backend engineer. Two years of experience. You are good at your job. You have never built an AI Skill before, and you are not totally sure what one even is.

### The people

| Who | Role | Why they matter to this story |
|---|---|---|
| **You** | Backend engineer, new joiner | The one learning this, start to finish |
| **Rahul** | Your tech lead | Asks the questions that push the story forward |
| **Divya** | Frontend engineer | Builds the frontend skill in the case studies |
| **Vikram** | Senior backend engineer | Builds the backend skill, sometimes explains the harder parts |
| **Ananya** | QA lead | Builds the QA skill, cares a lot about false positives |

### The team's problem

Kestrel's engineers do the same handful of things every single day, by hand:

- Write commit messages that half-follow the team's format, half don't.
- Ask a teammate "does this PR follow our review checklist?" instead of checking it themselves.
- Explain the same onboarding steps to every new hire.
- Copy-paste the same debugging questions into Claude, worded slightly differently each time.

None of this is hard. All of it is repeated. And repeated-but-not-automated is exactly where an AI Skill earns its keep.

In your first week, you watch a teammate type `/code-review` in the terminal. Claude Code responds instantly with a structured review, following rules specific to Kestrel's codebase — rules you have never seen written down anywhere.

"What was that?" you ask.

"A skill," they say. "Someone on the platform team built it two months ago. Everyone uses it now."

You want to know how to build one. This is that story.

---

## What "done" looks like

By the last chapter, you will have:

1. Built a small, real skill from nothing — the same one, refined chapter by chapter.
2. Learned why it did not trigger the first three times you tried it, and fixed that properly.
3. Given it to Divya, Vikram, and Ananya, and watched each of them adapt the same process to their own domain.
4. Learned what to check before a skill goes anywhere near the whole company, not just your team.

The four case studies at the end are not new material. They are the same nine chapters, applied by four different people, in four different corners of the codebase. Once you see the pattern repeat four times, it stops being "a thing you read about" and becomes "a thing you know how to do."

---

## The chapter arc, in one table

Keep coming back to this table. It is the whole tutorial on one page.

| Ch | The problem | What you learn | What it creates |
|---|---|---|---|
| [1](tutorial/01-what-is-a-skill.md) | You don't know what a skill actually is | The mental model, and real Kestrel-style use cases | The vocabulary to keep going |
| [2](tutorial/02-anatomy-of-a-skill.md) | You open a real skill folder and can't read it | The shape every skill has | You can now read any skill |
| [3](tutorial/03-your-first-skill.md) | You want to build one, and don't know where to start | Build a tiny real skill, badly, then correctly | Your first working skill |
| [4](tutorial/04-writing-trigger-descriptions.md) | Your skill only triggers sometimes | Why, and the fix | A skill that triggers reliably |
| [5](tutorial/05-tools-and-scripts.md) | Prose instructions aren't enough for this task | Bundling real scripts into a skill | A skill that *does* something, not just *says* something |
| [6](tutorial/06-skills-vs-other-tools.md) | Rahul asks "why not a subagent? why not a hook?" | The decision framework | You stop guessing which tool to reach for |
| [7](tutorial/07-testing-and-iterating.md) | You're about to share this — is it actually reliable? | A real testing discipline | Confidence, backed by evidence |
| [8](tutorial/08-packaging-and-sharing.md) | Divya wants to use your skill too | Packaging, versioning, three levels of sharing | A skill your whole team can use |
| [9](tutorial/09-governance-and-capstone.md) | A teammate's skill almost does something risky | Safety review, and the full decision checklist | The judgement to know when a skill is ready |

---

## How to read this repo

1. Read the chapters in order the first time. They build on each other — chapter 4 assumes you did chapter 3.
2. Each chapter ends with **"What's still missing"** — the exact problem the next chapter solves. Don't skip it; it's the thread.
3. After chapter 9, read the [case studies](case-studies/) — pick the one closest to your own team, or read all four to see the pattern repeat.
4. Keep [`templates/`](templates/SKILL-template.md) open in a second tab once you start building for real.

---

← [Back to README](README.md) · Next: [The Learning Path](learning-path.md)
