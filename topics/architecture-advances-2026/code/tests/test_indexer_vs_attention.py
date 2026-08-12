from __future__ import annotations

from arch_adv_2026.indexer_vs_attention import (
    build_indexer_vs_attention_cases,
    evaluate_variant,
    explain_variant_ranking,
    render_indexer_vs_attention_markdown,
    run_indexer_vs_attention_matrix,
    select_chunks,
)


def test_build_indexer_vs_attention_cases_has_expected_shape() -> None:
    cases = build_indexer_vs_attention_cases()
    assert len(cases) >= 5
    assert any(case.task_type == "multi_hop_spread" for case in cases)
    assert any(len(case.gold_chunk_ids) > 1 for case in cases)
    assert any(case.task_type == "synonym_bridge" for case in cases)


def test_sparse_mixed_can_recover_multihop_support_at_budget_two() -> None:
    case = next(case for case in build_indexer_vs_attention_cases() if case.task_id == "lc_multihop")
    result = evaluate_variant(case, variant="sparse_indexer_mixed", budget_k=2)
    assert result.support_recall == 1.0
    assert result.answer_correct is True


def test_structured_indexer_recovers_synonym_bridge_case_at_budget_two() -> None:
    case = next(case for case in build_indexer_vs_attention_cases() if case.task_id == "lc_synonym_bridge")
    result = evaluate_variant(case, variant="sparse_indexer_structured", budget_k=2)
    assert result.support_recall == 1.0
    assert result.answer_correct is True


def test_structured_indexer_beats_lexical_on_synonym_bridge_at_budget_one() -> None:
    case = next(case for case in build_indexer_vs_attention_cases() if case.task_id == "lc_synonym_bridge")
    lexical = evaluate_variant(case, variant="sparse_indexer_lexical", budget_k=1)
    structured = evaluate_variant(case, variant="sparse_indexer_structured", budget_k=1)
    assert structured.support_recall >= lexical.support_recall


def test_window_plus_anchor_drops_support_under_tight_budget() -> None:
    case = next(case for case in build_indexer_vs_attention_cases() if case.task_id == "lc_multihop")
    result = evaluate_variant(case, variant="window_plus_anchor", budget_k=1)
    assert result.support_recall < 1.0
    assert result.answer_correct is False


def test_selection_variants_return_bounded_chunk_counts() -> None:
    case = build_indexer_vs_attention_cases()[0]
    for variant in [
        "fuller_context_baseline",
        "window_plus_anchor",
        "sparse_indexer_lexical",
        "sparse_indexer_mixed",
        "sparse_indexer_structured",
        "compressed_attention_reference",
    ]:
        selected = select_chunks(case, variant=variant, budget_k=2)
        assert 1 <= len(selected) <= 2


def test_run_indexer_vs_attention_matrix_builds_summary() -> None:
    report = run_indexer_vs_attention_matrix(budgets=[1, 2])
    assert report["task_count"] >= 5
    assert "sparse_indexer_mixed" in report["summary"]
    assert "sparse_indexer_structured" in report["summary"]
    assert report["summary"]["compressed_attention_reference"]["budgets"] == [1, 2]
    assert len(report["diagnostics"]) == report["task_count"]


def test_explain_variant_ranking_exposes_structured_breakdown() -> None:
    case = next(case for case in build_indexer_vs_attention_cases() if case.task_id == "lc_verifier_chain")
    ranking = explain_variant_ranking(case, variant="sparse_indexer_structured")
    assert ranking[0]["score"] >= ranking[-1]["score"]
    assert "path_overlap" in ranking[0]["breakdown"]


def test_render_indexer_vs_attention_markdown_has_tables() -> None:
    markdown = render_indexer_vs_attention_markdown(run_indexer_vs_attention_matrix(budgets=[1]))
    assert "# Indexer vs Attention Report" in markdown
    assert "Mean Support Recall" in markdown
    assert "sparse_indexer_mixed" in markdown
    assert "Structured Indexer Diagnostics" in markdown
