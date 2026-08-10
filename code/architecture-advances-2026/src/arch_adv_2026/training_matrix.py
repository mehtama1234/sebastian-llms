from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .training_report import generate_training_report, load_default_training_report_configs


DEFAULT_SEQ_LENS = (8, 16)
DEFAULT_STEPS = (4, 8)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a training-stability matrix across multiple schedules and seeds."
    )
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--artifact-out", required=False)
    parser.add_argument(
        "--batch-size",
        dest="batch_sizes",
        action="append",
        type=int,
        help="Batch size to include. Can be passed multiple times.",
    )
    parser.add_argument(
        "--variant",
        dest="variants",
        action="append",
        help="Limit the matrix to one or more variant labels. Can be passed multiple times.",
    )
    parser.add_argument(
        "--seq-len",
        dest="seq_lens",
        action="append",
        type=int,
        help="Sequence length to include. Can be passed multiple times.",
    )
    parser.add_argument(
        "--steps",
        dest="steps_list",
        action="append",
        type=int,
        help="Training step count to include. Can be passed multiple times.",
    )
    parser.add_argument(
        "--seed",
        dest="seeds",
        action="append",
        type=int,
        help="Base seed to include. Can be passed multiple times.",
    )
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--clip-grad-norm", type=float, default=1.0)
    parser.add_argument("--report-runs", type=int, default=1)
    parser.add_argument("--stdout", action="store_true")
    return parser


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def _variant_trend_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["variant"], []).append(row)

    trend_rows: list[dict[str, Any]] = []
    for variant, bucket in sorted(grouped.items()):
        final_loss_deltas = [row["final_loss_delta_vs_baseline_mean"] for row in bucket]
        speed_ratios = [row["mean_step_ms_ratio_vs_baseline_mean"] for row in bucket]
        grad_deltas = [row["max_grad_norm_delta_vs_baseline_mean"] for row in bucket]
        speed_win_count = sum(1 for row in bucket if row["row_fastest_variant"] == variant)
        loss_win_count = sum(1 for row in bucket if row["row_lowest_final_loss_delta_variant"] == variant)
        grad_win_count = sum(1 for row in bucket if row["row_lowest_grad_norm_delta_variant"] == variant)
        speed_min = min(speed_ratios)
        speed_max = max(speed_ratios)
        loss_min = min(final_loss_deltas)
        loss_max = max(final_loss_deltas)
        grad_min = min(grad_deltas)
        grad_max = max(grad_deltas)
        trend_rows.append(
            {
                "variant": variant,
                "matrix_rows": len(bucket),
                "all_matrix_rows_finite": all(row["all_runs_finite"] for row in bucket),
                "final_loss_delta_vs_baseline_mean": statistics.fmean(final_loss_deltas),
                "final_loss_delta_vs_baseline_min": loss_min,
                "final_loss_delta_vs_baseline_max": loss_max,
                "final_loss_delta_vs_baseline_range": loss_max - loss_min,
                "mean_step_ms_ratio_vs_baseline_mean": statistics.fmean(speed_ratios),
                "mean_step_ms_ratio_vs_baseline_min": speed_min,
                "mean_step_ms_ratio_vs_baseline_max": speed_max,
                "mean_step_ms_ratio_vs_baseline_range": speed_max - speed_min,
                "max_grad_norm_delta_vs_baseline_mean": statistics.fmean(grad_deltas),
                "max_grad_norm_delta_vs_baseline_min": grad_min,
                "max_grad_norm_delta_vs_baseline_max": grad_max,
                "max_grad_norm_delta_vs_baseline_range": grad_max - grad_min,
                "fastest_step_win_count": speed_win_count,
                "fastest_step_win_rate": speed_win_count / len(bucket),
                "lowest_final_loss_delta_win_count": loss_win_count,
                "lowest_final_loss_delta_win_rate": loss_win_count / len(bucket),
                "lowest_grad_norm_delta_win_count": grad_win_count,
                "lowest_grad_norm_delta_win_rate": grad_win_count / len(bucket),
                "consistent_speed_advantage": speed_max < 1.0,
                "consistent_loss_advantage": loss_max < 0.0,
                "total_nonfinite_step_count": sum(row["total_nonfinite_step_count"] for row in bucket),
            }
        )
    return trend_rows


