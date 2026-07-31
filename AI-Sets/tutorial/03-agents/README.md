# Lesson 03 — AI Agent

## 1. What you will learn

- How the think → choose a tool → run it → observe → repeat loop actually
  works, line by line.
- Why a step budget and loop detection are not optional extras — they're
  the difference between an agent and a runaway process.
- How a tool error becomes information the model can react to, instead of
  a crash.
- The difference between short-term memory (this run's conversation) and
  long-term memory (facts that survive across runs).
- Why a read-only agent should never even be OFFERED a write tool.

## 2. The idea in one picture

See [docs/diagrams/agent-loop.md](../../docs/diagrams/agent-loop.md) for
the full pseudocode. The short version:

```
while step < MAX_STEPS:
    ask the model: "given everything so far, what next?"
    if model answered directly -> DONE, return the answer
    if model wants to repeat an EXACT earlier tool call -> STOP (loop)
    run the tool; if it errors, feed the error back as an observation
    add {tool call, tool result} to the conversation
    loop again
if we ran out of steps -> STOP, say so honestly
```

## 3. The idea in plain words

Milestone 3's workflow was a recipe YOU wrote. This agent is different:
you give the model a QUESTION and a set of TOOLS, and it decides, turn by
turn, what to look at next based on what it's already seen.

**Analogy:** a junior engineer with a runbook and shell access, given a
bug report. They don't run a fixed script — they check one thing, read the
output, and DECIDE what to check next based on what they saw. That
decision-making is exactly what `AgentLoop.run()` delegates to the model.

## 4. Walk the code

- [`src/aisets/agent/loop.py`](../../src/aisets/agent/loop.py) — the loop
  itself. Read this file end to end; it's under 130 lines and every
  branch is unit-tested (100% coverage — see docs/00-PLAN.md's testing plan).
- [`src/aisets/agent/tools.py`](../../src/aisets/agent/tools.py) &
  [`registry.py`](../../src/aisets/agent/registry.py) — built in
  Milestone 4, used here for real.
- [`src/aisets/agent/memory.py`](../../src/aisets/agent/memory.py) —
  `ConversationMemory` (short-term, trims to a char budget) and
  `LongTermMemory` (SQLite-backed facts across separate runs). Note:
  `AgentLoop` itself doesn't use `ConversationMemory` internally yet (it
  keeps the full history for a single run) — `ConversationMemory` is
  introduced here as a standalone building block; Milestone 6's Agentic
  layer is where a long-running goal actually needs it wired in.
- [`src/aisets/agent/simple_agent.py`](../../src/aisets/agent/simple_agent.py)
  — the concrete first agent: 3 read-only tools (`query_orders`,
  `search_logs`, `get_metrics`), no write tools registered at all.

## 5. Run it

```powershell
.\scripts\run-example.ps1 08_agent_first_loop
.\scripts\run-example.ps1 09_agent_with_memory
.\scripts\run-example.ps1 10_agent_guardrails
```

In example 08, watch the agent call `query_orders`, then `search_logs`,
then answer — three DIFFERENT steps for three different questions it
needed answered, decided one at a time. In example 10, watch it stop
itself after exactly 2 steps when the same tool call repeats, and stop
after exactly `max_agent_steps` when it never converges on an answer.

## 6. Why this design

See [DECISIONS.md](DECISIONS.md). One tool call per turn for a traceable
loop (D-301); loop detection is an exact match, not fuzzy (D-302); tool
errors are fed back as observations, never raised (D-303); write tools
aren't even offered to a read-only agent (D-304); memory trims by
character count as a simple stand-in for real tokenization (D-305).

## 7. When to use this / when NOT to

**Use an agent when:**
- The right next step genuinely depends on what an earlier step found,
  in a way you can't enumerate as fixed `if/else` branches.
- You're OK with the path (and therefore the cost/latency) varying run to
  run.

**Don't use an agent when:**
- A Workflow (Milestone 3) would do — if you can write down the steps in
  advance, do that instead; it's cheaper, faster, and fully testable.
- The task needs to persist across MUCH longer than one question-answer
  exchange, with its own goal, self-checks, and a human escalation path
  — that's Agentic AI (Milestone 6).

## 8. How it breaks

| Symptom | How to detect | How to recover |
|---|---|---|
| `stopped_reason == "loop_detected"` | Check `result.steps` — the last two tool-call steps have identical `tool_name`/`tool_arguments` | Usually means the tools available don't actually answer the question, or the system prompt isn't clear enough about when to stop investigating and answer. |
| `stopped_reason == "budget_exhausted"` | `len(result.steps)` reaches `max_steps` with no final answer | Either raise `MAX_AGENT_STEPS` (if the task genuinely needs more steps) or the question is too broad for this agent's tool set — check `docs/07-cost-and-latency.md` before just raising the budget, since more steps means more cost. |
| A tool call keeps returning `"error: ..."` | Check `step.tool_result` for the `AgentStepLog` in question | This is fed back to the model on purpose — if the MODEL doesn't adapt to the error and keeps trying the same broken thing, that surfaces as `loop_detected`, not a silent hang. |
| The model tried to call a tool that "doesn't exist" | Compare against `registry.specs(allow_write=...)` | Likely a `write` tool with `allow_write=False` — by design (D-304), it was never offered, so the model can only have hallucinated a tool name, not actually attempted a blocked one. |

## 9. Security, privacy, cost

- **Security:** `build_simple_agent` registers ZERO write tools — there
  is nothing this agent can do except read. This is the safest possible
  agent configuration and the one to default to whenever an agent doesn't
  need to take action. See `docs/06-security-and-privacy.md` for the full
  tool-permission model.
- **Privacy:** tool results (order records, log lines) flow into the
  conversation history for the duration of one run and are not persisted
  anywhere by `AgentLoop` itself — only `LongTermMemory`, if you choose to
  write to it, persists across runs.
- **Cost:** each step is one model call. A 3-step investigation (like
  example 08) costs roughly 3x a single skill call — see
  docs/07-cost-and-latency.md for real numbers and why the step budget
  directly caps worst-case cost.

## 10. Tests

`tests/unit/test_agent_loop.py` covers every branch of the loop (final
answer, tool call, tool error, loop detection, budget exhaustion, and the
read/write tool-offering gate) with dummy tools, isolated from the real
sample-data tools. `tests/unit/test_agent_memory.py` covers both memory
classes, including persistence across separate `LongTermMemory` instances.

```powershell
.\scripts\test.ps1 -Path tests\unit\test_agent_loop.py
.\scripts\test.ps1 -Path tests\unit\test_agent_memory.py
```

## 11. Exercises

See [EXERCISES.md](EXERCISES.md).

## 12. What changes in the next lesson

Lesson 04 (Agentic AI) turns this one-question agent into a system that
owns a GOAL over a much longer investigation: it plans before acting,
checks its own result against the goal (a "critic"), re-plans if reality
surprises it, and — most importantly — knows when to stop and ask a human
instead of guessing, especially before any WRITE action.
