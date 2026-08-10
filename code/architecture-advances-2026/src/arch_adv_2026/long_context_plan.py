from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


VARIANT_CONFIG_BASENAMES = {
    "baseline": "baseline",
    "kv_sharing": "kv-sharing",
    "attention_budgeting": "attention-budgeting",
    "compressed_attention": "compressed-attention",
    "per_layer_embeddings": "ple",
    "history_compression": "history-compression",
    "mhc": "mhc",
}

BENCHMARK_MODE_PROXY_NUMERIC = "proxy_numeric"
BENCHMARK_MODE_TORCH_PROXY = "torch_proxy"
BENCHMARK_MODE_SUMMARY_ONLY = "summary_only"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve a long-context selector artifact into a concrete config-backed run plan."
    )
    parser.add_argument("--selector-artifact", required=True)
    parser.add_argument("--config-family", default="qwen3")
    parser.add_argument("--objective", choices=["memory", "speed", "balanced"], default="balanced")
    parser.add_argument(
        "--benchmark-mode",
        choices=[BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_TORCH_PROXY, BENCHMARK_MODE_SUMMARY_ONLY],
        default=BENCHMARK_MODE_PROXY_NUMERIC,
    )
    parser.add_argument("--root-dir", default=None)
    parser.add_argument("--artifact-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json_artifact(data: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return output_path


def resolve_config_path(
    *,
    root_dir: str | Path,
    config_family: str,
    variant_kind: str,
) -> Path:
    basename = VARIANT_CONFIG_BASENAMES.get(variant_kind)
    if basename is None:
        raise ValueError(f"unsupported variant kind for config resolution: {variant_kind}")
    return Path(root_dir) / "configs" / f"{config_family}-{basename}.json"


def resolve_plan_artifact_path(
    *,
    root_dir: str | Path,
    config_family: str,
    objective: str,
    benchmark_mode: str,
) -> Path:
    suffix = "" if benchmark_mode == BENCHMARK_MODE_PROXY_NUMERIC else f"-{benchmark_mode}"
    return Path(root_dir) / "artifacts" / "plans" / f"{config_family}-{objective}{suffix}-run-plan.json"


def build_run_plan(
    selector_artifact: dict[str, Any],
    *,
    objective: str,
    config_family: str,
    root_dir: str | Path,
    benchmark_mode: str = BENCHMARK_MODE_PROXY_NUMERIC,
) -> dict[str, Any]:
    recommendation = selector_artifact["recommendations"][objective]
    config_path = resolve_config_path(
        root_dir=root_dir,
        config_family=config_family,
        variant_kind=recommendation["variant_kind"],
    )
    baseline_config_path = resolve_config_path(
        root_dir=root_dir,
        config_family=config_family,
        variant_kind="baseline",
    )
    summary_artifact_path = (
        Path(root_dir) / "artifacts" / "summaries" / f"{config_family}-{recommendation['variant_kind']}-selected.json"
    )
    benchmark_artifact_path = (
        Path(root_dir)
        / "artifacts"
        / "benchmarks"
        / f"{config_family}-baseline-vs-{recommendation['variant_kind']}-{benchmark_mode}.json"
    )
    plan_artifact_path = resolve_plan_artifact_path(
        root_dir=root_dir,
        config_family=config_family,
        objective=objective,
        benchmark_mode=benchmark_mode,
    )

    suggested_commands = [
        (
            "python -m arch_adv_2026.cli "
            f"--config '{config_path}' "
            f"--artifact '{summary_artifact_path}' --stdout"
        ),
        (
            "python -m arch_adv_2026.long_context_compare "
            f"--sweep-artifact '{Path(root_dir) / 'artifacts' / 'long_context' / 'qwen3_long_context_medium.json'}' "
            f"--projection-artifact '{Path(root_dir) / 'artifacts' / 'long_context' / 'qwen3_long_context_medium_qwen_projection.json'}' "
            f"--artifact-out '{Path(root_dir) / 'artifacts' / 'long_context' / 'qwen3_long_context_medium_selector.json'}' "
            f"--markdown-out '{Path(root_dir) / 'artifacts' / 'long_context' / 'qwen3_long_context_medium_compare.md'}'"
        ),
    ]

    return {
        "reference_model_id": selector_artifact["reference_model_id"],
        "objective": objective,
        "config_family": config_family,
        "selector_policy": selector_artifact["selection_policy"],
        "selected_recommendation": recommendation,
        "selected_variant_kind": recommendation["variant_kind"],
        "selected_config_path": str(config_path),
        "baseline_config_path": str(baseline_config_path),
        "planned_summary_artifact_path": str(summary_artifact_path),
        "planned_benchmark_artifact_path": str(benchmark_artifact_path),
        "planned_plan_artifact_path": str(plan_artifact_path),
        "benchmark_mode": benchmark_mode,
        "benchmark_params": {
            "config_family": "micro",
            "batch_size": 1,
            "seq_len": 2,
            "seed": 0,
            "warmup_runs": 0,
            "measured_runs": 1,
        },
        "suggested_commands": suggested_commands,
        "notes": [
            "This plan resolves the selector recommendation to a concrete config path in the local config family.",
            "The suggested commands only use surfaces that already exist in this workspace.",
            "This does not claim a real re-trained Qwen variant exists; it is the next-step experiment plan for the chosen architecture shape.",
            "Benchmark mode explicitly controls whether execution runs a proxy numeric benchmark or only summary generation.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    selector_artifact = load_json(args.selector_artifact)
    root_dir = Path(args.root_dir) if args.root_dir else Path(__file__).resolve().parents[2]
    plan = build_run_plan(
        selector_artifact,
        objective=args.objective,
        config_family=args.config_family,
        root_dir=root_dir,
        benchmark_mode=args.benchmark_mode,
    )
    if args.artifact_out:
        path = write_json_artifact(plan, args.artifact_out)
        print(f"Wrote long-context run-plan artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
