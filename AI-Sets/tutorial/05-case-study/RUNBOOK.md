# Runbook — Case Study Failure-Handling Matrix

This is the failure/debugging reference for the incident-triage capstone
(`examples/15_case_study_incident_triage.py`). Unlike the sample runbooks
in `data/runbooks/` (which the AGENT reads to diagnose a fake incident),
this document is for YOU, debugging the case study system itself.

## The three variants and what "correct" looks like

| Variant | Evidence quality | Expected `attempts` | Expected `critic_met` | Expected `escalated` |
|---|---|---|---|---|
| `easy` | Clear, consistent (explicit ERROR log + sharp metrics spike) | 1 | `True` | `False` |
| `ambiguous` | Weak at first, resolves on a broader second pass | 2 | `True` (after attempt 2) | `False` |
| `trap` | Genuinely contradictory (spike belongs to a DIFFERENT service) | 2 (exhausted) | `False` | `True` |

If your run doesn't match this table, something in the composition is
broken — see the matrix below for where to look.

## Failure-handling matrix

| Symptom | Likely cause | How to detect | How to recover |
|---|---|---|---|
| `easy` variant needs 2 attempts instead of 1 | The Critic's `_script_easy` verdict wasn't scripted as `goal_met=True`, or the investigator's answer is missing a cited log line | Print `verdict.reasoning` and `verdict.missing` after the first `critic.check` call | Check `_script_easy`'s queued critic response matches the investigator's queued final answer closely enough that a REAL model (not the fake) would also accept it — the fake is a stand-in for real behavior, not an excuse to game the test |
| `ambiguous` variant succeeds on attempt 1 | The first-attempt answer accidentally already satisfies all success criteria | Compare `GOAL.success_criteria` against the attempt-1 scripted answer text | This is fine functionally, but pedagogically wrong — the whole point of this variant is to show attempt 2 happening. Weaken the attempt-1 evidence in `data/case_study/ambiguous/` or the scripted answer. |
| `trap` variant ends up with `critic_met=True` | The scripted critic verdict for attempt 2 was accidentally set to `goal_met=True` even though the evidence points at `checkout`, not `payments` | Check `_script_trap`'s second `queue_json` call for the critic | Fix the scripted verdict — a real Critic reading `GOAL.success_criteria`'s "for the PAYMENTS service specifically" clause should reject evidence about a different service |
| `trap` variant's `action_approved` is unexpectedly `True` | The `human_approve` callback passed to `run_incident_triage` returns `True` | Check what callback the caller passed — `run_incident_triage` ALWAYS asks the human on the escalation path (see `test_trap_variant_never_auto_approves_even_if_a_human_would_say_yes`) | This is not a bug — it's the intended behavior: the system asks, it never assumes an answer. If you want the trap variant to always end in "no action", pass a callback that returns `False`, as the example's `main()` and most integration tests do. |
| `FakeLLM: no scripted response for this call` | The number/order of `queue_*` calls in `_script_*` doesn't match the actual call sequence `run_incident_triage` makes | Count expected calls: `planner.make_plan` (1) + per attempt (`investigator` tool-call + final-answer = 2, `critic.check` = 1) × attempts, plus a re-plan `planner.make_plan` before any retry attempt | Walk through `run_incident_triage`'s `while` loop line by line against your queued responses, in order |
| `sqlite3.OperationalError` or missing file | `settings.data_dir` doesn't point at a directory containing `case_study/<variant>/` | Run `python data\case_study\build_case_study_data.py` (see docs/02-setup-windows.md) | Regenerate the case-study data; it's deterministic, so re-running is always safe |

## The one invariant this whole case study exists to prove

**No write action is ever taken without an actual human decision, and no
root cause is ever claimed without cited, non-contradicted evidence.**
`tests/integration/test_case_study.py::test_trap_variant_never_auto_approves_even_if_a_human_would_say_yes`
is the test that guards this — if you ever find yourself wanting to
"simplify" the escalation path to skip asking in some case, re-read that
test's docstring first.
