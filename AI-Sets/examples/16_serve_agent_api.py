"""
Example 16 — expose the Milestone 8 incident-triage system as a backend
HTTP service (FastAPI). This is the "productionizing" step: the exact
same `run_incident_triage` function from Lesson 05, now behind a real API
your other services could call.

Endpoints:
    POST /triage        - run a triage (body: {"variant": "easy"|"ambiguous"|"trap", "auto_approve": bool})
    GET  /runs/{run_id}  - fetch a previously completed run's summary

Run the server:
    .\\scripts\\run-example.ps1 16_serve_agent_api
    (or directly: uvicorn examples.16_serve_agent_api:app --reload  -- note the
     digit-leading filename means uvicorn's dotted-path form won't work; use
     the run-example script, which runs this file as __main__ instead.)

Then, in a second terminal:
    curl -X POST https://localhost:8100/triage -H "Content-Type: application/json" -d "{\"variant\": \"easy\", \"auto_approve\": true}"
    curl https://localhost:8100/runs/<run_id from the previous response>

This is example code, not a hardened production service — see
docs/06-security-and-privacy.md before exposing anything like this
outside your own machine (no auth, in-memory run storage, no rate limiting).
"""

from __future__ import annotations

import importlib
import sys
import uuid
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from _common import is_fake, setup

EXAMPLES_DIR = Path(__file__).resolve().parent
if str(EXAMPLES_DIR) not in sys.path:
    sys.path.insert(0, str(EXAMPLES_DIR))
case_study = importlib.import_module("15_case_study_incident_triage")

settings, llm = setup()

app = FastAPI(title="AI-Sets Incident Triage API", version="0.1.0")

_runs: dict[str, "RunSummary"] = {}

_SCRIPTERS = {
    "easy": case_study._script_easy,
    "ambiguous": case_study._script_ambiguous,
    "trap": case_study._script_trap,
}


class TriageRequest(BaseModel):
    variant: Literal["easy", "ambiguous", "trap"]
    # In a real deployment, an approval request would go to a human via a
    # UI/notification, and this endpoint would return "pending" until they
    # respond. This flag simulates that decision synchronously, for a
    # runnable teaching example — see docs/06-security-and-privacy.md.
    auto_approve: bool = False


class RunSummary(BaseModel):
    run_id: str
    status: Literal["completed"]
    variant: str
    attempts: int
    critic_met: bool
    escalated: bool
    action_approved: bool
    final_message: str


@app.post("/triage", response_model=RunSummary)
def create_triage(req: TriageRequest) -> RunSummary:
    if is_fake(llm):
        _SCRIPTERS[req.variant](llm)

    result = case_study.run_incident_triage(
        llm, settings, req.variant, human_approve=lambda r: req.auto_approve
    )

    run_id = str(uuid.uuid4())
    summary = RunSummary(
        run_id=run_id,
        status="completed",
        variant=result.variant,
        attempts=result.attempts,
        critic_met=result.critic_met,
        escalated=result.escalated,
        action_approved=result.action_approved,
        final_message=result.final_message,
    )
    _runs[run_id] = summary
    return summary


@app.get("/runs/{run_id}", response_model=RunSummary)
def get_run(run_id: str) -> RunSummary:
    run = _runs.get(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"run '{run_id}' not found")
    return run


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8100)
