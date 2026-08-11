from __future__ import annotations

from arch_adv_2026.compressed_attention_remediation_plan import (
    build_compressed_attention_remediation_plan,
    render_compressed_attention_remediation_plan_markdown,
)


def test_build_compressed_attention_remediation_plan_prioritizes_training_and_speed() -> None:
    promotion = {
        "recommendation": "defer",
        "gates": {
            "long_context_pass": True,
            "training_pass": False,
            "benchmark_pass": True,
        },
        "benchmark": {"batch_sizes": [1, 2], "seq_lens": [4, 8]},
    }
    stress = {
        "worst_loss_row": {"batch_size": 2, "seq_len": 8, "steps": 4, "seed": 31},
        "slowest_row": {"batch_size": 4, "seq_len": 8, "steps": 8, "seed": 31},
    }
    speed_tail = {
        "batch_summaries": [
            {"batch_size": 2, "slow_row_fraction": 0.8, "mean_speed_ratio": 1.3, "worst_speed_ratio": 1.9},
            {"batch_size": 4, "slow_row_fraction": 0.3, "mean_speed_ratio": 2.1, "worst_speed_ratio": 8.8},
        ],
        "dominant_steps": {"steps": 8},
    }
    plan = build_compressed_attention_remediation_plan(promotion, stress, speed_tail)
    assert plan["steps"][0]["priority"] == 1
    assert any(step["title"].startswith("Reduce broad short-context slowdown") for step in plan["steps"])
    markdown = render_compressed_attention_remediation_plan_markdown(plan)
    assert "Compressed Attention Remediation Plan" in markdown
