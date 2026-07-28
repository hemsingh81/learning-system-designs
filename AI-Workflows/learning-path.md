# The Learning Path

← [The Story](00-the-story.md) · [Back to README](README.md)

Nine chapters, read in order — each needs the last. Then four case studies, readable in any order.

---

## The shape of every chapter

Same five parts as AI-Skills, so the habit carries over:

1. **Where you left off** — one paragraph, so you can start cold.
2. **What you'll learn** — two or three plain sentences.
3. **The lesson** — explained slowly, with analogies and real examples.
4. **Try it yourself** — a real, small exercise.
5. **What's still missing** — the exact gap the next chapter fills.

---

## The full path

| # | Chapter | Time | Where the story is | File |
|---|---|---|---|---|
| 1 | What Is a Workflow? | 20 min | One reviewer, one pass, no real focus on what matters | [`tutorial/01-what-is-a-workflow.md`](tutorial/01-what-is-a-workflow.md) |
| 2 | Anatomy of a Workflow | 25 min | You look at a real workflow script and can't read it yet | [`tutorial/02-anatomy-of-a-workflow.md`](tutorial/02-anatomy-of-a-workflow.md) |
| 3 | Your First Workflow | 40 min | You build one, and it's not actually any faster | [`tutorial/03-your-first-workflow.md`](tutorial/03-your-first-workflow.md) |
| 4 | Parallel vs. Pipeline | 40 min | Your workflow waits for everything before starting anything | [`tutorial/04-parallel-vs-pipeline.md`](tutorial/04-parallel-vs-pipeline.md) |
| 5 | Fan-Out and Verify | 35 min | An independent check finds something that turns out to be wrong | [`tutorial/05-fan-out-and-verify.md`](tutorial/05-fan-out-and-verify.md) |
| 6 | Workflows vs. Other Tools | 30 min | Rahul asks why this isn't just five separate skills | [`tutorial/06-workflows-vs-other-tools.md`](tutorial/06-workflows-vs-other-tools.md) |
| 7 | Testing and Iterating | 30 min | You're about to share this — does it hold up at real scale? | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) |
| 8 | Packaging and Sharing | 35 min | Divya wants this pattern for her own check | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) |
| 9 | Governance and Capstone | 30 min | Someone's workflow quietly spawns forty agents on a small PR | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) |
| 10 | The Execution Lifecycle (bonus) | 25 min | Rahul asks you to trace the whole run, including its failure paths | [`tutorial/10-lifecycle-of-execution.md`](tutorial/10-lifecycle-of-execution.md) |

**Total: about 5 hours**, including every exercise.

---

## Chapter details

### Chapter 1 — What Is a Workflow?
**File:** [`tutorial/01-what-is-a-workflow.md`](tutorial/01-what-is-a-workflow.md)

**You'll be able to:**
1. Explain what a workflow is, and how it's different from a skill, in your own words.
2. Name a real task on your team that a single skill genuinely can't do well.
3. Explain why "just write a longer skill" doesn't solve that problem.

**You'll try:** Take a task you do that has independent parts, or clear stages. Write down, in one sentence, why doing it as one continuous pass (like a skill would) loses something real.

---

### Chapter 2 — Anatomy of a Workflow
**File:** [`tutorial/02-anatomy-of-a-workflow.md`](tutorial/02-anatomy-of-a-workflow.md)

**You'll be able to:**
1. Read a real workflow script and understand every part of it.
2. Explain what a "phase" is, and why workflows are organised into them.
3. Explain the difference between a workflow's plan and the actual work each stage does.

**You'll try:** Read a real workflow script (one is included) and, before checking the answer, sketch what order its stages actually run in.

---

### Chapter 3 — Your First Workflow
**File:** [`tutorial/03-your-first-workflow.md`](tutorial/03-your-first-workflow.md)

**You'll be able to:**
1. Write a working workflow with more than one stage.
2. Notice when a workflow isn't actually buying you anything over doing the same work one step at a time.
3. Name the first mistake almost everyone makes when they start.

**You'll try:** Build a tiny two-stage workflow. Time it against doing the same steps as separate, sequential requests. Be honest about whether it actually helped.

---

