"""
`ToolRegistry` — where every tool an agent MIGHT use is registered, and
the single gate that decides whether a 'write' tool is actually allowed
to run right now.

Why a separate `allow_write` gate instead of just registering fewer
tools: the SAME registry (with the SAME tools) is used for both a
read-only investigation phase and a write-allowed action phase in the
Agentic modules (Milestone 6+) — the gate lets one registry serve both,
rather than needing two separate tool sets kept in sync.
"""

from __future__ import annotations

from aisets.agent.tools import ToolError, ToolMeta, ToolPermissionError, get_tool_meta, validate_and_call
from aisets.llm.base import ToolSpec


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolMeta] = {}

    def register(self, tool_func) -> "ToolRegistry":
        meta = get_tool_meta(tool_func)
        self._tools[meta.name] = meta
        return self

    def register_all(self, tool_funcs) -> "ToolRegistry":
        for tool_func in tool_funcs:
            self.register(tool_func)
        return self

    def specs(self, *, allow_write: bool = False) -> list[ToolSpec]:
        """The tool specs to hand the model — this is what the model
        actually sees. A 'write' tool is not even OFFERED unless
        `allow_write=True`, so a read-only agent can't be tricked into
        attempting one (it wouldn't know it exists)."""
        return [
            meta.spec
            for meta in self._tools.values()
            if allow_write or meta.permission == "read"
        ]

    def invoke(self, name: str, arguments: dict, *, allow_write: bool = False):
        meta = self._tools.get(name)
        if meta is None:
            raise ToolError(f"unknown tool '{name}' — not registered in this ToolRegistry.")
        if meta.permission == "write" and not allow_write:
            raise ToolPermissionError(
                f"tool '{name}' requires write permission, which is not allowed in this context."
            )
        return validate_and_call(meta, arguments)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __len__(self) -> int:
        return len(self._tools)
