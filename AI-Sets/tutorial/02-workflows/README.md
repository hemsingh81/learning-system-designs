# Lesson 02 — AI Workflows

## 1. What you will learn

- How to chain several skills into a fixed, ordered pipeline.
- How to branch (skip a step) based on a rule YOU write, not the model.
- The difference between a skill's internal retry (Milestone 2) and a
  workflow step's retry policy — and why both exist.
- How a circuit breaker protects a struggling dependency from being
  hammered by every pipeline run.
- How a fallback keeps a pipeline useful even when one step totally fails.

## 2. The idea in one picture

```
  ticket_text
       │
       ▼
  [classify_ticket] ──ok──► [extract_fields] ──ok──► [score_severity]
       │ retry x2                 │ retry x3                │
       │ circuit breaker          │                          │
       ▼ fail (no fallback)       ▼                          ▼
   PIPELINE STOPS            (continues)              severity == "low"?
                                                              │
                                            ┌─────────yes─────┴─────no──────┐
                                            ▼                               ▼
                                    [draft_reply: SKIPPED]           [draft_reply]
                                                                     retry x2, fallback
```

## 3. The idea in plain words

A workflow is a **recipe**: step 1, then step 2, then step 3, always in
that order, with a couple of "if X, skip step Y" rules you wrote down in
advance. Nothing here is a surprise — you can read `ticket_pipeline.py`
top to bottom and know exactly what will happen for any input, before you
ever run it.

**Analogy:** a CI/CD pipeline. `build` always runs before `test`, which
always runs before `deploy`. You might skip `deploy` on a non-main branch
(a branch condition, same idea as `needs_reply`). If `test` fails, the
pipeline stops — it doesn't silently deploy broken code.

## 4. Walk the code

- [`src/aisets/workflow/context.py`](../../src/aisets/workflow/context.py)
  — `WorkflowContext`, the shared data bag every step reads/writes.
- [`src/aisets/workflow/policies.py`](../../src/aisets/workflow/policies.py)
  — `RetryPolicy` and `CircuitBreaker`, the two reliability tools a step
    can be wrapped with.
- [`src/aisets/workflow/engine.py`](../../src/aisets/workflow/engine.py)
  — `Step` and `Pipeline`: the actual execution loop. Read `Step.run()`
    closely — every branch of that method is covered by a unit test in
    `tests/unit/test_workflow_engine.py`.
- [`src/aisets/workflow/ticket_pipeline.py`](../../src/aisets/workflow/ticket_pipeline.py)
  — the concrete 4-step pipeline: classify → extract → severity → (branch)
    draft reply.

## 5. Run it

```powershell
.\scripts\run-example.ps1 05_workflow_sequential
.\scripts\run-example.ps1 06_workflow_branching
.\scripts\run-example.ps1 07_workflow_retry_and_fallback
```

In example 07, watch `extract_fields` fail twice and succeed on attempt 3
(`attempts=3` in the printed outcome), and `draft_reply` fail both of its
allowed attempts and fall back to a safe generic reply instead of
crashing the whole pipeline.

## 6. Why this design

See [DECISIONS.md](DECISIONS.md). Short version: branches are plain
Python functions a human wrote (D-201); retry exists at two layers because
"wrong shape" and "infra hiccup" are different problems (D-202); a
fallback is a safe default value, not an infinite retry (D-203); an
unrecovered failure stops the whole pipeline rather than silently
continuing with missing data (D-204).

## 7. When to use this / when NOT to

**Use a workflow when:**
- You can write down every step and every branch condition in advance.
- Predictability and testability matter more than handling completely
  novel requests.

**Don't use a plain workflow when:**
- The right NEXT step genuinely depends on what an earlier step found,
  in a way you can't enumerate as `if/else` rules in advance → that's an
  **Agent** (Milestone 5).
- A branch's condition can't be reduced to reading `WorkflowContext`
  values — if you find yourself wanting to ask the model "what should we
  do next?", you've stepped over the line into agent territory.

## 8. How it breaks

| Symptom | How to detect | How to recover |
|---|---|---|
| Pipeline stops early, later steps never ran | `outcomes` list is shorter than `pipeline.steps`; last outcome has `status="failed"` | Check `outcome.error` for the root cause. If it's a genuinely transient problem, consider raising `max_attempts` on that step — but first ask why 2-3 attempts weren't enough. |
| A step keeps needing all its retry attempts | `outcome.attempts == max_attempts` on every run, not just occasionally | This usually means the FAILURE ISN'T TRANSIENT — check whether a fallback would be safer than continuing to retry, or whether the underlying prompt/schema needs fixing (Milestone 2 territory). |
| Circuit breaker stuck open | `breaker.is_open == True`, every subsequent call goes straight to fallback | This project's breaker doesn't auto-close (see D-205) — call `breaker.reset()` once you've confirmed the dependency recovered. |
| `draft_reply` runs when you expected it to be skipped (or vice versa) | Check `ctx["severity_result"].severity` against `needs_reply`'s condition | The condition function is plain Python — read it directly, it's not hidden behind a prompt. |

## 9. Security, privacy, cost

- **Security:** nothing new at this layer beyond Milestone 2's — the
  workflow doesn't change how untrusted input is handled, it only decides
  ORDER and BRANCHING around already-safe skills.
- **Privacy:** `WorkflowContext` holds whatever the skills put into it
  (including the raw ticket text) for the lifetime of one `run()` call —
  it is not persisted anywhere by this project. A real deployment storing
  `ctx.values` for audit purposes should redact PII first.
- **Cost:** a full successful run through `ticket_pipeline` costs 3-4
  model calls (3 if severity is low and `draft_reply` is skipped). A run
  that needs every retry attempt on every step could cost up to 2+3+2+2 =
  9 calls in the worst case — see docs/07-cost-and-latency.md.

## 10. Tests

`tests/unit/test_workflow_engine.py` covers the engine mechanics in
isolation (no skills, no LLM — just plain functions). 100% line coverage
on `engine.py` (see docs/00-PLAN.md's testing plan — this is one of the
four files with a 100% target).

`tests/integration/test_ticket_pipeline.py` covers the full pipeline
against `FakeLLM`: the sequential happy path, the branch, a retry, and a
fallback.

```powershell
.\scripts\test.ps1 -Path tests\unit\test_workflow_engine.py
.\scripts\test.ps1 -Path tests\integration\test_ticket_pipeline.py
```

## 11. Exercises

See [EXERCISES.md](EXERCISES.md).

## 12. What changes in the next lesson

Lesson 03 (Agents) removes the FIXED order entirely. Instead of you
writing `classify → extract → severity → draft`, the model itself looks
at the situation and decides which tool to call next — the same skills'
underlying ideas (structured output, validation), but now the PATH is no
longer something you can read off a Python file in advance.
