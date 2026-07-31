"""Structured JSON logging with a per-document correlation id.

Every log line the pipeline emits is a JSON object on one line, which is what
Application Insights and any log search tool want. The correlation id is held in
a :class:`~contextvars.ContextVar` so that call sites deep in ``core/`` do not
have to thread it through every signature — the orchestrator binds it once per
document and everything logged under that document carries it.

This matters operationally: when an analyst asks "what happened to the Broker
Alpha statement that arrived at 07:12", one correlation id returns the whole
story — classification, extraction, gate result, rule violations, sink writes.
"""

from __future__ import annotations

import json
import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterator
from contextlib import contextmanager

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)

# Attributes the stdlib puts on every LogRecord. Anything NOT in here was added
# by the caller via ``extra=`` and therefore belongs in the JSON payload.
_STANDARD_ATTRS = frozenset(
    """
    args asctime created exc_info exc_text filename funcName levelname levelno
    lineno module msecs message msg name pathname process processName
    relativeCreated stack_info thread threadName taskName
    """.split()
)


def current_correlation_id() -> str | None:
    """The correlation id bound to the current document, if any."""
    return _correlation_id.get()


def new_correlation_id() -> str:
    """Mint a correlation id. One per document, generated at the trigger."""
    return str(uuid.uuid4())


@contextmanager
def correlation_scope(correlation_id: str | None = None) -> Iterator[str]:
    """Bind a correlation id for the duration of a block.

    Used by both Function entry points so that the id travels with the document
    rather than with the thread that happens to be running.
    """
    value = correlation_id or new_correlation_id()
    token = _correlation_id.set(value)
    try:
        yield value
    finally:
        _correlation_id.reset(token)


class JsonFormatter(logging.Formatter):
    """Render a LogRecord as a single-line JSON object."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "event": record.getMessage(),
        }

        correlation_id = _correlation_id.get()
        if correlation_id:
            payload["correlation_id"] = correlation_id

        # Anything passed via extra= is structured context, not prose.
        for key, value in record.__dict__.items():
            if key not in _STANDARD_ATTRS and not key.startswith("_"):
                payload[key] = _jsonable(value)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str, separators=(",", ":"))


def _jsonable(value: Any) -> Any:
    """Best-effort coercion so one unserialisable extra never loses a log line."""
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    return str(value)


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON formatter on the root logger. Idempotent.

    Called at module import in ``function_app.py`` because the Function host may
    import the module once and invoke it thousands of times.
    """
    root = logging.getLogger()
    root.setLevel(level)

    for handler in root.handlers:
        if isinstance(handler.formatter, JsonFormatter):
            return

    handler = logging.StreamHandler(stream=sys.stdout)
    handler.setFormatter(JsonFormatter())
    root.handlers = [handler]

    # The Azure SDKs log every HTTP request at INFO, which drowns the pipeline's
    # own events. Errors from them are still surfaced.
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(
        logging.WARNING
    )
    logging.getLogger("snowflake.connector").setLevel(logging.WARNING)
