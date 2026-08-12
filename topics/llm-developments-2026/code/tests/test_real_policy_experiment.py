from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.real_policy_experiment import (
    REAL_BASELINE,
    RealPolicyConfig,
    RealPolicyMatrix,
    default_real_policy_matrix,
    run_real_policy_experiment,
)
from llm_dev_2026.real_policy_experiment_cli import main as real_policy_experiment_main


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_default_real_policy_matrix_names_unique():
    names = [config.name for config in default_real_policy_matrix().configs]
    assert len(names) == len(set(names))


def test_real_policy_experiment_covers_configs_and_comparisons():
    default_matrix = default_real_policy_matrix()
    for config in default_matrix.configs:
        assert config.name

    matrix = RealPolicyMatrix(
        label="llm-developments-2026-real-policy-test",
        configs=[
            RealPolicyConfig(REAL_BASELINE, provider_backend="local", evidence_source="gold", evidence_selection="all", run_validation_checks=False),
            RealPolicyConfig("real_retrieval_lexical", provider_backend="local", evidence_source="retrieval", retrieval_mode="lexical", retrieval_top_k=2, run_validation_checks=False),
            RealPolicyConfig("real_retrieval_task_aware", provider_backend="local", evidence_source="retrieval", retrieval_mode="task_aware", retrieval_top_k=2, run_validation_checks=False),
        ],
    )
    report = run_real_policy_experiment(str(_sample_path()), matrix=matrix)
    for config in matrix.configs:
        assert config.name in report.scorecards
    assert REAL_BASELINE in report.reports
    assert report.comparisons
    assert any(delta.candidate == "real_retrieval_lexical" for delta in report.comparisons)
    assert any(delta.candidate == "real_retrieval_task_aware" for delta in report.comparisons)


def test_real_policy_experiment_cli_writes_json(tmp_path):
    out = tmp_path / "real-policy.json"
    assert real_policy_experiment_main([str(_sample_path()), "--out", str(out), "--quiet"]) == 0
    payload = json.loads(out.read_text())
    assert payload["label"] == "llm-developments-2026-real-policy-default"
    assert "real_baseline" in payload["scorecards"]
