from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _training_row(matrix: dict[str, Any], variant: str) -> dict[str, Any]:
    rows = {row["variant"]: row for row in matrix.get("variant_trends", [])}
    if variant not in rows:
        raise ValueError(f"missing training trend row for {variant}")
    return rows[variant]


def _benchmark_row(matrix: dict[str, Any], variant: str) -> dict[str, Any]:
    rows = {row["variant"]: row for row in matrix.get("variant_summary_rows", [])}
    if variant not in rows:
        raise ValueError(f"missing benchmark summary row for {variant}")
    return rows[variant]


def _long_context_rows(execution: dict[str, Any], variant: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if execution.get("selected_variant_kind") != variant:
        raise ValueError(
            f"long-context execution selected {execution.get('selected_variant_kind')}, expected {variant}"
        )
    summary = execution.get("focused_compare_summary")
    if not summary:
        raise ValueError("long-context execution is missing focused_compare_summary")
    return summary["selected_bucket"], summary["baseline_bucket"]


def build_compressed_attention_promotion_assessment(
    training_matrix: dict[str, Any],
    benchmark_matrix: dict[str, Any],
    long_context_execution: dict[str, Any],
) -> dict[str, Any]:
    variant = "compressed_attention"
    training = _training_row(training_matrix, variant)
    benchmark = _benchmark_row(benchmark_matrix, variant)
    selected_bucket, baseline_bucket = _long_context_rows(long_context_execution, variant)

    quality_delta = (
        selected_bucket["mean_proxy_pass_probability"] - baseline_bucket["mean_proxy_pass_probability"]
    )
    pass_rate_delta = selected_bucket["proxy_pass_rate"] - baseline_bucket["proxy_pass_rate"]
    kv_saving_ratio = long_context_execution["delta"]["kv_cache_saving_ratio_vs_baseline"]

    long_context_pass = (
        selected_bucket["proxy_pass_rate"] >= 1.0
        and quality_delta > -0.05
        and kv_saving_ratio > 0.0
    )
    training_pass = (
        training["all_matrix_rows_finite"]
        and training["consistent_loss_advantage"]
        and training["final_loss_delta_vs_baseline_mean"] < 0.0
    )
    benchmark_pass = (
        benchmark["mean_ratio_across_grid"] <= 1.0
        and benchmark["worst_ratio_across_grid"] <= 1.10
    )

    signals: list[str] = []
    risks: list[str] = []

    if long_context_pass:
        signals.append("hardest available long-context proxy bucket stays at full pass rate with acceptable quality loss")
    else:
        risks.append("long-context proxy evidence is not strong enough to close the promotion decision")
    if kv_saving_ratio > 0.0:
        signals.append("long-context execution still saves KV cache relative to baseline")

    if training_pass:
        signals.append("broader training follow-up keeps a consistent loss advantage across the sampled grid")
    else:
        risks.append("training follow-up does not yet show a consistent loss advantage across the sampled grid")
    if not training["all_matrix_rows_finite"]:
        risks.append("training follow-up contains non-finite rows")
    if not training["consistent_speed_advantage"]:
        risks.append("training speed advantage is not consistent across the follow-up grid")

    if benchmark_pass:
        signals.append("systems sweep stays near or better than baseline on both mean and worst-case runtime")
    else:
        risks.append("systems sweep still shows too much runtime regression for a default promotion")

    recommendation = "promote" if long_context_pass and training_pass and benchmark_pass else "defer"
    conclusion = (
        "Compressed attention is ready for promotion to the next heavier experiment stage."
        if recommendation == "promote"
        else "Compressed attention should remain the default carry-forward candidate, but promotion should be deferred until the weaker evidence surfaces are widened or improved."
    )

    return {
        "headline": "Compressed Attention Promotion Assessment",
        "assessment_kind": "compressed_attention_promotion",
        "date": "2026-08-09",
        "variant": variant,
        "recommendation": recommendation,
        "conclusion": conclusion,
        "gates": {
            "long_context_pass": long_context_pass,
            "training_pass": training_pass,
            "benchmark_pass": benchmark_pass,
        },
        "signals": signals,
        "risks": risks,
        "long_context": {
            "quality_delta_vs_baseline": quality_delta,
            "pass_rate_delta_vs_baseline": pass_rate_delta,
            "kv_cache_saving_ratio_vs_baseline": kv_saving_ratio,
            "selected_bucket": selected_bucket,
            "baseline_bucket": baseline_bucket,
        },
        "training": training,
        "benchmark": benchmark,
    }


def render_compressed_attention_promotion_assessment_markdown(assessment: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {assessment['headline']}")
    lines.append("")
    lines.append(f"_Updated: {assessment['date']}_")
    lines.append("")
    lines.append("## Recommendation")
    lines.append(f"- Recommendation: `{assessment['recommendation']}`")
    lines.append(f"- {assessment['conclusion']}")
    lines.append("")
    lines.append("## Gate Status")
    lines.append(f"- Long-context gate: `{str(bool(assessment['gates']['long_context_pass'])).lower()}`")
    lines.append(f"- Training gate: `{str(bool(assessment['gates']['training_pass'])).lower()}`")
    lines.append(f"- Systems gate: `{str(bool(assessment['gates']['benchmark_pass'])).lower()}`")
    lines.append("")
    lines.append("## Positive Signals")
    for signal in assessment["signals"]:
        lines.append(f"- {signal}")
    lines.append("")
    lines.append("## Risks")
    for risk in assessment["risks"]:
        lines.append(f"- {risk}")
    lines.append("")
    long_context = assessment["long_context"]
    training = assessment["training"]
    benchmark = assessment["benchmark"]
    lines.append("## Evidence Snapshot")
    lines.append("")
    lines.append("| Surface | Key Metrics |")
    lines.append("|---|---|")
    lines.append(
        f"| Long-context | quality delta `{long_context['quality_delta_vs_baseline']:.3f}`; pass-rate delta `{long_context['pass_rate_delta_vs_baseline']:.3f}`; KV saving `{long_context['kv_cache_saving_ratio_vs_baseline']:.3f}` |"
    )
    lines.append(
        f"| Training | mean loss delta `{training['final_loss_delta_vs_baseline_mean']:.3f}`; loss range `{training['final_loss_delta_vs_baseline_range']:.3f}`; mean speed ratio `{training['mean_step_ms_ratio_vs_baseline_mean']:.3f}`; consistent loss `{str(bool(training['consistent_loss_advantage'])).lower()}` |"
    )
    lines.append(
        f"| Systems | mean runtime ratio `{benchmark['mean_ratio_across_grid']:.3f}`; worst runtime ratio `{benchmark['worst_ratio_across_grid']:.3f}`; KV bytes `{benchmark['estimated_kv_cache_bytes']}` |"
    )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assess whether compressed_attention has enough evidence to justify the next heavier experiment-stage promotion."
    )
    parser.add_argument("--training-matrix", required=True)
    parser.add_argument("--benchmark-matrix", required=True)
    parser.add_argument("--long-context-execution", required=True)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    assessment = build_compressed_attention_promotion_assessment(
        load_json(args.training_matrix),
        load_json(args.benchmark_matrix),
        load_json(args.long_context_execution),
    )
    markdown = render_compressed_attention_promotion_assessment_markdown(assessment)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(assessment, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
