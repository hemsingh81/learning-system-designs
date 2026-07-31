"""Unit tests for agentic/escalation.py — EscalationPolicy and
EscalationGate, including the "no human available -> safe deny" default."""

from __future__ import annotations

from aisets.agentic.escalation import ApprovalRequest, EscalationGate, EscalationPolicy


def test_read_action_high_confidence_is_auto() -> None:
    policy = EscalationPolicy()
    decision = policy.decide(is_write_action=False, risk_level="low", confidence=0.9)
    assert decision.action == "auto"


def test_write_action_always_requires_confirm_regardless_of_confidence() -> None:
    policy = EscalationPolicy(always_confirm_write=True)
    decision = policy.decide(is_write_action=True, risk_level="low", confidence=0.99)
    assert decision.action == "confirm"


def test_high_risk_read_action_is_human_only() -> None:
    policy = EscalationPolicy()
    decision = policy.decide(is_write_action=False, risk_level="high", confidence=0.99)
    assert decision.action == "human_only"


def test_low_confidence_read_action_is_human_only() -> None:
    policy = EscalationPolicy(min_auto_confidence=0.7)
    decision = policy.decide(is_write_action=False, risk_level="low", confidence=0.3)
    assert decision.action == "human_only"


def test_gate_auto_decision_needs_no_human_callback() -> None:
    gate = EscalationGate(EscalationPolicy(), human_approve=None)
    record = gate.request(
        action="search_logs", arguments={}, is_write_action=False,
        risk_level="low", confidence=0.9, reasoning="safe lookup",
    )
    assert record.approved is True
    assert record.decided_by == "auto"


def test_gate_confirm_decision_uses_human_callback() -> None:
    def approve(req: ApprovalRequest) -> bool:
        assert req.action == "restart_service"
        return True

    gate = EscalationGate(EscalationPolicy(), human_approve=approve)
    record = gate.request(
        action="restart_service", arguments={"service_name": "payments"}, is_write_action=True,
        risk_level="low", confidence=0.9, reasoning="runbook says restart",
    )
    assert record.approved is True
    assert record.decided_by == "human"


def test_gate_with_no_human_available_denies_safely_by_default() -> None:
    gate = EscalationGate(EscalationPolicy(), human_approve=None)
    record = gate.request(
        action="restart_service", arguments={}, is_write_action=True,
        risk_level="low", confidence=0.9, reasoning="needs confirm but nobody is here",
    )
    assert record.approved is False
    assert record.decided_by == "no_human_available"


def test_gate_keeps_an_audit_trail_of_every_request() -> None:
    gate = EscalationGate(EscalationPolicy(), human_approve=lambda req: True)
    gate.request(action="a", arguments={}, is_write_action=False, risk_level="low", confidence=0.9, reasoning="r1")
    gate.request(action="b", arguments={}, is_write_action=True, risk_level="low", confidence=0.9, reasoning="r2")
    assert len(gate.records) == 2
    assert gate.records[0].request.action == "a"
    assert gate.records[1].request.action == "b"
