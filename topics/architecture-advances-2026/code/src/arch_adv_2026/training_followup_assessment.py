from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_training_followup_assessment(
    matrix: dict[str, Any],
    *,
    current_decision: str,
    candidate_decision: str,
) -> dict[str, Any]:
    rows = matrix.get("variant_trends", [])
    if len(rows) != 1:
        raise ValueError("focused training follow-up assessment expects exactly one variant trend row")
    row = rows[0]
    variant = row["variant"]

    supports_current = False
    supports_candidate = False
    reasons: list[str] = []

    if row["final_loss_delta_vs_baseline_mean"] > 0.0:
        reasons.append("mean final-loss delta is worse than baseline")
        supports_current = current_decision == "drop"
    if row["mean_step_ms_ratio_vs_baseline_mean"] > 1.0:
        reasons.append("mean training step time is slower than baseline")
        supports_current = supports_current or current_decision in {"drop", "exploratory"}
    if not row["consistent_loss_advantage"]:
        reasons.append("loss advantage is not consistent across the follow-up grid")
    if not row["consistent_speed_advantage"]:
        reasons.append("speed advantage is not consistent across the follow-up grid")
    if row["all_matrix_rows_finite"]:
        reasons.append("all follow-up rows stayed finite")

    if (
        row["consistent_loss_advantage"]
        and row["final_loss_delta_vs_baseline_mean"] < 0.0
        and row["mean_step_ms_ratio_vs_baseline_mean"] <= 1.0
    ):
        supports_candidate = True
        reasons.append("the follow-up clears both loss and speed gates strongly enough to support promotion")
    elif candidate_decision in {"exploratory", "drop"} and (
        row["final_loss_delta_vs_baseline_mean"] > 0.0
        or row["mean_step_ms_ratio_vs_baseline_mean"] > 1.0
    ):
        supports_candidate = True
        reasons.append("the follow-up is weak enough on loss or speed to support a more conservative label")

    conclusion = (
        f"Focused training follow-up for `{variant}` supports the current `{current_decision}` label over the candidate "
        f"`{candidate_decision}` label."
        if supports_current and not supports_candidate
        else (
            f"Focused training follow-up for `{variant}` supports the candidate `{candidate_decision}` label over the current "
            f"`{current_decision}` label."
            if supports_candidate and not supports_current
            else (
                f"Focused training follow-up for `{variant}` is mixed: it does not cleanly resolve `{current_decision}` versus "
                f"`{candidate_decision}`."
            )
        )
    )

    return {
        "headline": "Focused Training Follow-up Assessment",
        "assessment_kind": "training_followup",
        "date": "2026-08-09",
        "variant": variant,
        "current_decision": current_decision,
        "candidate_decision": candidate_decision,
        "supports_current_decision": supports_current,
        "supports_candidate_decision": supports_candidate,
        "conclusion": conclusion,
        "trend_row": row,
        "reasons": reasons,
    }


def render_training_followup_assessment_markdown(assessment: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {assessment['headline']}")
    lines.append("")
    lines.append(f"_Updated: {assessment['date']}_")
    lines.append("")
    lines.append("## Conclusion")
    lines.append(f"- {assessment['conclusion']}")
    lines.append("")
    lines.append("## Signals")
    for reason in assessment["reasons"]:
        lines.append(f"- {reason}")
    lines.append("")
    row = assessment["trend_row"]
    lines.append("## Trend Row")
    lines.append("")
    lines.append("| Variant | Mean Loss Delta | Loss Range | Mean Speed Ratio | Speed Range | Consistent Loss | Consistent Speed |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    lines.append(
        f"| `{row['variant']}` | {row['final_loss_delta_vs_baseline_mean']:.3f} | {row['final_loss_delta_vs_baseline_range']:.3f} | "
        f"{row['mean_step_ms_ratio_vs_baseline_mean']:.3f} | {row['mean_step_ms_ratio_vs_baseline_range']:.3f} | "
        f"{str(bool(row['consistent_loss_advantage'])).lower()} | {str(bool(row['consistent_speed_advantage'])).lower()} |"
    )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess a focused single-variant training follow-up artifact.")
    parser.add_argument("--matrix", required=True)
    parser.add_argument("--current-decision", required=True)
    parser.add_argument("--candidate-decision", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = build_training_followup_assessment(
        load_json(args.matrix),
        current_decision=args.current_decision,
        candidate_decision=args.candidate_decision,
    )
    markdown = render_training_followup_assessment_markdown(assessment)
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
