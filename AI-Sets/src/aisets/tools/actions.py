"""
Write tools: `restart_service`, `scale_service`, `page_oncall`.

EVERY action here is SIMULATED — no real service is ever touched, no real
page is ever sent. This project never talks to a real broker/infra API.
Each action still writes to an `AuditLog`, because "simulate the effect,
but always keep a real record of what would have happened and why" is the
pattern you'd want for any REAL write action too — see
docs/06-security-and-privacy.md's section on tool permissions.

These are 'write' tools (`permission="write"`), meaning `ToolRegistry`
refuses to run them unless the caller explicitly passes `allow_write=True`
— see Milestone 6's escalation module for where that gate is actually
decided (a human, not the model, flips it on).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aisets.agent.tools import tool


@dataclass
class AuditEntry:
    action: str
    arguments: dict
    result: str


@dataclass
class AuditLog:
    entries: list[AuditEntry] = field(default_factory=list)

    def record(self, action: str, arguments: dict, result: str) -> None:
        self.entries.append(AuditEntry(action=action, arguments=arguments, result=result))


def make_restart_service_tool(audit: AuditLog):
    @tool(permission="write", name="restart_service")
    def restart_service(service_name: str, reason: str) -> dict:
        """Restart a backend service. SIMULATED ONLY — no real service is
        ever touched. `reason` is required and is recorded in the audit
        log. Only call this after a runbook confirms a restart is the
        appropriate action — restarting during a genuine upstream outage
        (rather than a local resource-exhaustion problem) does nothing
        and adds risk."""
        result = f"service '{service_name}' restarted (simulated)"
        audit.record("restart_service", {"service_name": service_name, "reason": reason}, result)
        return {"status": "ok", "message": result}

    return restart_service


def make_scale_service_tool(audit: AuditLog):
    @tool(permission="write", name="scale_service")
    def scale_service(service_name: str, target_instances: int, reason: str) -> dict:
        """Scale a backend service to `target_instances` instances.
        SIMULATED ONLY. `reason` is required and is recorded in the audit
        log. Only helps for load-related degradation, not an upstream
        dependency outage."""
        result = f"service '{service_name}' scaled to {target_instances} instances (simulated)"
        audit.record(
            "scale_service",
            {"service_name": service_name, "target_instances": target_instances, "reason": reason},
            result,
        )
        return {"status": "ok", "message": result}

    return scale_service


def make_page_oncall_tool(audit: AuditLog):
    @tool(permission="write", name="page_oncall")
    def page_oncall(service_name: str, severity: str, message: str) -> dict:
        """Page the on-call engineer for `service_name` with the given
        `severity` (low/medium/high/critical) and a short `message`.
        SIMULATED ONLY — no real page is sent."""
        result = f"on-call paged for '{service_name}' (severity={severity}) (simulated)"
        audit.record(
            "page_oncall",
            {"service_name": service_name, "severity": severity, "message": message},
            result,
        )
        return {"status": "ok", "message": result}

    return page_oncall
