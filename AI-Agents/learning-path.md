# The Learning Path

← [The Story](00-the-story.md) · [Back to README](README.md)

Nine chapters, read in order — each needs the last. Then four case studies, readable in any order.

---

## The shape of every chapter

Same five parts as AI-Skills and AI-Workflows, so the habit carries over:

1. **Where you left off** — one paragraph, so you can start cold.
2. **What you'll learn** — two or three plain sentences.
3. **The lesson** — explained slowly, with analogies and real examples.
4. **Try it yourself** — a real, small exercise.
5. **What's still missing** — the exact gap the next chapter fills.

---

## The full path

| # | Chapter | Time | Where the story is | File |
|---|---|---|---|---|
| 1 | What Is an Agent? | 20 min | A five-angle workflow can't review a bug that doesn't have a diff yet | [`tutorial/01-what-is-an-agent.md`](tutorial/01-what-is-an-agent.md) |
| 2 | Anatomy of an Agent | 25 min | You look at a real agent loop and can't tell what decides its next step | [`tutorial/02-anatomy-of-an-agent.md`](tutorial/02-anatomy-of-an-agent.md) |
| 3 | Your First Agent | 40 min | You build one, and it's genuinely overkill for the task you picked | [`tutorial/03-your-first-agent.md`](tutorial/03-your-first-agent.md) |
| 4 | Tools and Grounding | 40 min | Your agent picks the wrong tool, confidently, and doesn't notice | [`tutorial/04-tools-and-grounding.md`](tutorial/04-tools-and-grounding.md) |
| 5 | Stopping Conditions and Budgets | 35 min | An agent keeps investigating something it already found the answer to | [`tutorial/05-stopping-conditions-and-budgets.md`](tutorial/05-stopping-conditions-and-budgets.md) |
| 6 | Agents vs. Other Tools | 30 min | Rahul asks why this isn't just a workflow with more phases | [`tutorial/06-agents-vs-other-tools.md`](tutorial/06-agents-vs-other-tools.md) |
| 7 | Testing and Iterating | 30 min | You're about to share this — but it never takes the same path twice | [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md) |
| 8 | Packaging and Sharing | 35 min | Vikram wants this pattern, but wants to know what it's allowed to touch | [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md) |
| 9 | Governance and Capstone | 30 min | An agent takes an action nobody explicitly approved | [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md) |

**Total: about 4.5 hours**, including every exercise.

---

## Chapter details

### Chapter 1 — What Is an Agent?
**File:** [`tutorial/01-what-is-an-agent.md`](tutorial/01-what-is-an-agent.md)

**You'll be able to:**
1. Explain what an agent is, and how it's different from a workflow, in your own words.
2. Name a real task on your team that a fixed workflow plan genuinely can't do well.
3. Explain why "just add more phases to the workflow" doesn't solve that problem.

**You'll try:** Take an open-ended task you've done recently — a bug you had to track down, an unfamiliar error you had to chase. Write down, in one sentence, why you couldn't have planned your exact steps in advance.

---

### Chapter 2 — Anatomy of an Agent
**File:** [`tutorial/02-anatomy-of-an-agent.md`](tutorial/02-anatomy-of-an-agent.md)

**You'll be able to:**
1. Read a real agent loop and understand every part of it.
2. Explain what a "goal" and a "stopping condition" are, and why an agent needs both.
3. Explain the difference between an agent's tools and a workflow's stages.

**You'll try:** Read a real agent loop (one is included) and, before checking the answer, predict what it would do differently on two different inputs.

---

### Chapter 3 — Your First Agent
**File:** [`tutorial/03-your-first-agent.md`](tutorial/03-your-first-agent.md)

**You'll be able to:**
1. Write a working agent with a real goal and a real loop.
2. Notice when a task doesn't actually need an agent — when the steps could have been planned in advance.
3. Name the first mistake almost everyone makes when they start.

**You'll try:** Build a tiny investigative agent. Then build the same task as a fixed workflow instead. Be honest about which one the task actually needed.

---

