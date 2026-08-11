from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a markdown report from a long-context sweep artifact.")
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--markdown-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_sweep_artifact(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _best_bucket(buckets: list[dict[str, Any]], key: str, reverse: bool = False) -> dict[str, Any]:
    return sorted(buckets, key=lambda row: row[key], reverse=reverse)[0]


def render_long_context_report_markdown(artifact: dict[str, Any]) -> str:
    buckets = artifact.get("sweep", {}).get("length_buckets", [])
    if not buckets:
        raise ValueError("artifact is missing sweep.length_buckets")

    best_quality = _best_bucket(buckets, "mean_pass_rate", reverse=True)
    cheapest_kv = _best_bucket(buckets, "mean_estimated_kv_cache_bytes")
    fastest_decode = _best_bucket(buckets, "mean_generated_tokens_per_second", reverse=True)

    lines: list[str] = []
    lines.append("# Long-Context Sweep Report")
    lines.append("")
    lines.append("## Bottom line")
    lines.append(
        f"- Best mean pass rate: filler repeats `{best_quality['filler_repeats']}` "
        f"({best_quality['mean_pass_rate']:.3f}, stdev {best_quality['pass_rate_stdev']:.3f})."
    )
    lines.append(
        f"- Lowest estimated KV cache: filler repeats `{cheapest_kv['filler_repeats']}` "
        f"({int(cheapest_kv['mean_estimated_kv_cache_bytes'])} bytes)."
    )
    lines.append(
        f"- Fastest generated-token throughput: filler repeats `{fastest_decode['filler_repeats']}` "
        f"({fastest_decode['mean_generated_tokens_per_second']:.3f} tokens/s)."
    )
    lines.append("")
    lines.append("## Length Buckets")
    lines.append("")
    lines.append(
        "| Filler Repeats | Runs | Cases/Run | Mean Pass Rate | Pass Rate Stdev | Mean Elapsed ms | "
        "Elapsed Stdev | Mean Gen Tok/s | Mean Total Tok/s | Mean KV Cache Bytes |"
    )
    lines.append("|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for bucket in buckets:
        lines.append(
            f"| {bucket['filler_repeats']} | {bucket['num_runs']} | {bucket['num_cases_per_run']} | "
            f"{bucket['mean_pass_rate']:.3f} | {bucket['pass_rate_stdev']:.3f} | "
            f"{bucket['mean_elapsed_ms']:.2f} | {bucket['elapsed_ms_stdev']:.2f} | "
            f"{bucket['mean_generated_tokens_per_second']:.3f} | {bucket['mean_total_tokens_per_second']:.3f} | "
            f"{int(bucket['mean_estimated_kv_cache_bytes'])} |"
        )
    lines.append("")
    lines.append("## Context")
    sweep = artifact["sweep"]
    lines.append(f"- Model: `{artifact['model_id']}`")
    lines.append(f"- Filler repeats: `{sweep['filler_repeat_values']}`")
    lines.append(f"- Cases per length: `{sweep['cases_per_length']}`")
    lines.append(f"- Sweep runs: `{sweep['sweep_runs']}`")
    lines.append(f"- Overall pass rate: `{artifact['pass_rate']:.3f}` across `{artifact['num_cases']}` cases")
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
    artifact = load_sweep_artifact(args.artifact)
    markdown = render_long_context_report_markdown(artifact)
    if args.markdown_out:
        path = write_markdown_report(markdown, args.markdown_out)
        print(f"Wrote long-context report to {path}")
    if args.stdout or not args.markdown_out:
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
