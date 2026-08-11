from pathlib import Path

from coding_agent_v1.models import PermissionOutcome, ToolKind, ToolRequest
from coding_agent_v1.permissions import decide_permission


def test_read_only_request_is_allowed(tmp_path: Path) -> None:
    request = ToolRequest(name="read_file", kind=ToolKind.READ_ONLY, target="README.md")

    assert decide_permission(request, tmp_path) is PermissionOutcome.ALLOW


def test_absolute_path_outside_workspace_is_denied(tmp_path: Path) -> None:
    external = tmp_path.parent / "external.txt"
    request = ToolRequest(name="edit_file", kind=ToolKind.FILE_EDIT, target=str(external))

    assert decide_permission(request, tmp_path) is PermissionOutcome.DENY
