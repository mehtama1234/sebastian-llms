from __future__ import annotations

from arch_adv_2026.long_context_followup_assessment import (
    build_long_context_followup_assessment,
    render_long_context_followup_assessment_markdown,
)


def test_build_long_context_followup_assessment_can_support_candidate() -> None:
    compare = {
        "filler_repeat_values": [64],
        "variant_buckets": [
            {
                "variant_kind": "baseline",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.995,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
            },
            {
                "variant_kind": "kv_sharing",
                "filler_repeats": 64,
                "num_cases": 4,
                "mean_proxy_pass_probability": 0.98,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
            },
        ],
    }
    assessment = build_long_context_followup_assessment(
        compare,
        variant="kv_sharing",
        current_decision="exploratory",
        candidate_decision="secondary",
    )
    assert assessment["supports_current_decision"] is False
    assert assessment["supports_candidate_decision"] is True
    markdown = render_long_context_followup_assessment_markdown(assessment)
    assert "Focused Long-Context Follow-up Assessment" in markdown
    assert "`kv_sharing`" in markdown
