from __future__ import annotations

from arch_adv_2026.concept_review_plan import (
    build_concept_review_plan,
    render_concept_review_plan_markdown,
)


def test_build_concept_review_plan_prioritizes_mismatches() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "benchmark_worst_ratio_across_grid": 1.05,
                "benchmark_ratio_range_across_grid": 0.2,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
                "training_speed_ratio_mean": 0.6,
            },
            {
                "variant": "history_compression",
                "decision": "exploratory",
                "benchmark_worst_ratio_across_grid": 1.35,
                "benchmark_ratio_range_across_grid": 0.6,
                "long_context_proxy_quality_at_longest": 0.93,
                "micro_runtime_ratio_mean": 1.10,
                "micro_estimated_kv_cache_bytes": 5120,
                "training_final_loss_delta_mean": -1.7,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": False,
                "training_speed_ratio_mean": 2.1,
            },
        ],
    }
    audit = {
        "summary": {"mismatch_variants": ["attention_budgeting"]},
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision_matches": False,
                "suggested_decision": "secondary",
            },
            {
                "variant": "history_compression",
                "decision_matches": True,
                "suggested_decision": "exploratory",
            },
        ],
    }

    plan = build_concept_review_plan(scorecard, audit)
    assert plan["summary"]["priority_variants"] == ["attention_budgeting"]
    assert plan["summary"]["raw_mismatch_variants"] == ["attention_budgeting"]
    assert plan["summary"]["unresolved_mismatch_variants"] == []
    first = plan["rows"][0]
    assert first["variant"] == "attention_budgeting"
    assert first["priority"] == 3
    assert any("carry-forward decision" in action for action in first["next_actions"])
    assert any("scaling-sensitive" in action for action in plan["rows"][1]["next_actions"])
    markdown = render_concept_review_plan_markdown(plan)
    assert "Architecture Concept Review Plan" in markdown
    assert "Raw decision mismatches from the audit" in markdown
    assert "Active unresolved mismatches needing review" not in markdown
    assert "`attention_budgeting`" in markdown


def test_build_concept_review_plan_downgrades_mismatch_when_followup_supports_current() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "benchmark_worst_ratio_across_grid": 1.05,
                "benchmark_ratio_range_across_grid": 0.2,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
                "training_speed_ratio_mean": 0.6,
            },
        ],
    }
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision_matches": False,
                "suggested_decision": "secondary",
            },
        ],
    }
    followup = [
        {
            "variant": "attention_budgeting",
            "supports_current_decision": True,
            "supports_candidate_decision": False,
        }
    ]

    plan = build_concept_review_plan(scorecard, audit, followup_assessments=followup)
    assert plan["summary"]["resolved_mismatch_variants"] == ["attention_budgeting"]
    assert plan["summary"]["unresolved_mismatch_variants"] == []
    row = plan["rows"][0]
    assert row["priority"] == 1
    assert any("Focused follow-up evidence already supports keeping" in action for action in row["next_actions"])
    markdown = render_concept_review_plan_markdown(plan)
    assert "Resolved mismatches with follow-up support for the current label" in markdown
    assert "Active unresolved mismatches needing review" not in markdown


def test_build_concept_review_plan_surfaces_unresolved_mismatch_summary() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "benchmark_worst_ratio_across_grid": 1.05,
                "benchmark_ratio_range_across_grid": 0.2,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
                "training_speed_ratio_mean": 0.6,
            },
        ],
    }
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        },
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision_matches": False,
                "suggested_decision": "secondary",
            },
        ],
    }

    plan = build_concept_review_plan(scorecard, audit)
    assert plan["summary"]["unresolved_mismatch_variants"] == ["attention_budgeting"]
    markdown = render_concept_review_plan_markdown(plan)
    assert "Active unresolved mismatches needing review" in markdown


def test_build_concept_review_plan_prioritizes_keep_label_when_followup_supports_downgrade() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "kv_sharing",
                "decision": "secondary",
                "benchmark_worst_ratio_across_grid": 1.35,
                "benchmark_ratio_range_across_grid": 0.7,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.12,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -0.4,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": False,
                "training_speed_ratio_mean": 3.8,
            },
        ],
    }
    audit = {
        "summary": {"mismatch_variants": []},
        "rows": [
            {
                "variant": "kv_sharing",
                "decision_matches": True,
                "suggested_decision": "secondary",
            },
        ],
    }
    followup = [
        {
            "variant": "kv_sharing",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
            "candidate_decision": "exploratory",
        }
    ]

    plan = build_concept_review_plan(scorecard, audit, followup_assessments=followup)
    row = plan["rows"][0]
    assert row["priority"] == 3
    assert any("supports moving" in action for action in row["next_actions"])


def test_build_concept_review_plan_marks_conflicting_followup_directions_high_priority() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "kv_sharing",
                "decision": "exploratory",
                "benchmark_worst_ratio_across_grid": 1.35,
                "benchmark_ratio_range_across_grid": 0.7,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.12,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -0.4,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": False,
                "training_speed_ratio_mean": 3.8,
            },
        ],
    }
    audit = {
        "summary": {"mismatch_variants": []},
        "rows": [
            {
                "variant": "kv_sharing",
                "decision_matches": True,
                "suggested_decision": "exploratory",
            },
        ],
    }
    followup = [
        {
            "variant": "kv_sharing",
            "supports_current_decision": True,
            "supports_candidate_decision": False,
            "current_decision": "exploratory",
            "candidate_decision": "secondary",
        },
        {
            "variant": "kv_sharing",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
            "current_decision": "exploratory",
            "candidate_decision": "secondary",
        },
    ]

    plan = build_concept_review_plan(scorecard, audit, followup_assessments=followup)
    row = plan["rows"][0]
    assert row["priority"] == 3
    assert row["followup_conflicting_directions"] is True
    assert row["suggested_decision"] == "exploratory"
    assert any("Focused follow-up evidence conflicts" in action for action in row["next_actions"])


def test_build_concept_review_plan_uses_weighted_followup_to_keep_current_label() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "kv_sharing",
                "decision": "secondary",
                "benchmark_worst_ratio_across_grid": 1.18,
                "benchmark_ratio_range_across_grid": 0.4,
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -0.3,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": False,
                "training_speed_ratio_mean": 3.8,
            },
        ],
    }
    audit = {
        "summary": {"mismatch_variants": []},
        "rows": [
            {
                "variant": "kv_sharing",
                "decision_matches": True,
                "suggested_decision": "secondary",
            },
        ],
    }
    followup = [
        {
            "assessment_kind": "training_followup",
            "variant": "kv_sharing",
            "current_decision": "secondary",
            "candidate_decision": "exploratory",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
        },
        {
            "assessment_kind": "long_context_followup",
            "variant": "kv_sharing",
            "current_decision": "exploratory",
            "candidate_decision": "secondary",
            "supports_current_decision": False,
            "supports_candidate_decision": True,
        },
    ]

    plan = build_concept_review_plan(scorecard, audit, followup_assessments=followup)
    row = plan["rows"][0]
    assert row["suggested_decision"] == "secondary"
    assert row["followup_conflicting_directions"] is False
    assert row["followup_mixed_but_current_favored"] is True
    assert row["priority"] == 2
    assert row["followup_label_scores"]["secondary"] == 2.0
    assert row["followup_label_scores"]["exploratory"] == 1.0
    assert any("stronger weighted signal still favors keeping" in action for action in row["next_actions"])
