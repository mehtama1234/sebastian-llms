from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any


OBJECTIVES = ("quality", "memory", "quality_preserving_memory", "balanced")
EXECUTION_MODE_FOCUSED_PROXY_COMPARE = "focused_proxy_compare"
EXECUTION_MODE_SUMMARY_ONLY = "summary_only"
QWEN3_COMPRESSED_ATTENTION_CONFIG_ENV = "ARCH_ADV_QWEN3_COMPRESSED_ATTENTION_CONFIG"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Resolve a long-context variant proxy selector into a concrete focused follow-up plan."
    )
    parser.add_argument("--selector-artifact", required=True)
    parser.add_argument("--compare-artifact", required=False)
    parser.add_argument("--config-family", default="qwen3")
    parser.add_argument("--objective", choices=list(OBJECTIVES), default="quality_preserving_memory")
    parser.add_argument(
        "--execution-mode",
        choices=[EXECUTION_MODE_FOCUSED_PROXY_COMPARE, EXECUTION_MODE_SUMMARY_ONLY],
        default=EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
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


def _resolve_compare_artifact_path(
    *,
    selector_artifact: dict[str, Any],
    selector_artifact_path: str | Path,
    explicit_compare_artifact: str | Path | None,
    root_dir: str | Path,
) -> Path:
    if explicit_compare_artifact:
        return Path(explicit_compare_artifact)
    selector_value = selector_artifact.get("source_variant_compare_artifact")
    if selector_value and selector_value != "unknown":
        return Path(selector_value)
    sibling_guess = Path(selector_artifact_path).with_name("qwen3_variant_proxy_compare.json")
    if sibling_guess.exists():
        return sibling_guess
    return Path(root_dir) / "artifacts" / "long_context" / "qwen3_variant_proxy_compare.json"


def _resolve_variant_config_path(
    *,
    selector_artifact: dict[str, Any],
    config_family: str,
    variant_kind: str,
    root_dir: str | Path,
) -> Path:
    if config_family == "qwen3" and variant_kind == "compressed_attention":
        override = os.environ.get(QWEN3_COMPRESSED_ATTENTION_CONFIG_ENV)
        if override:
            return Path(override) if Path(override).is_absolute() else Path(root_dir) / override
    variant_configs = [Path(path) for path in selector_artifact.get("variant_configs", [])]
    for path in variant_configs:
        if path.stem == f"{config_family}-{variant_kind.replace('_', '-')}":
            return path
    return Path(root_dir) / "configs" / f"{config_family}-{variant_kind.replace('_', '-')}.json"


def _focused_compare_params(compare_artifact: dict[str, Any], objective: str) -> dict[str, Any]:
    longest = compare_artifact["filler_repeat_values"][-1]
    return {
        "source_compare_artifact": compare_artifact.get("source_artifact"),
        "filler_repeat_values": compare_artifact["filler_repeat_values"],
        "cases_per_length": compare_artifact["cases_per_length"],
        "seed": compare_artifact["seed"],
        "sweep_runs": compare_artifact["sweep_runs"],
        "selected_longest_context_bucket": next(
            row
            for row in compare_artifact["variant_buckets"]
            if row["variant_kind"] == compare_artifact["selected_recommendation"]["variant_kind"]
            and row["filler_repeats"] == longest
        )
        if "selected_recommendation" in compare_artifact
        else None,
        "objective": objective,
    }


def resolve_plan_artifact_path(
    *,
    root_dir: str | Path,
    config_family: str,
    objective: str,
    execution_mode: str,
) -> Path:
    suffix = "" if execution_mode == EXECUTION_MODE_FOCUSED_PROXY_COMPARE else f"-{execution_mode}"
    return Path(root_dir) / "artifacts" / "plans" / f"{config_family}-{objective}{suffix}-variant-proxy-plan.json"


def resolve_execution_artifact_path(
    *,
    root_dir: str | Path,
    config_family: str,
    objective: str,
    execution_mode: str,
) -> Path:
    suffix = "" if execution_mode == EXECUTION_MODE_FOCUSED_PROXY_COMPARE else f"-{execution_mode}"
    return Path(root_dir) / "artifacts" / "plans" / f"{config_family}-{objective}{suffix}-variant-proxy-execution.json"


def build_variant_run_plan(
    selector_artifact: dict[str, Any],
    *,
    selector_artifact_path: str | Path,
    compare_artifact_path: str | Path | None,
    objective: str,
    config_family: str,
    root_dir: str | Path,
    execution_mode: str = EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
) -> dict[str, Any]:
    recommendation = selector_artifact["recommendations"][objective]
    baseline_config_path = Path(selector_artifact["baseline_config"])
    selected_config_path = _resolve_variant_config_path(
        selector_artifact=selector_artifact,
        config_family=config_family,
        variant_kind=recommendation["variant_kind"],
        root_dir=root_dir,
    )
    resolved_compare_artifact_path = _resolve_compare_artifact_path(
        selector_artifact=selector_artifact,
        selector_artifact_path=selector_artifact_path,
        explicit_compare_artifact=compare_artifact_path,
        root_dir=root_dir,
    )
    compare_artifact_exists = resolved_compare_artifact_path.exists()
    compare_artifact = load_json(resolved_compare_artifact_path) if compare_artifact_exists else None
    if compare_artifact is not None:
        compare_artifact = dict(compare_artifact)
        compare_artifact["selected_recommendation"] = recommendation

    selected_summary_artifact_path = (
        Path(root_dir) / "artifacts" / "summaries" / f"{config_family}-{recommendation['variant_kind']}-variant-proxy-selected.json"
    )
    baseline_summary_artifact_path = (
        Path(root_dir) / "artifacts" / "summaries" / f"{config_family}-baseline-variant-proxy-baseline.json"
    )
    focused_compare_artifact_path = (
        Path(root_dir)
        / "artifacts"
        / "long_context"
        / f"{config_family}-{objective}-variant-proxy-focused-compare.json"
    )
    focused_report_artifact_path = focused_compare_artifact_path.with_suffix(".md")
    plan_artifact_path = resolve_plan_artifact_path(
        root_dir=root_dir,
        config_family=config_family,
        objective=objective,
        execution_mode=execution_mode,
    )
    execution_artifact_path = resolve_execution_artifact_path(
        root_dir=root_dir,
        config_family=config_family,
        objective=objective,
        execution_mode=execution_mode,
    )

    suggested_commands = [
        (
            "python -m arch_adv_2026.cli "
            f"--config '{selected_config_path}' "
            f"--artifact '{selected_summary_artifact_path}' --stdout"
        ),
    ]
    if execution_mode == EXECUTION_MODE_FOCUSED_PROXY_COMPARE:
        suggested_commands.append(
            "python -m arch_adv_2026.long_context_variant_compare "
            f"--baseline-config '{baseline_config_path}' "
            f"--variant-configs '{selected_config_path}' "
            f"--filler-repeats '{','.join(str(value) for value in compare_artifact['filler_repeat_values']) if compare_artifact else '32,64,128,256'}' "
            f"--cases-per-length {compare_artifact['cases_per_length'] if compare_artifact else 2} "
            f"--seed {compare_artifact['seed'] if compare_artifact else 17} "
            f"--sweep-runs {compare_artifact['sweep_runs'] if compare_artifact else 2} "
            f"--artifact '{focused_compare_artifact_path}' --stdout"
        )

    return {
        "workflow": "long_context_variant_proxy",
        "selector_artifact_path": str(selector_artifact_path),
        "source_compare_artifact_path": str(resolved_compare_artifact_path),
        "source_compare_artifact_exists": compare_artifact_exists,
        "objective": objective,
        "config_family": config_family,
        "execution_mode": execution_mode,
        "selection_policy": selector_artifact["selection_policy"],
        "selected_recommendation": recommendation,
        "selected_variant_kind": recommendation["variant_kind"],
        "selected_config_path": str(selected_config_path),
        "baseline_config_path": str(baseline_config_path),
        "planned_selected_summary_artifact_path": str(selected_summary_artifact_path),
        "planned_baseline_summary_artifact_path": str(baseline_summary_artifact_path),
        "planned_focused_compare_artifact_path": str(focused_compare_artifact_path),
        "planned_focused_report_artifact_path": str(focused_report_artifact_path),
        "planned_execution_artifact_path": str(execution_artifact_path),
        "planned_plan_artifact_path": str(plan_artifact_path),
        "focused_compare_params": (
            _focused_compare_params(compare_artifact, objective) if compare_artifact is not None else None
        ),
        "suggested_commands": suggested_commands,
        "notes": [
            "This plan resolves a proxy-selector recommendation into concrete config-backed follow-up artifacts.",
            "The focused compare reruns only the baseline and selected variant on the same synthetic proxy cases.",
            "This keeps the workflow proxy-only while making the selector result executable and reproducible.",
        ],
    }


def main() -> int:
    args = build_parser().parse_args()
    selector_artifact = load_json(args.selector_artifact)
    root_dir = Path(args.root_dir) if args.root_dir else Path(__file__).resolve().parents[2]
    plan = build_variant_run_plan(
        selector_artifact,
        selector_artifact_path=args.selector_artifact,
        compare_artifact_path=args.compare_artifact,
        objective=args.objective,
        config_family=args.config_family,
        root_dir=root_dir,
        execution_mode=args.execution_mode,
    )
    if args.artifact_out:
        path = write_json_artifact(plan, args.artifact_out)
        print(f"Wrote long-context variant proxy run-plan artifact to {path}")
    if args.stdout or not args.artifact_out:
        print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
