from __future__ import annotations

from arch_adv_2026.long_context_variant_report import render_long_context_variant_report_markdown


def test_render_long_context_variant_report_contains_core_sections() -> None:
    artifact = {
        "baseline_config": "/tmp/baseline.json",
        "variant_configs": ["/tmp/a.json", "/tmp/b.json"],
        "filler_repeat_values": [32, 256],
        "cases_per_length": 2,
        "sweep_runs": 2,
        "case_result_count": 12,
        "notes": ["note a"],
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
                "mean_proxy_pass_probability": 0.955,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 400,
                "estimated_kv_saving_ratio_at_max_seq": 0.6,
                "estimated_total_params": 120,
            },
            {
                "variant_kind": "mhc",
                "filler_repeats": 256,
                "mean_proxy_pass_probability": 0.999,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
                "estimated_total_params": 140,
            },
        ],
    }
    markdown = render_long_context_variant_report_markdown(artifact)
    assert "# Long-Context Variant Proxy Report" in markdown
    assert "## Bottom line" in markdown
    assert "## Longest Context Ranking" in markdown
    assert "## All Buckets" in markdown
    assert "## Context" in markdown


def test_render_long_context_variant_report_prefers_strong_quality_tradeoff() -> None:
    artifact = {
        "baseline_config": "/tmp/baseline.json",
        "variant_configs": ["/tmp/a.json", "/tmp/b.json"],
        "filler_repeat_values": [256],
        "cases_per_length": 2,
        "sweep_runs": 1,
        "case_result_count": 6,
        "notes": [],
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
    markdown = render_long_context_variant_report_markdown(artifact)
    assert "Best memory-aware quality tradeoff at the longest context: `kv_sharing`" in markdown
