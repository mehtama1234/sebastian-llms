from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_compressed_attention_training_stress_assessment(matrix: dict[str, Any]) -> dict[str, Any]:
    rows = matrix.get("rows", [])
    if not rows:
        raise ValueError("stress follow-up matrix must contain rows")

    loss_rows: list[float] = []
    speed_rows: list[float] = []
    positive_loss_rows = 0
    slow_rows = 0
    worst_loss_row: dict[str, Any] | None = None
    slowest_row: dict[str, Any] | None = None

    for row in rows:
        variant_row = row["report"]["variant_rows"][0]
        loss = variant_row["final_loss_delta_vs_baseline_mean"]
        speed = variant_row["mean_step_ms_ratio_vs_baseline_mean"]
        loss_rows.append(loss)
        speed_rows.append(speed)
        if loss > 0.0:
            positive_loss_rows += 1
        if speed > 1.0:
            slow_rows += 1

        candidate = {
            "batch_size": row["batch_size"],
            "seq_len": row["seq_len"],
            "steps": row["steps"],
            "seed": row["seed"],
            "loss_delta": loss,
            "speed_ratio": speed,
        }
        if worst_loss_row is None or candidate["loss_delta"] > worst_loss_row["loss_delta"]:
            worst_loss_row = candidate
        if slowest_row is None or candidate["speed_ratio"] > slowest_row["speed_ratio"]:
            slowest_row = candidate

    mean_loss = statistics.fmean(loss_rows)
    mean_speed = statistics.fmean(speed_rows)
    positive_loss_fraction = positive_loss_rows / len(rows)
    slow_fraction = slow_rows / len(rows)

    reproduces_failure = (
        mean_loss > 0.0
        and positive_loss_fraction >= 0.5
    )
    speed_instability = mean_speed > 1.0 or slow_fraction >= 0.25

    reasons: list[str] = []
    if reproduces_failure:
        reasons.append("the stress grid still has more worse-than-baseline loss rows than better-than-baseline rows")
    else:
        reasons.append("the stress grid does not clearly reproduce a broad loss failure")
    if speed_instability:
        reasons.append("the stress grid still contains a material slow-tail under the diagnosed slices")
    else:
        reasons.append("the stress grid does not show a broad speed-tail problem")

    conclusion = (
        "Focused compressed_attention stress follow-up reproduces the diagnosed training weakness."
        if reproduces_failure or speed_instability
        else "Focused compressed_attention stress follow-up does not strongly reproduce the diagnosed weakness."
    )

    return {
        "headline": "Compressed Attention Training Stress Assessment",
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "row_count": len(rows),
        "mean_loss_delta": mean_loss,
        "mean_speed_ratio": mean_speed,
        "positive_loss_fraction": positive_loss_fraction,
        "slow_row_fraction": slow_fraction,
        "reproduces_failure": reproduces_failure,
        "speed_instability": speed_instability,
        "conclusion": conclusion,
        "reasons": reasons,
        "worst_loss_row": worst_loss_row,
        "slowest_row": slowest_row,
        "coverage": {
            "batch_sizes": matrix.get("batch_sizes", []),
            "seq_lens": matrix.get("seq_lens", []),
            "steps_list": matrix.get("steps_list", []),
            "seeds": matrix.get("seeds", []),
            "report_runs": matrix.get("report_runs"),
        },
    }


def render_compressed_attention_training_stress_assessment_markdown(assessment: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {assessment['headline']}")
    lines.append("")
    lines.append(f"_Updated: {assessment['date']}_")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(f"- {assessment['conclusion']}")
    lines.append("")
    lines.append("## Signals")
    lines.append(f"- Mean loss delta: `{assessment['mean_loss_delta']:.3f}`")
    lines.append(f"- Mean speed ratio: `{assessment['mean_speed_ratio']:.3f}`")
    lines.append(f"- Positive-loss row fraction: `{assessment['positive_loss_fraction']:.3f}`")
    lines.append(f"- Slow-row fraction: `{assessment['slow_row_fraction']:.3f}`")
    for reason in assessment["reasons"]:
        lines.append(f"- {reason}")
    lines.append("")
    lines.append("## Stress Coverage")
    coverage = assessment["coverage"]
    lines.append(f"- Batch sizes: `{coverage['batch_sizes']}`")
    lines.append(f"- Seq lens: `{coverage['seq_lens']}`")
    lines.append(f"- Steps: `{coverage['steps_list']}`")
    lines.append(f"- Seeds: `{coverage['seeds']}`")
    lines.append(f"- Report runs: `{coverage['report_runs']}`")
    lines.append("")
    lines.append("## Worst Rows")
    lines.append("")
    lines.append("| Kind | Batch | Seq Len | Steps | Seed | Loss Delta | Speed Ratio |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for label, row in [("worst_loss", assessment["worst_loss_row"]), ("slowest", assessment["slowest_row"])]:
        lines.append(
            f"| `{label}` | {row['batch_size']} | {row['seq_len']} | {row['steps']} | {row['seed']} | "
            f"{row['loss_delta']:.3f} | {row['speed_ratio']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess whether the diagnosed compressed_attention training weakness reproduces on a focused stress grid.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = build_compressed_attention_training_stress_assessment(load_json(args.matrix))
    markdown = render_compressed_attention_training_stress_assessment_markdown(assessment)
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
