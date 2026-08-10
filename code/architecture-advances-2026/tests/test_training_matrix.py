from __future__ import annotations

import pytest

from arch_adv_2026.torch_model import check_torch
from arch_adv_2026.training_matrix import execute_training_matrix


TORCH_AVAILABLE = check_torch().available


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_execute_training_matrix_smoke(tmp_path) -> None:
    root_dir = "/home/manishmehta/ui-projects/sebastian-llms/code/architecture-advances-2026"
    matrix = execute_training_matrix(
        root_dir=root_dir,
        batch_sizes=[2],
        seq_lens=[6],
        steps_list=[2],
        seeds=[5, 7],
        lr=1e-2,
        clip_grad_norm=1.0,
        report_runs=1,
    )
    assert matrix["row_count"] == 2
    assert len(matrix["rows"]) == 2
    assert matrix["batch_sizes"] == [2]
    assert matrix["baseline"]["batch_sizes"] == [2]
    assert matrix["rows"][0]["fastest_variant"]
    assert matrix["variant_trends"]
    assert matrix["winner_counts"]["fastest_step_ratio"]
    assert all("all_matrix_rows_finite" in row for row in matrix["variant_trends"])
    assert all("mean_step_ms_ratio_vs_baseline_range" in row for row in matrix["variant_trends"])
    assert all("final_loss_delta_vs_baseline_range" in row for row in matrix["variant_trends"])
    assert all("fastest_step_win_rate" in row for row in matrix["variant_trends"])


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_execute_training_matrix_filters_variants() -> None:
    root_dir = "/home/manishmehta/ui-projects/sebastian-llms/code/architecture-advances-2026"
    matrix = execute_training_matrix(
        root_dir=root_dir,
        batch_sizes=[2],
        seq_lens=[6],
        steps_list=[2],
        seeds=[5],
        lr=1e-2,
        clip_grad_norm=1.0,
        report_runs=1,
        variant_names=["attention_budgeting"],
    )
    assert matrix["variant_labels"] == ["attention_budgeting"]
    assert [row["variant"] for row in matrix["variant_trends"]] == ["attention_budgeting"]


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_execute_training_matrix_supports_multiple_batch_sizes() -> None:
    root_dir = "/home/manishmehta/ui-projects/sebastian-llms/code/architecture-advances-2026"
    matrix = execute_training_matrix(
        root_dir=root_dir,
        batch_sizes=[2, 3],
        seq_lens=[6],
        steps_list=[2],
        seeds=[5],
        lr=1e-2,
        clip_grad_norm=1.0,
        report_runs=1,
        variant_names=["attention_budgeting"],
    )
    assert matrix["row_count"] == 2
    assert matrix["batch_sizes"] == [2, 3]
    assert matrix["baseline"]["batch_sizes"] == [2, 3]
    assert {row["batch_size"] for row in matrix["rows"]} == {2, 3}
