from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _safe_float(value: Any) -> float | None:
    return None if value is None else float(value)


def _resolved_by_followup(
    *,
    current_decision: str,
    suggested_decision: str,
    assessments: list[dict[str, Any]],
) -> bool:
    if not assessments:
        return False
    current_support = 0.0
    suggested_support = 0.0
    for assessment in assessments:
        kind = assessment.get("assessment_kind")
        weight = 2.0 if kind == "long_context_followup" else 1.0
        if assessment.get("supports_current_decision") is True:
            label = assessment.get("current_decision") or current_decision
            if label == current_decision:
                current_support += weight
        if assessment.get("supports_candidate_decision") is True:
            label = assessment.get("candidate_decision") or suggested_decision
            if label == current_decision:
                current_support += weight
            if label == suggested_decision:
                suggested_support += weight
    return current_support > 0.0 and current_support >= suggested_support


def _suggest_decision(row: dict[str, Any]) -> tuple[str, list[str]]:
    rules: list[str] = []
    long_quality = _safe_float(row.get("long_context_proxy_quality_at_longest"))
    runtime = _safe_float(row.get("micro_runtime_ratio_mean"))
    benchmark_mean_runtime = _safe_float(row.get("benchmark_mean_ratio_across_grid"))
    benchmark_median_runtime = _safe_float(row.get("benchmark_median_ratio_across_grid"))
    benchmark_worst_runtime = _safe_float(row.get("benchmark_worst_ratio_across_grid"))
    kv_bytes = row.get("micro_estimated_kv_cache_bytes")
    loss_delta = _safe_float(row.get("training_final_loss_delta_mean"))
    consistent_loss = bool(row.get("training_consistent_loss_advantage"))
    consistent_speed = bool(row.get("training_consistent_speed_advantage"))
    systems_mean = benchmark_mean_runtime if benchmark_mean_runtime is not None else runtime
    systems_median = benchmark_median_runtime if benchmark_median_runtime is not None else runtime
    systems_worst = benchmark_worst_runtime if benchmark_worst_runtime is not None else runtime

    if (
        long_quality is not None
        and systems_mean is not None
        and systems_median is not None
        and systems_worst is not None
        and loss_delta is not None
        and long_quality >= 0.95
        and systems_mean <= 1.02
        and systems_median <= 1.1
        and consistent_loss
        and loss_delta < -2.0
    ):
        rules.append("strong blended winner: clears long-context, near-parity systems-sweep, and training-loss gates")
        return "default", rules

    if (
        long_quality is not None
        and systems_mean is not None
        and systems_median is not None
        and loss_delta is not None
        and long_quality >= 0.95
        and systems_mean <= 1.15
        and systems_median <= 1.2
        and (
            consistent_speed
            or kv_bytes == 4096
        )
    ):
        rules.append("keep candidate: clears long-context bar and enough systems/training support for a bounded keep")
        return "secondary", rules

    if (
        long_quality is not None
        and systems_mean is not None
        and loss_delta is not None
        and long_quality >= 0.93
        and (
            (consistent_loss and loss_delta < 0.0)
            or loss_delta < -1.0
            or (consistent_speed and systems_mean <= 1.15)
        )
    ):
        rules.append("promising but incomplete: some quality/training support without enough stable systems evidence")
        return "exploratory", rules

    rules.append("insufficient blended evidence for carry-forward")
    return "drop", rules


