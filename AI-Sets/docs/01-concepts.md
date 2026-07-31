# 01 — Concepts: Skills, Workflows, Agents, Agentic AI

This page explains the four ideas this whole project teaches, using plain
English and backend-engineer analogies. Read this once before you touch
any code. Every later lesson assumes you understand this page.

## The one sentence to remember

> A **skill** does one thing. A **workflow** is a path **you** chose. An
> **agent** is a path the **model** chooses. **Agentic AI** is an agent
> that owns a **goal**, with memory, safety limits, and an escape hatch
> to a human.

See [diagrams/four-levels.md](diagrams/four-levels.md) for the full picture.

## Level 1: AI Skill

**What it is:** one small, focused unit of AI work. You give it input, it
gives you output. It has no memory of past calls and makes no decisions
about what happens next.

**Analogy:** a pure function, or a single REST endpoint. `classify(text) ->
category`. Nothing more.

**Example from this project:** `classify_ticket("my payment failed twice")
-> "billing"`.

**Why it matters:** if you cannot build and test ONE skill in isolation,
you have no business chaining ten of them into a workflow or handing them
to an agent. Skills are the unit tests of the AI world.

## Level 2: AI Workflow

**What it is:** several skills chained together in an order **you**
decided at design time. The order is fixed — it does not change based on
what the model "thinks". You add retries, fallbacks, and branching around
the skills, but the shape of the path is yours.

**Analogy:** a CI/CD pipeline (build → test → deploy), or a queue consumer
that always does step 1, then step 2, then step 3.

**Example from this project:** classify → extract fields → score severity
→ draft a reply. If severity is low, skip drafting a reply and just log
it (a branch you decided, not the model).

**Why it matters:** most "AI features" that companies ship are actually
workflows, not agents — and that is usually the RIGHT choice. A workflow
is predictable, cheap, fast, and easy to test, because you already know
every path it can take.

## Level 3: AI Agent

**What it is:** a loop where the **model** decides what to do next, not
you. The model looks at the situation, picks a tool (a database query, a
log search, a calculation), looks at the result, and decides again — until
it thinks it has enough to answer.

**Analogy:** a junior engineer with a runbook and shell access, figuring
out step 2 based on what step 1's command printed. You didn't tell them
the exact commands in advance — you gave them access and a goal.

**Example from this project:** "why did order 8842 fail?" → the agent
decides to query the orders database, then decides to search the logs
around that timestamp, then answers.

**Why it matters — and the tradeoff:** an agent can handle questions you
never anticipated, because the model picks the path. The cost is that the
path is no longer fully predictable, so it is harder to test exhaustively,
slower (each tool call is a round trip), and more expensive (more model
calls). See [07-cost-and-latency.md](07-cost-and-latency.md) for numbers.

## Level 4: Agentic AI

**What it is:** an agent that owns a **goal over time**, not just one
question. It makes a plan, executes it, checks its own work against the
goal (a "critic" step), re-plans when reality surprises it, has hard
limits on steps/time/money, and — critically — knows when a decision is
too risky to make alone and stops to ask a human.

**Analogy:** an on-call team following an incident runbook. They don't
just run one command and stop; they investigate, form a hypothesis, check
it, maybe revise it, and they have a clear rule for "page a human now"
instead of guessing forever.

**Example from this project:** the [incident-triage case study](../tutorial/05-case-study/README.md)
— detect a payment-service error spike, gather evidence from three
sources, form a hypothesis, check it against a runbook, propose a fix,
and **refuse to apply the fix without human approval**.

**Why it matters:** this is where the real safety and reliability
questions live. Anyone can wire a model to a tool. The hard part — and
the part backend engineers are naturally good at — is bounding it: budgets,
timeouts, validation, escalation, audit trails. That is 80% of this
project's content.

## The tradeoffs, side by side

| | Skill | Workflow | Agent | Agentic AI |
|---|---|---|---|---|
| Who decides the path | n/a (no path) | you, at design time | the model, per run | the model, with a plan + limits |
| Predictability | total | total | low-to-medium | medium (bounded by budgets/critic) |
| Cost per run | 1 model call | fixed N model calls | variable, can be high | variable, usually highest |
| Latency | low | low-medium | medium-high | high |
| Handles novel requests | no | no (only what you coded) | yes | yes |
| Easiest to test | yes | yes | harder (non-deterministic) | hardest (use FakeLLM + property tests) |
| When to choose it | one clear transformation | you know every step in advance | the steps genuinely depend on what's found | the task is a standing goal, not one question |
| When NOT to choose it | never — it's the base case | steps can't be known in advance | a workflow would be simpler and cheaper | almost anything simpler will do |

## What "context window" and "tokens" mean (just enough to start)

You do not need the full detail yet — see
[03-llm-basics.md](03-llm-basics.md) for that. For now: a model reads and
writes **tokens** (roughly, word-pieces), and it can only see a limited
number of them at once — the **context window**. Every skill, workflow
step, and agent turn you add makes the conversation longer, which costs
more money and, eventually, gets truncated. This is why the Memory module
(Milestone 5) exists: something has to decide what stays and what gets
dropped, exactly like a cache eviction policy.

## Where to go next

1. [docs/02-setup-windows.md](02-setup-windows.md) — get your machine ready.
2. [docs/03-llm-basics.md](03-llm-basics.md) — tokens, prompts, temperature, cost.
3. [tutorial/01-skills/README.md](../tutorial/01-skills/README.md) — build your first skill.
