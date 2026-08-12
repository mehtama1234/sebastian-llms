from __future__ import annotations

from pathlib import Path

import pytest

from llm_dev_2026.benchmark_loader import load_benchmark_manifest, validate_manifest_paths
from llm_dev_2026.benchmark_schema import (
    BenchmarkManifest,
    EvidenceSpan,
    RealTask,
    RepoSpec,
    ValidationSpec,
    manifest_from_dict,
)
from llm_dev_2026.task_pack import TaskPack


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_load_sample_benchmark_manifest():
    manifest = load_benchmark_manifest(_sample_path())
    assert manifest.benchmark_id == "real-repos-sample"
    assert len(manifest.repos) == 2
    assert len(manifest.tasks) == 15
    assert manifest.tasks[0].validation.mode == "human_review"


def test_manifest_roundtrip():
    manifest = load_benchmark_manifest(_sample_path())
    restored = manifest_from_dict(manifest.to_dict())
    assert restored.to_dict() == manifest.to_dict()


def test_validate_manifest_paths_accepts_existing_workspace_paths():
    manifest = load_benchmark_manifest(_sample_path())
    assert validate_manifest_paths(manifest) == []


def test_task_pack_filters():
    pack = TaskPack(load_benchmark_manifest(_sample_path()))
    assert len(pack.tasks_for_repo("sebastian_topics")) == 15
    assert len(pack.tasks_for_class("research")) == 3
    assert len(pack.tasks_for_class("diagnose")) == 5
    assert len(pack.tasks_for_difficulty("medium")) == 10
    assert len(pack.long_context_tasks()) == 7
    assert [task.task_id for task in pack.slice(task_class="inspect", long_context=True)] == [
        "topics.inspect.deepseek_architecture_lane",
        "topics.inspect.architecture_runtime_entrypoints",
        "topics.inspect.real_indexer_bridge",
        "topics.inspect.attention_budgeting_connection",
    ]


def test_invalid_task_class_raises():
    with pytest.raises(ValueError):
        RealTask(
            task_id="bad",
            repo_id="r",
            repo_commit="c",
            task_class="unknown",
            prompt="x",
            expected_artifact_type="patch",
            validation=ValidationSpec(mode="human_review"),
        )


def test_manifest_rejects_unknown_repo_reference():
    repo = RepoSpec(repo_id="r1", root="/tmp", commit="abc")
    task = RealTask(
        task_id="t1",
        repo_id="missing",
        repo_commit="abc",
        task_class="inspect",
        prompt="inspect",
        expected_artifact_type="memo",
        validation=ValidationSpec(mode="human_review"),
    )
    with pytest.raises(ValueError):
        BenchmarkManifest(benchmark_id="b", version="1", repos=[repo], tasks=[task])


def test_evidence_span_line_validation():
    with pytest.raises(ValueError):
        EvidenceSpan(path="x.py", start_line=10, end_line=9)
