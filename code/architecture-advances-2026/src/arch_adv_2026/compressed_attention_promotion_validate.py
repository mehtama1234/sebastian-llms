from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def validate_compressed_attention_promotion_artifacts(
    training_matrix: dict[str, Any],
    benchmark_matrix: dict[str, Any],
    long_context_execution: dict[str, Any],
    assessment: dict[str, Any],
    stress_assessment: dict[str, Any] | None = None,
    speed_tail_assessment: dict[str, Any] | None = None,
    memo_bundle: dict[str, Any] | None = None,
    remediation_plan: dict[str, Any] | None = None,
    remediation_execution: dict[str, Any] | None = None,
) -> list[str]:
    errors: list[str] = []
    variant = "compressed_attention"

    training_rows = {row.get("variant"): row for row in training_matrix.get("variant_trends", [])}
    benchmark_rows = {row.get("variant"): row for row in benchmark_matrix.get("variant_summary_rows", [])}
    assessment_training = assessment.get("training", {})
    assessment_benchmark = assessment.get("benchmark", {})
    assessment_long_context = assessment.get("long_context", {})
    gates = assessment.get("gates", {})

    if assessment.get("variant") != variant:
        errors.append("assessment variant must be compressed_attention")
    if long_context_execution.get("selected_variant_kind") != variant:
        errors.append("long-context execution selected_variant_kind must be compressed_attention")
    if variant not in training_rows:
        errors.append("training matrix is missing compressed_attention trend data")
    if variant not in benchmark_rows:
        errors.append("benchmark matrix is missing compressed_attention summary data")

    if errors:
        return errors

    training_row = training_rows[variant]
    benchmark_row = benchmark_rows[variant]
    summary = long_context_execution.get("focused_compare_summary")
    if not summary:
        errors.append("long-context execution is missing focused_compare_summary")
        return errors

    selected_bucket = summary.get("selected_bucket", {})
    baseline_bucket = summary.get("baseline_bucket", {})
    if selected_bucket.get("variant_kind") != variant:
        errors.append("long-context selected bucket must be compressed_attention")
    if baseline_bucket.get("variant_kind") != "baseline":
        errors.append("long-context baseline bucket must be baseline")

    if assessment_training != training_row:
        errors.append("assessment training row does not match the training matrix")
    if assessment_benchmark != benchmark_row:
        errors.append("assessment benchmark row does not match the benchmark matrix")
    if assessment_long_context.get("selected_bucket") != selected_bucket:
        errors.append("assessment long-context selected bucket does not match the execution artifact")
    if assessment_long_context.get("baseline_bucket") != baseline_bucket:
        errors.append("assessment long-context baseline bucket does not match the execution artifact")

    quality_delta = selected_bucket["mean_proxy_pass_probability"] - baseline_bucket["mean_proxy_pass_probability"]
    pass_rate_delta = selected_bucket["proxy_pass_rate"] - baseline_bucket["proxy_pass_rate"]
    kv_saving_ratio = long_context_execution["delta"]["kv_cache_saving_ratio_vs_baseline"]

    if assessment_long_context.get("quality_delta_vs_baseline") != quality_delta:
        errors.append("assessment quality_delta_vs_baseline does not match the execution artifact")
    if assessment_long_context.get("pass_rate_delta_vs_baseline") != pass_rate_delta:
        errors.append("assessment pass_rate_delta_vs_baseline does not match the execution artifact")
    if assessment_long_context.get("kv_cache_saving_ratio_vs_baseline") != kv_saving_ratio:
        errors.append("assessment kv_cache_saving_ratio_vs_baseline does not match the execution artifact")

    expected_long_context_pass = (
        selected_bucket["proxy_pass_rate"] >= 1.0
        and quality_delta > -0.05
        and kv_saving_ratio > 0.0
    )
    expected_training_pass = (
        training_row["all_matrix_rows_finite"]
        and training_row["consistent_loss_advantage"]
        and training_row["final_loss_delta_vs_baseline_mean"] < 0.0
    )
    expected_benchmark_pass = (
        benchmark_row["mean_ratio_across_grid"] <= 1.0
        and benchmark_row["worst_ratio_across_grid"] <= 1.10
    )
    expected_recommendation = "promote" if (
        expected_long_context_pass and expected_training_pass and expected_benchmark_pass
    ) else "defer"

    if gates.get("long_context_pass") != expected_long_context_pass:
        errors.append("assessment long_context_pass gate is inconsistent with the execution artifact")
    if gates.get("training_pass") != expected_training_pass:
        errors.append("assessment training_pass gate is inconsistent with the training matrix")
    if gates.get("benchmark_pass") != expected_benchmark_pass:
        errors.append("assessment benchmark_pass gate is inconsistent with the benchmark matrix")
    if assessment.get("recommendation") != expected_recommendation:
        errors.append("assessment recommendation is inconsistent with the gate state")

    if stress_assessment is not None:
        if stress_assessment.get("variant") != variant:
            errors.append("stress assessment variant must be compressed_attention")
        if stress_assessment.get("reproduces_failure") not in {True, False}:
            errors.append("stress assessment must include reproduces_failure")
        if stress_assessment.get("speed_instability") not in {True, False}:
            errors.append("stress assessment must include speed_instability")

    if speed_tail_assessment is not None:
        if speed_tail_assessment.get("variant") != variant:
            errors.append("speed-tail assessment variant must be compressed_attention")
        if speed_tail_assessment.get("slow_row_fraction") is None:
            errors.append("speed-tail assessment must include slow_row_fraction")
        if speed_tail_assessment.get("dominant_steps") is None:
            errors.append("speed-tail assessment must include dominant_steps")

    if memo_bundle is not None:
        memo = memo_bundle.get("memo", {})
        bundled_assessment = memo_bundle.get("assessment")
        bundled_stress = memo_bundle.get("stress_assessment")
        bundled_speed_tail = memo_bundle.get("speed_tail_assessment")

        if bundled_assessment != assessment:
            errors.append("memo bundle assessment does not match the promotion assessment artifact")
        if stress_assessment is not None and bundled_stress != stress_assessment:
            errors.append("memo bundle stress assessment does not match the stress assessment artifact")
        if speed_tail_assessment is not None and bundled_speed_tail != speed_tail_assessment:
            errors.append("memo bundle speed-tail assessment does not match the speed-tail assessment artifact")

        if memo.get("variant") != variant:
            errors.append("memo variant must be compressed_attention")
        if memo.get("recommendation") != assessment.get("recommendation"):
            errors.append("memo recommendation does not match the promotion assessment")
        if memo.get("gates") != gates:
            errors.append("memo gates do not match the promotion assessment")

        summary_lines = memo.get("summary_lines", [])
        expected_stress_line = None
        if stress_assessment is not None:
            expected_stress_line = (
                f"Focused stress follow-up reproduces failure: `{str(bool(stress_assessment['reproduces_failure'])).lower()}`; "
                f"slow-tail persists: `{str(bool(stress_assessment['speed_instability'])).lower()}`."
            )
            if expected_stress_line not in summary_lines:
                errors.append("memo summary is missing the stress follow-up line")

        if speed_tail_assessment is not None:
            widest_slow_batch = max(
                speed_tail_assessment["batch_summaries"],
                key=lambda row: (row["slow_row_fraction"], row["mean_speed_ratio"]),
            )
            worst_tail_batch = max(
                speed_tail_assessment["batch_summaries"],
                key=lambda row: (row["worst_speed_ratio"], row["mean_speed_ratio"]),
            )
            dominant_steps = speed_tail_assessment["dominant_steps"]
            expected_speed_tail_line = (
                f"Short-context speed tail: broadest slow-row concentration at batch `{widest_slow_batch['batch_size']}` "
                f"(slow fraction `{widest_slow_batch['slow_row_fraction']:.3f}`), but worst tail at batch `{worst_tail_batch['batch_size']}` "
                f"with worst speed ratio `{worst_tail_batch['worst_speed_ratio']:.3f}` and step slice `{dominant_steps['steps']}`."
            )
            if expected_speed_tail_line not in summary_lines:
                errors.append("memo summary is missing the speed-tail line")

            expected_recommendation_line = (
                f"Treat batch `{widest_slow_batch['batch_size']}` as the broad slowdown slice and `{dominant_steps['steps']}` steps as the worst tail slice in the next training investigation."
            )
            if expected_recommendation_line not in memo.get("recommendations", []):
                errors.append("memo recommendations are missing the speed-tail investigation line")

    if remediation_plan is not None:
        if remediation_plan.get("variant") != variant:
            errors.append("remediation plan variant must be compressed_attention")
        if remediation_plan.get("promotion_recommendation") != assessment.get("recommendation"):
            errors.append("remediation plan recommendation does not match the promotion assessment")
        if remediation_plan.get("gates") != gates:
            errors.append("remediation plan gates do not match the promotion assessment")

        steps = remediation_plan.get("steps", [])
        priorities = [step.get("priority") for step in steps]
        if priorities != sorted(priorities):
            errors.append("remediation plan steps must be sorted by priority")

        if not gates.get("training_pass", False):
            worst_loss_row = stress_assessment.get("worst_loss_row") if stress_assessment else None
            expected_target = {
                "batch_size": worst_loss_row["batch_size"],
                "seq_len": worst_loss_row["seq_len"],
                "steps": worst_loss_row["steps"],
                "seed": worst_loss_row["seed"],
            } if worst_loss_row else None
            first_step = steps[0] if steps else None
            if first_step is None or first_step.get("target_slice") != expected_target:
                errors.append("remediation plan first step does not target the worst-loss stress row")

        if speed_tail_assessment is not None:
            widest_slow_batch = max(
                speed_tail_assessment["batch_summaries"],
                key=lambda row: (row["slow_row_fraction"], row["mean_speed_ratio"]),
            )
            dominant_steps = speed_tail_assessment["dominant_steps"]["steps"]
            expected_speed_line = (
                f"Treat batch `{widest_slow_batch['batch_size']}` as the broad slowdown slice and `{dominant_steps}` steps as the worst tail slice in the next training investigation."
            )
            remediation_titles = [step.get("title") for step in steps]
            if "Reduce broad short-context slowdown at the small batch slice" not in remediation_titles:
                errors.append("remediation plan is missing the broad short-context slowdown step")
            if "Eliminate the worst speed-tail event" not in remediation_titles:
                errors.append("remediation plan is missing the worst speed-tail step")
            if memo_bundle is not None:
                memo_recommendations = memo_bundle.get("memo", {}).get("recommendations", [])
                if expected_speed_line not in memo_recommendations:
                    errors.append("memo recommendations are missing the remediation-plan speed-tail line")

    if remediation_execution is not None:
        if remediation_execution.get("variant") != variant:
            errors.append("remediation execution variant must be compressed_attention")
        if remediation_plan is None:
            errors.append("remediation execution was provided without a remediation plan")
        else:
            plan_steps = sorted(remediation_plan.get("steps", []), key=lambda row: row.get("priority", 0))
            execution_steps = sorted(remediation_execution.get("execution_steps", []), key=lambda row: row.get("priority", 0))
            if len(plan_steps) != len(execution_steps):
                errors.append("remediation execution step count does not match the remediation plan")
            else:
                for plan_step, execution_step in zip(plan_steps, execution_steps, strict=True):
                    if plan_step.get("priority") != execution_step.get("priority"):
                        errors.append("remediation execution step priorities do not match the remediation plan")
                        break
                    if plan_step.get("title") != execution_step.get("title"):
                        errors.append("remediation execution step titles do not match the remediation plan")
                        break
                    if execution_step.get("skipped"):
                        continue
                    if plan_step.get("target_slice") != execution_step.get("target_slice"):
                        errors.append("remediation execution target slice does not match the remediation plan")
                        break
                    variant_row = execution_step.get("variant_row", {})
                    success_checks = execution_step.get("success_checks", {})
                    expected_checks = {
                        "loss_nonpositive": variant_row.get("final_loss_delta_vs_baseline_mean", 1.0) <= 0.0,
                        "speed_at_or_below_baseline": variant_row.get("mean_step_ms_ratio_vs_baseline_mean", 2.0) <= 1.0,
                        "finite_runs": bool(variant_row.get("all_runs_finite", False)),
                    }
                    if success_checks != expected_checks:
                        errors.append("remediation execution success checks do not match the reported variant row")
                        break
                    if execution_step.get("all_success_checks_passed") != all(expected_checks.values()):
                        errors.append("remediation execution all_success_checks_passed does not match the success checks")
                        break

    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate that compressed_attention promotion artifacts agree across long-context, training, systems, and assessment layers."
    )
    parser.add_argument("--training-matrix", required=True)
    parser.add_argument("--benchmark-matrix", required=True)
    parser.add_argument("--long-context-execution", required=True)
    parser.add_argument("--assessment", required=True)
    parser.add_argument("--stress-assessment", required=False)
    parser.add_argument("--speed-tail-assessment", required=False)
    parser.add_argument("--memo-json", required=False)
    parser.add_argument("--remediation-plan", required=False)
    parser.add_argument("--remediation-execution", required=False)
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    errors = validate_compressed_attention_promotion_artifacts(
        load_json(args.training_matrix),
        load_json(args.benchmark_matrix),
        load_json(args.long_context_execution),
        load_json(args.assessment),
        load_json(args.stress_assessment) if args.stress_assessment else None,
        load_json(args.speed_tail_assessment) if args.speed_tail_assessment else None,
        load_json(args.memo_json) if args.memo_json else None,
        load_json(args.remediation_plan) if args.remediation_plan else None,
        load_json(args.remediation_execution) if args.remediation_execution else None,
    )
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if args.stdout:
        print("compressed_attention promotion artifacts are consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
