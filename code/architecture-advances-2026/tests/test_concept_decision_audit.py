from __future__ import annotations

from arch_adv_2026.concept_decision_audit import (
    build_concept_decision_audit,
    render_concept_decision_audit_markdown,
)


def test_build_concept_decision_audit_flags_mismatches() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "compressed_attention",
                "decision": "default",
                "long_context_proxy_quality_at_longest": 0.96,
                "micro_runtime_ratio_mean": 0.9,
                "benchmark_mean_ratio_across_grid": 0.92,
                "benchmark_median_ratio_across_grid": 0.95,
                "benchmark_worst_ratio_across_grid": 1.05,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -4.0,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": False,
            },
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "benchmark_mean_ratio_across_grid": 0.94,
                "benchmark_median_ratio_across_grid": 0.98,
                "benchmark_worst_ratio_across_grid": 1.44,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
            },
            {
                "variant": "per_layer_embeddings",
                "decision": "drop",
                "long_context_proxy_quality_at_longest": 0.99,
                "micro_runtime_ratio_mean": 1.2,
                "benchmark_mean_ratio_across_grid": 1.55,
                "benchmark_median_ratio_across_grid": 1.50,
                "benchmark_worst_ratio_across_grid": 1.99,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": 0.0,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": True,
            },
        ],
    }

    audit = build_concept_decision_audit(scorecard)
    assert audit["summary"]["variant_count"] == 3
    assert "attention_budgeting" in audit["summary"]["mismatch_variants"]
    mismatched = {row["variant"]: row for row in audit["rows"]}
    assert mismatched["compressed_attention"]["suggested_decision"] == "default"
    assert mismatched["attention_budgeting"]["suggested_decision"] == "secondary"
    assert mismatched["per_layer_embeddings"]["suggested_decision"] == "drop"
    markdown = render_concept_decision_audit_markdown(audit)
    assert "Architecture Concept Decision Audit" in markdown
    assert "Decision Matrix" in markdown
    assert "`attention_budgeting`" in markdown


def test_build_concept_decision_audit_keeps_near_parity_default_when_training_is_strong() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "compressed_attention",
                "decision": "default",
                "long_context_proxy_quality_at_longest": 0.955,
                "micro_runtime_ratio_mean": 0.87,
                "benchmark_mean_ratio_across_grid": 1.001,
                "benchmark_median_ratio_across_grid": 0.89,
                "benchmark_worst_ratio_across_grid": 1.73,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -4.9,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": False,
            }
        ],
    }

    audit = build_concept_decision_audit(scorecard)
    assert audit["summary"]["mismatch_count"] == 0
    assert audit["rows"][0]["suggested_decision"] == "default"


def test_build_concept_decision_audit_marks_mismatch_resolved_by_followup() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "benchmark_mean_ratio_across_grid": 0.94,
                "benchmark_median_ratio_across_grid": 0.98,
                "benchmark_worst_ratio_across_grid": 1.44,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
            }
        ],
    }
    followup = [
        {
            "assessment_kind": "training_followup",
            "variant": "attention_budgeting",
            "current_decision": "drop",
            "candidate_decision": "secondary",
            "supports_current_decision": True,
            "supports_candidate_decision": False,
        }
    ]

    audit = build_concept_decision_audit(scorecard, followup_assessments=followup)
    assert audit["summary"]["mismatch_count"] == 1
    assert audit["summary"]["resolved_mismatch_count"] == 1
    assert audit["summary"]["unresolved_mismatch_count"] == 0
    assert audit["summary"]["resolved_mismatch_variants"] == ["attention_budgeting"]
    assert audit["rows"][0]["resolved_by_followup"] is True
    markdown = render_concept_decision_audit_markdown(audit)
    assert "Mismatches resolved by focused follow-up" in markdown
    assert "Follow-up Resolved" in markdown


def test_build_concept_decision_audit_keeps_systems_expensive_non_memory_variant_exploratory() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "mhc",
                "decision": "exploratory",
                "long_context_proxy_quality_at_longest": 0.999,
                "micro_runtime_ratio_mean": 0.92,
                "benchmark_mean_ratio_across_grid": 1.12,
                "benchmark_median_ratio_across_grid": 1.13,
                "benchmark_worst_ratio_across_grid": 1.86,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -3.96,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": False,
            }
        ],
    }

    audit = build_concept_decision_audit(scorecard)
    assert audit["summary"]["mismatch_count"] == 0
    assert audit["rows"][0]["suggested_decision"] == "exploratory"


def test_build_concept_decision_audit_keeps_memory_variant_secondary_without_consistent_loss() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "kv_sharing",
                "decision": "secondary",
                "long_context_proxy_quality_at_longest": 0.975,
                "micro_runtime_ratio_mean": 1.05,
                "benchmark_mean_ratio_across_grid": 1.01,
                "benchmark_median_ratio_across_grid": 1.02,
                "benchmark_worst_ratio_across_grid": 1.14,
                "micro_estimated_kv_cache_bytes": 4096,
                "training_final_loss_delta_mean": -0.3,
                "training_consistent_loss_advantage": False,
                "training_consistent_speed_advantage": False,
            }
        ],
    }

    audit = build_concept_decision_audit(scorecard)
    assert audit["summary"]["mismatch_count"] == 0
    assert audit["rows"][0]["suggested_decision"] == "secondary"


def test_build_concept_decision_audit_keeps_speed_consistent_variant_secondary() -> None:
    scorecard = {
        "date": "2026-08-09",
        "rows": [
            {
                "variant": "attention_budgeting",
                "decision": "drop",
                "long_context_proxy_quality_at_longest": 0.98,
                "micro_runtime_ratio_mean": 1.05,
                "benchmark_mean_ratio_across_grid": 0.94,
                "benchmark_median_ratio_across_grid": 0.98,
                "benchmark_worst_ratio_across_grid": 1.14,
                "micro_estimated_kv_cache_bytes": 8192,
                "training_final_loss_delta_mean": -1.3,
                "training_consistent_loss_advantage": True,
                "training_consistent_speed_advantage": True,
            }
        ],
    }

    audit = build_concept_decision_audit(scorecard)
    assert audit["summary"]["mismatch_count"] == 1
    assert audit["rows"][0]["suggested_decision"] == "secondary"
