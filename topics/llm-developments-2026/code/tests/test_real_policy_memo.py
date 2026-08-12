from __future__ import annotations

from pathlib import Path

from llm_dev_2026.real_policy_experiment import retrieval_only_real_policy_matrix, run_real_policy_experiment
from llm_dev_2026.real_policy_memo import generate_real_policy_memo, render_real_policy_memo_markdown


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_generate_real_policy_memo_recommends_one_retrieval_default() -> None:
    report = run_real_policy_experiment(
        str(_sample_path()),
        matrix=retrieval_only_real_policy_matrix(),
    )
    memo = generate_real_policy_memo(report)
    assert memo["recommended_default"] in {
        "real_retrieval_lexical",
        "real_retrieval_sparse",
        "real_retrieval_task_aware",
    }
    assert memo["retrieval_candidates"]
    assert "acceptance_swings_vs_baseline" in memo
    assert "winner_common_misses" in memo


def test_render_real_policy_memo_markdown_has_recommendation() -> None:
    report = run_real_policy_experiment(
        str(_sample_path()),
        matrix=retrieval_only_real_policy_matrix(),
    )
    markdown = render_real_policy_memo_markdown(generate_real_policy_memo(report))
    assert "# Real Retrieval Policy Memo" in markdown
    assert "Recommended retrieval default" in markdown
    assert "real_retrieval_task_aware" in markdown
    assert "Acceptance Swings Vs Lexical" in markdown
    assert "Common Misses" in markdown
