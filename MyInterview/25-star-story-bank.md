# 25 · STAR Story Bank (10 behavioural stories)

[← Role-Tailoring Guide](24-role-tailoring-guide.md) · [Home](README.md) · [Next → Reverse-Interview Questions](26-reverse-interview-questions.md)

Panels test *how I work with people and pressure*, not just what I know. This is my bank of fully-written behavioural stories — each in **STAR-D** form (**S**ituation → **T**ask → **A**ction → **R**esult → **D** = the lesson) so no answer rambles. All first-person, all true to my resume, all anchored to a real project (A–E). I rehearse the **D** line hardest — the lesson is what makes a story land.

> **My rule for behavioural questions:** *one story, one project, one number, one lesson.* If I can't name the result, I pick a different story.

**Jump to:**
[B1 Failure](#b1--tell-me-about-a-failure) · [B2 Conflict](#b2--a-conflict-with-a-colleague) · [B3 Influence w/o authority](#b3--influencing-without-authority) · [B4 Tight deadline](#b4--a-very-tight-deadline) · [B5 Difficult stakeholder](#b5--a-difficult-stakeholder) · [B6 Disagreed with a decision](#b6--you-disagreed-with-a-decision) · [B7 Mentoring](#b7--developing-someone) · [B8 Ambiguity](#b8--working-with-ambiguity) · [B9 Production crisis](#b9--a-production-crisis) · [B10 Proudest achievement](#b10--proudest-achievement) · [Section index](#section-index)

---

## B1 · Tell me about a failure

**S.** Early on Project A, my first ingestion of Aladdin data looked complete, but a downstream report showed positions that didn't reconcile to the source.

**T.** I had to find out why, fast — in a regulated firm a wrong number is worse than a late one.

**A.** I traced it to my own assumption: I treated a late-arriving batch from the third-party API as "missing" and moved on, instead of waiting and reconciling. I owned the mistake to the team the same day, then rebuilt the pipeline with explicit validation, retry and a reconciliation check that refuses to publish unless source and target totals match.

**R.** After that, processing errors dropped sharply (the same validation discipline later cut errors 25% on the completion platform), and "is the number right?" stopped being a question.

**D.** *"The failure taught me that in financial data, 'looks complete' is not 'is correct'. I now design the reconciliation check first, not last."*

**Follow-ups**
- *"Did you tell anyone or hide it?"* — I raised it the same day. Hiding a data error in a regulated firm is the real failure.
- *"What would you do differently now?"* — I build the reconciliation gate on day one, so a wrong number can never reach a report.

---

## B2 · A conflict with a colleague

**S.** On Project A, a senior engineer wanted every new report to keep writing its own bespoke controller and data-access code — "it's faster for me right now."

**T.** I believed a shared, reusable pattern was right for the platform, but I couldn't win by rank — I had to win on evidence.

**A.** Instead of overruling him, I asked him to pair with me on one report using my proposed controller + Web API pattern, and we timed it against his bespoke approach. I let the result speak.

**R.** The shared pattern was faster to build *and* consistent to maintain; he became its biggest advocate, and it's now reused by every reporting module.

**D.** *"I learned to turn a disagreement into a small experiment. Data ends an argument that opinion just prolongs."*

**Follow-ups**
- *"What if the experiment had proved him right?"* — Then I'd have adopted his way — the goal is the best outcome, not being right.
- *"Was it personal?"* — No, and keeping it about the code, not the person, is exactly why it stayed healthy.

---

## B3 · Influencing without authority

**S.** At TCW (Project B), teams were starting to experiment with LLMs individually — different models, no data-handling rules, no evaluation. I wasn't anyone's manager.

**T.** I wanted the firm to adopt one safe reference architecture, without the power to mandate it.

**A.** I didn't send a policy. I *built* the first grounded, evaluated RAG app on my proposed pattern, showed it working with cited answers and a LangSmith evaluation loop, and framed it as "here's the safe path, already proven" rather than "stop what you're doing."

**R.** It became the firm's first production RAG app and the reference pattern other teams now reuse — adopted because it was easier and safer, not because it was ordered.

**D.** *"Influence without authority is about making the right way the easy way. A working example beats a mandate."*

**Follow-ups**
- *"What if teams ignored it?"* — A proven, easier, safer path sells itself; I also brought compliance in early so the pattern carried weight.
- *"How long did it take to catch on?"* — Once one team reused it successfully, the rest followed — social proof did the rest.

---

## B4 · A very tight deadline

**S.** Project A's whole promise is a hard one: reporting must land *before the US market opens*, every day, with third-party data that sometimes arrives late.

**T.** I had to guarantee a daily deadline I didn't fully control, because the upstream Aladdin feed wasn't mine.

**A.** I designed a dependency-aware orchestration layer across Azure Data Factory, Tidal and Airflow, with retry logic for late data, structured logging, and automated failure alerts that page us early — so we act while there's still time in the window, not after it closes.

**R.** Daily reporting lands inside the pre-market window; late upstream data became a managed event, not a missed deadline.

**D.** *"For a deadline you don't fully control, you don't work harder — you build early warning and slack into the schedule."*

**Follow-ups**
- *"What if data is simply too late?"* — The alert fires early enough to trigger a defined fallback and a heads-up to stakeholders, not a silent miss.
- *"Did you ever miss it?"* — The design's whole point is that a late feed degrades gracefully instead of breaking the deadline.

---

## B5 · A difficult stakeholder

**S.** On the completion platform (Project C) in Kazakhstan, a business stakeholder kept asking for scope changes mid-sprint, framed as "small tweaks."

**T.** I had to protect delivery without making them feel unheard — they were on-site, regulated, and important.

**A.** I sat with them, translated each "tweak" into its real cost in the plan, and gave them a choice: swap it in for something of equal size this sprint, or schedule it next. I made the trade-off visible instead of just saying no.

**R.** Change requests turned into prioritised, planned work; we still cut manual effort 60% and halved release-cycle time because the plan stayed intact.

**D.** *"A difficult stakeholder is usually an unheard one. Show them the trade-off and let them choose — they own the priority, I own the delivery."*

**Follow-ups**
- *"What if they escalated?"* — Then the same visible trade-off goes up the chain — it's a business priority call, made with full cost in view.
- *"Did the relationship survive?"* — It improved — being honest about cost built more trust than always saying yes would have.

---

## B6 · You disagreed with a decision

**S.** On Project A there was pressure to serve heavy historical/analytical queries from the same SQL Server that ran the time-critical operational reads.

**T.** I disagreed — a big historical query could slow the report with the morning deadline — but the simpler single-store option was tempting.

**A.** I laid out the risk plainly and proposed the split: SQL Server for transactional/operational reads, Snowflake for analytical/historical work. I costed both and showed the deadline risk of the single-store path.

**R.** We adopted the two-store design; a heavy historical query can no longer threaten the deadline-critical report.

**D.** *"I disagree with the decision, not the person, and I bring the trade-off in numbers. Then I commit fully to whatever we choose."*

**Follow-ups**
- *"What if they'd overruled you?"* — I'd disagree-and-commit, but log the risk clearly so the decision is made with eyes open.
- *"Isn't two stores more complex?"* — Yes, and I owned that cost openly — but protecting the deadline was worth it.

---

## B7 · Developing someone

**S.** Across Projects A, C and D I've mentored engineers — one in particular was strong technically but wrote code others struggled to maintain.

**T.** I wanted to lift the whole team's maintainability, not just fix their code myself.

**A.** I set a light code-review standard, paired with them on the reusable controller pattern, and had them present it to the team — turning their strength into shared leverage instead of a solo skill.

**R.** They became an advocate for the shared pattern; the team's code got more consistent and easier to hand over.

**D.** *"The best mentoring turns one person's strength into the team's standard. I develop people by giving them ownership of a pattern, not just feedback."*

**Follow-ups**
- *"What if they resisted the standard?"* — I involve them in *setting* it, so it's theirs — people defend what they helped build.
- *"How do you measure growth?"* — Fewer review comments over time, and them mentoring the next person.

---

## B8 · Working with ambiguity

**S.** Starting the Aladdin integration (Project A), the exact contract for late, partial and corrected data from the third-party API wasn't fully documented.

**T.** I had to design a reliable pipeline against an incompletely-specified source.

**A.** I didn't wait for perfect specs. I designed defensively — validation, retry, reconciliation and idempotent loads — so the pipeline behaves correctly whatever the source throws, and I documented the real behaviour I observed as the contract.

**R.** A robust pipeline that lands on time daily, plus a written integration contract that didn't exist before.

**D.** *"With ambiguity I design for the worst input, not the documented one — and I write down what I learn so the next person has the spec I didn't."*

**Follow-ups**
- *"Isn't that over-engineering?"* — For financial data crossing a system boundary, defensive design is right-sizing, not gold-plating.
- *"How did you validate assumptions?"* — By observing real API behaviour over time and reconciling against source totals.

---

## B9 · A production crisis

**S.** On Project A I own production governance — including the night a slow query threatened to push reporting past the pre-market window.

**T.** I had to restore the SLA before the deadline, then make sure it couldn't recur.

**A.** I triaged from the structured logs to the exact slow query, tuned it (made the predicate sargable and fixed the plan), confirmed the window was safe, then did a root-cause pass and added a monitor so the pattern gets caught early next time.

**R.** The deadline held; the fix plus the monitor turned a near-miss into a documented, non-recurring incident.

**D.** *"In a crisis: stabilise first, then root-cause, then prevent recurrence — in that order. And because I designed it and I code, I can fix it myself at 3 a.m."*

**Follow-ups**
- *"Stabilise vs root-cause — which first?"* — Always stabilise first when a deadline is live; root cause the moment the SLA is safe.
- *"How do you prevent repeats?"* — A monitor on the failure signature plus a short write-up so the team learns from it.

---

## B10 · Proudest achievement

**S.** At TCW, LLMs were exciting but risky — no agreed, safe way to use them in a regulated firm.

**T.** I wanted to give the firm a safe path *and* prove it in production, not just on a slide.

**A.** I authored the AI/LLM reference architecture — retrieval, grounding, orchestration, evaluation — and delivered the firm's first production RAG assistant on it (LangChain, LangGraph, LangSmith, Chroma), with grounded, cited answers and an evaluation loop.

**R.** TCW's first production RAG app, now the firm's reference pattern that other teams reuse.

**D.** *"I'm proudest when I turn a risky idea into a safe, reusable standard — innovation that outlives the first project."*

**Follow-ups**
- *"Why proudest?"* — It combined everything: architecture, hands-on build, governance in a regulated firm, and lasting reuse.
- *"What's next for it?"* — Broaden the evaluation set and let more teams onboard onto the same grounded pattern.

---

## Section index

| # | Question type | Project | Result / number | The lesson (D) |
|---|---|---|---|---|
| B1 | Failure | A | Errors down (25% discipline) | "Looks complete" ≠ "is correct"; reconcile first |
| B2 | Conflict | A | Reusable pattern adopted | Turn disagreement into a small experiment |
| B3 | Influence w/o authority | B | First production RAG app | Make the right way the easy way |
| B4 | Tight deadline | A | Daily pre-market window held | Build early warning + slack, don't just work harder |
| B5 | Difficult stakeholder | C | 60% effort, 50% release cut | An unheard stakeholder; show the trade-off |
| B6 | Disagreed with a decision | A | Two-store split adopted | Disagree with numbers, then commit |
| B7 | Mentoring | A/C/D | Team consistency up | Turn one strength into the team's standard |
| B8 | Ambiguity | A | On-time pipeline + written contract | Design for the worst input, document what you learn |
| B9 | Production crisis | A | SLA held, non-recurring | Stabilise → root-cause → prevent |
| B10 | Proudest achievement | B | Firm's reference RAG pattern | Turn a risky idea into a reusable standard |

---

[← Role-Tailoring Guide](24-role-tailoring-guide.md) · [Home](README.md) · [Next → Reverse-Interview Questions](26-reverse-interview-questions.md)
