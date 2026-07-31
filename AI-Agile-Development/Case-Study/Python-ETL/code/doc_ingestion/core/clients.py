"""Azure client factory: managed identity, one shared retry policy, cached.

Three things are deliberate here and are worth stating out loud.

**No API keys anywhere.** Every client authenticates with
``DefaultAzureCredential`` — managed identity in Azure, the developer's own
Azure CLI login locally. The Function's identity needs ``Cognitive Services
User`` on the AI resources, ``Storage Blob Data Contributor`` on the storage
account, and ``Key Vault Secrets User`` if a Key Vault-held secret (the
Snowflake private key, the Aladdin API key) is in play.

**One retry policy, applied identically to every client.** Month-end is when
this pipeline is busiest and it is exactly when Document Intelligence starts
returning 429. The SDK honours ``Retry-After`` automatically; the numbers below
tune how patient it is.

**A tenacity wrapper for transport errors** — the fix for NWD-141. The SDK's
retry policy handles HTTP-level responses it can see, but a connection reset or
a DNS blip surfaces as ``ServiceRequestError``/``ServiceResponseError`` and used
to kill the whole run. :func:`retry_on_transport_error` wraps the call sites in
``extract``/``redact``/``translate`` with exponential backoff so a transport
hiccup at month-end costs seconds, not a day's ingestion.

Clients are cached with ``lru_cache`` because they hold connection pools; making
a new one per document is how you end up exhausting sockets under load.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Callable, TypeVar

from tenacity import (
    RetryCallState,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from config.settings import get_settings

log = logging.getLogger(__name__)

T = TypeVar("T")

# Retry tuning shared by every Azure AI client.
#   - 429 responses carry a Retry-After header which the SDK honours automatically
#   - backoff_factor grows the wait between attempts
#   - read timeout is generous because analysis of a large PDF is a long operation
_RETRY: dict[str, Any] = dict(
    retry_total=5,
    retry_backoff_factor=2.0,
    retry_backoff_max=60,
    connection_timeout=30,
    read_timeout=300,
)


def _is_transport_error(exc: BaseException) -> bool:
    """True for the SDK's connection-level failures.

    The import is deliberately inside the function. Keeping ``azure.*`` off the
    module's import path means the pure modules that import from here for
    typing — and the pure gate in ``core/confidence.py`` — can be unit tested
    without the Azure SDK installed at all.
    """
    from azure.core.exceptions import ServiceRequestError, ServiceResponseError

    return isinstance(exc, (ServiceRequestError, ServiceResponseError))


def _log_retry(state: RetryCallState) -> None:
    log.warning(
        "azure_transport_retry",
        extra={
            "attempt": state.attempt_number,
            "callable": getattr(state.fn, "__name__", "unknown"),
            "error": str(state.outcome.exception()) if state.outcome else None,
        },
    )


def retry_on_transport_error(fn: Callable[..., T]) -> Callable[..., T]:
    """Exponential-backoff wrapper for a call that talks to an Azure AI service.

    NWD-141: a 429 burst at month-end killed the run. The SDK backs off on the
    responses it sees; this covers the transport errors it cannot, and caps the
    total wait so a genuinely dead endpoint still fails the document rather than
    hanging the worker.
    """
    return retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception(_is_transport_error),
        before_sleep=_log_retry,
        reraise=True,
    )(fn)


@lru_cache(maxsize=1)
def credential():
    """Managed identity in Azure, developer credentials locally. No secrets in code."""
    from azure.identity import DefaultAzureCredential

    return DefaultAzureCredential(exclude_interactive_browser_credential=False)


@lru_cache(maxsize=1)
def doc_intel():
    """Document Intelligence client — classification and custom extraction."""
    from azure.ai.documentintelligence import DocumentIntelligenceClient

    return DocumentIntelligenceClient(
        endpoint=get_settings().doc_intel_endpoint,
        credential=credential(),
        **_RETRY,
    )


@lru_cache(maxsize=1)
def language():
    """AI Language client — PII detection and redaction."""
    from azure.ai.textanalytics import TextAnalyticsClient

    return TextAnalyticsClient(
        endpoint=get_settings().language_endpoint,
        credential=credential(),
        **_RETRY,
    )


@lru_cache(maxsize=1)
def translator():
    """AI Translator client — EM documents normalised to English."""
    from azure.ai.translation.text import TextTranslationClient

    return TextTranslationClient(
        endpoint=get_settings().translator_endpoint,
        credential=credential(),
    )


@lru_cache(maxsize=1)
def blobs():
    """Blob service client for the raw / bronze / review containers."""
    from azure.storage.blob import BlobServiceClient

    return BlobServiceClient(
        account_url=get_settings().storage_account_url,
        credential=credential(),
    )


@lru_cache(maxsize=1)
def queues():
    """Queue service client — the blob trigger enqueues, a worker analyses."""
    from azure.storage.queue import QueueServiceClient

    account_url = get_settings().storage_account_url.replace(".blob.", ".queue.")
    return QueueServiceClient(account_url=account_url, credential=credential())


def secret(vault_url: str, name: str) -> str:
    """Read one secret from Key Vault using the same managed identity.

    Used for the two credentials that genuinely cannot be an Azure RBAC role:
    the Snowflake key-pair private key and the Aladdin API key.
    """
    from azure.keyvault.secrets import SecretClient

    client = SecretClient(vault_url=vault_url, credential=credential())
    return client.get_secret(name).value or ""


def reset_clients() -> None:
    """Drop every cached client. Tests only — never call this in the pipeline."""
    for cached in (credential, doc_intel, language, translator, blobs, queues):
        cached.cache_clear()
