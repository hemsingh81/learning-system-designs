"""Unit tests for skills/summarize_log.py — including chunking behavior
for input longer than the context-window-sized chunk limit."""

from __future__ import annotations

from aisets.skills.summarize_log import SummarizeLog


def test_happy_path_single_chunk(fake_llm) -> None:
    fake_llm.queue_json({
        "headline": "Normal traffic, no issues.",
        "key_events": ["all requests handled ok"],
        "error_count": 0,
    })
    skill = SummarizeLog(fake_llm)

    result = skill.run("2026-01-01T00:00:00 INFO app: request handled ok in 40ms\n")

    assert result.headline
    assert result.error_count == 0
    assert len(fake_llm.calls) == 1


def test_empty_input_returns_default_without_calling_model(fake_llm) -> None:
    skill = SummarizeLog(fake_llm)
    result = skill.run("")
    assert result.error_count == 0
    assert len(fake_llm.calls) == 0


def test_long_input_is_chunked_into_multiple_calls(fake_llm) -> None:
    skill = SummarizeLog(fake_llm)
    # Build a log much longer than chunk_size_chars so it must be split.
    line = "2026-01-01T00:00:00 ERROR app: something failed\n"
    long_log = line * (skill.chunk_size_chars // len(line) * 3)  # ~3 chunks worth

    # One response per chunk, plus one final "combine" response.
    fake_llm.queue_json({"headline": "chunk 1 had errors", "key_events": ["error x"], "error_count": 5})
    fake_llm.queue_json({"headline": "chunk 2 had errors", "key_events": ["error y"], "error_count": 4})
    fake_llm.queue_json({"headline": "chunk 3 had errors", "key_events": ["error z"], "error_count": 3})
    fake_llm.queue_json({"headline": "Overall: repeated errors across the log.", "key_events": ["errors throughout"], "error_count": 999})

    result = skill.run(long_log)

    assert len(fake_llm.calls) == 4  # 3 chunk calls + 1 combine call
    # error_count is recomputed from the chunk totals, not trusted from the
    # final combine call's own arithmetic (which queued a wrong 999).
    assert result.error_count == 5 + 4 + 3


def test_oversized_single_line_is_still_handled(fake_llm) -> None:
    # A pathological single line longer than the chunk size should not crash
    # the splitter — it becomes its own (oversized) chunk.
    skill = SummarizeLog(fake_llm)
    huge_single_line = "x" * (skill.chunk_size_chars * 2)

    fake_llm.queue_json({"headline": "one huge line", "key_events": [], "error_count": 0})

    result = skill.run(huge_single_line)
    assert result.headline == "one huge line"
