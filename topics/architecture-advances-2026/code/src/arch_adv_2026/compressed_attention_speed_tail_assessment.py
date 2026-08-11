from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _slice_speed(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    grouped: dict[Any, list[float]] = {}
    for row in rows:
        grouped.setdefault(row[key], []).append(row["speed_ratio"])
    result: list[dict[str, Any]] = []
    for value, values in sorted(grouped.items(), key=lambda item: item[0]):
        result.append(
            {
                key: value,
                "row_count": len(values),
                "mean_speed_ratio": statistics.fmean(values),
                "median_speed_ratio": statistics.median(values),
                "worst_speed_ratio": max(values),
                "slow_row_fraction": sum(1 for value in values if value > 1.0) / len(values),
            }
        )
    return result


def build_compressed_attention_speed_tail_assessment(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix.get("rows", [])
    if not rows:
        raise ValueError("stress follow-up matrix must contain rows")

    flat_rows: list[dict[str, Any]] = []
    for row in rows:
        variant_row = row["report"]["variant_rows"][0]
        flat_rows.append(
            {
                "batch_size": row["batch_size"],
                "seq_len": row["seq_len"],
                "steps": row["steps"],
                "seed": row["seed"],
                "speed_ratio": variant_row["mean_step_ms_ratio_vs_baseline_mean"],
                "loss_delta": variant_row["final_loss_delta_vs_baseline_mean"],
            }
        )

    slow_rows = [row for row in flat_rows if row["speed_ratio"] > 1.0]
    worst_rows = sorted(flat_rows, key=lambda row: row["speed_ratio"], reverse=True)[:5]

    batch_summaries = _slice_speed(flat_rows, "batch_size")
    step_summaries = _slice_speed(flat_rows, "steps")
    seed_summaries = _slice_speed(flat_rows, "seed")

    dominant_batch = max(batch_summaries, key=lambda row: (row["worst_speed_ratio"], row["mean_speed_ratio"]))
    dominant_steps = max(step_summaries, key=lambda row: (row["worst_speed_ratio"], row["mean_speed_ratio"]))

    conclusion_parts: list[str] = []
    if dominant_batch["slow_row_fraction"] > 0.5:
        conclusion_parts.append(f"speed tail is concentrated in batch `{dominant_batch['batch_size']}`")
    if dominant_steps["slow_row_fraction"] > 0.5:
        conclusion_parts.append(f"speed tail is concentrated at `{dominant_steps['steps']}` training steps")
    if not conclusion_parts:
        conclusion_parts.append("speed tail is spread across the stressed short-context grid")

    return {
        "headline": "Compressed Attention Short-Context Speed-Tail Assessment",
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "row_count": len(flat_rows),
        "slow_row_count": len(slow_rows),
        "slow_row_fraction": len(slow_rows) / len(flat_rows),
        "mean_speed_ratio": statistics.fmean(row["speed_ratio"] for row in flat_rows),
        "worst_speed_ratio": max(row["speed_ratio"] for row in flat_rows),
        "dominant_batch": dominant_batch,
        "dominant_steps": dominant_steps,
        "batch_summaries": batch_summaries,
        "step_summaries": step_summaries,
        "seed_summaries": seed_summaries,
        "worst_rows": worst_rows,
        "conclusion": "; ".join(conclusion_parts) + ".",
    }


def render_compressed_attention_speed_tail_assessment_markdown(assessment: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {assessment['headline']}")
    lines.append("")
    lines.append(f"_Updated: {assessment['date']}_")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(f"- {assessment['conclusion']}")
    lines.append(f"- Slow-row fraction: `{assessment['slow_row_fraction']:.3f}`")
    lines.append(f"- Mean speed ratio: `{assessment['mean_speed_ratio']:.3f}`")
    lines.append(f"- Worst speed ratio: `{assessment['worst_speed_ratio']:.3f}`")
    lines.append("")
    lines.append("## Worst Rows")
    lines.append("")
    lines.append("| Batch | Seq Len | Steps | Seed | Speed Ratio | Loss Delta |")
    lines.append("|---:|---:|---:|---:|---:|---:|")
    for row in assessment["worst_rows"]:
        lines.append(
            f"| {row['batch_size']} | {row['seq_len']} | {row['steps']} | {row['seed']} | "
            f"{row['speed_ratio']:.3f} | {row['loss_delta']:.3f} |"
        )
    lines.append("")
    for section, key, label in [
        ("Batch Slices", "batch_summaries", "batch_size"),
        ("Step Slices", "step_summaries", "steps"),
        ("Seed Slices", "seed_summaries", "seed"),
    ]:
        lines.append(f"## {section}")
        lines.append("")
        lines.append(f"| {label.replace('_', ' ').title()} | Rows | Mean Speed Ratio | Worst Speed Ratio | Slow Row Fraction |")
        lines.append("|---:|---:|---:|---:|---:|")
        for row in assessment[key]:
            lines.append(
                f"| {row[label]} | {row['row_count']} | {row['mean_speed_ratio']:.3f} | "
                f"{row['worst_speed_ratio']:.3f} | {row['slow_row_fraction']:.3f} |"
            )
        lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess the short-context speed-tail structure inside the compressed_attention stress follow-up.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = build_compressed_attention_speed_tail_assessment(load_json(args.matrix))
    markdown = render_compressed_attention_speed_tail_assessment_markdown(assessment)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
