--- filename: chapter-05-workflows.md ---

# Chapter 5 — Integrating Prompts into Dev Workflows

← [Chapter 4 — Prompt Management](./chapter-04-prompt-management.md) · [Learning path](./learning-path.md) · Next: [Chapter 6 — Case Study: E-commerce](./chapter-06-case-study-ecommerce.md)

## Narrative

The catalog works. Asha's team has a shared, versioned set of prompts. Nobody asks "which version did you use?" any more.

But she notices something else.

Everyone still runs these prompts **by hand**. Someone opens a chat window, pastes a prompt, pastes a diff, copies the answer back. The PR description prompt gets used maybe half the time — whenever someone remembers it exists.

She thinks about the linter. Nobody *remembers* to run the linter. It runs on its own, and it tells you about a problem before you can ignore it.

That is what she wants for prompts. And getting there needs three things she has not thought about yet:

1. **Trigger points** — when does this run, automatically?
2. **Review gates** — who checks the output before it goes anywhere?
3. **Guardrails** — what happens when the model gets it wrong and nobody is watching?

This chapter is about that wiring. Not "can an LLM help" — she already knows it can. The question now is how this becomes a dependable part of how the team ships software.

---

## Learning objectives

By the end of this chapter you will be able to:

1. Find at least 3 points in a normal dev workflow where a prompt can replace manual work.
2. Design a human review gate for AI-generated output.
3. Name the guardrails needed before a prompt runs unattended in CI.

---

## Key concepts

### Trigger point

**Plain definition:** The workflow event that runs a prompt automatically. A git push. A PR being opened. A release tag.

**Why it matters:** "Remember to run the prompt" is not a process. It is a hope. A trigger point turns a good intention into something that happens whether or not anyone is thinking about it.

### Review gate

**Plain definition:** A required human checkpoint between AI output and anything that ships, merges, or gets sent to a customer.

**The rule that decides how strict it should be:** match it to blast radius (next concept). Not every output needs the same scrutiny, and treating them all the same means either wasting time on trivia or under-checking the dangerous things.

### Blast radius

**Plain definition:** How much damage a wrong output causes if nobody catches it.

Some examples, roughly ordered:

| Output | If it is wrong | Blast radius |
|---|---|---|
| A commit message | Mildly annoying, easily fixed | Near zero |
| A PR description | Reviewer is briefly confused | Low |
| An auto-merged security fix | You shipped a vulnerability | High |
| A customer-facing financial disclaimer | Legal and trust problem | Very high |

**Why this is the central idea of the chapter:** everything else — how strict the gate is, whether it can run unattended, what guardrails you need — follows from this one judgement.

### Unattended execution

**Plain definition:** A prompt running in CI where its output takes effect with **no human looking at it first**.

Example: a prompt that auto-labels incoming issues. Nobody reviews each label.

**Why it needs more care:** With a human in the loop, a wrong output is caught by that human. Unattended, a wrong output just happens. So the guardrails have to do the job the human would have done.

### Guardrail

**Plain definition:** A hard check that stops bad output before it causes damage.

Common ones:

- **Schema validation** — does the output parse and have the required fields?
- **Banned-phrase check** — does it contain something it must never say?
- **Confidence threshold** — did the model flag uncertainty?
- **Mandatory dry-run** — show what it *would* do without doing it.
- **Automatic escalation** — on failure, tell a human instead of continuing.

### Fallback behaviour

**Plain definition:** What the workflow does when the prompt step fails, times out, or returns garbage.

**The wrong answer:** nothing happens, silently.

**The usually-right answer:** block and notify — for anything above near-zero blast radius.

The reason silent failure is so bad is that it looks identical to success. A pipeline that quietly skipped its safety check looks exactly like a pipeline that ran it and passed.

---

## Where prompts fit in a normal workflow

