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
