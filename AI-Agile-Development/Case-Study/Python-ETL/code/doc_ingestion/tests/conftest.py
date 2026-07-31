"""Shared pytest fixtures.

Two things worth noticing about this file, because they are the payoff for the
design decisions elsewhere in the tree.

First, most of the fixtures build plain dataclasses. The confidence gate, the
rules engine and the transform all take :class:`ExtractedDocument` in and return
plain values out, so testing them needs no Azure account, no network, and no
mocking framework — just constructors.

Second, the one fixture that *does* stub Azure (:func:`stub_azure_sdk`) only has
to stub two tiny things, because ``core/extract.py`` imports the SDK at the point
of use rather than at module import. That is what keeps ``import core.confidence``
free of the whole Azure dependency tree.
"""

from __future__ import annotations

import sys
import types
from datetime import date
from pathlib import Path
from typing import Any

import pytest

# The package root, so `import core.confidence` resolves when pytest is run from
# anywhere. There are no __init__.py files; these are namespace packages.
PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from config.settings import (  # noqa: E402  - must follow the sys.path insert
    ConfidenceConfig,
    RuleConfig,
    SourceConfig,
    load_settings,
)
from core.extract import ExtractedDocument, ExtractedField  # noqa: E402


# -----------------------------------------------------------------------------
# Builders
# -----------------------------------------------------------------------------


def make_field(
    name: str,
    value: Any,
    confidence: float | None,
    field_type: str = "string",
    page_number: int | None = None,
) -> ExtractedField:
    """One extracted field. The shorthand every test in this suite uses."""
    return ExtractedField(
        name=name,
        value=value,
        confidence=confidence,
        field_type=field_type,
        raw_content=None if value is None else str(value),
        page_number=page_number,
    )


def make_document(
    header: dict[str, ExtractedField] | None = None,
    line_items: list[dict[str, ExtractedField]] | None = None,
    *,
    source_key: str = "test",
    model_id: str = "m",
    page_count: int = 1,
    table_pages: list[int] | None = None,
    declared_line_item_count: int | None = None,
) -> ExtractedDocument:
    """An extracted document with sensible defaults."""
    return ExtractedDocument(
        source_key=source_key,
        model_id=model_id,
        page_count=page_count,
        header=header or {},
        line_items=line_items or [],
        table_pages=table_pages or [],
        declared_line_item_count=declared_line_item_count,
    )


@pytest.fixture
def field_factory():
    """Expose :func:`make_field` as a fixture for tests that prefer injection."""
    return make_field


@pytest.fixture
def document_factory():
    """Expose :func:`make_document` as a fixture."""
    return make_document


# -----------------------------------------------------------------------------
# Source configurations
# -----------------------------------------------------------------------------


@pytest.fixture
def source() -> SourceConfig:
    """A minimal source with the production threshold profile and no rules."""
    return SourceConfig(
        key="test",
        display_name="t",
        container="raw",
        prefix="test/",
        model_id="m",
        doc_type="position_statement",
        confidence=ConfidenceConfig(
            default=0.80,
            by_field_type={"currency": 0.90, "number": 0.90, "date": 0.85, "string": 0.75},
        ),
    )


@pytest.fixture
def gated_source(source: SourceConfig) -> SourceConfig:
    """The same source, with the confidence gate wired into the rules engine."""
    return source.model_copy(
        update={
            "rules": [RuleConfig(id="confidence_gate", type="confidence_gate")],
        }
    )


@pytest.fixture
def completeness_source(source: SourceConfig) -> SourceConfig:
    """A source configured with only the two NWD-142 completeness rules.

    Isolated on purpose: when one of these tests fails you want to know the
    completeness rule broke, not that some unrelated required-field rule fired.
    """
    return source.model_copy(
        update={
            "line_item_count_field": "declared_line_item_count",
            "rules": [
                RuleConfig(id="declared_line_item_count", type="line_item_count"),
                RuleConfig(id="page_continuation", type="page_continuation"),
            ],
        }
    )


