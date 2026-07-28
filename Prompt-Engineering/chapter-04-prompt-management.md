--- filename: chapter-04-prompt-management.md ---

# Chapter 4 — Prompt Management

← [Chapter 3 — Prompt Design Patterns](./chapter-03-prompt-design-patterns.md) · [Learning path](./learning-path.md) · Next: [Chapter 5 — Workflows](./chapter-05-workflows.md)

## Narrative

Three weeks after the midnight debugging session, a teammate messages Asha:

> "Hey, didn't you have a good prompt for diagnosing flaky tests? Can you send it?"

She searches her chat history for ten minutes. She finds three different versions of roughly the same prompt. She is not sure which one she actually used last. She sends him one.

It turns out to be an older, worse version.

That is the moment she realises something: **a good prompt that only lives in someone's chat history is barely better than no prompt at all.**

Her code has version control. It has a naming convention. It has tests that fail loudly when something breaks. Her prompts had none of that. They were tribal knowledge with extra steps.

So she does the obvious thing. She treats prompts like code:

- One file per prompt
- A naming convention
- A version number
- A few tests that check the *shape* of the output
- A catalog file the whole team can search

It takes an afternoon. The "which version did you use?" problem never comes back.

---

## Learning objectives

By the end of this chapter you will be able to:

1. Design a naming convention and version numbering scheme for prompts.
2. Build a complete catalog entry with metadata.
3. Explain why prompt tests check output **shape** and not exact text — and why that difference matters.

---

## Key concepts

### Prompt catalog

**Plain definition:** A searchable, versioned list of your team's prompts. Usually a JSON or YAML file, plus the prompt text files it points to.

**What problem it solves:** Exactly Asha's problem above. Three versions in chat history, no way to know which is current.

**What good looks like:** A teammate can find the right prompt without asking you, and can tell at a glance whether it is current.

### Semantic versioning for prompts

You already know `MAJOR.MINOR.PATCH` from software. Here is what each means for a prompt:

| Change | Bump | Example |
|---|---|---|
| Wording tweak, same behaviour | **PATCH** (1.0.0 → 1.0.1) | Fixed a typo |
| New capability, still backward compatible | **MINOR** (1.0.1 → 1.1.0) | Added an optional `severity` field |
| Output format or behaviour changed in a way that breaks existing users | **MAJOR** (1.1.0 → 2.0.0) | Changed output from prose to strict JSON |

**Why bother?** Because "I improved the prompt" is not enough information for someone whose script parses its output. MAJOR tells them: *stop, check your code before upgrading.*

### Prompt test case

**Plain definition:** An input, plus a description of what a correct output should *look like*.

**The critical detail: test the shape, not the exact words.**

Here is why. Run the same prompt twice and you will get two slightly different answers. Not wrong — just worded differently. A test that checks for exact text will fail on a harmless rewording, and you will start ignoring it. An ignored test is worse than no test.

So instead of *"output must equal this exact string,"* you check things like:

- Does the JSON parse?
- Are all required fields present?
- Does it avoid these banned phrases?
- Does it include these section headings?

Those hold true across reasonable variation, and fail when something is actually broken.

### Tagging taxonomy

**Plain definition:** A small, fixed set of tags so prompts are findable by more than just their title.

**Why keep it small:** A tag list that grows without limit becomes useless. If every prompt has unique tags, tags are not helping anyone search.

Aim for 2–4 tags per prompt: one domain, one task type, and optionally a risk level.

### Drift

**Plain definition:** A prompt's real-world quality getting worse over time — **without the prompt text changing at all.**

**How that happens:** Your provider updates the model. The prompt is byte-for-byte identical. The output is subtly different, and worse for your use case.

**Why it is dangerous:** Nothing in your git history shows a change, so there is nothing to point at. You only find it by re-running your test cases regularly, not just when you write them.

### Prompt owner

**Plain definition:** The person or team accountable for a catalog entry being correct and current. Same idea as a code owner.

**Why name one:** Without an owner, every prompt slowly becomes nobody's job, and the catalog rots back into the chat-history situation Asha started with.

---

## Naming conventions

```
<domain>-<task>-<variant>-v<major>
```

Examples:

```
bugfix-root-cause-v1
status-standup-v1
ecommerce-schema-design-v1
trading-compliance-check-v1
```

**The rules:**

- All lowercase, hyphen-separated, no spaces.
- `<domain>` — the area: `bugfix`, `status`, `research`, `ecommerce`, `trading`, `dating`, `review`.
- `<task>` — the specific job it does.
- `<variant>` — optional. Use when you have genuinely different approaches to the same task: `-fewshot`, `-cot`.
- `-v<major>` — matches the MAJOR version only.

