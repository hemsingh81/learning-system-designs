# 12 · Checklists

[← Email Templates](11-email-templates.md) · [Home](README.md) · [Next → Reproduce Prompt](13-reproduce-prompt.md)

The checklists I actually run — for pursuits, design reviews, go-live and handover. Each one exists because skipping a line on it once cost me something. Print these; do not trust memory.

**Jump to:** [Bid / no-bid](#bid--no-bid) · [Pre-sales activity](#pre-sales-activity) · [Solution outline](#solution-outline) · [Estimate](#estimate) · [Design review](#design-review) · [Go-live readiness](#go-live-readiness) · [Support handover](#support-handover) · [Interview-day](#interview-day)

---

## Bid / no-bid

The first checklist, before any writing. The honest answer to "should we bid?" saves the senior time you need for the bid you *can* win.

- [ ] Do we genuinely understand the domain?
- [ ] Can we meet every non-negotiable requirement? (see [R6](06-rfp-presales.md#r6--the-rfp-has-a-requirement-you-cannot-meet-what-do-you-do))
- [ ] Is there an incumbent — and can we realistically displace them?
- [ ] Is the timeline real, or impossible?
- [ ] Do we have the right people available for the pursuit *and* the delivery?
- [ ] Is the price band one we can win at without cutting work?
- [ ] Have I written down what this client is *actually* worried about?

> If three or more of these are "no", the recommendation is usually **no-bid** — and saying so credibly is what makes a "bid" recommendation trusted.

---

## Pre-sales activity

Once we have decided to bid. The full version of the short table in [06](06-rfp-presales.md#the-checklist-i-run-every-time).

- [ ] Read the RFP twice — once for content, once for what is over-specified (that is where they were burned).
- [ ] Is the support/SLA section longer than the build section? If so, build the response around operations.
- [ ] Draft the clarification questions — good ones also market our understanding.
- [ ] Agree the three win themes with the pursuit team.
- [ ] Identify each decision-maker and the fear each one has.
- [ ] Name our real, evidenced differentiators (no marketing claims).
- [ ] Name our weakness — and how we address it in our own words.
- [ ] Confirm the delivery architect will be named and present.

---

## Solution outline

Before the outline leaves the building.

- [ ] Does the target architecture fit on **one page**?
- [ ] Is every RFP requirement traceable to a box on the diagram?
- [ ] Are the key design decisions written down **with the rejected alternatives**?
- [ ] Is every claim specific — or is it adjectives? ("robust, scalable, secure" = cut it)
- [ ] Are the NFRs answered with **numbers** (availability, recovery, security, performance, deadline)?
- [ ] Are client dependencies stated plainly?
- [ ] Is the transition-to-support section present, even if unprompted?
- [ ] Could the delivery team build from this without a translation layer?

---

## Estimate

Before any number is committed.

- [ ] Decomposed to items that resemble work I have **actually delivered**?
- [ ] Three-point (best / likely / worst) per item, with the spread noted as risk?
- [ ] Contingency **named and visible**, not padded into the total?
- [ ] Cross-checked top-down against a comparable delivery?
- [ ] Environment setup, data migration and UAT support all included? (the three everyone forgets)
- [ ] Assumptions written **inside** the number, not in an appendix?
- [ ] Is out-of-scope explicitly listed?

---

## Design review

Before I sign off an architecture — mine or the team's.

- [ ] What are we optimising for? (stated, not assumed)
- [ ] Operational vs analytical data — separated where a heavy query could threaten a deadline?
- [ ] Failure modes identified — and does each have a recovery path (replay from checkpoint, no duplicates)?
- [ ] Idempotency / retry / reconciliation on every ingestion path?
- [ ] Security: identity (Entra ID), least privilege, data residency honoured in the design?
- [ ] Observability: structured logging, per-stage row counts, alerts mapped to runbooks?
- [ ] Does the design meet the SLA the contract commits to — have I personally checked?
- [ ] Is it supportable by someone who did not build it?
- [ ] Are the key decisions and rejected alternatives documented?

---

## Go-live readiness

Before flipping to production.

- [ ] CI/CD pipeline green; rollback tested, not just assumed.
- [ ] Monitoring and alerting live **before** traffic, not after.
- [ ] Every critical alert has a runbook, written from a real or rehearsed incident.
- [ ] Escalation path agreed and time-based triggers defined.
- [ ] Performance validated at expected data volume (not just at test-data volume).
- [ ] Deadline-critical path proven inside its time budget with margin.
- [ ] Data validation, retry and reconciliation verified end to end.
- [ ] Business informed of the support model and who to call.
- [ ] Backout plan documented and understood by the team.

---

## Support handover

When handing to a client's own team (pairs with the [handover email](11-email-templates.md#4--support-handover)).

- [ ] Support model documented: hours, critical window, what is / is not covered.
- [ ] Runbooks complete, current, and grounded in real incidents.
- [ ] Escalation path with named contacts at each level.
- [ ] Team has run first-line incidents with me alongside (proof, not a sign-off sheet).
- [ ] Standard operational path documented (schema change → release), not tribal knowledge.
- [ ] Year-two / continuous-improvement roadmap outlined.
- [ ] Architecture-level escalation contact (me) confirmed and agreed.

---

## Interview-day

The 5-minute check before I walk in (or join the call).

- [ ] Opening 3 sentences — can I say them cold?
- [ ] Four anchor projects (A–E) — one number ready for each?
- [ ] The numbers table — 60 / 25 / 50 / 30 / 20 / pre-market / first RAG — recalled?
- [ ] STAR-D and C-QUAD — both ready?
- [ ] One story each for: a conflict, an incident, a hard client "no", an estimate.
- [ ] One diagram I can draw from memory (the reporting platform).
- [ ] The two questions I do *not* want — answers prepared?
- [ ] Two good questions to ask *them*.
- [ ] Water, notepad, quiet space, tech tested (if remote).

---

[← Email Templates](11-email-templates.md) · [Home](README.md) · [Next → Reproduce Prompt](13-reproduce-prompt.md)
