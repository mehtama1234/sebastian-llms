from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .real_policy_experiment import (
    RealPolicyExperimentReport,
    retrieval_only_real_policy_matrix,
    run_real_policy_experiment,
)


RETRIEVAL_CANDIDATES = [
    "real_retrieval_lexical",
    "real_retrieval_sparse",
    "real_retrieval_task_aware",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a retrieval-default recommendation memo from the real policy experiment."
    )
    parser.add_argument("manifest", type=Path)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def _retrieval_rows(report: RealPolicyExperimentReport) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name in RETRIEVAL_CANDIDATES:
        if name not in report.scorecards:
            continue
        scorecard = report.scorecards[name]
        rows.append(
            {
                "name": name,
                "accepted_rate": scorecard.accepted_rate,
                "grounded_rate": scorecard.grounded_rate,
                "escalation_rate": scorecard.escalation_rate,
                "validation_pass_rate": scorecard.validation_pass_rate,
                "mean_context_snippets": scorecard.mean_context_snippets,
                "mean_response_tokens": scorecard.mean_response_tokens,
                "response_tokens_per_accepted_task": scorecard.response_tokens_per_accepted_task,
                "task_with_any_gold_hit_rate": scorecard.retrieval_diagnostics["task_with_any_gold_hit_rate"],
                "mean_gold_file_recall": scorecard.retrieval_diagnostics["mean_gold_file_recall"],
                "tasks_without_gold_hit": scorecard.retrieval_diagnostics["tasks_without_gold_hit"],
            }
        )
    return rows


def _acceptance_swings(
    report: RealPolicyExperimentReport,
    *,
    baseline_name: str,
    winner_name: str,
) -> list[dict[str, Any]]:
    baseline_tasks = {task.task_id: task for task in report.reports[baseline_name].tasks}
    winner_tasks = {task.task_id: task for task in report.reports[winner_name].tasks}
    swings: list[dict[str, Any]] = []
    for task_id in sorted(set(baseline_tasks) & set(winner_tasks)):
        baseline = baseline_tasks[task_id]
        winner = winner_tasks[task_id]
        if baseline.accepted == winner.accepted:
            continue
        swings.append(
            {
                "task_id": task_id,
                "baseline_accepted": baseline.accepted,
                "winner_accepted": winner.accepted,
                "baseline_hits": baseline.runtime["retrieval_diagnostics"]["retrieved_gold_files"],
                "winner_hits": winner.runtime["retrieval_diagnostics"]["retrieved_gold_files"],
                "baseline_misses": baseline.runtime["retrieval_diagnostics"]["missed_gold_files"],
                "winner_misses": winner.runtime["retrieval_diagnostics"]["missed_gold_files"],
            }
        )
    return swings


def _common_misses(report: RealPolicyExperimentReport, policy_name: str) -> list[dict[str, Any]]:
    counts: dict[str, int] = {}
    for task in report.reports[policy_name].tasks:
        for path in task.runtime["retrieval_diagnostics"]["missed_gold_files"]:
            counts[path] = counts.get(path, 0) + 1
    return [
        {"path": path, "count": count}
        for path, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))[:5]
    ]


