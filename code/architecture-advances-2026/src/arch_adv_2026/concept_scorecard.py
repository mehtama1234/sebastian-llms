from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _decision_by_variant(final_memo: dict[str, Any]) -> dict[str, str]:
    decisions: dict[str, str] = {}
    decisions[final_memo["default_carry_forward_variant"]] = "default"
    for variant in final_memo.get("secondary_variants", []):
        decisions[variant] = "secondary"
    for variant in final_memo.get("exploratory_variants", []):
        decisions[variant] = "exploratory"
    for variant in final_memo.get("drop_for_now_variants", []):
        decisions[variant] = "drop"
    return decisions


def _longest_context_rows(compare: dict[str, Any]) -> dict[str, dict[str, Any]]:
    buckets = compare.get("variant_buckets", [])
    if not buckets:
        return {}
    longest_filler = max(bucket["filler_repeats"] for bucket in buckets)
    return {
        bucket["variant_kind"]: bucket
        for bucket in buckets
        if bucket["filler_repeats"] == longest_filler
    }


def _training_rows(training: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if "variant_trends" in training:
        return {row["variant"]: row for row in training["variant_trends"]}
    if "variant_rows" in training:
        return {row["variant"]: row for row in training["variant_rows"]}
    return {}


def _benchmark_rows(benchmark_matrix: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not benchmark_matrix:
        return {}
    return {row["variant"]: row for row in benchmark_matrix.get("variant_summary_rows", [])}


def _summary_lines(rows: list[dict[str, Any]]) -> list[str]:
    default_rows = [row for row in rows if row["decision"] == "default"]
    secondary_rows = [row for row in rows if row["decision"] == "secondary"]
    exploratory_rows = [row for row in rows if row["decision"] == "exploratory"]

    lines: list[str] = []
    if default_rows:
        row = default_rows[0]
        lines.append(
            f"Default carry-forward concept: `{row['variant']}` with long-context proxy quality "
            f"`{row['long_context_proxy_quality_at_longest']:.3f}` and training loss delta "
            f"`{row['training_final_loss_delta_mean']:.3f}`."
        )
        if row.get("benchmark_mean_ratio_across_grid") is not None:
            lines.append(
                f"Default systems sweep mean runtime ratio across the micro grid: `{row['benchmark_mean_ratio_across_grid']:.3f}` "
                f"(worst cell `{row['benchmark_worst_ratio_across_grid']:.3f}`)."
            )
    if secondary_rows:
        lines.append(
            "Secondary keep set: " + ", ".join(f"`{row['variant']}`" for row in secondary_rows) + "."
        )
    if exploratory_rows:
        lines.append(
            "Exploratory-only set: " + ", ".join(f"`{row['variant']}`" for row in exploratory_rows) + "."
        )
    return lines


def build_concept_scorecard(
    micro_report: dict[str, Any],
    long_context_compare: dict[str, Any],
    training_matrix: dict[str, Any],
    final_memo: dict[str, Any],
    benchmark_matrix: dict[str, Any] | None = None,
) -> dict[str, Any]:
    decision_map = _decision_by_variant(final_memo)
    long_context_rows = _longest_context_rows(long_context_compare)
    training_rows = _training_rows(training_matrix)
    benchmark_rows = _benchmark_rows(benchmark_matrix)

    rows: list[dict[str, Any]] = []
    for micro_row in micro_report["variant_rows"]:
        variant = micro_row["variant"]
        long_row = long_context_rows.get(variant, {})
        training_row = training_rows.get(variant, {})
        benchmark_row = benchmark_rows.get(variant, {})
        rows.append(
            {
                "variant": variant,
                "name": micro_row["name"],
                "decision": decision_map.get(variant, "unclassified"),
                "micro_runtime_ratio_mean": micro_row["mean_ratio_vs_baseline_mean"],
                "micro_runtime_ratio_stdev": micro_row["mean_ratio_vs_baseline_stdev"],
                "micro_estimated_flops": micro_row["estimated_flops"],
                "micro_estimated_kv_cache_bytes": micro_row["estimated_kv_cache_bytes"],
                "micro_estimated_kv_cache_bytes_saved": micro_row["estimated_kv_cache_bytes_saved"],
                "long_context_proxy_quality_at_longest": long_row.get("mean_proxy_pass_probability"),
                "long_context_proxy_pass_rate_at_longest": long_row.get("proxy_pass_rate"),
                "long_context_kv_saving_ratio_at_max_seq": long_row.get("estimated_kv_saving_ratio_at_max_seq"),
                "long_context_cases_at_longest": long_row.get("num_cases"),
                "training_speed_ratio_mean": training_row.get("mean_step_ms_ratio_vs_baseline_mean"),
                "training_speed_ratio_range": training_row.get("mean_step_ms_ratio_vs_baseline_range"),
                "training_consistent_speed_advantage": training_row.get("consistent_speed_advantage"),
                "training_speed_win_rate": training_row.get("fastest_step_win_rate"),
                "training_final_loss_delta_mean": training_row.get("final_loss_delta_vs_baseline_mean"),
                "training_final_loss_delta_range": training_row.get("final_loss_delta_vs_baseline_range"),
                "training_consistent_loss_advantage": training_row.get("consistent_loss_advantage"),
                "training_loss_win_rate": training_row.get("lowest_final_loss_delta_win_rate"),
                "training_all_finite": training_row.get("all_matrix_rows_finite", training_row.get("all_runs_finite")),
                "benchmark_mean_ratio_across_grid": benchmark_row.get("mean_ratio_across_grid"),
                "benchmark_median_ratio_across_grid": benchmark_row.get("median_ratio_across_grid"),
                "benchmark_best_ratio_across_grid": benchmark_row.get("best_ratio_across_grid"),
                "benchmark_worst_ratio_across_grid": benchmark_row.get("worst_ratio_across_grid"),
                "benchmark_ratio_range_across_grid": benchmark_row.get("ratio_range_across_grid"),
            }
        )

    decision_order = {"default": 0, "secondary": 1, "exploratory": 2, "drop": 3, "unclassified": 4}
    rows.sort(key=lambda row: (decision_order.get(row["decision"], 99), row["variant"]))

    return {
        "headline": "Architecture Concept Scorecard",
        "date": final_memo.get("date", "2026-08-09"),
        "baseline": micro_report["baseline"],
        "benchmark_matrix_coverage": benchmark_matrix.get("baseline") if benchmark_matrix else None,
        "long_context_filler_values": long_context_compare.get("filler_repeat_values", []),
        "training_matrix_coverage": {
            "seq_lens": training_matrix.get("seq_lens", []),
            "steps_list": training_matrix.get("steps_list", []),
            "seeds": training_matrix.get("seeds", []),
        },
        "summary_lines": _summary_lines(rows),
        "rows": rows,
        "notes": [
            "This scorecard aligns systems, proxy long-context, and training evidence per architecture concept.",
            "Decision labels come from the final architecture memo so the per-concept rows match the current carry-forward call.",
        ],
    }


def render_concept_scorecard_markdown(scorecard: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {scorecard['headline']}")
    lines.append("")
    lines.append(f"_Updated: {scorecard['date']}_")
    lines.append("")
    lines.append("## Bottom line")
    for line in scorecard["summary_lines"]:
        lines.append(f"- {line}")
    lines.append("")
    lines.append("## Concept Matrix")
    lines.append("")
    lines.append(
        "| Variant | Decision | Micro Runtime | Sweep Mean Ratio | Sweep Median Ratio | Sweep Worst Ratio | Micro KV Bytes | Long Proxy Quality | Long Pass Rate | "
        "Training Loss Delta | Training Loss Range | Consistent Loss | Training Speed Ratio | Consistent Speed |"
    )
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in scorecard["rows"]:
        sweep_mean = (
            f"{row['benchmark_mean_ratio_across_grid']:.3f}"
            if row.get("benchmark_mean_ratio_across_grid") is not None
            else "n/a"
        )
        sweep_median = (
            f"{row['benchmark_median_ratio_across_grid']:.3f}"
            if row.get("benchmark_median_ratio_across_grid") is not None
            else "n/a"
        )
        sweep_worst = (
            f"{row['benchmark_worst_ratio_across_grid']:.3f}"
            if row.get("benchmark_worst_ratio_across_grid") is not None
            else "n/a"
        )
        lines.append(
            f"| `{row['variant']}` | {row['decision']} | {row['micro_runtime_ratio_mean']:.3f} | "
            f"{sweep_mean} | {sweep_median} | {sweep_worst} | {row['micro_estimated_kv_cache_bytes']} | {row['long_context_proxy_quality_at_longest']:.3f} | "
            f"{row['long_context_proxy_pass_rate_at_longest']:.3f} | {row['training_final_loss_delta_mean']:.3f} | "
            f"{row['training_final_loss_delta_range']:.3f} | {str(bool(row['training_consistent_loss_advantage'])).lower()} | "
            f"{row['training_speed_ratio_mean']:.3f} | {str(bool(row['training_consistent_speed_advantage'])).lower()} |"
        )
    lines.append("")
    lines.append("## Coverage")
    lines.append(
        f"- Micro baseline: `{scorecard['baseline']['name']}` with sequence length `{scorecard['baseline']['seq_len']}`."
    )
    lines.append(
        f"- Long-context filler repeats: `{scorecard['long_context_filler_values']}`."
    )
    lines.append(
        f"- Training matrix coverage: seq_lens `{scorecard['training_matrix_coverage']['seq_lens']}`, "
        f"steps `{scorecard['training_matrix_coverage']['steps_list']}`, seeds `{scorecard['training_matrix_coverage']['seeds']}`."
    )
    if scorecard.get("benchmark_matrix_coverage"):
        benchmark = scorecard["benchmark_matrix_coverage"]
        lines.append(
            f"- Benchmark matrix coverage: batch sizes `{benchmark['batch_sizes']}`, seq_lens `{benchmark['seq_lens']}`, "
            f"measured runs `{benchmark['measured_runs']}`, report runs `{benchmark['report_runs']}`."
        )
    for note in scorecard.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a per-concept architecture scorecard across all evidence surfaces.")
    parser.add_argument("--micro-report", required=True)
    parser.add_argument("--long-context-compare", required=True)
    parser.add_argument("--training-matrix", required=True)
    parser.add_argument("--final-memo", required=True)
    parser.add_argument("--benchmark-matrix", required=False)
    parser.add_argument("--artifact-json", required=False)
    parser.add_argument("--artifact-md", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    scorecard = build_concept_scorecard(
        load_json(args.micro_report),
        load_json(args.long_context_compare),
        load_json(args.training_matrix),
        load_json(args.final_memo),
        load_json(args.benchmark_matrix) if args.benchmark_matrix else None,
    )
    markdown = render_concept_scorecard_markdown(scorecard)
    if args.artifact_json:
        json_path = Path(args.artifact_json)
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(scorecard, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        md_path = Path(args.artifact_md)
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
