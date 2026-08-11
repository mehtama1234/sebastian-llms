from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .decision_stack_validate import load_json as load_validation_json
from .decision_stack_validate import validate_decision_stack_artifacts
from .final_memo import (
    generate_final_decision_memo,
    load_json,
    render_final_decision_memo_markdown,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate the final cross-surface architecture decision memo.")
    parser.add_argument("--micro-report", required=True)
    parser.add_argument("--benchmark-matrix", required=False)
    parser.add_argument("--long-context-selector", required=True)
    parser.add_argument("--long-context-execution", required=True)
    parser.add_argument("--training-benchmark", required=True)
    parser.add_argument("--review-plan", required=False)
    parser.add_argument("--validate-audit", required=False)
    parser.add_argument("--validate-review-plan", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    memo = generate_final_decision_memo(
        load_json(args.micro_report),
        load_json(args.long_context_selector),
        load_json(args.long_context_execution),
        load_json(args.training_benchmark),
        load_json(args.review_plan) if args.review_plan else None,
        load_json(args.benchmark_matrix) if args.benchmark_matrix else None,
    )

    validation_review_plan = args.validate_review_plan or args.review_plan
    requested_validation = bool(args.validate_audit or args.validate_review_plan)
    if requested_validation:
        if not args.validate_audit or not validation_review_plan:
            print(
                "ERROR: final_memo_cli validation requires both --validate-audit and a review plan source.",
                file=sys.stderr,
            )
            return 1
        errors = validate_decision_stack_artifacts(
            load_validation_json(args.validate_audit),
            load_validation_json(validation_review_plan),
            memo,
        )
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1

    markdown = render_final_decision_memo_markdown(memo)

    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(memo, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")

    if args.stdout or (not args.artifact_md and not args.artifact_json):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
