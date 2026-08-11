from __future__ import annotations

from arch_adv_2026.compressed_attention_remediation_execute import (
    render_compressed_attention_remediation_execution_markdown,
)


def test_render_compressed_attention_remediation_execution_markdown() -> None:
    execution = {
        "headline": "Compressed Attention Remediation Execution",
        "date": "2026-08-09",
        "execution_steps": [
            {
                "priority": 1,
                "title": "Stabilize short-context training loss",
                "target_slice": {"batch_size": 2, "seq_len": 8, "steps": 4, "seed": 31},
                "variant_row": {
                    "final_loss_delta_vs_baseline_mean": 1.2,
                    "mean_step_ms_ratio_vs_baseline_mean": 0.9,
                    "all_runs_finite": True,
                },
                "success_checks": {
                    "loss_nonpositive": False,
                    "speed_at_or_below_baseline": True,
                    "finite_runs": True,
                },
            }
        ],
    }
    markdown = render_compressed_attention_remediation_execution_markdown(execution)
    assert "Compressed Attention Remediation Execution" in markdown
    assert "loss delta `1.200`" in markdown
