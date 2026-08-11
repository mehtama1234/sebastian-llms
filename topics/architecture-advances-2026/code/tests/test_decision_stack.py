from __future__ import annotations

from arch_adv_2026.decision_stack import refresh_decision_stack


def _resolved_mismatch_stack_fixture() -> dict[str, object]:
    return {
        "micro_report": {
            "baseline": {"name": "micro-baseline", "variant": "baseline", "seq_len": 8},
            "variant_rows": [
                {
                    "variant": "kv_sharing",
                    "name": "micro-kv-sharing",
                    "mean_ratio_vs_baseline_mean": 0.86,
                    "mean_ratio_vs_baseline_stdev": 0.1,
                    "estimated_flops": 100,
                    "estimated_kv_cache_bytes": 100,
                    "estimated_kv_cache_bytes_saved": 50,
                },
                {
                    "variant": "compressed_attention",
                    "name": "micro-compressed-attention",
                    "mean_ratio_vs_baseline_mean": 0.88,
                    "mean_ratio_vs_baseline_stdev": 0.1,
                    "estimated_flops": 90,
                    "estimated_kv_cache_bytes": 100,
                    "estimated_kv_cache_bytes_saved": 0,
                },
                {
                    "variant": "mhc",
                    "name": "micro-mhc",
                    "mean_ratio_vs_baseline_mean": 1.3,
                    "mean_ratio_vs_baseline_stdev": 0.2,
                    "estimated_flops": 140,
                    "estimated_kv_cache_bytes": 140,
                    "estimated_kv_cache_bytes_saved": 0,
                },
                {
                    "variant": "history_compression",
                    "name": "micro-history-compression",
                    "mean_ratio_vs_baseline_mean": 1.2,
                    "mean_ratio_vs_baseline_stdev": 0.2,
                    "estimated_flops": 120,
                    "estimated_kv_cache_bytes": 130,
                    "estimated_kv_cache_bytes_saved": 20,
                },
                {
                    "variant": "attention_budgeting",
                    "name": "micro-attention-budgeting",
                    "mean_ratio_vs_baseline_mean": 1.35,
                    "mean_ratio_vs_baseline_stdev": 0.2,
                    "estimated_flops": 125,
                    "estimated_kv_cache_bytes": 160,
                    "estimated_kv_cache_bytes_saved": 0,
                },
                {
                    "variant": "per_layer_embeddings",
                    "name": "micro-per-layer-embeddings",
                    "mean_ratio_vs_baseline_mean": 1.23,
                    "mean_ratio_vs_baseline_stdev": 0.2,
                    "estimated_flops": 150,
                    "estimated_kv_cache_bytes": 160,
                    "estimated_kv_cache_bytes_saved": 0,
                },
            ],
        },
        "long_context_compare": {
            "filler_repeat_values": [256],
            "variant_buckets": [
                {
                    "variant_kind": "compressed_attention",
                    "filler_repeats": 256,
                    "num_cases": 4,
                    "mean_proxy_pass_probability": 0.955,
                    "proxy_pass_rate": 1.0,
                    "estimated_kv_saving_ratio_at_max_seq": 0.5,
                },
                {
                    "variant_kind": "kv_sharing",
                    "filler_repeats": 256,
                    "num_cases": 4,
                    "mean_proxy_pass_probability": 0.94,
                    "proxy_pass_rate": 0.75,
                    "estimated_kv_saving_ratio_at_max_seq": 0.5,
                },
                {
                    "variant_kind": "mhc",
                    "filler_repeats": 256,
                    "num_cases": 4,
                    "mean_proxy_pass_probability": 0.97,
                    "proxy_pass_rate": 1.0,
                    "estimated_kv_saving_ratio_at_max_seq": 0.0,
                },
                {
                    "variant_kind": "history_compression",
                    "filler_repeats": 256,
                    "num_cases": 4,
                    "mean_proxy_pass_probability": 0.93,
                    "proxy_pass_rate": 0.75,
                    "estimated_kv_saving_ratio_at_max_seq": 0.75,
                },
            ],
        },
        "benchmark_matrix": {
            "baseline": {
                "batch_sizes": [1, 2],
                "seq_lens": [4, 8, 16],
                "measured_runs": 3,
                "report_runs": 3,
            },
            "summary": {
                "best_mean_runtime_variant": "compressed_attention",
                "best_mean_runtime_variants": ["compressed_attention"],
                "best_worst_case_runtime_variant": "compressed_attention",
                "best_worst_case_runtime_variants": ["compressed_attention"],
                "lowest_kv_variant": "compressed_attention",
                "lowest_kv_variants": ["compressed_attention", "kv_sharing"],
                "grid_cell_count": 6,
            },
            "variant_summary_rows": [
                {
                    "variant": "compressed_attention",
                    "mean_ratio_across_grid": 0.797,
                    "best_ratio_across_grid": 0.72,
                    "worst_ratio_across_grid": 1.016,
                    "ratio_range_across_grid": 0.296,
                    "estimated_kv_cache_bytes": 4096,
                },
                {
                    "variant": "kv_sharing",
                    "mean_ratio_across_grid": 1.002,
                    "best_ratio_across_grid": 0.81,
                    "worst_ratio_across_grid": 1.242,
                    "ratio_range_across_grid": 0.432,
                    "estimated_kv_cache_bytes": 4096,
                },
                {
                    "variant": "mhc",
                    "mean_ratio_across_grid": 1.248,
                    "best_ratio_across_grid": 1.12,
                    "worst_ratio_across_grid": 1.399,
                    "ratio_range_across_grid": 0.279,
                    "estimated_kv_cache_bytes": 8192,
                },
                {
                    "variant": "history_compression",
                    "mean_ratio_across_grid": 1.103,
                    "best_ratio_across_grid": 0.95,
                    "worst_ratio_across_grid": 1.182,
                    "ratio_range_across_grid": 0.232,
                    "estimated_kv_cache_bytes": 5120,
                },
                {
                    "variant": "attention_budgeting",
                    "mean_ratio_across_grid": 1.024,
                    "best_ratio_across_grid": 0.92,
                    "worst_ratio_across_grid": 1.106,
                    "ratio_range_across_grid": 0.186,
                    "estimated_kv_cache_bytes": 8192,
                },
                {
                    "variant": "per_layer_embeddings",
                    "mean_ratio_across_grid": 1.424,
                    "best_ratio_across_grid": 1.20,
                    "worst_ratio_across_grid": 1.563,
                    "ratio_range_across_grid": 0.363,
                    "estimated_kv_cache_bytes": 8192,
                },
            ],
        },
        "training_matrix": {
            "seq_lens": [8, 16],
            "steps_list": [4],
            "seeds": [17],
            "rows": [{}, {}],
            "winner_counts": {
                "fastest_step_ratio": {"attention_budgeting": 1, "per_layer_embeddings": 1},
                "lowest_final_loss_delta": {"compressed_attention": 2},
                "lowest_grad_norm_delta": {"attention_budgeting": 1, "kv_sharing": 1},
            },
            "variant_trends": [
                {
                    "variant": "attention_budgeting",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -1.36,
                    "final_loss_delta_vs_baseline_range": 1.55,
                    "mean_step_ms_ratio_vs_baseline_mean": 0.60,
                    "mean_step_ms_ratio_vs_baseline_range": 0.59,
                    "max_grad_norm_delta_vs_baseline_mean": -1.64,
                    "consistent_speed_advantage": True,
                    "consistent_loss_advantage": True,
                    "fastest_step_win_rate": 0.5,
                    "lowest_final_loss_delta_win_rate": 0.0,
                },
                {
                    "variant": "compressed_attention",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -4.91,
                    "final_loss_delta_vs_baseline_range": 0.79,
                    "mean_step_ms_ratio_vs_baseline_mean": 2.19,
                    "mean_step_ms_ratio_vs_baseline_range": 1.79,
                    "max_grad_norm_delta_vs_baseline_mean": 11.99,
                    "consistent_speed_advantage": False,
                    "consistent_loss_advantage": True,
                    "fastest_step_win_rate": 0.0,
                    "lowest_final_loss_delta_win_rate": 1.0,
                },
                {
                    "variant": "history_compression",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -1.76,
                    "final_loss_delta_vs_baseline_range": 3.76,
                    "mean_step_ms_ratio_vs_baseline_mean": 2.17,
                    "mean_step_ms_ratio_vs_baseline_range": 2.72,
                    "max_grad_norm_delta_vs_baseline_mean": 9.82,
                    "consistent_speed_advantage": False,
                    "consistent_loss_advantage": False,
                    "fastest_step_win_rate": 0.0,
                    "lowest_final_loss_delta_win_rate": 0.0,
                },
                {
                    "variant": "kv_sharing",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -0.39,
                    "final_loss_delta_vs_baseline_range": 1.21,
                    "mean_step_ms_ratio_vs_baseline_mean": 3.83,
                    "mean_step_ms_ratio_vs_baseline_range": 0.80,
                    "max_grad_norm_delta_vs_baseline_mean": 0.32,
                    "consistent_speed_advantage": False,
                    "consistent_loss_advantage": False,
                    "fastest_step_win_rate": 0.0,
                    "lowest_final_loss_delta_win_rate": 0.0,
                },
                {
                    "variant": "mhc",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -3.96,
                    "final_loss_delta_vs_baseline_range": 1.20,
                    "mean_step_ms_ratio_vs_baseline_mean": 2.50,
                    "mean_step_ms_ratio_vs_baseline_range": 0.70,
                    "max_grad_norm_delta_vs_baseline_mean": 4.00,
                    "consistent_speed_advantage": False,
                    "consistent_loss_advantage": False,
                    "fastest_step_win_rate": 0.0,
                    "lowest_final_loss_delta_win_rate": 0.0,
                },
                {
                    "variant": "per_layer_embeddings",
                    "all_matrix_rows_finite": True,
                    "final_loss_delta_vs_baseline_mean": -0.20,
                    "final_loss_delta_vs_baseline_range": 0.90,
                    "mean_step_ms_ratio_vs_baseline_mean": 0.58,
                    "mean_step_ms_ratio_vs_baseline_range": 0.20,
                    "max_grad_norm_delta_vs_baseline_mean": 2.50,
                    "consistent_speed_advantage": True,
                    "consistent_loss_advantage": False,
                    "fastest_step_win_rate": 0.5,
                    "lowest_final_loss_delta_win_rate": 0.0,
                },
            ],
        },
        "seed_final_memo": {
            "date": "2026-08-09",
            "default_carry_forward_variant": "compressed_attention",
            "secondary_variants": ["kv_sharing"],
            "exploratory_variants": ["history_compression", "mhc"],
            "drop_for_now_variants": ["attention_budgeting", "per_layer_embeddings"],
        },
        "long_context_selector": {
            "selection_policy": {"minimum_proxy_quality": 0.95},
            "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
        },
        "long_context_execution": {
            "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
            "focused_compare_summary": {
                "selected_bucket": {"variant_kind": "compressed_attention"},
                "baseline_bucket": {"variant_kind": "baseline"},
                "proxy_quality_delta": -0.04,
            },
        },
        "followups": [
            {
                "assessment_kind": "training_followup",
                "variant": "attention_budgeting",
                "current_decision": "drop",
                "candidate_decision": "secondary",
                "supports_current_decision": True,
                "supports_candidate_decision": False,
            },
            {
                "assessment_kind": "training_followup",
                "variant": "kv_sharing",
                "current_decision": "secondary",
                "candidate_decision": "exploratory",
                "supports_current_decision": False,
                "supports_candidate_decision": True,
            },
            {
                "assessment_kind": "long_context_followup",
                "variant": "kv_sharing",
                "current_decision": "exploratory",
                "candidate_decision": "secondary",
                "supports_current_decision": False,
                "supports_candidate_decision": True,
            },
        ],
    }


