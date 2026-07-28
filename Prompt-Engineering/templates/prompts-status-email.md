--- filename: templates/prompts-status-email.md ---

# Status & Communication Prompt Templates

← [Back to README](../README.md) · Related: [Chapter 5 — Workflows](../chapter-05-workflows.md)

8 prompts for generating status updates for your team and manager. Each includes a subject template, body prompt, placeholders, tone options, and an example output.

---

## 1. Daily Standup Summary

**Subject template:** *(none — spoken/chat format, not email)*

**Prompt:**
```
Summarize my work from today into a 3-line standup update: what I did
yesterday, what I'm doing today, and any blockers. Source material:
[paste commits, ticket updates, or rough notes]. Tone: concise.
```

**Placeholders:** `[source material]`

**Tone options:**
- **Concise (default):** 3 lines, no elaboration.
- **Detailed:** Add one sub-bullet per line for context, for async/written standups where teammates aren't in the room to ask follow-ups.

**Example output (concise):**
```
Yesterday: Fixed the duplicate-charge bug in checkout retry logic (PR #412, merged).
Today: Writing regression tests for the fix, starting the search-relevance ticket.
Blockers: none.
```

---

## 2. Sprint Summary

**Subject template:** `Sprint [N] Summary — [team/project name]`

**Prompt:**
```
Write a sprint summary email covering: what shipped, what's still in
progress and why, and what's planned for next sprint. Source material:
[paste completed/in-progress/planned ticket list]. Tone: [concise/
detailed]. Audience: [team / manager / cross-team stakeholders].
```

**Placeholders:** `[ticket list]`, `[tone]`, `[audience]`

**Tone options:**
- **Concise:** Bullet points only, no narrative, for a team that reads every sprint summary and doesn't need re-orientation.
- **Detailed:** Add a one-paragraph narrative intro, for a stakeholder audience that only checks in periodically.

**Example output (concise, team audience):**
```
Subject: Sprint 14 Summary — Checkout Team

Shipped:
- Duplicate-charge fix (PR #412)
- Idempotency key enforcement on /checkout (PR #415)

In progress:
- Search relevance tuning — blocked on real query log access, ETA slips to Sprint 15

Next sprint:
- Load testing for flash-sale scenario
- Admin metrics dashboard v1
```

---

## 3. Incident Report (Internal)

**Subject template:** `[SEV-N] Incident Report — [short description] — [date]`

**Prompt:**
```
Draft an internal incident report from this timeline: [paste raw
timeline notes/logs]. Sections: Impact (who/what was affected, for how
long), Timeline (chronological, timestamped), Root Cause, Remediation
(immediate + follow-up action items with owners), Detection (how we
found out, and how we could have found out sooner). Tone: blameless —
describe what happened to the system, not who made a mistake.
```

**Placeholders:** `[timeline notes/logs]`

**Tone options:**
- **Blameless (default, required for internal postmortems):** Describes system and process failures, never individual blame.
- N/A — this template should not have a "less blameless" variant; that's a deliberate constraint, not a missing feature.

**Example output (excerpt):**
```
Subject: [SEV-2] Incident Report — Checkout 500 errors — 2026-01-14

Impact: ~4% of checkout attempts failed for 22 minutes (14:08-14:30 UTC).
No data loss; affected users saw a generic error and could retry successfully.

Timeline:
14:08 — Error rate alert fired for /checkout
14:11 — On-call engineer acknowledged, began investigation
14:19 — Root cause identified: DB connection pool exhausted after a
        deploy changed a query's isolation level
14:24 — Rollback initiated
14:30 — Error rate returned to baseline

Root Cause: A deploy at 14:05 changed the checkout query's isolation
level, causing connections to hold locks longer than expected under load.

Remediation:
- [x] Rolled back the deploy (done, 14:24)
- [ ] Add connection pool exhaustion to alerting (owner: @asha, due Fri)
- [ ] Add isolation-level changes to the pre-deploy review checklist (owner: @rohan, due next sprint)
```

---

## 4. Release Notes (Customer-Facing)

**Subject template:** `[Product name] — What's New — [date/version]`

**Prompt:**
```
Draft customer-facing release notes from this internal changelog:
[paste changelog]. Rules: no internal ticket IDs, no engineering jargon,
group by New / Improved / Fixed, one line per item, lead with what
matters most to the user. Tone: [friendly/matter-of-fact]. Mark clearly
as DRAFT pending release-manager sign-off.
```

**Placeholders:** `[changelog]`, `[tone]`

**Tone options:**
- **Friendly:** Light, conversational — good for consumer products.
- **Matter-of-fact:** Direct, no exclamation marks — good for B2B/enterprise products where over-enthusiasm reads as unprofessional.

