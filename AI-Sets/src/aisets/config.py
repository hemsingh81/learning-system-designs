"""
Typed settings for the whole project, loaded once from `.env`.

Why this file exists (the backend-engineer framing):
    Think of this the same way you'd think of a Settings/appsettings.json
    loader in a normal backend service. Every other module asks THIS file
    for config — nobody else calls `os.environ` directly. That gives us
    one place to see every knob, one place to set safe defaults, and one
    place to validate that a bad value fails LOUDLY at startup instead of
    quietly three files deep.

Design decision (see docs/00-PLAN.md, D-003):
    LLM_BACKEND defaults to "fake" so the entire tutorial runs with ZERO
    API keys and ZERO network calls until you explicitly opt in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Load .env once, from the project root, no matter where this module is
# imported from. This mirrors how ASP.NET Core loads appsettings.json
# relative to the app root, not the current working directory.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(_PROJECT_ROOT / ".env")


class ConfigError(Exception):
    """Raised when a setting is missing or invalid. Fails fast, on purpose."""


def _get_str(name: str, default: str) -> str:
    return os.environ.get(name, default)


def _get_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ConfigError(f"{name}='{raw}' is not a valid integer") from exc


def _get_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError as exc:
        raise ConfigError(f"{name}='{raw}' is not a valid number") from exc


@dataclass(frozen=True)
class Settings:
    """Immutable settings snapshot. Frozen so nothing can mutate it at runtime
    (the same reason you'd mark a config record `readonly` in C#)."""

    llm_backend: str
    anthropic_api_key: str
    claude_model: str

    max_agent_steps: int
    max_usd_per_run: float
    max_seconds_per_run: int

    log_format: str
    log_level: str

    data_dir: Path
    project_root: Path

    def validate(self) -> None:
        if self.llm_backend not in ("fake", "claude"):
            raise ConfigError(
                f"LLM_BACKEND must be 'fake' or 'claude', got '{self.llm_backend}'"
            )
        if self.llm_backend == "claude" and not self.anthropic_api_key:
            raise ConfigError(
                "LLM_BACKEND=claude but ANTHROPIC_API_KEY is empty. "
                "Either set the key in .env, or set LLM_BACKEND=fake."
            )
        if self.max_agent_steps < 1:
            raise ConfigError("MAX_AGENT_STEPS must be >= 1")
        if self.max_usd_per_run <= 0:
            raise ConfigError("MAX_USD_PER_RUN must be > 0")
        if self.log_format not in ("text", "json"):
            raise ConfigError("LOG_FORMAT must be 'text' or 'json'")


def load_settings() -> Settings:
    """Read settings from the environment. Call this once per process
    (examples/tests call it at the top of `main()`), then pass the result
    around explicitly — no hidden global state to chase during debugging.
    """
    data_dir_raw = _get_str("DATA_DIR", "data")
    data_dir = (_PROJECT_ROOT / data_dir_raw).resolve()

    settings = Settings(
        llm_backend=_get_str("LLM_BACKEND", "fake"),
        anthropic_api_key=_get_str("ANTHROPIC_API_KEY", ""),
        claude_model=_get_str("CLAUDE_MODEL", "claude-3-5-haiku-latest"),
        max_agent_steps=_get_int("MAX_AGENT_STEPS", 5),
        max_usd_per_run=_get_float("MAX_USD_PER_RUN", 0.50),
        max_seconds_per_run=_get_int("MAX_SECONDS_PER_RUN", 60),
        log_format=_get_str("LOG_FORMAT", "text"),
        log_level=_get_str("LOG_LEVEL", "INFO"),
        data_dir=data_dir,
        project_root=_PROJECT_ROOT,
    )
    settings.validate()
    return settings
