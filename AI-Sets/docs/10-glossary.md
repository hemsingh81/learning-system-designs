# 10 — Glossary

Every term used anywhere in this project, in one simple sentence. If you
hit a word you don't recognize while reading a lesson, it's here.

**Agent** — a loop where the model decides what to do next (which tool to
call), instead of following a path you hard-coded.

**Agentic AI** — an agent that owns a goal over time: it plans, remembers,
checks its own work, has hard limits, and can escalate to a human.

**Backoff (exponential backoff)** — waiting longer between each retry
(1s, 2s, 4s, 8s...) instead of retrying instantly, so you don't hammer a
struggling service.

**Budget (agent budget)** — a hard cap on how many steps, how much money,
or how much time a run is allowed to use before it must stop.

**Circuit breaker** — a safety switch that stops calling a failing
dependency for a while after too many failures in a row, instead of
retrying forever.

**Claude** — the Anthropic model family this project's real (non-fake)
LLM backend talks to.

**Context window** — the maximum amount of text (measured in tokens) a
model can "see" at once, including the whole conversation so far.

**Critic (in Agentic AI)** — a step that checks the agent's result against
the original goal before declaring success, similar to a code reviewer.

**Escalation** — the agent stopping and asking a human to decide, instead
of guessing, when the risk or uncertainty is too high.

**FakeLLM** — this project's offline, scripted, deterministic stand-in for
a real model. No network call, no cost, always returns the same output for
the same input. Used as the default everywhere.

**Fixed-fractional sizing** — not used for money here, but the same
"cap it to a percentage of a limit" idea applies to agent budgets.

**Hallucination** — when a model states something false or made-up with
full confidence. One reason we validate every AI output with a schema
instead of trusting it blindly.

**JSON Schema** — a formal description of what shape a piece of JSON must
have (which fields, which types). Used here to tell the model exactly what
output shape we require, and to validate what it returns.

**LLM (Large Language Model)** — the kind of AI model this project uses
(e.g. Claude) — it predicts text, one token at a time, based on everything
it has seen so far.

**Memory (agent memory)** — what the agent remembers between turns.
Short-term = the current conversation. Long-term = facts saved to a
database that persist across separate runs.

**Multi-agent orchestration** — several agents (often with different
specialties) coordinated by a supervisor, instead of one agent doing
everything.

**Plan (in Agentic AI)** — an ordered list of intended steps toward a goal,
made before acting, and revised ("re-planned") when reality doesn't match
expectations.

**Prompt** — the text you send the model, including instructions, context,
and the actual question. Treat it like an API contract — the more precise
it is, the more reliable the output.

**Prompt injection** — text (often hidden inside normal-looking input)
that tries to trick the model into ignoring its real instructions. Exactly
like SQL injection, but the "query language" is natural language.

**Pydantic** — the Python library this project uses to define typed data
models and validate that AI output actually matches the shape we expect.

**Runbook** — a written guide for diagnosing and fixing a specific kind of
incident. The agent reads these the same way a human on-call engineer
would.

**Skill** — one small, focused unit of AI work: input in, output out, no
memory, no decision about what happens next.

**Step budget** — the maximum number of think→act→observe cycles an agent
may run before it must stop and answer (or escalate) with what it has.

**Temperature** — a setting that controls how "creative" vs. "consistent"
a model's output is. Lower = more consistent. This project mostly uses low
temperature because we want reliable, testable behavior.

**Token** — roughly, a word or word-piece — the unit a model reads and
writes in, and the unit its cost is measured in.

**Tool** — a function the agent is allowed to call (e.g. "search the logs",
"query the database"). Each tool has a name, a description, and a schema
for its arguments — exactly like an internal API endpoint.

**Tool schema** — the JSON Schema describing a tool's name, description,
and expected arguments, generated here from Python type hints and
docstrings.

**Workflow** — several skills chained together in a fixed order that a
human decided at design time, with retries/branching/fallbacks wired
around them.
