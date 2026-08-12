from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.real_retrieval_slice_report import (
    build_real_retrieval_slice_report,
    main as real_retrieval_slice_report_main,
    render_real_retrieval_slice_report_markdown,
)


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_build_real_retrieval_slice_report_contains_expected_slices() -> None:
    report = build_real_retrieval_slice_report(str(_sample_path()))
    slice_names = {item["name"] for item in report["slices"]}
    assert {"all", "long_context", "short_context", "inspect", "diagnose", "bug_fix", "research"} <= slice_names
    overall = next(item for item in report["slices"] if item["name"] == "all")
    assert overall["task_count"] == 15
    assert overall["recommended_default"] in {
        "real_retrieval_lexical",
        "real_retrieval_sparse",
        "real_retrieval_task_aware",
    }


def test_render_real_retrieval_slice_report_markdown_has_sections() -> None:
    markdown = render_real_retrieval_slice_report_markdown(
        build_real_retrieval_slice_report(str(_sample_path()))
    )
    assert "# Real Retrieval Slice Report" in markdown
    assert "## all" in markdown
    assert "## inspect" in markdown
    assert "Tokens / Accepted Task" in markdown


def test_real_retrieval_slice_report_cli_writes_json(tmp_path) -> None:
    out = tmp_path / "slice-report.json"
    assert real_retrieval_slice_report_main([str(_sample_path()), "--artifact-json", str(out)]) == 0
    payload = json.loads(out.read_text())
    assert payload["report_type"] == "real_retrieval_slice_report"
    assert payload["slices"]
