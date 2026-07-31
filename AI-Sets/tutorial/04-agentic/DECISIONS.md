# Decision log — Agentic AI (Milestones 6 & 7)

### D-401: The Critic is a separate model call, never the same reasoning
Options:
  A) Have the investigating agent grade its own final answer as part of
     the same response.
     — pros: one fewer call. cons: the same reasoning that produced a
       flawed answer is unlikely to spot its own flaw — this is why code
       review by someone else works better than self-review.
  B) A separate `Critic.check()` call, with its OWN system prompt
     ("be skeptical, don't be generous"), reasoning fresh from the goal
     and the proposed answer.
Chosen: B
Why: see example 12 — the Critic caught "not sure why" as failing "cite
evidence", something the original agent's own confidence didn't flag.
Revisit if: the extra call's cost isn't justified for low-stakes
questions — make the Critic pass OPTIONAL/configurable per goal, rather
than removing it project-wide.

### D-402: Re-planning reuses `Planner.make_plan`, it isn't a new code path
Options:
  A) A dedicated "recovery plan" function, separate from the normal
     planning path.
  B) The SAME `make_plan(goal, context_notes)`, just called again with
     `context_notes` describing what was tried and what the Critic said
     was missing.
Chosen: B
Why: "re-plan when reality (or the Critic) surprises you" isn't a special
case — it's the SAME planning operation with more context. One code path
is easier to trust and test than two that are supposed to behave
similarly.
Revisit if: a genuinely different planning STRATEGY is needed after a
rejection (e.g. "try a completely different investigation angle") — that
would be a real second path, not this one.

### D-403: Write actions ALWAYS require human confirmation
Options:
  A) Skip confirmation for write actions above some confidence threshold.
     — pros: faster automation for "obviously safe" cases. cons: model
       confidence is not the same thing as correctness (a wrong answer
       can be stated confidently) — see docs/03-llm-basics.md on
       hallucination. Automating a write action on confidence alone
       stakes real infrastructure on that miscalibration.
  B) Every write action requires human confirmation, no matter the
     confidence — see `EscalationPolicy.decide`'s `always_confirm_write`.
Chosen: B
Why: read actions are reversible (a lookup has no side effect); write
actions (restart/scale/page) are not free to undo. The cost of asking a
human for a genuinely safe action is low; the cost of an unattended wrong
write action is not.
Revisit if: a SPECIFIC, narrow write action is proven low-risk enough by
real incident history to warrant its own carve-out — add that as an
explicit, reviewed exception, not a blanket confidence threshold.

### D-404: No human available -> deny, never silently approve
Options:
  A) If no `human_approve` callback is wired up, fall back to the
     policy's automatic decision anyway.
     — pros: the system "just works" even without a human in the loop.
       cons: this defeats the entire point of requiring confirmation —
       a missing integration silently becomes "always yes".
  B) If a decision requires a human and none is available, the SAFE
     default is DENY (`decided_by="no_human_available"`).
Chosen: B
Why: a missing safety mechanism should fail closed (block the risky
action) not fail open (approve it by default). See
`test_gate_with_no_human_available_denies_safely_by_default`.
Revisit if: never for write actions. For low-stakes read-only escalations
where "human_only" was itself a borderline call, you might choose a
different default — but write actions must stay fail-closed.

### D-405: Budget wraps the WHOLE investigation, not one agent call
Options:
  A) Rely only on Milestone 5's `AgentLoop.max_steps` (per-question step
     budget).
     — pros: already exists. cons: an Agentic run can call the agent loop
       MULTIPLE times (plan -> act -> critic rejects -> re-plan -> act
       again) — each call's own step budget doesn't cap the TOTAL cost
       across re-plans.
  B) A separate `Budget` (steps/dollars/seconds) that the orchestrating
     code increments on every phase (agent call, planner call, critic
     call), independent of `AgentLoop`'s own internal step cap.
Chosen: B
Why: these are budgets at two different scopes — "how many tool calls
for THIS question" (Milestone 5) vs. "how much total work for THIS
GOAL, across possibly several questions" (this milestone). Conflating
them would let an unbounded number of re-plans slip through even though
each individual agent call stayed within its own small step cap.
Revisit if: never — keep the two scopes distinct even if their numeric
limits happen to be tuned similarly.

<!-- Milestone 7 (multi-agent orchestration) decisions are appended here
     once that module is built. -->
