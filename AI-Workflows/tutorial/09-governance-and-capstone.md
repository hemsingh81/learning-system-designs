# Chapter 9 — Governance and Capstone

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Case Studies →](../case-studies/README.md)

---

## Where you left off

Rahul asks you to sit in on a review, again — same as your very last AI-Skills chapter, but this time it's a workflow.

Another team built a per-file review workflow: pipeline through every changed file, and for *each* file, run the same five-angle fan-out you built, complete with verification.

Nobody did anything wrong, individually. Each piece — the pipeline, the fan-out, the verification — is exactly the pattern this tutorial taught you. But a PR touching 8 files means 8 × 5 = 40 review calls. Add verification on top, and a good number of those get checked twice. On one ordinary PR, this workflow quietly spun up somewhere north of fifty separate pieces of work.

Nobody noticed until someone asked why a routine PR review had taken eleven minutes and cost noticeably more than expected.

---

## What you'll learn

1. Why fan-out multiplies invisibly when it's nested, and why nobody has to make a single bad decision for it to happen.
2. How to set a real, explicit limit that catches this before it ships.
3. The complete checklist — thought process to sharing — tying together everything from Chapters 1 through 8.

---

## The lesson

### Why this is the risk unique to workflows

A skill can't do this. One skill, triggered, does one focused piece of work — its cost is bounded by definition, because there's only ever one flow of reasoning happening.

A workflow's entire value, as you've spent this whole tutorial learning, is coordinating *multiple* pieces of work on purpose. That's exactly what makes it powerful, and it's exactly what makes uncontrolled growth possible in a way a skill never could produce. **The same feature that makes workflows valuable is the one that makes runaway cost possible.** This isn't a coincidence you can design away — it's a direct consequence of what a workflow is for, and it's why this needs its own deliberate governance, the same way irreversible actions needed their own review in AI-Skills.

### Why the other team's mistake is easy to miss

Look at each piece on its own. A pipeline through 8 files — completely reasonable, exactly [Chapter 4](04-parallel-vs-pipeline.md)'s lesson. A five-angle fan-out per file — completely reasonable, exactly [Chapter 5](05-fan-out-and-verify.md)'s lesson. Verification on findings — also completely reasonable.

**The problem only exists at the point where they were nested together**, and nesting is invisible in a way a single large number wouldn't be. Nobody wrote "spawn 50 pieces of work" anywhere in the code. They wrote two individually-sensible patterns, and multiplication did the rest.

This is worth stating plainly, because it generalises far past this one example: **whenever a workflow calls another piece of orchestrated work inside one of its own stages — a pipeline inside a pipeline, a fan-out inside each item of a pipeline — the real cost is the product of both, not the sum.** 8 files times 5 checks isn't 13. It's 40. That arithmetic is easy to say out loud and very easy to miss while you're heads-down building each piece separately.

### The fix: an explicit, visible limit

The honest fix isn't "be more careful" — you already learned that lesson doesn't hold up under real deadline pressure, back in AI-Skills. The fix is a real, checkable limit that exists in the workflow itself, not in someone's memory.

```javascript
meta = {
  name: "per-file-five-angle-review",
  description: "Reviews changed files, 5 angles each, with verification",
  phases: [{ title: "Review" }]
}

MAX_FILES = 10   // an explicit, visible cap

phase("Review")

changed_files = get_changed_files(pr)

if (changed_files.length > MAX_FILES) {
  return "This PR touches " + changed_files.length + " files, above " +
         "this workflow's limit of " + MAX_FILES + ". Running the full " +
         "5-angle review on every file would spawn roughly " +
         (changed_files.length * 5) + " pieces of work. Falling back to " +
         "a single combined review instead — ask a human to review the " +
         "largest or most sensitive files individually if needed."
}

// Only runs the expensive per-file fan-out below the explicit cap.
results = pipeline(
  changed_files,
  (file) => run_five_angle_review(file)   // this itself contains a parallel() fan-out
)

return results
```

Three things worth noticing about this fix:

**The cap is a real number, written down, not a vague intention.** `MAX_FILES = 10` is checkable. "Don't let this get too big" is not.

**Going over the cap doesn't fail silently — it falls back to something cheaper, and says why.** The workflow doesn't just refuse to run. It explains the actual math — "roughly 40 pieces of work" — so whoever's reading the output understands exactly what was avoided and why, and can decide whether the fallback is good enough or whether this specific PR is worth the full cost anyway.

**The estimate is stated honestly** — files times angles — so the person reading it can do their own judgement call, instead of the workflow silently deciding for them without explanation.

### The three questions for any workflow, before it ships

Adapted from AI-Skills' safety questions, for the risk that's actually unique to workflows.

**1. Does this workflow call orchestrated work — a pipeline, a fan-out — inside one of its own stages?** If yes, the next two questions matter a lot more.

