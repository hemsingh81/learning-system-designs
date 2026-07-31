"""Typed configuration for the counterparty ingestion pipeline.

Everything the pipeline needs to know about a counterparty lives in
``sources.yaml`` and is parsed here into pydantic models. Nothing in ``core/``
or ``sinks/`` reads the YAML directly — they take a :class:`SourceConfig` and
behave accordingly. That is what makes "adding a counterparty is a YAML change
plus a trained model, never a code change" true rather than aspirational.

Environment variables carry only endpoints and account URLs. There are no
credentials here, by design: authentication is managed identity (see
``core/clients.py``).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, Field

# Document Intelligence reports a richer set of field types than we want to
# maintain thresholds for. Collapse the long tail onto the four types the
# business actually reasoned about when the thresholds were swept.
FIELD_TYPE_ALIASES: dict[str, str] = {
    "integer": "number",
    "time": "date",
    "countryRegion": "string",
    "phoneNumber": "string",
    "selectionMark": "string",
    "address": "string",
    "signature": "string",
}

Severity = Literal["error", "warning"]


class ConfidenceConfig(BaseModel):
    """Per-field-type confidence thresholds.

    The defaults come from a threshold sweep against a labelled ground-truth
    set, not from intuition: for each field type the threshold was swept from
    0.5 to 0.99 and the point chosen where auto-accepted errors on monetary
    fields hit zero, then one step up for margin.
    """

    default: float = 0.80
    by_field_type: dict[str, float] = Field(default_factory=dict)

    def threshold_for(self, field_type: str) -> float:
        """Resolve the gate threshold for a Document Intelligence field type."""
        canonical = FIELD_TYPE_ALIASES.get(field_type, field_type)
        return self.by_field_type.get(canonical, self.default)


class ClassifierConfig(BaseModel):
    """Which classifier routes documents, and how sure it has to be."""

    classifier_id: str = "counterparty-doc-classifier-v2"
    min_confidence: float = 0.75


class RuleConfig(BaseModel):
    """One entry in the rules engine's ordered rule list.

    ``type`` selects an implementation registered in ``core/rules.py``; the
    engine refuses to start if a type is unknown, so a typo in YAML fails loudly
    at configuration load rather than silently skipping a control.
    """

    id: str
    type: str
    severity: Severity = "error"
    # Empty means "every document type"; otherwise restrict to these doc_types.
    applies_to: list[str] = Field(default_factory=list)
    params: dict[str, Any] = Field(default_factory=dict)

    def applies(self, doc_type: str) -> bool:
        return not self.applies_to or doc_type in self.applies_to


class SourceConfig(BaseModel):
    """Everything the pipeline knows about one counterparty."""

    key: str
    display_name: str
    container: str = "raw"
    prefix: str
    model_id: str
    doc_type: str
    language: str = "en"
    translate_to: str | None = None

    field_map: dict[str, str] = Field(default_factory=dict)
    line_item_map: dict[str, str] = Field(default_factory=dict)
    # Canonical name of the header field carrying the document's own count of
    # line items. Present only for layouts that state it. See NWD-142.
    line_item_count_field: str | None = None

    confidence: ConfidenceConfig = Field(default_factory=ConfidenceConfig)
    classifier: ClassifierConfig = Field(default_factory=ClassifierConfig)

    redact_pii: bool = True
    max_pages: int = 50

    no_translate_fields: list[str] = Field(default_factory=list)
    translate_field_types: list[str] = Field(default_factory=lambda: ["string"])

    rules: list[RuleConfig] = Field(default_factory=list)
    extra_rules: list[RuleConfig] = Field(default_factory=list)

    @property
    def all_rules(self) -> list[RuleConfig]:
        """Default rules first, then this counterparty's additions.

        Order is meaningful — normalisation rules must run before the validators
        that read the values they normalise, and the shared defaults are the
        ones that establish the baseline shape of a document.
        """
        return [*self.rules, *self.extra_rules]

    def is_translatable_field(self, canonical_name: str, field_type: str) -> bool:
        """Whether a field may be sent to Translator.

        NWD-138: a Spanish confirmation had its security identifier translated,
        which broke the match against Aladdin. Identifiers are data, not prose.
        """
        if canonical_name in self.no_translate_fields:
            return False
        return FIELD_TYPE_ALIASES.get(field_type, field_type) in self.translate_field_types


class Settings(BaseModel):
    """Process-wide settings: endpoints, containers, and the source registry."""

    doc_intel_endpoint: str
    language_endpoint: str
    translator_endpoint: str
    storage_account_url: str

    raw_container: str = "raw"
    bronze_container: str = "bronze"
    review_container: str = "review"
    analysis_queue: str = "doc-analysis"

    sources: dict[str, SourceConfig]

    def source_for_blob(self, blob_path: str) -> SourceConfig:
        """Route an incoming blob to its counterparty config by path prefix.

        ``blob_path`` is the path *inside* the raw container, e.g.
        ``broker_alpha/2026-07-31/statement.pdf``.
        """
        for source in self.sources.values():
            if blob_path.startswith(source.prefix):
                return source
        raise ValueError(f"No source configuration matches blob path: {blob_path}")


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge ``override`` onto ``base`` without mutating either.

    Dicts merge key-by-key; every other type (including lists) is replaced
    outright. That is why per-source rule additions use ``extra_rules`` rather
    than trying to append to ``rules``.
    """
    out = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_settings(yaml_path: Path | None = None) -> Settings:
    """Build :class:`Settings` from the YAML file and the environment.

    Split out from :func:`get_settings` so tests can load a fixture YAML without
    fighting the cache.
    """
    path = yaml_path or Path(__file__).with_name("sources.yaml")
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults", {}) or {}

    sources = {
        key: SourceConfig(key=key, **_deep_merge(defaults, cfg or {}))
        for key, cfg in (raw.get("sources") or {}).items()
    }

    return Settings(
        doc_intel_endpoint=os.environ["DOC_INTEL_ENDPOINT"],
        language_endpoint=os.environ["LANGUAGE_ENDPOINT"],
        translator_endpoint=os.environ["TRANSLATOR_ENDPOINT"],
        storage_account_url=os.environ["STORAGE_ACCOUNT_URL"],
        raw_container=os.environ.get("RAW_CONTAINER", "raw"),
        bronze_container=os.environ.get("BRONZE_CONTAINER", "bronze"),
        review_container=os.environ.get("REVIEW_CONTAINER", "review"),
        analysis_queue=os.environ.get("ANALYSIS_QUEUE", "doc-analysis"),
        sources=sources,
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings for the life of the Function host process.

    Cached because a Function instance handles many documents and re-reading
    YAML per invocation is pure waste; a configuration change is a deployment,
    which restarts the host anyway.
    """
    return load_settings()
