"""
Factory: turn `Settings.llm_backend` into a real `LLMClient` instance.

This is the ONE place that reads `settings.llm_backend` and decides which
concrete class to build. Every example calls `build_llm_client(settings)`
and then only ever talks to the returned object through the `LLMClient`
shape — it never checks "am I fake or real" again.
"""

from __future__ import annotations

from aisets.config import Settings
from aisets.llm.base import LLMClient, LLMResponse, Message, ToolCall, ToolSpec
from aisets.llm.claude import ClaudeLLM
from aisets.llm.fake import FakeLLM

__all__ = [
    "LLMClient",
    "LLMResponse",
    "Message",
    "ToolCall",
    "ToolSpec",
    "FakeLLM",
    "ClaudeLLM",
    "build_llm_client",
]


def build_llm_client(settings: Settings) -> LLMClient:
    if settings.llm_backend == "fake":
        return FakeLLM()
    return ClaudeLLM(model=settings.claude_model, api_key=settings.anthropic_api_key)
