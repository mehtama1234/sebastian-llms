from __future__ import annotations

from typing import Any


def _best_by(rows: list[dict[str, Any]], key: str, reverse: bool = False) -> dict[str, Any]:
    return sorted(rows, key=lambda row: row[key], reverse=reverse)[0]


def generate_decision_memo(report: dict[str, Any]) -> dict[str, Any]:
    rows = report["variant_rows"]
    fastest = _best_by(rows, "mean_ratio_vs_baseline_mean")
    lowest_flops = _best_by(rows, "estimated_flops")
    lowest_kv = _best_by(rows, "estimated_kv_cache_bytes")
    highest_cost = _best_by(rows, "mean_ratio_vs_baseline_mean", reverse=True)

    summary_lines = [
        f"Fastest variant on the aggregated micro benchmark: `{fastest['variant']}` ({fastest['mean_ratio_vs_baseline_mean']:.3f}x baseline mean time, stdev {fastest['mean_ratio_vs_baseline_stdev']:.3f}).",
        f"Lowest estimated FLOPs: `{lowest_flops['variant']}` ({lowest_flops['estimated_flops']}).",
        f"Lowest estimated KV cache: `{lowest_kv['variant']}` ({lowest_kv['estimated_kv_cache_bytes']} bytes).",
        f"Most expensive timing direction on this aggregated micro setup: `{highest_cost['variant']}` ({highest_cost['mean_ratio_vs_baseline_mean']:.3f}x baseline mean time, stdev {highest_cost['mean_ratio_vs_baseline_stdev']:.3f}).",
    ]

    recommendations: list[str] = []
    if lowest_kv["variant"] == "kv_sharing":
        recommendations.append(
            "Use `kv_sharing` when the main constraint is KV-cache footprint rather than absolute lowest estimated FLOPs."
        )
    if lowest_flops["variant"] == "compressed_attention":
        recommendations.append(
            "Use `compressed_attention` when the main goal is reducing attention-side compute and KV storage together."
        )
    if lowest_kv["variant"] == "history_compression" or lowest_flops["variant"] == "history_compression":
        recommendations.append(
            "Use `history_compression` when long-context cost is dominated by old tokens and you want a recent-window plus compressed-history tradeoff."
        )
    if fastest["variant"] == "attention_budgeting":
        recommendations.append(
            "Use `attention_budgeting` when you want a simpler speed-oriented tweak without reducing KV ownership."
        )
    if highest_cost["variant"] == "mhc":
        recommendations.append(
            "Treat `mhc` as a residual-capacity experiment: it raises compute without reducing KV cache, so keep it only if later quality evals justify the extra complexity."
        )
    recommendations.append(
        "Treat `per_layer_embeddings` as a capacity-increasing variant that likely needs stronger quality justification before adoption."
    )

    return {
        "headline": "Micro-scale architecture decision memo",
        "summary_lines": summary_lines,
        "recommendations": recommendations,
        "supporting_rows": rows,
    }


def render_decision_memo_markdown(memo: dict[str, Any], report: dict[str, Any]) -> str:
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
    lines.append("## Variant Matrix")
    lines.append("")
    lines.append("| Variant | Mean Ratio vs Baseline | Ratio Stdev | Estimated FLOPs | KV Cache Bytes | KV Cache Delta |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in memo["supporting_rows"]:
        lines.append(
            f"| `{row['variant']}` | {row['mean_ratio_vs_baseline_mean']:.3f} | {row['mean_ratio_vs_baseline_stdev']:.3f} | {row['estimated_flops']} | "
            f"{row['estimated_kv_cache_bytes']} | {row['estimated_kv_cache_bytes_delta']} |"
        )
    lines.append("")
    lines.append("## Benchmark Context")
    baseline = report["baseline"]
    lines.append(
        f"- Baseline: `{baseline['name']}` with batch size `{baseline['batch_size']}`, sequence length `{baseline['seq_len']}`, "
        f"warmup runs `{baseline['warmup_runs']}`, measured runs `{baseline['measured_runs']}`, report runs `{baseline['report_runs']}`."
    )
    for note in report.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)
