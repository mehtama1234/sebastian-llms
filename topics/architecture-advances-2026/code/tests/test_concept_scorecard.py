from __future__ import annotations

from arch_adv_2026.concept_scorecard import (
    build_concept_scorecard,
    render_concept_scorecard_markdown,
)


def test_build_concept_scorecard_combines_all_surfaces() -> None:
    micro_report = {
        "baseline": {"name": "micro-baseline", "seq_len": 8},
        "variant_rows": [
            {
                "variant": "compressed_attention",
                "name": "micro-compressed-attention",
                "mean_ratio_vs_baseline_mean": 0.9,
                "mean_ratio_vs_baseline_stdev": 0.1,
                "estimated_flops": 100,
                "estimated_kv_cache_bytes": 200,
                "estimated_kv_cache_bytes_saved": 50,
            },
            {
                "variant": "kv_sharing",
                "name": "micro-kv-sharing",
                "mean_ratio_vs_baseline_mean": 1.1,
                "mean_ratio_vs_baseline_stdev": 0.05,
                "estimated_flops": 110,
                "estimated_kv_cache_bytes": 150,
                "estimated_kv_cache_bytes_saved": 100,
            },
            {
                "variant": "mhc",
                "name": "micro-mhc",
                "mean_ratio_vs_baseline_mean": 1.3,
                "mean_ratio_vs_baseline_stdev": 0.2,
                "estimated_flops": 140,
                "estimated_kv_cache_bytes": 240,
                "estimated_kv_cache_bytes_saved": 0,
            },
        ],
    }
    long_context_compare = {
        "filler_repeat_values": [32, 64],
        "variant_buckets": [
            {
                "variant_kind": "compressed_attention",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.96,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
            {
                "variant_kind": "kv_sharing",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.94,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
            {
                "variant_kind": "mhc",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.95,
                "proxy_pass_rate": 1.0,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
            },
        ],
    }
    training_matrix = {
        "seq_lens": [8, 16],
        "steps_list": [4],
        "seeds": [17],
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "mean_step_ms_ratio_vs_baseline_mean": 2.2,
                "mean_step_ms_ratio_vs_baseline_range": 1.8,
                "consistent_speed_advantage": False,
                "fastest_step_win_rate": 0.0,
                "final_loss_delta_vs_baseline_mean": -4.9,
                "final_loss_delta_vs_baseline_range": 0.8,
                "consistent_loss_advantage": True,
                "lowest_final_loss_delta_win_rate": 1.0,
                "all_matrix_rows_finite": True,
            },
            {
                "variant": "kv_sharing",
                "mean_step_ms_ratio_vs_baseline_mean": 3.8,
                "mean_step_ms_ratio_vs_baseline_range": 0.8,
                "consistent_speed_advantage": False,
                "fastest_step_win_rate": 0.0,
                "final_loss_delta_vs_baseline_mean": -0.4,
                "final_loss_delta_vs_baseline_range": 1.2,
                "consistent_loss_advantage": False,
                "lowest_final_loss_delta_win_rate": 0.0,
                "all_matrix_rows_finite": True,
            },
            {
                "variant": "mhc",
                "mean_step_ms_ratio_vs_baseline_mean": 1.2,
                "mean_step_ms_ratio_vs_baseline_range": 0.7,
                "consistent_speed_advantage": False,
                "fastest_step_win_rate": 0.0,
                "final_loss_delta_vs_baseline_mean": -4.0,
                "final_loss_delta_vs_baseline_range": 0.6,
                "consistent_loss_advantage": True,
                "lowest_final_loss_delta_win_rate": 0.0,
                "all_matrix_rows_finite": True,
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
                "mean_ratio_across_grid": 0.92,
                "median_ratio_across_grid": 0.90,
                "best_ratio_across_grid": 0.80,
                "worst_ratio_across_grid": 1.05,
                "ratio_range_across_grid": 0.25,
            },
            {
                "variant": "kv_sharing",
                "mean_ratio_across_grid": 0.98,
                "median_ratio_across_grid": 0.95,
                "best_ratio_across_grid": 0.70,
                "worst_ratio_across_grid": 1.30,
                "ratio_range_across_grid": 0.60,
            },
            {
                "variant": "mhc",
                "mean_ratio_across_grid": 1.30,
                "median_ratio_across_grid": 1.25,
                "best_ratio_across_grid": 0.95,
                "worst_ratio_across_grid": 1.55,
                "ratio_range_across_grid": 0.60,
            },
        ],
    }
    final_memo = {
        "date": "2026-08-09",
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": ["kv_sharing"],
        "exploratory_variants": ["mhc"],
        "drop_for_now_variants": [],
    }

    scorecard = build_concept_scorecard(
        micro_report,
        long_context_compare,
        training_matrix,
        final_memo,
        benchmark_matrix,
    )
    assert scorecard["rows"][0]["variant"] == "compressed_attention"
    assert scorecard["rows"][0]["decision"] == "default"
    assert scorecard["rows"][0]["benchmark_median_ratio_across_grid"] == 0.90
    assert scorecard["rows"][1]["benchmark_worst_ratio_across_grid"] == 1.30
    assert scorecard["rows"][1]["decision"] == "secondary"
    assert scorecard["rows"][2]["decision"] == "exploratory"
    markdown = render_concept_scorecard_markdown(scorecard)
    assert "Architecture Concept Scorecard" in markdown
    assert "Concept Matrix" in markdown
    assert "`compressed_attention`" in markdown
    assert "Training matrix coverage" in markdown
    assert "Benchmark matrix coverage" in markdown
