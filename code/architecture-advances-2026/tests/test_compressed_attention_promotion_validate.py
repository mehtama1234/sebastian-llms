from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from arch_adv_2026.compressed_attention_promotion_validate import (
    validate_compressed_attention_promotion_artifacts,
)


def _artifacts() -> tuple[dict, dict, dict, dict, dict, dict, dict, dict]:
    training = {
        "variant_trends": [
            {
                "variant": "compressed_attention",
                "all_matrix_rows_finite": True,
                "final_loss_delta_vs_baseline_mean": 1.5,
                "consistent_loss_advantage": False,
            }
        ]
    }
    benchmark = {
        "variant_summary_rows": [
            {
                "variant": "compressed_attention",
                "mean_ratio_across_grid": 0.9,
                "worst_ratio_across_grid": 1.05,
            }
        ]
    }
    execution = {
        "selected_variant_kind": "compressed_attention",
        "delta": {"kv_cache_saving_ratio_vs_baseline": 0.5},
        "focused_compare_summary": {
            "selected_bucket": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.96,
                "proxy_pass_rate": 1.0,
            },
            "baseline_bucket": {
                "variant_kind": "baseline",
                "mean_proxy_pass_probability": 0.995,
                "proxy_pass_rate": 1.0,
            },
        },
    }
    assessment = {
        "variant": "compressed_attention",
        "recommendation": "defer",
        "gates": {
            "long_context_pass": True,
            "training_pass": False,
            "benchmark_pass": True,
        },
        "long_context": {
            "quality_delta_vs_baseline": -0.03500000000000003,
            "pass_rate_delta_vs_baseline": 0.0,
            "kv_cache_saving_ratio_vs_baseline": 0.5,
            "selected_bucket": execution["focused_compare_summary"]["selected_bucket"],
            "baseline_bucket": execution["focused_compare_summary"]["baseline_bucket"],
        },
        "training": training["variant_trends"][0],
        "benchmark": benchmark["variant_summary_rows"][0],
    }
    stress_assessment = {
        "variant": "compressed_attention",
        "reproduces_failure": True,
        "speed_instability": True,
        "worst_loss_row": {"batch_size": 2, "seq_len": 8, "steps": 4, "seed": 31},
        "slowest_row": {"batch_size": 4, "seq_len": 8, "steps": 8, "seed": 31},
    }
    speed_tail_assessment = {
        "variant": "compressed_attention",
        "batch_summaries": [
            {"batch_size": 2, "slow_row_fraction": 0.8, "mean_speed_ratio": 1.3, "worst_speed_ratio": 1.9},
            {"batch_size": 4, "slow_row_fraction": 0.3, "mean_speed_ratio": 2.1, "worst_speed_ratio": 8.8},
        ],
        "dominant_steps": {"steps": 8},
        "slow_row_fraction": 0.5,
    }
    memo_bundle = {
        "memo": {
            "variant": "compressed_attention",
            "recommendation": "defer",
            "gates": assessment["gates"],
            "summary_lines": [
                "Focused stress follow-up reproduces failure: `true`; slow-tail persists: `true`.",
                "Short-context speed tail: broadest slow-row concentration at batch `2` (slow fraction `0.800`), but worst tail at batch `4` with worst speed ratio `8.800` and step slice `8`.",
            ],
            "recommendations": [
                "Treat batch `2` as the broad slowdown slice and `8` steps as the worst tail slice in the next training investigation.",
            ],
        },
        "assessment": assessment,
        "stress_assessment": stress_assessment,
        "speed_tail_assessment": speed_tail_assessment,
    }
    remediation_plan = {
        "variant": "compressed_attention",
        "promotion_recommendation": "defer",
        "gates": assessment["gates"],
        "steps": [
            {
                "priority": 1,
                "title": "Stabilize short-context training loss",
                "target_slice": {"batch_size": 2, "seq_len": 8, "steps": 4, "seed": 31},
            },
            {
                "priority": 2,
                "title": "Reduce broad short-context slowdown at the small batch slice",
                "target_slice": {"batch_size": 2, "seq_len": 8, "steps": 8},
            },
            {
                "priority": 3,
                "title": "Eliminate the worst speed-tail event",
                "target_slice": {"batch_size": 4, "seq_len": 8, "steps": 8, "seed": 31},
            },
        ],
    }
    remediation_execution = {
        "variant": "compressed_attention",
        "execution_steps": [
            {
                "priority": 1,
                "title": "Stabilize short-context training loss",
                "target_slice": {"batch_size": 2, "seq_len": 8, "steps": 4, "seed": 31},
                "variant_row": {
                    "final_loss_delta_vs_baseline_mean": 1.2,
                    "mean_step_ms_ratio_vs_baseline_mean": 0.8,
                    "all_runs_finite": True,
                },
                "success_checks": {
                    "loss_nonpositive": False,
                    "speed_at_or_below_baseline": True,
                    "finite_runs": True,
                },
                "all_success_checks_passed": False,
            },
            {
                "priority": 2,
                "title": "Reduce broad short-context slowdown at the small batch slice",
                "target_slice": {"batch_size": 2, "seq_len": 8, "steps": 8},
                "variant_row": {
                    "final_loss_delta_vs_baseline_mean": 0.5,
                    "mean_step_ms_ratio_vs_baseline_mean": 1.1,
                    "all_runs_finite": True,
                },
                "success_checks": {
                    "loss_nonpositive": False,
                    "speed_at_or_below_baseline": False,
                    "finite_runs": True,
                },
                "all_success_checks_passed": False,
            },
            {
                "priority": 3,
                "title": "Eliminate the worst speed-tail event",
                "target_slice": {"batch_size": 4, "seq_len": 8, "steps": 8, "seed": 31},
                "variant_row": {
                    "final_loss_delta_vs_baseline_mean": 0.2,
                    "mean_step_ms_ratio_vs_baseline_mean": 0.9,
                    "all_runs_finite": True,
                },
                "success_checks": {
                    "loss_nonpositive": False,
                    "speed_at_or_below_baseline": True,
                    "finite_runs": True,
                },
                "all_success_checks_passed": False,
            },
        ],
    }
    return training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution


