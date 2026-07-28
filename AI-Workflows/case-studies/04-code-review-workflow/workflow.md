# `pr-five-angle-review` v1.1.0 — real, runnable workflow

← [Back to case study](README.md)

Copy the script below into your own workflow tool, adapting syntax as needed per the [note on accuracy](../../README.md#a-note-on-accuracy). `run_skill(...)` is the one line that has to change most between tools — it should resolve to however your tool invokes an existing skill/slash-command from inside a script; if your tool has no such primitive, replace that line with a direct `agent()` call carrying the same style-review instructions.

**Inputs this workflow expects:** `diff` (the PR's diff, as a string).
**Typical cost:** 5 parallel review calls + up to 5 verification calls ≈ 10 pieces of work per PR — documented in the case study's [sharing-ladder section](README.md#where-it-sits-on-the-sharing-ladder) as required before Level 3 sharing, per [Chapter 9](../../tutorial/09-governance-and-capstone.md).

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
  // See AI-Skills Case Study 4 for the skill this line calls.
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

---

← [Back to case study](README.md)
