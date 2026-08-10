from __future__ import annotations

import json
from pathlib import Path

import pytest

from arch_adv_2026.long_context_execute import execute_run_plan, write_json_artifact
from arch_adv_2026.long_context_plan import (
    BENCHMARK_MODE_SUMMARY_ONLY,
    BENCHMARK_MODE_TORCH_PROXY,
    resolve_config_path,
)
from arch_adv_2026.torch_model import check_torch


TORCH_AVAILABLE = check_torch().available


def test_execute_run_plan_materializes_baseline_and_selected_summaries(tmp_path: Path) -> None:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    selected_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="compressed_attention",
    )
    baseline_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="baseline",
    )
    proxy_selected_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="micro",
        variant_kind="compressed_attention",
    )
    proxy_baseline_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="micro",
        variant_kind="baseline",
    )
    selected_config.write_text(
        json.dumps(
            {
                "name": "qwen3-compressed-attention",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "compressed_attention", "compressed_head_dim": 4},
            }
        ),
        encoding="utf-8",
    )
    baseline_config.write_text(
        json.dumps(
            {
                "name": "qwen3-baseline",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "baseline"},
            }
        ),
        encoding="utf-8",
    )
    proxy_selected_config.write_text(
        json.dumps(
            {
                "name": "micro-compressed-attention",
                "vocab_size": 64,
                "max_seq_len": 32,
                "d_model": 16,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 4,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "compressed_attention", "compressed_head_dim": 2},
            }
        ),
        encoding="utf-8",
    )
    proxy_baseline_config.write_text(
        json.dumps(
            {
                "name": "micro-baseline",
                "vocab_size": 64,
                "max_seq_len": 32,
                "d_model": 16,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 4,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "baseline"},
            }
        ),
        encoding="utf-8",
    )
    plan = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "objective": "balanced",
        "config_family": "qwen3",
        "selected_variant_kind": "compressed_attention",
        "selected_config_path": str(selected_config),
        "baseline_config_path": str(baseline_config),
        "planned_summary_artifact_path": str(tmp_path / "artifacts" / "selected-summary.json"),
        "planned_benchmark_artifact_path": str(tmp_path / "artifacts" / "benchmark.json"),
        "benchmark_params": {
            "config_family": "micro",
            "batch_size": 1,
            "seq_len": 4,
            "seed": 0,
            "warmup_runs": 0,
            "measured_runs": 1,
        },
    }
    execution = execute_run_plan(plan)
    assert Path(execution["selected_summary_artifact_path"]).exists()
    assert Path(execution["baseline_summary_artifact_path"]).exists()
    assert Path(execution["benchmark_artifact_path"]).exists()
    assert execution["benchmark_config_family"] == "micro"
    assert execution["selected_summary"]["shape"]["effective_attn_head_dim"] == 4
    assert execution["delta"]["kv_cache_saving_ratio_vs_baseline"] > 0.0
    assert execution["benchmark_result"]["variant"]["variant"] == "compressed_attention"
    assert execution["benchmark_result"]["comparison"]["owner_cache_delta"] == 0


