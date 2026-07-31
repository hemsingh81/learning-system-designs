"""Unit tests for tools/logs.py — search_logs against the seeded app.log."""

from __future__ import annotations

from aisets.tools.logs import make_search_logs_tool


def test_search_finds_the_seeded_incident(sample_log_path) -> None:
    search_logs = make_search_logs_tool(sample_log_path)
    matches = search_logs(query="circuit breaker OPEN")
    assert len(matches) > 0
    assert all("circuit breaker OPEN" in m for m in matches)


def test_search_is_case_insensitive(sample_log_path) -> None:
    search_logs = make_search_logs_tool(sample_log_path)
    matches_lower = search_logs(query="error")
    matches_upper = search_logs(query="ERROR")
    assert matches_lower == matches_upper
    assert len(matches_lower) > 0


def test_search_respects_max_lines(sample_log_path) -> None:
    search_logs = make_search_logs_tool(sample_log_path)
    matches = search_logs(query="request handled ok", max_lines=3)
    assert len(matches) == 3


def test_search_empty_query_returns_empty(sample_log_path) -> None:
    search_logs = make_search_logs_tool(sample_log_path)
    assert search_logs(query="") == []


def test_search_no_match_returns_empty(sample_log_path) -> None:
    search_logs = make_search_logs_tool(sample_log_path)
    assert search_logs(query="this string will never appear in the log") == []
