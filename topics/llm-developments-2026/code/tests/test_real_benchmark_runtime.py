from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.benchmark_loader import load_benchmark_manifest
from llm_dev_2026.real_benchmark_cli import main as real_benchmark_main
from llm_dev_2026.real_benchmark_runtime import (
    format_real_benchmark_summary,
    run_real_benchmark_readiness,
)


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_real_benchmark_readiness_marks_sample_tasks_ready():
    manifest = load_benchmark_manifest(_sample_path())
    report = run_real_benchmark_readiness(manifest)
    assert report.task_count == 15
    assert report.ready_task_count == 15
    assert report.repos_missing == []
    assert all(task.ready for task in report.tasks)


def test_real_benchmark_summary_mentions_readiness():
    manifest = load_benchmark_manifest(_sample_path())
    summary = format_real_benchmark_summary(run_real_benchmark_readiness(manifest))
    assert "ready=15/15" in summary
    assert "topics.inspect.deepseek_architecture_lane" in summary


def test_real_benchmark_cli_writes_json(tmp_path):
    out = tmp_path / "real-benchmark.json"
    assert real_benchmark_main([str(_sample_path()), "--out", str(out), "--quiet"]) == 0
    payload = json.loads(out.read_text())
    assert payload["benchmark_id"] == "real-repos-sample"
    assert payload["ready_task_count"] == payload["task_count"] == 15
