from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a machine-readable selector artifact from a long-context variant proxy comparison artifact."
    )
    parser.add_argument("--artifact", required=True, help="Path to qwen3_variant_proxy_compare.json")
    parser.add_argument("--min-proxy-quality", type=float, default=0.95)
    parser.add_argument("--selector-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_variant_compare_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _longest_context_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    longest = max(artifact["filler_repeat_values"])
    return [row for row in artifact["variant_buckets"] if row["filler_repeats"] == longest]


def _best_row(rows: list[dict[str, Any]], key: str, reverse: bool = False) -> dict[str, Any]:
    return sorted(rows, key=lambda row: row[key], reverse=reverse)[0]


def build_variant_selector_artifact(
    artifact: dict[str, Any],
    *,
    min_proxy_quality: float = 0.95,
) -> dict[str, Any]:
    rows = _longest_context_rows(artifact)
    acceptable_rows = [row for row in rows if row["mean_proxy_pass_probability"] >= min_proxy_quality]
    if not acceptable_rows:
        acceptable_rows = rows

    best_quality = _best_row(rows, "mean_proxy_pass_probability", reverse=True)
    lowest_kv = _best_row(acceptable_rows, "estimated_kv_cache_bytes_at_max_seq")
    quality_preserving_memory = _best_row(
        acceptable_rows,
        "estimated_kv_cache_bytes_at_max_seq",
    )
    balanced = _best_row(
        acceptable_rows,
        "estimated_total_params",
    )

    return {
        "baseline_config": artifact["baseline_config"],
        "variant_configs": artifact["variant_configs"],
        "source_variant_compare_artifact": artifact.get("source_artifact", "unknown"),
        "selection_policy": {
            "longest_context_filler_repeats": max(artifact["filler_repeat_values"]),
            "minimum_proxy_quality": min_proxy_quality,
            "fallback_to_all_rows_if_no_variant_meets_threshold": True,
            "used_fallback_rows": len(acceptable_rows) == len(rows)
            and not any(row["mean_proxy_pass_probability"] >= min_proxy_quality for row in rows),
            "acceptable_row_count": len(acceptable_rows),
            "total_row_count": len(rows),
        },
        "recommendations": {
            "quality": best_quality,
            "memory": lowest_kv,
            "quality_preserving_memory": quality_preserving_memory,
            "balanced": balanced,
        },
        "notes": [
            "Recommendations are computed only from the longest-context bucket in the proxy comparison artifact.",
            "Memory chooses the lowest KV footprint among variants that clear the proxy-quality threshold.",
            "Balanced chooses the lowest parameter count among variants that clear the proxy-quality threshold.",
            "This selector is proxy-only and should guide heavier experiments, not replace them.",
        ],
    }


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def main() -> int:
    args = build_parser().parse_args()
    artifact = load_variant_compare_artifact(args.artifact)
    selector = build_variant_selector_artifact(
        artifact,
        min_proxy_quality=args.min_proxy_quality,
    )
    if args.selector_out:
        path = write_json_artifact(selector, args.selector_out)
        print(f"Wrote long-context variant selector to {path}")
    if args.stdout or not args.selector_out:
        print(json.dumps(selector, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
