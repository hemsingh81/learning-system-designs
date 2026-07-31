# Sprint 2 Plan — Build the Pipeline

| | |
|---|---|
| **Produced by** | Farhan Qureshi (Project Manager) |
| **Using** | [P16 — Sprint Plan and Assignment](../../../AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md) |
| **Date** | 2026-05-18 |
| **Sprint** | 2 of 5 · two weeks · 2026-05-18 to 2026-05-29 |
| **Status** | Closed 2026-05-29 |
| **Version** | 1.1 |

---

## 1. Sprint goal

> **A counterparty PDF dropped into the raw container ends up either as trustworthy rows in Snowflake, or as an exception a human can act on. End to end, for Broker Alpha, in English.**

One sentence, and it is a sentence about an outcome rather than a list of tickets. If we finish six of the seven stories but a PDF still cannot make it all the way through, we did not hit the goal.

The two deliberate exclusions from the goal — EM translation and PII redaction — are real work that does not change the answer to *"does the pipeline work?"*

---

## 2. Capacity

| Person | Available days | Notes |
|---|---|---|
| Tomas Vargas (Backend) | 9 | One day on Sprint 3 discovery for the Aladdin pull |
| Ji-woo Park (Frontend) | 8 | Two days lost to the design-system upgrade |
| Ananya Iyer (QA) | 7 | Half-time until day 4; the E2E harness needs the pipeline to exist first |
| Rahul Nair (Team Lead) | 5 | Review, pairing, and unblocking. Not counted as delivery capacity |

**Committed: 31 points** against a 39-point backlog. NWD-104 (translation) and NWD-105 (redaction) roll to Sprint 3.

> **Note on velocity.** This is our first build sprint, so we have no measured velocity. 31 points is a guess dressed up as a number. Treat the goal as the commitment and the points as a way of noticing if we are badly off.

---

## 3. Assignment

| ID | Story | Pts | Owner | Day started | Done |
|---|---|---|---|---|---|
| [NWD-101](stories/NWD-101.md) | Land PDFs immutably in the raw zone | 2 | Tomas | 1 | ✅ d1 |
| [NWD-102](stories/NWD-102.md) | Classify a PDF to its counterparty layout | 5 | Tomas | 2 | ✅ d3 |
| [NWD-103](stories/NWD-103.md) | **Gate every field on its confidence score** | 8 | Tomas | 3 | ✅ d6 |
| [NWD-106](stories/NWD-106.md) | Transform to the canonical position schema | 3 | Tomas | 7 | ✅ d8 |
| [NWD-107](stories/NWD-107.md) | Load to Azure SQL and Snowflake idempotently | 5 | Tomas | 8 | ✅ d10 |
| [NWD-108](stories/NWD-108.md) | Exception queue screen for analyst review | 8 | Ji-woo | 4 | ✅ d10 |

---

## 4. The dependency, and what we did about it

This is the part of the plan worth reading.

**NWD-108 — Ji-woo's exception queue — has nothing to display until NWD-103 exists.** The screen's entire job is to show an analyst *which field failed, what value the machine read, what confidence it had, and what threshold it missed*. All four of those come out of the gate's failure output. Until the gate exists, there is no shape to render.

On the naive plan, Ji-woo starts NWD-108 on day 1, discovers on day 1 that there is nothing to build against, and either waits five days or invents a shape that the gate then contradicts.

Three options considered:

| Option | Cost |
|---|---|
| Ji-woo waits for NWD-103 | 5 idle days, and the sprint goal becomes unreachable |
| Ji-woo invents the shape and reconciles later | Rework, and the reconciliation lands in the last two days of the sprint where there is no slack |
| **Freeze the failure shape as a contract on day 1, before either side is built** | **One hour of Sofia's time on day 1** |

We took the third. Sofia wrote the failure output shape into [`spec-confidence-gate.md`](spec-confidence-gate.md) §4 on day 1, before Tomas started the gate and before Ji-woo started the screen. Both built against the frozen shape rather than against each other's code.

```json
{
  "passed": false,
  "reason": "low_confidence: market_value",
  "straight_through": false,
  "failures": [
    {
      "field": "market_value",
      "row": 3,
      "value": 1042500.00,
      "confidence": 0.8712,
      "threshold": 0.92,
      "why": "below_threshold"
    }
  ]
}
```

Ji-woo built against that JSON with a hand-written fixture for four days before a real one existed. When they finally connected on day 8, it worked first time.

> **This is the [handoff contract](../../../AI-Prompts-Library/02-the-handoff-contract.md) applied to a schedule rather than a document.** The reason it worked is that the shape was written down and agreed *before* either side had an opinion shaped by their own half of the code.

---

## 5. Risks tracked during the sprint

| Risk | Status at close |
|---|---|
| Threshold values are a judgement call with money behind them | Resolved — swept against the ground-truth set. 0.90 money, 0.92 for Broker Alpha, 0.75 descriptive |
| Ji-woo blocked on NWD-103's output shape | **Mitigated by the day-1 contract freeze.** Did not materialise |
| Ananya cannot write E2E tests until the pipeline runs end to end | Materialised. E2E started day 8, ran into Sprint 3. Accepted |
| Tomas is the single point of delivery for six of seven stories | Materialised and unaddressed. See below |

---

## 6. Sprint close — what actually happened

**All six committed stories delivered. Sprint goal met on day 10.** A Broker Alpha PDF goes in one end and comes out as rows in Snowflake or as an exception on Priya's screen.

Two things worth recording honestly.

**Tomas finished NWD-103 in three days against an eight-point estimate.** The gate logic itself took about ninety minutes; the rest was thresholds and tests. This looked like excellent news at the time. It is the same speed that let a serious defect through undetected two weeks later — see [NWD-142](bug-NWD-142.md) and the [retrospective](retrospective-sprint-3.md). The lesson is not that Tomas went too fast. It is that our **verification** did not speed up to match, so the ratio of code-produced to code-genuinely-checked quietly got worse and nobody was measuring it.

**Six of seven stories on one person was a real risk and we ran it anyway.** It worked, and it also meant one person's mental model was the only mental model of the pipeline. Rahul's review caught style and one real defect; it did not catch a missing concept, because you cannot review for a concept nobody in the room has.

**Not done, rolled to Sprint 3:** NWD-104 (EM translation), NWD-105 (PII redaction), and the E2E suite.

---

> **Artifact contract — `artifacts/sprint-2-plan.md`**
>
> Produced by: Farhan Qureshi (Project Manager), using [P16](../../../AI-Prompts-Library/phase-3-planning/P16-sprint-plan-and-assignment.md)
> Approved by: the team at sprint planning, 2026-05-18
>
> Anyone reading this plan can rely on finding:
> - A sprint **goal** stated as an outcome, not a ticket list
> - Capacity per person, with the reasons days are unavailable
> - Story assignment with points and owner
> - **Every cross-story dependency, and the specific mitigation for each**
> - Risks tracked, with their status at close
> - An honest close-out including what did not get done
>
> This plan does **not** contain: estimates or their basis (see [backlog-ranked.md](backlog-ranked.md)),
> or the build sequence within a story (see [implementation-plan-NWD-103.md](implementation-plan-NWD-103.md)).
>
> **If a dependency is listed without a mitigation, the plan is not done.**
>
> Changing this file: PM. Adding scope mid-sprint requires the Product Owner.
