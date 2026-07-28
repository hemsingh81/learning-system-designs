--- filename: README.md ---

# Prompt Engineering for Software Engineers

**From "Google it and copy-paste" to systematic, testable prompt engineering — told through one engineer's journey.**

---

## What this is

A practical, GitHub-ready tutorial for **experienced software engineers** who have spent years solving problems by searching Google, skimming Stack Overflow, and copy-pasting fixes. It teaches a different habit: treating prompts to an LLM as **engineered artifacts** — designed, versioned, tested, reviewed, and reused — the same way you already treat code.

The whole repo follows one protagonist, **Asha**, a senior engineer who is good at her job and bad at explaining why her "just Google it" instinct is starting to slow her down. Every chapter opens with the problem she's facing, shows her old habit, and then shows the prompt-engineering habit that replaces it. The case studies (e-commerce, trading, dating) are three projects she builds using nothing but disciplined prompting.

This is not a prompt-collection dump. It is a **learning path with a story**, followed by **reusable templates** you can copy into your own repo on day one.

---

## Who this is for

- Engineers with 3+ years of experience who are strong at traditional debugging and weak at getting consistent, high-quality output from an LLM.
- Tech leads who want a repeatable way to bring prompt engineering into a team's workflow — not just individual chat sessions.
- Anyone hiring for or building toward a "Prompt Engineer" or "PromptOps" role and wants a concrete picture of what the job actually involves.

## What you will be able to do after this

- Diagnose a bug using a **structured diagnostic prompt** instead of forty browser tabs.
- Design prompts with a repeatable **anatomy** (role, context, task, constraints, output format) instead of trial and error.
- **Version, tag, and test** prompts like code, with a catalog and a CI check.
- Run an end-to-end project — planning, schema, API, frontend, tests, release notes — using an **orchestrated sequence of prompts**, not one giant "build me an app" request.
- Evaluate prompt output for **correctness, hallucination risk, safety, and latency**, and know what "good" looks like.

---

## How to use the learning path

1. Read [`learning-path.md`](./learning-path.md) first — it maps all 10 chapters to Asha's story, with objectives and time estimates.
2. Work through Chapters 1–5 in order. They build on each other (mindset → foundations → patterns → management → workflow integration).
3. Pick **one** case study (Chapters 6–8) that's closest to your own domain, or read all three to see how the same discipline adapts to very different constraints (e-commerce vs. trading vs. dating).
4. Keep `templates/` open in a second tab while you work — copy prompts directly into your own projects.
5. Use `appendix-best-practices.md` as your ongoing checklist once you've finished the path.

**Quick start (30 minutes):** Read `chapter-01-assumptions.md`, then run the 3 exercises in `chapter-02-foundations.md`. You'll already be prompting differently by the end of the hour.

---

## Table of contents

### Learning path
| File | Description |
|---|---|
| [`learning-path.md`](./learning-path.md) | Full 10-chapter path, mapped to Asha's story, with objectives, exercises, and time estimates |
| [`chapter-template.md`](./chapter-template.md) | The reusable template every chapter is built from (useful if you want to write your own chapter) |

### Chapters
| File | Description |
|---|---|
| [`chapter-01-assumptions.md`](./chapter-01-assumptions.md) | Who this is for, and the mindset shift from search-first to prompt-first |
| [`chapter-02-foundations.md`](./chapter-02-foundations.md) | Core concepts and mental models for working with LLMs |
| [`chapter-03-prompt-design-patterns.md`](./chapter-03-prompt-design-patterns.md) | Prompt anatomy, the prompt lifecycle, and reusable patterns |
| [`chapter-04-prompt-management.md`](./chapter-04-prompt-management.md) | Versioning, tagging, testing, and prompt catalogs |
| [`chapter-05-workflows.md`](./chapter-05-workflows.md) | Integrating prompts into dev workflows, CI, and code review |
| [`chapter-06-case-study-ecommerce.md`](./chapter-06-case-study-ecommerce.md) | Case study: an e-commerce app, start to end |
| [`chapter-07-case-study-trading.md`](./chapter-07-case-study-trading.md) | Case study: a trading platform prototype, start to end |
| [`chapter-08-case-study-dating.md`](./chapter-08-case-study-dating.md) | Case study: a dating site MVP, start to end |

### Templates (copy-paste ready)
| File | Description |
|---|---|
| [`templates/prompts-bug-fix.md`](./templates/prompts-bug-fix.md) | 12 ready-to-run prompts for diagnosing and fixing bugs |
| [`templates/prompts-status-email.md`](./templates/prompts-status-email.md) | 8 prompts for status updates, standups, incident reports, release notes |
| [`templates/prompts-research.md`](./templates/prompts-research.md) | 10 prompts for researching and summarizing new concepts |
| [`templates/catalog.json`](./templates/catalog.json) | Sample machine-readable prompt catalog with metadata |

### Reference
| File | Description |
|---|---|
| [`roles-and-jobs.md`](./roles-and-jobs.md) | 8 prompt-engineering role descriptions, skills, interview questions, hiring checklists |
| [`assets/image-prompts.md`](./assets/image-prompts.md) | Copy-paste image-generation prompts for diagrams and persona art |
| [`appendix-best-practices.md`](./appendix-best-practices.md) | Safety checklist, hallucination mitigation, evaluation rubric, 30-day plan |
| [`CONTRIBUTING.md`](./CONTRIBUTING.md) | How to contribute, PR template, issue template |
| [`CHANGELOG.md`](./CHANGELOG.md) | Version history and commit message conventions |
| [`LICENSE`](./LICENSE) | MIT License |

---

## Repo structure

```
Prompt-Engineering/
├── README.md
├── learning-path.md
├── chapter-template.md
├── chapter-01-assumptions.md
├── chapter-02-foundations.md
├── chapter-03-prompt-design-patterns.md
├── chapter-04-prompt-management.md
├── chapter-05-workflows.md
├── chapter-06-case-study-ecommerce.md
├── chapter-07-case-study-trading.md
├── chapter-08-case-study-dating.md
├── roles-and-jobs.md
├── appendix-best-practices.md
├── CONTRIBUTING.md
├── CHANGELOG.md
├── LICENSE
├── templates/
│   ├── prompts-bug-fix.md
│   ├── prompts-status-email.md
│   ├── prompts-research.md
│   └── catalog.json
└── assets/
    └── image-prompts.md
```

---

## A note on how the prompts are written

Every prompt template in this repo follows the same shape: **purpose → prompt text with `[placeholders]` → example input → expected output format → why it works**. That consistency is deliberate — it's the same "prompt anatomy" taught in Chapter 3, applied to itself.

Prompts are written to be **model-agnostic in spirit** (they'll work with any capable LLM) but tuned in examples for Claude, since that's what Asha uses throughout the story.

---

## License

[MIT](./LICENSE) — use, adapt, and redistribute freely, including in commercial training material. Attribution appreciated but not required.

---

## Suggested initial commit

```
chore: add prompt-engineering tutorial skeleton, learning path, templates, and case studies
```
