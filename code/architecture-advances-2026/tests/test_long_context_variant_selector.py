from __future__ import annotations

from arch_adv_2026.long_context_variant_selector import build_variant_selector_artifact


def test_build_variant_selector_artifact_filters_by_proxy_quality() -> None:
    artifact = {
        "baseline_config": "/tmp/baseline.json",
        "variant_configs": ["/tmp/a.json", "/tmp/b.json"],
        "filler_repeat_values": [32, 256],
        "variant_buckets": [
            {
                "variant_kind": "baseline",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.995,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
                "estimated_total_params": 100,
            },
            {
                "variant_kind": "history_compression",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.930,
                "proxy_pass_rate": 0.75,
                "estimated_kv_cache_bytes_at_max_seq": 300,
                "estimated_kv_saving_ratio_at_max_seq": 0.7,
                "estimated_total_params": 120,
            },
            {
                "variant_kind": "kv_sharing",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.970,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
                "estimated_total_params": 110,
            },
        ],
    }
    selector = build_variant_selector_artifact(artifact, min_proxy_quality=0.95)
    assert selector["recommendations"]["quality"]["variant_kind"] == "baseline"
    assert selector["recommendations"]["memory"]["variant_kind"] == "kv_sharing"
    assert selector["recommendations"]["quality_preserving_memory"]["variant_kind"] == "kv_sharing"
    assert selector["recommendations"]["balanced"]["variant_kind"] == "baseline"


def test_build_variant_selector_artifact_falls_back_when_needed() -> None:
    artifact = {
        "baseline_config": "/tmp/baseline.json",
        "variant_configs": ["/tmp/a.json"],
        "filler_repeat_values": [256],
        "variant_buckets": [
            {
                "variant_kind": "history_compression",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.90,
                "proxy_pass_rate": 0.5,
                "estimated_kv_cache_bytes_at_max_seq": 300,
                "estimated_kv_saving_ratio_at_max_seq": 0.7,
                "estimated_total_params": 120,
            }
        ],
    }
    selector = build_variant_selector_artifact(artifact, min_proxy_quality=0.95)
    assert selector["selection_policy"]["used_fallback_rows"] is True
    assert selector["recommendations"]["memory"]["variant_kind"] == "history_compression"
