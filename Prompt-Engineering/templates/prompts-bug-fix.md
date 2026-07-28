--- filename: templates/prompts-bug-fix.md ---

# Bug-Fix Prompt Templates

← [Back to README](../README.md) · Related: [Chapter 1 — Assumptions](../chapter-01-assumptions.md), [Chapter 3 — Prompt Design Patterns](../chapter-03-prompt-design-patterns.md)

12 ready-to-run prompts for diagnosing and fixing bugs. Each includes purpose, prompt text with `[placeholders]`, example input, expected output format, and why it works. Language variants are noted where the prompt benefits from being language-specific.

---

## 1. Root Cause Hypothesis

**Purpose:** The core diagnostic prompt — turns a stack trace and a diff into a ranked, actionable diagnosis instead of a guess.

**Prompt:**
```
You are an expert debugging assistant. Given:
- Repository: [repo name/path]
- Failing test: [test name]
- Stack trace:
[paste stack trace]
- Recent commit diff:
[paste diff]

Produce: 1) a concise root-cause hypothesis, 2) minimal reproduction
steps, 3) three candidate fixes ranked by risk, with code snippets,
4) unit tests that would cover the fix, 5) a one-line commit message.
Output in Markdown.
```

**Example input:**
```
Repository: checkout-service
Failing test: test_apply_discount_after_partial_refund
Stack trace: AssertionError: expected 45.00, got 50.00 at
  discount_calculator.py:112, in apply_discount
Recent commit diff: [diff adding partial-refund support to Order model]
```

**Expected output format:** Markdown with 5 numbered sections matching the prompt's request; code snippets in fenced blocks.

**Why it works:** Every input the model needs is explicit and separated by type (test, trace, diff). Naming all five output sections prevents the model from jumping straight to "here's a fix" without showing the reasoning that justifies it.

---

## 2. Minimal Reproduction Builder

**Purpose:** Isolates a bug to the smallest possible failing case, which is often more valuable than the fix itself.

**Prompt:**
```
Given this bug report: [paste report/description] and this codebase
context: [paste relevant files or describe structure], write the
smallest possible code snippet that reproduces the bug in isolation —
remove everything not essential to triggering it.
```

**Expected output format:** A single, runnable, minimal code block plus one sentence confirming what condition triggers the bug.

**Why it works:** Minimization forces precision — a model (or a human) that can't minimize a bug usually doesn't actually understand it yet.

---

## 3. "What Am I Missing" Edge-Case Reviewer

**Purpose:** Catches blind spots in a proposed fix before it ships.

**Prompt:**
```
Here is my proposed fix for [bug]: [paste diff or description].
What edge cases, race conditions, or regressions might this introduce?
List them by likelihood, most likely first.
```

**Expected output format:** A ranked bullet list, each item naming a specific scenario, not a generic warning.

**Why it works:** Explicitly asks for critique rather than confirmation — the default failure mode of asking "does this fix look right?" is a model that just agrees with you.

---

## 4. Flaky Test Diagnoser

**Purpose:** Distinguishes timing/ordering issues from genuine logic bugs in intermittently-failing tests.

**Prompt:**
```
This test fails intermittently, not every run: [paste test code].
Here are logs from 2 failing runs and 1 passing run: [paste logs].
Is this more likely a timing/ordering/concurrency issue, a test-data
pollution issue (shared state between tests), or a genuine logic bug
that only triggers under specific data? Justify with evidence from the
logs, not general reasoning.
```

**Expected output format:** One classification (timing/pollution/logic) with cited evidence from the specific logs provided.

**Why it works:** "Justify with evidence from the logs" prevents the model from defaulting to the statistically most common answer ("probably a race condition") without actually checking whether the provided evidence supports it.

---

## 5. Language Variant — Python

**Purpose:** Root-cause diagnosis tuned for common Python failure classes.

**Prompt:**
```
Debug this Python error: [paste traceback]. Given this code:
[paste code]. Common Python-specific causes to consider explicitly:
mutable default arguments, late-binding closures in loops, off-by-one
in slicing, and None vs. falsy-value confusion. State which (if any)
apply here, and provide the fix.
```

**Expected output format:** A named root cause (from the listed categories or otherwise) plus a corrected code block.

**Why it works:** Naming language-specific gotchas up front primes the model to check for them explicitly rather than only pattern-matching to the surface error message.

---

## 6. Language Variant — JavaScript/TypeScript

**Purpose:** Root-cause diagnosis tuned for common JS/TS failure classes.

**Prompt:**
```
Debug this JavaScript/TypeScript error: [paste error/stack]. Given this
code: [paste code]. Common JS-specific causes to consider explicitly:
`this` binding issues, unhandled promise rejections, async/await
ordering assumptions, and `==` vs `===` type coercion. State which (if
any) apply here, and provide the fix with correct typing if TypeScript.
```

