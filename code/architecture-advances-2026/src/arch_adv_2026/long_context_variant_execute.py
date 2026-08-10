from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .config import load_config
from .long_context_variant_compare import build_variant_long_context_compare
from .long_context_variant_plan import EXECUTION_MODE_FOCUSED_PROXY_COMPARE, EXECUTION_MODE_SUMMARY_ONLY
from .summary import build_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Execute a long-context variant proxy run-plan artifact and materialize the planned outputs."
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


def _focused_rows(compare_result: dict[str, Any], variant_kind: str, longest_filler: int) -> dict[str, Any]:
    buckets = compare_result["variant_buckets"]
    selected_bucket = next(
        row for row in buckets if row["variant_kind"] == variant_kind and row["filler_repeats"] == longest_filler
    )
    baseline_bucket = next(
        row for row in buckets if row["variant_kind"] == "baseline" and row["filler_repeats"] == longest_filler
    )
    return {
        "selected_bucket": selected_bucket,
        "baseline_bucket": baseline_bucket,
        "proxy_quality_delta": (
            selected_bucket["mean_proxy_pass_probability"] - baseline_bucket["mean_proxy_pass_probability"]
        ),
        "proxy_kv_bytes_delta": (
            selected_bucket["estimated_kv_cache_bytes_at_max_seq"] - baseline_bucket["estimated_kv_cache_bytes_at_max_seq"]
        ),
    }


def execute_variant_run_plan(plan: dict[str, Any]) -> dict[str, Any]:
    selected_summary = _write_summary(
        plan["selected_config_path"],
        plan["planned_selected_summary_artifact_path"],
    )
    baseline_summary = _write_summary(
        plan["baseline_config_path"],
        plan["planned_baseline_summary_artifact_path"],
    )

    compare_result: dict[str, Any] | None = None
    focused_compare_summary: dict[str, Any] | None = None
    execution_mode = plan.get("execution_mode", EXECUTION_MODE_FOCUSED_PROXY_COMPARE)
    focused_compare_artifact_path = Path(plan["planned_focused_compare_artifact_path"])

    if execution_mode == EXECUTION_MODE_FOCUSED_PROXY_COMPARE:
        params = plan.get("focused_compare_params")
        if params is None:
            raise ValueError("focused_proxy_compare execution requires focused_compare_params in the plan artifact")
        compare_result = build_variant_long_context_compare(
            baseline_config_path=plan["baseline_config_path"],
            variant_config_paths=[plan["selected_config_path"]],
            filler_repeat_values=params["filler_repeat_values"],
            cases_per_length=params["cases_per_length"],
            seed=params["seed"],
            sweep_runs=params["sweep_runs"],
        )
        write_json_artifact(compare_result, focused_compare_artifact_path)
        focused_compare_summary = _focused_rows(
            compare_result,
            variant_kind=plan["selected_variant_kind"],
            longest_filler=max(params["filler_repeat_values"]),
        )
    elif execution_mode == EXECUTION_MODE_SUMMARY_ONLY:
        compare_result = None
        focused_compare_summary = None
    else:
        raise ValueError(f"unsupported execution_mode: {execution_mode}")

    baseline_kv = baseline_summary["kv_cache"]["variant_bytes_at_max_seq"]
    selected_kv = selected_summary["kv_cache"]["variant_bytes_at_max_seq"]
    baseline_params = baseline_summary["params"]["total"]
    selected_params = selected_summary["params"]["total"]

    return {
        "workflow": plan["workflow"],
        "objective": plan["objective"],
        "config_family": plan["config_family"],
        "execution_mode": execution_mode,
        "selected_variant_kind": plan["selected_variant_kind"],
        "selected_config_path": plan["selected_config_path"],
        "baseline_config_path": plan["baseline_config_path"],
        "selected_summary_artifact_path": plan["planned_selected_summary_artifact_path"],
        "baseline_summary_artifact_path": plan["planned_baseline_summary_artifact_path"],
        "focused_compare_artifact_path": str(focused_compare_artifact_path),
        "selected_summary": selected_summary,
        "baseline_summary": baseline_summary,
        "focused_compare_result": compare_result,
        "focused_compare_summary": focused_compare_summary,
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
            "This execution materializes baseline and selected summaries for the proxy-selector recommendation.",
            "Focused proxy compare reruns only the selected variant and baseline on the same synthetic case schedule.",
            "The output is still a proxy experiment artifact, not a trained-weight benchmark.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    plan = load_json(args.plan_artifact)
    execution = execute_variant_run_plan(plan)
    if args.artifact_out:
        path = write_json_artifact(execution, args.artifact_out)
        print(f"Wrote long-context variant proxy execution artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(execution, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
