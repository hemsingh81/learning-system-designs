# Workflow Template

← [Back to README](../README.md) · See it explained: [Chapter 2 — Anatomy of a Workflow](../tutorial/02-anatomy-of-a-workflow.md)

Copy the block below to start a new workflow. Every `[LIKE THIS]` is a placeholder. Delete the comments once you've filled a section in for real.

---

```javascript
meta = {
  name: "[your-workflow-name-in-lowercase-with-hyphens]",
  version: "1.0.0",
  description: "[WHAT it coordinates, one sentence — this is documentation,
    NOT a trigger. Workflows are run on purpose, never auto-triggered.]",
  phases: [
    { title: "[Phase 1 name]" },
    { title: "[Phase 2 name]" }
    // one entry per phase() call below
  ]
}

// ── BEFORE YOU WRITE ANY CODE ──
// Run Chapter 3's test: would ONE focused piece of work, given the same
// information, do just as good a job as several separate pieces? If yes,
// this doesn't need to be a workflow. Build a skill instead.
//
// If genuinely separate parts / real stages / a need for independent
// verification — continue.

phase("[Phase 1 name]")

// [WHAT this phase does, in one line]
//
// Default to pipeline() unless you can name the SPECIFIC cross-item
// reason a parallel() barrier is needed (deduplication across everything,
// an early-exit decision, or a genuine comparison between items).
// See Chapter 4 before reaching for parallel().

results = pipeline(
  [ITEMS],
  (item) => agent("[stage 1 instructions for one item]"),
  (stage1_result, item) => agent("[stage 2 instructions, using stage1_result]")
)

phase("[Phase 2 name]")

// [IF FINDINGS NEED TRUST: add a verification stage here. Word it as
// "try to find a reason this might be WRONG" — not "confirm this is
// right." See Chapter 5. Use a FRESH agent() call, not the same one
// that produced the finding.]

verified = pipeline(
  results,
  (finding) => agent("A claim was made: '" + finding + "'. Try to find " +
    "a reason this might be WRONG. Report CONFIRMED or REJECTED, with " +
    "a one-line reason.")
)

confirmed_only = filter(verified, (f) => f.status == "CONFIRMED")

return confirmed_only
```

---

## The checklist to run before you consider this "done"

Pulled from [Chapter 9](../tutorial/09-governance-and-capstone.md) — the short version.

- [ ] Does this genuinely have separate parts, real stages, or need an independent check? ([Chapter 1](../tutorial/01-what-is-a-workflow.md))
- [ ] Would one focused piece of work do just as well? If so, build a skill instead. ([Chapter 3](../tutorial/03-your-first-workflow.md))
- [ ] For every `parallel()` barrier — can you name the specific cross-item reason it's needed? ([Chapter 4](../tutorial/04-parallel-vs-pipeline.md))
- [ ] If findings need trust, is verification worded to look for reasons a claim is WRONG, using a fresh agent call? ([Chapter 5](../tutorial/05-fan-out-and-verify.md))
- [ ] Tested at a realistic scale, not just your smallest example? ([Chapter 7](../tutorial/07-testing-and-iterating.md))
- [ ] Does it require a deliberate decision to run — never automatic, the way a skill triggers? ([Chapter 8](../tutorial/08-packaging-and-sharing.md))
- [ ] Any nested orchestration? If so, is the real multiplication written down, with an explicit cap? ([Chapter 9](../tutorial/09-governance-and-capstone.md))

---

## A filled-in example, for reference

The five-angle review workflow, built across Chapters 1, 4, and 5, shown complete.

```javascript
meta = {
  name: "pr-five-angle-review",
  version: "1.1.0",
  description: "Reviews a PR from 5 angles (security, tests, style, data " +
    "access, docs), then independently verifies each finding before it " +
    "reaches the PR.",
  phases: [
    { title: "Review" },
    { title: "Verify" }
  ]
}

phase("Review")

findings = parallel([
  () => agent("Review this diff for SECURITY issues only: " + diff),
  () => agent("Review this diff for missing TEST coverage only: " + diff),
  () => agent("Review this diff for STYLE issues only: " + diff),
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

---

← [Back to README](../README.md)
