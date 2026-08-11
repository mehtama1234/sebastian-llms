from __future__ import annotations

from pathlib import Path

from arch_adv_2026.benchmark import compare_numeric_benchmarks
from arch_adv_2026.config import load_config
from arch_adv_2026.numeric_runtime import describe_numeric_demo
from arch_adv_2026.summary import build_summary


ROOT = Path(__file__).resolve().parents[1]


def test_compressed_attention_summary_reports_effective_head_dim() -> None:
    config = load_config(ROOT / "configs" / "tiny-compressed-attention.json")
    summary = build_summary(config)
    assert summary["shape"]["compressed_head_dim"] == 32
    assert summary["shape"]["effective_attn_head_dim"] == 32


def test_compressed_attention_reduces_kv_cache_estimate() -> None:
    baseline = load_config(ROOT / "configs" / "tiny-baseline.json")
    compressed = load_config(ROOT / "configs" / "tiny-compressed-attention.json")
    baseline_summary = build_summary(baseline)
    compressed_summary = build_summary(compressed)
    assert compressed_summary["kv_cache"]["variant_bytes_at_max_seq"] < baseline_summary["kv_cache"]["variant_bytes_at_max_seq"]


def test_compressed_attention_numeric_demo_runs() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = describe_numeric_demo(config, seq_len=16, seed=19)
    assert result["numeric_run"]["output_shape"] == [1, 16, config.d_model]
    assert result["numeric_run"]["estimated_kv_cache_bytes"] > 0


def test_compressed_attention_reduces_estimated_flops_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    compressed = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = compare_numeric_benchmarks(
        baseline,
        compressed,
        seq_len=16,
        warmup_runs=0,
        measured_runs=1,
        seed=23,
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_flops"]
        < result["demo_context"]["baseline"]["numeric_run"]["estimated_flops"]
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_kv_cache_bytes"]
        < result["demo_context"]["baseline"]["numeric_run"]["estimated_kv_cache_bytes"]
    )


def test_compressed_attention_uses_baseline_head_dim_below_threshold() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = describe_numeric_demo(config, seq_len=8, seed=19)
    assert result["numeric_run"]["cache_shapes"][0] == [1, 2, 8, 16]
