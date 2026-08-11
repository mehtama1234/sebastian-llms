from __future__ import annotations

from dataclasses import dataclass
import os
import statistics
from typing import Any

from .benchmark import compare_numeric_benchmarks
from .config import ModelConfig, load_config


@dataclass(slots=True)
class VariantTarget:
    label: str
    config_path: str


DEFAULT_VARIANT_TARGETS = [
    VariantTarget(label="kv_sharing", config_path="configs/micro-kv-sharing.json"),
    VariantTarget(label="attention_budgeting", config_path="configs/micro-attention-budgeting.json"),
    VariantTarget(label="per_layer_embeddings", config_path="configs/micro-ple.json"),
    VariantTarget(label="compressed_attention", config_path="configs/micro-compressed-attention.json"),
    VariantTarget(label="history_compression", config_path="configs/micro-history-compression.json"),
    VariantTarget(label="mhc", config_path="configs/micro-mhc.json"),
]

COMPRESSED_ATTENTION_MICRO_CONFIG_ENV = "ARCH_ADV_MICRO_COMPRESSED_ATTENTION_CONFIG"


def resolve_variant_target_config_path(root_dir: str, target: VariantTarget) -> str:
    if target.label == "compressed_attention":
        override = os.environ.get(COMPRESSED_ATTENTION_MICRO_CONFIG_ENV)
        if override:
            return f"{root_dir}/{override}" if not override.startswith("/") else override
    return f"{root_dir}/{target.config_path}"


def _variant_row(comparison: dict[str, Any]) -> dict[str, Any]:
    baseline_demo = comparison["demo_context"]["baseline"]["numeric_run"]
    variant_demo = comparison["demo_context"]["variant"]["numeric_run"]
    return {
        "variant": comparison["variant"]["variant"],
        "name": comparison["variant"]["name"],
        "mean_ms": comparison["variant"]["mean_ms"],
        "mean_ratio_vs_baseline": comparison["comparison"]["mean_ratio_variant_over_baseline"],
        "owner_cache_count": comparison["variant"]["owner_cache_count"],
        "owner_cache_delta": comparison["comparison"]["owner_cache_delta"],
        "estimated_flops": variant_demo["estimated_flops"],
        "estimated_flops_delta": variant_demo["estimated_flops"] - baseline_demo["estimated_flops"],
        "estimated_kv_cache_bytes": variant_demo["estimated_kv_cache_bytes"],
        "estimated_kv_cache_bytes_delta": (
            variant_demo["estimated_kv_cache_bytes"] - baseline_demo["estimated_kv_cache_bytes"]
        ),
        "estimated_kv_cache_bytes_saved": variant_demo["estimated_kv_cache_bytes_saved"],
        "estimated_kv_projection_bytes_written": variant_demo["estimated_kv_projection_bytes_written"],
    }


def _aggregate_variant_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    first = rows[0]
    mean_ratios = [row["mean_ratio_vs_baseline"] for row in rows]
    mean_mses = [row["mean_ms"] for row in rows]
    return {
        "variant": first["variant"],
        "name": first["name"],
        "report_runs": len(rows),
        "mean_ms_mean": statistics.fmean(mean_mses),
        "mean_ms_min": min(mean_mses),
        "mean_ms_max": max(mean_mses),
        "mean_ratio_vs_baseline_mean": statistics.fmean(mean_ratios),
        "mean_ratio_vs_baseline_min": min(mean_ratios),
        "mean_ratio_vs_baseline_max": max(mean_ratios),
        "mean_ratio_vs_baseline_stdev": statistics.pstdev(mean_ratios) if len(mean_ratios) > 1 else 0.0,
        "owner_cache_count": first["owner_cache_count"],
        "owner_cache_delta": first["owner_cache_delta"],
        "estimated_flops": first["estimated_flops"],
        "estimated_flops_delta": first["estimated_flops_delta"],
        "estimated_kv_cache_bytes": first["estimated_kv_cache_bytes"],
        "estimated_kv_cache_bytes_delta": first["estimated_kv_cache_bytes_delta"],
        "estimated_kv_cache_bytes_saved": first["estimated_kv_cache_bytes_saved"],
        "estimated_kv_projection_bytes_written": first["estimated_kv_projection_bytes_written"],
    }


def generate_variant_report(
    baseline: ModelConfig,
    variants: list[ModelConfig],
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
    report_runs: int = 3,
) -> dict[str, Any]:
    if report_runs <= 0:
        raise ValueError("report_runs must be positive")
    comparisons = []
    rows = []
    aggregated_rows = []
    for variant in variants:
        variant_comparisons = []
        variant_rows = []
        for run_idx in range(report_runs):
            comparison = compare_numeric_benchmarks(
                baseline,
                variant,
                batch_size=batch_size,
                seq_len=seq_len,
                seed=seed + run_idx,
                warmup_runs=warmup_runs,
                measured_runs=measured_runs,
            )
            variant_comparisons.append(comparison)
            variant_rows.append(_variant_row(comparison))
        comparisons.append({"variant": variant.variant.kind, "runs": variant_comparisons})
        rows.extend(variant_rows)
        aggregated_rows.append(_aggregate_variant_rows(variant_rows))

    ranked_by_speed = sorted(aggregated_rows, key=lambda row: row["mean_ratio_vs_baseline_mean"])
    ranked_by_flops = sorted(aggregated_rows, key=lambda row: row["estimated_flops"])
    ranked_by_kv_cache = sorted(aggregated_rows, key=lambda row: row["estimated_kv_cache_bytes"])

    return {
        "baseline": {
            "name": baseline.name,
            "variant": baseline.variant.kind,
            "batch_size": batch_size,
            "seq_len": seq_len,
            "warmup_runs": warmup_runs,
            "measured_runs": measured_runs,
            "report_runs": report_runs,
        },
        "variant_rows": aggregated_rows,
        "rankings": {
            "fastest_by_mean_ratio": [row["variant"] for row in ranked_by_speed],
            "lowest_estimated_flops": [row["variant"] for row in ranked_by_flops],
            "lowest_estimated_kv_cache_bytes": [row["variant"] for row in ranked_by_kv_cache],
        },
        "comparisons": comparisons,
        "notes": [
            "This report aggregates multiple micro-scale NumPy benchmark runs against a shared baseline.",
            "Use it to compare directional tradeoffs across variants, not to make production hardware claims.",
        ],
    }


def load_default_report_configs(root_dir: str) -> tuple[ModelConfig, list[ModelConfig]]:
    baseline = load_config(f"{root_dir}/configs/micro-baseline.json")
    variants = [load_config(resolve_variant_target_config_path(root_dir, target)) for target in DEFAULT_VARIANT_TARGETS]
    return baseline, variants
