"""
Example 09 — memory: short-term trimming within one run, and long-term
facts that survive across separate runs (even separate processes), as
long as they point at the same SQLite file.

Run:
    .\\scripts\\run-example.ps1 09_agent_with_memory
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from _common import console, setup

from aisets.agent.memory import ConversationMemory, LongTermMemory
from aisets.llm.base import Message


def demo_short_term_trimming() -> None:
    console.rule("1. Short-term memory: trimming under a char budget")
    memory = ConversationMemory(max_chars=200)

    memory.add(Message(role="user", content="ORIGINAL QUESTION: why is payments slow?" + " " * 40))
    for i in range(5):
        memory.add(Message(role="tool", content=f"tool result #{i}: " + ("x" * 50)))

    console.print(f"Messages kept: {len(memory.as_list())}")
    for m in memory.as_list():
        console.print(f"  [{m.role}] {m.content[:50]}...")
    console.print(
        "\n[dim]Notice the ORIGINAL QUESTION is still message #0 even though several "
        "tool results were trimmed to stay under the char budget.[/dim]"
    )


def demo_long_term_memory_across_runs() -> None:
    console.rule("2. Long-term memory: persists across separate agent runs")
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "agent_memory.db"

        console.print("[bold]Run 1[/bold] (a fresh LongTermMemory instance)")
        run1_memory = LongTermMemory(db_path)
        run1_memory.remember("known_root_cause:payments", "payment_gateway_timeout")
        console.print("  Remembered: known_root_cause:payments = payment_gateway_timeout")

        console.print("\n[bold]Run 2[/bold] (a DIFFERENT LongTermMemory instance, same db file)")
        run2_memory = LongTermMemory(db_path)
        recalled = run2_memory.recall("known_root_cause:payments")
        console.print(f"  Recalled: known_root_cause:payments = {recalled!r}")

        console.print(f"\n  All facts in storage: {run2_memory.all_facts()}")


def main() -> None:
    setup()
    demo_short_term_trimming()
    demo_long_term_memory_across_runs()


if __name__ == "__main__":
    main()
