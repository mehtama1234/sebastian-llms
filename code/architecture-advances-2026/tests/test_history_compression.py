from __future__ import annotations

from pathlib import Path

from arch_adv_2026.benchmark import compare_numeric_benchmarks
from arch_adv_2026.config import load_config
from arch_adv_2026.numeric_runtime import describe_numeric_demo
from arch_adv_2026.summary import build_summary


ROOT = Path(__file__).resolve().parents[1]


def test_history_compression_summary_reports_recent_window_and_ratio() -> None:
    config = load_config(ROOT / "configs" / "tiny-history-compression.json")
    summary = build_summary(config)
    assert summary["history_path"]["kind"] == "history_compression"
    assert summary["history_path"]["recent_window_size"] == 512
    assert summary["history_path"]["history_compression_ratio"] == 8
    assert summary["history_path"]["effective_history_tokens_at_max_seq"] < config.max_seq_len


def test_history_compression_reduces_kv_cache_estimate_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "tiny-baseline.json")
    variant = load_config(ROOT / "configs" / "tiny-history-compression.json")
    baseline_summary = build_summary(baseline)
    variant_summary = build_summary(variant)
    assert variant_summary["kv_cache"]["variant_bytes_at_max_seq"] < baseline_summary["kv_cache"]["variant_bytes_at_max_seq"]
    assert variant_summary["kv_cache"]["saving_ratio"] > 0.0


def test_history_compression_numeric_demo_runs_with_shorter_cache() -> None:
    config = load_config(ROOT / "configs" / "micro-history-compression.json")
    result = describe_numeric_demo(config, seq_len=16, seed=59)
    assert result["numeric_run"]["output_shape"] == [1, 16, config.d_model]
    assert result["numeric_run"]["cache_shapes"][0][2] < 16


def test_history_compression_reduces_estimated_flops_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variant = load_config(ROOT / "configs" / "micro-history-compression.json")
    result = compare_numeric_benchmarks(
        baseline,
        variant,
        seq_len=16,
        warmup_runs=0,
        measured_runs=1,
        seed=61,
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_flops"]
        < result["demo_context"]["baseline"]["numeric_run"]["estimated_flops"]
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_kv_cache_bytes"]
        < result["demo_context"]["baseline"]["numeric_run"]["estimated_kv_cache_bytes"]
    )
