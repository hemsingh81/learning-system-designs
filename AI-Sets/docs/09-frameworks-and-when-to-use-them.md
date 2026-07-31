# 09 — Frameworks, and when to reach for one

This project deliberately builds everything from a raw SDK — no
LangChain, no LlamaIndex, no CrewAI (`docs/00-PLAN.md` D-002). Now that
you've built the agent loop, the tool registry, and the Agentic
building blocks by hand, this page explains what those frameworks
actually automate, so you can make an informed choice instead of
cargo-culting one.

## What you built vs. what a framework would give you for free

| Concept in this project | What we wrote | What a framework typically gives you |
|---|---|---|
| Tool schema generation | `agent/tools.py`'s `@tool` decorator (~90 lines) | Similar decorator/wrapper, often with more type coercion edge cases handled |
| The agent loop | `agent/loop.py` (~130 lines) | A configurable loop, often supporting parallel tool calls and more built-in stop conditions |
| Memory | `agent/memory.py` (short-term trim + SQLite facts) | Pluggable memory backends (vector stores, various DBs), more built-in eviction strategies |
| Multi-agent orchestration | `agentic/orchestrator.py`'s `Supervisor` | Graph-based orchestration, streaming between agents, more built-in coordination patterns |
| Retrieval over documents | `tools/runbook.py`'s keyword search | Vector search / RAG pipelines, embeddings, chunking strategies |

## Why we didn't use one for THIS project

1. **The loop is the lesson.** If a framework hides the think→act→observe
   loop behind a `.run()` call, you can't SEE it to learn it. Writing it
   yourself once means you'll recognize it instantly inside any framework
   later — you'll know what a framework's `AgentExecutor` (or equivalent)
   is actually doing under the hood.
2. **Debuggability.** When something goes wrong in a 130-line loop you
   wrote, you can read every line. When something goes wrong three layers
   deep inside a framework's abstraction, you're debugging someone else's
   code with less context about why it's shaped that way.
3. **Dependency weight.** Frameworks bring transitive dependencies,
   version churn, and API surface you don't need for a single teaching
   project — this project's entire dependency list fits in
   `pyproject.toml`'s few lines.

## When a framework genuinely earns its keep

- **You need retrieval over a large, real document corpus** (not five
  short runbooks) — a framework's chunking/embedding/vector-store
  integrations save real time over hand-rolling one.
- **You need many pre-built integrations** (dozens of tools, connectors
  to third-party services) — a framework's tool ecosystem can be faster
  to wire up than writing each one.
- **You need production features you don't want to build yourself**:
  streaming, distributed tracing, retry/backoff policies tuned across
  many providers, a hosted agent runtime.
- **Your team already standardized on one** — consistency across a
  codebase has real value, even over a marginally "better" hand-rolled
  approach.

## When to stay with a hand-rolled approach (like this project)

- You need to understand or debug EXACTLY what's happening at each step
  (this is most of what makes Agentic AI trustworthy for something like
  the incident-triage case study).
- Your actual tool set is small and stable (a handful of internal APIs) —
  the `@tool` decorator pattern here scales fine to dozens of tools
  without needing a framework.
- You want tight control over safety mechanisms (loop detection, budgets,
  escalation) — these are exactly the parts you should NOT want hidden
  behind a framework default you haven't personally verified.

## What to look for if you DO adopt a framework later

Map every concept in this project to the framework's equivalent before
you trust it:
- Does it validate tool arguments against a schema, or just pass raw
  strings? (Compare to `agent/tools.py`'s Pydantic validation.)
- Does it have an explicit step budget / loop detection, or could an
  agent spin forever? (Compare to `agent/loop.py`.)
- Does it let you gate write actions behind an explicit human-approval
  step, or does "tool calling" mean immediate execution? (Compare to
  `agentic/escalation.py`.)
- Can you swap in a fake/offline backend for tests, the way `FakeLLM`
  lets this project run and test entirely offline? (Compare to
  `llm/base.py`'s `LLMClient` protocol.)

If a framework can't answer these clearly, you've just traded a loop you
understand for one you don't — that's a worse position, not a better one.
