# Decision log — AI Workflows (Milestone 3)

### D-201: A branch condition is written by a human, evaluated per-run
Options:
  A) Let the model decide whether to draft a reply (ask it "should we
     reply?" as part of the severity call).
     — pros: one fewer explicit rule to write. cons: the branch becomes
       unpredictable and untestable — you can no longer say in a design
       review "we never draft a reply below severity X".
  B) A plain Python function, `needs_reply(ctx) -> bool`, checked by the
     engine between steps.
     — pros: 100% predictable, trivially unit-testable (see
       `test_low_severity_skips_draft_reply`), reviewable in a PR diff.
     cons: you have to think through the rule yourself.
Chosen: B
Why: this IS the workflow/agent boundary from docs/01-concepts.md. The
moment the model chooses the path, you've built an agent, with all of an
agent's unpredictability — sometimes that's right, but a fixed business
rule ("don't bother replying automatically to a low-severity ticket") is
exactly the kind of decision that should be pinned down and testable.
Revisit if: the "should we reply" decision genuinely needs judgment that
can't be reduced to a simple field check (then you may actually want an
agent for that one decision — see Milestone 5).

### D-202: Retry lives at TWO layers, and they mean different things
Options:
  A) Only retry inside the skill (Milestone 2's one retry on bad output).
     — pros: simple, one place. cons: doesn't help with a transient
       infrastructure failure (a 429 rate limit, a network blip) that has
       nothing to do with the output's SHAPE.
  B) Only retry at the workflow layer (RetryPolicy wrapping the whole step).
     — pros: handles infra failures. cons: a step could exhaust its
       retries retrying a bad-shape problem that a skill-level nudge
       would have fixed on attempt 2 for free.
  C) Both: the skill retries once for a SHAPE problem, the workflow step
     retries the WHOLE step (including the skill's own internal retry)
     for an INFRASTRUCTURE problem.
Chosen: C
Why: these are different failure classes needing different fixes — "the
model answered the wrong shape" (fixed by a schema nudge) vs. "the network
call itself failed" (fixed by trying again later). Conflating them into
one retry loop hides which kind of failure you're actually seeing.
Revisit if: this two-layer retry ever masks a REAL bug for too long (e.g.
a step that always needs 3 attempts might indicate a broken prompt, not
bad luck) — watch the `attempts` field on `StepOutcome` in production.

### D-203: A fallback is a value, not a re-try
Options:
  A) On total failure, retry forever until it works.
     — pros: eventually correct. cons: could genuinely never finish (see
       docs/01-concepts.md's agent step-budget problem — same bug, workflow
       edition); leaves the customer waiting indefinitely.
  B) On total failure, fall back to a safe, generic, pre-written default
     (see `fallback_draft` in `ticket_pipeline.py`) and CONTINUE the
     pipeline instead of stopping it.
Chosen: B
Why: a generic "a team member will follow up" reply is always safe to
send, even under a real outage of the reply-drafting dependency itself.
Continuing the pipeline (rather than aborting) means the ticket still
gets its category/severity/fields recorded even if the LAST step is
struggling.
Revisit if: the fallback value itself becomes wrong often enough that it
needs a smarter default — at that point you likely want more than one
fallback tier (see docs/09-frameworks-and-when-to-use-them.md).

### D-204: A step failing with NO fallback stops the whole pipeline
Options:
  A) Skip a failed step (as if it had `status="skipped"`) and continue.
     — pros: pipeline "finishes" even under failure. cons: DANGEROUS —
       later steps might silently read a missing/None value and produce
       a nonsensical result (e.g. drafting a reply with no category or
       severity at all).
  B) Stop the pipeline immediately on an unrecovered failure (see
     `Pipeline.run`'s `break` on `status == "failed"`).
Chosen: B
Why: "fail loud and stop" beats "silently continue with missing data".
The caller inspects `outcomes` and `ctx.trace` to see exactly where and
why it stopped — see `docs/08-troubleshooting.md`.
Revisit if: a specific later step is proven safe to run with partial/
missing upstream data (write an explicit fallback for THAT step instead
of changing this global rule).

### D-205: The circuit breaker doesn't auto-close (a teaching simplification)
Options:
  A) Auto-close after a cooldown window (the real-world pattern).
  B) Stay open until `reset()` is called explicitly.
Chosen: B, for this project only
Why: a time-based auto-close makes the breaker's behavior depend on wall-
clock time, which makes it harder to write a fast, deterministic unit
test (`test_circuit_breaker_opens_after_threshold_and_uses_fallback` runs
in milliseconds because nothing sleeps). A real production system SHOULD
auto-close — this is called out explicitly as a simplification, not
hidden.
Revisit if: you take this code toward production — add a cooldown timer
before shipping it for real.
