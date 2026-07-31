# Decision log — AI Skills (Milestone 2)

### D-101: Force structured output (a schema/tool call) instead of parsing free text
Options:
  A) Ask the model to answer in prose, parse the string with regex/string ops.
     — pros: simple prompt. cons: fragile parsing, no validation, easy to
       break with a slightly different phrasing, no defense against
       prompt injection producing an out-of-band answer.
  B) Force output through a schema (`complete_json` — a tool call under
     the hood, see `src/aisets/llm/claude.py`).
     — pros: typed, validated, closed value sets are enforceable, a
       malformed/injected answer fails validation instead of silently
       "working". cons: slightly more setup per skill (a Pydantic model).
Chosen: B
Why: the whole point of a skill is to be a reliable building block for a
workflow or an agent. A building block that sometimes returns unparseable
text is not reliable.
Revisit if: never, for anything a program reads. Free text is fine for
the FINAL human-facing message only (see `draft_reply`'s `reply_text`).

### D-102: Retry once on bad output, inside the skill, then raise
Options:
  A) Never retry — raise immediately on the first bad output.
     — pros: simplest, fails fast. cons: throws away runs that would have
       succeeded on a trivial second attempt (models occasionally slip
       on the very first call).
  B) Retry once with an explicit "you got the shape wrong" nudge, then
     raise if it fails again.
     — pros: fixes the common transient case cheaply (one extra call).
       cons: doubles worst-case cost/latency for a call that will never
       succeed.
  C) Retry many times / forever.
     — pros: none worth the cost. cons: hides a persistently broken
       prompt or schema behind repeated retries; wastes money.
Chosen: B
Why: one retry catches most "model slipped on the shape" cases. More than
one retry usually means the PROMPT or SCHEMA is wrong, not the model —
and retrying a broken contract forever just burns money quietly.
Revisit if: real-world data shows the second attempt rarely helps (then
drop to A) or regularly needs more attempts (then something about the
schema/prompt itself needs fixing first — do that, don't add retries).

### D-103: Empty input never reaches the model
Options:
  A) Send empty/whitespace input to the model anyway and let it decide.
     — pros: one less special case in code. cons: spends a real call on
       an answer we can already determine locally (in a batch of 1000
       tickets, some fraction are always going to be blank).
  B) Detect empty input locally and return a skill-specific default.
     — pros: zero cost, zero latency, and forces every skill author to
       explicitly decide "what's the right default here" instead of
       leaving it to chance.
Chosen: B
Why: if you already know the answer without asking, asking anyway is
just wasted money — the same reasoning as a cache check before a DB
query.
Revisit if: a skill's "right default" turns out to be genuinely
context-dependent (then it isn't really "no info" — reconsider whether
empty input should even be valid for that skill).

### D-104: Never trust the model's self-assessment where local logic can check
Options:
  A) Ask the model to report on itself (e.g. "did your reply contain a
     guarantee?") and use its answer directly.
     — pros: no extra code. cons: the model can be wrong about its own
       output, and there is no way to audit "why" it said yes/no.
  B) Run a plain, deterministic, auditable local check on the model's
     actual output, and let that override the model's self-report.
     — pros: fully auditable (you can point at the exact list of banned
       phrases), doesn't depend on the model being self-aware correctly.
     cons: only catches what the local check is written to catch.
Chosen: B (see `draft_reply.py`'s `_contains_forbidden_phrase`)
Why: "ask the AI whether the AI did something wrong" is circular. A
small, explicit, testable local check is worth more than a bigger prompt
asking for self-honesty.
Revisit if: the local check needs to become large/complex enough that it
should be its own moderation service instead of an inline keyword list.

### D-105: Chunk long input rather than silently truncate it
Options:
  A) Truncate to `max_input_chars` like every other skill does.
     — pros: simple, consistent with the rest of the project.
       cons: for a LOG file specifically, the important incident might
       be in the part that gets cut off.
  B) Split into chunks, summarize each, then summarize the summaries.
     — pros: nothing gets silently dropped. cons: more model calls (cost),
       more code.
Chosen: B, but ONLY for `summarize_log` — every other skill still
truncates (D-105 is a deliberate exception, not a project-wide rule).
Why: for most skills (a support ticket), truncating the tail of an
already-short message rarely loses anything important. For a multi-hour
log file, the incident could be anywhere — truncating risks missing the
one thing you're looking for. The cost/correctness tradeoff points the
other way for this one skill.
Revisit if: log volume grows large enough that even chunked summarization
becomes too slow/expensive — at that point, a smarter pre-filter (e.g.
only summarize ERROR/WARN lines) would be the next step, not more chunking.
