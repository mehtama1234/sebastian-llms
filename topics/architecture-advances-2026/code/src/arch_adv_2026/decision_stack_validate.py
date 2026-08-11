from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_decision_stack_artifacts(
    audit: dict[str, Any],
    review_plan: dict[str, Any],
    final_memo: dict[str, Any],
) -> list[str]:
    errors: list[str] = []

    audit_summary = audit.get("summary", {})
    review_summary = review_plan.get("summary", {})
    memo_review_summary = final_memo.get("evidence", {}).get("review_summary", {})
    memo_summary_lines = final_memo.get("summary_lines", [])
    evidence_matrix = final_memo.get("evidence_matrix", [])

    raw_mismatches = audit_summary.get("mismatch_variants", [])
    resolved_mismatches = audit_summary.get("resolved_mismatch_variants", [])
    unresolved_mismatches = audit_summary.get("unresolved_mismatch_variants", [])
    raw_mismatch_set = set(raw_mismatches)
    resolved_mismatch_set = set(resolved_mismatches)
    unresolved_mismatch_set = set(unresolved_mismatches)
    audit_row_variants = [row.get("variant") for row in audit.get("rows", [])]
    review_row_variants = [row.get("variant") for row in review_plan.get("rows", [])]
    memo_matrix_variants = [row.get("variant") for row in evidence_matrix]

    if audit_summary.get("variant_count") is not None and audit_summary.get("variant_count") != len(audit.get("rows", [])):
        errors.append("audit variant_count does not match the number of audit rows")
    if audit_summary.get("mismatch_count") is not None and audit_summary.get("mismatch_count") != len(raw_mismatches):
        errors.append("audit mismatch_count does not match mismatch_variants")
    if audit_summary.get("resolved_mismatch_count") is not None and audit_summary.get("resolved_mismatch_count") != len(
        resolved_mismatches
    ):
        errors.append("audit resolved_mismatch_count does not match resolved_mismatch_variants")
    if audit_summary.get("unresolved_mismatch_count") is not None and audit_summary.get(
        "unresolved_mismatch_count"
    ) != len(unresolved_mismatches):
        errors.append("audit unresolved_mismatch_count does not match unresolved_mismatch_variants")
    if len(audit_row_variants) != len(set(audit_row_variants)):
        errors.append("audit rows contain duplicate variant entries")

    if resolved_mismatch_set - raw_mismatch_set:
        errors.append("audit resolved mismatches must be a subset of the raw mismatch variants")
    if unresolved_mismatch_set - raw_mismatch_set:
        errors.append("audit unresolved mismatches must be a subset of the raw mismatch variants")
    if resolved_mismatch_set & unresolved_mismatch_set:
        errors.append("audit resolved and unresolved mismatches must be disjoint")
    if raw_mismatch_set != resolved_mismatch_set | unresolved_mismatch_set:
        errors.append("audit raw mismatches must equal resolved plus unresolved mismatches")

    if review_summary.get("raw_mismatch_variants", review_summary.get("mismatch_variants", [])) != raw_mismatches:
        errors.append("review plan raw mismatches do not match the audit mismatch variants")
    if review_summary.get("resolved_mismatch_variants", []) != resolved_mismatches:
        errors.append("review plan resolved mismatches do not match the audit resolved mismatches")
    if review_summary.get("unresolved_mismatch_variants", []) != unresolved_mismatches:
        errors.append("review plan unresolved mismatches do not match the audit unresolved mismatches")

    if memo_review_summary.get("raw_mismatch_variants", []) != review_summary.get(
        "raw_mismatch_variants",
        review_summary.get("mismatch_variants", []),
    ):
        errors.append("final memo raw mismatches do not match the review plan")
    if memo_review_summary.get("resolved_mismatch_variants", []) != review_summary.get("resolved_mismatch_variants", []):
        errors.append("final memo resolved mismatches do not match the review plan")
    if memo_review_summary.get("unresolved_mismatch_variants", []) != review_summary.get(
        "unresolved_mismatch_variants", []
    ):
        errors.append("final memo unresolved mismatches do not match the review plan")
    if memo_review_summary.get("priority_variants", []) != review_summary.get("priority_variants", []):
        errors.append("final memo review priorities do not match the review plan")

    expected_priority_variants = [
        row["variant"]
        for row in review_plan.get("rows", [])
        if row.get("priority", 0) >= 2
    ]
    if review_summary.get("priority_variants", []) != expected_priority_variants:
        errors.append("review plan priority variants do not match the rows marked priority >= 2")

    unresolved_summary_present = any(
        str(line).startswith("Active unresolved decision mismatches still needing review: ")
        for line in memo_summary_lines
    )
    if unresolved_mismatches and not unresolved_summary_present:
        errors.append("final memo summary is missing the active unresolved mismatch line")
    if not unresolved_mismatches and unresolved_summary_present:
        errors.append("final memo summary includes an unresolved mismatch line when none are active")

    priority_summary_present = any(
        str(line).startswith("Focused follow-up review priority variants: ")
        for line in memo_summary_lines
    )
    if review_summary.get("priority_variants") and not priority_summary_present:
        errors.append("final memo summary is missing the focused review priority line")
    if review_summary.get("review_count") is not None and review_summary.get("review_count") != len(review_plan.get("rows", [])):
        errors.append("review plan review_count does not match the number of review rows")
    if len(review_row_variants) != len(set(review_row_variants)):
        errors.append("review plan rows contain duplicate variant entries")

    if len(memo_matrix_variants) != len(set(memo_matrix_variants)):
        errors.append("final memo evidence_matrix contains duplicate variant entries")

    memo_partition_variants = [
        final_memo.get("default_carry_forward_variant"),
        *final_memo.get("secondary_variants", []),
        *final_memo.get("exploratory_variants", []),
        *final_memo.get("drop_for_now_variants", []),
    ]
    memo_partition_set = set(memo_partition_variants)
    if len(memo_partition_variants) != len(memo_partition_set):
        errors.append("final memo carry-forward partition contains duplicate variant entries")
    if set(memo_matrix_variants) != memo_partition_set:
        errors.append("final memo evidence_matrix variants do not match the carry-forward partition")
    if audit_row_variants and set(memo_matrix_variants) != set(audit_row_variants):
        errors.append("final memo variants do not match the audit row variants")
    if review_row_variants and set(memo_matrix_variants) != set(review_row_variants):
        errors.append("final memo variants do not match the review-plan row variants")

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that audit, review-plan, and final-memo artifacts agree on decision-stack mismatch state."
    )
    parser.add_argument("--audit", required=True)
    parser.add_argument("--review-plan", required=True)
    parser.add_argument("--final-memo", required=True)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors = validate_decision_stack_artifacts(
        load_json(args.audit),
        load_json(args.review_plan),
        load_json(args.final_memo),
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.stdout:
        print("decision stack artifacts are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
