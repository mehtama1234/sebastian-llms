from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .concept_decision_audit import build_concept_decision_audit, render_concept_decision_audit_markdown
from .concept_review_plan import build_concept_review_plan, render_concept_review_plan_markdown
from .concept_scorecard import build_concept_scorecard, render_concept_scorecard_markdown
from .final_memo import generate_final_decision_memo, render_final_decision_memo_markdown


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, data: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_text(path: str | Path, text: str) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def refresh_decision_stack(
    *,
    micro_report: dict[str, Any],
    benchmark_matrix: dict[str, Any] | None,
    long_context_compare: dict[str, Any],
    training_matrix: dict[str, Any],
    seed_final_memo: dict[str, Any],
    long_context_selector: dict[str, Any],
    long_context_execution: dict[str, Any],
    followup_assessments: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, Any]]:
    current_final_memo = seed_final_memo
    final_stack: dict[str, dict[str, Any]] | None = None

    for _ in range(2):
        scorecard = build_concept_scorecard(
            micro_report,
            long_context_compare,
            training_matrix,
            current_final_memo,
            benchmark_matrix,
        )
        audit = build_concept_decision_audit(
            scorecard,
            followup_assessments=followup_assessments or [],
        )
        review_plan = build_concept_review_plan(
            scorecard,
            audit,
            followup_assessments=followup_assessments or [],
        )
        final_memo = generate_final_decision_memo(
            micro_report,
            long_context_selector,
            long_context_execution,
            training_matrix,
            review_plan,
            benchmark_matrix,
        )
        final_stack = {
            "scorecard": scorecard,
            "audit": audit,
            "review_plan": review_plan,
            "final_memo": final_memo,
        }
        if final_memo == current_final_memo:
            break
        current_final_memo = final_memo

    assert final_stack is not None
    return final_stack


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Refresh the architecture decision stack so scorecard, audit, review plan, and final memo agree."
    )
    parser.add_argument("--micro-report", required=True)
    parser.add_argument("--benchmark-matrix", required=False)
    parser.add_argument("--long-context-compare", required=True)
    parser.add_argument("--training-matrix", required=True)
    parser.add_argument("--seed-final-memo", required=True)
    parser.add_argument("--long-context-selector", required=True)
    parser.add_argument("--long-context-execution", required=True)
    parser.add_argument(
        "--followup-assessment",
        dest="followup_assessments",
        action="append",
        help="Optional focused follow-up assessment artifacts to fold into the review plan.",
    )
    parser.add_argument("--scorecard-json", required=True)
    parser.add_argument("--scorecard-md", required=True)
    parser.add_argument("--audit-json", required=True)
    parser.add_argument("--audit-md", required=True)
    parser.add_argument("--review-plan-json", required=True)
    parser.add_argument("--review-plan-md", required=True)
    parser.add_argument("--final-memo-json", required=True)
    parser.add_argument("--final-memo-md", required=True)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    refreshed = refresh_decision_stack(
        micro_report=load_json(args.micro_report),
        benchmark_matrix=load_json(args.benchmark_matrix) if args.benchmark_matrix else None,
        long_context_compare=load_json(args.long_context_compare),
        training_matrix=load_json(args.training_matrix),
        seed_final_memo=load_json(args.seed_final_memo),
        long_context_selector=load_json(args.long_context_selector),
        long_context_execution=load_json(args.long_context_execution),
        followup_assessments=[load_json(path) for path in (args.followup_assessments or [])],
    )

    _write_json(args.scorecard_json, refreshed["scorecard"])
    _write_text(args.scorecard_md, render_concept_scorecard_markdown(refreshed["scorecard"]))
    _write_json(args.audit_json, refreshed["audit"])
    _write_text(args.audit_md, render_concept_decision_audit_markdown(refreshed["audit"]))
    _write_json(args.review_plan_json, refreshed["review_plan"])
    _write_text(args.review_plan_md, render_concept_review_plan_markdown(refreshed["review_plan"]))
    _write_json(args.final_memo_json, refreshed["final_memo"])
    _write_text(args.final_memo_md, render_final_decision_memo_markdown(refreshed["final_memo"]))

    if args.stdout:
        print(render_final_decision_memo_markdown(refreshed["final_memo"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
