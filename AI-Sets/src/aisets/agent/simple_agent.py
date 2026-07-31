"""
`build_simple_agent` — the first, simplest agent: 3 READ-ONLY tools
(query_orders, search_logs, get_metrics), no write tools registered at
all (so `allow_write` doesn't even matter — there's nothing dangerous to
gate), and the step budget from `Settings.max_agent_steps`.
"""

from __future__ import annotations

from aisets.agent.loop import AgentLoop
from aisets.agent.registry import ToolRegistry
from aisets.config import Settings
from aisets.llm.base import LLMClient
from aisets.tools.db import make_query_orders_tool
from aisets.tools.logs import make_search_logs_tool
from aisets.tools.metrics import make_get_metrics_tool

SYSTEM_PROMPT = (
    "You are a backend support investigator. You can call tools to look up "
    "order records, search logs, and check service metrics. Gather evidence "
    "with tools BEFORE answering — don't guess. When you have enough "
    "information, answer the user's question directly and concisely, citing "
    "what you found (order status, log lines, metric values). If you cannot "
    "find a clear answer, say so honestly rather than making one up."
)


def build_simple_agent(llm: LLMClient, settings: Settings) -> AgentLoop:
    registry = ToolRegistry()
    registry.register(make_query_orders_tool(settings.data_dir / "orders.db"))
    registry.register(make_search_logs_tool(settings.data_dir / "app.log"))
    registry.register(make_get_metrics_tool(settings.data_dir / "metrics.json"))

    return AgentLoop(
        llm,
        registry,
        system_prompt=SYSTEM_PROMPT,
        max_steps=settings.max_agent_steps,
        allow_write=False,
    )
