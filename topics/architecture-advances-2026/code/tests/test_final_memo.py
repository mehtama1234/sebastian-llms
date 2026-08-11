from __future__ import annotations

from arch_adv_2026.final_memo import generate_final_decision_memo, render_final_decision_memo_markdown


def test_generate_final_decision_memo_combines_surfaces() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {
                "variant": "kv_sharing",
                "mean_ratio_vs_baseline_mean": 1.2,
                "estimated_kv_cache_bytes": 100,
            },
            {
                "variant": "compressed_attention",
                "mean_ratio_vs_baseline_mean": 0.9,
                "estimated_kv_cache_bytes": 120,
            },
            {
                "variant": "mhc",
                "mean_ratio_vs_baseline_mean": 1.5,
                "estimated_kv_cache_bytes": 140,
            },
            {
                "variant": "history_compression",
                "mean_ratio_vs_baseline_mean": 1.1,
                "estimated_kv_cache_bytes": 130,
            },
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {
            "quality_preserving_memory": {"variant_kind": "compressed_attention"},
        },
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8, 16],
        "steps_list": [4, 8],
        "seeds": [17, 23],
        "rows": [{}, {}],
        "winner_counts": {
            "fastest_step_ratio": {"compressed_attention": 1, "kv_sharing": 1},
            "lowest_final_loss_delta": {"kv_sharing": 2},
            "lowest_grad_norm_delta": {"compressed_attention": 1, "kv_sharing": 1},
        },
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": 1.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "kv_sharing",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": 0.5,
                "final_loss_delta_vs_baseline_range": 0.1,
                "mean_step_ms_ratio_vs_baseline_mean": 0.9,
                "mean_step_ms_ratio_vs_baseline_range": 0.3,
                "max_grad_norm_delta_vs_baseline_mean": 3.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 1.0,
            },
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1, 2], "seq_lens": [4, 8]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variant": "compressed_attention",
            "lowest_kv_variant": "kv_sharing",
            "grid_cell_count": 4,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.3},
            {"variant": "mhc", "mean_ratio_across_grid": 1.4, "worst_ratio_across_grid": 1.6},
            {"variant": "history_compression", "mean_ratio_across_grid": 1.1, "worst_ratio_across_grid": 1.4},
        ],
    }
    review_plan = {
        "summary": {
            "priority_variants": ["kv_sharing"],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {
                "variant": "kv_sharing",
                "suggested_decision": "exploratory",
            }
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert memo["default_carry_forward_variant"] == "compressed_attention"
    assert "kv_sharing" not in memo["secondary_variants"]
    assert "kv_sharing" in memo["exploratory_variants"]
    assert "mhc" in memo["exploratory_variants"]
    assert memo["evidence"]["training_summary"]["stable_fastest_variant"] == "compressed_attention"
    assert memo["evidence"]["training_summary"]["stable_lowest_final_loss_delta_variant"] == "kv_sharing"
    assert memo["evidence"]["review_summary"]["priority_variants"] == ["kv_sharing"]
    assert memo["evidence"]["review_summary"]["raw_mismatch_variants"] == ["attention_budgeting"]
    assert memo["evidence"]["review_summary"]["resolved_mismatch_variants"] == ["attention_budgeting"]
    assert memo["evidence"]["review_summary"]["unresolved_mismatch_variants"] == []
    assert memo["evidence"]["benchmark_summary"]["best_mean_runtime_variant"] == "compressed_attention"
    assert memo["evidence_matrix"][0]["has_training_evidence"] in {True, False}
    assert memo["evidence_matrix"][0]["benchmark_worst_ratio_across_grid"] is not None
    markdown = render_final_decision_memo_markdown(memo)
    assert "Architecture Advances 2026 Final Decision Memo" in markdown
    assert "`compressed_attention`" in markdown
    assert "Training matrix coverage" in markdown
    assert "Matrix winner counts" in markdown
    assert "Stable matrix leaders" in markdown
    assert "Benchmark matrix coverage" in markdown
    assert "Benchmark matrix leaders" in markdown
    assert "Focused review priorities" in markdown
    assert "Raw audit mismatches" in markdown
    assert "Resolved mismatches via focused follow-up" in markdown
    assert any(
        (
            "strongest blended quality-preserving systems trade" in line
            or "also the fastest micro runtime direction" in line
        )
        for line in memo["recommendations"]
    )


def test_generate_final_decision_memo_surfaces_active_unresolved_mismatches() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.2, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 120},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "kv_sharing",
            "lowest_kv_variants": ["kv_sharing"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.1},
        ],
    }
    review_plan = {
        "summary": {
            "priority_variants": ["attention_budgeting"],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        },
        "rows": [
            {
                "variant": "attention_budgeting",
                "priority": 3,
                "suggested_decision": "secondary",
            }
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert any("Active unresolved decision mismatches still needing review" in line for line in memo["summary_lines"])
    markdown = render_final_decision_memo_markdown(memo)
    assert "Active unresolved mismatches" in markdown


def test_generate_final_decision_memo_falls_back_to_legacy_mismatch_summary_field() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.2, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 120},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "kv_sharing",
            "lowest_kv_variants": ["kv_sharing"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.1},
        ],
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        },
        "rows": [],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert memo["evidence"]["review_summary"]["raw_mismatch_variants"] == ["attention_budgeting"]


