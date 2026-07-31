"""
Example 03 — structured output in depth: extract_fields.

What this shows: the model returns a typed object with OPTIONAL fields
(order_id, amount_usd, customer_email may be None) instead of a string you
have to parse. Notice how the two tickets below get genuinely different
shapes back — one has an amount, one doesn't, and neither is "wrong".

Run:
    .\\scripts\\run-example.ps1 03_skill_structured_output
"""

from __future__ import annotations

from _common import console, is_fake, setup

from aisets.skills.extract_fields import ExtractFields

TICKET_WITH_AMOUNT = (
    "My invoice for May shows the wrong plan tier (Pro instead of Starter). "
    "I was charged $49.00 but should have been charged $19.00. My email on "
    "file is jane.doe@example.com."
)
TICKET_WITHOUT_AMOUNT = "How do I change the email address on my account?"


def main() -> None:
    settings, llm = setup()

    if is_fake(llm):
        llm.queue_json({
            "order_id": None,
            "amount_usd": 49.00,
            "customer_email": "jane.doe@example.com",
            "issue_summary": "Customer was billed Pro tier pricing but expected Starter tier pricing.",
        })
        llm.queue_json({
            "order_id": None,
            "amount_usd": None,
            "customer_email": None,
            "issue_summary": "Customer wants to change the email address on their account.",
        })

    skill = ExtractFields(llm)

    for label, text in [("WITH amount/email", TICKET_WITH_AMOUNT), ("WITHOUT amount/email", TICKET_WITHOUT_AMOUNT)]:
        result = skill.run(text)
        console.print(f"\n[bold]{label}[/bold]")
        console.print(f"  order_id:       {result.order_id!r}")
        console.print(f"  amount_usd:     {result.amount_usd!r}")
        console.print(f"  customer_email: {result.customer_email!r}")
        console.print(f"  issue_summary:  {result.issue_summary!r}")

    console.print(
        "\n[dim]Notice: the second result has amount_usd=None and customer_email=None "
        "— the skill did NOT invent values that weren't in the text.[/dim]"
    )


if __name__ == "__main__":
    main()
