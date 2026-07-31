"""Unit tests for tools/actions.py — the simulated write tools and their
audit trail."""

from __future__ import annotations

from aisets.agent.registry import ToolRegistry
from aisets.tools.actions import AuditLog, make_page_oncall_tool, make_restart_service_tool, make_scale_service_tool


def test_restart_service_is_simulated_and_audited() -> None:
    audit = AuditLog()
    restart_service = make_restart_service_tool(audit)

    result = restart_service(service_name="payments", reason="pool exhausted")

    assert result["status"] == "ok"
    assert "simulated" in result["message"]
    assert len(audit.entries) == 1
    assert audit.entries[0].action == "restart_service"
    assert audit.entries[0].arguments["reason"] == "pool exhausted"


def test_scale_service_is_simulated_and_audited() -> None:
    audit = AuditLog()
    scale_service = make_scale_service_tool(audit)

    result = scale_service(service_name="checkout", target_instances=5, reason="high load")

    assert "5 instances" in result["message"]
    assert audit.entries[0].arguments["target_instances"] == 5


def test_page_oncall_is_simulated_and_audited() -> None:
    audit = AuditLog()
    page_oncall = make_page_oncall_tool(audit)

    result = page_oncall(service_name="payments", severity="critical", message="full outage")

    assert "simulated" in result["message"]
    assert audit.entries[0].arguments["severity"] == "critical"


def test_write_tools_require_allow_write_through_the_registry() -> None:
    from aisets.agent.tools import ToolPermissionError
    import pytest

    audit = AuditLog()
    restart_service = make_restart_service_tool(audit)
    registry = ToolRegistry().register(restart_service)

    with pytest.raises(ToolPermissionError):
        registry.invoke("restart_service", {"service_name": "payments", "reason": "test"})

    # With allow_write=True, it goes through AND still gets audited.
    result = registry.invoke(
        "restart_service", {"service_name": "payments", "reason": "test"}, allow_write=True
    )
    assert result["status"] == "ok"
    assert len(audit.entries) == 1
