"""Unit tests for agent/tools.py (@tool decorator, schema generation) and
agent/registry.py (ToolRegistry: lookup, permission gating, invocation)."""

from __future__ import annotations

import pytest

from aisets.agent.registry import ToolRegistry
from aisets.agent.tools import ToolError, ToolPermissionError, tool


@tool(permission="read", name="add_numbers")
def add_numbers(a: int, b: int = 10) -> int:
    """Add two integers together, `b` defaults to 10 if not given."""
    return a + b


@tool(permission="write", name="delete_thing")
def delete_thing(thing_id: str) -> dict:
    """Delete a thing by id. Dangerous, write-permission only."""
    return {"deleted": thing_id}


@tool(permission="read", name="always_fails")
def always_fails(x: int) -> int:
    """A tool that always raises, to test error wrapping."""
    raise RuntimeError("boom")


def test_schema_generation_includes_params_and_types() -> None:
    meta = add_numbers._tool_meta
    schema = meta.spec.parameters

    assert "a" in schema["properties"]
    assert "b" in schema["properties"]
    assert schema["properties"]["a"]["type"] == "integer"
    assert "a" in schema.get("required", [])
    assert "b" not in schema.get("required", [])  # has a default


def test_description_comes_from_docstring_first_paragraph() -> None:
    meta = add_numbers._tool_meta
    assert meta.spec.description.startswith("Add two integers together")


def test_registry_specs_hides_write_tools_by_default() -> None:
    registry = ToolRegistry().register_all([add_numbers, delete_thing])

    read_only_specs = registry.specs(allow_write=False)
    all_specs = registry.specs(allow_write=True)

    assert {s.name for s in read_only_specs} == {"add_numbers"}
    assert {s.name for s in all_specs} == {"add_numbers", "delete_thing"}


def test_registry_invoke_happy_path() -> None:
    registry = ToolRegistry().register(add_numbers)
    result = registry.invoke("add_numbers", {"a": 5, "b": 2})
    assert result == 7


def test_registry_invoke_uses_default_argument() -> None:
    registry = ToolRegistry().register(add_numbers)
    result = registry.invoke("add_numbers", {"a": 5})
    assert result == 15


def test_registry_invoke_unknown_tool_raises_tool_error() -> None:
    registry = ToolRegistry().register(add_numbers)
    with pytest.raises(ToolError, match="unknown tool"):
        registry.invoke("does_not_exist", {})


def test_registry_invoke_invalid_arguments_raises_tool_error() -> None:
    registry = ToolRegistry().register(add_numbers)
    with pytest.raises(ToolError, match="invalid arguments"):
        registry.invoke("add_numbers", {"a": "not a number"})


def test_registry_denies_write_tool_without_allow_write() -> None:
    registry = ToolRegistry().register(delete_thing)
    with pytest.raises(ToolPermissionError, match="requires write permission"):
        registry.invoke("delete_thing", {"thing_id": "x1"})


def test_registry_allows_write_tool_with_allow_write() -> None:
    registry = ToolRegistry().register(delete_thing)
    result = registry.invoke("delete_thing", {"thing_id": "x1"}, allow_write=True)
    assert result == {"deleted": "x1"}


def test_tool_runtime_error_is_wrapped_as_tool_error() -> None:
    registry = ToolRegistry().register(always_fails)
    with pytest.raises(ToolError, match="raised an error"):
        registry.invoke("always_fails", {"x": 1})
