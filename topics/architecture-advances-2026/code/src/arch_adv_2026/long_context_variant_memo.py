from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a markdown decision memo from the long-context variant proxy selector."
    )
    parser.add_argument("--selector-artifact", required=True)
    parser.add_argument("--report-artifact", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def generate_long_context_variant_memo(selector: dict[str, Any], report: dict[str, Any] | None = None) -> dict[str, Any]:
    recommendations = selector["recommendations"]
    quality = recommendations["quality"]
    memory = recommendations["memory"]
    quality_preserving_memory = recommendations["quality_preserving_memory"]
    balanced = recommendations["balanced"]
    policy = selector["selection_policy"]

    summary_lines = [
        f"Best longest-context proxy quality: `{quality['variant_kind']}` ({quality['mean_proxy_pass_probability']:.3f}).",
        f"Best longest-context KV savings inside the quality bar: `{memory['variant_kind']}` "
        f"({int(memory['estimated_kv_cache_bytes_at_max_seq'])} bytes, saving ratio {memory['estimated_kv_saving_ratio_at_max_seq']:.3f}).",
        f"Best overall carry-forward candidate from this proxy selector: `{quality_preserving_memory['variant_kind']}`.",
        f"Quality threshold used for memory-preserving picks: `{policy['minimum_proxy_quality']:.3f}`.",
    ]

    recommendation_lines = [
        f"Carry forward `{quality_preserving_memory['variant_kind']}` as the default long-context efficiency candidate for the next heavier experiment tier.",
        f"Keep `{quality['variant_kind']}` as the quality ceiling reference for proxy long-context behavior.",
        f"Keep `{memory['variant_kind']}` as the aggressive memory-reduction candidate when KV footprint dominates the requirement.",
    ]
    if balanced["variant_kind"] != quality_preserving_memory["variant_kind"]:
        recommendation_lines.append(
            f"Track `{balanced['variant_kind']}` separately as the lowest-parameter quality-preserving alternative."
        )
    if policy["used_fallback_rows"]:
        recommendation_lines.append(
            "The selector fell back to all variants because none cleared the requested proxy-quality threshold; treat this memo as exploratory only."
        )
    else:
        recommendation_lines.append(
            "The selector did not need fallback, so the memory-oriented recommendation already clears the requested proxy-quality threshold."
        )

    return {
        "headline": "Long-context variant proxy decision memo",
        "summary_lines": summary_lines,
        "recommendations": recommendation_lines,
        "selector_policy": policy,
        "supporting_recommendations": recommendations,
        "report_context_available": report is not None,
    }


def render_long_context_variant_memo_markdown(
    memo: dict[str, Any],
    selector: dict[str, Any],
    report: dict[str, Any] | None = None,
) -> str:
    lines: list[str] = []
    lines.append(f"# {memo['headline']}")
    lines.append("")
    lines.append("## Bottom line")
    for line in memo["summary_lines"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Recommendations")
    for line in memo["recommendations"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Selector Picks")
    lines.append("")
    lines.append("| Objective | Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio | Total Params |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for objective, row in selector["recommendations"].items():
        lines.append(
            f"| `{objective}` | `{row['variant_kind']}` | {row['mean_proxy_pass_probability']:.3f} | "
            f"{row['proxy_pass_rate']:.3f} | {int(row['estimated_kv_cache_bytes_at_max_seq'])} | "
            f"{row['estimated_kv_saving_ratio_at_max_seq']:.3f} | {int(row['estimated_total_params'])} |"
        )
    lines.append("")
    lines.append("## Policy")
    policy = selector["selection_policy"]
    lines.append(f"- Longest filler bucket: `{policy['longest_context_filler_repeats']}`")
    lines.append(f"- Minimum proxy quality: `{policy['minimum_proxy_quality']:.3f}`")
    lines.append(f"- Acceptable rows: `{policy['acceptable_row_count']}` / `{policy['total_row_count']}`")
    lines.append(f"- Used fallback rows: `{policy['used_fallback_rows']}`")
    if report is not None:
        lines.append("")
        lines.append("## Report Context")
        lines.append(f"- Variant count in report: `{len(report.get('variant_configs', []))}`")
        lines.append(f"- Cases per length: `{report.get('cases_per_length')}`")
        lines.append(f"- Sweep runs: `{report.get('sweep_runs')}`")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    selector = load_json(args.selector_artifact)
    report = load_json(args.report_artifact) if args.report_artifact else None
    memo = generate_long_context_variant_memo(selector, report)
    markdown = render_long_context_variant_memo_markdown(memo, selector, report)

    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps({"memo": memo, "selector": selector, "report": report}, indent=2) + "\n", encoding="utf-8")

    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")

    if args.stdout or (not args.artifact_md and not args.artifact_json):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
