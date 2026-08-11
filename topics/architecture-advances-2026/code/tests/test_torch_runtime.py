from __future__ import annotations

from pathlib import Path

import pytest

from arch_adv_2026.config import load_config
from arch_adv_2026.torch_model import check_torch, run_torch_demo


ROOT = Path(__file__).resolve().parents[1]
TORCH_AVAILABLE = check_torch().available


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_runs_on_micro_baseline() -> None:
    config = load_config(ROOT / "configs" / "micro-baseline.json")
    result = run_torch_demo(config, seq_len=4, seed=3)
    assert result["torch_run"]["output_shape"] == [1, 4, config.d_model]
    assert result["torch_run"]["owner_cache_count"] == config.n_layers


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_reuses_owner_cache_on_shared_layers() -> None:
    config = load_config(ROOT / "configs" / "micro-kv-sharing.json")
    result = run_torch_demo(config, seq_len=4, seed=3)
    assert result["torch_run"]["owner_cache_count"] == 2
    assert result["graph"]["layers"][1]["kv_source_layer"] == 0
    assert result["graph"]["layers"][3]["kv_source_layer"] == 2


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_uses_compressed_attention_head_dim() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = run_torch_demo(config, seq_len=16, seed=3)
    assert result["torch_run"]["cache_shapes"][0] == [1, 2, 16, 8]


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_falls_back_to_baseline_head_dim_below_compression_threshold() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    result = run_torch_demo(config, seq_len=8, seed=3)
    assert result["torch_run"]["cache_shapes"][0] == [1, 2, 8, 16]


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_history_compression_shortens_cache() -> None:
    config = load_config(ROOT / "configs" / "micro-history-compression.json")
    result = run_torch_demo(config, seq_len=8, seed=3)
    assert result["torch_run"]["cache_shapes"][0] == [1, 2, 5, 16]


@pytest.mark.skipif(not TORCH_AVAILABLE, reason="torch not installed")
def test_torch_demo_mhc_runs() -> None:
    config = load_config(ROOT / "configs" / "micro-mhc.json")
    result = run_torch_demo(config, seq_len=4, seed=3)
    assert result["torch_run"]["output_shape"] == [1, 4, config.d_model]
    assert result["torch_run"]["owner_cache_count"] == config.n_layers
