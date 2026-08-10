from __future__ import annotations

from arch_adv_2026.compressed_attention_speed_tail_assessment import (
    build_compressed_attention_speed_tail_assessment,
    render_compressed_attention_speed_tail_assessment_markdown,
)


def test_build_compressed_attention_speed_tail_assessment_summarizes_dominant_slices() -> None:
    matrix = {
        "rows": [
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 4,
                "seed": 23,
                "report": {"variant_rows": [{"mean_step_ms_ratio_vs_baseline_mean": 1.8, "final_loss_delta_vs_baseline_mean": 5.0}]},
            },
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 8,
                "seed": 29,
                "report": {"variant_rows": [{"mean_step_ms_ratio_vs_baseline_mean": 1.4, "final_loss_delta_vs_baseline_mean": 2.0}]},
            },
            {
                "batch_size": 4,
                "seq_len": 8,
                "steps": 8,
                "seed": 31,
                "report": {"variant_rows": [{"mean_step_ms_ratio_vs_baseline_mean": 0.8, "final_loss_delta_vs_baseline_mean": 1.0}]},
            },
        ]
    }
    assessment = build_compressed_attention_speed_tail_assessment(matrix)
    assert assessment["slow_row_fraction"] == 2 / 3
    assert assessment["dominant_batch"]["batch_size"] == 2
    markdown = render_compressed_attention_speed_tail_assessment_markdown(assessment)
    assert "Compressed Attention Short-Context Speed-Tail Assessment" in markdown