def build_concept_decision_audit(
    scorecard: dict[str, Any],
    *,
    followup_assessments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    assessment_rows: dict[str, list[dict[str, Any]]] = {}
    for assessment in (followup_assessments or []):
        assessment_rows.setdefault(assessment["variant"], []).append(assessment)
    rows: list[dict[str, Any]] = []
    mismatches: list[dict[str, Any]] = []
    resolved_mismatches: list[dict[str, Any]] = []
    for row in scorecard["rows"]:
        suggested, triggered_rules = _suggest_decision(row)
        assessments = assessment_rows.get(row["variant"], [])
        resolved_by_followup = (
            row["decision"] != suggested
            and _resolved_by_followup(
                current_decision=row["decision"],
                suggested_decision=suggested,
                assessments=assessments,
            )
        )
        audited = {
            **row,
            "suggested_decision": suggested,
            "decision_matches": row["decision"] == suggested,
            "resolved_by_followup": resolved_by_followup,
            "triggered_rules": triggered_rules,
        }
        rows.append(audited)
        if not audited["decision_matches"]:
            mismatch = {
                "variant": row["variant"],
                "current_decision": row["decision"],
                "suggested_decision": suggested,
                "resolved_by_followup": resolved_by_followup,
                "triggered_rules": triggered_rules,
            }
            mismatches.append(mismatch)
            if resolved_by_followup:
                resolved_mismatches.append(mismatch)

    return {
        "headline": "Architecture Concept Decision Audit",
        "date": scorecard.get("date", "2026-08-09"),
        "summary": {
            "variant_count": len(rows),
            "mismatch_count": len(mismatches),
            "mismatch_variants": [item["variant"] for item in mismatches],
            "resolved_mismatch_count": len(resolved_mismatches),
            "resolved_mismatch_variants": [item["variant"] for item in resolved_mismatches],
            "unresolved_mismatch_count": len(mismatches) - len(resolved_mismatches),
            "unresolved_mismatch_variants": [
                item["variant"] for item in mismatches if not item["resolved_by_followup"]
            ],
        },
        "rows": rows,
        "mismatches": mismatches,
        "resolved_mismatches": resolved_mismatches,
        "notes": [
            "This audit applies explicit decision rules to the concept scorecard and compares the result to the current memo labels.",
            "A mismatch is not automatically a bug; it marks where the current narrative and the current thresholds disagree.",
            "Focused follow-up evidence can mark a raw mismatch as resolved even when the base threshold rule still points elsewhere.",
        ],
    }


def render_concept_decision_audit_markdown(audit: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {audit['headline']}")
    lines.append("")
    lines.append(f"_Updated: {audit['date']}_")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- Variants audited: `{audit['summary']['variant_count']}`")
    lines.append(f"- Decision mismatches: `{audit['summary']['mismatch_count']}`")
    if audit["summary"]["mismatch_variants"]:
        lines.append(
            "- Mismatch variants: " + ", ".join(f"`{name}`" for name in audit["summary"]["mismatch_variants"])
        )
    if audit["summary"].get("resolved_mismatch_variants"):
        lines.append(
            "- Mismatches resolved by focused follow-up: "
            + ", ".join(f"`{name}`" for name in audit["summary"]["resolved_mismatch_variants"])
        )
    if audit["summary"].get("unresolved_mismatch_variants"):
        lines.append(
            "- Unresolved mismatches: "
            + ", ".join(f"`{name}`" for name in audit["summary"]["unresolved_mismatch_variants"])
        )
    lines.append("")
    lines.append("## Decision Matrix")
    lines.append("")
    lines.append("| Variant | Current | Suggested | Match | Follow-up Resolved | Why |")
    lines.append("|---|---|---|---:|---:|---|")
    for row in audit["rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['decision']} | {row['suggested_decision']} | "
            f"{str(bool(row['decision_matches'])).lower()} | {str(bool(row.get('resolved_by_followup', False))).lower()} | "
            f"{'; '.join(row['triggered_rules'])} |"
        )
    lines.append("")
    lines.append("## Notes")
    for note in audit.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Audit current architecture concept decisions against explicit rules.")
    parser.add_argument("--scorecard", required=True)
    parser.add_argument(
        "--followup-assessment",
        dest="followup_assessments",
        action="append",
        help="Optional focused follow-up assessment artifacts to classify raw mismatches as resolved or unresolved.",
    )
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    audit = build_concept_decision_audit(
        load_json(args.scorecard),
        followup_assessments=[load_json(path) for path in (args.followup_assessments or [])],
    )
    markdown = render_concept_decision_audit_markdown(audit)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
