"""
Integration test for the Milestone 9 FastAPI service
(examples/16_serve_agent_api.py) — `POST /triage` and `GET /runs/{id}`,
using FastAPI's httpx-based TestClient (no real network, no real server
process).
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

EXAMPLES_DIR = Path(__file__).resolve().parents[2] / "examples"


@pytest.fixture(scope="module")
def client():
    sys.path.insert(0, str(EXAMPLES_DIR))
    try:
        api_module = importlib.import_module("16_serve_agent_api")
        with TestClient(api_module.app) as test_client:
            yield test_client
    finally:
        sys.path.remove(str(EXAMPLES_DIR))


def test_triage_easy_variant_returns_completed_summary(client) -> None:
    response = client.post("/triage", json={"variant": "easy", "auto_approve": True})

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "completed"
    assert body["variant"] == "easy"
    assert body["attempts"] == 1
    assert body["critic_met"] is True
    assert body["action_approved"] is True
    assert "run_id" in body


def test_get_run_returns_the_same_summary(client) -> None:
    create_response = client.post("/triage", json={"variant": "easy", "auto_approve": True})
    run_id = create_response.json()["run_id"]

    get_response = client.get(f"/runs/{run_id}")

    assert get_response.status_code == 200
    assert get_response.json() == create_response.json()


def test_get_run_unknown_id_returns_404(client) -> None:
    response = client.get("/runs/does-not-exist")
    assert response.status_code == 404


def test_triage_trap_variant_never_auto_approves_even_with_auto_approve_true(client) -> None:
    # auto_approve=True simulates a human who WOULD approve if asked about
    # a specific fix — but the trap variant never reaches a confirmed root
    # cause, so it must escalate with no action, regardless of this flag.
    response = client.post("/triage", json={"variant": "trap", "auto_approve": True})

    body = response.json()
    assert body["critic_met"] is False
    assert body["escalated"] is True
    assert body["action_approved"] is False


def test_triage_rejects_invalid_variant() -> None:
    sys.path.insert(0, str(EXAMPLES_DIR))
    try:
        api_module = importlib.import_module("16_serve_agent_api")
        with TestClient(api_module.app) as client:
            response = client.post("/triage", json={"variant": "not_a_real_variant"})
            assert response.status_code == 422  # pydantic validation error
    finally:
        if str(EXAMPLES_DIR) in sys.path:
            sys.path.remove(str(EXAMPLES_DIR))