### Chapter 4 — Parallel vs. Pipeline
**File:** [`tutorial/04-parallel-vs-pipeline.md`](tutorial/04-parallel-vs-pipeline.md)

**You'll be able to:**
1. Explain the real difference between running things in parallel and running them as a pipeline.
2. Pick correctly between them for a real task.
3. Explain what a "barrier" is, and name the actual cost of using one when you didn't need to.

**You'll try:** Take a workflow with 3 independent stages. Run it once as a strict barrier, once as a pipeline. Measure the real difference.

---

### Chapter 5 — Fan-Out and Verify
**File:** [`tutorial/05-fan-out-and-verify.md`](tutorial/05-fan-out-and-verify.md)

**You'll be able to:**
1. Design a "check from several angles" review.
2. Explain why an independent check can sound confident and still be wrong.
3. Add a verification step that actually catches that.

**You'll try:** Take one of your fan-out checks. Deliberately feed it something plausible-but-wrong. See if your verification step catches it.

---

### Chapter 6 — Workflows vs. Other Tools
**File:** [`tutorial/06-workflows-vs-other-tools.md`](tutorial/06-workflows-vs-other-tools.md)

**You'll be able to:**
1. Choose correctly between a skill, a workflow, and a subagent for a real task.
2. Explain why "call several skills, one after another, by hand" isn't the same as a workflow.
3. Explain, in one sentence, what a workflow still can't do — and what comes next.

**You'll try:** Take three real tasks from your own team. Assign each to a skill, a workflow, or neither, and say why.

---

### Chapter 7 — Testing and Iterating
**File:** [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md)

**You'll be able to:**
1. Test that a workflow's stages run in the order and shape you designed.
2. Test that a verification stage actually rejects bad findings, not just wave them through.
3. Decide when a workflow is genuinely ready to share.

**You'll try:** Run your workflow against 3 real inputs of different sizes. Check whether its behaviour — not just its output — stayed correct as the input grew.

---

### Chapter 8 — Packaging and Sharing
**File:** [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md)

**You'll be able to:**
1. Version a workflow so a structural change doesn't silently surprise anyone using it.
2. Explain why workflows are normally run on purpose, not triggered automatically like a skill.
3. Write a short changelog entry for a workflow update.

**You'll try:** Move your workflow from personal to project-shared, and write its first changelog entry.

---

### Chapter 9 — Governance and Capstone
**File:** [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md)

**You'll be able to:**
1. Explain the cost risk a workflow introduces that a skill never could.
2. Set a real limit that stops a workflow from silently growing out of control.
3. Use the full "is this ready?" checklist, from thought process to sharing.

**You'll try:** Run the pre-distribution checklist against your own workflow. Check specifically: what stops this from spawning more work than intended?

---

### Chapter 10 — The Execution Lifecycle (bonus)
**File:** [`tutorial/10-lifecycle-of-execution.md`](tutorial/10-lifecycle-of-execution.md)

**You'll be able to:**
1. Trace a real multi-phase workflow's full runtime, from invocation to return value.
2. Explain exactly what happens inside a `parallel()` barrier and a `pipeline()`, moment to moment.
3. Predict what happens when a stage fails, for both orchestration shapes.

**You'll try:** Trace your own workflow the way this chapter traced the five-angle review — every `phase()`, every `parallel()`/`pipeline()` call, and what a single failed stage would do at each one.

---

## Then, the case studies

Same nine chapters. Four different people, four different jobs, four different orchestration shapes.

- [Frontend — cross-size check](case-studies/01-frontend-workflow/README.md) — Divya, parallel fan-out with a barrier
- [Backend — scaffold, test, document](case-studies/02-backend-workflow/README.md) — Vikram, pipeline with overlapping stages
- [QA — generate and verify coverage](case-studies/03-qa-workflow/README.md) — Ananya, fan-out plus adversarial verification
- [Code review — five angles, verified](case-studies/04-code-review-workflow/README.md) — Rahul, a skill living inside a workflow stage

Read the one closest to your own role first. Read all four to see the same discipline bend to fit a genuinely different orchestration shape each time — that contrast is the actual point.

---

← [The Story](00-the-story.md) · [Back to README](README.md) · Start: [Chapter 1 →](tutorial/01-what-is-a-workflow.md)