def _winner_counts(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts = {
        "fastest_step_ratio": {},
        "lowest_final_loss_delta": {},
        "lowest_grad_norm_delta": {},
    }
    for row in rows:
        counts["fastest_step_ratio"][row["fastest_variant"]] = counts["fastest_step_ratio"].get(row["fastest_variant"], 0) + 1
        counts["lowest_final_loss_delta"][row["lowest_final_loss_delta_variant"]] = (
            counts["lowest_final_loss_delta"].get(row["lowest_final_loss_delta_variant"], 0) + 1
        )
        counts["lowest_grad_norm_delta"][row["lowest_grad_norm_delta_variant"]] = (
            counts["lowest_grad_norm_delta"].get(row["lowest_grad_norm_delta_variant"], 0) + 1
        )
    return counts


def execute_training_matrix(
    *,
    root_dir: str | Path,
    batch_size: int | None = None,
    batch_sizes: list[int] | None = None,
    seq_lens: list[int] | None = None,
    steps_list: list[int] | None = None,
    seeds: list[int] | None = None,
    lr: float = 1e-2,
    clip_grad_norm: float | None = 1.0,
    report_runs: int = 1,
    variant_names: list[str] | None = None,
) -> dict[str, Any]:
    baseline, variants = load_default_training_report_configs(
        str(root_dir),
        variant_names=variant_names,
    )
    resolved_batch_sizes = batch_sizes or ([batch_size] if batch_size is not None else [4])
    resolved_seq_lens = seq_lens or list(DEFAULT_SEQ_LENS)
    resolved_steps = steps_list or list(DEFAULT_STEPS)
    resolved_seeds = seeds or [17, 23]
    rows: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []

    for current_batch_size in resolved_batch_sizes:
        for seq_len in resolved_seq_lens:
            for steps in resolved_steps:
                for seed in resolved_seeds:
                    report = generate_training_report(
                        baseline,
                        variants,
                        batch_size=current_batch_size,
                        seq_len=seq_len,
                        steps=steps,
                        lr=lr,
                        seed=seed,
                        clip_grad_norm=clip_grad_norm,
                        report_runs=report_runs,
                    )
                    reports.append(report)
                    rows.append(
                        {
                            "batch_size": current_batch_size,
                            "seq_len": seq_len,
                            "steps": steps,
                            "seed": seed,
                            "report": report,
                            "fastest_variant": report["rankings"]["fastest_step_ratio"][0],
                            "lowest_final_loss_delta_variant": report["rankings"]["lowest_final_loss_delta"][0],
                            "lowest_grad_norm_delta_variant": report["rankings"]["lowest_grad_norm_delta"][0],
                        }
                    )

    flattened_variant_rows = [
        {
            **variant_row,
            "row_fastest_variant": row["fastest_variant"],
            "row_lowest_final_loss_delta_variant": row["lowest_final_loss_delta_variant"],
            "row_lowest_grad_norm_delta_variant": row["lowest_grad_norm_delta_variant"],
        }
        for row in rows
        for variant_row in row["report"]["variant_rows"]
    ]
    trend_rows = _variant_trend_rows(flattened_variant_rows)
    winner_counts = _winner_counts(rows)

    return {
        "baseline": {
            "name": baseline.name,
            "variant": baseline.variant.kind,
            "batch_size": resolved_batch_sizes[0],
            "batch_sizes": resolved_batch_sizes,
        },
        "batch_sizes": resolved_batch_sizes,
        "seq_lens": resolved_seq_lens,
        "steps_list": resolved_steps,
        "seeds": resolved_seeds,
        "lr": lr,
        "clip_grad_norm": clip_grad_norm,
        "report_runs": report_runs,
        "variant_labels": [variant.variant.kind for variant in variants],
        "row_count": len(rows),
        "rows": rows,
        "variant_trends": trend_rows,
        "winner_counts": winner_counts,
        "notes": [
            "This matrix expands training stability from one schedule to multiple schedule/seed combinations.",
            "Batch size can also vary across the matrix so speed or stability wins are not tied to one micro batch shape.",
            "Use the per-row winners for sensitivity and the per-variant trends for carry-forward decisions.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    matrix = execute_training_matrix(
        root_dir=args.root_dir,
        batch_sizes=args.batch_sizes,
        seq_lens=args.seq_lens,
        steps_list=args.steps_list,
        seeds=args.seeds,
        lr=args.lr,
        clip_grad_norm=args.clip_grad_norm,
        report_runs=args.report_runs,
        variant_names=args.variants,
    )
    if args.artifact_out:
        path = write_json_artifact(matrix, args.artifact_out)
        print(f"Wrote training matrix artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(matrix, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
