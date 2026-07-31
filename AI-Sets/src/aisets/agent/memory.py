"""
Agent memory: short-term (the current conversation) and long-term (facts
that survive across separate agent runs).

Short-term memory is a bounded cache-eviction problem: the context window
is finite (docs/03-llm-basics.md), so `ConversationMemory` trims the
OLDEST turns once the total size crosses a budget — always keeping the
very first message (the original question), because losing track of what
was even asked is worse than losing an intermediate tool result.

Long-term memory is a tiny SQLite key/value table — the same idea as a
`Facts` or `KnownIssues` table in a real backend, except the "writer" is
the agent itself, deciding what's worth remembering.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from aisets.llm.base import Message


class ConversationMemory:
    """Short-term memory: the message history for ONE agent run, trimmed
    to stay under `max_chars` (a crude but simple stand-in for a token
    budget — good enough to teach the eviction behavior)."""

    def __init__(self, max_chars: int = 8_000) -> None:
        self.max_chars = max_chars
        self.messages: list[Message] = []

    def add(self, message: Message) -> None:
        self.messages.append(message)
        self._trim()

    def as_list(self) -> list[Message]:
        return list(self.messages)

    def _trim(self) -> None:
        total = sum(len(m.content) for m in self.messages)
        # Always keep index 0 (the original question) and at least the
        # most recent message — trim from just after the start.
        while total > self.max_chars and len(self.messages) > 2:
            removed = self.messages.pop(1)
            total -= len(removed.content)


class LongTermMemory:
    """Long-term memory: a tiny SQLite-backed fact store that survives
    across separate `LongTermMemory` instances (i.e. across separate agent
    runs, or even separate processes) as long as they point at the same
    `db_path`."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_facts (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.commit()
        finally:
            conn.close()

    def remember(self, key: str, value: str) -> None:
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute(
                """
                INSERT INTO agent_facts (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, value, datetime.now(timezone.utc).isoformat()),
            )
            conn.commit()
        finally:
            conn.close()

    def recall(self, key: str) -> str | None:
        conn = sqlite3.connect(self.db_path)
        try:
            row = conn.execute("SELECT value FROM agent_facts WHERE key = ?", (key,)).fetchone()
            return row[0] if row else None
        finally:
            conn.close()

    def all_facts(self) -> dict[str, str]:
        conn = sqlite3.connect(self.db_path)
        try:
            rows = conn.execute("SELECT key, value FROM agent_facts").fetchall()
            return dict(rows)
        finally:
            conn.close()
