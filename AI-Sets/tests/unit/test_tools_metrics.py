"""Unit tests for tools/metrics.py — get_metrics against the seeded
metrics.json (which contains a deliberate payments-service spike)."""

from __future__ import annotations

from aisets.tools.metrics import make_get_metrics_tool


def test_get_metrics_returns_summary_for_known_service(sample_metrics_path) -> None:
    get_metrics = make_get_metrics_tool(sample_metrics_path)
    result = get_metrics(service="payments")

    assert result["service"] == "payments"
    assert result["sample_count"] > 0
    assert result["peak_latency_ms_p99"] >= result["avg_latency_ms_p99"]
    assert result["peak_error_rate"] >= result["avg_error_rate"]


def test_get_metrics_payments_incident_is_visible_in_peaks(sample_metrics_path) -> None:
    get_metrics = make_get_metrics_tool(sample_metrics_path)
    result = get_metrics(service="payments")

    # data/seed_data.py seeds a payments incident with latency 4000-5000ms
    # and error_rate 0.35-0.60 — the peak must reflect that spike.
    assert result["peak_latency_ms_p99"] >= 4000
    assert result["peak_error_rate"] >= 0.35


def test_get_metrics_unknown_service_returns_error_dict(sample_metrics_path) -> None:
    get_metrics = make_get_metrics_tool(sample_metrics_path)
    result = get_metrics(service="not_a_real_service")
    assert "error" in result
