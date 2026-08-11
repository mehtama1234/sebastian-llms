from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.numeric_runtime import describe_numeric_demo, prepare_numeric_demo, run_numeric_demo, run_prepared_numeric_demo


ROOT = Path(__file__).resolve().parents[1]


def test_numeric_demo_runs_on_micro_baseline() -> None:
    config = load_config(ROOT / "configs" / "micro-baseline.json")
    result = run_numeric_demo(config, seq_len=4, seed=7)
    assert result.output_shape == (1, 4, config.d_model)
    assert result.owner_cache_count == config.n_layers
    assert result.estimated_flops > 0
    assert result.estimated_kv_cache_bytes == result.estimated_kv_cache_bytes_with_no_sharing


def test_numeric_demo_reuses_kv_cache_on_shared_layers() -> None:
    config = load_config(ROOT / "configs" / "micro-kv-sharing.json")
    result = describe_numeric_demo(config, seq_len=4, seed=7)
    assert result["numeric_run"]["owner_cache_count"] == 2
    assert result["graph"]["layers"][1]["kv_source_layer"] == 0
    assert result["graph"]["layers"][3]["kv_source_layer"] == 2
    assert result["numeric_run"]["estimated_kv_cache_bytes_saved"] > 0


def test_prepared_numeric_demo_matches_direct_run() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    prepared = prepare_numeric_demo(config, batch_size=2, seq_len=16, seed=11)
    direct = run_numeric_demo(config, batch_size=2, seq_len=16, seed=11)
    prepared_run = run_prepared_numeric_demo(prepared)
    assert prepared_run.to_dict() == direct.to_dict()
