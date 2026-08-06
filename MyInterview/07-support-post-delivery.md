# 07 · Support & Post-Delivery (8 questions)

[← RFP & Pre-Sales](06-rfp-presales.md) · [Home](README.md) · [Next → Cheat Sheets](08-cheatsheets.md)

Most architects hand over after go-live and disappear. I do the opposite. At TCW Group I **own production governance for business-critical processes** — incident triage, root-cause analysis, slow-query tuning and data-discrepancy resolution within agreed SLAs. That is not a burden I tolerate; it is my strongest sales argument, because I have run what I built. The system that has a daily pre-market deadline is not a system you can throw over a wall.

**Jump to:** [S1](#s1--how-do-you-run-production-support-for-a-system-with-a-hard-daily-deadline) · [S2](#s2--walk-me-through-a-real-incident-you-handled) · [S3](#s3--how-do-you-do-root-cause-analysis) · [S4](#s4--how-do-you-tune-a-slow-query-in-production) · [S5](#s5--how-do-you-handle-a-data-discrepancy) · [S6](#s6--how-do-you-do-knowledge-transfer-and-runbooks) · [S7](#s7--how-did-ai-change-your-support-model) · [S8](#s8--how-does-support-turn-into-more-work) · [Runbook template](#the-runbook-template-i-reuse) · [Section index](#section-index)

---

## S1 · How do you run production support for a system with a hard daily deadline?

**Situation.** The TCW investment-reporting platform (Project A) has to land reporting inside the **pre-market window every day**. If the daily Aladdin ingestion is late, portfolio managers do not have their numbers before the market opens. There is no "we will fix it tomorrow" — tomorrow is a different trading day.

**Task.** Design a support model where a failure is caught early enough to still make the deadline, not discovered when someone asks where the report is.

**Action.** I run it on three levels.

**One — the system tells me before a human does.** The orchestration layer across Azure Data Factory, Tidal and Airflow has structured logging and automated failure alerting built in, not bolted on. Every stage of the daily cycle emits a start, a finish and a row count. If a stage does not finish by its expected time, an alert fires with enough context to act — which pipeline, which entity, which upstream dependency. The whole design is **dependency-aware sequencing**, so I know the moment a link in the chain slips, and I know how much slack is left before the deadline.

**Two — a runbook for every alert.** An alert with no matching runbook is a 3 a.m. guessing game. Each known failure mode — Aladdin API unavailable, a reconciliation mismatch, a slow load — has a written first response: what it means, what to check, what to do, and when to escalate. See [S6](#s6--how-do-you-do-knowledge-transfer-and-runbooks).

**Three — a clear escalation path with a time budget.** Because the deadline is fixed, escalation is driven by *time remaining*, not by severity guessing. If we are inside the window's safety margin, first line handles it. If the margin is at risk, it comes to me immediately, and the business is told early rather than at the deadline. Telling a portfolio manager "the load is running late, expect data 20 minutes after open" at 6 a.m. is a manageable conversation. Silence until 9 a.m. is not.

**Result.** Reporting lands inside the pre-market window daily. The rare late run is caught with slack to spare and communicated before it becomes a surprise.

**Lesson.** *"For a deadline-driven system, support is a clock, not a queue. Design the alerting around 'how much time is left', not 'how bad is it'."*

**Follow-ups**

- *"What is the worst time to find a failure?"* — When the business finds it for you. If a user reports the outage, the monitoring failed, and I treat that as a monitoring defect to fix, not just an incident to close.
- *"How do you avoid alert fatigue?"* — Every alert must be actionable and mapped to a runbook. An alert nobody acts on gets tuned or removed. Noisy monitoring is worse than none because it trains people to ignore the screen.
- *"Do you carry a pager?"* — For the critical daily window, yes — the architect who built it should feel the pain of a 5 a.m. failure. That feedback loop makes the next design better.

---

## S2 · Walk me through a real incident you handled.

**Situation.** A daily reporting run was tracking late. An upstream Aladdin ingestion stage was slower than its normal profile, and the dependency-aware orchestration flagged that the downstream reporting step was now at risk of missing the pre-market window.

**Task.** Get reporting out on time, or if not, get the business the earliest honest expectation — and stop it recurring.

**Action.** I work incidents in a fixed order, because under time pressure a fixed order stops me thrashing.

**Stabilise first, diagnose second.** The immediate question is not "why" — it is "can we still make the deadline". I checked the run against the time budget, confirmed which downstream steps had not started, and decided whether to let it run or intervene. Restoring service beats understanding it while the clock is running.

**Communicate early, in business terms.** I told the business the reporting might land slightly late and gave a specific expected time, before the deadline passed. One clear message early prevents ten anxious ones later.

**Contain the blast radius.** Because the pipeline is dependency-aware, a delay in one entity does not corrupt the others. I confirmed the delay was isolated and that no partial or duplicate data would flow downstream — the ETL has validation, retry logic and reconciliation checks exactly so a slow or failed load cannot poison the report.

**Then diagnose properly.** Once the run was safe, I moved to root cause (see [S3](#s3--how-do-you-do-root-cause-analysis)). The slowness traced to a data-volume growth pattern hitting a query that had been fine at smaller scale — a slow-query problem, not an outage.

**Fix, then fix the class.** I tuned the query for the immediate relief (see [S4](#s4--how-do-you-tune-a-slow-query-in-production)), then set a monitoring threshold so the same profile of slow-down would alert *earlier* next time, while there was still margin.

**Result.** The business got an accurate expectation early, the data stayed correct, and the recurrence was closed by both a query fix and an earlier warning trigger.

**Lesson.** *"In an incident, the order is stabilise, communicate, contain, then diagnose. Diagnosing first is the classic mistake — it feels productive and it costs you the deadline."*

**Follow-ups**

- *"What if you cannot make the deadline at all?"* — Then the job is the earliest, most honest expectation and a clear reason. The business can plan around a known 20-minute delay; it cannot plan around silence.
- *"Who declares an incident?"* — Whoever sees it first. I would far rather have a false alarm than a real one that sat because someone was unsure it counted.
- *"How do you keep calm?"* — The fixed order does it for me. When you know the next step is always 'stabilise', you do not freeze.

---

## S3 · How do you do root-cause analysis?

**Situation.** RCA is part of my production-governance remit at TCW. The temptation after every incident is to fix the symptom, close the ticket and move on — which guarantees you see it again.

**Task.** Find the real cause, not the nearest one, and turn it into a change that prevents recurrence.

**Action.** I keep it simple and evidence-driven.

**Start from the evidence, not a theory.** The structured logging is the first source — timings, row counts, error context per stage. I follow the timeline of the actual run rather than starting from a hunch, because a hunch makes you read the logs to confirm what you already believe.

**Ask 'why' until it stops being technical.** A slow report is the symptom. Why? A query slowed down. Why? A table grew past the point where its access pattern held up. Why did nobody see it coming? Because the monitoring watched for failure, not for *degradation*. That last 'why' is usually the real finding — the fix is rarely just the query; it is the missing early-warning signal.

**Separate the trigger from the cause.** The trigger might be a one-off spike. The cause is that the system had no headroom or no alert for it. I write both down, because fixing only the trigger leaves the fragility in place.

**Write it down plainly, and assign the fix an owner and a date.** A root-cause note nobody acts on is theatre. Each finding becomes a concrete action — a query change, a new alert threshold, a runbook entry — with a name and a date against it.

**Result.** Incidents convert into permanent improvements: better queries, earlier alerts, richer runbooks. The system gets quieter over time instead of accumulating recurring pain.

**Lesson.** *"The last 'why' is usually not technical — it is a missing signal or a missing check. Fix the query and you close the ticket; fix the missing signal and you close the class."*

**Follow-ups**

- *"Blameless?"* — Always. The moment RCA becomes about who, people hide detail, and you lose the very information you need. It is about the system, not the person.
- *"How deep do you go?"* — Until the fix is a change to the system, not a change to how carefully a human behaves. "Be more careful" is not a root cause.
- *"Do you RCA near-misses too?"* — Yes. A run that was late but made the deadline is free intelligence. Waiting for the actual breach to learn is expensive.

---

## S4 · How do you tune a slow query in production?

**Situation.** As data volumes grow on the reporting platform, queries that were fast on year-one data can slow down. Keeping report generation fast as volumes grow is an explicit part of my remit, and slow-query tuning is a recurring, concrete task — not a theoretical skill.

**Task.** Make the query fast again without breaking correctness or blowing up write performance elsewhere.

**Action.** I follow a disciplined sequence rather than guessing at indexes.

**Measure before touching anything.** I look at the actual execution plan and the real statistics — where the time and the reads are actually going. Tuning by intuition is how you add an index that helps one query and slows every insert.

**Look for the usual, cheap causes first.** In practice most slow reporting queries come from a small list: a missing or wrong index, stale statistics, a non-sargable predicate (a function wrapped around a column so the index cannot be used), or an over-broad query pulling far more than the report needs. I check those before anything exotic.

**Fix the query before the schema.** Often the fastest, safest win is rewriting the query — narrowing the columns, fixing the predicate so an index can be used, or removing a needless sort — rather than changing the schema. A query rewrite has a smaller blast radius than an index change.

**Add indexes deliberately, and account for the write cost.** When an index is genuinely needed I add it knowing it costs on every write. On a reporting store that reads far more than it writes, that trade is usually worth it — but it is a decision, made with the numbers, not a reflex.

**Design for volume up front on new work.** Because I also set the data-modelling and query-tuning standards, the better answer is to model for growth before it hurts — sensible partitioning, the right indexes, and a separation between the operational store and the analytical store so a heavy historical query never competes with the one that has the morning deadline.

**Result.** Report generation stays inside its time budget even as data grows, and tuning is a measured, repeatable exercise rather than firefighting.

**Lesson.** *"Measure first, rewrite before you re-index, and remember every index you add is paid for on every write. Guessing at tuning usually moves the problem rather than fixing it."*

**Follow-ups**

- *"SQL Server and Snowflake — same approach?"* — The discipline is the same (measure, then act) but the levers differ. On SQL Server I think indexes, statistics and plans; on Snowflake I think clustering, pruning and warehouse sizing. Same question — where is the time going — different answers.
- *"When do you split operational from analytical?"* — When a heavy historical or ad-hoc query can threaten a deadline-driven one. That separation is a core decision on the reporting platform.
- *"How do you stop it recurring?"* — Monitor query duration as a trend, not just as a failure. A query creeping from two seconds to eight is a warning I want *before* it becomes an incident.

---

## S5 · How do you handle a data discrepancy?

**Situation.** In investment reporting, a data discrepancy is the incident that scares people most — a number in the report does not match what a portfolio manager expects. Resolving data discrepancies within SLA is part of my production-governance role, and it is a different animal from an outage: the system is *up*, it is just *wrong*, or appears to be.

**Task.** Establish quickly whether the report is wrong or the expectation is wrong, and either way restore trust in the number.

**Action.** I built the pipeline so this question is answerable, and I work it methodically.

**Trust the reconciliation, then verify it.** The FastAPI ETL ingests from Aladdin with **automated validation, retry logic and reconciliation checks**. So the first move is to look at the reconciliation for that run — did source and target agree at load time? That single check usually tells me immediately whether the data was ingested faithfully or whether something diverged.

**Trace the number back to source.** Because the ingestion is auditable, I can follow a specific figure from the report, back through the transformation, to the raw Aladdin value. Nine times out of ten this locates the discrepancy precisely: a source value that genuinely changed, a transformation edge case, or an expectation based on stale data.

**Separate 'wrong' from 'different'.** Often the report is correct and the expectation was formed against yesterday's data, or against a different scope. Proving that calmly — here is the source, here is the transform, here is the number — resolves it without changing anything, and it protects confidence in the platform.

**If it is genuinely wrong, contain and correct.** Fix the data, identify anything downstream that consumed the bad value, and RCA the transformation or validation gap that let it through so the check exists next time.

**Result.** Discrepancies are resolved within SLA with an evidence trail, and — just as important — the *right* numbers keep their credibility because I can always show the lineage.

**Lesson.** *"In reporting, 'the system is up' is not the same as 'the system is right'. Build lineage and reconciliation in from day one, so a discrepancy is a five-minute trace instead of a two-day argument."*

**Follow-ups**

- *"What if source data itself is wrong?"* — Then I flag it to the source owner with evidence, and we decide whether to correct or annotate. I do not silently patch source data in my layer — that hides a real problem.
- *"How do you prevent them?"* — Validation and reconciliation at ingestion, so a bad or partial load is caught before it ever reaches a report, not after someone questions it.
- *"Who decides what 'correct' is?"* — The business owns the definition; I own the faithful, auditable implementation of it. Confusing those two roles is how discrepancies turn into blame.

---

## S6 · How do you do knowledge transfer and runbooks?

**Situation.** A system that only I can support is a liability, not an asset — for the client and for me. I lead and mentor engineering teams, and part of owning production governance is making sure the knowledge is not trapped in one head.

**Task.** Make the system supportable by the team, and make handover to a client's own team clean when the time comes.

**Action.** Three practical things.

**Runbooks tied to real alerts.** Every alert the system can raise has a matching runbook entry: what it means, first checks, the fix, and when to escalate. I write them from real incidents, so they describe what actually happens, not what I imagine might. A runbook written from a genuine 5 a.m. failure is worth ten written from theory.

**The team supports while I am still there.** The fastest knowledge transfer is doing the work together. I have the team take first line on incidents with me alongside, rather than lecturing them and hoping. Mentoring engineers on the design and then having them run it is the same loop I used on the completion platform — teach the pattern, then let them own it.

**Design for supportability, not just for me.** The cross-platform database utility generator I built for Azure SQL and Snowflake exists partly for this reason — it gives the team **one repeatable path from schema change to release**, with change traceability, so support does not depend on remembering a bespoke procedure. Standardised, traceable, repeatable operations are what make a system supportable by someone who did not build it.

**Result.** Systems the team can run without me, runbooks grounded in real events, and a clean handover story I can put in a proposal with a straight face.

**Lesson.** *"Write runbooks from real incidents, not from imagination, and prove knowledge transfer by having the team run the system while you are still there to catch them."*

**Follow-ups**

- *"How do you keep runbooks current?"* — Every incident updates the runbook as part of closing it. A runbook that is not maintained is worse than none, because it is trusted and wrong.
- *"Documentation nobody reads?"* — I keep it short and task-shaped: what to do when X happens. Nobody reads a 40-page manual at 5 a.m.; they read a one-page runbook for the alert in front of them.
- *"How do you know KT worked?"* — The team resolves an incident without me and I only hear about it afterwards. That is the real test, not a sign-off sheet.

---

## S7 · How did AI change your support model?

**Situation.** Recurring support questions eat senior time. At TCW the same kinds of issues came up repeatedly, and the knowledge to answer them existed — but it was scattered across support emails, Confluence runbooks and past response threads. So I did something about it, on the AI/LLM reference architecture I had defined (Project B).

**Task.** Cut the time to a grounded answer for recurring support issues, without inventing answers.

**Action.** I delivered the firm's **first production RAG application** — a support assistant, built as the first end-to-end implementation on the reusable AI/LLM integration framework I authored.

**Index the knowledge that already exists.** It ingests support emails, Confluence runbooks and past response threads into a **Chroma vector database**, so the institutional memory of how issues were solved becomes searchable by meaning, not just keyword.

**Ground every answer — no free-floating generation.** Built with **LangChain and LangGraph** for retrieval and orchestration, it returns answers grounded in the retrieved documents. That grounding is the whole point in a regulated environment: the assistant is not allowed to make things up; it answers from the firm's own material and shows where the answer came from.

**Evaluate it, do not just ship it.** With **LangSmith** I could trace and evaluate responses rather than trust them blindly. Retrieval, grounding, orchestration *and evaluation* were the four pillars of the reference pattern precisely because an AI feature you cannot measure is one you cannot govern.

**Result.** Faster, grounded answers to recurring support issues, and — more strategically — a **reusable pattern now adopted as the firm's reference** for retrieval, grounding, orchestration and evaluation. The support assistant proved the framework; the framework is the lasting asset.

**Lesson.** *"AI in support is only useful if it is grounded and evaluated. A confident wrong answer in a regulated firm is worse than no answer. Build retrieval and evaluation in, not just generation."*

**Follow-ups**

- *"Why RAG and not fine-tuning?"* — The knowledge changes constantly and must be traceable to a source. RAG lets me point at the exact runbook or email an answer came from; a fine-tuned model cannot show its working, which is a problem when someone asks 'why'.
- *"How do you stop hallucination?"* — Ground strictly in retrieved context, and use LangSmith evaluation to catch drift. If the retrieval finds nothing relevant, the right behaviour is to say so, not to improvise.
- *"Did it replace support engineers?"* — No — it removed the repetitive lookups so they spend time on the genuinely hard issues. It is a first-responder for the known, not a replacement for the skilled.

---

## S8 · How does support turn into more work?

**Situation.** Running a client's production system is the best sales position there is, because trust is already earned. But it only converts to more work if you are watching for the opening rather than just closing tickets.

**Task.** Spot genuine opportunities to help the client more — and raise them as their advisor, never as someone padding a contract.

**Action.** I let the signals come from the support work itself.

**Recurring incidents point at missing capability.** If the same class of issue keeps recurring, that is not just a support cost — it is a business case. On the completion platform, automating the manual workflow that kept generating errors is exactly the kind of "this keeps hurting, here is the fix" conversation that turns firefighting into funded improvement.

**A proven pattern travels.** Once I had built the AI/LLM reference architecture and shipped the first RAG app, the natural next conversation was "where else in the firm does this pattern apply?" A reusable framework is, by design, an upsell that the client asks *you* to extend, because you already proved it works.

**Efficiency wins fund the next phase.** When I can show that CI/CD halved release time, or that automation cut manual effort by 60%, the next improvement is an easy business case — the client has seen the return, so the conversation is about ROI, not cost.

**I raise it as their advisor.** I only propose work I believe they need, and I say plainly what problem it solves and what it is worth. The credibility to do that comes entirely from having run their system well — an incident handled cleanly earns more future work than any sales pitch.

**Result.** Support relationships that grow into new phases because the client trusts the person who kept the lights on, not because anyone was upsold.

**Lesson.** *"The best pre-sales I do is running production well. A recurring incident is a business case in disguise, and a proven pattern is the client asking you to do more."*

**Follow-ups**

- *"Isn't that a conflict of interest?"* — Only if you propose work they do not need. I raise things I would raise if it were my own money. That honesty is why the relationship lasts.
- *"How do you time it?"* — Never during an active incident. First fix the problem; the improvement conversation comes when the system is calm and trust is high.
- *"What is the strongest upsell signal?"* — A pattern you have already proven for them. "We built this, it works, here is the next place it applies" is far stronger than any new pitch.

---

## The runbook template I reuse

Every alert the system can raise gets an entry in this shape. Short, task-focused, written from a real incident.

```text
RUNBOOK: <alert name>
---------------------------------------------------------------
WHAT IT MEANS      One line, in plain language.
SEVERITY / CLOCK   How much time is left before it hurts the business?
                   (For deadline systems, time-to-deadline drives everything.)
FIRST CHECKS       The 2-3 things to look at first, in order.
                     - the structured log for the failing stage
                     - the row counts / reconciliation for the run
                     - the upstream dependency (e.g. Aladdin API status)
LIKELY CAUSES      Ranked by how often they are the real cause.
FIX                The steps that resolve it. Copy-paste ready where possible.
CONTAINMENT        How to stop bad/partial data flowing downstream.
ESCALATE WHEN      The trigger to escalate — time-based, not vibe-based.
COMMUNICATE        Who to tell, and the plain-English message to send.
AFTER              RCA required? Update this runbook. Add/adjust an alert?
```

---

## Section index

| # | Question | Core message |
|---|---|---|
| S1 | Support for a hard daily deadline | Support is a clock, not a queue — alert on time-remaining |
| S2 | A real incident | Stabilise, communicate, contain, then diagnose |
| S3 | Root-cause analysis | The last 'why' is usually a missing signal, not a bug |
| S4 | Tuning a slow query | Measure first; rewrite before re-index; indexes cost on writes |
| S5 | A data discrepancy | 'Up' is not 'right' — build lineage and reconciliation in |
| S6 | Knowledge transfer & runbooks | Runbooks from real incidents; team runs it while you watch |
| S7 | AI in support | Grounded and evaluated, or not shipped — first production RAG app |
| S8 | Support into more work | Running production well is the best pre-sales there is |

---

[← RFP & Pre-Sales](06-rfp-presales.md) · [Home](README.md) · [Next → Cheat Sheets](08-cheatsheets.md)
