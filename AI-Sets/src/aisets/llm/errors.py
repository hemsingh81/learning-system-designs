"""
The error types every LLM backend (fake or real) raises. Callers catch
THESE, never provider-specific exceptions — the same reason a repository
layer translates a raw DB driver exception into your own `NotFoundError`.
"""

from __future__ import annotations


class LLMError(Exception):
    """Base class for every error an LLMClient can raise."""


class RateLimited(LLMError):
    """The provider is rate-limiting us. Callers should back off and retry."""


class Timeout(LLMError):
    """The call took too long and was cancelled."""


class BadOutput(LLMError):
    """The model's output did not match the schema/shape we required.

    This is the single most common "AI bug" you will hit in this project.
    It is not a crash in your code — it means the model said something
    that doesn't fit the contract, and your code correctly refused to
    trust it blindly.
    """


class Refused(LLMError):
    """The model declined to answer (safety refusal, or explicitly said
    it cannot help)."""