**Example output (matter-of-fact):**
```
Subject: Checkout — What's New — v2.4.0
[DRAFT — pending release manager sign-off]

New:
- Saved payment methods can now be set as default at checkout.

Improved:
- Checkout now recovers automatically from brief network interruptions
  without requiring you to re-enter payment details.

Fixed:
- Resolved an issue where some orders could be charged twice on retry.
```

---

## 5. Manager 1:1 Prep Summary

**Subject template:** *(agenda doc, not email)*

**Prompt:**
```
Turn these rough notes into a 1:1 agenda for my manager: [paste notes —
wins, blockers, questions, career topics]. Group into: Updates (quick,
FYI-level), Discussion (needs their input/decision), Career/Growth (if
any this week). Keep each item to one line unless it genuinely needs more.
```

**Placeholders:** `[rough notes]`

**Tone options:**
- **Concise (default):** One line per item.
- **Detailed:** Add context for items you expect to need more than a one-line explanation.

**Example output:**
```
Updates:
- Duplicate-charge bug shipped and verified in prod.

Discussion:
- Search relevance work is blocked on query log access — need help
  unblocking with the data team.
- Want your take on prioritizing load testing vs. the admin dashboard
  next sprint.

Career/Growth:
- Interested in leading the trading platform prototype's compliance
  workstream — is that a reasonable stretch for this quarter?
```

---

## 6. Cross-Team Dependency Request

**Subject template:** `Request: [what you need] by [date] — [your team/project]`

**Prompt:**
```
Draft an email to another team requesting [what you need], needed by
[date], for [project/reason]. Include: what specifically you need, why
it's needed by that date (what it unblocks), and what you can offer in
return (context, code, time) to make the ask easy to say yes to. Tone:
respectful of their time and priorities, not entitled.
```

**Placeholders:** `[what you need]`, `[date]`, `[project/reason]`

**Tone options:**
- **Respectful/collaborative (default and only recommended option):** Frames the ask as a negotiation, not a demand.

**Example output:**
```
Subject: Request: read access to search query logs by Jan 20 — Checkout MVP

Hi [Data team],

For the checkout MVP's search relevance work, I need read access to
the last 30 days of search query logs (anonymized is fine — I don't
need user IDs, just query text and clicked-result IDs).

This unblocks our search tuning work, currently blocked and at risk of
slipping our Jan 24 launch date if we don't have log access by Jan 20.

Happy to walk through exactly what fields I need on a quick call, or
work with whatever export format is easiest on your end.

Thanks,
Asha
```

---

## 7. Escalation Email (Blocker)

**Subject template:** `Blocked: [what's blocked] — need [decision/resource] by [date]`

**Prompt:**
```
Draft an escalation email about a blocker: [describe blocker]. State:
what's blocked, the impact if unresolved by [date], the decision or
resource needed to unblock, and who needs to make that decision. Tone:
factual and urgent without being alarmist — state impact in concrete
terms (dates, numbers), not adjectives.
```

**Placeholders:** `[blocker description]`, `[date]`

**Tone options:**
- **Factual/urgent (default):** Concrete impact statements, no adjective-driven urgency ("critical," "urgent" used sparingly and only when true).

**Example output:**
```
Subject: Blocked: load testing — need staging environment access by Jan 22

The flash-sale load test can't start until we have a staging
environment that mirrors production capacity. Currently blocked on
infra provisioning.

If unresolved by Jan 22, we lose the buffer needed to fix issues the
load test surfaces before the Jan 30 launch — meaning we'd either
launch without load validation or slip the date.

Decision needed: prioritize the staging environment provisioning
ticket (INFRA-891) this week. [Infra lead] — can you confirm this is
feasible, or should we discuss alternatives?
```

---

## 8. Weekly Team Digest

**Subject template:** `[Team name] Weekly Digest — Week of [date]`

**Prompt:**
```
Write a weekly digest for the team from this week's activity: [paste
PRs merged, tickets closed, incidents, decisions made]. Sections:
Shipped, Decided (any notable decisions and their reasoning, for future
reference), Coming Up. Keep it skimmable — bullets, not paragraphs.
```

**Placeholders:** `[week's activity]`

**Tone options:**
- **Skimmable (default):** Bullets only, designed to be read in under a minute.
- **Detailed:** Add a "why" clause to each Decided item for a team that references digests later as informal decision records.

**Example output:**
```
Subject: Checkout Team Weekly Digest — Week of Jan 13

Shipped:
- Duplicate-charge fix
- Idempotency key enforcement

Decided:
- Going with Azure Service Bus over RabbitMQ for order events — team's
  already on Azure, and we don't need replay for this use case.

Coming Up:
- Flash-sale load testing (blocked on staging access, see escalation
  sent Jan 15)
- Search relevance tuning kickoff
```

---

← [Back to README](../README.md) · Related: [`prompts-bug-fix.md`](./prompts-bug-fix.md), [`prompts-research.md`](./prompts-research.md)