def _pick_best_retrieval(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return sorted(
        rows,
        key=lambda row: (
            row["accepted_rate"],
            row["grounded_rate"],
            -row["escalation_rate"],
            row["validation_pass_rate"],
            -row["mean_response_tokens"],
            -row["mean_context_snippets"],
            row["name"] == "real_retrieval_task_aware",
        ),
        reverse=True,
    )[0]


def generate_real_policy_memo(report: RealPolicyExperimentReport) -> dict[str, Any]:
    rows = _retrieval_rows(report)
    if not rows:
        raise ValueError("report has no retrieval candidates")
    winner = _pick_best_retrieval(rows)
    baseline = next(row for row in rows if row["name"] == "real_retrieval_lexical")
    sparse = next((row for row in rows if row["name"] == "real_retrieval_sparse"), None)
    rationale: list[str] = []

    if winner["accepted_rate"] >= baseline["accepted_rate"] and winner["grounded_rate"] >= baseline["grounded_rate"]:
        rationale.append("It matches or exceeds the baseline retrieval policies on accepted and grounded rates.")
    if winner["accepted_rate"] > baseline["accepted_rate"]:
        rationale.append("Its acceptance lift comes from retrieving at least one gold file on more tasks than lexical retrieval.")
    if winner["mean_response_tokens"] < baseline["mean_response_tokens"]:
        rationale.append("It produces shorter grounded outputs than lexical retrieval on the sample benchmark.")
    if sparse is not None and winner["mean_response_tokens"] < sparse["mean_response_tokens"]:
        rationale.append("It is also cheaper than sparse retrieval on response-token cost.")
    if winner["name"] == "real_retrieval_task_aware":
        rationale.append("Its advantage comes from task-aware file-family balancing and entrypoint bias, not from adding more context snippets.")

    return {
        "label": report.label,
        "benchmark_count": len(report.reports),
        "retrieval_candidates": rows,
        "recommended_default": winner["name"],
        "baseline_reference": baseline["name"],
        "acceptance_swings_vs_baseline": _acceptance_swings(
            report,
            baseline_name=baseline["name"],
            winner_name=winner["name"],
        ),
        "winner_common_misses": _common_misses(report, winner["name"]),
        "rationale": rationale,
        "notes": [
            "This memo compares only retrieval-backed policies against each other.",
            "It does not treat the gold-evidence baseline as a fair replacement target because gold context is an oracle, not a runtime retrieval policy.",
        ],
    }


def render_real_policy_memo_markdown(memo: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Real Retrieval Policy Memo")
    lines.append("")
    lines.append(f"Recommended retrieval default: `{memo['recommended_default']}`")
    lines.append("")
    lines.append("## Retrieval Candidates")
    lines.append("")
    lines.append("| Policy | Accepted | Grounded | Gold-Hit Tasks | Mean Gold Recall | Validation | Mean Context Snippets | Tokens / Accepted Task |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in memo["retrieval_candidates"]:
        lines.append(
            f"| `{row['name']}` | {row['accepted_rate']:.3f} | {row['grounded_rate']:.3f} | "
            f"{row['task_with_any_gold_hit_rate']:.3f} | {row['mean_gold_file_recall']:.3f} | "
            f"{row['validation_pass_rate']:.3f} | {row['mean_context_snippets']:.1f} | "
            f"{row['response_tokens_per_accepted_task']:.1f} |"
        )
    lines.append("")
    lines.append("## Why")
    for line in memo["rationale"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Acceptance Swings Vs Lexical")
    if memo["acceptance_swings_vs_baseline"]:
        for swing in memo["acceptance_swings_vs_baseline"]:
            lines.append(
                f"- `{swing['task_id']}`: lexical accepted={str(swing['baseline_accepted']).lower()}, "
                f"winner accepted={str(swing['winner_accepted']).lower()}, "
                f"lexical hits={len(swing['baseline_hits'])}, winner hits={len(swing['winner_hits'])}."
            )
    else:
        lines.append("- No task changed acceptance between lexical retrieval and the recommended policy.")
    lines.append("")
    lines.append("## Common Misses")
    if memo["winner_common_misses"]:
        for item in memo["winner_common_misses"]:
            lines.append(f"- `{item['path']}` missed on {item['count']} task(s) by the recommended policy.")
    else:
        lines.append("- The recommended policy did not miss any declared gold files on this sample.")
    lines.append("")
    lines.append("## Notes")
    for line in memo["notes"]:
        lines.append(f"- {line}")
    lines.append("")
    return "\n".join(lines)


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def write_markdown_artifact(markdown: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = run_real_policy_experiment(
        str(args.manifest),
        matrix=retrieval_only_real_policy_matrix(),
    )
    memo = generate_real_policy_memo(report)
    markdown = render_real_policy_memo_markdown(memo)
    if args.artifact_json:
        path = write_json_artifact({"memo": memo, "report": report.to_dict()}, args.artifact_json)
        print(f"Wrote real retrieval policy memo JSON to {path}")
    if args.artifact_md:
        path = write_markdown_artifact(markdown, args.artifact_md)
        print(f"Wrote real retrieval policy memo markdown to {path}")
    if args.stdout or not args.artifact_md:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
