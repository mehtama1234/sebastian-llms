from __future__ import annotations

from llm_dev_2026.real_policy_memo import render_real_policy_memo_markdown


def test_render_real_policy_memo_contract_sections() -> None:
    memo = {
        "recommended_default": "real_retrieval_sparse",
        "retrieval_candidates": [
            {
                "name": "real_retrieval_lexical",
                "accepted_rate": 0.5,
                "grounded_rate": 1.0,
                "task_with_any_gold_hit_rate": 0.5,
                "mean_gold_file_recall": 0.3,
                "validation_pass_rate": 1.0,
                "mean_context_snippets": 2.0,
                "response_tokens_per_accepted_task": 200.0,
            },
            {
                "name": "real_retrieval_sparse",
                "accepted_rate": 0.75,
                "grounded_rate": 1.0,
                "task_with_any_gold_hit_rate": 0.75,
                "mean_gold_file_recall": 0.55,
                "validation_pass_rate": 1.0,
                "mean_context_snippets": 2.0,
                "response_tokens_per_accepted_task": 180.0,
            },
        ],
        "rationale": ["Sparse hits more gold files on this sample."],
        "acceptance_swings_vs_baseline": [
            {
                "task_id": "topics.inspect.real_indexer_bridge",
                "baseline_accepted": False,
                "winner_accepted": True,
                "baseline_hits": [],
                "winner_hits": ["architecture-advances-2026/code/src/arch_adv_2026/real_indexer_vs_attention.py"],
                "baseline_misses": ["architecture-advances-2026/code/src/arch_adv_2026/real_indexer_vs_attention.py"],
                "winner_misses": [],
            }
        ],
        "winner_common_misses": [
            {"path": "llm-developments-2026/projects/meaty-end-to-end-goal.md", "count": 1}
        ],
        "notes": [
            "This memo compares only retrieval-backed policies against each other.",
        ],
    }

    markdown = render_real_policy_memo_markdown(memo)
    assert "# Real Retrieval Policy Memo" in markdown
    assert "Recommended retrieval default: `real_retrieval_sparse`" in markdown
    assert "Acceptance Swings Vs Lexical" in markdown
    assert "Common Misses" in markdown
