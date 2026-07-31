# NNNN — <short imperative title: the decision, not the topic>

| | |
|---|---|
| **Produced by** | <name>, <role> |
| **Using** | [P12 — Record an Architecture Decision](../../../../AI-Prompts-Library/phase-2-design/P12-record-an-architecture-decision.md) |
| **Date** | YYYY-MM-DD |
| **Status** | Proposed / Accepted / Accepted, contested / Superseded by NNNN / Deprecated |
| **Version** | 1.0 |
| **In the room** | <names and roles of everyone who took part> |

---

## Context

What forces are in play. Written so somebody who joins in six months understands why this was even a question. State the constraint that makes the decision non-obvious — if there isn't one, this is not an ADR.

Include the numbers. "High volume" is not context; "12,600 pages a month, spiking at month-end" is.

## Options considered

At least two, honestly stated. An option nobody could have chosen is padding, and a reader can tell.

### Option A — <name>

**What it is.** One or two lines, in plain words.

**For.**
- …

**Against.**
- …

### Option B — <name>

Same shape. Give the rejected options their best argument. If the rejected option has no good argument, either you have not understood it or it should not be in the list.

## Decision

One paragraph. Present tense. "We use X."

Then the reasons, numbered, so they can be referred to individually when somebody reopens this in four months.

## Consequences

### What this gives us
- …

### What this costs us
- …

### What we have accepted that we do not like
- … — this subsection is not optional. A decision with no downside was not a decision.

### Objections on the record
- **<Name>, <date>:** <the objection, in their words or a fair summary>. <Whether it was accepted, and if not, why not.>

## Revisit when

The condition under which this decision should be reopened. A date is weak; a trigger is strong. "If straight-through rate is still below 80% after two model retrains" is a trigger.

## References

- Related ADRs, stories, spec sections, and the measurements this decision rested on.

---

> **Artifact contract — `<path/to/this/adr.md>`**
>
> Produced by: <role> using P12 — Record an Architecture Decision
> Approved by: <role, date>
>
> Anyone consuming this file can rely on finding:
> - The context and the constraint that made this a decision rather than a default
> - At least two options with their honest arguments for and against
> - The decision, with numbered reasons
> - Consequences in three parts: what we gain, what it costs, and what we accepted that we do not like
> - Any objection raised, attributed and dated
>
> This file does **not** contain: implementation detail, schemas, or sequencing.
> Those live in: `spec-confidence-gate.md` (P11), `data-contract-counterparty-position.md` (P13), `implementation-plan-NWD-103.md` (P15).
>
> **If any guarantee above is missing, this artifact is not done.**
> Do not build on it — send it back.
>
> Changing this file: never edit an accepted Decision section. Supersede it with a new ADR and set this one's status.