def test_refresh_decision_stack_converges_to_followup_aware_final_state() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline", "seq_len": 8},
        "variant_rows": [
            {
                "variant": "kv_sharing",
                "name": "micro-kv-sharing",
                "mean_ratio_vs_baseline_mean": 1.1,
                "mean_ratio_vs_baseline_stdev": 0.1,
                "estimated_flops": 100,
                "estimated_kv_cache_bytes": 100,
                "estimated_kv_cache_bytes_saved": 50,
            },
            {
                "variant": "compressed_attention",
                "name": "micro-compressed-attention",
                "mean_ratio_vs_baseline_mean": 0.9,
                "mean_ratio_vs_baseline_stdev": 0.1,
                "estimated_flops": 90,
                "estimated_kv_cache_bytes": 120,
                "estimated_kv_cache_bytes_saved": 0,
            },
            {
                "variant": "mhc",
                "name": "micro-mhc",
                "mean_ratio_vs_baseline_mean": 1.3,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 140,
                "estimated_kv_cache_bytes": 140,
                "estimated_kv_cache_bytes_saved": 0,
            },
            {
                "variant": "history_compression",
                "name": "micro-history-compression",
                "mean_ratio_vs_baseline_mean": 1.2,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 120,
                "estimated_kv_cache_bytes": 130,
                "estimated_kv_cache_bytes_saved": 20,
            },
        ],
    }
    long_context_compare = {
        "filler_repeat_values": [64],
        "variant_buckets": [
            {
                "variant_kind": "compressed_attention",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.96,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
            },
            {
                "variant_kind": "kv_sharing",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.98,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
            {
                "variant_kind": "mhc",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.99,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
            },
            {
                "variant_kind": "history_compression",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.94,
                "proxy_pass_rate": 0.75,
                "estimated_kv_saving_ratio_at_max_seq": 0.75,
            },
        ],
    }
    benchmark_matrix = {
        "baseline": {
            "batch_sizes": [1, 2],
            "seq_lens": [4, 8],
            "measured_runs": 1,
            "report_runs": 2,
        },
        "variant_summary_rows": [
            {
                "variant": "compressed_attention",
                "mean_ratio_across_grid": 0.90,
                "best_ratio_across_grid": 0.80,
                "worst_ratio_across_grid": 1.00,
                "ratio_range_across_grid": 0.20,
            },
            {
                "variant": "kv_sharing",
                "mean_ratio_across_grid": 1.05,
                "best_ratio_across_grid": 0.70,
                "worst_ratio_across_grid": 1.40,
                "ratio_range_across_grid": 0.70,
            },
            {
                "variant": "mhc",
                "mean_ratio_across_grid": 1.20,
                "best_ratio_across_grid": 1.00,
                "worst_ratio_across_grid": 1.40,
                "ratio_range_across_grid": 0.40,
            },
            {
                "variant": "history_compression",
                "mean_ratio_across_grid": 1.10,
                "best_ratio_across_grid": 0.95,
                "worst_ratio_across_grid": 1.25,
                "ratio_range_across_grid": 0.30,
            },
        ],
    }
    training_matrix = {
        "seq_lens": [8, 16],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}, {}],
        "winner_counts": {
            "fastest_step_ratio": {"kv_sharing": 1, "compressed_attention": 1},
            "lowest_final_loss_delta": {"compressed_attention": 2},
            "lowest_grad_norm_delta": {"kv_sharing": 1, "attention_budgeting": 1},
        },
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.5,
                "mean_step_ms_ratio_vs_baseline_mean": 1.5,
                "mean_step_ms_ratio_vs_baseline_range": 0.5,
                "max_grad_norm_delta_vs_baseline_mean": 2.0,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 0.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            },
            {
                "variant": "kv_sharing",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -0.2,
                "final_loss_delta_vs_baseline_range": 1.0,
                "mean_step_ms_ratio_vs_baseline_mean": 1.2,
                "mean_step_ms_ratio_vs_baseline_range": 0.9,
                "max_grad_norm_delta_vs_baseline_mean": 0.3,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
        ],
    }
    seed_final_memo = {
        "date": "2026-08-09",
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": ["kv_sharing"],
        "exploratory_variants": ["mhc", "history_compression"],
        "drop_for_now_variants": [],
    }
    long_context_selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    long_context_execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    followups = [
        {
            "variant": "attention_budgeting",
            "current_decision": "drop",
            "candidate_decision": "secondary",
            "supports_current_decision": True,
            "supports_candidate_decision": False,
        },
        {
            "variant": "kv_sharing",
            "current_decision": "secondary",
            "candidate_decision": "exploratory",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
        },
    ]

    refreshed = refresh_decision_stack(
        micro_report=micro_report,
        benchmark_matrix=benchmark_matrix,
        long_context_compare=long_context_compare,
        training_matrix=training_matrix,
        seed_final_memo=seed_final_memo,
        long_context_selector=long_context_selector,
        long_context_execution=long_context_execution,
        followup_assessments=followups,
    )
    assert refreshed["final_memo"]["secondary_variants"] == []
    assert "kv_sharing" in refreshed["final_memo"]["exploratory_variants"]
    scorecard_rows = {row["variant"]: row for row in refreshed["scorecard"]["rows"]}
    assert scorecard_rows["kv_sharing"]["decision"] == "exploratory"
    assert scorecard_rows["kv_sharing"]["benchmark_worst_ratio_across_grid"] == 1.40