**Why does the filename only carry the MAJOR version?**

So references stay stable. If someone's script points at `bugfix-root-cause-v1`, they keep getting v1 behaviour through every patch and minor update. They only have to think about it when you ship v2 — which is exactly when they *should* think about it, because that is when the output shape changed.

---

## Sample catalog entry

Full 20+ entry example: [`templates/catalog.json`](./templates/catalog.json). Each entry looks like this:

```json
{
  "id": "bugfix-root-cause-v1",
  "title": "Root Cause Hypothesis",
  "description": "Diagnoses a failing test/stack trace and proposes ranked fixes.",
  "tags": ["debugging", "bugfix", "backend"],
  "version": "1.2.0",
  "author": "asha.k",
  "last_modified": "2026-01-10",
  "test_cases": ["Given a NullReferenceException stack trace + diff, returns 3 ranked fixes with code"],
  "example_output_hash": "sha256:PLACEHOLDER_HASH_0001"
}
```

**Two fields worth explaining:**

**`test_cases`** — in this sample catalog it is a plain-English one-liner, to keep the example readable. In a real setup you would point at an actual test file instead.

**`example_output_hash`** — a hash of a known-good output from a "golden" run. This is your drift detector. If you re-run the prompt months later and the output is materially different, comparing against this tells you something changed on the provider's side even though your prompt did not.

---

## Tagging taxonomy

| Category | Example tags |
|---|---|
| Domain | `bugfix`, `status`, `research`, `ecommerce`, `trading`, `dating`, `review` |
| Task type | `debugging`, `summarization`, `generation`, `classification`, `comparison` |
| Risk level | `low-risk`, `customer-facing`, `financial`, `safety-critical` |
| Technique | `few-shot`, `chain-of-thought`, `output-schema` |

---

## CI integration (pseudocode)

This is deliberately provider-agnostic. Swap in whatever SDK your CI uses.

```yaml
# .github/workflows/prompt-tests.yml (pseudocode)
name: prompt-regression-tests

on:
  pull_request:
    paths:
      - 'templates/**'
      - 'prompts/**'

jobs:
  test-prompts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run prompt test suite
        run: |
          for entry in $(jq -r '.prompts[].id' templates/catalog.json); do
            echo "Testing $entry..."
            # 1. Load the prompt text file for $entry
            # 2. Load its test_cases (input + expected shape/schema)
            # 3. Call the model API with the prompt + test input
            # 4. Validate SHAPE: does the output match the expected schema?
            #    Are required sections present? Any banned phrases?
            # 5. Fail the job if validation fails
            run-prompt-test --id "$entry" --catalog templates/catalog.json
          done
```

**What this actually catches in practice:**

1. **A prompt edit that breaks the output schema.** Someone removes "return only JSON" and every downstream parser breaks. The test catches it in the PR, not in production.

2. **Drift from a model update.** Your prompt did not change but the behaviour did. Only regular re-runs find this.

3. **A new prompt added with no test at all.** Fail the build if a new catalog entry has an empty `test_cases` array. Otherwise untested prompts accumulate quietly.

---

## Example prompts (6)

### 1. Catalog entry drafting prompt

**Purpose:** Turns a working prompt into a proper catalog entry.

```
Here is a prompt I use successfully: [paste prompt text]. Draft a
catalog.json entry for it following this schema: id, title, description,
tags (2-4 from this taxonomy: [paste taxonomy]), version starting at
1.0.0, and one test case describing expected output shape (not exact text).
```

**Why it works:** Formalising a prompt is tedious, so people skip it. Offloading the mechanical part means it actually gets done.

### 2. Test-case-shape prompt

**Purpose:** Writes a shape-based test instead of a brittle exact-match one.

```
For this prompt: [paste prompt], and this example input: [paste input],
write a test case that checks the STRUCTURE of a correct output (required
fields, format, banned phrases) rather than exact wording, since LLM
output varies between runs.
```

**Why it works:** It builds the chapter's main lesson into the tool itself, so you avoid the beginner mistake without having to remember to avoid it.

### 3. Version-bump classifier prompt

**Purpose:** Decides PATCH vs MINOR vs MAJOR.

```
Here is the old version of a prompt: [paste old], and the new version:
[paste new]. Classify this change as PATCH (wording only), MINOR (new
non-breaking capability), or MAJOR (output format/behavior change that
would break existing callers). Justify in one sentence.
```

**Why it works:** Applying semver to prose is genuinely ambiguous. Reasoning it out explicitly gives more consistent decisions than eyeballing it — especially across a team where different people would judge it differently.

### 4. Drift-detection prompt

**Purpose:** Compares a fresh output against a known-good one.

