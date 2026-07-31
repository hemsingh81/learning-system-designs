# Async parallel tool calls (appendix)

`src/aisets/agent/loop.py` is deliberately SYNCHRONOUS and handles ONE
tool call per turn (`tutorial/03-agents/DECISIONS.md` D-301) — the right
choice for learning the loop clearly. This appendix shows the async
version and MEASURES the latency win when a turn's tool calls are
genuinely independent of each other.

## Why this is separate from the main project

Async code doubles the concepts you need to hold in your head at once
(the loop's logic AND Python's `asyncio` model) — mixing them into
Milestone 5 would have made the FIRST agent harder to learn, for a
benefit (latency) that doesn't matter until you have multiple
independent tool calls per turn. This appendix exists once you're ready
for that next step.

## The synchronous version (what Milestone 5 does)

```python
result = registry.invoke(tool_call.name, tool_call.arguments)
# one tool call, one wait, then continue
```

If a turn genuinely needs 3 independent lookups (e.g. "check payments
metrics AND checkout metrics AND auth metrics"), the sync loop still only
handles the FIRST tool call per turn (by design) — so 3 independent
lookups take 3 separate turns, each a full model round trip.

## The async version

```python
import asyncio

async def run_tool_calls_concurrently(registry, tool_calls, *, allow_write=False):
    async def invoke_one(tool_call):
        # ToolRegistry.invoke is sync; run it in a thread so it doesn't
        # block the event loop (most tools here do blocking I/O: sqlite,
        # file reads).
        return await asyncio.to_thread(
            registry.invoke, tool_call.name, tool_call.arguments, allow_write=allow_write
        )

    return await asyncio.gather(*(invoke_one(tc) for tc in tool_calls))
```

If the model's `LLMResponse.tool_calls` contains MULTIPLE calls in one
turn (real Claude tool-use supports this — this project's `AgentLoop`
just chooses not to act on more than the first, per D-301), you can run
them all concurrently with `asyncio.gather`, then feed all their results
back as separate `tool` messages before the next turn.

## Measuring the latency win

`benchmark.py` in this folder simulates 3 tool calls, each with an
artificial 200ms delay (representing a slow DB query, log search, and
metrics fetch), run sequentially vs. concurrently:

```powershell
cd appendix\async-parallel-tools
python benchmark.py
```

Expected output (illustrative — exact numbers vary by machine):
```
Sequential: 3 calls x ~200ms each = ~600ms total
Concurrent: 3 calls run together = ~200ms total (bounded by the slowest one)
Speedup: ~3.0x
```

## The tradeoff this appendix doesn't hide

Concurrency isn't free:
- **Error handling gets harder.** If 2 of 3 concurrent calls succeed and
  1 fails, what do you feed back to the model? (This project's sync loop
  sidesteps this — see `docs/01-concepts.md`'s accuracy/latency tradeoff
  table for the general shape of this tradeoff.)
- **Loop detection needs rethinking.** `AgentLoop`'s loop detection
  compares ONE call at a time; a concurrent batch needs to detect a
  REPEATED BATCH, not just a repeated single call.
- **Debugging is harder.** A sequential trace (this project's default) is
  trivial to read top to bottom. A concurrent trace requires reasoning
  about interleaving.

**Rule of thumb:** reach for this only once you've measured (not
guessed) that tool-call latency, not model "thinking" time, dominates
your agent's wall-clock time, AND your tool calls are genuinely
independent of each other's results.
