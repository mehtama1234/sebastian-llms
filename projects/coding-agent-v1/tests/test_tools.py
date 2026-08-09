from pathlib import Path

from coding_agent_v1.models import ToolKind, ToolRequest
from coding_agent_v1.tools import execute_tool


def test_execute_read_file_reads_workspace_file(tmp_path: Path) -> None:
    file_path = tmp_path / "README.md"
    file_path.write_text("hello world", encoding="utf-8")

    result = execute_tool(
        ToolRequest(
            name="read_file",
            kind=ToolKind.READ_ONLY,
            target="README.md",
            args={"max_chars": "100"},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert "hello world" in result.output


def test_execute_search_code_finds_pattern(tmp_path: Path) -> None:
    file_path = tmp_path / "app.py"
    file_path.write_text("print('target')\n", encoding="utf-8")

    result = execute_tool(
        ToolRequest(
            name="search_code",
            kind=ToolKind.READ_ONLY,
            target=".",
            args={"pattern": "target"},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert "app.py:1:" in result.output


def test_execute_search_code_ignores_runtime_artifacts(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    cache_dir = tmp_path / ".pytest_cache" / "v"
    source.write_text("print('target')\n", encoding="utf-8")
    cache_dir.mkdir(parents=True)
    (cache_dir / "cache.txt").write_text("target\n", encoding="utf-8")

    result = execute_tool(
        ToolRequest(
            name="search_code",
            kind=ToolKind.READ_ONLY,
            target=".",
            args={"pattern": "target"},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert "app.py:1:" in result.output
    assert ".pytest_cache" not in result.output


def test_execute_edit_file_replaces_unique_text(tmp_path: Path) -> None:
    file_path = tmp_path / "config.txt"
    file_path.write_text("alpha=1\n", encoding="utf-8")

    result = execute_tool(
        ToolRequest(
            name="edit_file",
            kind=ToolKind.FILE_EDIT,
            target="config.txt",
            args={"old_text": "alpha=1", "new_text": "alpha=2"},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert file_path.read_text(encoding="utf-8") == "alpha=2\n"


def test_execute_rename_symbol_in_file_replaces_exact_symbol_matches(tmp_path: Path) -> None:
    file_path = tmp_path / "calc.py"
    file_path.write_text(
        "def add(a, b):\n    total = add_impl(a, b)\n    return total\n",
        encoding="utf-8",
    )

    result = execute_tool(
        ToolRequest(
            name="rename_symbol_in_file",
            kind=ToolKind.FILE_EDIT,
            target="calc.py",
            args={"old_name": "add", "new_name": "plus"},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert "calc.py" in result.output
    updated = file_path.read_text(encoding="utf-8")
    assert "def plus(a, b):" in updated
    assert "add_impl" in updated


def test_execute_run_command_runs_inside_workspace(tmp_path: Path) -> None:
    result = execute_tool(
        ToolRequest(
            name="run_command",
            kind=ToolKind.COMMAND,
            target=".",
            args={"command": "python3 -c \"print('ok')\""},
        ),
        tmp_path,
    )

    assert result.ok is True
    assert "ok" in result.output
