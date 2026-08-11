from __future__ import annotations

from arch_adv_2026.long_context_report import render_long_context_report_markdown


def test_render_long_context_report_markdown_contains_core_sections() -> None:
    artifact = {
        "model_id": "Qwen/Qwen3-0.6B",
        "num_cases": 4,
        "pass_rate": 0.5,
        "notes": ["note a"],
        "sweep": {
            "filler_repeat_values": [8, 16],
            "cases_per_length": 2,
            "sweep_runs": 2,
            "length_buckets": [
                {
                    "filler_repeats": 8,
                    "num_runs": 2,
                    "num_cases_per_run": 2,
                    "mean_pass_rate": 0.5,
                    "pass_rate_stdev": 0.1,
                    "mean_elapsed_ms": 100.0,
                    "elapsed_ms_stdev": 10.0,
                    "mean_generated_tokens_per_second": 2.0,
                    "mean_total_tokens_per_second": 20.0,
                    "mean_estimated_kv_cache_bytes": 1000.0,
                },
                {
                    "filler_repeats": 16,
                    "num_runs": 2,
                    "num_cases_per_run": 2,
                    "mean_pass_rate": 0.25,
                    "pass_rate_stdev": 0.2,
                    "mean_elapsed_ms": 120.0,
                    "elapsed_ms_stdev": 20.0,
                    "mean_generated_tokens_per_second": 1.5,
                    "mean_total_tokens_per_second": 18.0,
                    "mean_estimated_kv_cache_bytes": 2000.0,
                },
            ],
        },
    }
    markdown = render_long_context_report_markdown(artifact)
    assert "# Long-Context Sweep Report" in markdown
    assert "## Bottom line" in markdown
    assert "## Length Buckets" in markdown
    assert "## Context" in markdown
    assert "Mean KV Cache Bytes" in markdown
