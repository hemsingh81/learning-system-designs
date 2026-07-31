"""
Example 13 — Escalation: three scenarios showing the policy in action.
1. A read-only, high-confidence action proceeds AUTOMATICALLY.
2. A write action always needs human CONFIRMATION, regardless of confidence.
3. A high-risk action is HUMAN_ONLY, and here the (simulated) human says no.

Run:
    .\\scripts\\run-example.ps1 13_agentic_escalation
"""

from __future__ import annotations

from _common import console, setup

from aisets.agentic.escalation import ApprovalRequest, EscalationGate, EscalationPolicy


def simulated_human_always_approves(request: ApprovalRequest) -> bool:
    console.print(f"  [dim](simulated human sees request: {request.action} — risk={request.risk_level}, reason: {request.reasoning})[/dim]")
    return True


def simulated_human_always_declines(request: ApprovalRequest) -> bool:
    console.print(f"  [dim](simulated human sees request: {request.action} — risk={request.risk_level}, reason: {request.reasoning})[/dim]")
    return False


def main() -> None:
    setup()
    policy = EscalationPolicy(always_confirm_write=True, min_auto_confidence=0.6)

    console.rule("1. Read-only action, high confidence -> AUTO")
    gate1 = EscalationGate(policy, human_approve=simulated_human_always_approves)
    record1 = gate1.request(
        action="search_logs",
        arguments={"query": "payments timeout"},
        is_write_action=False,
        risk_level="low",
        confidence=0.9,
        reasoning="A read-only lookup, no side effects.",
    )
    console.print(f"Decision: approved={record1.approved}, decided_by={record1.decided_by}")

    console.rule("2. Write action, high confidence -> still requires CONFIRM")
    gate2 = EscalationGate(policy, human_approve=simulated_human_always_approves)
    record2 = gate2.request(
        action="restart_service",
        arguments={"service_name": "payments", "reason": "connection pool exhausted"},
        is_write_action=True,
        risk_level="medium",
        confidence=0.95,
        reasoning="Runbook-recommended restart for a resource-exhaustion pattern.",
    )
    console.print(f"Decision: approved={record2.approved}, decided_by={record2.decided_by}")

    console.rule("3. High-risk action -> HUMAN_ONLY, and the human says no")
    gate3 = EscalationGate(policy, human_approve=simulated_human_always_declines)
    record3 = gate3.request(
        action="scale_service",
        arguments={"service_name": "payments", "target_instances": 20},
        is_write_action=True,
        risk_level="high",
        confidence=0.4,
        reasoning="Uncertain whether scaling addresses an upstream gateway outage.",
    )
    console.print(f"Decision: approved={record3.approved}, decided_by={record3.decided_by}")

    console.print(f"\n[bold]Audit trail (gate 3):[/bold] {len(gate3.records)} record(s) kept, "
                  f"first approved={gate3.records[0].approved}")


if __name__ == "__main__":
    main()
