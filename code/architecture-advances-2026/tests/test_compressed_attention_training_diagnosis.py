from __future__ import annotations

from arch_adv_2026.compressed_attention_training_diagnosis import (
    build_compressed_attention_training_diagnosis,
    render_compressed_attention_training_diagnosis_markdown,
)


def test_build_compressed_attention_training_diagnosis_summarizes_slices() -> None:
    matrix = {
        "rows": [
            {
                "batch_size": 2,
                "seq_len": 8,
                "steps": 4,
                "seed": 17,
                "report": {
                    "variant_rows": [
                        {
                            "variant": "compressed_attention",
                            "final_loss_delta_vs_baseline_mean": 5.0,
                            "mean_step_ms_ratio_vs_baseline_mean": 0.6,
                            "all_runs_finite": True,
                        }
                    ]
                },
            },
            {
                "batch_size": 4,
                "seq_len": 16,
                "steps": 8,
                "seed": 23,
                "report": {
                    "variant_rows": [
                        {
                            "variant": "compressed_attention",
                            "final_loss_delta_vs_baseline_mean": -1.0,
                            "mean_step_ms_ratio_vs_baseline_mean": 1.4,
                            "all_runs_finite": True,
                        }
                    ]
                },
            },
        ]
    }
    diagnosis = build_compressed_attention_training_diagnosis(matrix)
    assert diagnosis["row_count"] == 2
    assert diagnosis["batch_size_summaries"][0]["batch_size"] == 2
    assert diagnosis["worst_loss_rows"][0]["final_loss_delta_vs_baseline_mean"] == 5.0
    assert diagnosis["slowest_rows"][0]["mean_step_ms_ratio_vs_baseline_mean"] == 1.4
    markdown = render_compressed_attention_training_diagnosis_markdown(diagnosis)
    assert "Compressed Attention Training Diagnosis" in markdown
    assert "Worst Loss Rows" in markdown
