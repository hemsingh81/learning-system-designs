# Exercises — AI Workflows

## Easy: change the branch rule

Currently `draft_reply` is skipped only when severity is exactly `"low"`.
Change `needs_reply` in `ticket_pipeline.py` so it ALSO skips `draft_reply`
for `"medium"` severity (only draft for `"high"`/`"critical"`). Update
`test_low_severity_skips_draft_reply` (or add a new test) to prove a
medium-severity ticket now skips the draft step too.

**Check yourself:** `.\scripts\test.ps1 -Path tests\integration\test_ticket_pipeline.py`
passes with your new rule.

## Medium: add a NEW step with its own retry policy

Add a fifth step, `log_ticket`, that runs AFTER `draft_reply` (or after
`score_severity` when `draft_reply` is skipped) and just records a line
to `ctx` (e.g. `ctx.set("logged_at", "...")`) — pretend this represents
writing an audit record to a database. Give it its own `RetryPolicy` with
`max_attempts=3` and NO fallback (a logging failure should stop the
pipeline loudly, not be silently swallowed).

Write a test proving: (a) it runs after `draft_reply` on the happy path,
(b) it also runs after `score_severity` when `draft_reply` was skipped,
(c) a persistent failure in `log_ticket` results in `status="failed"` with
no fallback.

**Check yourself:** all three new test cases pass.

## Break it on purpose: remove the pipeline's stop-on-failure

In `engine.py`'s `Pipeline.run`, comment out the `if outcome.status ==
"failed": break` lines so the pipeline keeps running every step even
after one fails with no fallback. Then:

1. Run `07_workflow_retry_and_fallback.py` after ALSO making `score_severity`
   fail every attempt (queue 2 `RateLimited` errors for it, matching its
   `max_attempts=2`, with no fallback configured).
2. Observe: `draft_reply` now runs anyway, reading `ctx.get("severity_result")`
   which is `None` — `needs_reply()` has to handle that `None` case (it
   already does, look closely at the `is not None` check), but imagine a
   less careful branch condition that assumed `severity_result` always
   exists. That would crash with an `AttributeError` deep inside the
   pipeline, or worse, silently draft a reply based on made-up defaults.
3. Put the `break` back.

**What this teaches:** "stop the pipeline on an unrecovered failure" isn't
just a style choice — it's what makes it SAFE for every later step to
assume its inputs exist. Removing it turns every downstream step into a
place that must defensively check for missing data, which is exactly the
kind of bug class `docs/08-troubleshooting.md` calls out.
