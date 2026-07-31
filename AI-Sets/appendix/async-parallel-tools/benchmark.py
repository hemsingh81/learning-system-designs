"""
Measures the latency difference between running 3 "tool calls" (each
simulating a 200ms blocking I/O operation — a DB query, a log search, a
metrics fetch) sequentially vs. concurrently.

Run:
    python appendix\\async-parallel-tools\\benchmark.py
"""

from __future__ import annotations

import asyncio
import time


def slow_tool_call(name: str, delay_seconds: float = 0.2) -> str:
    """Simulates a blocking I/O tool call (e.g. a DB query)."""
    time.sleep(delay_seconds)
    return f"{name}: done"


async def run_sequentially(names: list[str]) -> list[str]:
    results = []
    for name in names:
        result = await asyncio.to_thread(slow_tool_call, name)
        results.append(result)
    return results


async def run_concurrently(names: list[str]) -> list[str]:
    return await asyncio.gather(*(asyncio.to_thread(slow_tool_call, name) for name in names))


async def main() -> None:
    names = ["query_orders", "search_logs", "get_metrics"]

    start = time.monotonic()
    await run_sequentially(names)
    sequential_elapsed = time.monotonic() - start

    start = time.monotonic()
    await run_concurrently(names)
    concurrent_elapsed = time.monotonic() - start

    print(f"Sequential: {len(names)} calls x ~200ms each = {sequential_elapsed:.3f}s total")
    print(f"Concurrent: {len(names)} calls run together = {concurrent_elapsed:.3f}s total")
    print(f"Speedup: {sequential_elapsed / concurrent_elapsed:.1f}x")


if __name__ == "__main__":
    asyncio.run(main())
