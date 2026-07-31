"""Read tool: `get_metrics` — summarized latency/error-rate/CPU metrics
for a service, computed from the sample time series in `data/metrics.json`."""

from __future__ import annotations

import json
from pathlib import Path

from aisets.agent.tools import tool


def make_get_metrics_tool(metrics_path: Path):
    @tool(permission="read", name="get_metrics")
    def get_metrics(service: str) -> dict:
        """Get latency/error-rate/CPU metrics for a service (e.g.
        'payments', 'checkout', 'auth') across the whole available time
        window. Returns average and peak latency_ms_p99, average and peak
        error_rate (with the timestamp of the peak), average and peak
        cpu_pct, and the sample count. Use this to judge HOW BAD an
        incident was and roughly WHEN it peaked."""
        data = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
        samples = data.get(service)
        if not samples:
            return {"service": service, "error": f"no metrics found for service '{service}'"}

        latencies = [s["latency_ms_p99"] for s in samples]
        error_rates = [s["error_rate"] for s in samples]
        cpu = [s["cpu_pct"] for s in samples]
        peak_error_sample = max(samples, key=lambda s: s["error_rate"])

        return {
            "service": service,
            "sample_count": len(samples),
            "avg_latency_ms_p99": round(sum(latencies) / len(latencies), 1),
            "peak_latency_ms_p99": max(latencies),
            "avg_error_rate": round(sum(error_rates) / len(error_rates), 4),
            "peak_error_rate": max(error_rates),
            "peak_error_rate_timestamp": peak_error_sample["timestamp"],
            "avg_cpu_pct": round(sum(cpu) / len(cpu), 1),
            "peak_cpu_pct": max(cpu),
        }

    return get_metrics
