from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .real_policy_experiment import (
    retrieval_only_real_policy_matrix,
    run_real_policy_experiment,
)
from .real_policy_memo import _pick_best_retrieval, _retrieval_rows


def _slice_specs() -> list[dict[str, Any]]:
    return [
        {"name": "all", "task_class": None, "long_context": None},
        {"name": "long_context", "task_class": None, "long_context": True},
        {"name": "short_context", "task_class": None, "long_context": False},
        {"name": "inspect", "task_class": "inspect", "long_context": None},
        {"name": "diagnose", "task_class": "diagnose", "long_context": None},
        {"name": "bug_fix", "task_class": "bug_fix", "long_context": None},
        {"name": "research", "task_class": "research", "long_context": None},
    ]


def build_real_retrieval_slice_report(manifest_path: str) -> dict[str, Any]:
    slices: list[dict[str, Any]] = []
    matrix = retrieval_only_real_policy_matrix()
    for spec in _slice_specs():
        report = run_real_policy_experiment(
            manifest_path,
            matrix=matrix,
            task_class=spec["task_class"],
            long_context=spec["long_context"],
        )
        rows = _retrieval_rows(report)
        if not rows:
            continue
        winner = _pick_best_retrieval(rows)
        slices.append(
            {
                "name": spec["name"],
                "task_class": spec["task_class"],
                "long_context": spec["long_context"],
                "task_count": next(iter(report.scorecards.values())).task_count if report.scorecards else 0,
                "recommended_default": winner["name"],
                "retrieval_candidates": rows,
            }
        )
    return {
        "report_type": "real_retrieval_slice_report",
        "slices": slices,
    }


def render_real_retrieval_slice_report_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = ["# Real Retrieval Slice Report", ""]
    for spec in report["slices"]:
        lines.append(f"## {spec['name']}")
        lines.append("")
        lines.append(f"- Recommended: `{spec['recommended_default']}`")
        lines.append(f"- Task count: `{spec['task_count']}`")
        lines.append("")
        lines.append("| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Tokens / Accepted Task |")
        lines.append("|---|---:|---:|---:|---:|---:|")
        for row in spec["retrieval_candidates"]:
            lines.append(
                f"| `{row['name']}` | {row['accepted_rate']:.3f} | {row['grounded_rate']:.3f} | "
                f"{row['task_with_any_gold_hit_rate']:.3f} | {row['mean_gold_file_recall']:.3f} | "
                f"{row['response_tokens_per_accepted_task']:.1f} |"
            )
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="llm-dev-real-retrieval-slice-report",
        description="Render retrieval-only policy comparisons over useful real benchmark slices.",
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-json")
    parser.add_argument("--artifact-md")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args(argv)

    report = build_real_retrieval_slice_report(str(args.manifest))
    markdown = render_real_retrieval_slice_report_markdown(report)
    if args.artifact_json:
        path = Path(args.artifact_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(f"Wrote real retrieval slice report JSON to {path}")
    if args.artifact_md:
        path = Path(args.artifact_md)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
        print(f"Wrote real retrieval slice report markdown to {path}")
    if args.stdout or not args.artifact_md:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
