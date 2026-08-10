from __future__ import annotations

from arch_adv_2026.compressed_attention_training_stress_assessment import (
    build_compressed_attention_training_stress_assessment,
    render_compressed_attention_training_stress_assessment_markdown,
)


def test_build_compressed_attention_training_stress_assessment_detects_reproduced_failure() -> None:
    matrix = {
        "batch_sizes": [2, 4],
        "seq_lens": [8],
        "steps_list": [4, 8],
        "seeds": [23, 29],
        "report_runs": 2,
        "rows": [
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 4,
                "seed": 23,
                "report": {"variant_rows": [{"final_loss_delta_vs_baseline_mean": 5.0, "mean_step_ms_ratio_vs_baseline_mean": 1.2}]},
            },
            {
                "batch_size": 4,
                "seq_len": 8,
                "steps": 8,
                "seed": 29,
                "report": {"variant_rows": [{"final_loss_delta_vs_baseline_mean": 2.0, "mean_step_ms_ratio_vs_baseline_mean": 0.8}]},
            },
        ],
    }
    assessment = build_compressed_attention_training_stress_assessment(matrix)
    assert assessment["reproduces_failure"] is True
    assert assessment["worst_loss_row"]["loss_delta"] == 5.0
    markdown = render_compressed_attention_training_stress_assessment_markdown(assessment)
    assert "Compressed Attention Training Stress Assessment" in markdown


def test_build_compressed_attention_training_stress_assessment_can_show_non_reproduced_failure() -> None:
    matrix = {
        "batch_sizes": [2],
        "seq_lens": [8],
        "steps_list": [4],
        "seeds": [23, 29],
        "report_runs": 2,
        "rows": [
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 4,
                "seed": 23,
                "report": {"variant_rows": [{"final_loss_delta_vs_baseline_mean": -1.0, "mean_step_ms_ratio_vs_baseline_mean": 0.7}]},
            },
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 4,
                "seed": 29,
                "report": {"variant_rows": [{"final_loss_delta_vs_baseline_mean": -0.5, "mean_step_ms_ratio_vs_baseline_mean": 0.8}]},
            },
        ],
    }
    assessment = build_compressed_attention_training_stress_assessment(matrix)
    assert assessment["reproduces_failure"] is False
