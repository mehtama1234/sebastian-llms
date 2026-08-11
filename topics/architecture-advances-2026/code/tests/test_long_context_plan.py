from __future__ import annotations

from pathlib import Path

from arch_adv_2026.long_context_plan import (
    BENCHMARK_MODE_PROXY_NUMERIC,
    BENCHMARK_MODE_TORCH_PROXY,
    build_run_plan,
    resolve_config_path,
    resolve_plan_artifact_path,
)


def test_resolve_config_path_supports_qwen3_variant_names(tmp_path: Path) -> None:
    root_dir = tmp_path
    assert resolve_config_path(root_dir=root_dir, config_family="qwen3", variant_kind="kv_sharing") == (
        root_dir / "configs" / "qwen3-kv-sharing.json"
    )
    assert resolve_config_path(
        root_dir=root_dir,
        config_family="qwen3",
        variant_kind="per_layer_embeddings",
    ) == (root_dir / "configs" / "qwen3-ple.json")


def test_build_run_plan_uses_selected_objective_recommendation(tmp_path: Path) -> None:
    selector = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "selection_policy": {
            "minimum_reference_pass_rate": 0.5,
            "fallback_to_all_rows_if_no_bucket_meets_threshold": True,
            "used_fallback_rows": False,
            "acceptable_row_count": 4,
            "total_row_count": 8,
        },
        "recommendations": {
            "memory": {
                "variant_kind": "kv_sharing",
                "filler_repeats": 12,
                "reference_mean_pass_rate": 1.0,
                "projected_kv_cache_bytes": 25718784.0,
            },
            "speed": {
                "variant_kind": "compressed_attention",
                "filler_repeats": 12,
                "reference_mean_pass_rate": 1.0,
                "projected_elapsed_ms": 22079.28,
            },
            "balanced": {
                "variant_kind": "compressed_attention",
                "filler_repeats": 12,
                "reference_mean_pass_rate": 1.0,
                "flops_ratio_vs_baseline": 0.799,
            },
        },
    }
    plan = build_run_plan(
        selector,
        objective="speed",
        config_family="qwen3",
        root_dir=tmp_path,
    )
    assert plan["objective"] == "speed"
    assert plan["selected_variant_kind"] == "compressed_attention"
    assert plan["selected_config_path"].endswith("configs/qwen3-compressed-attention.json")
    assert plan["baseline_config_path"].endswith("configs/qwen3-baseline.json")
    assert plan["planned_benchmark_artifact_path"].endswith(
        "artifacts/benchmarks/qwen3-baseline-vs-compressed_attention-proxy_numeric.json"
    )
    assert plan["planned_plan_artifact_path"].endswith("artifacts/plans/qwen3-speed-run-plan.json")
    assert plan["benchmark_mode"] == BENCHMARK_MODE_PROXY_NUMERIC
    assert plan["benchmark_params"]["config_family"] == "micro"
    assert plan["benchmark_params"]["seq_len"] == 2
    assert plan["benchmark_params"]["measured_runs"] == 1
    assert len(plan["suggested_commands"]) == 2
    assert "compressed-attention" in plan["selected_config_path"]


def test_build_run_plan_accepts_torch_proxy_mode(tmp_path: Path) -> None:
    selector = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "selection_policy": {
            "minimum_reference_pass_rate": 0.5,
            "fallback_to_all_rows_if_no_bucket_meets_threshold": True,
            "used_fallback_rows": False,
            "acceptable_row_count": 4,
            "total_row_count": 8,
        },
        "recommendations": {
            "memory": {"variant_kind": "kv_sharing"},
            "speed": {"variant_kind": "compressed_attention"},
            "balanced": {"variant_kind": "compressed_attention"},
        },
    }
    plan = build_run_plan(
        selector,
        objective="balanced",
        config_family="qwen3",
        root_dir=tmp_path,
        benchmark_mode=BENCHMARK_MODE_TORCH_PROXY,
    )
    assert plan["benchmark_mode"] == BENCHMARK_MODE_TORCH_PROXY
    assert plan["planned_benchmark_artifact_path"].endswith(
        "artifacts/benchmarks/qwen3-baseline-vs-compressed_attention-torch_proxy.json"
    )
    assert plan["planned_plan_artifact_path"].endswith("artifacts/plans/qwen3-balanced-torch_proxy-run-plan.json")
    assert plan["benchmark_params"]["config_family"] == "micro"


def test_resolve_plan_artifact_path_uses_mode_suffix_only_for_non_default_modes(tmp_path: Path) -> None:
    assert resolve_plan_artifact_path(
        root_dir=tmp_path,
        config_family="qwen3",
        objective="balanced",
        benchmark_mode=BENCHMARK_MODE_PROXY_NUMERIC,
    ) == (tmp_path / "artifacts" / "plans" / "qwen3-balanced-run-plan.json")
    assert resolve_plan_artifact_path(
        root_dir=tmp_path,
        config_family="qwen3",
        objective="balanced",
        benchmark_mode=BENCHMARK_MODE_TORCH_PROXY,
    ) == (tmp_path / "artifacts" / "plans" / "qwen3-balanced-torch_proxy-run-plan.json")
