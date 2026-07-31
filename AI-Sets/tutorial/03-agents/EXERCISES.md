# Exercises — AI Agent

## Easy: lower the step budget and watch it matter

Set `MAX_AGENT_STEPS=2` in `.env` and re-run `08_agent_first_loop.py`
(which needs 3 steps: `query_orders`, `search_logs`, final answer).
Observe it now stops with `stopped_reason == "budget_exhausted"` instead
of answering. Put it back to `5` afterward.

**Check yourself:** you can explain in one sentence why 2 wasn't enough
for a question that needs 2 tool calls PLUS one more turn for the final
answer.

## Medium: add a fourth tool — `find_runbook`

`build_simple_agent` (in `src/aisets/agent/simple_agent.py`) only
registers 3 tools. Add `find_runbook` (from Milestone 4's
`src/aisets/tools/runbook.py`) as a fourth read-only tool, and update the
system prompt to mention it's available for finding diagnosis/fix
guidance once a hypothesis has formed.

Then write a NEW example, `examples/18_agent_with_runbook.py`, where the
scripted question is "What should I do about the payments incident?" and
the FakeLLM script has the agent: (1) check metrics for `payments`, (2)
call `find_runbook` with keywords like "payments gateway timeout", (3)
answer citing the runbook's recommended diagnosis steps.

**Check yourself:** running your new example shows all 3 steps and a
final answer that references the runbook by name.

## Break it on purpose: remove the loop-detection check

In `src/aisets/agent/loop.py`, comment out the `if call_key in
seen_calls:` block (the loop-detection check) entirely — just remove the
early return, but keep adding to `seen_calls` (or even remove that too).
Then:

1. Run `10_agent_guardrails.py`'s first demo (loop detection) again.
2. Observe: instead of stopping after 2 steps with `loop_detected`, the
   agent now keeps calling the exact same `query_orders(order_id="9002")`
   over and over until it exhausts the ENTIRE step budget — 5 wasted
   tool calls instead of 2.
3. Put the check back.

**What this teaches:** loop detection isn't a nice-to-have polish
feature — without it, a stuck model burns through its ENTIRE budget on a
call that was never going to produce new information. In a real system
with a real (paid) API, this is the difference between a $0.01 mistake
and a $1.00+ mistake, repeated on every stuck run.
