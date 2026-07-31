# Lesson 04 — Agentic AI

## 1. What you will learn

- What turns a one-question Agent (Milestone 5) into Agentic AI: a Goal,
  a Plan, a Critic, a Budget, and an Escalation policy.
- Why re-planning after a rejected result is a feature, not a failure.
- Why a Critic is a SEPARATE, skeptical pass, not the same reasoning that
  produced the answer.
- Why write actions ALWAYS require human confirmation, no matter how
  confident the model is.
- The difference between an agent's per-question step budget (Milestone
  5) and a whole investigation's steps/dollars/time budget (this lesson).

## 2. The idea in one picture

See [docs/diagrams/four-levels.md](../../docs/diagrams/four-levels.md)'s
Level 4 diagram. The building blocks in this lesson map onto it directly:

```
 GOAL (goal.py)
    │
    ▼
 PLAN (planner.py) ──► AGENT LOOP (Milestone 5, x N steps) ──► answer
    ▲                                                              │
    │                                                              ▼
    └──────────────── re-plan if CRITIC (critic.py) says "not met" ──┘
                                                              │
                                                     goal met? ──yes──► DONE
                                                              │
                                                              no, but risk is high
                                                              ▼
                                          ESCALATION (escalation.py) ──► ask a human
```

`budget.py`'s `Budget` wraps the WHOLE loop above (not just one agent
call) — it's the circuit breaker for an entire investigation, not one
question.

## 3. The idea in plain words

An agent (Milestone 5) answers one question well. Agentic AI answers a
STANDING GOAL: it might try, get an incomplete answer, notice that
itself (via the Critic), and try again with what it learned — the same
way a person doesn't give up after one incomplete attempt, but also
doesn't try forever (the Budget) or take a risky action without checking
first (Escalation).

**Analogy:** an on-call engineer with an incident runbook. They form a
hypothesis, check it, and if the evidence doesn't fully support their
first theory, they revise it — but they don't restart a production
service without telling someone first, and they don't investigate forever
if the incident is time-critical.

## 4. Walk the code

- [`src/aisets/agentic/goal.py`](../../src/aisets/agentic/goal.py) —
  `Goal`: objective, success criteria, hard constraints, stop conditions.
  Plain data, read by everything else in this lesson.
- [`src/aisets/agentic/planner.py`](../../src/aisets/agentic/planner.py)
  — `Planner.make_plan(goal, context_notes)`: an ordered list of
  plain-English investigation steps.
- [`src/aisets/agentic/critic.py`](../../src/aisets/agentic/critic.py) —
  `Critic.check(goal, answer)`: a skeptical, separate pass that can
  reject an answer and say exactly what's missing.
- [`src/aisets/agentic/budget.py`](../../src/aisets/agentic/budget.py) —
  `Budget`: hard caps on steps/dollars/seconds across a WHOLE
  investigation, with an injectable clock so tests never sleep.
- [`src/aisets/agentic/escalation.py`](../../src/aisets/agentic/escalation.py)
  — `EscalationPolicy` (the rule) + `EscalationGate` (applies the rule,
  calls a human if needed, keeps an audit trail).

## 5. Run it

```powershell
.\scripts\run-example.ps1 11_agentic_goal_and_plan
.\scripts\run-example.ps1 12_agentic_self_correct
.\scripts\run-example.ps1 13_agentic_escalation
```

In example 12, watch the Critic REJECT the first attempt ("Order 9002
failed. Not sure why." — no cited evidence) and watch the second attempt,
informed by what was missing, succeed. In example 13, watch the SAME
`always_confirm_write=True` rule require confirmation for a write action
even at 95% confidence, while a read-only action at 90% confidence
proceeds automatically.

## 6. Why this design

See [DECISIONS.md](DECISIONS.md) for the full log (D-401 through D-405).
Short version: the Critic is a genuinely separate, skeptical pass, not
the agent grading its own homework (D-401); re-planning reuses the same
`Planner.make_plan` with more context rather than a new code path
(D-402); write actions always need a human, no exceptions (D-403); "no
human available" defaults to DENY, never silent approval (D-404); and
`Budget` caps the WHOLE investigation, a different scope than Milestone
5's per-question step budget (D-405).

## 7. When to use this / when NOT to

**Use Agentic AI when:**
- The task is a standing GOAL, not a single question — it may take
  several attempts, and "good enough" needs an explicit check.
- Some outcomes could take real action (restart a service, spend money) —
  you need an explicit escalation policy, not implicit trust.

**Don't use it when:**
- A single Agent call (Milestone 5) already reliably answers the
  question — the Critic/re-plan machinery adds cost and latency for no
  benefit if the first attempt is already good.
- Nothing here ever needs a write action AND the question is simple —
  then Milestone 5's plain agent (or even Milestone 3's workflow) is
  enough.

## 8. How it breaks

