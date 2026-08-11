from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _assessment_weight(assessment: dict[str, Any]) -> float:
    kind = assessment.get("assessment_kind")
    if kind == "long_context_followup":
        return 2.0
    if kind == "training_followup":
        return 1.0
    return 1.0


def _plan_items(row: dict[str, Any]) -> list[str]:
    items: list[str] = []
    variant = row["variant"]
    followup_supports_current = row.get("followup_supports_current_decision") is True
    followup_supports_candidate = row.get("followup_supports_candidate_decision") is True
    followup_conflict = row.get("followup_conflicting_directions") is True
    followup_current_favored = row.get("followup_mixed_but_current_favored") is True
    training_loss_mean = row.get("training_final_loss_delta_mean")
    training_speed_mean = row.get("training_speed_ratio_mean")
    micro_runtime_mean = row.get("micro_runtime_ratio_mean")
    benchmark_worst_ratio = row.get("benchmark_worst_ratio_across_grid")
    benchmark_ratio_range = row.get("benchmark_ratio_range_across_grid")
    long_quality = row.get("long_context_proxy_quality_at_longest")
    micro_kv_bytes = row.get("micro_estimated_kv_cache_bytes")

    if not row.get("decision_matches", True) and not followup_supports_current:
        items.append(
            f"Re-run the carry-forward decision for `{variant}` with a human review of the scorecard and audit mismatch."
        )
    if followup_current_favored:
        items.append(
            f"Focused follow-up evidence is mixed for `{variant}`, but the stronger weighted signal still favors keeping `{row.get('current_decision', row.get('decision'))}` over `{row.get('followup_candidate_decision', row.get('suggested_decision', row.get('decision')))}`."
        )
    elif followup_conflict:
        items.append(
            f"Focused follow-up evidence conflicts for `{variant}`: some surfaces support `{row.get('current_decision', row.get('decision'))}` while others support `{row.get('followup_candidate_decision', row.get('suggested_decision', row.get('decision')))}`."
        )
    elif followup_supports_current:
        items.append(
            f"Focused follow-up evidence already supports keeping `{variant}` at `{row.get('current_decision', row.get('decision'))}`; resolve the mismatch by updating thresholds or gathering non-training evidence."
        )
    elif followup_supports_candidate:
        candidate = row.get("followup_candidate_decision", row.get("suggested_decision", row.get("decision")))
        direction = "promoting" if candidate in {"default", "secondary"} else "moving"
        items.append(
            f"Focused follow-up evidence supports {direction} `{variant}` toward `{candidate}`; review whether the current label should change."
        )
    if long_quality is not None and long_quality < 0.95:
        items.append(
            f"Expand long-context evaluation for `{variant}` with more hard retrieval cases because current longest-context proxy quality is below the strong keep bar."
        )
    if row.get("training_consistent_loss_advantage") is False and training_loss_mean is not None and training_loss_mean > -1.0:
        items.append(
            f"Run a broader training matrix for `{variant}` because the current training-loss signal is weak or unstable."
        )
    if training_speed_mean is not None and training_speed_mean > 1.0 and not row.get("training_consistent_speed_advantage", False):
        items.append(
            f"Profile `{variant}` under a wider training schedule grid because the current training speed signal is not a stable advantage."
        )
    if benchmark_worst_ratio is not None and benchmark_worst_ratio > 1.2:
        items.append(
            f"Recheck `{variant}` on a broader systems sweep because its worst micro benchmark cell regresses above 1.2x baseline."
        )
    if benchmark_ratio_range is not None and benchmark_ratio_range > 0.5:
        items.append(
            f"Treat `{variant}` as scaling-sensitive for now because its micro benchmark ratio swings materially across the current batch/sequence grid."
        )
    if micro_runtime_mean is not None and micro_runtime_mean > 1.1:
        items.append(
            f"Treat `{variant}` as systems-expensive for now and require a stronger quality win before promotion."
        )
    if micro_kv_bytes is not None and micro_kv_bytes >= 8192:
        items.append(
            f"Do not treat `{variant}` as a memory-saving path until a different surface shows a compensating quality gain."
        )
    if not items:
        items.append(
            f"No immediate evidence gap for `{variant}`; keep current label and wait for heavier real-model quality work."
        )
    return items


