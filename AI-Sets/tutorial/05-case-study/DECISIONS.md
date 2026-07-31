# Decision log — Case Study (Milestone 8)

### D-501: Three variants live in real data files, not just scripted model verdicts
Options:
  A) Keep one dataset and only vary the SCRIPTED FakeLLM responses across
     easy/ambiguous/trap.
     — pros: less data to generate. cons: the "evidence" a learner reads
       in `data/case_study/*/app.log` and `metrics.json` would be
       identical across variants, making the lesson feel fake — you'd be
       trusting the narration, not the data.
  B) Generate three genuinely different `app.log`/`metrics.json` pairs
     (`data/case_study/build_case_study_data.py`), where the DATA ITSELF
     tells a different story per variant — a real model given the SAME
     tools and SAME prompts, pointed at different data, would plausibly
     produce similar attempts/verdicts to what's scripted.
Chosen: B
Why: the scripted FakeLLM responses are a stand-in for what a real model
would conclude — they need to be a PLAUSIBLE reading of real data, not an
arbitrary narrative. See docs/00-PLAN.md's testing philosophy: FakeLLM
scripts responses, but the surrounding system (data, tools, schemas)
should be real enough that swapping to `ClaudeLLM` would plausibly
produce a similar outcome.
Revisit if: you want to actually RUN the case study against a real model
(`LLM_BACKEND=claude`) to validate the scripted verdicts — the honest
data variants are what make that comparison meaningful.

### D-502: The "trap" variant's contradiction is a DIFFERENT SERVICE, not missing data
Options:
  A) Make the trap variant simply have NO evidence at all (empty logs,
     flat metrics).
     — pros: simple. cons: "no evidence" is easy to handle correctly —
       any reasonable system says "I don't know". It doesn't test whether
       the system can resist a MISLEADING signal.
  B) Make the trap variant have a real, measurable anomaly — just in the
     WRONG service (`checkout`, not `payments`) — so there IS a story to
     tell, and it's tempting to tell it, but doing so would violate the
     Goal's success criterion "for the PAYMENTS service specifically".
Chosen: B
Why: a genuinely dangerous failure mode is a model that finds SOME
plausible-looking evidence and reports it confidently, even though it
doesn't actually answer the question asked. This variant tests exactly
that temptation, and the Critic's job is to catch it (see
`GOAL.success_criteria`'s specific wording in
`examples/15_case_study_incident_triage.py`).
Revisit if: you find the "wrong service" trap too subtle for a first-time
reader — consider adding a simpler "no evidence at all" trap variant
alongside this one, not instead of it.

### D-503: `run_incident_triage` always asks the human, even on the escalation path
Options:
  A) On the "insufficient evidence" path, skip asking a human at all and
     just return "escalated" with a hardcoded `approved=False`.
     — pros: guarantees the safety property by construction, no matter
       what a badly-configured caller passes as `human_approve`.
     cons: this HIDES the decision from the human entirely — they never
       even see the request, which is arguably worse than asking and
       having them decline.
  B) Always call `gate.request(...)`, which always consults
     `human_approve` (see `EscalationPolicy`'s `is_write_action=True` +
     `always_confirm_write=True` routing every proposed action through a
     real human decision) — see D-403 in tutorial/04-agentic/DECISIONS.md.
Chosen: B
Why: transparency matters as much as safety here. A human should SEE
that the system couldn't confirm a root cause and be the one to decide
what happens next — not have that decision made silently on their behalf,
even if the silent decision happens to be the safe one.
Revisit if: never — always show the human the actual situation, don't
pre-decide it for them "for their own safety".

### D-504: `max_attempts` defaults to 2, not more
Options:
  A) Allow unlimited re-plan attempts until the Critic is satisfied.
     — pros: might eventually succeed. cons: this is exactly the
       unbounded-cost problem `Budget` (Milestone 6) exists to prevent —
       and the `trap` variant is specifically designed to NEVER succeed,
       so unlimited attempts there would spin forever.
  B) A small, explicit `max_attempts` (default 2): one initial attempt,
     one informed re-plan attempt, then escalate if still unresolved.
Chosen: B
Why: two attempts is enough to demonstrate genuine re-planning (the
`ambiguous` variant) while still bounding worst-case cost — and it forces
the `trap` variant to hit its escalation path deterministically rather
than "eventually" giving up.
Revisit if: real-world investigations show 2 attempts is too few for
genuinely recoverable ambiguous cases — raise it, but pair the change
with an explicit `Budget` cap (Milestone 6) so it stays bounded.
