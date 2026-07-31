"""
Example 01 — the smallest possible skill run.

What this shows: a Skill is just `run(text) -> a typed Pydantic object`.
No memory, no branching, no tools. Read this file top to bottom, then run:

    .\\scripts\\run-example.ps1 01_skill_hello

Switch .env's LLM_BACKEND from "fake" to "claude" (with a real API key)
and run it again — the code below does not change at all.
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.skills.classify_ticket import ClassifyTicket, TicketCategory

TICKET_TEXT = "I was charged twice for my subscription this month, please refund the duplicate charge."


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        # Script the ONE response this demo needs. In real life (LLM_BACKEND=claude)
        # this block is skipped entirely and a real model answers instead.
        llm.queue_json({"category": "billing", "confidence": 0.94})

    skill = ClassifyTicket(llm)
    result: TicketCategory = skill.run(TICKET_TEXT)

    console.print(f"\nTicket text: [italic]{TICKET_TEXT!r}[/italic]")
    console.print(f"Category:    [bold]{result.category}[/bold]")
    console.print(f"Confidence:  {result.confidence:.2f}")
    console.print(f"\nResult is a typed object: {type(result).__name__}(category={result.category!r}, confidence={result.confidence})")


if __name__ == "__main__":
    main()