def build_concept_review_plan(
    scorecard: dict[str, Any],
    audit: dict[str, Any],
    *,
    followup_assessments: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    audit_rows = {row["variant"]: row for row in audit["rows"]}
    assessment_rows: dict[str, list[dict[str, Any]]] = {}
    for assessment in (followup_assessments or []):
        assessment_rows.setdefault(assessment["variant"], []).append(assessment)
    review_rows: list[dict[str, Any]] = []
    priority_variants: list[str] = []
    resolved_mismatch_variants: list[str] = []

    for row in scorecard["rows"]:
        assessments = assessment_rows.get(row["variant"], [])
        audit_row = audit_rows.get(row["variant"], {})
        label_scores: dict[str, float] = {}
        for assessment in assessments:
            weight = _assessment_weight(assessment)
            current_label = assessment.get("current_decision") or row["decision"]
            candidate_label = assessment.get("candidate_decision") or audit_row.get("suggested_decision")
            if assessment.get("supports_current_decision") is True and current_label:
                label_scores[current_label] = label_scores.get(current_label, 0.0) + weight
            if assessment.get("supports_candidate_decision") is True and candidate_label:
                label_scores[candidate_label] = label_scores.get(candidate_label, 0.0) + weight
        distinct_recommendations = list(label_scores.keys())
        current_score = label_scores.get(row["decision"], 0.0)
        alternative_scores = {label: score for label, score in label_scores.items() if label != row["decision"]}
        best_alternative_label = (
            max(
                alternative_scores.items(),
                key=lambda item: (item[1], item[0]),
            )[0]
            if alternative_scores
            else None
        )
        best_alternative_score = alternative_scores.get(best_alternative_label, 0.0) if best_alternative_label else 0.0
        best_label = (
            max(
                label_scores.items(),
                key=lambda item: (item[1], item[0] == row["decision"], item[0]),
            )[0]
            if label_scores
            else None
        )
        supports_current = current_score > 0.0
        supports_candidate = bool(alternative_scores)
        followup_candidate_decision = best_alternative_label
        followup_conflicting = (
            bool(best_alternative_label)
            and current_score > 0.0
            and best_alternative_score > 0.0
            and abs(current_score - best_alternative_score) < 0.75
        )
        followup_current_favored = (
            bool(best_alternative_label)
            and current_score > 0.0
            and best_alternative_score > 0.0
            and current_score >= best_alternative_score + 0.75
        )
        merged = {
            **row,
            **audit_row,
            "followup_supports_current_decision": supports_current,
            "followup_supports_candidate_decision": supports_candidate,
            "followup_conflicting_directions": followup_conflicting,
            "followup_mixed_but_current_favored": followup_current_favored,
            "followup_current_decision": row["decision"],
            "followup_candidate_decision": followup_candidate_decision,
            "followup_label_scores": label_scores,
        }
        items = _plan_items(merged)
        priority = 0
        if merged.get("followup_conflicting_directions") is True:
            priority = 3
        elif merged.get("followup_mixed_but_current_favored") is True:
            priority = 2 if row["decision"] in {"default", "secondary"} else 1
        elif merged.get("followup_supports_candidate_decision") is True and row["decision"] in {"default", "secondary"}:
            priority = 3
        elif not merged.get("decision_matches", True) and merged.get("followup_supports_current_decision") is True:
            priority = 1
            resolved_mismatch_variants.append(row["variant"])
        elif not merged.get("decision_matches", True):
            priority = 3
        elif row["decision"] in {"default", "secondary"} and len(items) > 1:
            priority = 2
        elif row["decision"] == "exploratory":
            priority = 1

        review_row = {
            "variant": row["variant"],
            "current_decision": row["decision"],
            "suggested_decision": (
                row["decision"]
                if merged.get("followup_conflicting_directions") is True
                else row["decision"]
                if merged.get("followup_supports_current_decision") is True
                else merged.get("followup_candidate_decision")
                if merged.get("followup_supports_candidate_decision") is True
                else merged.get("suggested_decision", row["decision"])
            ),
            "decision_matches": merged.get("decision_matches", True),
            "followup_supports_current_decision": merged.get("followup_supports_current_decision"),
            "followup_supports_candidate_decision": merged.get("followup_supports_candidate_decision"),
            "followup_conflicting_directions": merged.get("followup_conflicting_directions"),
            "followup_mixed_but_current_favored": merged.get("followup_mixed_but_current_favored"),
            "followup_candidate_decision": merged.get("followup_candidate_decision"),
            "followup_label_scores": merged.get("followup_label_scores"),
            "priority": priority,
            "next_actions": items,
        }
        review_rows.append(review_row)
        if priority >= 2:
            priority_variants.append(row["variant"])

    review_rows.sort(key=lambda row: (-row["priority"], row["variant"]))

    raw_mismatch_variants = audit["summary"].get("mismatch_variants", [])
    audit_resolved_mismatch_variants = audit["summary"].get("resolved_mismatch_variants", [])
    unresolved_mismatch_variants = audit["summary"].get("unresolved_mismatch_variants", [])

    return {
        "headline": "Architecture Concept Review Plan",
        "date": scorecard.get("date", "2026-08-09"),
        "summary": {
            "priority_variants": priority_variants,
            "mismatch_variants": raw_mismatch_variants,
            "raw_mismatch_variants": raw_mismatch_variants,
            "resolved_mismatch_variants": sorted(set(audit_resolved_mismatch_variants) | set(resolved_mismatch_variants)),
            "unresolved_mismatch_variants": unresolved_mismatch_variants,
            "review_count": len(review_rows),
        },
        "rows": review_rows,
        "notes": [
            "This review plan converts scorecard and audit findings into concrete next experiments or hold decisions.",
            "Higher priority means either an explicit unresolved decision mismatch or a current keep-label with unresolved evidence gaps.",
        ],
    }


def render_concept_review_plan_markdown(plan: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {plan['headline']}")
    lines.append("")
    lines.append(f"_Updated: {plan['date']}_")
    lines.append("")
    lines.append("## Summary")
    if plan["summary"]["priority_variants"]:
        lines.append(
            "- Priority variants: " + ", ".join(f"`{name}`" for name in plan["summary"]["priority_variants"])
        )
    if plan["summary"].get("raw_mismatch_variants"):
        lines.append(
            "- Raw decision mismatches from the audit: "
            + ", ".join(f"`{name}`" for name in plan["summary"]["raw_mismatch_variants"])
        )
    if plan["summary"].get("resolved_mismatch_variants"):
        lines.append(
            "- Resolved mismatches with follow-up support for the current label: "
            + ", ".join(f"`{name}`" for name in plan["summary"]["resolved_mismatch_variants"])
        )
    if plan["summary"].get("unresolved_mismatch_variants"):
        lines.append(
            "- Active unresolved mismatches needing review: "
            + ", ".join(f"`{name}`" for name in plan["summary"]["unresolved_mismatch_variants"])
        )
    lines.append(f"- Review rows: `{plan['summary']['review_count']}`")
    lines.append("")
    lines.append("## Review Queue")
    for row in plan["rows"]:
        lines.append(
            f"- `{row['variant']}`: current `{row['current_decision']}`, suggested `{row['suggested_decision']}`, priority `{row['priority']}`."
        )
        for action in row["next_actions"]:
            lines.append(f"  - {action}")
    lines.append("")
    lines.append("## Notes")
    for note in plan.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a concrete review plan from architecture scorecard and audit artifacts.")
    parser.add_argument("--scorecard", required=True)
    parser.add_argument("--audit", required=True)
    parser.add_argument(
        "--followup-assessment",
        dest="followup_assessments",
        action="append",
        help="Optional focused follow-up assessment artifacts to fold into the review queue. Can be passed multiple times.",
    )
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    plan = build_concept_review_plan(
        load_json(args.scorecard),
        load_json(args.audit),
        followup_assessments=[load_json(path) for path in (args.followup_assessments or [])],
    )
    markdown = render_concept_review_plan_markdown(plan)
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
