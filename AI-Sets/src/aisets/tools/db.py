"""
Read tool: `query_orders` — the agent's window into the (fake) orders
database.

Every tool factory in this project takes a PATH as a parameter and
returns the decorated function, instead of hard-coding a path inside the
function body. This is the same reason you'd inject a connection string
into a repository class rather than hard-coding it: it makes the tool
testable against a throwaway copy of the data (see `tmp_orders_db` in
`tests/conftest.py`) instead of always touching the real sample data.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from aisets.agent.tools import tool


def make_query_orders_tool(db_path: Path):
    @tool(permission="read", name="query_orders")
    def query_orders(
        order_id: str | None = None,
        status: str | None = None,
        service: str | None = None,
        limit: int = 20,
    ) -> list[dict]:
        """Query orders from the orders database. Optionally filter by
        `order_id` (an exact order number, e.g. '9002'), `status` (one of:
        completed, pending, failed, refunded), and/or `service` (e.g.
        'payments', 'checkout', 'billing'). Returns at most `limit` rows
        (default 20), most recent first. Use this to find out WHAT
        happened to a specific order/customer, not why — pair with
        search_logs for the 'why'."""
        conn = sqlite3.connect(db_path)
        try:
            conn.row_factory = sqlite3.Row
            query = "SELECT * FROM orders WHERE 1=1"
            params: list = []
            if order_id is not None:
                query += " AND order_id = ?"
                params.append(int(order_id))
            if status is not None:
                query += " AND status = ?"
                params.append(status)
            if service is not None:
                query += " AND service = ?"
                params.append(service)
            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)
            rows = conn.execute(query, params).fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    return query_orders
