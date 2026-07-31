"""
Shared setup used by every example script — NOT itself a numbered lesson.

Every example does the same three things first: load settings, configure
logging, build an LLM client from those settings. Centralizing that here
means each numbered example file can stay focused on the ONE concept it
teaches.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from aisets.config import Settings, load_settings
from aisets.llm import LLMClient, build_llm_client
from aisets.llm.fake import FakeLLM
from aisets.logging_setup import configure_logging, new_trace_id

console = Console()


def setup() -> tuple[Settings, LLMClient]:
    settings = load_settings()
    configure_logging(settings.log_format, settings.log_level)
    new_trace_id()
    llm = build_llm_client(settings)
    console.print(f"[dim]LLM backend: {settings.llm_backend} (model={getattr(llm, 'model', '?')})[/dim]")
    return settings, llm


def is_fake(llm: LLMClient) -> bool:
    return isinstance(llm, FakeLLM)


def load_tickets(settings: Settings) -> list[dict[str, Any]]:
    path = settings.data_dir / "tickets.json"
    return json.loads(path.read_text(encoding="utf-8"))


def load_app_log(settings: Settings) -> str:
    path = settings.data_dir / "app.log"
    return path.read_text(encoding="utf-8")
