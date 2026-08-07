# 56 · Case Study D — Asset-Management Reporting & Delivery (Sculptor · Bain) (5 questions + follow-ups)

[← Case Study C: Completion Platform](55-case-study-c-completion-platform.md) · [Home](README.md) · [Next → Case Study E: UK Web Platforms](57-case-study-e-uk-web-platforms.md)

This is my **data-engineering + delivery-improvement** case study: reporting and delivery for **Sculptor Capital** and **Bain Capital** — ADF-based ETL and BI, and a measurable lift in team velocity and quality. I reach for it on *"how do you improve a team's delivery?"*, *"how do you design ETL?"* and *"how do you raise quality and speed at the same time?"* For theory, see [50 Data Design](50-concept-data-design.md), [37 Azure Services](37-concept-azure-services.md), [03 Delivery](03-delivery-management.md) and [04 Team](04-team-management.md).

> One-line decision: *"I attacked rework, not effort — automation plus review gates — so velocity and quality rose together, +20% and −15%."*

**Jump to:** [The story](#the-story-the-8-beats) · [Decision log](#decision-log-adr-style) · [CD1](#cd1--how-did-you-increase-team-velocity-by-20-without-burning-people-out) · [CD2](#cd2--how-did-you-cut-defects-by-15-at-the-same-time-as-going-faster) · [CD3](#cd3--how-did-you-design-the-adf-etl-for-reporting) · [CD4](#cd4--how-do-you-choose-what-goes-into-a-report-vs-a-self-service-model) · [CD5](#cd5--what-was-your-role-across-sculptor-and-bain) · [Section index](#section-index)

---

## The story (the 8 beats)

**1. How it started.** Both **Sculptor Capital** and **Bain Capital** are alternative-asset managers that live on **accurate, timely reporting** — fund performance, positions, investor reporting. The trigger was two-fold: reporting pipelines needed to be **more reliable and automated**, and the delivery team's **velocity and quality needed to improve** — too much time was going into rework and firefighting rather than new value.

**2. The problem / constraints.**
- **Financial reporting correctness** — same as Case Study A: a wrong number is a liability.
- **Manual, fragile pipelines** that ate engineer time and were error-prone.
- **Delivery drag** — rework and defects slowing the team, not raw effort.
- **Agile delivery** with real stakeholders expecting a steady flow of value.

**3. Options I considered.**
- *Push the team to work harder / longer.* Short-term output, long-term burnout and more defects — rejected.
- *Add more people.* Slow to onboard, and doesn't fix the rework that's the real drag.
- *Attack the rework itself* — automate the fragile pipelines (ADF ETL) and put **review gates and quality practices** in so defects are caught early, not in production. Fewer defects → less firefighting → more capacity for new value.

**4. The decision & why.** I chose to **improve the system, not the effort**: automate the ETL with **Azure Data Factory** and standard patterns, and introduce **code review, testing and quality gates** into the Agile flow. The insight that settled it: *velocity isn't gained by going faster; it's gained by not doing the work twice.* Cutting rework raises **both** speed and quality — they're not a trade-off when the enemy is defects.

**5. What I built / changed.**
- **ADF-based ETL** pipelines for reporting, with validation and standardised, reusable patterns replacing bespoke fragile jobs.
- **BI/reporting** outputs stakeholders could trust.
- **Review gates and testing** woven into the Agile delivery so defects are caught upstream.
- Coaching the team on the patterns so quality became the default, not an inspection at the end.

**6. Who was involved.** I worked across **data engineers** (on the ETL patterns), the **delivery team** (on the Agile flow and review gates), **QA**, and **business/reporting stakeholders** who defined what "correct and timely" meant. My role was to set the patterns, the quality bar and the delivery rhythm — and to coach the team into them.

**7. The result.** Team velocity up **~20%**. Defects down **~15%**. Reporting became more reliable and automated, freeing engineers from firefighting.

**8. The lesson.** *"You don't get faster by working harder; you get faster by not doing the work twice. Kill rework and both speed and quality go up together."*

---

## Decision log (ADR-style)

| # | Decision | Options weighed | What I chose & the trade-off accepted |
|---|----------|-----------------|----------------------------------------|
| D-1 | How to raise velocity | Work harder / add people / **cut rework** | **Cut rework** — slower to show than overtime, bought durable velocity + quality |
| D-2 | ETL approach | Bespoke jobs / **ADF standard patterns** | **ADF patterns** — some upfront standardisation, bought reliability + reuse |
| D-3 | Quality timing | Test at the end / **review gates upstream** | **Upstream gates** — feels slower per PR, bought fewer production defects |
| D-4 | Reporting model | All bespoke reports / **curated + self-service BI** | **Mix** — more modelling, bought fewer ad-hoc requests on the team |

---

### CD1 · How did you increase team velocity by 20% without burning people out?

**Context.** Velocity was the ask, but sustainable velocity was the real goal.

**The problem.** The team's time was going into **rework and firefighting** fragile pipelines, not new value. Pushing harder would have raised defects and burned people out — making things worse.

**The decision & why.** I **attacked the source of the drag**: automated the fragile ETL with ADF standard patterns, and added review gates so defects were caught early. Less rework means more capacity for new work — velocity rises **because** quality rises. That's the opposite of the "go faster, break things" trap.

**Result.** ~20% velocity gain that was **sustainable**, because it came from removing waste, not from overtime.

**Lesson.** *"Sustainable velocity comes from removing waste (rework), not from adding hours. Measure the rework, then kill it."*

**Follow-up: How did you measure velocity honestly, not game it?**
> By pairing throughput with quality — velocity *and* defect rate together. Velocity alone is easy to fake by cutting corners; velocity plus falling defects proves the gain is real, not borrowed from the future.

**Follow-up: What if leadership just wants 'faster' now?**
> I show that firefighting is the tax on speed: every production defect steals a day of new-feature time. Investing a little in gates buys that time back within a sprint or two. I make the trade-off visible with the numbers. See [03 Delivery](03-delivery-management.md).

---

### CD2 · How did you cut defects by 15% at the same time as going faster?

**Context.** Most people assume speed and quality trade off. Here they moved together.

**The decision & why.** They move together **when the enemy is rework**. Review gates, testing and standardised ETL patterns catch defects **upstream**, where they're cheap to fix, instead of in production, where they're expensive and slow. Fewer defects → less firefighting → more time for new value → higher velocity. Quality *is* the velocity strategy.

**Result.** Defects down ~15% and velocity up ~20% — the same intervention drove both.

**Lesson.** *"Speed and quality only trade off when you inspect quality at the end. Move it upstream and they reinforce each other."*

**Follow-up: What quality gates specifically?**
> Code review with a clear standard, automated tests on the transform logic, validation stages in the ETL, and a definition-of-done that includes them. The gate is only useful if it's automated and consistent — a manual checklist rots.

**Follow-up: How do you get a team to embrace review gates they see as slowing them down?**
> By coaching, not mandating — pair on the first few, show the defect-cost data, and let them feel the drop in firefighting. Once they stop getting paged for the same bugs, the gates sell themselves. See [04 Team](04-team-management.md).

---

### CD3 · How did you design the ADF ETL for reporting?

**Context.** Financial reporting pipelines must be reliable, automated and correct.

**The decision & why.** **Azure Data Factory** with **standardised, reusable pipeline patterns** rather than bespoke jobs: parameterised pipelines, a **validation stage** before load, structured logging and alerting, and idempotent, restartable steps. Reuse means a new report is a configuration, not a rewrite — the same reuse instinct as Case Study A's controller pattern.

**Result.** Reliable, automated reporting pipelines that engineers didn't have to babysit, and new reports built faster on the shared pattern.

**Lesson.** *"Standardise the pipeline so a new report is configuration, not code. Reuse is where reliability and speed both come from."* See [50 Data Design](50-concept-data-design.md).

**Follow-up: How do you ensure correctness in these pipelines?**
> Validation before load and reconciliation of control totals — the same discipline as the investment-reporting platform. On money data, correctness is a gate, not a hope.

**Follow-up: ADF vs writing your own ETL code — why ADF?**
> Managed, visual, integrates natively with the Azure data estate, and the client's team could operate it — the fit-to-operating-model filter. For complex transforms I still drop to code (data flows / functions), but the orchestration backbone stays managed.

---

### CD4 · How do you choose what goes into a report vs a self-service model?

**Context.** Not every question deserves a hand-built report; not everything can be self-service.

**The decision & why.** **Curate the trusted, repeated, high-stakes numbers** as governed reports (correctness guaranteed), and expose a **self-service BI model** for exploratory, lower-stakes questions so the team isn't a bottleneck for every ad-hoc request. The line is *stakes and repetition*: high-stakes-and-repeated → governed report; exploratory → self-service.

**Result.** Fewer ad-hoc requests hitting the team, while the numbers that matter stay governed and correct.

**Lesson.** *"Govern the numbers people bet on; free up the rest with self-service. Match the delivery model to the stakes."*

**Follow-up: How do you stop self-service from producing conflicting numbers?**
> A single governed semantic model underneath — shared definitions and measures — so self-service explores the *same* trusted data, not private copies. Governance of definitions is what makes self-service safe.

---

### CD5 · What was your role across Sculptor and Bain?

**Context.** Two alternative-asset managers, similar needs.

**My answer.** I set the **ETL and quality patterns**, the **delivery rhythm** (Agile with review gates), and **coached the team** into them, while working with reporting stakeholders on what "correct and timely" meant. My value was the **system change** — patterns and practices that outlast me — not just individual pipelines. The measure of success is the same as always: the team keeps the velocity and quality after I've handed over.

**Result.** Durable improvement (+20% velocity, −15% defects) that lived in the team's way of working, not in me.

**Lesson.** *"Improve the system, not just the output. Patterns and practices outlast any single deliverable."*

**Follow-up: How do you make an improvement stick after you leave?**
> Bake it into the defaults — templates, pipeline patterns, the definition-of-done — and coach until it's habit, not instruction. If the right way is the easy way, it survives handover.

---

## Section index

| ID | Topic | One-line summary |
|----|-------|------------------|
| — | The story | Attack rework, not effort; ADF ETL + BI; Agile with gates |
| — | Decision log | Four ADR-style decisions with the trade-off accepted |
| CD1 | +20% velocity | Sustainable speed comes from removing rework |
| CD2 | −15% defects | Speed & quality reinforce when quality moves upstream |
| CD3 | ADF ETL design | Standard reusable patterns; new report = configuration |
| CD4 | Report vs self-service | Govern high-stakes numbers; free the rest |
| CD5 | My role | Change the system (patterns/practice), not just the output |

---

[← Case Study C: Completion Platform](55-case-study-c-completion-platform.md) · [Home](README.md) · [Next → Case Study E: UK Web Platforms](57-case-study-e-uk-web-platforms.md)