def test_execute_run_plan_supports_summary_only_mode(tmp_path: Path) -> None:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    selected_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="compressed_attention",
    )
    baseline_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="baseline",
    )
    selected_config.write_text(
        json.dumps(
            {
                "name": "qwen3-compressed-attention",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "compressed_attention", "compressed_head_dim": 4},
            }
        ),
        encoding="utf-8",
    )
    baseline_config.write_text(
        json.dumps(
            {
                "name": "qwen3-baseline",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "baseline"},
            }
        ),
        encoding="utf-8",
    )
    plan = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "objective": "balanced",
        "config_family": "qwen3",
        "selected_variant_kind": "compressed_attention",
        "selected_config_path": str(selected_config),
        "baseline_config_path": str(baseline_config),
        "planned_summary_artifact_path": str(tmp_path / "artifacts" / "selected-summary.json"),
        "planned_benchmark_artifact_path": str(tmp_path / "artifacts" / "benchmark.json"),
        "benchmark_mode": BENCHMARK_MODE_SUMMARY_ONLY,
        "benchmark_params": {
            "config_family": "micro",
            "batch_size": 1,
            "seq_len": 4,
            "seed": 0,
            "warmup_runs": 0,
            "measured_runs": 1,
        },
    }
    execution = execute_run_plan(plan)
    assert execution["benchmark_mode"] == BENCHMARK_MODE_SUMMARY_ONLY
    assert execution["benchmark_result"] is None
    assert execution["benchmark_config_family"] is None
    assert not Path(execution["benchmark_artifact_path"]).exists()


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_execute_run_plan_supports_torch_proxy_mode(tmp_path: Path) -> None:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    selected_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="compressed_attention",
    )
    baseline_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="qwen3",
        variant_kind="baseline",
    )
    proxy_selected_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="micro",
        variant_kind="compressed_attention",
    )
    proxy_baseline_config = resolve_config_path(
        root_dir=tmp_path,
        config_family="micro",
        variant_kind="baseline",
    )
    selected_config.write_text(
        json.dumps(
            {
                "name": "qwen3-compressed-attention",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "compressed_attention", "compressed_head_dim": 4},
            }
        ),
        encoding="utf-8",
    )
    baseline_config.write_text(
        json.dumps(
            {
                "name": "qwen3-baseline",
                "vocab_size": 100,
                "max_seq_len": 64,
                "d_model": 32,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 8,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "baseline"},
            }
        ),
        encoding="utf-8",
    )
    proxy_selected_config.write_text(
        json.dumps(
            {
                "name": "micro-compressed-attention",
                "vocab_size": 64,
                "max_seq_len": 32,
                "d_model": 16,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 4,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "compressed_attention", "compressed_head_dim": 2},
            }
        ),
        encoding="utf-8",
    )
    proxy_baseline_config.write_text(
        json.dumps(
            {
                "name": "micro-baseline",
                "vocab_size": 64,
                "max_seq_len": 32,
                "d_model": 16,
                "n_layers": 4,
                "n_query_heads": 4,
                "n_kv_heads": 2,
                "head_dim": 4,
                "ffn_mult": 2.0,
                "attention_pattern": "full",
                "window_size": None,
                "variant": {"kind": "baseline"},
            }
        ),
        encoding="utf-8",
    )
    plan = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "objective": "balanced",
        "config_family": "qwen3",
        "selected_variant_kind": "compressed_attention",
        "selected_config_path": str(selected_config),
        "baseline_config_path": str(baseline_config),
        "planned_summary_artifact_path": str(tmp_path / "artifacts" / "selected-summary.json"),
        "planned_benchmark_artifact_path": str(tmp_path / "artifacts" / "benchmark.json"),
        "benchmark_mode": BENCHMARK_MODE_TORCH_PROXY,
        "benchmark_params": {
            "config_family": "micro",
            "batch_size": 1,
            "seq_len": 2,
            "seed": 0,
            "warmup_runs": 0,
            "measured_runs": 1,
        },
    }
    execution = execute_run_plan(plan)
    assert execution["benchmark_mode"] == BENCHMARK_MODE_TORCH_PROXY
    assert execution["benchmark_result"]["variant"]["variant"] == "compressed_attention"
    assert execution["benchmark_result"]["demo_context"]["variant"]["torch_run"]["owner_cache_count"] == 4
    assert Path(execution["benchmark_artifact_path"]).exists()


def test_write_json_artifact_writes_execution_payload(tmp_path: Path) -> None:
    payload = {"ok": True}
    path = write_json_artifact(payload, tmp_path / "execution.json")
    assert path.exists()
    assert json.loads(path.read_text(encoding="utf-8")) == payload