def test_generate_final_decision_memo_keeps_secondary_when_followup_conflicts() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.2, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 120},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": 1.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "kv_sharing",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": 0.5,
                "final_loss_delta_vs_baseline_range": 0.1,
                "mean_step_ms_ratio_vs_baseline_mean": 0.9,
                "mean_step_ms_ratio_vs_baseline_range": 0.3,
                "max_grad_norm_delta_vs_baseline_mean": 3.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 1.0,
            },
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variant": "compressed_attention",
            "lowest_kv_variant": "kv_sharing",
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.35},
            {"variant": "mhc", "mean_ratio_across_grid": 1.4, "worst_ratio_across_grid": 1.5},
            {"variant": "history_compression", "mean_ratio_across_grid": 1.1, "worst_ratio_across_grid": 1.2},
        ],
    }
    review_plan = {
        "summary": {"priority_variants": ["kv_sharing"], "resolved_mismatch_variants": []},
        "rows": [
            {
                "variant": "kv_sharing",
                "suggested_decision": "secondary",
                "followup_conflicting_directions": True,
            }
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert "kv_sharing" in memo["secondary_variants"]
    assert "kv_sharing" not in memo["exploratory_variants"]
    assert any("keeps `kv_sharing` secondary" in line for line in memo["recommendations"])
    assert any("Do not promote `kv_sharing` beyond secondary" in line for line in memo["recommendations"])


def test_generate_final_decision_memo_keeps_secondary_when_weighted_followup_favors_current() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.0, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 120},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            },
            {
                "variant": "kv_sharing",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -0.4,
                "final_loss_delta_vs_baseline_range": 1.2,
                "mean_step_ms_ratio_vs_baseline_mean": 1.1,
                "mean_step_ms_ratio_vs_baseline_range": 0.5,
                "max_grad_norm_delta_vs_baseline_mean": 3.0,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variant": "compressed_attention",
            "lowest_kv_variant": "kv_sharing",
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.15},
            {"variant": "mhc", "mean_ratio_across_grid": 1.4, "worst_ratio_across_grid": 1.5},
            {"variant": "history_compression", "mean_ratio_across_grid": 1.1, "worst_ratio_across_grid": 1.2},
        ],
    }
    review_plan = {
        "summary": {"priority_variants": ["kv_sharing"], "resolved_mismatch_variants": []},
        "rows": [
            {
                "variant": "kv_sharing",
                "suggested_decision": "secondary",
                "followup_conflicting_directions": False,
                "followup_mixed_but_current_favored": True,
            }
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert "kv_sharing" in memo["secondary_variants"]
    assert "kv_sharing" not in memo["exploratory_variants"]
    assert any("weighted balance still favors `secondary`" in line for line in memo["recommendations"])
    assert any("weighted evidence still favors the current label" in line for line in memo["recommendations"])


def test_generate_final_decision_memo_reports_benchmark_ties_honestly() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.0, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 100},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention", "kv_sharing"],
            "best_worst_case_runtime_variant": "attention_budgeting",
            "best_worst_case_runtime_variants": ["attention_budgeting", "compressed_attention"],
            "lowest_kv_variant": "compressed_attention",
            "lowest_kv_variants": ["compressed_attention", "kv_sharing"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 0.905, "worst_ratio_across_grid": 1.005},
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, None, benchmark_matrix)
    joined = "\n".join(memo["summary_lines"] + memo["recommendations"])
    assert "tie between `compressed_attention`, `kv_sharing`" in joined
    assert "best worst-case systems-sweep direction among carry-forward candidates: tie between `compressed_attention`, `kv_sharing`" in joined


