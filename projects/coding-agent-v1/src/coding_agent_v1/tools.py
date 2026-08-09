from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import shutil
import subprocess

from .models import ToolKind, ToolRequest, ToolResult


@dataclass(slots=True)
class ToolSpec:
    name: str
    kind: ToolKind
    description: str


TOOL_SPECS = [
    ToolSpec("read_file", ToolKind.READ_ONLY, "Read a file from the workspace."),
    ToolSpec("search_code", ToolKind.READ_ONLY, "Search code or text in the workspace."),
    ToolSpec("edit_file", ToolKind.FILE_EDIT, "Apply a targeted file edit."),
    ToolSpec("rename_symbol_in_file", ToolKind.FILE_EDIT, "Rename an exact symbol across one file."),
    ToolSpec("run_command", ToolKind.COMMAND, "Run a bounded shell command."),
    ToolSpec("request_approval", ToolKind.APPROVAL, "Ask the user to approve a risky action."),
]

IGNORED_PATH_PARTS = {".git", ".pytest_cache", "__pycache__", ".coding-agent-v1", "sessions"}


def get_tool_spec(name: str) -> ToolSpec | None:
    for spec in TOOL_SPECS:
        if spec.name == name:
            return spec
    return None


def resolve_workspace_path(workspace_root: Path, target: str) -> Path:
    candidate = Path(target)
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    resolved = candidate.resolve()
    resolved.relative_to(workspace_root.resolve())
    return resolved


def is_ignored_path(path: Path, workspace_root: Path) -> bool:
    try:
        rel = path.resolve().relative_to(workspace_root.resolve())
    except ValueError:
        return True
    return any(part in IGNORED_PATH_PARTS for part in rel.parts)


def execute_tool(request: ToolRequest, workspace_root: Path) -> ToolResult:
    handlers = {
        "read_file": execute_read_file,
        "search_code": execute_search_code,
        "edit_file": execute_edit_file,
        "rename_symbol_in_file": execute_rename_symbol_in_file,
        "run_command": execute_run_command,
        "request_approval": execute_request_approval,
    }
    handler = handlers.get(request.name)
    if handler is None:
        return ToolResult(name=request.name, ok=False, output=f"Unknown tool: {request.name}")
    try:
        return handler(request, workspace_root)
    except ValueError as exc:
        return ToolResult(name=request.name, ok=False, output=str(exc))


def execute_read_file(request: ToolRequest, workspace_root: Path) -> ToolResult:
    path = resolve_workspace_path(workspace_root, request.target)
    if not path.exists():
        return ToolResult(name=request.name, ok=False, output=f"File not found: {path}")
    if not path.is_file():
        return ToolResult(name=request.name, ok=False, output=f"Not a file: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    max_chars = int(request.args.get("max_chars", "4000"))
    clipped = text[:max_chars]
    if len(text) > max_chars:
        clipped += "\n...[clipped]..."
    return ToolResult(name=request.name, ok=True, output=clipped)


def execute_search_code(request: ToolRequest, workspace_root: Path) -> ToolResult:
    pattern = request.args.get("pattern", "").strip()
    if not pattern:
        raise ValueError("search_code requires a non-empty pattern")
    max_hits = int(request.args.get("max_hits", "20"))
    hits: list[str] = []
    for path in sorted(workspace_root.rglob("*")):
        if not path.is_file():
            continue
        if is_ignored_path(path, workspace_root):
            continue
        try:
            rel = path.relative_to(workspace_root)
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern in line:
                hits.append(f"{rel}:{lineno}: {line.strip()}")
                if len(hits) >= max_hits:
                    return ToolResult(name=request.name, ok=True, output="\n".join(hits))
    if not hits:
        return ToolResult(name=request.name, ok=True, output="No matches found.")
    return ToolResult(name=request.name, ok=True, output="\n".join(hits))


def execute_edit_file(request: ToolRequest, workspace_root: Path) -> ToolResult:
    path = resolve_workspace_path(workspace_root, request.target)
    old_text = request.args.get("old_text", "")
    new_text = request.args.get("new_text", "")
    if not old_text:
        raise ValueError("edit_file requires old_text")
    if not path.exists():
        return ToolResult(name=request.name, ok=False, output=f"File not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    occurrences = len(re.findall(re.escape(old_text), text))
    if occurrences == 0:
        return ToolResult(name=request.name, ok=False, output="Target text not found.")
    if occurrences > 1:
        return ToolResult(name=request.name, ok=False, output="Target text is ambiguous.")
    updated = text.replace(old_text, new_text, 1)
    path.write_text(updated, encoding="utf-8")
    rel = path.relative_to(workspace_root)
    return ToolResult(name=request.name, ok=True, output=f"Edited {rel}")


def execute_rename_symbol_in_file(request: ToolRequest, workspace_root: Path) -> ToolResult:
    path = resolve_workspace_path(workspace_root, request.target)
    old_name = request.args.get("old_name", "").strip()
    new_name = request.args.get("new_name", "").strip()
    if not old_name or not new_name:
        raise ValueError("rename_symbol_in_file requires old_name and new_name")
    if old_name == new_name:
        raise ValueError("rename_symbol_in_file requires different old_name and new_name")
    if not path.exists():
        return ToolResult(name=request.name, ok=False, output=f"File not found: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    pattern = re.compile(rf"\b{re.escape(old_name)}\b")
    matches = pattern.findall(text)
    if not matches:
        return ToolResult(name=request.name, ok=False, output=f"Symbol {old_name!r} not found in {path.name}.")
    updated = pattern.sub(new_name, text)
    path.write_text(updated, encoding="utf-8")
    rel = path.relative_to(workspace_root)
    return ToolResult(
        name=request.name,
        ok=True,
        output=f"Renamed {old_name} -> {new_name} in {rel} ({len(matches)} occurrence(s))",
    )


def execute_run_command(request: ToolRequest, workspace_root: Path) -> ToolResult:
    command = request.args.get("command", "").strip()
    if not command:
        raise ValueError("run_command requires a command")
    timeout = float(request.args.get("timeout_seconds", "10"))
    if "pytest" in command:
        _clear_python_caches(workspace_root)
    result = subprocess.run(
        command,
        cwd=workspace_root,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    combined = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    max_chars = int(request.args.get("max_chars", "4000"))
    output = combined[:max_chars]
    if len(combined) > max_chars:
        output += "\n...[clipped]..."
    ok = result.returncode == 0
    return ToolResult(name=request.name, ok=ok, output=output or f"Command exited with {result.returncode}")


def _clear_python_caches(workspace_root: Path) -> None:
    for cache_dir in workspace_root.rglob("__pycache__"):
        if cache_dir.is_dir():
            shutil.rmtree(cache_dir, ignore_errors=True)
    for pyc_file in workspace_root.rglob("*.pyc"):
        try:
            pyc_file.unlink()
        except OSError:
            continue


def execute_request_approval(request: ToolRequest, workspace_root: Path) -> ToolResult:
    _ = workspace_root
    reason = request.args.get("reason", "Action requires approval.")
    return ToolResult(name=request.name, ok=True, output=reason)
