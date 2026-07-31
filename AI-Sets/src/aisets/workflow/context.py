"""
`WorkflowContext` — the data bag passed between a pipeline's steps.

Every step reads from and writes to this ONE object, instead of steps
calling each other directly. This is the same idea as passing a shared
"request context" object through an HTTP middleware chain: each piece of
middleware can read what came before it and add its own data, without
needing to know how the earlier pieces produced it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class WorkflowContext:
    values: dict[str, Any] = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.values[key] = value

    def record(self, step_label: str) -> None:
        self.trace.append(step_label)

    def __getitem__(self, key: str) -> Any:
        return self.values[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.values[key] = value