def test_generate_final_decision_memo_reports_micro_ties_honestly() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 0.91, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.90, "estimated_kv_cache_bytes": 100},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "compressed_attention",
            "lowest_kv_variants": ["compressed_attention"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.1},
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, None, benchmark_matrix)
    joined = "\n".join(memo["summary_lines"])
    assert "Best micro runtime direction: tie between `compressed_attention`, `kv_sharing`." in joined
    assert "Best micro KV-memory direction: tie between `compressed_attention`, `kv_sharing`." in joined
    assert memo["evidence"]["micro_runtime_leaders"] == ["compressed_attention", "kv_sharing"]
    assert memo["evidence"]["micro_memory_leaders"] == ["compressed_attention", "kv_sharing"]


def test_generate_final_decision_memo_marks_default_as_provisional_when_review_priority() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.0, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 0.9, "estimated_kv_cache_bytes": 120},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.5, "estimated_kv_cache_bytes": 140},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 1.1, "estimated_kv_cache_bytes": 130},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "kv_sharing",
            "lowest_kv_variants": ["kv_sharing"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.1},
        ],
    }
    review_plan = {
        "summary": {"priority_variants": ["compressed_attention"], "resolved_mismatch_variants": []},
        "rows": [
            {
                "variant": "compressed_attention",
                "priority": 2,
            }
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, review_plan, benchmark_matrix)
    assert memo["summary_lines"][0] == (
        "Default carry-forward architecture: `compressed_attention` (provisional; still flagged for follow-up review)."
    )
    assert any(
        line.startswith("Keep provisionally `compressed_attention` as the default next heavier experiment candidate")
        for line in memo["recommendations"]
    )


def test_generate_final_decision_memo_does_not_seed_secondary_from_noisy_runtime_pick() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline"},
        "variant_rows": [
            {"variant": "kv_sharing", "mean_ratio_vs_baseline_mean": 1.05, "estimated_kv_cache_bytes": 100},
            {"variant": "compressed_attention", "mean_ratio_vs_baseline_mean": 1.09, "estimated_kv_cache_bytes": 100},
            {"variant": "history_compression", "mean_ratio_vs_baseline_mean": 0.98, "estimated_kv_cache_bytes": 130},
            {"variant": "mhc", "mean_ratio_vs_baseline_mean": 1.2, "estimated_kv_cache_bytes": 140},
        ],
    }
    selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    training = {
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}],
        "winner_counts": {},
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.2,
                "mean_step_ms_ratio_vs_baseline_mean": 0.7,
                "mean_step_ms_ratio_vs_baseline_range": 0.1,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 1.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            }
        ],
    }
    benchmark_matrix = {
        "baseline": {"batch_sizes": [1], "seq_lens": [4]},
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "kv_sharing",
            "lowest_kv_variants": ["kv_sharing"],
            "grid_cell_count": 1,
        },
        "variant_summary_rows": [
            {"variant": "compressed_attention", "mean_ratio_across_grid": 0.9, "worst_ratio_across_grid": 1.0},
            {"variant": "kv_sharing", "mean_ratio_across_grid": 1.0, "worst_ratio_across_grid": 1.1},
            {"variant": "history_compression", "mean_ratio_across_grid": 1.06, "worst_ratio_across_grid": 1.42},
        ],
    }

    memo = generate_final_decision_memo(micro_report, selector, execution, training, None, benchmark_matrix)
    assert memo["secondary_variants"] == ["kv_sharing"]
    assert "history_compression" not in memo["secondary_variants"]
    assert "history_compression" in memo["exploratory_variants"]
