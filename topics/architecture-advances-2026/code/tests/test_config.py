from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import compression_active_for_seq_len, compression_falls_back_to_baseline, load_config


ROOT = Path(__file__).resolve().parents[1]


def test_load_baseline_config() -> None:
    config = load_config(ROOT / "configs" / "tiny-baseline.json")
    assert config.name == "tiny-baseline"
    assert config.ffn_hidden_dim == 1792
    assert config.variant.kind == "baseline"


def test_load_kv_sharing_config() -> None:
    config = load_config(ROOT / "configs" / "tiny-kv-sharing.json")
    assert config.variant.kind == "kv_sharing"
    assert config.variant.share_every == 2


def test_load_compressed_attention_threshold_config() -> None:
    config = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    assert config.variant.kind == "compressed_attention"
    assert config.variant.compressed_head_dim == 8
    assert config.variant.min_compression_seq_len == 16
    assert not compression_active_for_seq_len(config, 8)
    assert compression_active_for_seq_len(config, 16)
    assert compression_falls_back_to_baseline(config, 8)
