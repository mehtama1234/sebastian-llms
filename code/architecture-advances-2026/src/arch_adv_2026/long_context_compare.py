from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a combined long-context comparison from a sweep artifact and a variant projection artifact."
    )
    parser.add_argument("--sweep-artifact", required=True)
    parser.add_argument("--projection-artifact", required=True)
    parser.add_argument("--min-pass-rate", type=float, default=0.5)
    parser.add_argument("--artifact-out", required=False)
    parser.add_argument("--markdown-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def build_combined_rows(
    sweep_artifact: dict[str, Any],
    projection_artifact: dict[str, Any],
) -> list[dict[str, Any]]:
    buckets = {row["filler_repeats"]: row for row in sweep_artifact["sweep"]["length_buckets"]}
    rows: list[dict[str, Any]] = []
    for projection_row in projection_artifact["projection_rows"]:
        filler_repeats = projection_row["filler_repeats"]
        bucket = buckets[filler_repeats]
        rows.append(
            {
                "filler_repeats": filler_repeats,
                "reference_mean_pass_rate": bucket["mean_pass_rate"],
                "reference_mean_elapsed_ms": bucket["mean_elapsed_ms"],
                "reference_mean_estimated_kv_cache_bytes": bucket["mean_estimated_kv_cache_bytes"],
                "variant_kind": projection_row["variant_kind"],
                "projected_kv_cache_bytes": projection_row["projected_kv_cache_bytes"],
                "projected_kv_saving_ratio": projection_row["projected_kv_saving_ratio"],
                "flops_ratio_vs_baseline": projection_row["flops_ratio_vs_baseline"],
                "projected_elapsed_ms": projection_row["projected_elapsed_ms"],
                "projected_elapsed_ms_delta": projection_row["projected_elapsed_ms_delta"],
                "owner_layer_count": projection_row["owner_layer_count"],
                "effective_attn_head_dim": projection_row["effective_attn_head_dim"],
            }
        )
    return rows


def _best_row(rows: list[dict[str, Any]], key: str) -> dict[str, Any]:
    return min(rows, key=lambda row: row[key])


def build_recommendation_summary(
    sweep_artifact: dict[str, Any],
    projection_artifact: dict[str, Any],
    *,
    min_pass_rate: float,
) -> dict[str, Any]:
    rows = build_combined_rows(sweep_artifact, projection_artifact)
    acceptable_rows = [row for row in rows if row["reference_mean_pass_rate"] >= min_pass_rate]
    if not acceptable_rows:
        acceptable_rows = rows
    best_quality_bucket = max(
        sweep_artifact["sweep"]["length_buckets"],
        key=lambda row: row["mean_pass_rate"],
    )
    lowest_kv_projection = _best_row(acceptable_rows, "projected_kv_cache_bytes")
    fastest_projection = _best_row(acceptable_rows, "projected_elapsed_ms")
    best_balanced_projection = _best_row(
        acceptable_rows,
        "flops_ratio_vs_baseline",
    )
    return {
        "rows": rows,
        "acceptable_rows": acceptable_rows,
        "used_fallback_rows": len(acceptable_rows) == len(rows) and not any(
            row["reference_mean_pass_rate"] >= min_pass_rate for row in rows
        ),
        "min_pass_rate": min_pass_rate,
        "best_quality_bucket": best_quality_bucket,
        "lowest_kv_projection": lowest_kv_projection,
        "fastest_projection": fastest_projection,
        "best_balanced_projection": best_balanced_projection,
    }


def build_selector_artifact(
    sweep_artifact: dict[str, Any],
    projection_artifact: dict[str, Any],
    *,
    min_pass_rate: float,
) -> dict[str, Any]:
    summary = build_recommendation_summary(
        sweep_artifact,
        projection_artifact,
        min_pass_rate=min_pass_rate,
    )
    return {
        "reference_model_id": sweep_artifact["model_id"],
        "reference_sweep_artifact": sweep_artifact.get("source_artifact", "unknown"),
        "projection_artifact": projection_artifact.get("reference_sweep_artifact", "unknown"),
        "selection_policy": {
            "minimum_reference_pass_rate": min_pass_rate,
            "fallback_to_all_rows_if_no_bucket_meets_threshold": True,
            "used_fallback_rows": summary["used_fallback_rows"],
            "acceptable_row_count": len(summary["acceptable_rows"]),
            "total_row_count": len(summary["rows"]),
        },
        "best_quality_bucket": summary["best_quality_bucket"],
        "recommendations": {
            "memory": summary["lowest_kv_projection"],
            "speed": summary["fastest_projection"],
            "balanced": summary["best_balanced_projection"],
        },
        "notes": [
            "Recommendations are filtered by the reference bucket pass-rate threshold before cost-based ranking.",
            "Memory chooses the lowest projected KV-cache bytes among acceptable rows.",
            "Speed chooses the lowest projected elapsed-ms among acceptable rows.",
            "Balanced chooses the lowest projected FLOPs ratio among acceptable rows.",
            "Projected costs come from the projection artifact and do not claim projected quality."
        ],
    }


