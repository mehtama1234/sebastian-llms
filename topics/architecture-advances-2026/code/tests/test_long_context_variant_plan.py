from __future__ import annotations

import json
from pathlib import Path

from arch_adv_2026.long_context_variant_plan import (
    QWEN3_COMPRESSED_ATTENTION_CONFIG_ENV,
    EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
    EXECUTION_MODE_SUMMARY_ONLY,
    build_variant_run_plan,
    resolve_execution_artifact_path,
    resolve_plan_artifact_path,
)


def test_build_variant_run_plan_uses_selected_proxy_recommendation(tmp_path: Path) -> None:
    compare_artifact = {
        "baseline_config": str(tmp_path / "configs" / "qwen3-baseline.json"),
        "variant_configs": [
            str(tmp_path / "configs" / "qwen3-compressed-attention.json"),
            str(tmp_path / "configs" / "qwen3-mhc.json"),
        ],
        "filler_repeat_values": [32, 64, 128, 256],
        "cases_per_length": 2,
        "seed": 17,
        "sweep_runs": 2,
        "variant_buckets": [
            {
                "variant_kind": "baseline",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.995,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_total_params": 2000,
            },
            {
                "variant_kind": "compressed_attention",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.955,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_total_params": 1500,
            },
        ],
    }
    compare_artifact_path = tmp_path / "compare.json"
    compare_artifact_path.write_text(json.dumps(compare_artifact), encoding="utf-8")
    selector = {
        "baseline_config": compare_artifact["baseline_config"],
        "variant_configs": compare_artifact["variant_configs"],
        "source_variant_compare_artifact": str(compare_artifact_path),
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {
            "quality": {"variant_kind": "mhc"},
            "memory": {"variant_kind": "compressed_attention"},
            "quality_preserving_memory": {"variant_kind": "compressed_attention"},
            "balanced": {"variant_kind": "compressed_attention"},
        },
    }
    selector_path = tmp_path / "selector.json"
    selector_path.write_text(json.dumps(selector), encoding="utf-8")

    plan = build_variant_run_plan(
        selector,
        selector_artifact_path=selector_path,
        compare_artifact_path=compare_artifact_path,
        objective="quality_preserving_memory",
        config_family="qwen3",
        root_dir=tmp_path,
    )

    assert plan["workflow"] == "long_context_variant_proxy"
    assert plan["objective"] == "quality_preserving_memory"
    assert plan["selected_variant_kind"] == "compressed_attention"
    assert plan["selected_config_path"].endswith("qwen3-compressed-attention.json")
    assert plan["baseline_config_path"].endswith("qwen3-baseline.json")
    assert plan["source_compare_artifact_exists"] is True
    assert plan["focused_compare_params"]["filler_repeat_values"] == [32, 64, 128, 256]
    assert plan["planned_plan_artifact_path"].endswith(
        "artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-plan.json"
    )
    assert plan["planned_execution_artifact_path"].endswith(
        "artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-execution.json"
    )
    assert len(plan["suggested_commands"]) == 2


def test_build_variant_run_plan_supports_summary_only_mode_without_compare_artifact(tmp_path: Path) -> None:
    selector = {
        "baseline_config": str(tmp_path / "configs" / "qwen3-baseline.json"),
        "variant_configs": [str(tmp_path / "configs" / "qwen3-mhc.json")],
        "source_variant_compare_artifact": "unknown",
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {
            "quality": {"variant_kind": "mhc"},
            "memory": {"variant_kind": "mhc"},
            "quality_preserving_memory": {"variant_kind": "mhc"},
            "balanced": {"variant_kind": "mhc"},
        },
    }
    selector_path = tmp_path / "selector.json"
    selector_path.write_text(json.dumps(selector), encoding="utf-8")

    plan = build_variant_run_plan(
        selector,
        selector_artifact_path=selector_path,
        compare_artifact_path=None,
        objective="quality",
        config_family="qwen3",
        root_dir=tmp_path,
        execution_mode=EXECUTION_MODE_SUMMARY_ONLY,
    )

    assert plan["execution_mode"] == EXECUTION_MODE_SUMMARY_ONLY
    assert plan["source_compare_artifact_exists"] is False
    assert plan["focused_compare_params"] is None
    assert len(plan["suggested_commands"]) == 1


def test_variant_plan_and_execution_artifact_paths_use_mode_suffix_only_when_needed(tmp_path: Path) -> None:
    assert resolve_plan_artifact_path(
        root_dir=tmp_path,
        config_family="qwen3",
        objective="quality",
        execution_mode=EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
    ) == (tmp_path / "artifacts" / "plans" / "qwen3-quality-variant-proxy-plan.json")
    assert resolve_plan_artifact_path(
        root_dir=tmp_path,
        config_family="qwen3",
        objective="quality",
        execution_mode=EXECUTION_MODE_SUMMARY_ONLY,
    ) == (tmp_path / "artifacts" / "plans" / "qwen3-quality-summary_only-variant-proxy-plan.json")
    assert resolve_execution_artifact_path(
        root_dir=tmp_path,
        config_family="qwen3",
        objective="quality",
        execution_mode=EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
    ) == (tmp_path / "artifacts" / "plans" / "qwen3-quality-variant-proxy-execution.json")


def test_build_variant_run_plan_honors_qwen3_compressed_attention_override(tmp_path: Path, monkeypatch) -> None:
    compare_artifact = {
        "baseline_config": str(tmp_path / "configs" / "qwen3-baseline.json"),
        "variant_configs": [str(tmp_path / "configs" / "qwen3-compressed-attention.json")],
        "filler_repeat_values": [32],
        "cases_per_length": 1,
        "seed": 17,
        "sweep_runs": 1,
        "variant_buckets": [
            {
                "variant_kind": "baseline",
                "filler_repeats": 32,
                "mean_proxy_pass_probability": 0.99,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_total_params": 2000,
            },
            {
                "variant_kind": "compressed_attention",
                "filler_repeats": 32,
                "mean_proxy_pass_probability": 0.95,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_total_params": 1500,
            },
        ],
    }
    compare_artifact_path = tmp_path / "compare.json"
    compare_artifact_path.write_text(json.dumps(compare_artifact), encoding="utf-8")
    selector = {
        "baseline_config": compare_artifact["baseline_config"],
        "variant_configs": compare_artifact["variant_configs"],
        "source_variant_compare_artifact": str(compare_artifact_path),
        "selection_policy": {"minimum_proxy_quality": 0.95},
        "recommendations": {
            "quality": {"variant_kind": "compressed_attention"},
            "memory": {"variant_kind": "compressed_attention"},
            "quality_preserving_memory": {"variant_kind": "compressed_attention"},
            "balanced": {"variant_kind": "compressed_attention"},
        },
    }
    selector_path = tmp_path / "selector.json"
    selector_path.write_text(json.dumps(selector), encoding="utf-8")
    monkeypatch.setenv(QWEN3_COMPRESSED_ATTENTION_CONFIG_ENV, "configs/qwen3-compressed-attention-d12.json")
    plan = build_variant_run_plan(
        selector,
        selector_artifact_path=selector_path,
        compare_artifact_path=compare_artifact_path,
        objective="quality",
        config_family="qwen3",
        root_dir=tmp_path,
    )
    assert plan["selected_config_path"].endswith("configs/qwen3-compressed-attention-d12.json")
