"""Unit tests for tools/runbook.py — find_runbook against the seeded
runbook markdown files."""

from __future__ import annotations

from aisets.tools.runbook import make_find_runbook_tool


def test_find_runbook_matches_payments_timeout(sample_runbooks_dir) -> None:
    find_runbook = make_find_runbook_tool(sample_runbooks_dir)
    results = find_runbook(keywords="payments gateway timeout")

    assert len(results) > 0
    assert results[0]["filename"] == "payments-gateway-timeout.md"


def test_find_runbook_no_match_returns_empty(sample_runbooks_dir) -> None:
    find_runbook = make_find_runbook_tool(sample_runbooks_dir)
    results = find_runbook(keywords="xyznonexistentterm")
    assert results == []


def test_find_runbook_empty_keywords_returns_empty(sample_runbooks_dir) -> None:
    find_runbook = make_find_runbook_tool(sample_runbooks_dir)
    assert find_runbook(keywords="") == []


def test_find_runbook_results_sorted_by_match_count(sample_runbooks_dir) -> None:
    find_runbook = make_find_runbook_tool(sample_runbooks_dir)
    results = find_runbook(keywords="error rate service")
    match_counts = [r["match_count"] for r in results]
    assert match_counts == sorted(match_counts, reverse=True)
