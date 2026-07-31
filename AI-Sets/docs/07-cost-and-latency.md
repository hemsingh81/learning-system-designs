# 07 — Cost and latency

Every number on this page is **illustrative**, computed from
`src/aisets/llm/usage.py`'s pricing table and a typical small-prompt size
for this project's skills (roughly 250-400 input tokens, 50-150 output
tokens per call). Check https://www.anthropic.com/pricing for current
real prices, and measure your OWN actual usage with `UsageTracker` before
relying on any number here for a real budget decision.

## How to measure your own real cost and latency

```python
import time
from aisets.llm.usage import UsageTracker

tracker = UsageTracker(model=settings.claude_model)
start = time.monotonic()

response = llm.complete(messages, system=system_prompt)
tracker.record(response.usage)

elapsed = time.monotonic() - start
print(f"{elapsed:.2f}s, {tracker.summary()}")
```

Every `LLMResponse` carries real `usage` (input/output token counts) —
`ClaudeLLM` reports the provider's actual counts; `FakeLLM` estimates
from character length (see `docs/03-llm-basics.md`) purely for demo
purposes, never for a real budget decision.

## Illustrative cost per call (claude-3-5-haiku-latest pricing)

At roughly 300 input / 100 output tokens per call:
`(300/1,000,000 × $0.80) + (100/1,000,000 × $4.00) ≈ $0.0006 per call`

| Scenario | Model calls | Illustrative cost | Illustrative latency (sequential) |
|---|---|---|---|
| One skill call (`classify_ticket`) | 1 | ~$0.0006 | ~0.5-1.5s |
| `summarize_log` on a long log (3 chunks) | 4 (3 chunk + 1 combine) | ~$0.0024 | ~2-6s |
| Full `ticket_pipeline` (severity ≥ medium) | 4 | ~$0.0024 | ~2-6s |
| Full `ticket_pipeline` (severity low, reply skipped) | 3 | ~$0.0018 | ~1.5-4.5s |
| Agent investigation (example 08, 3 turns) | 3 | ~$0.0018 | ~1.5-4.5s |
| Case study `easy` (1 attempt: plan+investigate+critic) | 4 | ~$0.0024 | ~2-6s |
| Case study `ambiguous`/`trap` (2 attempts) | 8 | ~$0.0048 | ~4-12s |
| Multi-agent team (3 specialists + synthesis) | 5 | ~$0.003 | ~2.5-7.5s (specialists could run in PARALLEL — see note below) |

**Scale check:** processing 10,000 tickets/day through the full pipeline
at ~$0.0024/ticket ≈ **$24/day, ~$720/month** — cheap in absolute terms,
but the number that should make you pause is the MULTIPLIER: an agentic
system that needs 2 re-plan attempts costs 2x a single-attempt one, and a
multi-agent team costs roughly (number of specialists + 1) x a single
agent. None of these costs are hidden — `Budget` (Milestone 6) exists so
you can put a hard number on the worst case before it happens.

## Tradeoff: accuracy vs. latency

- **Lower temperature** (this project's default, near 0) trades some
  creative variety for more consistent, predictable output — the right
  trade for classification/extraction/scoring tasks, wrong for creative
  writing.
- **More investigation steps** (a bigger `max_steps`, more re-plan
  attempts) generally improves accuracy on hard questions but multiplies
  latency linearly (each step is a full round trip) — there are
  diminishing returns past a handful of steps; if step N+1 rarely changes
  the answer, it isn't worth the latency.
- **Chunking long input** (`summarize_log`, Milestone 2 D-105) trades more
  calls (more latency) for not silently dropping information — worth it
  for a log file where the important part could be anywhere, not worth it
  for a short support ticket where truncating the tail rarely matters.

## Tradeoff: cost vs. capability

- **Skill → Workflow**: same cost (a workflow is just skills in a fixed
  order) — no capability tradeoff here, just added predictability.
- **Workflow → Agent**: cost becomes VARIABLE and generally HIGHER (each
  tool call is a full model round trip) in exchange for handling
  questions you didn't anticipate. If a workflow already covers your
  cases, don't pay for an agent's flexibility you don't need.
- **Agent → Agentic AI**: cost rises again (Planner + Critic + possible
  re-plans) in exchange for self-checking and safe escalation. This is
  worth it exactly when being WRONG is expensive — an incident
  investigation that recommends the wrong fix costs far more than a few
  extra cents of model calls.
- **One agent → Multi-agent**: cost roughly scales with the number of
  specialists (see `tutorial/04-agentic/README.md` section 12's tradeoff
  table) — only worth it when the sub-tasks are genuinely independent and
  benefit from different tools/prompts.

## Reducing cost without reducing correctness

1. **Cache identical requests** if your workload has repeats (not
   implemented in this project — would live as a wrapper around
   `LLMClient.complete_json`, keyed by a hash of the messages+schema).
2. **Use a cheaper model for easier steps.** `Settings.claude_model` is
   one global setting in this project for simplicity — a real system
   might use a cheaper model for `classify_ticket` and a stronger one for
   the Critic, since a wrong classification is cheap to notice and a
   wrong critic verdict is not.
3. **Lower `max_steps`/`max_attempts` once you've measured that fewer
   steps rarely change the outcome** — don't guess at the right number,
   measure it (see `docs/00-PLAN.md`'s testing plan for how to do this
   with real logged runs).
4. **Prefer a Workflow over an Agent, and an Agent over Agentic AI,**
   whenever the simpler level already gets the job done — see
   `docs/01-concepts.md`'s tradeoff table. This is the single biggest
   lever: most of the cost difference between levels comes from HOW MANY
   MODEL CALLS a task needs, and the simpler levels need fewer by
   construction.

## A latency note on multi-agent parallelism

`src/aisets/agentic/orchestrator.py`'s `Supervisor.run` calls each
specialist SEQUENTIALLY in this project (`[s.run(task) for s in
specialists]`), which is the simplest, most traceable version to learn
from. In a real deployment, specialists with no dependency on each
other's output could run concurrently (see `appendix/async-parallel-tools/`
for the async mechanics and a measured latency comparison) — turning "3
specialists = 3x the latency" into closer to "3 specialists = ~1x the
latency of the slowest one", at the cost of more complex error handling
(what do you do if two specialists finish at very different times?).
