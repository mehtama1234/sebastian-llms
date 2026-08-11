from __future__ import annotations

from arch_adv_2026.compressed_attention_promotion_assessment import (
    build_compressed_attention_promotion_assessment,
    render_compressed_attention_promotion_assessment_markdown,
)


def test_compressed_attention_promotion_assessment_can_promote() -> None:
    training = {
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -2.5,
                "final_loss_delta_vs_baseline_range": 0.8,
                "mean_step_ms_ratio_vs_baseline_mean": 0.95,
                "mean_step_ms_ratio_vs_baseline_range": 0.2,
                "consistent_loss_advantage": True,
                "consistent_speed_advantage": False,
            }
        ]
    }
    benchmark = {
        "variant_summary_rows": [
            {
                "variant": "compressed_attention",
                "mean_ratio_across_grid": 0.92,
                "worst_ratio_across_grid": 1.05,
                "estimated_kv_cache_bytes": 4096,
            }
        ]
    }
    execution = {
        "selected_variant_kind": "compressed_attention",
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.96,
                "proxy_pass_rate": 1.0,
            },
            "baseline_bucket": {
                "variant_kind": "baseline",
                "mean_proxy_pass_probability": 0.995,
                "proxy_pass_rate": 1.0,
            },
        },
    }

    assessment = build_compressed_attention_promotion_assessment(training, benchmark, execution)
    assert assessment["recommendation"] == "promote"
    assert assessment["gates"]["long_context_pass"] is True
    assert assessment["gates"]["training_pass"] is True
    assert assessment["gates"]["benchmark_pass"] is True
    markdown = render_compressed_attention_promotion_assessment_markdown(assessment)
    assert "Compressed Attention Promotion Assessment" in markdown
    assert "`promote`" in markdown


def test_compressed_attention_promotion_assessment_can_defer() -> None:
    training = {
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": -0.1,
                "final_loss_delta_vs_baseline_range": 2.0,
                "mean_step_ms_ratio_vs_baseline_mean": 1.1,
                "mean_step_ms_ratio_vs_baseline_range": 0.4,
                "consistent_loss_advantage": False,
                "consistent_speed_advantage": False,
            }
        ]
    }
    benchmark = {
        "variant_summary_rows": [
            {
                "variant": "compressed_attention",
                "mean_ratio_across_grid": 1.02,
                "worst_ratio_across_grid": 1.18,
                "estimated_kv_cache_bytes": 4096,
            }
        ]
    }
    execution = {
        "selected_variant_kind": "compressed_attention",
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.94,
                "proxy_pass_rate": 1.0,
            },
            "baseline_bucket": {
                "variant_kind": "baseline",
                "mean_proxy_pass_probability": 0.995,
                "proxy_pass_rate": 1.0,
            },
        },
    }

    assessment = build_compressed_attention_promotion_assessment(training, benchmark, execution)
    assert assessment["recommendation"] == "defer"
    assert assessment["gates"]["training_pass"] is False
    assert assessment["gates"]["benchmark_pass"] is False
    assert assessment["gates"]["long_context_pass"] is False
    assert any("training follow-up does not yet show a consistent loss advantage" in risk for risk in assessment["risks"])
