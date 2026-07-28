--- filename: learning-path.md ---

# The Learning Path

← [Back to README](./README.md)

Ten chapters, one story. Asha is a senior software engineer, eight years in, excellent at reading stack traces and terrible — by her own admission — at getting consistent value out of an LLM. She treats it like a smarter search engine: type a vague question, skim the answer, copy what looks right, move on. It works often enough that she never questioned it.

This path is what changes her mind, chapter by chapter, problem by problem.

---

## How to read this table

Each row is one chapter. **Time** is a realistic estimate including the exercises, not just reading. Chapters 1–5 are sequential — each depends on the last. Chapters 6–8 (the case studies) are independent of each other; read the one closest to your domain, or all three to see the same discipline flex across very different constraints. Chapters 9–10 are reference material you'll return to.

| # | Chapter | Time | Asha's situation | File |
|---|---|---|---|---|
| 1 | The Mindset Shift | 30 min | Loses two hours to a bug Google can't help with, realizes her habits are the bottleneck | [`chapter-01-assumptions.md`](./chapter-01-assumptions.md) |
| 2 | Foundations & Mental Models | 45 min | Learns *why* vague prompts fail — tokens, context windows, instruction-following, and what "hallucination" actually means | [`chapter-02-foundations.md`](./chapter-02-foundations.md) |
| 3 | Prompt Design Patterns | 60 min | Builds her first reusable prompt template instead of retyping the same request five different ways | [`chapter-03-prompt-design-patterns.md`](./chapter-03-prompt-design-patterns.md) |
| 4 | Prompt Management | 60 min | Her prompts start drifting and nobody on the team can tell which version fixed which bug — she builds a catalog | [`chapter-04-prompt-management.md`](./chapter-04-prompt-management.md) |
| 5 | Workflows & CI | 60 min | Wires prompt checks into code review and CI so prompt quality doesn't silently regress | [`chapter-05-workflows.md`](./chapter-05-workflows.md) |
| 6 | Case Study: E-commerce | 90 min | Builds a checkout flow end-to-end using an orchestrated sequence of prompts | [`chapter-06-case-study-ecommerce.md`](./chapter-06-case-study-ecommerce.md) |
| 7 | Case Study: Trading Platform | 90 min | Builds a trading prototype where a wrong prompt has real financial consequences | [`chapter-07-case-study-trading.md`](./chapter-07-case-study-trading.md) |
| 8 | Case Study: Dating Site | 90 min | Builds an MVP where fairness, privacy, and moderation are first-class requirements | [`chapter-08-case-study-dating.md`](./chapter-08-case-study-dating.md) |
| 9 | Roles & Careers | 30 min | Realizes this is now a job title, not just a skill, and maps out where she fits | [`roles-and-jobs.md`](./roles-and-jobs.md) |
| 10 | Best Practices & the 30-Day Plan | 30 min | Turns everything she's learned into a checklist she actually uses | [`appendix-best-practices.md`](./appendix-best-practices.md) |

**Total: ~9.5 hours** to complete the full path with exercises.

---

## Chapter-by-chapter detail

### Chapter 1 — The Mindset Shift
**File:** [`chapter-01-assumptions.md`](./chapter-01-assumptions.md)

**Learning objectives**
1. Name the specific habits that make search-first debugging slow (re-reading docs, re-typing the same question, losing context between tabs).
2. Explain the difference between "asking a question" and "engineering a prompt."
3. Identify at least 2 recent problems in your own work where a structured prompt would have saved real time.

**Hands-on exercises**
1. Take the last bug you fixed by Googling. Rewrite the search query as a structured prompt using the template in the chapter. Compare the time-to-answer.
2. Run the "root cause hypothesis" prompt (given in the chapter) against a real stack trace from your own codebase.
3. Write one paragraph: what does your team lose today because prompts aren't treated as reusable artifacts?

---

### Chapter 2 — Foundations & Mental Models
**File:** [`chapter-02-foundations.md`](./chapter-02-foundations.md)

**Learning objectives**
1. Explain context windows, tokens, and instruction-following in terms a backend engineer already understands (analogies to function scope, buffers, and API contracts).
2. Describe what causes hallucination and 3 concrete ways to reduce it.
3. Distinguish between a prompting failure and a model-capability failure.

**Hands-on exercises**
1. Ask the model an ambiguous question with no context, then the same question with full context. Diff the two answers.
2. Deliberately trigger a hallucination by asking for a fact outside the model's likely training data or asking it to invent a citation. Observe how it fails.
3. Rewrite a failing prompt using explicit constraints ("only use information provided below; say 'I don't know' if it's not here") and confirm the hallucination stops.