def test_refresh_decision_stack_propagates_review_mismatch_state_into_final_memo() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "variant": "baseline", "seq_len": 8},
        "variant_rows": [
            {
                "variant": "kv_sharing",
                "name": "micro-kv-sharing",
                "mean_ratio_vs_baseline_mean": 0.86,
                "mean_ratio_vs_baseline_stdev": 0.1,
                "estimated_flops": 100,
                "estimated_kv_cache_bytes": 100,
                "estimated_kv_cache_bytes_saved": 50,
            },
            {
                "variant": "compressed_attention",
                "name": "micro-compressed-attention",
                "mean_ratio_vs_baseline_mean": 0.88,
                "mean_ratio_vs_baseline_stdev": 0.1,
                "estimated_flops": 90,
                "estimated_kv_cache_bytes": 100,
                "estimated_kv_cache_bytes_saved": 0,
            },
            {
                "variant": "mhc",
                "name": "micro-mhc",
                "mean_ratio_vs_baseline_mean": 1.3,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 140,
                "estimated_kv_cache_bytes": 140,
                "estimated_kv_cache_bytes_saved": 0,
            },
            {
                "variant": "history_compression",
                "name": "micro-history-compression",
                "mean_ratio_vs_baseline_mean": 1.2,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 120,
                "estimated_kv_cache_bytes": 130,
                "estimated_kv_cache_bytes_saved": 20,
            },
            {
                "variant": "attention_budgeting",
                "name": "micro-attention-budgeting",
                "mean_ratio_vs_baseline_mean": 1.35,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 125,
                "estimated_kv_cache_bytes": 160,
                "estimated_kv_cache_bytes_saved": 0,
            },
            {
                "variant": "per_layer_embeddings",
                "name": "micro-per-layer-embeddings",
                "mean_ratio_vs_baseline_mean": 1.23,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 150,
                "estimated_kv_cache_bytes": 160,
                "estimated_kv_cache_bytes_saved": 0,
            },
        ],
    }
    long_context_compare = {
        "filler_repeat_values": [256],
        "variant_buckets": [
            {
                "variant_kind": "compressed_attention",
                "filler_repeats": 256,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.955,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
            {
                "variant_kind": "kv_sharing",
                "filler_repeats": 256,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.94,
                "proxy_pass_rate": 0.75,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
            {
                "variant_kind": "mhc",
                "filler_repeats": 256,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.97,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
            },
            {
                "variant_kind": "history_compression",
                "filler_repeats": 256,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.93,
                "proxy_pass_rate": 0.75,
                "estimated_kv_saving_ratio_at_max_seq": 0.75,
            },
        ],
    }
    benchmark_matrix = {
        "baseline": {
            "batch_sizes": [1, 2],
            "seq_lens": [4, 8, 16],
            "measured_runs": 3,
            "report_runs": 3,
        },
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention"],
            "best_worst_case_runtime_variant": "compressed_attention",
            "best_worst_case_runtime_variants": ["compressed_attention"],
            "lowest_kv_variant": "compressed_attention",
            "lowest_kv_variants": ["compressed_attention", "kv_sharing"],
            "grid_cell_count": 6,
        },
        "variant_summary_rows": [
            {
                "variant": "compressed_attention",
                "mean_ratio_across_grid": 0.797,
                "best_ratio_across_grid": 0.72,
                "worst_ratio_across_grid": 1.016,
                "ratio_range_across_grid": 0.296,
                "estimated_kv_cache_bytes": 4096,
            },
            {
                "variant": "kv_sharing",
                "mean_ratio_across_grid": 1.002,
                "best_ratio_across_grid": 0.81,
                "worst_ratio_across_grid": 1.242,
                "ratio_range_across_grid": 0.432,
                "estimated_kv_cache_bytes": 4096,
            },
            {
                "variant": "mhc",
                "mean_ratio_across_grid": 1.248,
                "best_ratio_across_grid": 1.12,
                "worst_ratio_across_grid": 1.399,
                "ratio_range_across_grid": 0.279,
                "estimated_kv_cache_bytes": 8192,
            },
            {
                "variant": "history_compression",
                "mean_ratio_across_grid": 1.103,
                "best_ratio_across_grid": 0.95,
                "worst_ratio_across_grid": 1.182,
                "ratio_range_across_grid": 0.232,
                "estimated_kv_cache_bytes": 5120,
            },
            {
                "variant": "attention_budgeting",
                "mean_ratio_across_grid": 1.024,
                "best_ratio_across_grid": 0.92,
                "worst_ratio_across_grid": 1.106,
                "ratio_range_across_grid": 0.186,
                "estimated_kv_cache_bytes": 8192,
            },
            {
                "variant": "per_layer_embeddings",
                "mean_ratio_across_grid": 1.424,
                "best_ratio_across_grid": 1.20,
                "worst_ratio_across_grid": 1.563,
                "ratio_range_across_grid": 0.363,
                "estimated_kv_cache_bytes": 8192,
            },
        ],
    }
    training_matrix = {
        "seq_lens": [8, 16],
        "steps_list": [4],
        "seeds": [17],
        "rows": [{}, {}],
        "winner_counts": {
            "fastest_step_ratio": {"attention_budgeting": 1, "per_layer_embeddings": 1},
            "lowest_final_loss_delta": {"compressed_attention": 2},
            "lowest_grad_norm_delta": {"attention_budgeting": 1, "kv_sharing": 1},
        },
        "variant_trends": [
            {
                "variant": "attention_budgeting",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -1.36,
                "final_loss_delta_vs_baseline_range": 1.55,
                "mean_step_ms_ratio_vs_baseline_mean": 0.60,
                "mean_step_ms_ratio_vs_baseline_range": 0.59,
                "max_grad_norm_delta_vs_baseline_mean": -1.64,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -4.91,
                "final_loss_delta_vs_baseline_range": 0.79,
                "mean_step_ms_ratio_vs_baseline_mean": 2.19,
                "mean_step_ms_ratio_vs_baseline_range": 1.79,
                "max_grad_norm_delta_vs_baseline_mean": 11.99,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": True,
                "fastest_step_win_rate": 0.0,
                "lowest_final_loss_delta_win_rate": 1.0,
            },
            {
                "variant": "history_compression",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -1.76,
                "final_loss_delta_vs_baseline_range": 3.76,
                "mean_step_ms_ratio_vs_baseline_mean": 2.17,
                "mean_step_ms_ratio_vs_baseline_range": 2.72,
                "max_grad_norm_delta_vs_baseline_mean": 9.82,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.0,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "kv_sharing",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -0.39,
                "final_loss_delta_vs_baseline_range": 1.21,
                "mean_step_ms_ratio_vs_baseline_mean": 3.83,
                "mean_step_ms_ratio_vs_baseline_range": 0.80,
                "max_grad_norm_delta_vs_baseline_mean": 0.32,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.0,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "mhc",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -3.96,
                "final_loss_delta_vs_baseline_range": 1.20,
                "mean_step_ms_ratio_vs_baseline_mean": 2.50,
                "mean_step_ms_ratio_vs_baseline_range": 0.70,
                "max_grad_norm_delta_vs_baseline_mean": 4.00,
                "consistent_speed_advantage": False,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.0,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
            {
                "variant": "per_layer_embeddings",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -0.20,
                "final_loss_delta_vs_baseline_range": 0.90,
                "mean_step_ms_ratio_vs_baseline_mean": 0.58,
                "mean_step_ms_ratio_vs_baseline_range": 0.20,
                "max_grad_norm_delta_vs_baseline_mean": 2.50,
                "consistent_speed_advantage": True,
                "consistent_loss_advantage": False,
                "fastest_step_win_rate": 0.5,
                "lowest_final_loss_delta_win_rate": 0.0,
            },
        ],
    }
    seed_final_memo = {
        "date": "2026-08-09",
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": ["kv_sharing"],
        "exploratory_variants": ["history_compression", "mhc"],
        "drop_for_now_variants": ["attention_budgeting", "per_layer_embeddings"],
    }
    long_context_selector = {
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {"quality_preserving_memory": {"variant_kind": "compressed_attention"}},
    }
    long_context_execution = {
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {"variant_kind": "compressed_attention"},
            "baseline_bucket": {"variant_kind": "baseline"},
            "proxy_quality_delta": -0.04,
        },
    }
    followups = [
        {
            "assessment_kind": "training_followup",
            "variant": "attention_budgeting",
            "current_decision": "drop",
            "candidate_decision": "secondary",
            "supports_current_decision": True,
            "supports_candidate_decision": False,
        },
        {
            "assessment_kind": "training_followup",
            "variant": "kv_sharing",
            "current_decision": "secondary",
            "candidate_decision": "exploratory",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
        },
        {
            "assessment_kind": "long_context_followup",
            "variant": "kv_sharing",
            "current_decision": "exploratory",
            "candidate_decision": "secondary",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
        },
    ]

    refreshed = refresh_decision_stack(
        micro_report=micro_report,
        benchmark_matrix=benchmark_matrix,
        long_context_compare=long_context_compare,
        training_matrix=training_matrix,
        seed_final_memo=seed_final_memo,
        long_context_selector=long_context_selector,
        long_context_execution=long_context_execution,
        followup_assessments=followups,
    )

    audit_summary = refreshed["audit"]["summary"]
    review_summary = refreshed["review_plan"]["summary"]
    memo_review_summary = refreshed["final_memo"]["evidence"]["review_summary"]

    assert review_summary["raw_mismatch_variants"] == audit_summary["mismatch_variants"]
    assert review_summary["resolved_mismatch_variants"] == audit_summary["resolved_mismatch_variants"]
    assert review_summary["unresolved_mismatch_variants"] == audit_summary["unresolved_mismatch_variants"]
    assert memo_review_summary["raw_mismatch_variants"] == review_summary["raw_mismatch_variants"]
    assert memo_review_summary["resolved_mismatch_variants"] == review_summary["resolved_mismatch_variants"]
    assert memo_review_summary["unresolved_mismatch_variants"] == review_summary["unresolved_mismatch_variants"]
    assert "kv_sharing" in memo_review_summary["priority_variants"]
    assert any(
        line == "Focused follow-up review priority variants: `kv_sharing`."
        for line in refreshed["final_memo"]["summary_lines"]
    )


def test_refresh_decision_stack_surfaces_unresolved_mismatch_in_final_memo_summary() -> None:
    fixture = _resolved_mismatch_stack_fixture()
    fixture["followups"] = []

    refreshed = refresh_decision_stack(
        micro_report=fixture["micro_report"],
        benchmark_matrix=fixture["benchmark_matrix"],
        long_context_compare=fixture["long_context_compare"],
        training_matrix=fixture["training_matrix"],
        seed_final_memo=fixture["seed_final_memo"],
        long_context_selector=fixture["long_context_selector"],
        long_context_execution=fixture["long_context_execution"],
        followup_assessments=fixture["followups"],
    )

    audit_summary = refreshed["audit"]["summary"]
    review_summary = refreshed["review_plan"]["summary"]
    memo_review_summary = refreshed["final_memo"]["evidence"]["review_summary"]

    assert audit_summary["unresolved_mismatch_variants"] == audit_summary["mismatch_variants"]
    assert review_summary["unresolved_mismatch_variants"] == audit_summary["unresolved_mismatch_variants"]
    assert memo_review_summary["unresolved_mismatch_variants"] == review_summary["unresolved_mismatch_variants"]
    assert any(
        line.startswith("Active unresolved decision mismatches still needing review: ")
        for line in refreshed["final_memo"]["summary_lines"]
    )