```
Here is a golden (previously verified correct) output for this prompt
and input: [paste golden output]. Here is a fresh output from the same
prompt and input, run today: [paste fresh output]. Are these materially
different in meaning, structure, or correctness? Ignore purely stylistic
wording differences.
```

**Why it works:** "Ignore stylistic differences" is the key instruction. It separates *the words changed* (normal, ignore it) from *the meaning or structure changed* (a real regression).

### 5. Catalog search prompt

**Purpose:** Helps a teammate find an existing prompt instead of writing a duplicate.

```
Here is our prompt catalog: [paste catalog.json or relevant excerpt].
I need to [describe task]. Which existing catalog entry is the closest
match, and what (if anything) would I need to adapt?
```

**Why it works:** This directly prevents Asha's original problem — three near-duplicate prompts and no clear current one.

### 6. Deprecation prompt

**Purpose:** Retires an old version cleanly.

```
This catalog entry is being superseded: [paste old entry]. Draft a
deprecation note (one paragraph) explaining why, what replaces it
([new id]), and a migration note for anyone still using the old version.
```

**Why it works:** Deprecating something without writing down *why* is how the "which one do I use?" confusion comes back six months later.

---

## Lab exercise (step-by-step)

1. Take the template you saved at the end of [Chapter 3](./chapter-03-prompt-design-patterns.md).
2. Run Prompt #1 to draft a full catalog entry for it.
3. Run Prompt #2 to write a shape-based test case.
4. Add both to a local `catalog.json`, or to [`templates/catalog.json`](./templates/catalog.json) if you are contributing back.
5. Make one small wording edit to the prompt. Run Prompt #3 to classify it as PATCH, MINOR, or MAJOR. Bump the version accordingly.

---

## Expected outputs

```json
{
  "id": "bugfix-flaky-test-diagnosis-v1",
  "title": "Flaky Test Diagnosis",
  "description": "Diagnoses intermittent test failures from logs across multiple runs.",
  "tags": ["debugging", "bugfix", "testing"],
  "version": "1.0.0",
  "author": "your.name",
  "last_modified": "2026-XX-XX",
  "test_cases": ["Given 3 runs of the same test with 1 failure, identifies timing/ordering as likely cause rather than logic error"],
  "example_output_hash": "sha256:PLACEHOLDER"
}
```

And a version decision that reads something like:

> Changed "list 3 causes" to "list up to 5 causes ranked by likelihood."
> This is **MINOR** (1.0.0 → 1.1.0): it adds a capability (ranking), the
> output still parses the same way, and existing callers still get a
> valid list.

---

## Reflection questions

1. How many good prompts do you have scattered across chat history, notes, and Slack right now? What would it take to formalise the top 3?
2. What would a MAJOR version change look like in your domain — something that would genuinely break a downstream consumer?
3. Who should own your team's catalog: one person, a rotating role, or everyone? What breaks in each case?

---

## Further reading

- Semantic Versioning spec — semver.org (adapted here for prompts)
- Provider docs on prompt caching and versioning features *(placeholder link)*
- Next: [`chapter-05-workflows.md`](./chapter-05-workflows.md) — wiring this catalog into real workflows and CI

---

## Quiz (5 MCQs)

**1. What triggers a MAJOR version bump?**
- A) Any edit at all
- B) A wording tweak with no behaviour change
- C) An output format or behaviour change that would break existing callers
- D) Adding a new tag

> **Answer: C.**

**2. Why do prompt tests check output shape rather than exact text?**
- A) Shape checks are easier to write
- B) LLM output varies between runs, so exact-match tests fail on harmless rewording — and a test that cries wolf gets ignored
- C) Exact matching is not supported by testing tools
- D) Shape checks run faster

> **Answer: B.**

**3. What is "drift"?**
- A) Tags becoming outdated
- B) Output quality getting worse over time because the model changed, while the prompt text stayed identical
- C) A prompt being used by the wrong team
- D) A version number going backwards

> **Answer: B.**

**4. In `bugfix-root-cause-v1`, why does the filename carry only the MAJOR version?**
- A) It is the creation date
- B) So references stay stable through patches and minors, and only break deliberately at a MAJOR change
- C) It is a random identifier
- D) It counts the test cases

> **Answer: B.**

**5. What is `example_output_hash` for?**
- A) Encrypting the prompt
- B) Pinning a known-good output so silent drift from a model update can be detected later
- C) Speeding up API calls
- D) It is required by all providers

> **Answer: B.**

---

← [Chapter 3 — Prompt Design Patterns](./chapter-03-prompt-design-patterns.md) · [Learning path](./learning-path.md) · Next: [Chapter 5 — Workflows](./chapter-05-workflows.md)
