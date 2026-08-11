from __future__ import annotations

from pathlib import Path

from .models import PermissionOutcome, ToolKind, ToolRequest


def decide_permission(request: ToolRequest, workspace_root: Path) -> PermissionOutcome:
    target_path = Path(request.target)
    if target_path.is_absolute():
        try:
            target_path.resolve().relative_to(workspace_root.resolve())
        except ValueError:
            return PermissionOutcome.DENY

    if request.kind is ToolKind.READ_ONLY:
        return PermissionOutcome.ALLOW
    if request.kind is ToolKind.APPROVAL:
        return PermissionOutcome.ALLOW
    return PermissionOutcome.ASK
