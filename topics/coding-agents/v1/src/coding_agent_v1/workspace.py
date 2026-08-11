from __future__ import annotations

import subprocess
from pathlib import Path

from .models import WorkspaceSummary


def detect_repo_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".git").exists():
            return candidate
    return current


def _git_output(repo_root: Path, args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def build_workspace_summary(start: Path) -> WorkspaceSummary:
    repo_root = detect_repo_root(start)
    entries = sorted(path.name for path in repo_root.iterdir())
    instruction_candidates = ["README.md", "README", "AGENTS.md", "CLAUDE.md"]
    instruction_files = [
        name for name in instruction_candidates if (repo_root / name).exists()
    ]
    return WorkspaceSummary(
        root=repo_root,
        branch=_git_output(repo_root, ["branch", "--show-current"]),
        git_status=_git_output(repo_root, ["status", "--short"]),
        top_level_entries=entries,
        instruction_files=instruction_files,
    )
