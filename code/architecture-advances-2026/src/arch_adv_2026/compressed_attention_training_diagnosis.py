from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _slice_summary(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[Any, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row)

    summaries: list[dict[str, Any]] = []
    for value, bucket in sorted(grouped.items(), key=lambda item: item[0]):
        loss_values = [row["report"]["variant_rows"][0]["final_loss_delta_vs_baseline_mean"] for row in bucket]
        speed_values = [row["report"]["variant_rows"][0]["mean_step_ms_ratio_vs_baseline_mean"] for row in bucket]
        summaries.append(
            {
                key: value,
                "row_count": len(bucket),
                "mean_loss_delta": statistics.fmean(loss_values),
                "worst_loss_delta": max(loss_values),
                "best_loss_delta": min(loss_values),
                "mean_speed_ratio": statistics.fmean(speed_values),
                "worst_speed_ratio": max(speed_values),
                "best_speed_ratio": min(speed_values),
            }
        )
    return summaries


def build_compressed_attention_training_diagnosis(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix.get("rows", [])
    if not rows:
        raise ValueError("training matrix must contain rows")

    enriched_rows: list[dict[str, Any]] = []
    for row in rows:
        variant_row = row["report"]["variant_rows"][0]
        enriched_rows.append(
            {
                "batch_size": row["batch_size"],
                "seq_len": row["seq_len"],
                "steps": row["steps"],
                "seed": row["seed"],
                "final_loss_delta_vs_baseline_mean": variant_row["final_loss_delta_vs_baseline_mean"],
                "mean_step_ms_ratio_vs_baseline_mean": variant_row["mean_step_ms_ratio_vs_baseline_mean"],
                "all_runs_finite": variant_row["all_runs_finite"],
                "report": row["report"],
            }
        )

    worst_loss_rows = sorted(
        enriched_rows,
        key=lambda row: (
            row["final_loss_delta_vs_baseline_mean"],
            row["mean_step_ms_ratio_vs_baseline_mean"],
        ),
        reverse=True,
    )[:3]
    slowest_rows = sorted(
        enriched_rows,
        key=lambda row: (
            row["mean_step_ms_ratio_vs_baseline_mean"],
            row["final_loss_delta_vs_baseline_mean"],
        ),
        reverse=True,
    )[:3]

    return {
        "headline": "Compressed Attention Training Diagnosis",
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "row_count": len(enriched_rows),
        "batch_size_summaries": _slice_summary(enriched_rows, "batch_size"),
        "seq_len_summaries": _slice_summary(enriched_rows, "seq_len"),
        "steps_summaries": _slice_summary(enriched_rows, "steps"),
        "worst_loss_rows": worst_loss_rows,
        "slowest_rows": slowest_rows,
        "notes": [
            "Use this diagnosis to see which training slices drive the promotion-stage failure.",
            "Positive loss delta means the variant ends with worse final loss than baseline on that row.",
        ],
    }


def render_compressed_attention_training_diagnosis_markdown(diagnosis: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {diagnosis['headline']}")
    lines.append("")
    lines.append(f"_Updated: {diagnosis['date']}_")
    lines.append("")
    lines.append("## Worst Loss Rows")
    lines.append("")
    lines.append("| Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    for row in diagnosis["worst_loss_rows"]:
        lines.append(
            f"| {row['batch_size']} | {row['seq_len']} | {row['steps']} | {row['seed']} | "
            f"{row['final_loss_delta_vs_baseline_mean']:.3f} | {row['mean_step_ms_ratio_vs_baseline_mean']:.3f} |"
        )
    lines.append("")
    lines.append("## Slowest Rows")
    lines.append("")
    lines.append("| Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    for row in diagnosis["slowest_rows"]:
        lines.append(
            f"| {row['batch_size']} | {row['seq_len']} | {row['steps']} | {row['seed']} | "
            f"{row['final_loss_delta_vs_baseline_mean']:.3f} | {row['mean_step_ms_ratio_vs_baseline_mean']:.3f} |"
        )
    lines.append("")
    for section, key, label in [
        ("Batch-size slices", "batch_size_summaries", "batch_size"),
        ("Sequence-length slices", "seq_len_summaries", "seq_len"),
        ("Step-count slices", "steps_summaries", "steps"),
    ]:
        lines.append(f"## {section}")
        lines.append("")
        lines.append(f"| {label.replace('_', ' ').title()} | Rows | Mean Loss Delta | Worst Loss Delta | Mean Speed Ratio | Worst Speed Ratio |")
        lines.append("|---:|---:|---:|---:|---:|---:|")
        for row in diagnosis[key]:
            lines.append(
                f"| {row[label]} | {row['row_count']} | {row['mean_loss_delta']:.3f} | {row['worst_loss_delta']:.3f} | "
                f"{row['mean_speed_ratio']:.3f} | {row['worst_speed_ratio']:.3f} |"
            )
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a slice-oriented diagnosis for the compressed_attention training follow-up.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    diagnosis = build_compressed_attention_training_diagnosis(load_json(args.matrix))
    markdown = render_compressed_attention_training_diagnosis_markdown(diagnosis)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(diagnosis, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
