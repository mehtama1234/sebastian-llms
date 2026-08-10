from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any

from .config import ModelConfig, load_config
from .long_context_eval import (
    LongContextCase,
    _filler_paragraph,
    build_sweep_cases,
    write_eval_artifact,
)
from .summary import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare baseline and architecture variants on the same synthetic long-context cases using a proxy retrieval model."
    )
    parser.add_argument("--baseline-config", required=True)
    parser.add_argument("--variant-configs", nargs="+", required=True)
    parser.add_argument("--filler-repeats", default="32,64,128,256")
    parser.add_argument("--cases-per-length", type=int, default=2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--sweep-runs", type=int, default=2)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def _tokens_per_filler_section() -> int:
    return max(1, len(_filler_paragraph(0)) // 4)


def _quality_factor(config: ModelConfig, summary: dict[str, Any]) -> float:
    kind = config.variant.kind
    if kind == "baseline":
        return 1.0
    if kind == "kv_sharing":
        owner_ratio = summary["kv_sharing"]["owner_layer_count"] / config.n_layers
        return 1.0 - 0.04 * (1.0 - owner_ratio)
    if kind == "attention_budgeting":
        avg_q_heads = statistics.fmean(summary["shape"]["per_layer_query_heads"])
        ratio = avg_q_heads / config.n_query_heads if config.n_query_heads else 1.0
        return 1.0 - 0.06 * (1.0 - ratio)
    if kind == "compressed_attention":
        ratio = summary["shape"]["effective_attn_head_dim"] / config.head_dim if config.head_dim else 1.0
        return 1.0 - 0.08 * (1.0 - ratio)
    if kind == "per_layer_embeddings":
        return 1.02
    if kind == "mhc":
        return 1.01
    if kind == "history_compression":
        return 0.98
    return 1.0


def _history_retention_factor(config: ModelConfig, case: LongContextCase) -> float:
    if config.variant.kind != "history_compression":
        return 1.0
    metadata = case.metadata or {}
    filler_repeats = int(metadata.get("filler_repeats", 0))
    insertion_section = int(metadata.get("insertion_section", 0))
    distance_sections = max(0, filler_repeats - insertion_section)
    recent_window_tokens = config.variant.recent_window_size or config.max_seq_len
    recent_window_sections = max(1, recent_window_tokens // _tokens_per_filler_section())
    if distance_sections <= recent_window_sections:
        return 1.0
    excess_sections = distance_sections - recent_window_sections
    compression_ratio = config.variant.history_compression_ratio or 1
    effective_old_sections = math.ceil(excess_sections / compression_ratio)
    retention_fraction = (recent_window_sections + effective_old_sections) / (
        recent_window_sections + excess_sections
    )
    return max(0.35, 1.0 - (1.0 - retention_fraction) * 0.6)


def proxy_retrieval_probability(config: ModelConfig, case: LongContextCase) -> float:
    summary = build_summary(config)
    base_probability = 0.995
    quality_factor = _quality_factor(config, summary)
    retention_factor = _history_retention_factor(config, case)
    probability = base_probability * quality_factor * retention_factor
    return min(0.999, max(0.05, probability))


def _variant_case_row(
    *,
    config: ModelConfig,
    summary: dict[str, Any],
    case: LongContextCase,
    run_index: int,
    run_seed: int,
) -> dict[str, Any]:
    proxy_probability = proxy_retrieval_probability(config, case)
    metadata = case.metadata or {}
    filler_repeats = int(metadata.get("filler_repeats", -1))
    insertion_section = int(metadata.get("insertion_section", -1))
    distance_sections = max(0, filler_repeats - insertion_section) if filler_repeats >= 0 and insertion_section >= 0 else 0
    return {
        "variant": config.name,
        "variant_kind": config.variant.kind,
        "case": case.name,
        "task_type": case.task_type,
        "run_index": run_index,
        "run_seed": run_seed,
        "filler_repeats": filler_repeats,
        "insertion_section": insertion_section,
        "distance_from_end_sections": distance_sections,
        "proxy_pass_probability": proxy_probability,
        "proxy_passed": proxy_probability >= 0.85,
        "estimated_kv_cache_bytes_at_max_seq": summary["kv_cache"]["variant_bytes_at_max_seq"],
        "estimated_kv_saving_ratio_at_max_seq": summary["kv_cache"]["saving_ratio"],
        "estimated_total_params": summary["params"]["total"],
    }


def _group_variant_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault((row["variant_kind"], row["filler_repeats"]), []).append(row)

    buckets: list[dict[str, Any]] = []
    for (variant_kind, filler_repeats), bucket_rows in sorted(grouped.items(), key=lambda item: (item[0][1], item[0][0])):
        probabilities = [row["proxy_pass_probability"] for row in bucket_rows]
        passed = [1.0 if row["proxy_passed"] else 0.0 for row in bucket_rows]
        buckets.append(
            {
                "variant_kind": variant_kind,
                "filler_repeats": filler_repeats,
                "num_cases": len(bucket_rows),
                "mean_proxy_pass_probability": statistics.fmean(probabilities),
                "proxy_pass_rate": statistics.fmean(passed),
                "min_proxy_pass_probability": min(probabilities),
                "max_proxy_pass_probability": max(probabilities),
                "estimated_kv_cache_bytes_at_max_seq": bucket_rows[0]["estimated_kv_cache_bytes_at_max_seq"],
                "estimated_kv_saving_ratio_at_max_seq": bucket_rows[0]["estimated_kv_saving_ratio_at_max_seq"],
                "estimated_total_params": bucket_rows[0]["estimated_total_params"],
            }
        )
    return buckets


def build_variant_long_context_compare(
    *,
    baseline_config_path: str | Path,
    variant_config_paths: list[str | Path],
    filler_repeat_values: list[int],
    cases_per_length: int = 2,
    seed: int = 0,
    sweep_runs: int = 2,
) -> dict[str, Any]:
    if sweep_runs <= 0:
        raise ValueError("sweep_runs must be positive")

    baseline_config = load_config(baseline_config_path)
    configs = [baseline_config] + [load_config(path) for path in variant_config_paths]
    summaries = {config.name: build_summary(config) for config in configs}
    all_rows: list[dict[str, Any]] = []

    for run_index in range(sweep_runs):
        run_seed = seed + run_index
        cases = build_sweep_cases(
            filler_repeat_values=filler_repeat_values,
            cases_per_length=cases_per_length,
            seed=run_seed,
        )
        for config in configs:
            summary = summaries[config.name]
            for case in cases:
                all_rows.append(
                    _variant_case_row(
                        config=config,
                        summary=summary,
                        case=case,
                        run_index=run_index,
                        run_seed=run_seed,
                    )
                )

    buckets = _group_variant_rows(all_rows)
    longest_filler = max(filler_repeat_values)
    longest_rows = [row for row in buckets if row["filler_repeats"] == longest_filler]
    ranked_by_quality = sorted(longest_rows, key=lambda row: row["mean_proxy_pass_probability"], reverse=True)
    ranked_by_memory = sorted(longest_rows, key=lambda row: row["estimated_kv_cache_bytes_at_max_seq"])

    return {
        "baseline_config": str(baseline_config_path),
        "variant_configs": [str(path) for path in variant_config_paths],
        "filler_repeat_values": filler_repeat_values,
        "cases_per_length": cases_per_length,
        "seed": seed,
        "sweep_runs": sweep_runs,
        "case_result_count": len(all_rows),
        "variant_case_results": all_rows,
        "variant_buckets": buckets,
        "rankings": {
            "best_proxy_quality_at_longest_context": [row["variant_kind"] for row in ranked_by_quality],
            "lowest_kv_at_longest_context": [row["variant_kind"] for row in ranked_by_memory],
        },
        "notes": [
            "This is a same-cases proxy comparison surface, not a real trained-model quality benchmark.",
            "It keeps the synthetic retrieval cases fixed across variants and uses architecture-aware proxy scoring.",
            "Use it to compare directional quality-vs-memory tradeoffs before investing in heavier training or finetuning work.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    filler_repeat_values = [int(value.strip()) for value in args.filler_repeats.split(",") if value.strip()]
    if not filler_repeat_values:
        raise SystemExit("at least one filler repeat value is required")
    result = build_variant_long_context_compare(
        baseline_config_path=args.baseline_config,
        variant_config_paths=args.variant_configs,
        filler_repeat_values=filler_repeat_values,
        cases_per_length=args.cases_per_length,
        seed=args.seed,
        sweep_runs=args.sweep_runs,
    )
    if args.artifact:
        path = write_eval_artifact(result, args.artifact)
        print(f"Wrote long-context variant comparison artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