---

### Chapter 3 — Prompt Design Patterns
**File:** [`chapter-03-prompt-design-patterns.md`](./chapter-03-prompt-design-patterns.md)

**Learning objectives**
1. Apply the 5-part prompt anatomy (role, context, task, constraints, output format) to any request.
2. Use at least 3 named patterns (few-shot, chain-of-thought, role-play, output-schema, self-critique) appropriately.
3. Build one prompt template with placeholders you can reuse across a whole project.

**Hands-on exercises**
1. Take a one-line vague prompt ("fix my code") and rebuild it using the 5-part anatomy. Compare output quality.
2. Convert a free-text prompt into one with a strict JSON output schema. Verify the output actually parses.
3. Write a few-shot prompt with 3 examples for a repetitive task you do weekly (e.g., writing commit messages, PR descriptions).

---

### Chapter 4 — Prompt Management
**File:** [`chapter-04-prompt-management.md`](./chapter-04-prompt-management.md)

**Learning objectives**
1. Design a naming convention and versioning scheme for prompts.
2. Build a prompt catalog entry with full metadata (id, tags, version, test cases).
3. Explain how prompt regression testing works and why it matters.

**Hands-on exercises**
1. Take 3 prompts you've used this week and formalize them into `catalog.json` entries.
2. Write one test case per prompt (input → expected output shape, not exact text).
3. Sketch a CI step that would fail the build if a prompt's output no longer matches its schema.

---

### Chapter 5 — Workflows & CI
**File:** [`chapter-05-workflows.md`](./chapter-05-workflows.md)

**Learning objectives**
1. Identify 3 points in a normal dev workflow (PR creation, code review, release) where a prompt can replace manual work.
2. Design a review gate for AI-assisted code changes.
3. Explain the guardrails needed before letting a prompt-driven step run unattended in CI.

**Hands-on exercises**
1. Draft a PR description generator prompt and wire it (conceptually) into your git pre-push hook.
2. Write a code-review prompt that checks a diff against your team's style guide.
3. List 3 failure modes if this ran unattended and how you'd guard against each.

---

### Chapters 6–8 — Case Studies

Each case study follows the same shape: problem statement → requirements → prompt inventory → orchestration plan → testing plan → metrics → sample project tree. Pick based on your interest, or do all three back-to-back — the contrast is the point (an e-commerce app optimizes for speed and conversion, a trading platform optimizes for correctness and auditability, a dating site optimizes for fairness and privacy).

- [`chapter-06-case-study-ecommerce.md`](./chapter-06-case-study-ecommerce.md)
- [`chapter-07-case-study-trading.md`](./chapter-07-case-study-trading.md)
- [`chapter-08-case-study-dating.md`](./chapter-08-case-study-dating.md)

---

### Chapter 9 — Roles & Careers
**File:** [`roles-and-jobs.md`](./roles-and-jobs.md)

**Learning objectives**
1. Distinguish between 8 adjacent-but-different prompt-engineering roles.
2. Identify which role best matches your current skills and interests.
3. Prepare for a prompt-engineering interview using the included question bank.

**Hands-on exercises**
1. Map your last 6 months of work onto the responsibilities of the closest-matching role.
2. Answer 5 of the sample interview questions in writing.
3. Draft a one-paragraph "why I'd be good at this" pitch using your case-study work as evidence.

---

### Chapter 10 — Best Practices & the 30-Day Plan
**File:** [`appendix-best-practices.md`](./appendix-best-practices.md)

**Learning objectives**
1. Apply the safety and hallucination-mitigation checklists to a real prompt before shipping it.
2. Score a prompt against the evaluation rubric (precision, recall, safety, latency).
3. Commit to a 30-day plan to build the habit permanently.

**Hands-on exercises**
1. Run the full safety checklist against your most-used prompt.
2. Score 3 of your prompts against the rubric. Fix the lowest scorer.
3. Fill in Week 1 of the 30-day plan with real, dated tasks.

---

## Where to go after this

- Keep [`templates/`](./templates/prompts-bug-fix.md) open as a living reference — copy prompts directly into your own projects.
- Use [`assets/image-prompts.md`](./assets/image-prompts.md) if you want to illustrate your own version of this material (architecture diagrams, persona art, flowcharts).
- Read [`CONTRIBUTING.md`](./CONTRIBUTING.md) if you want to add a chapter, case study, or template back to this repo.

← [Back to README](./README.md)
