from __future__ import annotations

from pathlib import Path

from arch_adv_2026.long_context_variant_compare import build_variant_long_context_compare


ROOT = Path(__file__).resolve().parents[1]


def test_variant_compare_contains_baseline_and_variants() -> None:
    result = build_variant_long_context_compare(
        baseline_config_path=ROOT / "configs" / "qwen3-baseline.json",
        variant_config_paths=[
            ROOT / "configs" / "qwen3-kv-sharing.json",
            ROOT / "configs" / "qwen3-history-compression.json",
        ],
        filler_repeat_values=[32, 256],
        cases_per_length=2,
        seed=5,
        sweep_runs=1,
    )
    kinds = {row["variant_kind"] for row in result["variant_buckets"]}
    assert "baseline" in kinds
    assert "kv_sharing" in kinds
    assert "history_compression" in kinds
    assert result["case_result_count"] == 12


def test_variant_compare_penalizes_history_compression_on_longer_contexts() -> None:
    result = build_variant_long_context_compare(
        baseline_config_path=ROOT / "configs" / "qwen3-baseline.json",
        variant_config_paths=[ROOT / "configs" / "qwen3-history-compression.json"],
        filler_repeat_values=[32, 256],
        cases_per_length=2,
        seed=7,
        sweep_runs=1,
    )
    buckets = {
        (row["variant_kind"], row["filler_repeats"]): row
        for row in result["variant_buckets"]
    }
    baseline_long = buckets[("baseline", 256)]
    history_long = buckets[("history_compression", 256)]
    assert history_long["estimated_kv_cache_bytes_at_max_seq"] < baseline_long["estimated_kv_cache_bytes_at_max_seq"]
    assert history_long["mean_proxy_pass_probability"] < baseline_long["mean_proxy_pass_probability"]
