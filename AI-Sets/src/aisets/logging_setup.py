"""
Structured logging with a trace id, so every example prints logs that look
like something you'd actually see in a backend service's log aggregator.

Why a trace id:
    Once you get to the Agent and Agentic levels, ONE user request can
    trigger many LLM calls and many tool calls. Without a trace id you
    cannot tell which log line belongs to which run. This is the exact
    same problem as tracing a request across microservices, and the
    exact same fix: generate one id at the top, thread it through.

Two output formats:
    "text" -> human-readable, good for reading along in the terminal.
    "json" -> one JSON object per line, good for feeding into a real log
              pipeline (this is what you'd ship to production).
"""

from __future__ import annotations

import contextvars
import json
import logging
import sys
import uuid
from datetime import datetime, timezone

_trace_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    "trace_id", default="-"
)


def new_trace_id() -> str:
    """Start a new trace id and make it the active one for this context."""
    trace_id = uuid.uuid4().hex[:12]
    _trace_id_var.set(trace_id)
    return trace_id


def current_trace_id() -> str:
    return _trace_id_var.get()


class _TraceIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.trace_id = current_trace_id()
        return True


class _JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "trace_id": getattr(record, "trace_id", "-"),
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging(log_format: str = "text", log_level: str = "INFO") -> None:
    """Call this once at process start (every example does this first)."""
    root = logging.getLogger()
    root.setLevel(log_level)
    root.handlers.clear()

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.addFilter(_TraceIdFilter())

    if log_format == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] [trace=%(trace_id)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )
    root.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
