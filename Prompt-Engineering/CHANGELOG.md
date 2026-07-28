--- filename: CHANGELOG.md ---

# Changelog

← [Back to README](./README.md)

All notable changes to this repo are documented here. Format loosely follows [Keep a Changelog](https://keepachangelog.com/); versioning follows the repo's own content-versioning spirit from [Chapter 4](./chapter-04-prompt-management.md) — MAJOR for structural/breaking reorganization, MINOR for new chapters/templates, PATCH for fixes and small clarifications.

## [1.0.0] — 2026-07-28

### Added
- Initial repo skeleton: `README.md`, `learning-path.md`, `chapter-template.md`.
- Chapters 1-5 (mindset shift → foundations → design patterns → prompt management → workflows), each following the standard chapter template with 6 example prompts, a lab exercise, and a 5-question quiz.
- Three end-to-end case studies: E-commerce ([Chapter 6](./chapter-06-case-study-ecommerce.md)), Trading Platform ([Chapter 7](./chapter-07-case-study-trading.md)), Dating Site MVP ([Chapter 8](./chapter-08-case-study-dating.md)), each with a full prompt inventory, orchestration plan, testing plan, metrics, and sample project structure.
- `templates/prompts-bug-fix.md` — 12 bug-diagnosis prompts, including Python/JS/Java variants and unit-test generation variants.
- `templates/prompts-status-email.md` — 8 status/communication prompts (standup, sprint summary, incident report, release notes, and 4 more).
- `templates/prompts-research.md` — 10 research/summarization prompts.
- `templates/catalog.json` — sample 20-entry machine-readable prompt catalog with full metadata schema.
- `roles-and-jobs.md` — 8 role descriptions with responsibilities, skills, career ladders, plus a dedicated Hiring section with a checklist and 10 interview questions each for Prompt Engineer and PromptOps Engineer.
- `assets/image-prompts.md` — 12 copy-paste image-generation prompts covering persona art, architecture diagrams, and UI mockups.
- `appendix-best-practices.md` — safety checklist, hallucination-mitigation checklist, 4-dimension evaluation rubric, and a 30-day adoption plan.
- `CONTRIBUTING.md` — contribution guidelines, PR template, issue template, code of conduct.
- `LICENSE` — MIT.

### Notes
- This is the initial complete pass through the full learning path. Content is expected to evolve — see [`CONTRIBUTING.md`](./CONTRIBUTING.md) for how to propose changes.

---

## Suggested commit messages for this history

If committing this repo incrementally rather than as one initial commit, here's a suggested breakdown:

```
chore: add prompt-engineering tutorial skeleton, learning path, templates, and case studies

docs: add README and learning-path with full navigation
docs: add reusable chapter-template.md
docs: add chapters 1-2 (mindset shift, foundations)
docs: add chapters 3-4 (design patterns, prompt management)
docs: add chapter 5 (workflow integration)
docs: add e-commerce case study (chapter 6)
docs: add trading platform case study (chapter 7)
docs: add dating site case study (chapter 8)
docs: add bug-fix, status-email, and research prompt templates
docs: add sample prompt catalog.json
docs: add roles-and-jobs with hiring section
docs: add image generation prompts
docs: add best-practices appendix and 30-day plan
docs: add CONTRIBUTING guide and issue/PR templates
chore: add MIT LICENSE
```

For future changes, follow conventional commits: `docs:` for content, `fix:` for corrections, `feat:` for new templates/chapters, `chore:` for repo maintenance.

---

← [Back to README](./README.md)
