"""Unit tests for tools/db.py — query_orders against a throwaway copy of
the seeded orders.db."""

from __future__ import annotations

from aisets.tools.db import make_query_orders_tool


def test_query_orders_no_filters_returns_rows(tmp_orders_db) -> None:
    query_orders = make_query_orders_tool(tmp_orders_db)
    rows = query_orders(limit=5)
    assert len(rows) == 5
    assert "order_id" in rows[0]


def test_query_orders_filters_by_status(tmp_orders_db) -> None:
    query_orders = make_query_orders_tool(tmp_orders_db)
    rows = query_orders(status="failed", limit=100)
    assert len(rows) > 0
    assert all(r["status"] == "failed" for r in rows)


def test_query_orders_filters_by_service(tmp_orders_db) -> None:
    query_orders = make_query_orders_tool(tmp_orders_db)
    rows = query_orders(service="payments", status="failed", limit=100)
    assert len(rows) > 0
    assert all(r["service"] == "payments" and r["status"] == "failed" for r in rows)


def test_query_orders_filters_by_order_id(tmp_orders_db) -> None:
    query_orders = make_query_orders_tool(tmp_orders_db)
    rows = query_orders(order_id="9002")
    assert len(rows) == 1
    assert rows[0]["order_id"] == 9002
    assert rows[0]["status"] == "failed"
    assert rows[0]["fail_reason"] == "payment_gateway_timeout"


def test_query_orders_finds_the_seeded_incident_cluster(tmp_orders_db) -> None:
    query_orders = make_query_orders_tool(tmp_orders_db)
    rows = query_orders(service="payments", status="failed", limit=100)
    incident_rows = [r for r in rows if r["fail_reason"] == "payment_gateway_timeout"]
    assert len(incident_rows) >= 12  # data/seed_data.py seeds exactly 12
