# Case Study 4 — Code Review: A Skill Inside a Workflow

← [Case Study 3 — QA](../03-qa-workflow/README.md) · [All case studies](../README.md)

Built by **Rahul**, tech lead at Kestrel. Pattern: **a skill running as one stage inside a workflow.**

---

## The problem

This is the story you've been following since [`00-the-story.md`](../../00-the-story.md). Rahul's original AI-Skills [`/code-review` skill](../../../AI-Skills/case-studies/04-code-review-skill/README.md) does one focused thing well: it applies the team's review standards, one pass, to a diff. That's exactly what a skill should do — and it's genuinely useful, most of the time.

It broke down on the 600-line PR that opens this tutorial's story, not because the skill was badly written, but because the *task* had stopped being one focused thing. A large PR genuinely needs several independent angles of attention — security, tests, style, data access, docs. A single linear pass, however well-written, has to spread its attention across all of them at once, instead of genuinely focusing on each.

---

## The thought process

This is the whole arc of Chapters 1, 4, and 5. This case study shows the **complete, finished shape** in one place. It also shows one thing none of the tutorial chapters showed explicitly: **Rahul's original skill didn't get thrown away.** It became one of the five angles.

Specifically, the "style" angle — the exact review his `/code-review` skill already did well — is now just one call to that same skill. It runs as a single stage inside a bigger workflow, sitting alongside four new focused angles it never covered on its own.

This is the direct, concrete answer to the question this whole tutorial exists to answer: **what happens to your skills once you start building workflows?** Nothing is wasted. A well-built skill doesn't get replaced by a workflow — it gets promoted into being one trustworthy piece of a bigger one.

---

## The workflow

The full, ready-to-run script also lives at [`workflow.md`](workflow.md) in this folder.

```javascript
meta = {
  name: "pr-five-angle-review",
  version: "1.1.0",
  description: "Reviews a PR from 5 angles (security, tests, style, data " +
    "access, docs), then independently verifies each finding before it " +
    "reaches the PR. The style angle reuses the team's existing " +
    "/code-review skill.",
  phases: [
    { title: "Review" },
    { title: "Verify" }
  ]
}

phase("Review")

findings = parallel([
  () => agent("Review this diff for SECURITY issues only: " + diff),
  () => agent("Review this diff for missing TEST coverage only: " + diff),

  // The STYLE angle is not a new prompt written for this workflow — it's
  // a call to the team's existing, already-tested /code-review skill.
  // The skill's own trigger description doesn't matter here; the
  // workflow invokes it directly and deliberately, as one stage.
  () => run_skill("/code-review", { diff: diff, scope: "style-only" }),

  () => agent("Review this diff for DATA ACCESS pattern issues only: " + diff),
  () => agent("Review this diff for missing or outdated DOCS only: " + diff)
])

phase("Verify")

verified_findings = pipeline(
  flatten(findings),
  (finding) => agent("A reviewer claims: '" + finding + "'. Here is the " +
    "actual diff: " + diff + ". Try to find a reason this claim might " +
    "be WRONG — check exact line numbers and variable names. Report " +
    "CONFIRMED or REJECTED, with a one-line reason.")
)

confirmed_only = filter(verified_findings, (f) => f.status == "CONFIRMED")

return confirmed_only
```

Two things worth noticing, both direct answers to Goal 3's question about how Skills, Workflows, and (later) Agents connect:

**The skill stage still gets verified exactly like the other four.** Being a mature, already-tested skill doesn't exempt it. Its findings go through the same "find a reason this might be WRONG" check as everything else in the fan-out. Trust is earned the same way for every stage, regardless of what kind of thing produced it.

**The skill itself didn't change at all.** `run_skill("/code-review", ...)` calls it exactly the way Rahul always has, just from inside a workflow stage instead of typing `/code-review` by hand. Nothing about promoting a skill into a workflow required rewriting the skill.

---

## What went wrong the first time

The first version of this workflow rewrote the style review from scratch as a new `agent()` call. That duplicated logic that already existed, already worked, and was already tuned against real Kestrel PRs over months of use in AI-Skills. It technically worked, but every time the team's style standards changed, someone now had to remember to update it in *two* places — the skill, and this workflow's copy of it.

The fix was realizing there was no reason to duplicate it at all: call the skill directly as a stage. That gives one source of truth for "what does Kestrel's style review actually check." It's used on its own for a small, single-angle PR that doesn't need the full five-angle treatment. It's used as a stage inside the bigger workflow for a large PR that does.

---

## How it was tested

Everything from [Chapter 5](../../tutorial/05-fan-out-and-verify.md)'s original testing — the line-84 false-positive story and its fix are the origin of this exact verification stage. Additionally: confirmed the style stage, called through `run_skill`, produces the same findings a direct `/code-review` run would on the same diff, so nothing was lost in translation by calling it from inside a workflow instead of by hand.

Real-world test: the same 600-line PR from this tutorial's opening story. Five angles found 14 raw findings. Verification rejected 3 of them, including a data-access finding that turned out to reference a file already deleted earlier in the same diff. 11 confirmed findings reached the PR — a real, focused review, at a size no single linear pass could have covered evenly.

---

## Where it sits on the sharing ladder

**Level 3 — Company-wide**, with the cost documented up front, per [Chapter 9](../../tutorial/09-governance-and-capstone.md)'s Part 4. This workflow is 5 parallel calls plus up to 5 verification calls — roughly 10 pieces of work per PR. There's no nested nesting, so it stays well within a sensible cap. The number itself is written into the workflow's own description, so nobody discovers it by surprise.

---

## References & assets

- **[`workflow.md`](workflow.md)** — the complete, real script. Copy it into your own workflow tool, adapting syntax per the repo's [note on accuracy](../../README.md#a-note-on-accuracy).
- **[`assets/flow-diagram.md`](assets/flow-diagram.md)** — this case study's own diagram, with the `run_skill()` stage marked explicitly.
- **Chapters used:** [Chapter 1](../../tutorial/01-what-is-a-workflow.md), [Chapter 4](../../tutorial/04-parallel-vs-pipeline.md), [Chapter 5](../../tutorial/05-fan-out-and-verify.md), [Chapter 9](../../tutorial/09-governance-and-capstone.md) (the documented cost that earns Level 3), [Chapter 10](../../tutorial/10-lifecycle-of-execution.md).
- **Where this started:** the exact skill this workflow's style angle calls is [AI-Skills Case Study 4](../../../AI-Skills/case-studies/04-code-review-skill/README.md).

---

## Where the story goes next

Rahul's skill became a stage in this workflow. The workflow itself has a fixed plan — five angles, always the same five, decided in advance, every time.

The next tutorial picks up exactly there: what happens when even a fixed plan isn't enough — when the right next step genuinely depends on what gets discovered along the way, not on something decided in advance.

**[AI-Agents →](../../../AI-Agents/README.md)**

---

← [Case Study 3 — QA](../03-qa-workflow/README.md) · [All case studies](../README.md)
