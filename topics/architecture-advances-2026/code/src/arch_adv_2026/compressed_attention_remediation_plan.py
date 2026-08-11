from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_compressed_attention_remediation_plan(
    promotion_assessment: dict[str, Any],
    stress_assessment: dict[str, Any],
    speed_tail_assessment: dict[str, Any],
) -> dict[str, Any]:
    gates = promotion_assessment["gates"]
    steps: list[dict[str, Any]] = []

    widest_slow_batch = max(
        speed_tail_assessment["batch_summaries"],
        key=lambda row: (row["slow_row_fraction"], row["mean_speed_ratio"]),
    )
    worst_tail_batch = max(
        speed_tail_assessment["batch_summaries"],
        key=lambda row: (row["worst_speed_ratio"], row["mean_speed_ratio"]),
    )
    dominant_steps = speed_tail_assessment["dominant_steps"]["steps"]
    worst_loss_row = stress_assessment["worst_loss_row"]
    slowest_row = stress_assessment["slowest_row"]

    if not gates["training_pass"]:
        steps.append(
            {
                "priority": 1,
                "title": "Stabilize short-context training loss",
                "why": "The focused stress rerun on August 9, 2026 reproduced worse-than-baseline loss on the short-context slice.",
                "target_slice": {
                    "batch_size": worst_loss_row["batch_size"],
                    "seq_len": worst_loss_row["seq_len"],
                    "steps": worst_loss_row["steps"],
                    "seed": worst_loss_row["seed"],
                },
                "success_criteria": [
                    "mean final-loss delta on the stressed short-context slice moves to 0 or below",
                    "positive-loss row fraction drops below 0.5 on the focused stress grid",
                ],
            }
        )

    steps.append(
        {
            "priority": 2,
            "title": "Reduce broad short-context slowdown at the small batch slice",
            "why": f"Batch {widest_slow_batch['batch_size']} has the broadest slow-row concentration in the current short-context speed-tail assessment.",
            "target_slice": {
                "batch_size": widest_slow_batch["batch_size"],
                "seq_len": 8,
                "steps": dominant_steps,
            },
            "success_criteria": [
                "slow-row fraction on the broad slowdown slice drops below 0.5",
                "mean speed ratio on that slice moves to 1.0 or below",
            ],
        }
    )

    steps.append(
        {
            "priority": 3,
            "title": "Eliminate the worst speed-tail event",
            "why": f"Batch {worst_tail_batch['batch_size']} contains the current worst short-context speed ratio, with the worst tail concentrated at {dominant_steps} steps.",
            "target_slice": {
                "batch_size": slowest_row["batch_size"],
                "seq_len": slowest_row["seq_len"],
                "steps": slowest_row["steps"],
                "seed": slowest_row["seed"],
            },
            "success_criteria": [
                "worst speed ratio on the focused stress grid drops below 1.2",
                "no single stressed row shows an outsized tail event relative to the rest of the grid",
            ],
        }
    )

    if not gates["benchmark_pass"]:
        steps.append(
            {
                "priority": 4,
                "title": "Reconfirm worst-case systems stability after the training fix",
                "why": "The current promotion assessment still marks the systems gate as failed on the broader grid.",
                "target_slice": {
                    "batch_sizes": promotion_assessment["benchmark"]["batch_sizes"],
                    "seq_lens": promotion_assessment["benchmark"]["seq_lens"],
                },
                "success_criteria": [
                    "worst runtime ratio in the promotion benchmark matrix drops to 1.10 or below",
                ],
            }
        )

    return {
        "headline": "Compressed Attention Remediation Plan",
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "promotion_recommendation": promotion_assessment["recommendation"],
        "gates": gates,
        "steps": steps,
        "notes": [
            "This plan is generated from the current promotion assessment plus the focused stress and speed-tail artifacts.",
            "Use it as the next concrete experiment queue rather than reopening the full architecture search.",
        ],
    }


def render_compressed_attention_remediation_plan_markdown(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {plan['headline']}")
    lines.append("")
    lines.append(f"_Updated: {plan['date']}_")
    lines.append("")
    lines.append("## Current State")
    lines.append(f"- Promotion recommendation: `{plan['promotion_recommendation']}`")
    lines.append(
        f"- Gates: long-context `{str(bool(plan['gates']['long_context_pass'])).lower()}`, "
        f"training `{str(bool(plan['gates']['training_pass'])).lower()}`, systems `{str(bool(plan['gates']['benchmark_pass'])).lower()}`"
    )
    lines.append("")
    lines.append("## Next Steps")
    for step in sorted(plan["steps"], key=lambda row: row["priority"]):
        lines.append(f"- P{step['priority']}: {step['title']}")
        lines.append(f"  Why: {step['why']}")
        lines.append(f"  Target: `{json.dumps(step['target_slice'], sort_keys=True)}`")
        for criterion in step["success_criteria"]:
            lines.append(f"  Success: {criterion}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the next concrete remediation plan for compressed_attention from the current promotion artifacts.")
    parser.add_argument("--promotion-assessment", required=True)
    parser.add_argument("--stress-assessment", required=True)
    parser.add_argument("--speed-tail-assessment", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = build_compressed_attention_remediation_plan(
        load_json(args.promotion_assessment),
        load_json(args.stress_assessment),
        load_json(args.speed_tail_assessment),
    )
    markdown = render_compressed_attention_remediation_plan_markdown(plan)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
