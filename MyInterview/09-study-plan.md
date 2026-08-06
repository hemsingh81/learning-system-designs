# 09 · Study Plan

[← Cheat Sheets](08-cheatsheets.md) · [Home](README.md) · [Next → Pitch & Resume Summary](10-pitch-and-resume.md)

Two plans and a set of mock scripts. Pick the plan that matches how much runway you have. Both end at the same place: I can tell my four anchor stories cold, with numbers, and defend the design in [03](03-system-design.md).

**Jump to:** [How to use](#how-to-use-these-plans) · [2-week plan](#the-2-week-plan) · [1-week plan](#the-1-week-plan) · [Night before](#the-night-before) · [Mock scripts](#mock-interview-scripts) · [Self-scoring](#self-scoring)

---

## How to use these plans

Three rules that make the difference:

1. **Speak the answers out loud.** Reading them in my head is not preparation. The interview is spoken, so I rehearse spoken. Ten minutes talking beats an hour reading.
2. **Always land the number.** Every practice answer must end on a project, a decision, and a measurable outcome. If I finish an answer with no number, I redo it.
3. **Time myself.** A great answer that runs four minutes loses the room. I aim for 60–90 seconds per answer, longer only for a system design walkthrough.

---

## The 2-week plan

About 45–60 minutes a day. Weekends lighter.

| Day | Focus | What I do |
|-----|-------|-----------|
| **1** | Foundation | Read [01 Overview](01-overview-positioning.md). Memorise the four anchor projects (A–E) and the numbers table. Say the 3-sentence opening out loud 5 times. |
| **2** | Story bank | Write my STAR-D version of projects A and B in my own words. Say each in under 90 seconds. |
| **3** | Story bank | Same for C, D, E. Now I can reach any story on demand. |
| **4** | Technical: .NET & APIs | [02 Technical Q&A](02-technical-qa.md) — .NET, Web API, microservices questions. Speak the answers. |
| **5** | Technical: Azure & data | [02](02-technical-qa.md) — Azure services, SQL/Snowflake, ETL, orchestration. Drill the [Azure table](08-cheatsheets.md#azure-services-what-and-when). |
| **6** | Technical: security, DevOps, AI/RAG | [02](02-technical-qa.md) — security, CI/CD, observability, RAG. Memorise the [4 RAG pillars](08-cheatsheets.md#ai--rag-recall). |
| **7** | Light / review | Re-say the opening and all five stories. Fix the two weakest. |
| **8** | System design 1 | [03 System Design](03-system-design.md) — first 4 scenarios. Draw each diagram from memory on paper. |
| **9** | System design 2 | [03](03-system-design.md) — remaining scenarios. Practise the C-QUAD flow out loud. |
| **10** | Team & leadership | [04 Team Management](04-team-management.md). Prepare one real conflict story and one mentoring story. |
| **11** | Client & pre-sales | [05 Client Engagement](05-client-engagement.md) + [06 RFP & Pre-Sales](06-rfp-presales.md). |
| **12** | Support & post-delivery | [07 Support & Post-Delivery](07-support-post-delivery.md). Rehearse the incident story (S2) and the discrepancy story (S5). |
| **13** | Full mock | Run the [mock scripts](#mock-interview-scripts) end to end, timed, out loud. Score myself. |
| **14** | Polish | [08 Cheat Sheets](08-cheatsheets.md) only. Re-drill the numbers and the [phrases](08-cheatsheets.md#phrases-that-land). Rest. |

---

## The 1-week plan

When there is less runway. About 60 minutes a day, ruthless prioritisation.

| Day | Focus | What I do |
|-----|-------|-----------|
| **1** | Core identity | [01 Overview](01-overview-positioning.md) + the [numbers table](08-cheatsheets.md#numbers-i-never-forget). Opening + all 5 stories, out loud. |
| **2** | Technical breadth | [02 Technical Q&A](02-technical-qa.md) — skim all, drill Azure, data, and AI/RAG hardest (my strengths, so lead with them). |
| **3** | System design | [03 System Design](03-system-design.md) — pick the 3 scenarios closest to the role. Draw and narrate each. |
| **4** | People & clients | [04 Team](04-team-management.md) + [05 Client](05-client-engagement.md). One conflict story, one negotiation story. |
| **5** | Pre-sales & support | [06 RFP](06-rfp-presales.md) + [07 Support](07-support-post-delivery.md). Estimation answer (R3) + incident answer (S2). |
| **6** | Full mock | Timed mock from the [scripts](#mock-interview-scripts). Score. Fix the two worst answers. |
| **7** | Polish | [08 Cheat Sheets](08-cheatsheets.md) + [10 Pitches](10-pitch-and-resume.md). Numbers and phrases only. Rest. |

---

## The night before

15 minutes, no cramming:

- Say the [30-second and 2-minute pitch](10-pitch-and-resume.md) once each.
- Read the [numbers table](08-cheatsheets.md#numbers-i-never-forget) and the [phrases](08-cheatsheets.md#phrases-that-land).
- Recall the four anchor projects by code (A–E) and one number for each.
- Recall the two frameworks: **STAR-D** and **C-QUAD**.
- Sleep. A rested brain recalls stories; a tired one blanks on numbers.

---

## Mock interview scripts

Run these out loud, timed. Answer as if the interviewer is in front of me.

### Mock A — the architect screen (30 min)

1. "Tell me about yourself." → the [2-minute pitch](10-pitch-and-resume.md).
2. "Walk me through a system you own end to end." → Project A, the reporting platform.
3. "How do you keep a deadline-driven data pipeline reliable?" → orchestration + [S1](07-support-post-delivery.md#s1--how-do-you-run-production-support-for-a-system-with-a-hard-daily-deadline).
4. "Design a data ingestion platform for a third-party feed." → C-QUAD, draw it, [03](03-system-design.md).
5. "Tell me about a production incident." → [S2](07-support-post-delivery.md#s2--walk-me-through-a-real-incident-you-handled).

### Mock B — the leadership panel (30 min)

1. "How do you lead an engineering team across workstreams?" → Project A team leadership.
2. "Tell me about a conflict you resolved." → [04](04-team-management.md).
3. "How do you say no to a client?" → [05 C5](05-client-engagement.md).
4. "Walk me through leading an RFP response." → [R1](06-rfp-presales.md#r1--walk-me-through-how-you-led-an-rfp-response).
5. "How do you estimate something new?" → [R3](06-rfp-presales.md#r3--how-do-you-estimate-effort-for-something-you-have-not-built-before).

### Mock C — the deep-technical (30 min)

1. "Microservices vs modular monolith — when each?" → [02](02-technical-qa.md), example from C.
2. "How did you build a production RAG application?" → Project B, the 4 pillars.
3. "A report is slow. Walk me through fixing it." → [S4](07-support-post-delivery.md#s4--how-do-you-tune-a-slow-query-in-production).
4. "How do you split operational and analytical data?" → the store-split one-liner.
5. "Design an AI feature for a regulated firm." → grounding + evaluation, [03](03-system-design.md).

### Mock D — the hands-on coding round (45 min)

This is the round that proves I still build. Have an editor open; be ready to write, not just talk. All from [14 Full-Stack Hands-On](14-fullstack-hands-on.md).

1. "Write a clean Web API endpoint for this." → [F1](14-fullstack-hands-on.md#f1--build-a-clean-aspnet-core-web-api-endpoint) — thin controller, service, status codes.
2. "Fix this async C# / why is it deadlocking?" → [F2](14-fullstack-hands-on.md#f2--how-do-you-write-correct-async-c) — no `.Result`, bound concurrency.
3. "This screen fires 50 queries — fix it." → [F3](14-fullstack-hands-on.md#f3--entity-framework-or-dapper-show-me) — the N+1 + DTO projection.
4. "Build a React component that loads and shows this data." → [F5](14-fullstack-hands-on.md#f5--build-a-react-data-screen) — the four states + AbortController.
5. "This query is slow — rewrite it." → [F8](14-fullstack-hands-on.md#f8--write-the-sql-not-just-design-it) — sargable predicate, window function.
6. "Walk me through debugging this bug." → [F12](14-fullstack-hands-on.md#f12--walk-me-through-debugging-a-production-issue-in-code) — reproduce, split the stack, fix the class.

---

## Self-scoring

After each mock, score every answer 1–5:

| Score | Meaning |
|-------|---------|
| **5** | Story + decision + number, under 90 seconds, no filler |
| **4** | Solid, but missed the number or ran slightly long |
| **3** | Right idea, no story or no number — sounded generic |
| **2** | Rambled or lost the thread |
| **1** | Blanked |

**Rule:** any answer scoring 3 or below gets rewritten and re-said until it is a 4+. I do not move on from a weak answer — the interviewer will find exactly the ones I skipped.

---

[← Cheat Sheets](08-cheatsheets.md) · [Home](README.md) · [Next → Pitch & Resume Summary](10-pitch-and-resume.md)
