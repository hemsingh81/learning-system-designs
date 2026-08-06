# 11 · Email Templates

[← Pitch & Resume Summary](10-pitch-and-resume.md) · [Home](README.md) · [Next → Checklists](12-checklists.md)

Real templates I adapt, not fill-in-the-blank forms. Each one carries the same principles as the rest of this kit: be specific, name the number, own the commitment, make the next step obvious. Replace anything in `<angle brackets>`.

**Jump to:** [Proposal cover](#1--proposal-cover-email) · [Post-demo follow-up](#2--post-demo-follow-up) · [Scope-change / change request](#3--scope-change--change-request) · [Support handover](#4--support-handover) · [Incident notification](#5--incident-notification) · [Estimate with assumptions](#6--estimate-with-assumptions) · [Writing rules](#the-rules-i-write-by)

---

## 1 · Proposal cover email

Sends the proposal *and* frames it. It leads with their problem and the three win themes.

> **Subject:** <Client> — proposal for <the outcome, in their words>
>
> Hi <Name>,
>
> Thank you for the opportunity. The attached proposal is built around the three things I understood to matter most to you:
>
> 1. **<Win theme 1>** — e.g. reporting that lands inside your daily deadline, every day.
> 2. **<Win theme 2>** — e.g. a design priced on real work, with assumptions stated openly.
> 3. **<Win theme 3>** — e.g. the same architect from proposal through to production support.
>
> A few things worth calling out:
>
> - The solution architecture is on a single page (section 3.1) — the fastest way to see how it fits together.
> - The estimate is broken down by phase, with assumptions stated inside the numbers (section 6).
> - What we would need from your side is listed plainly in section 4.5, so there are no surprises later.
>
> I would welcome a short session to walk you through the architecture and answer questions directly. Would <day/time> or <day/time> suit?
>
> Best regards,
> Hem Singh

---

## 2 · Post-demo follow-up

Sent within a day of a demo or PoC. Recaps value, answers the open question, keeps momentum.

> **Subject:** Follow-up — <topic> demo, and next steps
>
> Hi <Name>,
>
> Thanks for your time today. Quick recap of what we showed and what it means for you:
>
> - **<Capability 1>** — <the outcome it gives them, not the feature>.
> - **<Capability 2>** — <outcome>.
>
> You asked about **<the open question>**. Here is the answer: <short, specific answer>. <If you promised to check something: "I said I would confirm X — confirmed: …".>
>
> Suggested next step: <one concrete step — a scoping call, a technical deep-dive, a short paid discovery>. I have held <day/time> and <day/time> — let me know which works and I will send an invite.
>
> Best regards,
> Hem Singh

---

## 3 · Scope-change / change request

Protects the relationship and the delivery. Never emotional, always specific about impact and options.

> **Subject:** Change request — <the requested change> (impact & options)
>
> Hi <Name>,
>
> Happy to take this on — here is what it means so we can decide together with eyes open.
>
> **What is changing:** <the new/changed requirement, in one line>.
>
> **Impact:**
> - **Effort:** approx. <estimate>, decomposed in the attached breakdown.
> - **Timeline:** <no change / +N weeks / affects milestone X>.
> - **Dependencies:** <anything this touches or blocks>.
>
> **Options:**
> 1. **Add it, extend the timeline** — <what this looks like>.
> 2. **Add it, swap out <lower-priority item>** — keeps the date, re-prioritises scope.
> 3. **Defer to phase 2** — if the current deadline is the priority.
>
> My recommendation, as your advisor, is **<option>**, because <reason tied to their goal>.
>
> No work starts on this until we agree the path. Which option would you like?
>
> Best regards,
> Hem Singh

---

## 4 · Support handover

Sent at go-live or when handing a system to a client's own team. Makes the support model unambiguous.

> **Subject:** <System> — support model, runbooks & escalation (go-live handover)
>
> Hi <Name>,
>
> <System> is live. Here is everything your team needs to run it confidently.
>
> **Support model**
> - Hours of cover: <hours>. Critical window: <e.g. the pre-market load, 04:00–07:00>.
> - What is covered / not covered: <one line each>.
>
> **Monitoring & alerts**
> - Alerts fire automatically for <the key failure modes>, each mapped to a runbook.
> - For deadline-critical steps, alerting is driven by time-remaining, not just severity.
>
> **Runbooks**
> - Location: <link>. Every alert has a matching runbook: what it means, first checks, the fix, and when to escalate. They are written from real incidents.
>
> **Escalation path**
> - Level 1: <team/contact>. Level 2: <team/contact>. Level 3 (architecture): me, <contact>.
> - Escalate when: <the time-based trigger>.
>
> **Knowledge transfer**
> - Sessions completed: <list>. Your team took first line during <period> with me alongside.
>
> I remain available for architecture-level escalation and the year-two improvement roadmap. Anything unclear, tell me and I will add it to the runbooks.
>
> Best regards,
> Hem Singh

---

## 5 · Incident notification

Sent *during* an incident, early. One clear message beats ten anxious ones. In business terms, not technical ones.

> **Subject:** [<Severity>] <System> — <plain-language what is happening>
>
> Hi <Name>,
>
> Flagging early so you can plan.
>
> **What is happening:** <one line, business terms — e.g. "today's reporting load is running slower than usual">.
> **Impact:** <who/what is affected — e.g. "reporting may land ~20 min after the pre-market window">.
> **What we are doing:** <current action>.
> **Expected resolution / next update:** <a specific time>.
>
> Data integrity is not affected — <one line on why, e.g. "the pipeline is dependency-aware, so no partial or duplicate data flows downstream">.
>
> I will send the next update by <time> whether or not it is resolved.
>
> Best regards,
> Hem Singh

---

## 6 · Estimate with assumptions

When sending a number. The assumptions live *inside* the estimate, not in a hidden appendix.

> **Subject:** Estimate — <work item>
>
> Hi <Name>,
>
> Estimate below. It is decomposed to the level of work I have actually delivered, so you can challenge an assumption rather than just the total.
>
> **Estimate:** <range — e.g. 8–10 weeks>, broken down in the attachment.
> **Contingency:** <named amount>, held specifically against <the one real unknown — e.g. the depth of the third-party integration>. This is separate and visible, not padded into the number.
>
> **This assumes:**
> 1. <e.g. the third-party API provides X>.
> 2. <e.g. environments are available by week two>.
> 3. <e.g. one client BA is available half-time>.
>
> If any assumption is wrong, tell me — it will change the number, and it is better we find that now than mid-delivery.
>
> Best regards,
> Hem Singh

---

## The rules I write by

Every template above follows these:

| Rule | Why |
|------|-----|
| **Lead with their problem, not my product** | The reader cares about their outcome, not my feature list |
| **One number, made specific** | "20 minutes late" is plannable; "delayed" is not |
| **Make the next step obvious** | An email with no clear next action stalls |
| **State assumptions in the open** | Hidden assumptions become disputes later |
| **Never let a commitment go out that I have not checked** | Same rule as the proposals in [R5](06-rfp-presales.md#r5--how-do-you-work-with-sales-commercial-and-legal) |
| **Short paragraphs, plain English** | People skim email; make the important parts survive a skim |

---

[← Pitch & Resume Summary](10-pitch-and-resume.md) · [Home](README.md) · [Next → Checklists](12-checklists.md)
