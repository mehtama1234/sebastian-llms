from pathlib import Path

from coding_agent_v1.workspace import detect_repo_root


def test_detect_repo_root_returns_parent_git_dir(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    nested = repo / "src" / "pkg"
    (repo / ".git").mkdir(parents=True)
    nested.mkdir(parents=True)

    assert detect_repo_root(nested) == repo
