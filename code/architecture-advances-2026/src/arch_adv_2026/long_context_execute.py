from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .benchmark import compare_numeric_benchmarks, compare_torch_benchmarks
from .config import load_config
from .long_context_plan import (
    BENCHMARK_MODE_PROXY_NUMERIC,
    BENCHMARK_MODE_SUMMARY_ONLY,
    BENCHMARK_MODE_TORCH_PROXY,
    resolve_config_path,
)
from .summary import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute a long-context run-plan artifact and materialize the planned summary outputs."
    )
    parser.add_argument("--plan-artifact", required=True)
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


def _write_summary(config_path: str | Path, artifact_path: str | Path) -> dict[str, Any]:
    summary = build_summary(load_config(config_path))
    write_json_artifact(summary, artifact_path)
    return summary


def execute_run_plan(plan: dict[str, Any]) -> dict[str, Any]:
    selected_summary_path = Path(plan["planned_summary_artifact_path"])
    baseline_summary_path = selected_summary_path.with_name(
        selected_summary_path.name.replace("-selected.json", "-baseline.json")
    )

    baseline_summary = _write_summary(plan["baseline_config_path"], baseline_summary_path)
    selected_summary = _write_summary(plan["selected_config_path"], selected_summary_path)
    baseline_config = load_config(plan["baseline_config_path"])
    selected_config = load_config(plan["selected_config_path"])
    benchmark_mode = plan.get("benchmark_mode", BENCHMARK_MODE_PROXY_NUMERIC)
    benchmark_params = plan.get(
        "benchmark_params",
        {"config_family": "micro", "batch_size": 1, "seq_len": 2, "seed": 0, "warmup_runs": 0, "measured_runs": 1},
    )
    benchmark_artifact_path = Path(plan["planned_benchmark_artifact_path"])
    benchmark_result: dict[str, Any] | None = None
    benchmark_config_family: str | None = None
    benchmark_note = "This plan executes summaries only and skips the benchmark step."
    if benchmark_mode == BENCHMARK_MODE_PROXY_NUMERIC:
        benchmark_note = "This plan executes the local NumPy proxy benchmark."
        benchmark_config_family = benchmark_params.get("config_family", plan["config_family"])
        proxy_baseline_config = load_config(
            resolve_config_path(
                root_dir=Path(plan["baseline_config_path"]).resolve().parents[1],
                config_family=benchmark_config_family,
                variant_kind="baseline",
            )
        )
        proxy_selected_config = load_config(
            resolve_config_path(
                root_dir=Path(plan["selected_config_path"]).resolve().parents[1],
                config_family=benchmark_config_family,
                variant_kind=plan["selected_variant_kind"],
            )
        )
        benchmark_result = compare_numeric_benchmarks(
            proxy_baseline_config,
            proxy_selected_config,
            batch_size=benchmark_params["batch_size"],
            seq_len=benchmark_params["seq_len"],
            seed=benchmark_params["seed"],
            warmup_runs=benchmark_params["warmup_runs"],
            measured_runs=benchmark_params["measured_runs"],
        )
        write_json_artifact(benchmark_result, benchmark_artifact_path)
    elif benchmark_mode == BENCHMARK_MODE_TORCH_PROXY:
        benchmark_note = "This plan executes the local Torch proxy benchmark."
        benchmark_config_family = benchmark_params.get("config_family", plan["config_family"])
        proxy_baseline_config = load_config(
            resolve_config_path(
                root_dir=Path(plan["baseline_config_path"]).resolve().parents[1],
                config_family=benchmark_config_family,
                variant_kind="baseline",
            )
        )
        proxy_selected_config = load_config(
            resolve_config_path(
                root_dir=Path(plan["selected_config_path"]).resolve().parents[1],
                config_family=benchmark_config_family,
                variant_kind=plan["selected_variant_kind"],
            )
        )
        benchmark_result = compare_torch_benchmarks(
            proxy_baseline_config,
            proxy_selected_config,
            batch_size=benchmark_params["batch_size"],
            seq_len=benchmark_params["seq_len"],
            seed=benchmark_params["seed"],
            warmup_runs=benchmark_params["warmup_runs"],
            measured_runs=benchmark_params["measured_runs"],
        )
        write_json_artifact(benchmark_result, benchmark_artifact_path)
    elif benchmark_mode == BENCHMARK_MODE_SUMMARY_ONLY:
        benchmark_config_family = None
        benchmark_result = None
    else:
        raise ValueError(f"unsupported benchmark_mode: {benchmark_mode}")

    baseline_kv = baseline_summary["kv_cache"]["variant_bytes_at_max_seq"]
    selected_kv = selected_summary["kv_cache"]["variant_bytes_at_max_seq"]
    baseline_params = baseline_summary["params"]["total"]
    selected_params = selected_summary["params"]["total"]

    return {
        "reference_model_id": plan["reference_model_id"],
        "objective": plan["objective"],
        "config_family": plan["config_family"],
        "selected_variant_kind": plan["selected_variant_kind"],
        "selected_config_path": plan["selected_config_path"],
        "baseline_config_path": plan["baseline_config_path"],
        "selected_summary_artifact_path": str(selected_summary_path),
        "baseline_summary_artifact_path": str(baseline_summary_path),
        "benchmark_mode": benchmark_mode,
        "benchmark_artifact_path": str(benchmark_artifact_path),
        "benchmark_params": benchmark_params,
        "benchmark_config_family": benchmark_config_family,
        "selected_summary": selected_summary,
        "baseline_summary": baseline_summary,
        "benchmark_result": benchmark_result,
        "delta": {
            "kv_cache_bytes_delta": selected_kv - baseline_kv,
            "kv_cache_saving_ratio_vs_baseline": (
                (baseline_kv - selected_kv) / baseline_kv if baseline_kv else 0.0
            ),
            "total_params_delta": selected_params - baseline_params,
            "total_params_ratio_vs_baseline": (
                selected_params / baseline_params if baseline_params else 1.0
            ),
        },
        "notes": [
            benchmark_note,
            "No real Qwen weights are modified or retrained here.",
            "The delta compares the selected config summary against the baseline config summary.",
            "The benchmark result can use a smaller proxy config family even when the selected plan targets a Qwen-shaped config.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    plan = load_json(args.plan_artifact)
    execution = execute_run_plan(plan)
    if args.artifact_out:
        path = write_json_artifact(execution, args.artifact_out)
        print(f"Wrote long-context execution artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(execution, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
