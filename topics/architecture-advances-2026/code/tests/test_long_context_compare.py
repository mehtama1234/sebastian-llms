from __future__ import annotations

from arch_adv_2026.long_context_compare import (
    build_combined_rows,
    build_recommendation_summary,
    build_selector_artifact,
    render_combined_markdown,
)


def test_build_combined_rows_joins_by_filler_repeats() -> None:
    sweep = {
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.5,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                }
            ]
        }
    }
    projection = {
        "projection_rows": [
            {
                "filler_repeats": 8,
                "variant_kind": "kv_sharing",
                "projected_kv_cache_bytes": 500.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_elapsed_ms": 90.0,
                "projected_elapsed_ms_delta": -10.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            }
        ]
    }
    rows = build_combined_rows(sweep, projection)
    assert len(rows) == 1
    assert rows[0]["reference_mean_pass_rate"] == 0.5
    assert rows[0]["variant_kind"] == "kv_sharing"


def test_render_combined_markdown_contains_table() -> None:
    sweep = {
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.5,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                }
            ]
        }
    }
    projection = {
        "projection_rows": [
            {
                "filler_repeats": 8,
                "variant_kind": "kv_sharing",
                "projected_kv_cache_bytes": 500.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_elapsed_ms": 90.0,
                "projected_elapsed_ms_delta": -10.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            }
        ]
    }
    markdown = render_combined_markdown(sweep, projection)
    assert "# Long-Context Comparison" in markdown
    assert "## Recommendation Layer" in markdown
    assert "## Combined Table" in markdown
    assert "Ref Pass Rate" in markdown


def test_recommendation_summary_filters_by_min_pass_rate() -> None:
    sweep = {
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.0,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                },
                {
                    "filler_repeats": 12,
                    "mean_pass_rate": 1.0,
                    "mean_elapsed_ms": 150.0,
                    "mean_estimated_kv_cache_bytes": 2000.0,
                },
            ]
        }
    }
    projection = {
        "projection_rows": [
            {
                "filler_repeats": 8,
                "variant_kind": "compressed_attention",
                "projected_kv_cache_bytes": 100.0,
                "projected_kv_saving_ratio": 0.9,
                "flops_ratio_vs_baseline": 0.7,
                "projected_elapsed_ms": 70.0,
                "projected_elapsed_ms_delta": -30.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            },
            {
                "filler_repeats": 12,
                "variant_kind": "kv_sharing",
                "projected_kv_cache_bytes": 1000.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_elapsed_ms": 135.0,
                "projected_elapsed_ms_delta": -15.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            },
        ]
    }
    summary = build_recommendation_summary(sweep, projection, min_pass_rate=0.5)
    assert len(summary["acceptable_rows"]) == 1
    assert summary["lowest_kv_projection"]["filler_repeats"] == 12
    assert summary["fastest_projection"]["filler_repeats"] == 12


def test_recommendation_summary_falls_back_when_no_rows_meet_threshold() -> None:
    sweep = {
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.2,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                }
            ]
        }
    }
    projection = {
        "projection_rows": [
            {
                "filler_repeats": 8,
                "variant_kind": "kv_sharing",
                "projected_kv_cache_bytes": 500.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_elapsed_ms": 90.0,
                "projected_elapsed_ms_delta": -10.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            }
        ]
    }
    summary = build_recommendation_summary(sweep, projection, min_pass_rate=0.5)
    assert summary["used_fallback_rows"] is True
    markdown = render_combined_markdown(sweep, projection, min_pass_rate=0.5)
    assert "fell back to all rows" in markdown


def test_build_selector_artifact_contains_ranked_recommendations() -> None:
    sweep = {
        "model_id": "Qwen/Qwen3-0.6B",
        "source_artifact": "real_sweep.json",
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.0,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                },
                {
                    "filler_repeats": 12,
                    "mean_pass_rate": 1.0,
                    "mean_elapsed_ms": 150.0,
                    "mean_estimated_kv_cache_bytes": 2000.0,
                },
            ]
        },
    }
    projection = {
        "reference_sweep_artifact": "projected_costs.json",
        "projection_rows": [
            {
                "filler_repeats": 12,
                "variant_kind": "kv_sharing",
                "projected_kv_cache_bytes": 1000.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_elapsed_ms": 135.0,
                "projected_elapsed_ms_delta": -15.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            },
            {
                "filler_repeats": 12,
                "variant_kind": "compressed_attention",
                "projected_kv_cache_bytes": 1000.0,
                "projected_kv_saving_ratio": 0.5,
                "flops_ratio_vs_baseline": 0.8,
                "projected_elapsed_ms": 120.0,
                "projected_elapsed_ms_delta": -30.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 8,
            },
        ],
    }
    selector = build_selector_artifact(sweep, projection, min_pass_rate=0.5)
    assert selector["reference_model_id"] == "Qwen/Qwen3-0.6B"
    assert selector["selection_policy"]["acceptable_row_count"] == 2
    assert selector["recommendations"]["memory"]["variant_kind"] == "kv_sharing"
    assert selector["recommendations"]["speed"]["variant_kind"] == "compressed_attention"
    assert selector["recommendations"]["balanced"]["variant_kind"] == "compressed_attention"
