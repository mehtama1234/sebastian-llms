from __future__ import annotations

from arch_adv_2026.indexer_vs_attention import run_indexer_vs_attention_matrix
from arch_adv_2026.indexer_vs_attention_selector import build_indexer_vs_attention_selector


def test_build_indexer_vs_attention_selector_returns_recommendations() -> None:
    report = run_indexer_vs_attention_matrix(budgets=[1, 2])
    selector = build_indexer_vs_attention_selector(report)
    assert selector["selection_policy"]["smallest_budget"] == 1
    assert selector["selection_policy"]["medium_budget"] == 2
    assert "tight_budget" in selector["recommendations"]
    assert "hard_tasks_medium_budget" in selector["recommendations"]


def test_selector_prefers_structured_for_hard_tasks_when_tied_or_better() -> None:
    report = run_indexer_vs_attention_matrix(budgets=[1, 2])
    selector = build_indexer_vs_attention_selector(report)
    hard_pick = selector["recommendations"]["hard_tasks_medium_budget"]["variant"]
    assert hard_pick in {
        "sparse_indexer_structured",
        "sparse_indexer_lexical",
        "sparse_indexer_mixed",
    }
    hard_table = selector["budget_tables"]["hard_tasks_medium_budget"]
    structured = next(row for row in hard_table if row["variant"] == "sparse_indexer_structured")
    assert structured["mean_answer_accuracy"] >= 0.99
