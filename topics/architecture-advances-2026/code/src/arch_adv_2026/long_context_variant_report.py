from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a markdown report from a long-context variant proxy comparison artifact."
    )
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--markdown-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_variant_compare_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _longest_context_rows(artifact: dict[str, Any]) -> list[dict[str, Any]]:
    longest = max(artifact["filler_repeat_values"])
    return [row for row in artifact["variant_buckets"] if row["filler_repeats"] == longest]


def _best_row(rows: list[dict[str, Any]], key: str, reverse: bool = False) -> dict[str, Any]:
    return sorted(rows, key=lambda row: row[key], reverse=reverse)[0]


def render_long_context_variant_report_markdown(artifact: dict[str, Any]) -> str:
    rows = artifact.get("variant_buckets", [])
    if not rows:
        raise ValueError("artifact is missing variant_buckets")

    longest_rows = _longest_context_rows(artifact)
    best_quality = _best_row(longest_rows, "mean_proxy_pass_probability", reverse=True)
    lowest_kv = _best_row(longest_rows, "estimated_kv_cache_bytes_at_max_seq")
    best_tradeoff = _best_row(
        longest_rows,
        "estimated_kv_cache_bytes_at_max_seq",
    )
    for row in sorted(longest_rows, key=lambda row: row["estimated_kv_cache_bytes_at_max_seq"]):
        if row["mean_proxy_pass_probability"] >= 0.95:
            best_tradeoff = row
            break

    lines: list[str] = []
    lines.append("# Long-Context Variant Proxy Report")
    lines.append("")
    lines.append("## Bottom line")
    lines.append(
        f"- Best proxy quality at the longest context: `{best_quality['variant_kind']}` "
        f"({best_quality['mean_proxy_pass_probability']:.3f})."
    )
    lines.append(
        f"- Lowest KV footprint at the longest context: `{lowest_kv['variant_kind']}` "
        f"({int(lowest_kv['estimated_kv_cache_bytes_at_max_seq'])} bytes, "
        f"saving ratio {lowest_kv['estimated_kv_saving_ratio_at_max_seq']:.3f})."
    )
    lines.append(
        f"- Best memory-aware quality tradeoff at the longest context: `{best_tradeoff['variant_kind']}` "
        f"({best_tradeoff['mean_proxy_pass_probability']:.3f} proxy quality, "
        f"{int(best_tradeoff['estimated_kv_cache_bytes_at_max_seq'])} KV bytes)."
    )
    lines.append("")
    lines.append("## Longest Context Ranking")
    lines.append("")
    lines.append("| Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio | Total Params |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in sorted(longest_rows, key=lambda row: row["mean_proxy_pass_probability"], reverse=True):
        lines.append(
            f"| `{row['variant_kind']}` | {row['mean_proxy_pass_probability']:.3f} | "
            f"{row['proxy_pass_rate']:.3f} | {int(row['estimated_kv_cache_bytes_at_max_seq'])} | "
            f"{row['estimated_kv_saving_ratio_at_max_seq']:.3f} | {int(row['estimated_total_params'])} |"
        )
    lines.append("")
    lines.append("## All Buckets")
    lines.append("")
    lines.append("| Filler Repeats | Variant | Proxy Quality | Proxy Pass Rate | KV Bytes | KV Saving Ratio |")
    lines.append("|---:|---|---:|---:|---:|---:|")
    for row in sorted(rows, key=lambda item: (item["filler_repeats"], item["variant_kind"])):
        lines.append(
            f"| {row['filler_repeats']} | `{row['variant_kind']}` | {row['mean_proxy_pass_probability']:.3f} | "
            f"{row['proxy_pass_rate']:.3f} | {int(row['estimated_kv_cache_bytes_at_max_seq'])} | "
            f"{row['estimated_kv_saving_ratio_at_max_seq']:.3f} |"
        )
    lines.append("")
    lines.append("## Context")
    lines.append(f"- Baseline config: `{artifact['baseline_config']}`")
    lines.append(f"- Variant configs: `{len(artifact['variant_configs'])}`")
    lines.append(f"- Filler repeats: `{artifact['filler_repeat_values']}`")
    lines.append(f"- Cases per length: `{artifact['cases_per_length']}`")
    lines.append(f"- Sweep runs: `{artifact['sweep_runs']}`")
    lines.append(f"- Case result count: `{artifact['case_result_count']}`")
    for note in artifact.get("notes", []):
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def write_markdown_report(markdown: str, path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    return output_path


def main() -> int:
    args = build_parser().parse_args()
    artifact = load_variant_compare_artifact(args.artifact)
    markdown = render_long_context_variant_report_markdown(artifact)
    if args.markdown_out:
        path = write_markdown_report(markdown, args.markdown_out)
        print(f"Wrote long-context variant report to {path}")
    if args.stdout or not args.markdown_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
