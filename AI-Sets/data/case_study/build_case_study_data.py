"""
Generates the THREE deterministic case-study variants used by Milestone 8
(examples/15_case_study_incident_triage.py and
tests/integration/test_case_study.py):

    data/case_study/easy/{app.log, metrics.json}
        Clear, consistent evidence: explicit ERROR lines AND a sharp
        metrics spike, both pointing at the same root cause. The system
        should investigate once and conclude confidently.

    data/case_study/ambiguous/{app.log, metrics.json}
        Real but WEAK/PARTIAL evidence: a mild metrics blip and only a
        WARN-level log line, no explicit ERROR. A first pass isn't
        conclusive enough to satisfy the Critic; a second, broader
        investigation pass (a genuine re-plan) finds the missing piece.

    data/case_study/trap/{app.log, metrics.json}
        Genuinely CONTRADICTORY evidence: the metrics spike points at a
        DIFFERENT service (checkout) than the one under investigation
        (payments), and the log excerpt contains a misleading, unrelated
        deploy event. There is no honest way to pick a single root cause
        from this evidence — the correct behavior is to ESCALATE, not guess.

Run:
    python data\\case_study\\build_case_study_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BASE_TIME = "2026-06-15T02:14:00"


def _write(variant: str, app_log_lines: list[str], metrics: dict) -> None:
    variant_dir = BASE_DIR / variant
    variant_dir.mkdir(parents=True, exist_ok=True)
    (variant_dir / "app.log").write_text("\n".join(app_log_lines) + "\n", encoding="utf-8")
    (variant_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")


def build_easy() -> None:
    lines = [
        "2026-06-15T02:10:00 INFO  payments       request handled ok in 80ms",
        "2026-06-15T02:13:55 INFO  payments       request handled ok in 90ms",
        "2026-06-15T02:14:00 WARN  payments       gateway response time degraded, p99=4200ms (threshold=1500ms)",
        "2026-06-15T02:14:03 ERROR payments       upstream call to payment-gateway timed out after 5000ms (order_id=9000)",
        "2026-06-15T02:14:06 ERROR payments       upstream call to payment-gateway timed out after 5000ms (order_id=9001)",
        "2026-06-15T02:14:09 ERROR payments       circuit breaker OPEN for payment-gateway, failing fast",
        "2026-06-15T02:16:00 ERROR payments       upstream call to payment-gateway timed out after 5000ms (order_id=9002)",
        "2026-06-15T02:20:00 INFO  payments       payment-gateway connectivity restored, response times normalizing",
        "2026-06-15T02:25:00 INFO  payments       request handled ok in 85ms",
    ]
    metrics = {
        "payments": [
            {"timestamp": "2026-06-15T02:10:00", "latency_ms_p99": 95, "error_rate": 0.01, "cpu_pct": 22.0},
            {"timestamp": "2026-06-15T02:14:00", "latency_ms_p99": 4300, "error_rate": 0.52, "cpu_pct": 88.0},
            {"timestamp": "2026-06-15T02:17:00", "latency_ms_p99": 4600, "error_rate": 0.58, "cpu_pct": 91.0},
            {"timestamp": "2026-06-15T02:22:00", "latency_ms_p99": 110, "error_rate": 0.02, "cpu_pct": 25.0},
        ],
        "checkout": [
            {"timestamp": "2026-06-15T02:10:00", "latency_ms_p99": 80, "error_rate": 0.01, "cpu_pct": 20.0},
            {"timestamp": "2026-06-15T02:20:00", "latency_ms_p99": 85, "error_rate": 0.01, "cpu_pct": 21.0},
        ],
    }
    _write("easy", lines, metrics)


def build_ambiguous() -> None:
    lines = [
        "2026-06-15T02:10:00 INFO  payments       request handled ok in 95ms",
        "2026-06-15T02:13:50 INFO  payments       request handled ok in 100ms",
        "2026-06-15T02:14:00 WARN  payments       gateway response time degraded, p99=650ms (threshold=500ms)",
        "2026-06-15T02:14:30 WARN  payments       connection pool at 85% utilization (18/20 connections in use)",
        "2026-06-15T02:15:00 INFO  payments       request handled ok in 110ms",
        "2026-06-15T02:19:00 INFO  payments       request handled ok in 90ms",
    ]
    metrics = {
        "payments": [
            {"timestamp": "2026-06-15T02:10:00", "latency_ms_p99": 100, "error_rate": 0.01, "cpu_pct": 30.0},
            {"timestamp": "2026-06-15T02:14:00", "latency_ms_p99": 610, "error_rate": 0.07, "cpu_pct": 55.0},
            {"timestamp": "2026-06-15T02:17:00", "latency_ms_p99": 590, "error_rate": 0.06, "cpu_pct": 52.0},
            {"timestamp": "2026-06-15T02:22:00", "latency_ms_p99": 105, "error_rate": 0.01, "cpu_pct": 28.0},
        ],
    }
    _write("ambiguous", lines, metrics)


def build_trap() -> None:
    lines = [
        "2026-06-15T02:09:00 INFO  checkout       new deployment v42 rolled out",
        "2026-06-15T02:10:00 INFO  payments       request handled ok in 90ms",
        "2026-06-15T02:14:00 INFO  payments       routine cache refresh completed",
        "2026-06-15T02:14:30 ERROR checkout       failed to render cart summary, unhandled exception in v42",
        "2026-06-15T02:15:00 ERROR checkout       failed to render cart summary, unhandled exception in v42",
        "2026-06-15T02:20:00 INFO  payments       request handled ok in 95ms",
    ]
    metrics = {
        "payments": [
            {"timestamp": "2026-06-15T02:10:00", "latency_ms_p99": 90, "error_rate": 0.01, "cpu_pct": 25.0},
            {"timestamp": "2026-06-15T02:14:00", "latency_ms_p99": 105, "error_rate": 0.02, "cpu_pct": 27.0},
            {"timestamp": "2026-06-15T02:20:00", "latency_ms_p99": 92, "error_rate": 0.01, "cpu_pct": 24.0},
        ],
        "checkout": [
            {"timestamp": "2026-06-15T02:10:00", "latency_ms_p99": 80, "error_rate": 0.01, "cpu_pct": 20.0},
            {"timestamp": "2026-06-15T02:14:00", "latency_ms_p99": 700, "error_rate": 0.61, "cpu_pct": 90.0},
            {"timestamp": "2026-06-15T02:20:00", "latency_ms_p99": 82, "error_rate": 0.01, "cpu_pct": 22.0},
        ],
    }
    _write("trap", lines, metrics)


def main() -> None:
    build_easy()
    build_ambiguous()
    build_trap()
    print("Wrote data/case_study/{easy,ambiguous,trap}/{app.log,metrics.json}")


if __name__ == "__main__":
    main()