**2. If it's nested, what's the real multiplication?** Write down the actual arithmetic, the way the example above did. "Roughly N times M pieces of work" is the number that matters, not a feeling that it's "probably fine."

**3. Is there an explicit, visible cap — and does going over it fail loudly with an explanation, or does it just silently run at whatever size the input happens to be?** A workflow with no cap will eventually meet an input large enough to make the multiplication genuinely expensive, and it won't warn anyone first.

### The pre-distribution safety review, extended

Everything from AI-Skills' checklist still applies — read what the instructions actually say, check the description is honest, test properly, version it. Add these, specific to what's new about a workflow:

- [ ] **Is there any nested orchestration** — a fan-out or pipeline called from inside another stage?
- [ ] **If yes, is the real multiplication written down** — the actual "N times M" arithmetic, not a guess?
- [ ] **Is there an explicit, checkable cap**, and does exceeding it fail loudly, with an explanation, rather than silently scaling up?
- [ ] **Is the workflow's typical cost stated somewhere visible** — in its description, or its documentation — so nobody discovers it by accident, the way the other team's reviewers discovered their eleven-minute PR review?
- [ ] **Does anything in this workflow run automatically**, the way a skill would, rather than requiring a deliberate, on-purpose decision to run? If so, per [Chapter 8](08-packaging-and-sharing.md), that's a real problem to fix before this ships anywhere.

### The full journey, in one checklist

**Thought process (Chapters 1, 3, 6)**
- [ ] Does this task genuinely have separate parts, real stages, or need an independent check — not just "it sounds more organised as a workflow"? (Chapter 1)
- [ ] Would one focused piece of work do just as well? If so, this doesn't need to be a workflow at all. (Chapter 3)
- [ ] Checked against the full decision framework — workflow, or actually a skill, subagent, or hook? (Chapter 6)

**Writing (Chapters 2, 4, 5)**
- [ ] Does it follow the standard shape — meta, phases, agent calls? (Chapter 2)
- [ ] For every `parallel()` barrier: can you name the specific cross-item reason it's needed? Default is pipeline. (Chapter 4)
- [ ] If findings need trust, is there a genuinely independent verification stage, worded to look for reasons a claim might be wrong? (Chapter 5)

**Testing (Chapter 7)**
- [ ] Structural tests confirm the shape behaves as designed — real parallelism, real pipeline overlap?
- [ ] Verification tests pass on both sides — rejects planted false findings, confirms real ones?
- [ ] Tested at a realistic scale, not just your smallest example?

**Sharing (Chapter 8)**
- [ ] Does it have a real version number, and does MAJOR actually mean the orchestration shape changed?
- [ ] Is there a changelog entry, calling out any cost change explicitly?
- [ ] Does it require a deliberate decision to run, not automatic triggering?

**Governance (Chapter 9)**
- [ ] Run the extended pre-distribution safety review above, every time nested orchestration is involved.

### Closing the loop

Go back to [`00-the-story.md`](../00-the-story.md) for a second, to "what done looks like."

You've built a workflow from nothing, watched it fail to earn its own overhead, learned the single decision that makes the difference between fast and slow, built a review nobody can quietly trust wrongly, and now know exactly what stops one small PR from spawning fifty pieces of work by accident. Rahul's original skill — the one that started your whole first tutorial — is now one well-tested stage inside something genuinely bigger.

### Where this leaves you

You now have two tools. A skill for one focused, recognisable, repeated request. A workflow for a fixed, deterministic plan that coordinates several. Both genuinely valuable, both with a real, honest limit.

Remember [Chapter 6](06-workflows-vs-other-tools.md)'s honest boundary: **a workflow's plan is fixed once it starts.** It can't decide, mid-run, that what it just discovered calls for a genuinely different next step than the one you wrote in advance.

That's exactly where the next tool picks up.

---

## Try it yourself

Run your own workflow — the one you've been building since Chapter 3 — through the complete checklist above, honestly, top to bottom. If it has any nested orchestration at all, do the actual multiplication arithmetic and write down the real number, even if you're confident it's fine. Confidence isn't the same as a written-down number, and this whole chapter exists because that gap is exactly where the other team's mistake lived.

---

## What's still missing

Nothing, for this one workflow. Same as your last capstone — you've done the whole thing, start to end.

Read the [case studies](../case-studies/README.md) next — four different teams, four genuinely different orchestration shapes, including the one where Rahul's original skill becomes a real stage inside a real workflow.

**Then, when you're ready:** [AI-Agents](../../AI-Agents/README.md) picks up exactly where this chapter's honest limit leaves off — for the tasks where even a fixed, deterministic plan isn't flexible enough.

---

← [Chapter 8 — Packaging and Sharing](08-packaging-and-sharing.md) · [Learning path](../learning-path.md) · Next: [Case Studies →](../case-studies/README.md)
