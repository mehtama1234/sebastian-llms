from __future__ import annotations

import statistics
from typing import Any

from .config import ModelConfig, load_config
from .report import DEFAULT_VARIANT_TARGETS, resolve_variant_target_config_path
from .training_benchmark import compare_torch_training_benchmarks


def _training_row(comparison: dict[str, Any]) -> dict[str, Any]:
    variant = comparison["variant"]
    variant_summary = variant["summary"]
    baseline_summary = comparison["baseline"]["summary"]
    cmp = comparison["comparison"]
    return {
        "variant": variant["variant"],
        "name": variant["name"],
        "final_loss": variant_summary["final_loss"],
        "initial_loss": variant_summary["initial_loss"],
        "loss_improvement_ratio": variant_summary["loss_improvement_ratio"],
        "mean_step_ms": variant_summary["mean_step_ms"],
        "max_grad_norm_before_clip": variant_summary["max_grad_norm_before_clip"],
        "nonfinite_step_count": variant_summary["nonfinite_step_count"],
        "all_steps_finite": variant_summary["all_steps_finite"],
        "owner_cache_count": variant_summary["owner_cache_count"],
        "final_loss_delta_vs_baseline": cmp["final_loss_delta"],
        "loss_improvement_ratio_delta_vs_baseline": cmp["loss_improvement_ratio_delta"],
        "mean_step_ms_ratio_vs_baseline": cmp["mean_step_ms_ratio_variant_over_baseline"],
        "max_grad_norm_delta_vs_baseline": cmp["max_grad_norm_delta"],
        "baseline_final_loss": baseline_summary["final_loss"],
    }


def _aggregate_training_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    final_loss_deltas = [row["final_loss_delta_vs_baseline"] for row in rows]
    step_ratios = [row["mean_step_ms_ratio_vs_baseline"] for row in rows]
    grad_deltas = [row["max_grad_norm_delta_vs_baseline"] for row in rows]
    loss_improvement_deltas = [row["loss_improvement_ratio_delta_vs_baseline"] for row in rows]
    return {
        "variant": first["variant"],
        "name": first["name"],
        "report_runs": len(rows),
        "final_loss_delta_vs_baseline_mean": statistics.fmean(final_loss_deltas),
        "final_loss_delta_vs_baseline_min": min(final_loss_deltas),
        "final_loss_delta_vs_baseline_max": max(final_loss_deltas),
        "loss_improvement_ratio_delta_vs_baseline_mean": statistics.fmean(loss_improvement_deltas),
        "mean_step_ms_ratio_vs_baseline_mean": statistics.fmean(step_ratios),
        "mean_step_ms_ratio_vs_baseline_min": min(step_ratios),
        "mean_step_ms_ratio_vs_baseline_max": max(step_ratios),
        "max_grad_norm_delta_vs_baseline_mean": statistics.fmean(grad_deltas),
        "all_runs_finite": all(row["all_steps_finite"] for row in rows),
        "total_nonfinite_step_count": sum(row["nonfinite_step_count"] for row in rows),
        "owner_cache_count": first["owner_cache_count"],
    }


def generate_training_report(
    baseline: ModelConfig,
    variants: list[ModelConfig],
    *,
    batch_size: int = 4,
    seq_len: int = 8,
    steps: int = 4,
    lr: float = 1e-2,
    seed: int = 0,
    clip_grad_norm: float | None = 1.0,
    report_runs: int = 1,
) -> dict[str, Any]:
    if report_runs <= 0:
        raise ValueError("report_runs must be positive")
    comparisons = []
    aggregated_rows = []
    for variant in variants:
        variant_runs = []
        variant_rows = []
        for run_idx in range(report_runs):
            comparison = compare_torch_training_benchmarks(
                baseline,
                variant,
                batch_size=batch_size,
                seq_len=seq_len,
                steps=steps,
                lr=lr,
                seed=seed + run_idx,
                clip_grad_norm=clip_grad_norm,
            )
            variant_runs.append(comparison)
            variant_rows.append(_training_row(comparison))
        comparisons.append({"variant": variant.variant.kind, "runs": variant_runs})
        aggregated_rows.append(_aggregate_training_rows(variant_rows))

    ranked_by_final_loss = sorted(aggregated_rows, key=lambda row: row["final_loss_delta_vs_baseline_mean"])
    ranked_by_speed = sorted(aggregated_rows, key=lambda row: row["mean_step_ms_ratio_vs_baseline_mean"])
    ranked_by_grad_stability = sorted(aggregated_rows, key=lambda row: row["max_grad_norm_delta_vs_baseline_mean"])

    return {
        "baseline": {
            "name": baseline.name,
            "variant": baseline.variant.kind,
            "batch_size": batch_size,
            "seq_len": seq_len,
            "steps": steps,
            "lr": lr,
            "seed": seed,
            "clip_grad_norm": clip_grad_norm,
            "report_runs": report_runs,
        },
        "variant_rows": aggregated_rows,
        "rankings": {
            "lowest_final_loss_delta": [row["variant"] for row in ranked_by_final_loss],
            "fastest_step_ratio": [row["variant"] for row in ranked_by_speed],
            "lowest_grad_norm_delta": [row["variant"] for row in ranked_by_grad_stability],
        },
        "comparisons": comparisons,
        "notes": [
            "This report aggregates tiny Torch training-stability proxy runs against a shared micro baseline.",
            "Use it to compare optimization directionality across variants under the same synthetic task.",
        ],
    }


def _filter_variant_targets(variant_names: list[str] | None) -> list[Any]:
    if not variant_names:
        return DEFAULT_VARIANT_TARGETS
    requested = set(variant_names)
    filtered = [target for target in DEFAULT_VARIANT_TARGETS if target.label in requested]
    missing = sorted(requested - {target.label for target in filtered})
    if missing:
        raise ValueError(f"unknown variant labels: {', '.join(missing)}")
    return filtered


def load_default_training_report_configs(
    root_dir: str,
    *,
    variant_names: list[str] | None = None,
) -> tuple[ModelConfig, list[ModelConfig]]:
    baseline = load_config(f"{root_dir}/configs/micro-baseline.json")
    selected_targets = _filter_variant_targets(variant_names)
    variants = [load_config(resolve_variant_target_config_path(root_dir, target)) for target in selected_targets]
    return baseline, variants