| Stage | Trigger | Candidate prompt | Blast radius | Review gate? |
|---|---|---|---|---|
| Local dev | Pre-commit hook | Commit message generator | Low | Optional — author edits before committing |
| PR creation | Push / PR opened | PR description generator | Low–Medium | Author reviews before requesting review |
| Code review | PR opened/updated | Style-guide diff checker | Medium | Posted as a comment, not a merge blocker |
| Pre-merge | CI on PR | Test coverage gap suggester | Medium | Reviewer sees it and decides |
| Release | Tag pushed | Release notes generator | Medium–High | Release manager reviews before publishing |
| Incident | Manual | Incident report drafter | High (external comms) | **Required** human sign-off |
| Production hotfix | Manual only | Root-cause diagnostic | High | **Never auto-applies a fix** |

**Read down the last two columns.** The pattern is consistent: the more visible or irreversible the output, the more mandatory the gate.

A wrong commit message is an annoyance. A wrong customer-facing incident report is a trust problem you cannot take back.

---

## Example prompts (6)

### 1. Pre-commit PR description prompt

**Purpose:** Runs at push time. Gives the author a draft to edit instead of a blank box.

```
Generate a PR description from this diff and linked ticket. Sections:
Summary (2-3 sentences), Changes (bulleted), Testing (how was this
verified), Risk (what could this break, if anything).

Diff: [paste diff]
Ticket: [paste ticket title/description]
```

**Why it works:** Low blast radius makes this the right *first* automation. The author edits it before anyone else sees it, so a bad draft costs nothing.

**Start here.** Build trust in the pipeline on something harmless before automating anything that matters.

### 2. Code review style-guide prompt

**Purpose:** Posted as an automated PR comment. Not a merge blocker.

```
Review this diff against our style guide below. Flag violations only —
do not comment on things the style guide doesn't cover. For each flag,
cite the specific style guide rule and line number in the diff.

Style guide: [paste or link style guide]
Diff: [paste diff]
```

**Why it works:** "Flag violations only, cite the specific rule" prevents the classic failure — an AI reviewer leaving vague opinion-based nitpicks. Once people start ignoring the bot's comments, the tool is worse than useless, because now real findings get ignored too.

Requiring a citation means every comment is checkable.

### 3. Merge-gate risk classifier prompt

**Purpose:** Helps a reviewer decide which PRs need the closest look.

```
Classify the blast radius of this diff as LOW, MEDIUM, or HIGH based on:
does it touch auth, payments, or data deletion; does it change a public
API; does it have test coverage for the changed lines. Justify in one
sentence per factor.

Diff: [paste diff]
Test coverage report: [paste or describe]
```

**Why it works:** Right now, how carefully a PR gets reviewed depends on who is reviewing and how busy they are. This makes it a stated judgement based on named factors.

### 4. Release notes gate prompt

**Purpose:** Drafts customer-facing notes, explicitly for sign-off.

```
Draft customer-facing release notes from this internal changelog. Rules:
no internal ticket IDs, no internal service names, no engineering jargon,
group by user-visible impact (New, Improved, Fixed). Mark this draft
"NEEDS REVIEW — do not publish without sign-off."
```

**Why it works:** The "NEEDS REVIEW" marker is a small thing that does real work. Someone has to visibly delete that line to publish. It cannot be published by accident.

### 5. CI failure guardrail prompt

**Purpose:** Defines what happens when the prompt step itself fails.

```
Given this prompt's expected output schema: [paste schema], and this
actual output: [paste output], validate: does it parse? are all required
fields present? does it contain any of these banned phrases: [list]?
Return PASS or FAIL with a one-line reason. On FAIL, this pipeline step
should block, not silently continue.
```

**Why it works:** It puts "fail loudly" into the actual output the pipeline branches on — not just into a design doc that everyone agreed with and nobody implemented.

### 6. Escalation prompt

**Purpose:** What a failed unattended step should do next.

```
This automated step failed validation: [paste failure reason]. Draft a
short, specific notification for the on-call engineer: what failed, what
the input was, what manual action is needed, and a link placeholder for
the pipeline run. Do not attempt to fix the underlying issue yourself.
```

**Why it works:** That last sentence is the important one.

