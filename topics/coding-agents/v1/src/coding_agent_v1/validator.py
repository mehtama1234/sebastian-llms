from __future__ import annotations

from .models import ToolResult


def summarize_validation(result: ToolResult | None) -> str:
    if result is None:
        return "No validation was run."
    if result.ok:
        return f"Validation passed via {result.name}."
    return f"Validation failed via {result.name}: {result.output}"
