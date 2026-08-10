from __future__ import annotations

from arch_adv_2026.compressed_attention_promotion_memo import (
    generate_compressed_attention_promotion_memo,
    render_compressed_attention_promotion_memo_markdown,
)


def test_generate_compressed_attention_promotion_memo_defer() -> None:
    assessment = {
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "recommendation": "defer",
        "gates": {
            "long_context_pass": True,
            "training_pass": False,
            "benchmark_pass": True,
        },
        "long_context": {
            "quality_delta_vs_baseline": -0.04,
            "kv_cache_saving_ratio_vs_baseline": 0.5,
        },
        "training": {
            "final_loss_delta_vs_baseline_mean": 0.5,
            "final_loss_delta_vs_baseline_range": 12.7,
        },
        "benchmark": {
            "mean_ratio_across_grid": 0.87,
            "worst_ratio_across_grid": 1.05,
        },
        "signals": ["systems sweep stays near or better than baseline on both mean and worst-case runtime"],
        "risks": ["training follow-up does not yet show a consistent loss advantage across the sampled grid"],
    }
    stress_assessment = {
        "reproduces_failure": True,
        "speed_instability": True,
    }
    speed_tail_assessment = {
        "batch_summaries": [
            {"batch_size": 2, "slow_row_fraction": 0.8, "mean_speed_ratio": 1.3, "worst_speed_ratio": 1.9},
            {"batch_size": 4, "slow_row_fraction": 0.3, "mean_speed_ratio": 2.1, "worst_speed_ratio": 8.8},
        ],
        "dominant_steps": {"steps": 8},
    }

    memo = generate_compressed_attention_promotion_memo(assessment, stress_assessment, speed_tail_assessment)
    assert memo["recommendation"] == "defer"
    assert any("stress rerun reproduces it" in line for line in memo["recommendations"])
    assert any("broad slowdown slice" in line for line in memo["recommendations"])
    assert any("Short-context speed tail:" in line for line in memo["summary_lines"])
    markdown = render_compressed_attention_promotion_memo_markdown(memo)
    assert "Compressed attention promotion memo" in markdown
    assert "`defer`" in markdown


def test_generate_compressed_attention_promotion_memo_promote() -> None:
    assessment = {
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "recommendation": "promote",
        "gates": {
            "long_context_pass": True,
            "training_pass": True,
            "benchmark_pass": True,
        },
        "long_context": {
            "quality_delta_vs_baseline": -0.02,
            "kv_cache_saving_ratio_vs_baseline": 0.5,
        },
        "training": {
            "final_loss_delta_vs_baseline_mean": -1.5,
            "final_loss_delta_vs_baseline_range": 0.7,
        },
        "benchmark": {
            "mean_ratio_across_grid": 0.82,
            "worst_ratio_across_grid": 1.02,
        },
        "signals": [],
        "risks": [],
    }

    memo = generate_compressed_attention_promotion_memo(assessment)
    assert any("Promote `compressed_attention`" in line for line in memo["recommendations"])
