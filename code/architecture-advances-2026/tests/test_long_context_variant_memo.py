from __future__ import annotations

from arch_adv_2026.long_context_variant_memo import (
    generate_long_context_variant_memo,
    render_long_context_variant_memo_markdown,
)


def _selector() -> dict:
    return {
        "selection_policy": {
            "longest_context_filler_repeats": 256,
            "minimum_proxy_quality": 0.95,
            "acceptable_row_count": 6,
            "total_row_count": 7,
            "used_fallback_rows": False,
        },
        "recommendations": {
            "quality": {
                "variant_kind": "mhc",
                "mean_proxy_pass_probability": 0.999,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 1000,
                "estimated_kv_saving_ratio_at_max_seq": 0.0,
                "estimated_total_params": 140,
            },
            "memory": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.955,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
                "estimated_total_params": 110,
            },
            "quality_preserving_memory": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.955,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
                "estimated_total_params": 110,
            },
            "balanced": {
                "variant_kind": "compressed_attention",
                "mean_proxy_pass_probability": 0.955,
                "proxy_pass_rate": 1.0,
                "estimated_kv_cache_bytes_at_max_seq": 500,
                "estimated_kv_saving_ratio_at_max_seq": 0.5,
                "estimated_total_params": 110,
            },
        },
    }


def test_generate_long_context_variant_memo_contains_expected_recommendation() -> None:
    memo = generate_long_context_variant_memo(_selector())
    assert memo["headline"] == "Long-context variant proxy decision memo"
    assert any("compressed_attention" in line for line in memo["recommendations"])


def test_render_long_context_variant_memo_markdown_contains_core_sections() -> None:
    selector = _selector()
    report = {"variant_configs": ["/tmp/a.json"], "cases_per_length": 2, "sweep_runs": 2}
    memo = generate_long_context_variant_memo(selector, report)
    markdown = render_long_context_variant_memo_markdown(memo, selector, report)
    assert "# Long-context variant proxy decision memo" in markdown
    assert "## Bottom line" in markdown
    assert "## Recommendations" in markdown
    assert "## Selector Picks" in markdown
    assert "## Policy" in markdown
