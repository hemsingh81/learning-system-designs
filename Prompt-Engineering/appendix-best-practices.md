--- filename: appendix-best-practices.md ---

# Appendix — Best Practices, Checklists, and the 30-Day Plan

← [Roles and Jobs](./roles-and-jobs.md) · [Learning path](./learning-path.md) · Back to [README](./README.md)

This is the reference material you'll come back to after finishing the learning path — the checklists to run before shipping a prompt, the rubric to score one against, and a 30-day plan for turning everything in this repo into a permanent habit.

---

## Prompt safety checklist

Run this before any new prompt ships, and especially before it runs unattended (per Chapter 5's guardrail framework):

- [ ] **Grounding:** Does the prompt provide actual source material for anything factual, or does it rely on the model's training-data memory for facts that matter? (Chapter 2)
- [ ] **Scope boundary:** Does the prompt explicitly state what it must NOT do (e.g., "no order execution code," "do not generate a response to the user")? (Chapters 5, 7, 8)
- [ ] **Output format:** Is the expected output shape explicit enough to validate automatically (schema, required sections, banned phrases)? (Chapter 3)
- [ ] **Blast radius classified:** Has someone explicitly decided Low/Medium/High blast radius, and does the review-gate strictness match? (Chapter 5)
- [ ] **Injection resistance:** If the prompt includes any user-supplied text, has it been checked against prompt-injection risk (see the e-commerce case study's Prompt #16)?
- [ ] **Failure behavior defined:** What happens when this prompt fails, times out, or returns invalid output? Is the fallback "block and escalate," not "silently continue"?
- [ ] **Sensitive-topic review:** If the prompt touches health, safety, finance, or protected attributes, has a domain specialist (not just engineering) reviewed it?

## Hallucination mitigation checklist

- [ ] Source material is pasted directly into the prompt wherever facts matter, not assumed from context.
- [ ] The prompt gives the model an explicit, safe way to say "I don't know" (e.g., "if not in the context, say 'Not found'").
- [ ] For anything customer-facing or decision-critical, a self-critique or independent-review pass (Chapter 3's self-critique pattern; the trading case study's independent-reviewer pattern) is included.
- [ ] Claims that look like facts (numbers, citations, API names, config values) are spot-checked against the actual source, not accepted on fluency alone.
- [ ] The prompt has been deliberately tested with an out-of-scope question to confirm it says "I don't know" rather than guessing (Chapter 2's lab exercise).

## Evaluation rubric

Score any prompt 1-5 on each dimension before considering it production-ready. A prompt scoring below 3 on any dimension needs work before shipping, regardless of how good its other scores are.

| Dimension | 1 (Poor) | 3 (Acceptable) | 5 (Excellent) |
|---|---|---|---|
| **Precision** | Frequently includes wrong/irrelevant content | Occasionally includes minor irrelevant content | Output consistently contains only what was asked for |
| **Recall** | Frequently misses required information | Usually captures required information | Reliably captures all required information, even in edge cases |
| **Safety** | No guardrails; can be steered off-purpose easily | Basic constraints present; occasional edge-case leaks | Explicit, tested guardrails; resistant to adversarial input |
| **Latency** | Unusably slow for its use case | Acceptable but noticeable delay | Fast enough that the workflow trigger point (Chapter 5) is genuinely seamless |

**How to use this rubric:** Score using real test cases from your catalog (Chapter 4), not a single anecdotal run. A prompt tested once and scored from memory isn't actually evaluated — it's a guess with a number attached.

---

## The 30-day plan

A realistic path from finishing this learning path to prompt engineering being a genuine, load-bearing habit — not a burst of enthusiasm that fades in two weeks.

### Week 1 — Build the habit
- [ ] Day 1-2: Complete Chapters 1-2 if not already done. Rewrite 3 recent search-first debugging sessions as structured prompts (Chapter 1's lab, repeated 3x for real muscle memory).
- [ ] Day 3-4: Complete Chapter 3. Build your first 2 reusable prompt templates from real, repeated tasks in your own work.
- [ ] Day 5: Score both templates against the evaluation rubric above. Fix whatever scores below 3.
- [ ] Weekend/buffer: Catch up if behind — this week is foundational, don't skip ahead with gaps.

### Week 2 — Formalize and share
- [ ] Day 8-9: Complete Chapter 4. Build a real `catalog.json` (or adapt [`templates/catalog.json`](./templates/catalog.json)) for your own team, seeded with the 2 templates from Week 1 plus at least 3 more from teammates.
- [ ] Day 10: Write shape-based test cases for every catalog entry — no entry ships without at least one.
- [ ] Day 11-12: Complete Chapter 5. Pick ONE low-blast-radius workflow trigger point (commit messages or PR descriptions are good starting points) and wire it in for real, even manually at first.
- [ ] Day 13-14: Share the catalog with your team. Get at least one teammate to use an existing entry instead of writing a prompt from scratch.

### Week 3 — Apply to a real project
- [ ] Day 15-17: Pick a real, current project. Run a lightweight version of a case-study orchestration plan (Chapters 6-8): planning prompt → design prompt → build → test prompts → release prompt.
- [ ] Day 18-19: For anything customer-facing or risk-bearing in that project, run the full safety checklist above before it ships.
- [ ] Day 20-21: Retrospective — what worked, what didn't, what would you change about your own prompt templates now that you've used them on something real.

### Week 4 — Institutionalize
- [ ] Day 22-24: Wire at least one prompt regression test into actual CI (Chapter 4's CI pattern), not just a manual checklist.
- [ ] Day 25-26: Present your catalog and workflow integration to your team or manager. Use the [status email templates](./templates/prompts-status-email.md) to draft the update.
- [ ] Day 27-28: Identify the gap — which of the 8 roles in [`roles-and-jobs.md`](./roles-and-jobs.md) is closest to what you actually want to grow into, and what's the one skill from that role's requirements you're weakest on?
- [ ] Day 29-30: Set a recurring cadence (weekly or biweekly) for catalog maintenance — reviewing drift, retiring stale entries, adding new ones. A catalog that isn't maintained decays back into scattered chat history within a quarter.

**The test of whether this worked:** thirty days from now, when you hit a bug, a status update, or a research question — do you reach for a catalog entry or a template first, before you reach for a search bar? That's the actual mindset shift from Chapter 1, made durable.

---

← [Roles and Jobs](./roles-and-jobs.md) · [Learning path](./learning-path.md) · Back to [README](./README.md)
