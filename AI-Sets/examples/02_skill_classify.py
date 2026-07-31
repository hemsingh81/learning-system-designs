"""
Example 02 — classify a batch of real sample tickets.

What this shows: the SAME skill instance, called once per ticket, with no
memory between calls — this is what "no memory" means concretely. Ticket
#7's answer has zero influence on ticket #8's answer.

Run:
    .\\scripts\\run-example.ps1 02_skill_classify
"""

from __future__ import annotations

from _common import console, is_fake, load_tickets, setup

from aisets.llm.fake import contains
from aisets.skills.classify_ticket import ClassifyTicket


def main() -> None:
    settings, llm = setup()
    tickets = load_tickets(settings)
    clean_tickets = [t for t in tickets if t["kind"] == "clean"]

    if is_fake(llm):
        # Script one rule per clean ticket (matched by a distinctive
        # substring), so the demo is deterministic without a real model.
        for t in clean_tickets:
            snippet = t["text"][:35]
            llm.add_rule(
                contains(snippet),
                _canned_response(t["category_hint"]),
            )

    skill = ClassifyTicket(llm)

    console.print(f"\nClassifying {len(clean_tickets)} sample tickets:\n")
    for t in clean_tickets:
        result = skill.run(t["text"])
        match = "OK" if result.category == t["category_hint"] else "DIFFERENT"
        console.print(
            f"[{t['id']}] expected={t['category_hint']:<16} got={result.category:<16} "
            f"confidence={result.confidence:.2f}  [{match}]"
        )


def _canned_response(category: str):
    from aisets.llm.base import LLMResponse
    import json

    return LLMResponse(text=json.dumps({"category": category, "confidence": 0.9}))


if __name__ == "__main__":
    main()
