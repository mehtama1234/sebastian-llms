from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_config
from .numeric_runtime import estimate_numeric_flops
from .summary import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Project architecture variant KV-cache costs onto a long-context sweep artifact."
    )
    parser.add_argument("--sweep-artifact", required=True)
    parser.add_argument("--baseline-config", required=True)
    parser.add_argument("--variant-configs", nargs="+", required=True)
    parser.add_argument("--artifact", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _variant_projection_rows(
    sweep_artifact: dict[str, Any],
    baseline_summary: dict[str, Any],
    baseline_flops: int,
    variant_summaries: list[dict[str, Any]],
    variant_flops: list[int],
) -> list[dict[str, Any]]:
    baseline_kv_bytes = baseline_summary["kv_cache"]["variant_bytes_at_max_seq"]
    rows: list[dict[str, Any]] = []
    for bucket in sweep_artifact["sweep"]["length_buckets"]:
        reference_kv = bucket["mean_estimated_kv_cache_bytes"]
        reference_elapsed_ms = bucket["mean_elapsed_ms"]
        for variant, flops in zip(variant_summaries, variant_flops, strict=True):
            variant_kv_bytes = variant["kv_cache"]["variant_bytes_at_max_seq"]
            kv_ratio_vs_baseline = variant_kv_bytes / baseline_kv_bytes if baseline_kv_bytes else 1.0
            projected_kv_bytes = reference_kv * kv_ratio_vs_baseline
            flops_ratio_vs_baseline = flops / baseline_flops if baseline_flops else 1.0
            projected_elapsed_ms = reference_elapsed_ms * flops_ratio_vs_baseline
            rows.append(
                {
                    "filler_repeats": bucket["filler_repeats"],
                    "reference_mean_pass_rate": bucket["mean_pass_rate"],
                    "reference_mean_elapsed_ms": reference_elapsed_ms,
                    "variant": variant["name"],
                    "variant_kind": variant["variant"]["kind"],
                    "kv_ratio_vs_baseline": kv_ratio_vs_baseline,
                    "flops_ratio_vs_baseline": flops_ratio_vs_baseline,
                    "projected_kv_cache_bytes": projected_kv_bytes,
                    "projected_kv_bytes_saved": reference_kv - projected_kv_bytes,
                    "projected_kv_saving_ratio": (
                        (reference_kv - projected_kv_bytes) / reference_kv if reference_kv else 0.0
                    ),
                    "projected_elapsed_ms": projected_elapsed_ms,
                    "projected_elapsed_ms_delta": projected_elapsed_ms - reference_elapsed_ms,
                    "estimated_flops_ratio_source": flops,
                    "owner_layer_count": variant["kv_sharing"]["owner_layer_count"],
                    "effective_attn_head_dim": variant["shape"]["effective_attn_head_dim"],
                }
            )
    return rows


def build_projection(
    sweep_artifact: dict[str, Any],
    baseline_config_path: str | Path,
    variant_config_paths: list[str | Path],
) -> dict[str, Any]:
    baseline_config = load_config(baseline_config_path)
    baseline_summary = build_summary(baseline_config)
    baseline_flops = estimate_numeric_flops(baseline_config, seq_len=8)

    variant_summaries = []
    variant_flops = []
    for path in variant_config_paths:
        config = load_config(path)
        variant_summaries.append(build_summary(config))
        variant_flops.append(estimate_numeric_flops(config, seq_len=8))

    rows = _variant_projection_rows(
        sweep_artifact,
        baseline_summary,
        baseline_flops,
        variant_summaries,
        variant_flops,
    )
    return {
        "reference_model_id": sweep_artifact["model_id"],
        "reference_sweep_artifact": sweep_artifact.get("source_artifact", "unknown"),
        "baseline_config": str(baseline_config_path),
        "variant_configs": [str(path) for path in variant_config_paths],
        "baseline_estimated_flops_source": baseline_flops,
        "projection_rows": rows,
        "notes": [
            "This is a cost-only projection anchored to the real Qwen sweep buckets.",
            "Projected KV-cache bytes use each variant's config-level KV ratio relative to the baseline config.",
            "Projected elapsed-ms uses each variant's estimated-FLOP ratio from the local numeric runtime.",
            "Reference pass rate and latency come from the real sweep artifact; projected quality is not claimed."
        ],
    }


def render_projection_markdown(projection: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Long-Context Variant Projection")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("- Reference quality comes from the real Qwen sweep artifact.")
    lines.append("- Variant rows project KV-cache cost and a compute-scaled elapsed-ms estimate, not quality.")
    lines.append("")
    lines.append("## Projected Buckets")
    lines.append("")
    lines.append(
        "| Filler Repeats | Reference Pass Rate | Variant | KV Ratio vs Baseline | FLOPs Ratio vs Baseline | "
        "Projected KV Bytes | Projected Saving Ratio | Projected Elapsed ms | Owner Layers | Effective Head Dim |"
    )
    lines.append("|---:|---:|---|---:|---:|---:|---:|---:|---:|---:|")
    for row in projection["projection_rows"]:
        lines.append(
            f"| {row['filler_repeats']} | {row['reference_mean_pass_rate']:.3f} | `{row['variant_kind']}` | "
            f"{row['kv_ratio_vs_baseline']:.3f} | {row['flops_ratio_vs_baseline']:.3f} | "
            f"{int(row['projected_kv_cache_bytes'])} | {row['projected_kv_saving_ratio']:.3f} | "
            f"{row['projected_elapsed_ms']:.2f} | {row['owner_layer_count']} | {row['effective_attn_head_dim']} |"
        )
    lines.append("")
    lines.append("## Notes")
    for note in projection.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    args = build_parser().parse_args()
    sweep_artifact = load_json(args.sweep_artifact)
    projection = build_projection(
        sweep_artifact,
        args.baseline_config,
        args.variant_configs,
    )
    if args.artifact:
        path = write_json_artifact(projection, args.artifact)
        print(f"Wrote long-context projection artifact to {path}")
    if args.stdout or not args.artifact:
        print(json.dumps(projection, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