def render_combined_markdown(
    sweep_artifact: dict[str, Any],
    projection_artifact: dict[str, Any],
    *,
    min_pass_rate: float = 0.5,
) -> str:
    summary = build_recommendation_summary(
        sweep_artifact,
        projection_artifact,
        min_pass_rate=min_pass_rate,
    )
    rows = summary["rows"]
    best_quality_bucket = summary["best_quality_bucket"]
    lowest_kv_projection = summary["lowest_kv_projection"]
    fastest_projection = summary["fastest_projection"]
    best_balanced_projection = summary["best_balanced_projection"]

    lines: list[str] = []
    lines.append("# Long-Context Comparison")
    lines.append("")
    lines.append("## Bottom line")
    lines.append(
        f"- Best observed reference pass rate was at filler repeats `{best_quality_bucket['filler_repeats']}` "
        f"({best_quality_bucket['mean_pass_rate']:.3f})."
    )
    lines.append(
        f"- Lowest projected KV-cache cost in this comparison is `{lowest_kv_projection['variant_kind']}` at "
        f"filler repeats `{lowest_kv_projection['filler_repeats']}` "
        f"({int(lowest_kv_projection['projected_kv_cache_bytes'])} bytes)."
    )
    lines.append(
        f"- Fastest projected elapsed-ms in this comparison is `{fastest_projection['variant_kind']}` at "
        f"filler repeats `{fastest_projection['filler_repeats']}` "
        f"({fastest_projection['projected_elapsed_ms']:.2f} ms)."
    )
    lines.append("")
    lines.append("## Recommendation Layer")
    if summary["used_fallback_rows"]:
        lines.append(
            f"- No reference bucket met the requested minimum pass rate of `{min_pass_rate:.3f}`, so recommendations fell back to all rows."
        )
    else:
        lines.append(
            f"- Recommendations below only consider rows whose reference bucket pass rate is at least `{min_pass_rate:.3f}`."
        )
    lines.append(
        f"- Best memory saver at acceptable quality: `{lowest_kv_projection['variant_kind']}` at filler repeats "
        f"`{lowest_kv_projection['filler_repeats']}` "
        f"with projected KV cache `{int(lowest_kv_projection['projected_kv_cache_bytes'])}` bytes "
        f"and reference pass rate `{lowest_kv_projection['reference_mean_pass_rate']:.3f}`."
    )
    lines.append(
        f"- Best projected speed at acceptable quality: `{fastest_projection['variant_kind']}` at filler repeats "
        f"`{fastest_projection['filler_repeats']}` "
        f"with projected elapsed `{fastest_projection['projected_elapsed_ms']:.2f}` ms."
    )
    lines.append(
        f"- Best balanced compute choice at acceptable quality: `{best_balanced_projection['variant_kind']}` at filler repeats "
        f"`{best_balanced_projection['filler_repeats']}` "
        f"with FLOPs ratio `{best_balanced_projection['flops_ratio_vs_baseline']:.3f}` and projected KV saving "
        f"`{best_balanced_projection['projected_kv_saving_ratio']:.3f}`."
    )
    lines.append("")
    lines.append("## Combined Table")
    lines.append("")
    lines.append(
        "| Filler Repeats | Ref Pass Rate | Ref Elapsed ms | Variant | Proj KV Bytes | Proj KV Saving | "
        "FLOPs Ratio | Proj Elapsed ms | Elapsed Delta ms | Owner Layers | Eff Head Dim |"
    )
    lines.append("|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['filler_repeats']} | {row['reference_mean_pass_rate']:.3f} | "
            f"{row['reference_mean_elapsed_ms']:.2f} | `{row['variant_kind']}` | "
            f"{int(row['projected_kv_cache_bytes'])} | {row['projected_kv_saving_ratio']:.3f} | "
            f"{row['flops_ratio_vs_baseline']:.3f} | {row['projected_elapsed_ms']:.2f} | "
            f"{row['projected_elapsed_ms_delta']:.2f} | {row['owner_layer_count']} | "
            f"{row['effective_attn_head_dim']} |"
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("- Reference quality and reference latency come from the real Qwen sweep artifact.")
    lines.append("- Variant costs are projected from the Qwen-shaped config family.")
    lines.append("- Projected elapsed-ms is a compute-side estimate from config-level FLOP ratios, not a measured runtime.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = build_parser().parse_args()
    sweep_artifact = load_json(args.sweep_artifact)
    projection_artifact = load_json(args.projection_artifact)
    selector_artifact = build_selector_artifact(
        sweep_artifact,
        projection_artifact,
        min_pass_rate=args.min_pass_rate,
    )
    markdown = render_combined_markdown(
        sweep_artifact,
        projection_artifact,
        min_pass_rate=args.min_pass_rate,
    )
    if args.artifact_out:
        path = write_json_artifact(selector_artifact, args.artifact_out)
        print(f"Wrote long-context selector artifact to {path}")
    if args.markdown_out:
        output_path = Path(args.markdown_out)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(markdown, encoding="utf-8")
        print(f"Wrote combined long-context report to {output_path}")
    if args.stdout or not args.markdown_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
