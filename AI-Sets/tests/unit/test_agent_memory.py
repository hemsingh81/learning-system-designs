"""Unit tests for agent/memory.py — ConversationMemory (short-term
trimming) and LongTermMemory (SQLite-backed facts across instances)."""

from __future__ import annotations

from aisets.agent.memory import ConversationMemory, LongTermMemory
from aisets.llm.base import Message


def test_conversation_memory_keeps_everything_under_budget() -> None:
    memory = ConversationMemory(max_chars=1000)
    memory.add(Message(role="user", content="short question"))
    memory.add(Message(role="tool", content="short result"))

    assert len(memory.as_list()) == 2


def test_conversation_memory_trims_oldest_but_keeps_first_message() -> None:
    memory = ConversationMemory(max_chars=100)
    memory.add(Message(role="user", content="ORIGINAL " + "a" * 30))
    for i in range(10):
        memory.add(Message(role="tool", content=f"result-{i} " + "b" * 30))

    messages = memory.as_list()
    assert messages[0].content.startswith("ORIGINAL")
    total_chars = sum(len(m.content) for m in messages)
    assert total_chars <= 100 + 40  # a little slack for the last add before re-trim


def test_conversation_memory_never_drops_below_two_messages() -> None:
    memory = ConversationMemory(max_chars=1)
    memory.add(Message(role="user", content="a" * 500))
    memory.add(Message(role="tool", content="b" * 500))
    memory.add(Message(role="tool", content="c" * 500))

    assert len(memory.as_list()) == 2  # first message + most recent, never fewer


def test_long_term_memory_remember_and_recall(tmp_path) -> None:
    db_path = tmp_path / "facts.db"
    memory = LongTermMemory(db_path)

    memory.remember("root_cause", "gateway_timeout")
    assert memory.recall("root_cause") == "gateway_timeout"


def test_long_term_memory_recall_missing_key_returns_none(tmp_path) -> None:
    memory = LongTermMemory(tmp_path / "facts.db")
    assert memory.recall("does_not_exist") is None


def test_long_term_memory_remember_overwrites_existing_key(tmp_path) -> None:
    memory = LongTermMemory(tmp_path / "facts.db")
    memory.remember("root_cause", "first_value")
    memory.remember("root_cause", "second_value")
    assert memory.recall("root_cause") == "second_value"


def test_long_term_memory_persists_across_separate_instances(tmp_path) -> None:
    db_path = tmp_path / "facts.db"

    first = LongTermMemory(db_path)
    first.remember("known_incident", "payments_gateway_timeout")

    second = LongTermMemory(db_path)  # simulates a new/separate agent run
    assert second.recall("known_incident") == "payments_gateway_timeout"


def test_long_term_memory_all_facts(tmp_path) -> None:
    memory = LongTermMemory(tmp_path / "facts.db")
    memory.remember("a", "1")
    memory.remember("b", "2")
    assert memory.all_facts() == {"a": "1", "b": "2"}