**Expected output format:** A named root cause plus a corrected, type-safe code block.

**Why it works:** Same principle as the Python variant — surfacing the language's known sharp edges up front improves diagnostic accuracy over a generic prompt.

---

## 7. Language Variant — Java

**Purpose:** Root-cause diagnosis tuned for common Java failure classes.

**Prompt:**
```
Debug this Java exception: [paste stack trace]. Given this code:
[paste code]. Common Java-specific causes to consider explicitly:
NullPointerException from unboxing, ConcurrentModificationException
from mutating a collection during iteration, and equals()/hashCode()
contract violations. State which (if any) apply here, and provide the fix.
```

**Expected output format:** A named root cause plus a corrected code block.

**Why it works:** Same pattern — language-specific priming reduces the chance of a generic, non-actionable diagnosis.

---

## 8. Unit Test Generator (fix-coverage variant)

**Purpose:** Generates the specific test that would have caught a given bug, so it can't silently regress.

**Prompt:**
```
Here is a bug: [paste description] and its fix: [paste diff]. Generate
a unit test that would have FAILED before this fix and PASSES after it.
Use [test framework, e.g., pytest / Jest / JUnit]. Include the failing
input and expected output explicitly, not just a happy-path test.
```

**Expected output format:** Runnable test code in the specified framework, targeting the exact failure condition.

**Why it works:** "Would have failed before, passes after" is a concrete, checkable property — you can literally run the test against the pre-fix code to verify it, rather than trusting the test is meaningful by inspection alone.

---

## 9. Unit Test Generator (edge-case variant)

**Purpose:** Broader test generation covering edge cases beyond the specific reported bug.

**Prompt:**
```
Generate a unit test suite for this function: [paste function]. Cover:
happy path, empty/null input, boundary values (zero, negative, max),
and at least one case that would catch the class of bug described here
if it recurred elsewhere: [paste bug description]. Use [test framework].
```

**Expected output format:** A test file with clearly-named test cases (one per scenario listed).

**Why it works:** Anchoring "at least one case that would catch this class of bug" to a real past bug makes the generated suite defend against a recurrence, not just generic coverage-for-coverage's-sake.

---

## 10. Regression Root-Cause Comparator

**Purpose:** Diagnoses a bug that appeared after a specific deploy/release, using bisection-style reasoning.

**Prompt:**
```
This bug appeared after deploying commits [list commit range/PRs]
between [version A] and [version B]. Bug symptom: [paste description].
Here are the changes in that range: [paste diffs or commit list].
Which specific change most plausibly caused this, and why? If multiple
are plausible, rank them and state what test would disambiguate.
```

**Expected output format:** A ranked list of plausible causal commits, each with a specific reasoning chain, plus a disambiguating test suggestion.

**Why it works:** Constraining the search space to a known commit range (rather than "why is this broken" over the whole codebase) turns an open-ended search into a tractable comparison.

---

## 11. Performance Regression Diagnoser

**Purpose:** Diagnoses a bug that isn't a crash but a measurable slowdown.

**Prompt:**
```
This endpoint's p95 latency went from [X]ms to [Y]ms after this change:
[paste diff]. Given this profiling data: [paste profile/flame graph
summary or query plan], identify the most likely cause: an added N+1
query, a missing index, an unbounded loop, a new synchronous call that
used to be async, or something else. State your reasoning against the
actual profiling data provided, not general suspicion.
```

**Expected output format:** A single most-likely cause with reasoning tied to the provided profiling data, plus a suggested fix.

**Why it works:** "Against the actual profiling data provided, not general suspicion" forces the model to reason from evidence rather than reciting the most common performance-bug checklist without verifying against what's actually shown.

---

## 12. Post-Fix Verification Prompt

**Purpose:** A final check before closing out a bug — confirms the fix actually addresses the stated root cause, not just the symptom.

**Prompt:**
```
Here is the original bug report: [paste report]. Here is the diagnosed
root cause: [paste from Prompt #1's output]. Here is the shipped fix:
[paste final diff]. Does the fix address the root cause, or does it only
suppress the symptom (e.g., adding a null check instead of fixing why
the value was null in the first place)? Be direct.
```

**Expected output format:** A direct verdict (addresses root cause / suppresses symptom) with one-sentence reasoning.

**Why it works:** Explicitly distinguishes "the test passes now" from "the actual bug is fixed" — a distinction easy to lose once a fix is in hand and the pressure is to close the ticket.

---

← [Back to README](../README.md) · Related: [`prompts-status-email.md`](./prompts-status-email.md), [`prompts-research.md`](./prompts-research.md)
