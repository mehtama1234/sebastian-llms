from __future__ import annotations

from pathlib import Path

import pytest

from arch_adv_2026.benchmark import (
    benchmark_numeric_demo,
    benchmark_torch_demo,
    compare_numeric_benchmarks,
    compare_torch_benchmarks,
)
from arch_adv_2026.config import load_config
from arch_adv_2026.torch_model import check_torch


ROOT = Path(__file__).resolve().parents[1]
TORCH_AVAILABLE = check_torch().available


def test_benchmark_returns_positive_timings() -> None:
    config = load_config(ROOT / "configs" / "micro-baseline.json")
    result = benchmark_numeric_demo(config, seq_len=4, warmup_runs=0, measured_runs=2, seed=1)
    assert len(result.timings_ms) == 2
    assert all(t > 0 for t in result.timings_ms)
    assert result.owner_cache_count == config.n_layers


def test_benchmark_comparison_captures_cache_delta() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variant = load_config(ROOT / "configs" / "micro-kv-sharing.json")
    result = compare_numeric_benchmarks(
        baseline,
        variant,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=2,
    )
    assert result["baseline"]["owner_cache_count"] == 4
    assert result["variant"]["owner_cache_count"] == 2
    assert result["comparison"]["owner_cache_delta"] == -2
    assert result["demo_context"]["variant"]["numeric_run"]["estimated_kv_cache_bytes_saved"] > 0


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_benchmark_returns_positive_timings() -> None:
    config = load_config(ROOT / "configs" / "micro-baseline.json")
    result = benchmark_torch_demo(config, seq_len=2, warmup_runs=0, measured_runs=1, seed=1)
    assert len(result.timings_ms) == 1
    assert result.timings_ms[0] > 0
    assert result.owner_cache_count == config.n_layers


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_benchmark_comparison_returns_variant_demo_context() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variant = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = compare_torch_benchmarks(
        baseline,
        variant,
        seq_len=2,
        warmup_runs=0,
        measured_runs=1,
        seed=2,
    )
    assert result["variant"]["variant"] == "compressed_attention"
    assert result["demo_context"]["variant"]["torch_run"]["owner_cache_count"] == variant.n_layers


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_benchmark_history_compression_reflects_shorter_cache() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variant = load_config(ROOT / "configs" / "micro-history-compression.json")
    result = compare_torch_benchmarks(
        baseline,
        variant,
        seq_len=8,
        warmup_runs=0,
        measured_runs=1,
        seed=5,
    )
    assert result["variant"]["variant"] == "history_compression"
    assert result["demo_context"]["variant"]["torch_run"]["cache_shapes"][0] == [1, 2, 5, 16]
