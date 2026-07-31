# Lesson 05 — Case Study: Incident Triage (the capstone)

## 1. What you will learn

- How every building block from Lessons 01-04 composes into ONE realistic
  backend scenario, end to end.
- Why "the agent found SOME evidence" is not the same as "the agent found
  the RIGHT evidence" — and how the Critic's success criteria catch that.
- Why re-planning after a rejection is a normal, expected part of the
  loop, not a fallback for something broken.
- The single most important property in this whole project: **no write
  action is ever taken without an actual human decision, and no root
  cause is ever claimed without cited, non-contradicted evidence.**

## 2. The idea in one picture

```
   incident reported (~02:14, payments)
              │
              ▼
   Goal: find root cause + recommend fix, never write without approval
              │
              ▼
   Plan (attempt 1) ──► Investigator (search_logs / get_metrics / find_runbook)
              │                              │
              │                              ▼
              │                          answer #1
              │                              │
              │                              ▼
              │                       Critic: goal met?
              │                         │            │
              │                        no            yes
              │                         │             │
              └────── re-plan ◄─────────┘             ▼
                  (attempt 2, informed              propose fix
                   by what was missing)             (write action)
                         │                             │
                         ▼                             ▼
                  Investigator again          EscalationGate: human
                         │                     must confirm, always
                         ▼                             │
                  Critic again                 approved?  not approved?
                    │        │                    │            │
                   no       yes                 EXECUTE    NOTHING
                    │        └───────────────────►  HAPPENS
                    ▼
             attempts exhausted?
                    │
                   yes
                    ▼
          ESCALATE: insufficient/contradictory
          evidence — NO action, ever, on a guess.
```

## 3. The idea in plain words

This is the same on-call-engineer story from every earlier lesson, but
now it's the WHOLE story at once: gather evidence (Milestone 5's agent +
tools), notice when your first answer wasn't good enough (Milestone 6's
Critic), try again with what you learned (the Planner, re-invoked), and —
if you genuinely can't confirm anything — say so and hand it to a human
instead of guessing. The "trap" variant exists specifically to prove the
system resists the temptation to report a plausible-but-wrong answer.

## 4. Walk the code

- [`data/case_study/build_case_study_data.py`](../../data/case_study/build_case_study_data.py)
  — generates the three variants' `app.log`/`metrics.json`. Read the
  module docstring for what each variant is designed to test.
- [`examples/15_case_study_incident_triage.py`](../../examples/15_case_study_incident_triage.py)
  — `run_incident_triage(llm, settings, variant, human_approve=...)` is
  the whole case study in one function, ~60 lines, composing `Goal`,
  `Planner`, `AgentLoop`, `Critic`, and `EscalationGate` — nothing here is
  a new abstraction, it's Lessons 01-04's pieces wired together by hand,
  exactly the way you'd wire them in a real system.
- [`tests/integration/test_case_study.py`](../../tests/integration/test_case_study.py)
  — imports and scripts the SAME function, proving the safety property
  under test, not just under a hand-run demo.

## 5. Run it

```powershell
.\scripts\run-example.ps1 15_case_study_incident_triage
```

Watch: `easy` resolves in 1 attempt; `ambiguous` is REJECTED on attempt 1
("an elevated metric alone is not a root cause") and resolves on attempt
2 after a broader log search; `trap` is rejected TWICE (the evidence
found belongs to `checkout`, not `payments`) and escalates with
**no action taken**, printed and asserted explicitly at the end of the
script.

## 6. Why this design

See [DECISIONS.md](DECISIONS.md). Short version: the three variants use
REAL, different sample data, not just different scripted narration
(D-501); the `trap` variant's contradiction is a plausible-but-wrong
signal (a different service), not just an absence of evidence, because
that's the harder and more realistic failure mode to resist (D-502); the
escalation path always genuinely asks a human, even when the system
already suspects the answer should be "no" (D-503); and the attempt limit
is small and explicit, not unlimited (D-504).

## 7. When to use this pattern / when NOT to

**Use the full Goal→Plan→Investigate→Critic→Escalate composition when:**
- Getting it WRONG has a real cost (a wrong root cause leads to acting on
  the wrong service, wasting an on-call engineer's time, or worse).
- The investigation might genuinely need more than one attempt.

**Don't use the full pattern when:**
- A single Milestone 5 agent call, or even a Milestone 3 workflow,
  already reliably answers the question — this composition's extra calls
  (Planner, Critic, potential re-plan) cost real money and latency for a
  benefit you don't need if the simple case already works.

## 8. How it breaks

See [RUNBOOK.md](RUNBOOK.md) for the full failure-handling matrix —
what each variant SHOULD produce, and what to check when it doesn't.

## 9. Security, privacy, cost

- **Security:** the investigator in this case study is registered with
  ONLY 3 read-only tools (no `restart_service`/`scale_service`) — any
  recommended action is proposed through `EscalationGate`, never executed
  directly by the investigating agent. See docs/06-security-and-privacy.md.
- **Privacy:** `data/case_study/*` contains only synthetic, generated
  sample data (fake emails, fake order ids) — nothing here resembles real
  customer data, and nothing should ever be replaced with real data
  without redaction.
- **Cost:** `easy` costs 4 model calls (1 plan + 2 investigate + 1
  critic); `ambiguous` and `trap` cost 8 (two full attempts). See
  docs/07-cost-and-latency.md for what this looks like in real dollars
  against `ClaudeLLM`.

## 10. Tests

`tests/integration/test_case_study.py` covers all three variants, including
the one non-negotiable safety property: a human is ALWAYS genuinely
consulted before any action, and the `trap` variant never confirms a root
cause on contradictory evidence.

```powershell
.\scripts\test.ps1 -Path tests\integration\test_case_study.py
```

## 11. Exercises

See [POSTMORTEM-EXERCISE.md](POSTMORTEM-EXERCISE.md) — instead of code
exercises, this lesson asks you to write up what you observed, the way a
real backend team would after an incident.

## 12. What's next

You've completed the full spine: Skill → Workflow → Agent → Agentic AI →
a realistic capstone. Milestone 9 wraps this into something you could
actually deploy: a FastAPI service exposing the agent, plus the
project-wide security/cost/troubleshooting docs and the final environment
checklist.
