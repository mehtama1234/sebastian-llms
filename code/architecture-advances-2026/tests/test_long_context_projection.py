from __future__ import annotations

from pathlib import Path

from arch_adv_2026.long_context_projection import build_projection, render_projection_markdown


ROOT = Path(__file__).resolve().parents[1]


def test_build_projection_contains_variant_rows() -> None:
    sweep_artifact = {
        "model_id": "Qwen/Qwen3-0.6B",
        "sweep": {
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "mean_pass_rate": 0.5,
                    "mean_elapsed_ms": 100.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                }
            ]
        },
    }
    projection = build_projection(
        sweep_artifact,
        ROOT / "configs" / "micro-baseline.json",
        [
            ROOT / "configs" / "micro-kv-sharing.json",
            ROOT / "configs" / "micro-compressed-attention.json",
        ],
    )
    assert len(projection["projection_rows"]) == 2
    kv_row = projection["projection_rows"][0]
    assert "projected_kv_cache_bytes" in kv_row
    assert "flops_ratio_vs_baseline" in kv_row
    assert "projected_elapsed_ms" in kv_row


def test_render_projection_markdown_has_table() -> None:
    projection = {
        "projection_rows": [
            {
                "filler_repeats": 8,
                "reference_mean_pass_rate": 0.5,
                "variant_kind": "kv_sharing",
                "kv_ratio_vs_baseline": 0.5,
                "flops_ratio_vs_baseline": 0.9,
                "projected_kv_cache_bytes": 1000,
                "projected_kv_saving_ratio": 0.5,
                "projected_elapsed_ms": 90.0,
                "owner_layer_count": 2,
                "effective_attn_head_dim": 16,
            }
        ],
        "notes": ["note a"],
    }
    markdown = render_projection_markdown(projection)
    assert "# Long-Context Variant Projection" in markdown
    assert "Projected Buckets" in markdown
    assert "kv_sharing" in markdown
    assert "FLOPs Ratio vs Baseline" in markdown
