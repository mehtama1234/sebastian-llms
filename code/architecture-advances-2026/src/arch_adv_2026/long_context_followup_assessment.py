from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _longest_bucket_rows(compare: dict[str, Any]) -> dict[str, dict[str, Any]]:
    longest = max(compare["filler_repeat_values"])
    return {
        row["variant_kind"]: row
        for row in compare["variant_buckets"]
        if row["filler_repeats"] == longest
    }


def build_long_context_followup_assessment(
    compare: dict[str, Any],
    *,
    variant: str,
    current_decision: str,
    candidate_decision: str,
) -> dict[str, Any]:
    rows = _longest_bucket_rows(compare)
    baseline = rows["baseline"]
    target = rows[variant]

    quality_delta = target["mean_proxy_pass_probability"] - baseline["mean_proxy_pass_probability"]
    pass_rate_delta = target["proxy_pass_rate"] - baseline["proxy_pass_rate"]
    kv_bytes_delta = target["estimated_kv_cache_bytes_at_max_seq"] - baseline["estimated_kv_cache_bytes_at_max_seq"]
    kv_saving_ratio = target["estimated_kv_saving_ratio_at_max_seq"]

    supports_current = False
    supports_candidate = False
    reasons: list[str] = []

    if target["proxy_pass_rate"] < 1.0:
        reasons.append("proxy pass rate drops below baseline at the longest context")
        supports_current = current_decision in {"exploratory", "drop"}
    if quality_delta <= -0.05:
        reasons.append("proxy quality loss versus baseline is large")
        supports_current = supports_current or current_decision in {"exploratory", "drop"}
    if kv_saving_ratio > 0.0:
        reasons.append("variant saves KV cache at the longest context")
    if kv_bytes_delta < 0:
        reasons.append("variant reduces longest-context KV bytes versus baseline")
    if quality_delta > -0.03 and target["proxy_pass_rate"] >= 1.0 and kv_saving_ratio > 0.0:
        reasons.append("quality stays close to baseline while KV cost drops materially")
        supports_candidate = True

    conclusion = (
        f"Focused long-context follow-up for `{variant}` supports the current `{current_decision}` label over the candidate "
        f"`{candidate_decision}` label."
        if supports_current and not supports_candidate
        else (
            f"Focused long-context follow-up for `{variant}` supports the candidate `{candidate_decision}` label over the current "
            f"`{current_decision}` label."
            if supports_candidate and not supports_current
            else (
                f"Focused long-context follow-up for `{variant}` is mixed: it does not cleanly resolve `{current_decision}` versus "
                f"`{candidate_decision}`."
            )
        )
    )

    return {
        "headline": "Focused Long-Context Follow-up Assessment",
        "assessment_kind": "long_context_followup",
        "date": "2026-08-09",
        "variant": variant,
        "current_decision": current_decision,
        "candidate_decision": candidate_decision,
        "supports_current_decision": supports_current,
        "supports_candidate_decision": supports_candidate,
        "conclusion": conclusion,
        "baseline_row": baseline,
        "target_row": target,
        "quality_delta_vs_baseline": quality_delta,
        "pass_rate_delta_vs_baseline": pass_rate_delta,
        "kv_bytes_delta_vs_baseline": kv_bytes_delta,
        "reasons": reasons,
    }


def render_long_context_followup_assessment_markdown(assessment: dict[str, Any]) -> str:
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
    lines.append("## Longest-Context Comparison")
    lines.append("")
    lines.append("| Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio |")
    lines.append("|---|---:|---:|---:|---:|")
    for label, row in [("baseline", assessment["baseline_row"]), (assessment["variant"], assessment["target_row"])]:
        lines.append(
            f"| `{label}` | {row['mean_proxy_pass_probability']:.3f} | {row['proxy_pass_rate']:.3f} | "
            f"{int(row['estimated_kv_cache_bytes_at_max_seq'])} | {row['estimated_kv_saving_ratio_at_max_seq']:.3f} |"
        )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Assess one variant's longest-context proxy behavior against baseline.")
    parser.add_argument("--compare", required=True)
    parser.add_argument("--variant", required=True)
    parser.add_argument("--current-decision", required=True)
    parser.add_argument("--candidate-decision", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = build_long_context_followup_assessment(
        load_json(args.compare),
        variant=args.variant,
        current_decision=args.current_decision,
        candidate_decision=args.candidate_decision,
    )
    markdown = render_long_context_followup_assessment_markdown(assessment)
    if args.artifact_json:
        path = Path(args.artifact_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        path = Path(args.artifact_md)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