def test_validate_compressed_attention_promotion_artifacts_accepts_consistent_state() -> None:
    training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution = _artifacts()
    speed_tail_assessment = memo_bundle["speed_tail_assessment"]
    assert (
        validate_compressed_attention_promotion_artifacts(
            training,
            benchmark,
            execution,
            assessment,
            stress_assessment,
            speed_tail_assessment,
            memo_bundle,
            remediation_plan,
            remediation_execution,
        )
        == []
    )


def test_validate_compressed_attention_promotion_artifacts_flags_bad_recommendation() -> None:
    training, benchmark, execution, assessment, _, _, _, _ = _artifacts()
    assessment["recommendation"] = "promote"
    errors = validate_compressed_attention_promotion_artifacts(training, benchmark, execution, assessment)
    assert "assessment recommendation is inconsistent with the gate state" in errors


def test_validate_compressed_attention_promotion_artifacts_flags_memo_speed_tail_drift() -> None:
    training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution = _artifacts()
    speed_tail_assessment = memo_bundle["speed_tail_assessment"]
    memo_bundle["memo"]["summary_lines"][-1] = "bad summary"
    errors = validate_compressed_attention_promotion_artifacts(
        training,
        benchmark,
        execution,
        assessment,
        stress_assessment,
        speed_tail_assessment,
        memo_bundle,
        remediation_plan,
        remediation_execution,
    )
    assert "memo summary is missing the speed-tail line" in errors


def test_validate_compressed_attention_promotion_artifacts_flags_remediation_drift() -> None:
    training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution = _artifacts()
    speed_tail_assessment = memo_bundle["speed_tail_assessment"]
    remediation_plan["steps"][0]["target_slice"]["seed"] = 99
    errors = validate_compressed_attention_promotion_artifacts(
        training,
        benchmark,
        execution,
        assessment,
        stress_assessment,
        speed_tail_assessment,
        memo_bundle,
        remediation_plan,
        remediation_execution,
    )
    assert "remediation plan first step does not target the worst-loss stress row" in errors


def test_validate_compressed_attention_promotion_artifacts_flags_remediation_execution_drift() -> None:
    training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution = _artifacts()
    speed_tail_assessment = memo_bundle["speed_tail_assessment"]
    remediation_execution["execution_steps"][1]["success_checks"]["speed_at_or_below_baseline"] = True
    errors = validate_compressed_attention_promotion_artifacts(
        training,
        benchmark,
        execution,
        assessment,
        stress_assessment,
        speed_tail_assessment,
        memo_bundle,
        remediation_plan,
        remediation_execution,
    )
    assert "remediation execution success checks do not match the reported variant row" in errors


def test_compressed_attention_promotion_validate_cli_writes_failures_to_stderr(tmp_path: Path) -> None:
    training, benchmark, execution, assessment, stress_assessment, memo_bundle, remediation_plan, remediation_execution = _artifacts()
    speed_tail_assessment = memo_bundle["speed_tail_assessment"]
    assessment["gates"]["benchmark_pass"] = False

    training_path = tmp_path / "training.json"
    benchmark_path = tmp_path / "benchmark.json"
    execution_path = tmp_path / "execution.json"
    assessment_path = tmp_path / "assessment.json"
    stress_path = tmp_path / "stress.json"
    speed_tail_path = tmp_path / "speed_tail.json"
    memo_path = tmp_path / "memo.json"
    remediation_path = tmp_path / "remediation.json"
    remediation_execution_path = tmp_path / "remediation_execution.json"
    training_path.write_text(json.dumps(training), encoding="utf-8")
    benchmark_path.write_text(json.dumps(benchmark), encoding="utf-8")
    execution_path.write_text(json.dumps(execution), encoding="utf-8")
    assessment_path.write_text(json.dumps(assessment), encoding="utf-8")
    stress_path.write_text(json.dumps(stress_assessment), encoding="utf-8")
    speed_tail_path.write_text(json.dumps(speed_tail_assessment), encoding="utf-8")
    memo_path.write_text(json.dumps(memo_bundle), encoding="utf-8")
    remediation_path.write_text(json.dumps(remediation_plan), encoding="utf-8")
    remediation_execution_path.write_text(json.dumps(remediation_execution), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arch_adv_2026.compressed_attention_promotion_validate",
            "--training-matrix",
            str(training_path),
            "--benchmark-matrix",
            str(benchmark_path),
            "--long-context-execution",
            str(execution_path),
            "--assessment",
            str(assessment_path),
            "--stress-assessment",
            str(stress_path),
            "--speed-tail-assessment",
            str(speed_tail_path),
            "--memo-json",
            str(memo_path),
            "--remediation-plan",
            str(remediation_path),
            "--remediation-execution",
            str(remediation_execution_path),
        ],
        cwd=tmp_path.parent,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "benchmark_pass gate is inconsistent" in result.stderr
    assert result.stdout == ""
