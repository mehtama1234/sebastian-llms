from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .report import generate_variant_report, load_default_report_configs


RATIO_TIE_TOLERANCE = 0.01


def _leader_variants(
    rows: list[dict[str, Any]],
    *,
    key: str,
    tolerance: float = RATIO_TIE_TOLERANCE,
) -> list[str]:
    best_value = min(row[key] for row in rows)
    leaders = [row["variant"] for row in rows if row[key] <= best_value + tolerance]
    return sorted(leaders)


def _lowest_kv_variants(rows: list[dict[str, Any]]) -> list[str]:
    lowest = min(row["estimated_kv_cache_bytes"] for row in rows)
    return sorted(row["variant"] for row in rows if row["estimated_kv_cache_bytes"] == lowest)


def _leader_text(variants: list[str]) -> str:
    if len(variants) == 1:
        return f"`{variants[0]}`"
    return "tie between " + ", ".join(f"`{variant}`" for variant in variants)


def _aggregate_variant_cells(cells: list[dict[str, Any]]) -> dict[str, Any]:
    first = cells[0]
    ratios = [cell["mean_ratio_vs_baseline_mean"] for cell in cells]
    mean_mses = [cell["mean_ms_mean"] for cell in cells]
    batch_sizes = sorted({cell["batch_size"] for cell in cells})
    seq_lens = sorted({cell["seq_len"] for cell in cells})

    return {
        "variant": first["variant"],
        "name": first["name"],
        "grid_cells": len(cells),
        "batch_sizes": batch_sizes,
        "seq_lens": seq_lens,
        "mean_ratio_across_grid": statistics.fmean(ratios),
        "median_ratio_across_grid": statistics.median(ratios),
        "best_ratio_across_grid": min(ratios),
        "worst_ratio_across_grid": max(ratios),
        "ratio_range_across_grid": max(ratios) - min(ratios),
        "mean_ms_across_grid": statistics.fmean(mean_mses),
        "estimated_flops": first["estimated_flops"],
        "estimated_kv_cache_bytes": first["estimated_kv_cache_bytes"],
        "estimated_kv_cache_bytes_saved": first["estimated_kv_cache_bytes_saved"],
    }


def build_benchmark_matrix(
    root_dir: str | Path,
    *,
    batch_sizes: list[int],
    seq_lens: list[int],
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
    report_runs: int = 3,
) -> dict[str, Any]:
    if not batch_sizes:
        raise ValueError("batch_sizes must not be empty")
    if not seq_lens:
        raise ValueError("seq_lens must not be empty")

    baseline, variants = load_default_report_configs(str(root_dir))
    grid_reports: list[dict[str, Any]] = []
    variant_cells: dict[str, list[dict[str, Any]]] = {}

    for batch_size in batch_sizes:
        for seq_len in seq_lens:
            report = generate_variant_report(
                baseline,
                variants,
                batch_size=batch_size,
                seq_len=seq_len,
                seed=seed,
                warmup_runs=warmup_runs,
                measured_runs=measured_runs,
                report_runs=report_runs,
            )
            grid_reports.append(
                {
                    "batch_size": batch_size,
                    "seq_len": seq_len,
                    "rankings": report["rankings"],
                    "variant_rows": report["variant_rows"],
                }
            )
            for row in report["variant_rows"]:
                variant_cells.setdefault(row["variant"], []).append(
                    {
                        "batch_size": batch_size,
                        "seq_len": seq_len,
                        **row,
                    }
                )

    variant_summary_rows = sorted(
        (_aggregate_variant_cells(cells) for cells in variant_cells.values()),
        key=lambda row: (row["mean_ratio_across_grid"], row["variant"]),
    )
    best_mean_variants = _leader_variants(variant_summary_rows, key="mean_ratio_across_grid")
    best_worst_case_variants = _leader_variants(variant_summary_rows, key="worst_ratio_across_grid")
    lowest_kv_variants = _lowest_kv_variants(variant_summary_rows)

    return {
        "headline": "Micro Benchmark Matrix",
        "baseline": {
            "name": baseline.name,
            "variant": baseline.variant.kind,
            "batch_sizes": batch_sizes,
            "seq_lens": seq_lens,
            "warmup_runs": warmup_runs,
            "measured_runs": measured_runs,
            "report_runs": report_runs,
        },
        "summary": {
            "best_mean_runtime_variant": best_mean_variants[0],
            "best_mean_runtime_variants": best_mean_variants,
            "best_worst_case_runtime_variant": best_worst_case_variants[0],
            "best_worst_case_runtime_variants": best_worst_case_variants,
            "lowest_kv_variant": lowest_kv_variants[0],
            "lowest_kv_variants": lowest_kv_variants,
            "grid_cell_count": len(grid_reports),
        },
        "variant_summary_rows": variant_summary_rows,
        "grid_reports": grid_reports,
        "notes": [
            "This matrix sweeps the existing micro benchmark across batch size and sequence length.",
            "Use it to inspect directional scaling behavior across variants, not to claim optimized hardware performance.",
        ],
    }


