"""Read tool: `search_logs` — a simple substring search over the sample
backend log file, the agent's equivalent of `grep`."""

from __future__ import annotations

from pathlib import Path

from aisets.agent.tools import tool


def make_search_logs_tool(log_path: Path):
    @tool(permission="read", name="search_logs")
    def search_logs(query: str, max_lines: int = 20) -> list[str]:
        """Search the backend service log for lines containing `query`
        (case-insensitive substring match, e.g. 'payments' or 'timeout' or
        'ERROR'). Returns at most `max_lines` matching lines, in the order
        they appear in the log (oldest first). Use this to find OUT WHY
        something happened around a given time — pair with query_orders
        for WHAT happened and get_metrics for HOW BAD it was."""
        if not query.strip():
            return []
        text = Path(log_path).read_text(encoding="utf-8")
        matches = [line for line in text.splitlines() if query.lower() in line.lower()]
        return matches[:max_lines]

    return search_logs
