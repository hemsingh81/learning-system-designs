--- filename: CONTRIBUTING.md ---

# Contributing

← [Back to README](./README.md)

Thanks for considering a contribution. This repo stays useful because it stays practical, consistent, and honest about tradeoffs — the guidelines below exist to protect that, not to add process for its own sake.

## Ways to contribute

- **Fix an error** — a broken link, a factual mistake, a prompt that doesn't actually produce the claimed output.
- **Add a prompt template** to an existing `templates/` file, following that file's established format.
- **Add a catalog entry** to [`templates/catalog.json`](./templates/catalog.json) for a prompt you've found genuinely useful and tested.
- **Add a new chapter** using [`chapter-template.md`](./chapter-template.md), if you're covering ground the existing path doesn't (propose it as an issue first — see below).
- **Improve an existing chapter's exercises, examples, or clarity.**

## Before you start

For anything beyond a small fix (typo, broken link, one prompt tweak), **open an issue first** describing what you want to add or change and why. This avoids duplicated effort and lets us align on scope before you invest time in a full PR.

## Content guidelines

1. **Keep Asha consistent.** She's a senior software engineer, search-first by habit, learning prompt-first discipline. Don't introduce a second protagonist or change her established background without discussion.
2. **Every prompt must be copy-paste ready.** No `...` or `etc.` inside prompt text itself — use `[placeholders]` for anything that varies.
3. **Every prompt needs purpose + example + expected output format + why it works** (or the safety/guardrail note, for higher-risk domains). See any file in `templates/` for the pattern.
4. **Use relative links matching exact filenames.** `./chapter-04-prompt-management.md`, not `chapter-04.md` or an absolute URL.
5. **Follow the chapter template** ([`chapter-template.md`](./chapter-template.md)) exactly for new chapters — narrative, objectives, key concepts, 6 example prompts, lab, expected outputs, reflection questions, further reading, 5-question quiz.
6. **State tradeoffs honestly.** If a technique has a real cost or failure mode, say so in the same breath as its benefit — this repo's credibility depends on not overselling AI-assisted workflows.
7. **Guardrails are not optional for risk-bearing domains.** If your addition touches finance, health, safety, or fairness-sensitive content (in the spirit of Chapters 7-8), it needs an explicit guardrails section, not just a working example.

## Pull request template

```markdown
## What this PR does
[One or two sentences]

## Which file(s) it touches
[List]

## Type of change
- [ ] Fix (typo, broken link, factual correction)
- [ ] New prompt template / catalog entry
- [ ] New or updated chapter content
- [ ] Other (describe)

## Checklist
- [ ] Prompts are copy-paste ready with [placeholders], no "..."
- [ ] Internal links use exact relative filenames and were verified to resolve
- [ ] New prompts include purpose, example input, expected output format, and why-it-works (or guardrails, if risk-bearing)
- [ ] Asha's story/background is consistent with existing chapters (if narrative content)
- [ ] Ran a spell/grammar check
```

## Issue template

```markdown
## Type
- [ ] Bug (broken link, factual error, prompt that doesn't work as described)
- [ ] Content proposal (new chapter, new template file, new case study)
- [ ] Question / discussion

## Description
[What's wrong, or what you're proposing]

## Where
[File(s) affected, or where you'd propose new content living]

## Proposed fix / addition (if you have one)
[Optional — sketch it out if you already have an idea]
```

## Style notes

- Markdown only. Code blocks use triple backticks with a language tag where applicable.
- Tables where a comparison is genuinely tabular (don't force prose into a table, or a table into prose).
- Prefer concrete, specific examples over abstract descriptions — this repo's whole premise is that specificity is what makes a prompt actually work.

## Code of conduct

Be direct and be kind — critique the content, not the contributor. This is a technical repo about a fast-moving field; disagreement about the "right" way to prompt or structure something is expected and welcome, as long as it's argued from evidence or reasoning, not asserted from authority. Harassment, personal attacks, or dismissive gatekeeping toward newer contributors will result in the contribution being closed and, if repeated, the contributor being blocked.

---

← [Back to README](./README.md)
