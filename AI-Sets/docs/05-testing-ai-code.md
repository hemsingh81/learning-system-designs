# 05 — Testing AI code

The hardest new problem AI code adds to your existing testing skills:
**the same input doesn't always produce the same output.** A real model
can phrase things differently every time, even at low temperature. This
page explains how this project tests AI code anyway, reliably.

## The core idea: test AGAINST a fake, test the FAKE's realism separately

Every test in `tests/unit/` and `tests/integration/` runs against
`FakeLLM` (see `src/aisets/llm/fake.py`), never the real API. `FakeLLM`
returns EXACTLY what you scripted, every time — so testing your CODE
(does the retry logic work? does validation reject bad output? does the
branch condition fire correctly?) becomes completely deterministic, the
same way testing a payment flow against a mocked payment gateway lets you
test your OWN logic without depending on a real, slow, flaky external
service.

The separate question — "does a REAL model actually behave the way I
scripted?" — is answered by the small `tests/live/` suite (see below),
run occasionally and deliberately, never as part of your fast feedback
loop.

## The three test tiers in this project

```
tests/unit/          <- FakeLLM only. No filesystem outside tmp_path.
                         Runs in milliseconds. This is your fast loop.

tests/integration/    <- FakeLLM + REAL sample data (SQLite, log files,
                         runbooks). Tests full pipelines/agents/the case
                         study end to end. Still fast (~3 seconds total).

tests/live/           <- The REAL Anthropic API. Costs real (tiny) money.
                         Excluded by default (see pyproject.toml's
                         `addopts = "-m 'not live'"`). Run deliberately:
                             .\scripts\test.ps1 -Live
```

## The five-case template every skill/tool test follows

See `docs/00-PLAN.md` section 5 and `tutorial/01-skills/README.md`
section 10. Every skill gets tests for:
1. **Happy path** — a normal, valid scripted response.
2. **Empty input** — proven to never even call the model
   (`assert len(fake_llm.calls) == 0`).
3. **Oversized input** — proven to be truncated before reaching the model.
4. **Malformed/out-of-range output** — proven to retry once, then raise
   `BadOutput` if it's still bad.
5. **Prompt injection** — proven that an injected instruction cannot
   produce an out-of-schema answer.

## How to script a `FakeLLM` response

```python
from aisets.llm.fake import FakeLLM

fake_llm = FakeLLM()  # the `fake_llm` pytest fixture gives you one of these

# For a skill's complete_json() call:
fake_llm.queue_json({"category": "billing", "confidence": 0.9})

# For a deliberately broken response (tests error handling):
fake_llm.queue_invalid_json("not json at all")

# For a simulated infrastructure failure (tests retry/fallback):
from aisets.llm.errors import RateLimited
fake_llm.queue_error(RateLimited("simulated 429"))

# For an agent's tool-calling turn:
from aisets.llm.base import LLMResponse, ToolCall
fake_llm.queue_response(LLMResponse(
    text=None,
    tool_calls=[ToolCall(id="c1", name="search_logs", arguments={"query": "ERROR"})],
    stop_reason="tool_use",
))

# For order-independent matching (any call containing "refund" -> this reply):
from aisets.llm.fake import contains
fake_llm.add_rule(contains("refund"), LLMResponse(text="billing"))
```

`fake_llm.calls` records every call made (messages, system prompt, tools
offered) — use it to assert things like "the write tool was never even
offered" (see `test_write_tool_is_not_offered_when_allow_write_false`).

## Testing non-deterministic AGENT behavior deterministically

An agent's PATH varies by design (Milestone 5) — so how do you test it?
By scripting the exact sequence of model turns and asserting on the
RESULTING trace, not by asserting "the agent behaves reasonably" in the
abstract:

```python
fake_llm.queue_response(LLMResponse(tool_calls=[...], stop_reason="tool_use"))
fake_llm.queue_text("final answer")

result = agent.run("question")

assert result.stopped_reason == "answered"
assert result.steps[0].tool_name == "search_logs"
```

This tests "given this exact sequence of model decisions, does the LOOP
behave correctly" (budget, loop detection, error handling) — which is
exactly what your code controls. Whether a REAL model would make those
same decisions is a separate, live-test question.

## Testing time-dependent code (budgets) without sleeping

`tests/unit/test_agentic_budget.py` injects a fake clock instead of using
real `time.sleep()`:

```python
def make_fake_clock():
    state = {"now": 0.0}
    def clock(): return state["now"]
    def advance(seconds): state["now"] += seconds
    return clock, advance

clock, advance = make_fake_clock()
budget = Budget(limits=..., clock=clock)
budget.start()
advance(100.0)  # instantly "100 seconds later", no real waiting
```

## Writing a `live` test (optional, deliberate)

```python
import pytest

pytestmark = pytest.mark.live  # excluded by default

def test_real_model_classifies_a_ticket():
    # ... build a real ClaudeLLM, skip if no API key ...
    result = skill.run("real ticket text")
    assert result.category in {"billing", "bug", "how_to", "feature_request", "outage", "unknown"}
    # Assert the SHAPE/membership, never exact wording — real model
    # output legitimately varies between calls and model versions.
```

## Commands

```powershell
.\scripts\test.ps1                                   # unit + integration, fast, free
.\scripts\test.ps1 -Path tests\unit\test_llm_fake.py  # one file
.\scripts\test.ps1 -Live                              # the live suite, needs ANTHROPIC_API_KEY
python -m pytest --cov=src\aisets --cov-report=term-missing  # coverage report
```

## What NOT to do

- Don't assert exact model wording against `ClaudeLLM` — assert shape,
  membership in an enum, or bounds instead.
- Don't skip the empty/oversized/malformed/injection cases "because the
  happy path works" — those are exactly where AI code differs from
  normal code, and where most real incidents in AI systems originate.
- Don't let a `live` test run in your normal test loop — it's slow, costs
  money, and its non-determinism defeats the purpose of a fast feedback loop.
