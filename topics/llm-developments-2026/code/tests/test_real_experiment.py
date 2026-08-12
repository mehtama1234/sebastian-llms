from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.real_experiment import run_real_experiment
from llm_dev_2026.real_experiment_cli import main as real_experiment_main


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_real_experiment_builds_scorecard_for_sample_manifest():
    report = run_real_experiment(str(_sample_path()), provider_backend="local", run_validation_checks=False)
    assert report.task_count == 15
    assert 0.0 <= report.scorecard.accepted_rate <= 1.0
    assert report.scorecard.task_count == 15
    assert report.scorecard.success_by_task_class
    assert report.scorecard.retrieval_diagnostics["task_with_any_gold_hit_rate"] == 1.0
    assert report.scorecard.response_tokens_per_accepted_task > 0.0


def test_real_experiment_supports_task_filters():
    report = run_real_experiment(
        str(_sample_path()),
        provider_backend="local",
        run_validation_checks=False,
        difficulty="hard",
    )
    assert report.task_count == 3
    assert {task.task_id for task in report.tasks} == {
        "topics.research.production_experiment_goal",
        "topics.research.real_retrieval_default",
        "topics.research.real_retrieval_rollout_checklist",
    }


def test_real_experiment_supports_sparse_evidence_selection():
    report = run_real_experiment(
        str(_sample_path()),
        provider_backend="local",
        run_validation_checks=False,
        evidence_selection="sparse",
        evidence_top_k=1,
        task_class="diagnose",
    )
    assert report.task_count == 5
    assert {
        task.task_id: task.runtime["request"]["context_snippets"][0]["path"]
        for task in report.tasks
    } == {
        "topics.diagnose.llm_dev_verifier_flow": "llm-developments-2026/code/src/llm_dev_2026/meta_verifier.py",
        "topics.diagnose.real_task_failure_stages": "llm-developments-2026/code/src/llm_dev_2026/runtime.py",
        "topics.diagnose.verifier_runtime_bridge": "llm-developments-2026/code/src/llm_dev_2026/real_task_verifier.py",
        "topics.diagnose.openai_provider_grounding": "llm-developments-2026/code/src/llm_dev_2026/provider.py",
        "topics.diagnose.policy_matrix_execution": "llm-developments-2026/code/src/llm_dev_2026/real_policy_experiment.py",
    }


def test_real_experiment_supports_repo_retrieval():
    report = run_real_experiment(
        str(_sample_path()),
        provider_backend="local",
        run_validation_checks=False,
        evidence_source="retrieval",
        retrieval_mode="lexical",
        retrieval_top_k=2,
        task_class="inspect",
    )
    assert report.task_count == 5
    retrieved = {
        task.task_id: [snippet["path"] for snippet in task.runtime["request"]["context_snippets"]]
        for task in report.tasks
    }
    assert set(retrieved) == {
        "topics.inspect.deepseek_architecture_lane",
        "topics.inspect.architecture_runtime_entrypoints",
        "topics.inspect.real_indexer_bridge",
        "topics.inspect.policy_memo_runtime_update",
        "topics.inspect.attention_budgeting_connection",
    }
    assert "architecture-advances-2026/docs/compressed-attention-promotion-goal.md" in retrieved["topics.inspect.deepseek_architecture_lane"]
    assert "architecture-advances-2026/docs/compressed-attention-promotion-goal.md" in retrieved["topics.inspect.architecture_runtime_entrypoints"]
    assert retrieved["topics.inspect.real_indexer_bridge"] == [
        "architecture-advances-2026/code/src/arch_adv_2026/real_indexer_vs_attention.py",
        "architecture-advances-2026/projects/indexer-vs-attention-goal.md",
    ]
    assert "llm-developments-2026/projects/experiment-findings.md" in retrieved["topics.inspect.policy_memo_runtime_update"]
    assert "architecture-advances-2026/docs/compressed-attention.md" in retrieved["topics.inspect.attention_budgeting_connection"]


def test_real_experiment_cli_writes_json(tmp_path):
    out = tmp_path / "real-experiment.json"
    assert real_experiment_main(
        [
            str(_sample_path()),
            "--provider",
            "local",
            "--skip-validation",
            "--out",
            str(out),
            "--quiet",
        ]
    ) == 0
    payload = json.loads(out.read_text())
    assert payload["benchmark_id"] == "real-repos-sample"
    assert payload["scorecard"]["task_count"] == 15