def render_benchmark_matrix_markdown(matrix: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {matrix['headline']}")
    lines.append("")
    lines.append("## Summary")
    lines.append(
        f"- Best mean runtime across the grid: {_leader_text(matrix['summary'].get('best_mean_runtime_variants', [matrix['summary']['best_mean_runtime_variant']]))}."
    )
    lines.append(
        f"- Best worst-case runtime across the grid: {_leader_text(matrix['summary'].get('best_worst_case_runtime_variants', [matrix['summary']['best_worst_case_runtime_variant']]))}."
    )
    lines.append(
        f"- Lowest KV cache across the grid: {_leader_text(matrix['summary'].get('lowest_kv_variants', [matrix['summary']['lowest_kv_variant']]))}."
    )
    lines.append(f"- Grid cells: `{matrix['summary']['grid_cell_count']}`.")
    lines.append("")
    lines.append("## Variant Matrix")
    lines.append("")
    lines.append("| Variant | Mean Ratio Across Grid | Median Ratio | Best Ratio | Worst Ratio | Ratio Range | Mean ms Across Grid | KV Cache Bytes |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in matrix["variant_summary_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['mean_ratio_across_grid']:.3f} | {row['median_ratio_across_grid']:.3f} | {row['best_ratio_across_grid']:.3f} | "
            f"{row['worst_ratio_across_grid']:.3f} | {row['ratio_range_across_grid']:.3f} | "
            f"{row['mean_ms_across_grid']:.3f} | {row['estimated_kv_cache_bytes']} |"
        )
    lines.append("")
    lines.append("## Benchmark Context")
    baseline = matrix["baseline"]
    lines.append(
        f"- Baseline: `{baseline['name']}`; batch sizes `{baseline['batch_sizes']}`; seq lens `{baseline['seq_lens']}`; "
        f"warmup `{baseline['warmup_runs']}`; measured `{baseline['measured_runs']}`; report runs `{baseline['report_runs']}`."
    )
    for note in matrix.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a micro benchmark matrix across batch-size and sequence-length settings.")
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--batch-size", dest="batch_sizes", type=int, action="append", required=True)
    parser.add_argument("--seq-len", dest="seq_lens", type=int, action="append", required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--warmup-runs", type=int, default=1)
    parser.add_argument("--measured-runs", type=int, default=5)
    parser.add_argument("--report-runs", type=int, default=3)
    parser.add_argument("--artifact-json")
    parser.add_argument("--artifact-md")
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    matrix = build_benchmark_matrix(
        args.root_dir,
        batch_sizes=args.batch_sizes,
        seq_lens=args.seq_lens,
        seed=args.seed,
        warmup_runs=args.warmup_runs,
        measured_runs=args.measured_runs,
        report_runs=args.report_runs,
    )
    markdown = render_benchmark_matrix_markdown(matrix)
    if args.artifact_json:
        path = Path(args.artifact_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(matrix, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        path = Path(args.artifact_md)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
