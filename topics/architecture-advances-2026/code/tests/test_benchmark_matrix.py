from __future__ import annotations

from pathlib import Path

from arch_adv_2026.benchmark_matrix import build_benchmark_matrix, render_benchmark_matrix_markdown


ROOT = Path(__file__).resolve().parents[1]


def test_build_benchmark_matrix_covers_requested_grid() -> None:
    matrix = build_benchmark_matrix(
        ROOT,
        batch_sizes=[1, 2],
        seq_lens=[4, 8],
        warmup_runs=0,
        measured_runs=1,
        report_runs=1,
        seed=7,
    )

    assert matrix["summary"]["grid_cell_count"] == 4
    assert matrix["baseline"]["batch_sizes"] == [1, 2]
    assert matrix["baseline"]["seq_lens"] == [4, 8]
    assert len(matrix["grid_reports"]) == 4
    assert "best_mean_runtime_variants" in matrix["summary"]
    assert "best_worst_case_runtime_variants" in matrix["summary"]
    assert "lowest_kv_variants" in matrix["summary"]
    assert all("median_ratio_across_grid" in row for row in matrix["variant_summary_rows"])
    variants = {row["variant"] for row in matrix["variant_summary_rows"]}
    assert variants == {
        "attention_budgeting",
        "compressed_attention",
        "history_compression",
        "kv_sharing",
        "mhc",
        "per_layer_embeddings",
    }


def test_render_benchmark_matrix_markdown_includes_summary() -> None:
    matrix = build_benchmark_matrix(
        ROOT,
        batch_sizes=[1],
        seq_lens=[4],
        warmup_runs=0,
        measured_runs=1,
        report_runs=1,
        seed=11,
    )

    markdown = render_benchmark_matrix_markdown(matrix)
    assert "Micro Benchmark Matrix" in markdown
    assert "Best mean runtime across the grid" in markdown
    assert "`kv_sharing`" in markdown or "`compressed_attention`" in markdown


def test_render_benchmark_matrix_markdown_handles_ties() -> None:
    matrix = {
        "headline": "Micro Benchmark Matrix",
        "summary": {
            "best_mean_runtime_variant": "compressed_attention",
            "best_mean_runtime_variants": ["compressed_attention", "kv_sharing"],
            "best_worst_case_runtime_variant": "attention_budgeting",
            "best_worst_case_runtime_variants": ["attention_budgeting", "compressed_attention"],
            "lowest_kv_variant": "compressed_attention",
            "lowest_kv_variants": ["compressed_attention", "kv_sharing"],
            "grid_cell_count": 6,
        },
        "baseline": {
            "name": "micro-baseline",
            "batch_sizes": [1, 2],
            "seq_lens": [4, 8],
            "warmup_runs": 1,
            "measured_runs": 3,
            "report_runs": 3,
        },
        "variant_summary_rows": [],
        "notes": [],
    }

    markdown = render_benchmark_matrix_markdown(matrix)
    assert "tie between `compressed_attention`, `kv_sharing`" in markdown
    assert "tie between `attention_budgeting`, `compressed_attention`" in markdown
