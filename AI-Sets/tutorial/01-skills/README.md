# Lesson 01 — AI Skills

## 1. What you will learn

- What a "skill" is, and why it's the smallest unit of AI work.
- How to force a model to answer in a typed, validated shape instead of
  free text you have to parse.
- Why every skill checks empty input and oversized input BEFORE calling
  the model.
- How one automatic retry recovers from a model that got the output shape
  wrong, without retrying forever.
- Why you should never trust a model's opinion of its own output when a
  local check can verify it directly.

## 2. The idea in one picture

```
      input text ──► [ validate: empty? oversized? ] ──► [ ask model for
                                                            STRUCTURED
                                                            output ]
                                                                 │
                                          shape wrong? ──► retry ONCE
                                                                 │
                                          still wrong? ──► raise BadOutput
                                                                 │
                                                            still good
                                                                 │
                                                                 ▼
                                                   typed, validated object
```

## 3. The idea in plain words

A skill answers ONE question about ONE piece of input, and gives you back
data you can trust the SHAPE of (even if you should still sanity-check the
CONTENT — models can be confidently wrong).

**Analogy:** think of a skill like a single, well-typed function in a
backend service: `def classify(text: str) -> TicketCategory`. You wouldn't
accept "whatever the function feels like returning" in normal code — you'd
have a return type. A skill gives the same guarantee for AI output.

## 4. Walk the code

- [`src/aisets/skills/base.py`](../../src/aisets/skills/base.py) — the
  `Skill` base class. Read this file first — every other skill file is
  short precisely because the hard parts (empty-input handling, retry,
  truncation) live here once.
- [`src/aisets/skills/classify_ticket.py`](../../src/aisets/skills/classify_ticket.py)
  — the simplest skill: free text → one of 6 fixed categories.
- [`src/aisets/skills/extract_fields.py`](../../src/aisets/skills/extract_fields.py)
  — pulling OPTIONAL structured fields out of text, never inventing values.
- [`src/aisets/skills/score_severity.py`](../../src/aisets/skills/score_severity.py)
  — a numeric field with Pydantic's `ge=1, le=10` bound, so an out-of-range
    answer is automatically rejected and retried.
- [`src/aisets/skills/draft_reply.py`](../../src/aisets/skills/draft_reply.py)
  — the ONE skill that produces free text (a human-facing reply) PLUS a
    local, non-AI safety check that never trusts the model's self-report.
- [`src/aisets/skills/summarize_log.py`](../../src/aisets/skills/summarize_log.py)
  — the ONE skill that chunks instead of truncating, because a log file's
    important content could be anywhere in a long file.

## 5. Run it

```powershell
.\scripts\run-example.ps1 01_skill_hello
.\scripts\run-example.ps1 02_skill_classify
.\scripts\run-example.ps1 03_skill_structured_output
.\scripts\run-example.ps1 04_skill_failure_modes
```

Expected output for `01_skill_hello`: a `TicketCategory` object with
`category='billing'` and a confidence above 0.9, printed to the console —
see `docs/02-setup-windows.md` if anything fails to run.

## 6. Why this design

See [DECISIONS.md](DECISIONS.md) for the full log. The short version:
structured output over free text (D-101), one retry not zero or many
(D-102), empty input never reaches the model (D-103), never trust a
model's self-report where a local check can verify (D-104), and chunk
instead of truncate specifically for logs (D-105).

## 7. When to use this / when NOT to

**Use a skill when:**
- The task is one clear input → one clear output, with no dependency on
  prior calls or external systems.
- You can write down the output shape in advance (even if some fields are
  optional).

**Don't use a plain skill when:**
- The task needs several steps in a fixed order → that's a **Workflow**
  (Milestone 3).
- The task needs the model to decide which step comes next, or to look
  things up in a database/log file → that's an **Agent** (Milestone 5).

## 8. How it breaks

| Symptom | How to detect | How to recover |
|---|---|---|
| `BadOutput` raised | Exception message names the schema and shows what came back | The base class already retried once. Check the prompt/schema — if this happens often, the schema or instructions are likely unclear to the model, not "unlucky". |
| Skill silently returns a wrong-looking but VALID answer | Compare against `expected_*` fields in `data/tickets.json`'s clean tickets | Structured output only guarantees the right SHAPE, never the right CONTENT — add a workflow-level or human-review check for anything high-stakes (see Milestone 3's branching). |
| `ConfigError` at startup | Raised from `aisets.config.load_settings()` | Usually `LLM_BACKEND=claude` with no `ANTHROPIC_API_KEY` set — either add the key or switch back to `fake` in `.env`. |
| Cost/latency higher than expected on `summarize_log` | Check `fake_llm.calls` length, or real usage via `UsageTracker` | Long logs get chunked into multiple model calls on purpose (D-105) — see docs/07-cost-and-latency.md for the tradeoff. |

## 9. Security, privacy, cost

- **Security:** every skill wraps untrusted input in `<ticket>`/`<log>`
  tags and instructs the model to treat it as DATA, never instructions —
  see `data/tickets.json`'s `kind: "injection"` tickets and
  `examples/04_skill_failure_modes.py`'s demo #3. Full details in
  `docs/06-security-and-privacy.md`.
- **Privacy:** these skills only ever see what you pass them — no skill
  reaches out to any external system. In a real deployment, redact PII
  (emails, card numbers) BEFORE it reaches a third-party model, if your
  data-handling policy requires it.
- **Cost:** `FakeLLM` is free. With `ClaudeLLM`, each skill call is 1-2
  round trips (1 normal, 2 if a retry fires); `summarize_log` is
  `ceil(log_length / chunk_size) + 1` calls. See docs/07-cost-and-latency.md
  for real numbers.

## 10. Tests

44 unit tests cover all five skills in `tests/unit/test_skills_*.py`, each
following the same five-case template: happy path, empty input, oversized
input, malformed/out-of-range output, and a prompt-injection attempt.

```powershell
.\scripts\test.ps1 -Path tests\unit
```

To add a test for a new skill, copy the five-case pattern from
`tests/unit/test_skills_classify_ticket.py`.

## 11. Exercises

See [EXERCISES.md](EXERCISES.md).

## 12. What changes in the next lesson

Lesson 02 (Workflows) chains several of these EXACT skills together in a
fixed order you control, adds retries/branching AROUND them (not inside
them — that's still the skill's job), and shows how to short-circuit a
low-severity ticket instead of drafting a reply for it.
