from __future__ import annotations

from pathlib import Path

import pytest

from arch_adv_2026.config import load_config
from arch_adv_2026.torch_model import check_torch
from arch_adv_2026.training_benchmark import (
    build_synthetic_autoregressive_batch,
    compare_torch_training_benchmarks,
)
from arch_adv_2026.training_report import generate_training_report, load_default_training_report_configs


TORCH_AVAILABLE = check_torch().available
ROOT_DIR = Path(__file__).resolve().parents[1]


def _config_path(name: str) -> str:
    return str(ROOT_DIR / "configs" / name)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_build_synthetic_autoregressive_batch_has_expected_shape() -> None:
    inputs, targets = build_synthetic_autoregressive_batch(
        vocab_size=32,
        batch_size=3,
        seq_len=5,
        seed=7,
    )
    assert list(inputs.shape) == [3, 5]
    assert list(targets.shape) == [3, 5]
    assert int(inputs[0, 1] - inputs[0, 0]) % 32 == int(targets[0, 1] - targets[0, 0]) % 32


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_compare_torch_training_benchmarks_smoke() -> None:
    baseline = load_config(_config_path("micro-baseline.json"))
    variant = load_config(_config_path("micro-compressed-attention.json"))
    result = compare_torch_training_benchmarks(
        baseline,
        variant,
        batch_size=4,
        seq_len=8,
        steps=3,
        lr=1e-2,
        seed=3,
        clip_grad_norm=1.0,
    )
    assert result["baseline"]["summary"]["initial_loss"] > 0.0
    assert result["variant"]["summary"]["initial_loss"] > 0.0
    assert len(result["baseline"]["step_results"]) == 3
    assert len(result["variant"]["step_results"]) == 3
    assert result["comparison"]["owner_cache_delta"] == 0
    assert isinstance(result["comparison"]["both_all_steps_finite"], bool)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_compressed_attention_short_context_fallback_matches_baseline_training() -> None:
    baseline = load_config(_config_path("micro-baseline.json"))
    variant = load_config(_config_path("micro-compressed-attention.json"))
    result = compare_torch_training_benchmarks(
        baseline,
        variant,
        batch_size=2,
        seq_len=8,
        steps=3,
        lr=1e-2,
        seed=11,
        clip_grad_norm=1.0,
    )
    assert result["comparison"]["final_loss_delta"] == pytest.approx(0.0)
    assert result["comparison"]["initial_loss_delta"] == pytest.approx(0.0)
    assert result["comparison"]["max_grad_norm_delta"] == pytest.approx(0.0)
    assert result["comparison"]["mean_step_ms_ratio_variant_over_baseline"] == pytest.approx(1.0)


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_generate_training_report_smoke() -> None:
    baseline = load_config(_config_path("micro-baseline.json"))
    variants = [
        load_config(_config_path("micro-kv-sharing.json")),
        load_config(_config_path("micro-compressed-attention.json")),
    ]
    report = generate_training_report(
        baseline,
        variants,
        batch_size=2,
        seq_len=6,
        steps=2,
        lr=1e-2,
        seed=5,
        clip_grad_norm=1.0,
        report_runs=1,
    )
    assert len(report["variant_rows"]) == 2
    assert report["rankings"]["fastest_step_ratio"]
    assert all("all_runs_finite" in row for row in report["variant_rows"])


def test_load_default_training_report_configs_filters_variants() -> None:
    baseline, variants = load_default_training_report_configs(
        str(ROOT_DIR),
        variant_names=["attention_budgeting", "kv_sharing"],
    )
    assert baseline.variant.kind == "baseline"
    assert [variant.variant.kind for variant in variants] == ["kv_sharing", "attention_budgeting"]
