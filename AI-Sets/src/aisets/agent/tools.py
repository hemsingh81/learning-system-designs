"""
`@tool` — turn a plain Python function into something an agent can call.

Why this matters: a tool's description IS a prompt. The model decides
whether and how to call a tool based ONLY on its name, description, and
argument schema — it never sees the function's source code. Write the
docstring the way you'd write an internal API's documentation: precise,
with units and examples, because that's literally what the model reads.

How it works: we inspect the function's signature (type hints + defaults)
and build a Pydantic model for its arguments, the same way FastAPI builds
a request-body model from a route function's parameters. The JSON Schema
of that model becomes `ToolSpec.parameters` — the shape the model must
fill in when it calls this tool.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Any, Callable, Literal

from pydantic import BaseModel, ValidationError, create_model

from aisets.llm.base import ToolSpec

Permission = Literal["read", "write"]


class ToolError(Exception):
    """The tool was called with bad arguments, or raised while running."""


class ToolPermissionError(Exception):
    """A 'write' tool was invoked in a context that only allows 'read'
    tools — see `ToolRegistry.invoke`'s `allow_write` parameter."""


@dataclass
class ToolMeta:
    name: str
    spec: ToolSpec
    args_model: type[BaseModel]
    permission: Permission
    func: Callable[..., Any]


def tool(*, name: str | None = None, permission: Permission = "read"):
    """Decorator: `@tool(permission="read")` above a plain function.

    The function's docstring's first paragraph becomes the tool
    description; its parameters (with type hints) become the argument
    schema. See `src/aisets/tools/db.py` for real examples.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        signature = inspect.signature(func)
        doc = inspect.getdoc(func) or func.__name__
        description = doc.strip().split("\n\n")[0].replace("\n", " ").strip()

        fields: dict[str, Any] = {}
        for param_name, param in signature.parameters.items():
            if param_name == "self":
                continue
            annotation = param.annotation if param.annotation is not inspect.Parameter.empty else str
            default = param.default if param.default is not inspect.Parameter.empty else ...
            fields[param_name] = (annotation, default)

        args_model = create_model(f"{func.__name__}_Args", **fields)  # type: ignore[call-overload]
        tool_name = name or func.__name__
        spec = ToolSpec(
            name=tool_name,
            description=description,
            parameters=args_model.model_json_schema(),
        )
        meta = ToolMeta(name=tool_name, spec=spec, args_model=args_model, permission=permission, func=func)

        func._tool_meta = meta  # type: ignore[attr-defined]
        return func

    return decorator


def get_tool_meta(func: Callable[..., Any]) -> ToolMeta:
    meta = getattr(func, "_tool_meta", None)
    if meta is None:
        raise ToolError(f"{func!r} is not decorated with @tool — cannot register it.")
    return meta


def validate_and_call(meta: ToolMeta, arguments: dict[str, Any]) -> Any:
    """Validate `arguments` against the tool's schema, then call the
    underlying function. Raises `ToolError` for either a bad-argument or
    an in-function failure — callers (the agent loop) catch ONE error
    type regardless of which kind it was."""
    try:
        validated = meta.args_model.model_validate(arguments)
    except ValidationError as exc:
        raise ToolError(f"invalid arguments for tool '{meta.name}': {exc}") from exc

    try:
        return meta.func(**validated.model_dump())
    except Exception as exc:  # noqa: BLE001 - any tool failure becomes a ToolError
        raise ToolError(f"tool '{meta.name}' raised an error: {exc}") from exc
