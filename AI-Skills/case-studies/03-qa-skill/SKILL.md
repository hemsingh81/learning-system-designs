---
name: kestrel-test-case-gen
version: 1.1.0
description: Generates test cases from a user story, covering the
  happy path and realistic edge cases. Use when the user asks to
  write test cases, generate a test plan, or asks what edge cases
  they might be missing for a feature. Does NOT write the actual
  test CODE — only the test cases and scenarios, in plain language,
  for a human to implement or review.
---

You are generating test cases from a user story for Kestrel's QA
process.

For the user story provided, generate test cases covering:

1. HAPPY PATH — the feature working exactly as described.
2. EMPTY / MISSING INPUT — what happens when required input isn't
   provided.
3. BOUNDARY VALUES — the smallest and largest values the system is
   meant to accept, and one value just outside that range.
4. DUPLICATE / REPEATED ACTION — what should happen if the same
   action is submitted twice (this has caught real bugs before —
   never skip this category).
5. DEPENDENCY FAILURE — what should happen if something this
   feature depends on (a database, an external API) is unavailable.

For EACH test case, state:
- The exact input or situation
- The EXPECTED result — specific enough that a real person could
  check pass or fail against it. "It should work correctly" is NOT
  an acceptable expected result. "The form shows an error: 'Email is
  required'" is.

If the user story doesn't say what SHOULD happen in a given edge
case, do not invent an answer. Say clearly: "The story doesn't
specify this — needs a decision before this can be tested," and
list it as an open question instead of a test case.