### Chapter 4 — Tools and Grounding
**File:** [`tutorial/04-tools-and-grounding.md`](tutorial/04-tools-and-grounding.md)

**You'll be able to:**
1. Give an agent a set of tools it can reliably choose correctly between.
2. Explain why a tool's description matters as much as a skill's trigger description did.
3. Recognise when an agent picked a plausible-sounding but wrong tool.

**You'll try:** Give your agent two tools with overlapping purposes. See if it picks correctly, and fix the descriptions until it does.

---

### Chapter 5 — Stopping Conditions and Budgets
**File:** [`tutorial/05-stopping-conditions-and-budgets.md`](tutorial/05-stopping-conditions-and-budgets.md)

**You'll be able to:**
1. Explain why an agent, unlike a workflow, can genuinely fail to stop on its own.
2. Set a real iteration and cost budget that catches this before it becomes expensive.
3. Recognise the difference between an agent making progress and an agent going in circles.

**You'll try:** Deliberately give your agent a goal it can't actually reach. Confirm your stopping condition catches it before it burns unbounded cost.

---

### Chapter 6 — Agents vs. Other Tools
**File:** [`tutorial/06-agents-vs-other-tools.md`](tutorial/06-agents-vs-other-tools.md)

**You'll be able to:**
1. Choose correctly between a skill, a workflow, a subagent, a hook, and an agent for a real task.
2. Explain why "a workflow with a lot of phases" isn't the same as an agent.
3. Explain, in one sentence, what makes an agent genuinely different — not just bigger.

**You'll try:** Take three real tasks from your own team. Assign each to a skill, a workflow, or an agent, and say why.

---

### Chapter 7 — Testing and Iterating
**File:** [`tutorial/07-testing-and-iterating.md`](tutorial/07-testing-and-iterating.md)

**You'll be able to:**
1. Test that an agent reaches the correct goal, even when it takes a different path each run.
2. Test that an agent's stopping condition actually fires when it should.
3. Decide when an agent is genuinely ready to share.

**You'll try:** Run your agent against the same starting input 3 times. Check whether it reached the same correct conclusion by three different real paths.

---

### Chapter 8 — Packaging and Sharing
**File:** [`tutorial/08-packaging-and-sharing.md`](tutorial/08-packaging-and-sharing.md)

**You'll be able to:**
1. Version an agent so a change to its goal or tools doesn't silently surprise anyone using it.
2. Explain the trust boundary a teammate needs before they'll hand your agent real tool access.
3. Write a short changelog entry for an agent update.

**You'll try:** Move your agent from personal to project-shared, and write down, in plain words, exactly what it is and isn't allowed to do without asking first.

---

### Chapter 9 — Governance and Capstone
**File:** [`tutorial/09-governance-and-capstone.md`](tutorial/09-governance-and-capstone.md)

**You'll be able to:**
1. Explain the risk an agent introduces that a workflow never could: an irreversible action nobody explicitly approved.
2. Set a real human-approval gate around irreversible actions.
3. Use the full "is this ready?" checklist, from thought process to sharing.

**You'll try:** Run the pre-distribution checklist against your own agent. Check specifically: what stops this from taking an action nobody agreed to?

---

## Then, the case studies

Same nine chapters. Four different people, four different jobs, four different investigations.

- [Frontend — the intermittent regression](case-studies/01-frontend-agent/README.md) — Divya, explore-narrow-confirm
- [Backend — the flaky test](case-studies/02-backend-agent/README.md) — Vikram, hypothesize-test-revise
- [QA — the edge cases nobody wrote down](case-studies/03-qa-agent/README.md) — Ananya, bounded autonomous exploration
- [Code review — the adaptive review](case-studies/04-code-review-agent/README.md) — Rahul, a workflow's fixed plan made adaptive

Read the one closest to your own role first. Read all four to see the same discipline bend to fit a genuinely different investigation each time — that contrast is the actual point.

---

← [The Story](00-the-story.md) · [Back to README](README.md) · Start: [Chapter 1 →](tutorial/01-what-is-an-agent.md)