@pytest.fixture
def azure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Endpoints the settings loader requires. No credentials — there are none."""
    monkeypatch.setenv("DOC_INTEL_ENDPOINT", "https://doc-intel.example.net/")
    monkeypatch.setenv("LANGUAGE_ENDPOINT", "https://language.example.net/")
    monkeypatch.setenv("TRANSLATOR_ENDPOINT", "https://translator.example.net/")
    monkeypatch.setenv("STORAGE_ACCOUNT_URL", "https://northwind.blob.core.windows.net")


@pytest.fixture
def settings(azure_env: None):
    """The real ``config/sources.yaml``, parsed.

    Tests use the shipped configuration rather than a fixture copy so that a
    typo in the YAML fails the suite. Configuration is code here — onboarding a
    counterparty is a YAML change, so YAML gets the same scrutiny.
    """
    return load_settings()


@pytest.fixture
def broker_alpha(settings) -> SourceConfig:
    return settings.sources["broker_alpha"]


@pytest.fixture
def broker_beta(settings) -> SourceConfig:
    return settings.sources["broker_beta_em"]


# -----------------------------------------------------------------------------
# Azure stubs — used only by tests/test_extract.py
# -----------------------------------------------------------------------------


class _StubDocumentField:
    """Stands in for ``azure.ai.documentintelligence.models.DocumentField``.

    Only the attributes ``core/extract.py`` actually reads are present, which is
    the point: a narrow surface is easy to fake faithfully.
    """

    def __init__(
        self,
        field_type: str,
        *,
        confidence: float | None = None,
        content: str | None = None,
        page: int | None = None,
        value_string: str | None = None,
        value_number: float | None = None,
        value_integer: int | None = None,
        value_date: date | None = None,
        value_time: Any = None,
        value_currency: Any = None,
        value_selection_mark: Any = None,
        value_array: list | None = None,
        value_object: dict | None = None,
    ) -> None:
        self.type = field_type
        self.confidence = confidence
        self.content = content
        self.value_string = value_string
        self.value_number = value_number
        self.value_integer = value_integer
        self.value_date = value_date
        self.value_time = value_time
        self.value_currency = value_currency
        self.value_selection_mark = value_selection_mark
        self.value_array = value_array
        self.value_object = value_object
        self.bounding_regions = (
            [types.SimpleNamespace(page_number=page)] if page is not None else []
        )


@pytest.fixture
def stub_field():
    """Expose the stub field class to tests."""
    return _StubDocumentField


@pytest.fixture
def stub_azure_sdk(monkeypatch: pytest.MonkeyPatch):
    """Install the two SDK symbols ``core/extract.py`` imports at call time.

    The whole stub is a dozen lines because the module's contact with the SDK is
    a request object and two exception classes. If this fixture ever needs to
    grow, that is a signal the Azure surface has leaked further into the code
    than it should have.
    """
    models = types.ModuleType("azure.ai.documentintelligence.models")

    class AnalyzeDocumentRequest:  # noqa: D401 - a stub, not documentation
        def __init__(self, bytes_source: bytes | None = None, **kwargs: Any) -> None:
            self.bytes_source = bytes_source

    class ClassifyDocumentRequest:
        def __init__(self, bytes_source: bytes | None = None, **kwargs: Any) -> None:
            self.bytes_source = bytes_source

    models.AnalyzeDocumentRequest = AnalyzeDocumentRequest
    models.ClassifyDocumentRequest = ClassifyDocumentRequest

    exceptions = types.ModuleType("azure.core.exceptions")

    class ServiceRequestError(Exception):
        pass

    class ServiceResponseError(Exception):
        pass

    exceptions.ServiceRequestError = ServiceRequestError
    exceptions.ServiceResponseError = ServiceResponseError

    installed = {
        "azure": types.ModuleType("azure"),
        "azure.ai": types.ModuleType("azure.ai"),
        "azure.ai.documentintelligence": types.ModuleType("azure.ai.documentintelligence"),
        "azure.ai.documentintelligence.models": models,
        "azure.core": types.ModuleType("azure.core"),
        "azure.core.exceptions": exceptions,
    }
    for name, module in installed.items():
        if name not in sys.modules:
            monkeypatch.setitem(sys.modules, name, module)
        elif name.endswith(("models", "exceptions")):
            monkeypatch.setitem(sys.modules, name, module)

    return types.SimpleNamespace(
        models=models,
        ServiceRequestError=ServiceRequestError,
        ServiceResponseError=ServiceResponseError,
    )
