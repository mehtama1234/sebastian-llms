from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.benchmark import compare_numeric_benchmarks
from arch_adv_2026.numeric_runtime import describe_numeric_demo
from arch_adv_2026.summary import build_summary


ROOT = Path(__file__).resolve().parents[1]


def test_ple_summary_marks_variant_enabled() -> None:
    config = load_config(ROOT / "configs" / "tiny-ple.json")
    summary = build_summary(config)
    assert summary["shape"]["ple_enabled"] is True


def test_ple_increases_embedding_parameter_estimate() -> None:
    baseline = load_config(ROOT / "configs" / "tiny-baseline.json")
    ple = load_config(ROOT / "configs" / "tiny-ple.json")
    baseline_summary = build_summary(baseline)
    ple_summary = build_summary(ple)
    assert ple_summary["params"]["embedding"] > baseline_summary["params"]["embedding"]
    assert ple_summary["params"]["total"] > baseline_summary["params"]["total"]


def test_ple_numeric_demo_runs() -> None:
    config = load_config(ROOT / "configs" / "micro-ple.json")
    result = describe_numeric_demo(config, seq_len=4, seed=13)
    assert result["numeric_run"]["output_shape"] == [1, 4, config.d_model]
    assert result["numeric_run"]["estimated_flops"] > 0


def test_ple_increases_estimated_flops_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    ple = load_config(ROOT / "configs" / "micro-ple.json")
    result = compare_numeric_benchmarks(
        baseline,
        ple,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=17,
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_flops"]
        > result["demo_context"]["baseline"]["numeric_run"]["estimated_flops"]
    )
