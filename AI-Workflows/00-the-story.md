# The Story — Read This First

← [Back to README](README.md) · Next: [The Learning Path](learning-path.md)

---

## If you're arriving from AI-Skills

This is the same journey, continued. Same you, same company, same cast. If you haven't been through [`AI-Skills`](../AI-Skills/README.md) yet, this tutorial will still make sense — but a few things will land harder if you have. Skills are the first rung of a ladder. This is the second.

If you have been through it: welcome back. You'll recognise Rahul's `/code-review` skill in a few pages. It's about to grow up.

---

## Where you left off

Your commit-message skill works. Your environment-check skill works. Divya's accessibility skill, Vikram's scaffolding skill, Ananya's test-case skill, Rahul's code-review skill — all shipped, all used daily across Kestrel Software.

Then a genuinely bigger PR lands. Six hundred lines, touching authentication, a database migration, and three frontend components. Rahul asks Kestrel's assistant to review it using his code-review skill.

It works. It's just slow, and shallow in a way that bothers you once you look closely. The skill reads through the diff once, top to bottom, checking every rule in `review-standards.md` in a single pass. A security issue on line 40 and a missing test on line 400 both get roughly the same amount of attention, because the skill is doing one linear pass, not really *focusing* on anything.

You say what you're both thinking: "What if we had five different reviewers — one for security, one for tests, one for style, one for data access, one for docs — all looking at the same diff, at the same time, and then someone checking that what each of them found is actually real before it goes on the PR?"

Rahul goes quiet for a second. "That's not a skill anymore," he says. "That's a workflow."

---

## What you'll learn

A skill is one set of instructions, picked up when relevant, followed in one continuous flow of reasoning. That's genuinely all it can be — and for most day-to-day tasks, that's plenty.

A **workflow** is different. It's a real, deterministic plan — written down as an actual script, not prose — that coordinates *multiple* pieces of work: some running at the same time, some running one after another, some checking each other's findings before anything gets reported. You write the plan once. The plan runs the same way every time, whether it's coordinating two pieces of work or twenty.

This tutorial teaches you to build that.

---

## The setup

### The people

Same cast as before, doing the same jobs, now hitting problems a skill alone can't solve.

| Who | Role | Their problem this time |
|---|---|---|
| **You** | Backend engineer | Learning workflows, start to finish |
| **Rahul** | Tech lead | Wants the code-review skill to become a proper multi-angle review |
| **Divya** | Frontend engineer | Needs to check a component across several screen sizes at once |
| **Vikram** | Backend engineer | Needs to scaffold, test, and document several endpoints without doing it one at a time by hand |
| **Ananya** | QA lead | Needs test cases generated from several angles, then checked for real coverage — not just the appearance of it |

### The actual problem, stated plainly

A skill is brilliant at one thing: recognising *when* to help, and then following *one* clear set of instructions.

It's genuinely bad at a different thing: doing several *independent* pieces of work at once, or doing work in stages where each stage needs the last one finished first, or having one piece of work double-check another's findings before anything gets trusted.

That's not a flaw in skills. It's just not what they're for. This tutorial is about the tool that's actually built for that job.

---

## What "done" looks like

By the end, you will have:

1. Built a real workflow from nothing — the same one, refined chapter by chapter, exactly like your first skill was.
2. Learned the single most important decision in workflow design: when work should run **in parallel** and when it should run as a **pipeline** — and why picking wrong quietly wastes time or quietly produces worse results.
3. Built a "fan out, then verify" review — several independent checks, then a second pass that catches the ones that sounded right but weren't.
4. Watched Rahul's code-review *skill* become one **stage** inside a bigger *workflow* — the actual, concrete link between the tool you already know and the one you're about to learn.
5. Learned the new kind of risk a workflow introduces that a skill never could — cost and runaway scale — and how to govern it properly before sharing one.

---

## The chapter arc, in one table

| Ch | The problem | What you learn | What it creates |
|---|---|---|---|
| [1](tutorial/01-what-is-a-workflow.md) | One reviewer, one pass, no real focus | What a workflow actually is, and why a skill alone can't do this | The vocabulary to keep going |
| [2](tutorial/02-anatomy-of-a-workflow.md) | You look at a real workflow script and can't read it | The shape every workflow has | You can now read any workflow |
| [3](tutorial/03-your-first-workflow.md) | You build one, and it doesn't actually save any time | Build a tiny real workflow, badly, then correctly | Your first working workflow |
| [4](tutorial/04-parallel-vs-pipeline.md) | Your workflow waits for everything before it starts anything | Parallel vs. pipeline — the central decision | A workflow that's actually fast |
| [5](tutorial/05-fan-out-and-verify.md) | Independent checks find things that turn out to be wrong | Fan-out review, and verifying findings before trusting them | A workflow you can actually trust |
| [6](tutorial/06-workflows-vs-other-tools.md) | Rahul asks why this isn't just five skills | The decision framework, and where Agents fit next | You stop guessing which tool to reach for |
| [7](tutorial/07-testing-and-iterating.md) | You're about to share this — does it actually work at scale? | A real testing discipline for orchestration | Confidence, backed by evidence |
| [8](tutorial/08-packaging-and-sharing.md) | Divya wants this pattern for her own check | Packaging, versioning, and why workflows need explicit consent to run | A workflow your team can use safely |
| [9](tutorial/09-governance-and-capstone.md) | Someone's workflow quietly spawns forty agents on a small PR | Cost governance — the risk unique to workflows | The judgement to know when a workflow is ready |

---

## How to read this repo

Same as before. Read the chapters in order — each depends on the last. Each ends with **"What's still missing,"** the exact gap the next chapter fills. After chapter 9, read the [case studies](case-studies/) — four workflows, four teams, each one deliberately using a different orchestration shape so you see the real range.

---

← [Back to README](README.md) · Next: [The Learning Path](learning-path.md)
