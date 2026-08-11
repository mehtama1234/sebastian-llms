from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .training_report import generate_training_report, load_default_training_report_configs


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def execute_compressed_attention_remediation_plan(
    plan: dict[str, Any],
    *,
    root_dir: str | Path,
    lr: float = 1e-2,
    clip_grad_norm: float | None = 1.0,
    report_runs: int = 2,
) -> dict[str, Any]:
    baseline, variants = load_default_training_report_configs(
        str(root_dir),
        variant_names=["compressed_attention"],
    )
    if len(variants) != 1:
        raise ValueError("expected exactly one compressed_attention variant config")

    execution_steps: list[dict[str, Any]] = []
    for step in sorted(plan.get("steps", []), key=lambda row: row.get("priority", 0)):
        target = step["target_slice"]
        if "batch_size" not in target or "seq_len" not in target or "steps" not in target:
            execution_steps.append(
                {
                    "priority": step["priority"],
                    "title": step["title"],
                    "skipped": True,
                    "reason": "target slice does not resolve to one training run",
                }
            )
            continue

        seed = target.get("seed", 17)
        report = generate_training_report(
            baseline,
            variants,
            batch_size=target["batch_size"],
            seq_len=target["seq_len"],
            steps=target["steps"],
            lr=lr,
            seed=seed,
            clip_grad_norm=clip_grad_norm,
            report_runs=report_runs,
        )
        variant_row = report["variant_rows"][0]
        success_checks = {
            "loss_nonpositive": variant_row["final_loss_delta_vs_baseline_mean"] <= 0.0,
            "speed_at_or_below_baseline": variant_row["mean_step_ms_ratio_vs_baseline_mean"] <= 1.0,
            "finite_runs": variant_row["all_runs_finite"],
        }
        execution_steps.append(
            {
                "priority": step["priority"],
                "title": step["title"],
                "target_slice": target,
                "report_runs": report_runs,
                "report": report,
                "variant_row": variant_row,
                "success_checks": success_checks,
                "all_success_checks_passed": all(success_checks.values()),
            }
        )

    return {
        "headline": "Compressed Attention Remediation Execution",
        "date": "2026-08-09",
        "variant": "compressed_attention",
        "plan_headline": plan.get("headline"),
        "promotion_recommendation": plan.get("promotion_recommendation"),
        "execution_steps": execution_steps,
    }


def render_compressed_attention_remediation_execution_markdown(execution: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {execution['headline']}")
    lines.append("")
    lines.append(f"_Updated: {execution['date']}_")
    lines.append("")
    lines.append("## Step Results")
    for step in execution["execution_steps"]:
        lines.append(f"- P{step['priority']}: {step['title']}")
        if step.get("skipped"):
            lines.append(f"  Skipped: {step['reason']}")
            continue
        row = step["variant_row"]
        lines.append(
            f"  Target: `{json.dumps(step['target_slice'], sort_keys=True)}`; "
            f"loss delta `{row['final_loss_delta_vs_baseline_mean']:.3f}`; "
            f"speed ratio `{row['mean_step_ms_ratio_vs_baseline_mean']:.3f}`; "
            f"finite `{str(bool(row['all_runs_finite'])).lower()}`"
        )
        for key, value in step["success_checks"].items():
            lines.append(f"  Check `{key}`: `{str(bool(value)).lower()}`")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute the compressed_attention remediation plan on its targeted training slices.")
    parser.add_argument("--plan", required=True)
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--clip-grad-norm", type=float, default=1.0)
    parser.add_argument("--report-runs", type=int, default=2)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    execution = execute_compressed_attention_remediation_plan(
        load_json(args.plan),
        root_dir=args.root_dir,
        lr=args.lr,
        clip_grad_norm=args.clip_grad_norm,
        report_runs=args.report_runs,
    )
    markdown = render_compressed_attention_remediation_execution_markdown(execution)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
