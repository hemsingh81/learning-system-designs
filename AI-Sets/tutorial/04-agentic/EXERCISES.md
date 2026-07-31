# Exercises — Agentic AI

## Easy: tighten the escalation policy

In `examples/13_agentic_escalation.py`, change `min_auto_confidence` from
`0.6` to `0.95` when constructing `EscalationPolicy`. Re-run the example
and observe: scenario 1 (previously AUTO at confidence 0.9) now requires
`human_only` instead. Write a one-sentence explanation of why raising
this threshold changes that outcome, referencing `EscalationPolicy.decide`.

## Medium: add a `max_reattempts` cap to the self-correct loop

`examples/12_agentic_self_correct.py` currently allows exactly ONE
re-attempt after a Critic rejection. Generalize this into a small
reusable function in a new file, `src/aisets/agentic/loop_with_critic.py`:

```python
def run_until_goal_met(agent, critic, goal, question, *, max_attempts=3):
    ...
```

It should: run the agent, check with the critic, and if not met, run
again (folding in the critic's `missing` list into the next question),
up to `max_attempts` times — returning the last answer and verdict either
way (goal met or not, after exhausting attempts).

Write tests proving: (a) it stops early once `goal_met=True`, (b) it
stops after exactly `max_attempts` if the critic never approves, (c) the
`missing` list from one rejection actually reaches the next attempt's
question/context.

**Check yourself:** all three tests pass, and re-running example 12
through your new function produces the same result as the hand-written
version.

## Break it on purpose: make the escalation gate fail OPEN

In `src/aisets/agentic/escalation.py`'s `EscalationGate.request`, change
the `elif self.human_approve is None:` branch so it returns
`ApprovalRecord(request=request, approved=True, decided_by="no_human_available")`
instead of `approved=False`. Then:

1. Run `13_agentic_escalation.py`'s scenario 2 (write action requiring
   confirm) WITHOUT passing a `human_approve` callback to the gate.
2. Observe: a `restart_service` write action is now approved with NOBODY
   having actually confirmed it — the audit record even LOOKS legitimate
   (`decided_by="no_human_available"`) but nothing was actually checked.
3. Revert the change.

**What this teaches:** "fail open" on a safety gate is worse than the
gate not existing at all, because it looks like protection was applied
when it wasn't. This is exactly the kind of bug `docs/06-security-and-privacy.md`
calls out as a tool-permission anti-pattern — always default a missing
safety check to the SAFE outcome, never the permissive one.
