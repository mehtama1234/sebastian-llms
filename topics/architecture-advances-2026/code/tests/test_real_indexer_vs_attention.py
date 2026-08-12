from __future__ import annotations

from pathlib import Path

from arch_adv_2026.real_indexer_vs_attention import (
    build_real_indexer_vs_attention_report,
    render_real_indexer_vs_attention_markdown,
)


def _sample_manifest() -> Path:
    return (
        Path(__file__).resolve().parents[3]
        / "llm-developments-2026"
        / "evals"
        / "datasets"
        / "real-repos"
        / "sample-benchmark.json"
    )


def test_build_real_indexer_vs_attention_report_has_expected_shape() -> None:
    report = build_real_indexer_vs_attention_report(_sample_manifest(), budgets=[1, 2], candidate_pool_k=4)
    assert report["task_count"] >= 4
    assert "union_structured_rerank" in report["summary"]
    assert "task_aware_balanced_rerank" in report["summary"]
    assert report["candidate_pool_k"] == 4
    assert report["rows"]
    assert report["diagnostics"]


def test_real_report_structured_variant_hits_support_on_some_rows() -> None:
    report = build_real_indexer_vs_attention_report(_sample_manifest(), budgets=[2], candidate_pool_k=6)
    structured_rows = [row for row in report["rows"] if row["variant"] == "union_structured_rerank"]
    assert any(row["any_support_hit"] for row in structured_rows)


def test_task_aware_balanced_rerank_recovers_bug_fix_support_at_budget_two() -> None:
    report = build_real_indexer_vs_attention_report(_sample_manifest(), budgets=[2], candidate_pool_k=6)
    rows = [
        row
        for row in report["rows"]
        if row["variant"] == "task_aware_balanced_rerank"
        and row["task_id"] == "topics.bug_fix.sample_benchmark_loader_tests"
        and row["budget_k"] == 2
    ]
    assert rows
    assert rows[0]["exact_support_hit"] is True


def test_render_real_indexer_vs_attention_markdown_has_key_sections() -> None:
    markdown = render_real_indexer_vs_attention_markdown(
        build_real_indexer_vs_attention_report(_sample_manifest(), budgets=[1], candidate_pool_k=4)
    )
    assert "# Real Indexer vs Attention Report" in markdown
    assert "Mean Support Recall" in markdown
    assert "Structured Diagnostics" in markdown
    assert "task_aware_balanced_rerank" in markdown
