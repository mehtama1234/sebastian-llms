from __future__ import annotations

from arch_adv_2026.training_followup_assessment import (
    build_training_followup_assessment,
    render_training_followup_assessment_markdown,
)


def test_build_training_followup_assessment_prefers_current_drop_label() -> None:
    matrix = {
        "variant_trends": [
            {
                "variant": "attention_budgeting",
                "final_loss_delta_vs_baseline_mean": 0.4,
                "final_loss_delta_vs_baseline_range": 6.8,
                "mean_step_ms_ratio_vs_baseline_mean": 1.1,
                "mean_step_ms_ratio_vs_baseline_range": 1.2,
                "consistent_loss_advantage": False,
                "consistent_speed_advantage": False,
                "all_matrix_rows_finite": True,
            }
        ]
    }
    assessment = build_training_followup_assessment(
        matrix,
        current_decision="drop",
        candidate_decision="secondary",
    )
    assert assessment["supports_current_decision"] is True
    assert assessment["supports_candidate_decision"] is False
    markdown = render_training_followup_assessment_markdown(assessment)
    assert "Focused Training Follow-up Assessment" in markdown
    assert "`attention_budgeting`" in markdown


def test_build_training_followup_assessment_can_support_downgrade_candidate() -> None:
    matrix = {
        "variant_trends": [
            {
                "variant": "kv_sharing",
                "final_loss_delta_vs_baseline_mean": 0.3,
                "final_loss_delta_vs_baseline_range": 0.0,
                "mean_step_ms_ratio_vs_baseline_mean": 1.2,
                "mean_step_ms_ratio_vs_baseline_range": 0.0,
                "consistent_loss_advantage": False,
                "consistent_speed_advantage": False,
                "all_matrix_rows_finite": True,
            }
        ]
    }
    assessment = build_training_followup_assessment(
        matrix,
        current_decision="secondary",
        candidate_decision="exploratory",
    )
    assert assessment["supports_current_decision"] is False
    assert assessment["supports_candidate_decision"] is True
