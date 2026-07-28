# Chapter 1 — What Is a Workflow?

← [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of a Workflow](02-anatomy-of-a-workflow.md)

---

## Where you left off

Rahul's `/code-review` skill — the one you watched a teammate use in your very first week — has been working well for months. Then a genuinely big PR lands: 600 lines, touching authentication, a database migration, and three frontend components.

The skill still runs. It reads the diff once, top to bottom, checking every rule in the review standards in a single continuous pass.

You read the output and something bothers you. A real security issue on line 40, and a missing test on line 400, got roughly the same amount of attention — a line or two each — because the skill wasn't *focusing* on anything. It was moving through the diff once, the same way, regardless of what kind of problem it was looking at.

"What if we had five reviewers," you say, "one for security, one for tests, one for style, one for data access, one for docs — all looking at the same diff, at the same time? And then someone checking that what each of them found is actually real, before it goes on the PR?"

Rahul thinks about it. "That's not a skill any more," he says. "That's a workflow."

---

## What you'll learn

1. What a workflow actually is, and how it's genuinely different from a skill.
2. Why a single skill's instructions can't do this job well, no matter how carefully you write them.
3. Real software engineering tasks that are a good fit for a workflow.

---

## The lesson

### Start with what a skill can't do

Go back to what you already know. A skill is one set of instructions, followed in one continuous flow of reasoning, from top to bottom. That's not a limitation someone forgot to fix — it's genuinely what a skill *is*.

Now think about what that means for Rahul's big PR. A skill reading the whole diff once, checking fifteen rules as it goes, is doing exactly what it was built to do. The problem isn't the skill. The problem is that **this particular task isn't a "read it once, check the rules" task any more.** It's five genuinely separate jobs — security review, test coverage, style, data access, documentation — that happen to share the same input.

### The analogy: one generalist vs. five specialists

Imagine handing that 600-line PR to one very capable, very thorough engineer, and asking them to check it for security issues, test coverage, style, data access patterns, and documentation, all by themselves, in one sitting.

They'll do an honest job. But they're one person, moving through the code once, and their attention is necessarily split five ways.

Now imagine instead handing the same PR to five specialists — a security engineer, a QA engineer, a style-conscious reviewer, a data-layer expert, a technical writer — each looking at the *whole diff*, but each only for their one thing. Then a sixth person reads all five reports and checks: does this "security issue" actually hold up? Is this "missing test" really missing, or did I miss where it was added?

**That second version is a workflow.** Several pieces of work, done with real focus, combined — and checked — deliberately.

### A precise definition

**A workflow is a written-down, repeatable plan that coordinates more than one piece of work — deciding exactly what happens at the same time, what happens in order, and what gets checked before it's trusted.**

The important word is *plan*. Not "ask the assistant to do five things and hope it organises itself well" — an actual, fixed structure you designed on purpose, the same way you'd design a script. It runs the same shape every time, whether it's coordinating two pieces of work or twenty.

### Why "just write a longer skill" doesn't work

This is worth sitting with, because it's the natural first instinct.

Could you write one skill with instructions like *"first check security, then check tests, then check style..."*? Technically, yes. But you'd lose the two things that actually made the five-specialist version better:

**You'd lose real parallel focus.** A skill follows one continuous line of reasoning. Even with a section for each rule, it's still one pass, one train of thought, moving through the code once. Genuinely running five *separate*, focused looks at the same diff — the way five different specialists would — needs five separate pieces of work, not five paragraphs in one prompt.

**You'd lose the check.** A skill trusts its own single pass. There's no natural place in "one set of instructions, followed once" for a second, independent look that catches the first pass getting something wrong. You'll build exactly that second look in [Chapter 5](05-fan-out-and-verify.md), and it genuinely needs a workflow's structure to work — you can't bolt a real independent check onto a single skill's single pass.

### Real workflow candidates, from a software team

| What's happening today | Why a skill alone falls short | The workflow instead |
|---|---|---|
| One reviewer reads a big diff once, checking everything | Attention is split across unrelated concerns | Five focused reviewers, run at once, then verified |
| Checking a component works on desktop, tablet, and mobile, one at a time | Each check is genuinely independent — no reason to do them in sequence | Three checks running in parallel, combined into one report |
| Scaffolding, testing, then documenting a new endpoint, one endpoint at a time | Different endpoints don't need to wait for each other to *start*, even though each one has fixed stages | A pipeline: stage-by-stage per endpoint, several endpoints moving through it at once |
| Generating test cases from one angle, and hoping it's thorough | One pass tends to reuse the same blind spots | Several independent testing "lenses," then a check that the coverage is real, not just plausible-sounding |

Notice the pattern across all four: **the task has real, separable parts, or real stages, or needs a genuine second opinion.** That's the actual test for "is this a workflow?" — and you'll refine it further once you've seen what a workflow costs, later in this tutorial.

---

## Try it yourself

1. Think of a task on your team that currently gets done as one continuous pass — by a person, or by a single skill — even though it's really checking several different, unrelated things.
2. Write down, honestly: if you split it into separate, focused pieces of work, would each piece actually do a *better* job — or would splitting it just add overhead for no real benefit? Not everything should be a workflow, and this question is how you find out early.
3. If it passed that test, name the pieces. Are they genuinely independent, or does one need to finish before another can start? Keep this — you'll need it in [Chapter 4](04-parallel-vs-pipeline.md).

---

## What's still missing

You now know *why* Rahul's review needs to become a workflow, in plain words. You still don't know what one actually looks like — the real shape, the real script, the real words inside it.

That's the next chapter.

---

← [Learning path](../learning-path.md) · Next: [Chapter 2 — Anatomy of a Workflow](02-anatomy-of-a-workflow.md)
