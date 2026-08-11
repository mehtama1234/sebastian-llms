from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .long_context_execute import execute_run_plan
from .long_context_plan import (
    BENCHMARK_MODE_PROXY_NUMERIC,
    BENCHMARK_MODE_SUMMARY_ONLY,
    BENCHMARK_MODE_TORCH_PROXY,
    build_run_plan,
    write_json_artifact,
)
from .torch_model import check_torch


DEFAULT_OBJECTIVES = ("memory", "speed", "balanced")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve and execute a long-context selector across multiple objectives and benchmark modes."
    )
    parser.add_argument("--selector-artifact", required=True)
    parser.add_argument("--config-family", default="qwen3")
    parser.add_argument("--root-dir", default=None)
    parser.add_argument(
        "--objective",
        dest="objectives",
        action="append",
        choices=list(DEFAULT_OBJECTIVES),
        help="Objective to include. Can be passed multiple times. Defaults to all objectives.",
    )
    parser.add_argument(
        "--benchmark-mode",
        dest="benchmark_modes",
        action="append",
        choices=[BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_TORCH_PROXY, BENCHMARK_MODE_SUMMARY_ONLY],
        help="Benchmark mode to include. Can be passed multiple times. Defaults to all available modes.",
    )
    parser.add_argument("--artifact-out", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def default_benchmark_modes() -> list[str]:
    modes = [BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_SUMMARY_ONLY]
    if check_torch().available:
        modes.append(BENCHMARK_MODE_TORCH_PROXY)
    return modes


def resolve_execution_artifact_path(
    *,
    root_dir: str | Path,
    config_family: str,
    objective: str,
    benchmark_mode: str,
) -> Path:
    suffix = "" if benchmark_mode == BENCHMARK_MODE_PROXY_NUMERIC else f"-{benchmark_mode}"
    return Path(root_dir) / "artifacts" / "plans" / f"{config_family}-{objective}{suffix}-execution.json"


def execute_matrix(
    selector_artifact: dict[str, Any],
    *,
    config_family: str,
    root_dir: str | Path,
    objectives: list[str] | None = None,
    benchmark_modes: list[str] | None = None,
) -> dict[str, Any]:
    resolved_objectives = objectives or list(DEFAULT_OBJECTIVES)
    resolved_benchmark_modes = benchmark_modes or default_benchmark_modes()
    rows: list[dict[str, Any]] = []

    for objective in resolved_objectives:
        for benchmark_mode in resolved_benchmark_modes:
            plan = build_run_plan(
                selector_artifact,
                objective=objective,
                config_family=config_family,
                root_dir=root_dir,
                benchmark_mode=benchmark_mode,
            )
            plan_artifact_path = Path(plan["planned_plan_artifact_path"])
            write_json_artifact(plan, plan_artifact_path)

            execution = execute_run_plan(plan)
            execution_artifact_path = resolve_execution_artifact_path(
                root_dir=root_dir,
                config_family=config_family,
                objective=objective,
                benchmark_mode=benchmark_mode,
            )
            write_json_artifact(execution, execution_artifact_path)

            benchmark_summary: dict[str, Any] | None = None
            if execution["benchmark_result"] is not None:
                comparison = execution["benchmark_result"].get("comparison", {})
                benchmark_summary = {
                    "mean_delta_ms": comparison.get("mean_delta_ms"),
                    "mean_ratio_variant_over_baseline": comparison.get("mean_ratio_variant_over_baseline"),
                    "owner_cache_delta": comparison.get("owner_cache_delta"),
                }

            rows.append(
                {
                    "objective": objective,
                    "benchmark_mode": benchmark_mode,
                    "selected_variant_kind": execution["selected_variant_kind"],
                    "selected_config_path": execution["selected_config_path"],
                    "plan_artifact_path": str(plan_artifact_path),
                    "execution_artifact_path": str(execution_artifact_path),
                    "benchmark_artifact_path": execution["benchmark_artifact_path"],
                    "kv_cache_saving_ratio_vs_baseline": execution["delta"]["kv_cache_saving_ratio_vs_baseline"],
                    "total_params_ratio_vs_baseline": execution["delta"]["total_params_ratio_vs_baseline"],
                    "benchmark_summary": benchmark_summary,
                }
            )

    return {
        "reference_model_id": selector_artifact["reference_model_id"],
        "config_family": config_family,
        "objectives": resolved_objectives,
        "benchmark_modes": resolved_benchmark_modes,
        "row_count": len(rows),
        "rows": rows,
        "notes": [
            "This materializes one plan artifact and one execution artifact for every requested objective/mode pair.",
            "The matrix is a workflow artifact: it makes the selector results executable across the whole current decision space.",
            "It still operates at config-summary and proxy-benchmark level, not full retraining.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    selector_artifact = load_json(args.selector_artifact)
    root_dir = Path(args.root_dir) if args.root_dir else Path(__file__).resolve().parents[2]
    matrix = execute_matrix(
        selector_artifact,
        config_family=args.config_family,
        root_dir=root_dir,
        objectives=args.objectives,
        benchmark_modes=args.benchmark_modes,
    )
    if args.artifact_out:
        path = write_json_artifact(matrix, args.artifact_out)
        print(f"Wrote long-context matrix artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(matrix, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