| Symptom | How to detect | How to recover |
|---|---|---|
| Critic keeps rejecting every attempt | Repeated `goal_met=False` across re-plans | Check whether `Goal.success_criteria` is achievable at all with the tools available — an unreachable goal will never satisfy a strict Critic. |
| `BudgetExceeded` raised mid-investigation | Exception message names which limit (steps/dollars/seconds) was hit | Either the goal genuinely needs a bigger budget, or (more likely) the investigation isn't converging — check the Critic's `missing` list across attempts for a pattern. |
| A write action never runs even though it seems obviously safe | `EscalationGate.records` shows `decided_by="no_human_available"` | By design (D-404) — wire up a real `human_approve` callback (or a human-in-the-loop UI) rather than treating this as a bug. |
| `EscalationPolicy.decide` returns `human_only` for something that feels low-risk | Check the `risk_level`/`confidence` values passed in | These are inputs YOU (or upstream code) provide — if they're miscalibrated, fix where they're computed, not the policy itself. |

## 9. Security, privacy, cost

- **Security:** the escalation gate is the last line of defense before
  any write tool from Milestone 4 executes — see `docs/06-security-and-privacy.md`
  for how this composes with `ToolRegistry`'s `allow_write` gate.
- **Privacy:** `EscalationGate.records` and `AuditLog` (Milestone 4) both
  keep a plain-text history of what was requested and decided — treat
  these the same as any other audit log containing operational data.
- **Cost:** Agentic AI is the most expensive level in this project — a
  Planner call, N agent-loop steps, a Critic call, and potentially a
  second Planner+agent-loop+Critic round on rejection. `Budget` exists
  specifically to cap this — see docs/07-cost-and-latency.md for a real
  worked example.

## 10. Tests

`tests/unit/test_agentic_goal.py`, `test_agentic_planner.py`,
`test_agentic_critic.py`, `test_agentic_budget.py` (100% coverage — one
of the four dangerous files), and `test_agentic_escalation.py` cover
every building block in isolation.

```powershell
.\scripts\test.ps1 -Path tests\unit\test_agentic_budget.py
.\scripts\test.ps1 -Path tests\unit\test_agentic_escalation.py
```

## 11. Exercises

See [EXERCISES.md](EXERCISES.md).

## 12. Multi-agent orchestration (continuing this lesson)

`src/aisets/agentic/orchestrator.py` adds one more pattern: a
`Supervisor` dispatches ONE task to several independent `Specialist`s
(e.g. an investigator, a fixer, a communicator), collects their results
— CONTINUING even if one fails or "stalls" (`SpecialistTimeout`) — and
synthesizes a final answer from whichever specialists succeeded,
surfacing any contradictions between them rather than silently picking a
side.

```
   task
    │
    ├──────────────┬──────────────┐
    ▼              ▼              ▼
[investigator] [fixer]      [communicator]
    │              │              │
    ▼              ▼              ▼
 result         result       FAILED (excluded, logged)
    │              │
    └──────┬───────┘
           ▼
     [ Supervisor: synthesize, flag contradictions ]
           │
           ▼
      final answer
```

Run `.\scripts\run-example.ps1 14_agentic_multi_agent` and watch: three
specialists run independently, the synthesis combines their findings into
one answer, and the printed call count (5 total model calls) is compared
against a single investigator-only agent (2 calls, example 08) — the
multi-agent team costs more, but covers 3 distinct concerns one agent's
tool set wasn't built to handle at once.

### Centralized (one agent) vs. distributed (multiple specialists)

| | One agent (Milestone 5/6) | Multiple specialists (Supervisor) |
|---|---|---|
| Cost | Lowest — one investigation thread | Higher — N specialists + 1 synthesis call, even when they could share findings |
| Latency | One thread, but strictly sequential | Specialists CAN run independently (only the synthesis step needs all of them) |
| Resilience to one failure | A single agent failing means no result at all | One specialist failing doesn't block the others — synthesis still runs on what succeeded |
| Handles genuinely different skills | Awkward — one system prompt and one tool set must cover every concern | Natural — each specialist gets its own focused prompt/tools, e.g. `DraftReplySkill` for tone, `AgentLoop` for investigation |
| Risk of internal disagreement | None — there's only one voice | Real — two specialists can contradict each other; the synthesis step must surface this, not hide it (see `test_contradictions_are_surfaced_not_silently_resolved`) |
| When to choose it | The task is one coherent line of reasoning | The task genuinely splits into independent sub-jobs needing different skills/tools |

**When NOT to reach for multiple agents:** if one well-scoped agent (or
even a Milestone 3 workflow) already covers the task, adding a Supervisor
and specialists is pure overhead — more tokens, more latency, more ways
for the pieces to disagree, with no corresponding benefit. Use this
pattern when the sub-tasks are genuinely independent AND benefit from
different tools/prompts — not by default.

## 13. What changes in the next lesson

Milestone 8's case study wires EVERYTHING from Lessons 01-04 together
into one realistic backend scenario: a payments incident that must be
detected, investigated across three evidence sources, diagnosed against
a runbook, proposed as a fix, and — critically — stopped before any write
action without a human's sign-off.