An unattended step that tries to fix its own failure is making an unsupervised decision at exactly the moment it has already demonstrated it is not working correctly. Its job when it fails is to hand over clearly — nothing else.

---

## Lab exercise (step-by-step)

1. Pick one prompt from your Chapter 4 catalog.
2. Using the workflow table above, decide its **trigger point** and **blast radius**.
3. If it is Low–Medium: design a review gate. Where does a human see the output before it is used?
4. If you were going to run it unattended: write the guardrail check (Prompt #5 style) that validates its output before the pipeline continues.
5. Write the escalation behaviour (Prompt #6 style) for when that guardrail fails.
6. Sketch the pipeline step that ties it together. Pseudocode is fine — follow the CI example in [Chapter 4](./chapter-04-prompt-management.md).

---

## Expected outputs

```
Prompt:        pr-description-v1
Trigger:       PR opened
Blast radius:  Low (author reviews before submitting)

Review gate:
  Draft goes into the PR description field. Author must edit or confirm
  before requesting review. Never auto-submitted as final.

Guardrail (if run unattended as a "suggested description" comment):
  - Output must be valid Markdown
  - Must include all 4 sections (Summary, Changes, Testing, Risk)
  - Must not exceed 400 words
  - On FAIL: do not post the comment, log a warning, continue the
    pipeline (stakes are low enough that a missing draft is fine)

Escalation:
  None needed at this blast radius. A failed draft just means no comment
  is posted, and a human writes the description manually — which is
  exactly what happens today.
```

Notice that last part. **Not every failure needs an escalation.** Matching the response to the blast radius is the skill — paging someone at 3 a.m. because a PR description draft failed is how people learn to ignore pages.

---

## Reflection questions

1. Which stage in your workflow is most *tempting* to automate first? Is that actually the lowest-risk place to start, or just the most annoying manual task? Those are often not the same.
2. Think of a time an automated tool failed silently and caused a problem later. What guardrail would have caught it?
3. Should an AI reviewer's comments be able to block a merge, or only advise? What would change your answer?

---

## Further reading

- CI/CD guardrail patterns *(placeholder link)*
- Human-in-the-loop system design *(placeholder link)*
- Next: pick a case study — [E-commerce](./chapter-06-case-study-ecommerce.md), [Trading](./chapter-07-case-study-trading.md), or [Dating](./chapter-08-case-study-dating.md) — to see all of this working end to end

---

## Quiz (5 MCQs)

**1. What decides how strict a review gate should be?**
- A) How long the prompt is
- B) Blast radius — how much damage a wrong output causes if unreviewed
- C) Which provider you use
- D) What time the pipeline runs

> **Answer: B.**

**2. Why is "posted as a comment, not a merge blocker" a good default for an AI code reviewer?**
- A) AI reviewers are never accurate enough to matter
- B) It balances catching real issues against the risk that opinion-based nitpicking gets the bot ignored entirely
- C) GitHub cannot block merges
- D) Only humans may comment on PRs

> **Answer: B.**

**3. On FAIL, what should the CI guardrail do?**
- A) Continue silently
- B) Block the step and surface the failure
- C) Automatically retry with a different model
- D) Delete the output and try again with no record

> **Answer: B.**

**4. Why does the escalation prompt say "do not attempt to fix the underlying issue yourself"?**
- A) To keep it short
- B) Because a step that just failed should not then make an unsupervised decision — its job is to hand over clearly
- C) For professionalism
- D) There is no such instruction

> **Answer: B.**

**5. Which is the lowest blast radius, and therefore the best first automation?**
- A) Auto-publishing customer-facing incident reports
- B) Production hotfix generation
- C) Pre-commit commit message generation, editable by the author
- D) Auto-merging security fixes

> **Answer: C.**

---

← [Chapter 4 — Prompt Management](./chapter-04-prompt-management.md) · [Learning path](./learning-path.md) · Next: [Chapter 6 — Case Study: E-commerce](./chapter-06-case-study-ecommerce.md)
