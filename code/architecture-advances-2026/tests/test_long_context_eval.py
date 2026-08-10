from __future__ import annotations

from arch_adv_2026.long_context_eval import (
    _group_bucket_summaries,
    _group_rows_by_filler_repeats,
    build_synthetic_cases,
    build_sweep_cases,
    score_answer,
)


def test_build_synthetic_cases_is_deterministic() -> None:
    cases_a = build_synthetic_cases(num_cases=2, seed=7, filler_repeats=12)
    cases_b = build_synthetic_cases(num_cases=2, seed=7, filler_repeats=12)
    assert [case.answer for case in cases_a] == [case.answer for case in cases_b]
    assert [case.name for case in cases_a] == ["passkey_0", "needle_1"]


def test_synthetic_cases_include_expected_metadata() -> None:
    case = build_synthetic_cases(num_cases=1, seed=3, filler_repeats=12)[0]
    assert case.task_type == "passkey_retrieval"
    assert case.metadata is not None
    assert case.metadata["filler_repeats"] == 12


def test_score_answer_supports_exact_and_substring() -> None:
    assert score_answer("12345", "12345", match="exact") is True
    assert score_answer("the code is 12345", "12345", match="substring") is True
    assert score_answer("wrong", "12345", match="substring") is False


def test_build_sweep_cases_covers_each_requested_length() -> None:
    cases = build_sweep_cases(filler_repeat_values=[8, 16], cases_per_length=2, seed=4)
    filler_values = [case.metadata["filler_repeats"] for case in cases if case.metadata]
    assert filler_values.count(8) == 2
    assert filler_values.count(16) == 2


def test_group_rows_by_filler_repeats_summarizes_buckets() -> None:
    rows = [
        {
            "passed": True,
            "elapsed_ms": 10.0,
            "input_token_count": 100,
            "output_token_count": 104,
            "generated_token_count": 4,
            "generated_tokens_per_second": 400.0,
            "total_tokens_per_second": 10400.0,
            "estimated_kv_cache_bytes": 6400,
            "metadata": {"filler_repeats": 8},
        },
        {
            "passed": False,
            "elapsed_ms": 14.0,
            "input_token_count": 110,
            "output_token_count": 115,
            "generated_token_count": 5,
            "generated_tokens_per_second": 357.0,
            "total_tokens_per_second": 8214.0,
            "estimated_kv_cache_bytes": 7040,
            "metadata": {"filler_repeats": 8},
        },
        {
            "passed": True,
            "elapsed_ms": 20.0,
            "input_token_count": 200,
            "output_token_count": 206,
            "generated_token_count": 6,
            "generated_tokens_per_second": 300.0,
            "total_tokens_per_second": 10300.0,
            "estimated_kv_cache_bytes": 12800,
            "metadata": {"filler_repeats": 16},
        },
    ]
    summaries = _group_rows_by_filler_repeats(rows)
    assert summaries[0]["filler_repeats"] == 8
    assert summaries[0]["pass_rate"] == 0.5
    assert summaries[0]["mean_estimated_kv_cache_bytes"] == 6720
    assert summaries[1]["filler_repeats"] == 16
    assert summaries[1]["num_cases"] == 1


def test_group_bucket_summaries_aggregates_across_runs() -> None:
    bucket_runs = [
        [
            {
                "filler_repeats": 8,
                "num_cases": 2,
                "pass_rate": 0.5,
                "mean_elapsed_ms": 10.0,
                "mean_generated_tokens_per_second": 2.0,
                "mean_total_tokens_per_second": 20.0,
                "mean_estimated_kv_cache_bytes": 1000.0,
            }
        ],
        [
            {
                "filler_repeats": 8,
                "num_cases": 2,
                "pass_rate": 1.0,
                "mean_elapsed_ms": 14.0,
                "mean_generated_tokens_per_second": 1.0,
                "mean_total_tokens_per_second": 10.0,
                "mean_estimated_kv_cache_bytes": 1200.0,
            }
        ],
    ]
    summaries = _group_bucket_summaries(bucket_runs)
    assert summaries[0]["filler_repeats"] == 8
    assert summaries[0]["num_runs"] == 2
    assert summaries[0]["mean_pass_rate"] == 0.75
    assert summaries[0]["pass_rate_stdev"] == 0.25
