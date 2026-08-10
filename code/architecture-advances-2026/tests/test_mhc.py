from __future__ import annotations

from pathlib import Path

from arch_adv_2026.benchmark import compare_numeric_benchmarks
from arch_adv_2026.config import load_config
from arch_adv_2026.numeric_runtime import describe_numeric_demo
from arch_adv_2026.summary import build_summary


ROOT = Path(__file__).resolve().parents[1]


def test_mhc_summary_reports_residual_stream_shape() -> None:
    config = load_config(ROOT / "configs" / "tiny-mhc.json")
    summary = build_summary(config)
    assert summary["residual_path"]["kind"] == "mhc"
    assert summary["residual_path"]["residual_stream_count"] == 3
    assert summary["residual_path"]["residual_mix_rank"] == 96
    assert summary["residual_path"]["extra_params_per_layer"] > 0


def test_mhc_increases_parameter_estimate_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "tiny-baseline.json")
    mhc = load_config(ROOT / "configs" / "tiny-mhc.json")
    baseline_summary = build_summary(baseline)
    mhc_summary = build_summary(mhc)
    assert mhc_summary["params"]["layers_total"] > baseline_summary["params"]["layers_total"]
    assert mhc_summary["params"]["total"] > baseline_summary["params"]["total"]


def test_mhc_numeric_demo_runs() -> None:
    config = load_config(ROOT / "configs" / "micro-mhc.json")
    result = describe_numeric_demo(config, seq_len=4, seed=47)
    assert result["numeric_run"]["output_shape"] == [1, 4, config.d_model]
    assert result["numeric_run"]["estimated_kv_cache_bytes"] > 0


def test_mhc_increases_estimated_flops_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    mhc = load_config(ROOT / "configs" / "micro-mhc.json")
    result = compare_numeric_benchmarks(
        baseline,
        mhc,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=53,
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_flops"]
        > result["demo_context"]["baseline"]["numeric_run"]["estimated_flops"]
    )
