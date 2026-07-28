--- filename: chapter-template.md ---

# Chapter Template

← [Back to README](./README.md)

This is the reusable structure every chapter in this repo is built from. If you're writing a new chapter (see [`CONTRIBUTING.md`](./CONTRIBUTING.md)), copy this file and fill in each section. Keep Asha as the protagonist unless you have a good reason not to — consistency of story is what makes the path easy to follow.

---

```markdown
# Chapter N — <Title>

← [Previous chapter](./chapter-0N-minus-1.md) · [Learning path](./learning-path.md) · [Next chapter](./chapter-0N-plus-1.md)

## Narrative

<2–4 paragraphs. Asha hits a concrete, specific problem — not an abstract one.
Show her *old* habit (Google search, Stack Overflow, trial-and-error) failing or
being slow. End the narrative at the moment she reaches for a better approach —
don't resolve it yet; the chapter body is the resolution.>

## Learning objectives

By the end of this chapter you will be able to:
1. <Objective — a verb + a concrete, checkable skill>
2. <Objective>
3. <Objective>

## Key concepts

- **<Term>** — <one-sentence plain-English definition>
- **<Term>** — <definition>
- **<Term>** — <definition>
(3–6 terms, only what's needed for this chapter — define once, reuse everywhere)

## Example prompts (6)

For each: purpose, prompt text with `[placeholders]`, and a one-line note on
why it works.

### 1. <Prompt name>
**Purpose:** <what problem this solves>
```
<prompt text with [placeholders]>
```
**Why it works:** <one sentence>

### 2–6. <repeat the same shape>

## Lab exercise (step-by-step)

1. <Step — something the reader actually does, not just reads>
2. <Step>
3. <Step>
4. <Step — should produce a concrete artifact: a file, a diff, a decision>

## Expected outputs

<Show what a correct run of the lab looks like — a sample output block, a
before/after diff, or a filled-in template. This is how the reader checks
their own work.>

## Reflection questions

1. <Question that connects this chapter's skill back to the reader's real work>
2. <Question>
3. <Question>

## Further reading

- <Placeholder — link to official model docs>
- <Placeholder — link to a relevant paper or blog post>
- <Placeholder — link to the next logical chapter or template>

## Quiz (5 MCQs)

**1. <Question>**
- A) <option>
- B) <option>
- C) <option>
- D) <option>
> Answer: <letter> — <one-line justification>

**2–5.** <same shape>

---

← [Previous chapter](./chapter-0N-minus-1.md) · [Learning path](./learning-path.md) · [Next chapter](./chapter-0N-plus-1.md)
```

---

## Notes on filling this in

- **Narrative length:** 150–250 words. It should read like the opening of a short story, not a case study abstract.
- **Example prompts:** always 6, always with placeholders in `[square brackets]`, always copy-paste ready — no "..." or "etc." inside the prompt text itself.
- **Lab exercise:** must produce something the reader can point at afterward (a file, a diff, a filled template). "Read and understand" is not a lab step.
- **Quiz:** test the concept, not the trivia. A reader who skimmed the chapter but didn't do the lab should get 2–3 out of 5, not 5 out of 5.
- **Word count target:** 800–1,500 words for a standard chapter; case studies run 1,500–3,000 words and use a different template (see any of the three case-study files for that shape).

← [Back to README](./README.md)
