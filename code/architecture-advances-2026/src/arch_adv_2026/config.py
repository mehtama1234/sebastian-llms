from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class VariantConfig:
    kind: str = "baseline"
    share_every: int | None = None
    tail_layers_only: bool = False
    per_layer_query_heads: list[int] | None = None
    ple_enabled: bool = False
    compressed_head_dim: int | None = None
    min_compression_seq_len: int | None = None
    residual_stream_count: int = 1
    residual_mix_rank: int | None = None
    recent_window_size: int | None = None
    history_compression_ratio: int | None = None


@dataclass(slots=True)
class ModelConfig:
    name: str
    vocab_size: int
    max_seq_len: int
    d_model: int
    n_layers: int
    n_query_heads: int
    n_kv_heads: int
    head_dim: int
    ffn_mult: float
    attention_pattern: str
    window_size: int | None
    variant: VariantConfig

    @property
    def ffn_hidden_dim(self) -> int:
        return int(self.d_model * self.ffn_mult)

    @property
    def d_attn(self) -> int:
        return self.n_query_heads * self.head_dim

    def query_heads_for_layer(self, layer_idx: int) -> int:
        if self.variant.per_layer_query_heads is None:
            return self.n_query_heads
        return self.variant.per_layer_query_heads[layer_idx]


def compression_active_for_seq_len(config: ModelConfig, seq_len: int) -> bool:
    if config.variant.kind != "compressed_attention":
        return False
    if config.variant.compressed_head_dim is None:
        return False
    threshold = config.variant.min_compression_seq_len
    if threshold is None:
        return True
    return seq_len >= threshold


def compression_falls_back_to_baseline(config: ModelConfig, seq_len: int) -> bool:
    return config.variant.kind == "compressed_attention" and not compression_active_for_seq_len(config, seq_len)


def load_config(path: str | Path) -> ModelConfig:
    raw = json.loads(Path(path).read_text())
    variant = VariantConfig(**raw.pop("variant", {}))
    if variant.per_layer_query_heads is not None and len(variant.per_layer_query_heads) != raw["n_layers"]:
        raise ValueError("per_layer_query_heads length must match n_layers")
    if variant.compressed_head_dim is not None and variant.compressed_head_dim <= 0:
        raise ValueError("compressed_head_dim must be positive")
    if variant.min_compression_seq_len is not None and variant.min_compression_seq_len <= 0:
        raise ValueError("min_compression_seq_len must be positive")
    if variant.residual_stream_count <= 0:
        raise ValueError("residual_stream_count must be positive")
    if variant.residual_mix_rank is not None and variant.residual_mix_rank <= 0:
        raise ValueError("residual_mix_rank must be positive")
    if variant.kind == "compressed_attention" and variant.min_compression_seq_len is not None:
        if variant.compressed_head_dim is None:
            raise ValueError("compressed_attention min_compression_seq_len requires compressed_head_dim")
        if variant.min_compression_seq_len > raw["max_seq_len"]:
            raise ValueError("min_compression_seq_len cannot exceed max_seq_len")
    if variant.kind == "mhc" and variant.residual_stream_count < 2:
        raise ValueError("mhc variants must use at least 2 residual streams")
    if variant.recent_window_size is not None and variant.recent_window_size <= 0:
        raise ValueError("recent_window_size must be positive")
    if variant.history_compression_ratio is not None and variant.history_compression_ratio <= 1:
        raise ValueError("history_compression_ratio must be greater than 1")
    if variant.kind == "history_compression":
        if variant.recent_window_size is None:
            raise ValueError("history_compression variants must set recent_window_size")
        if variant.history_compression_ratio is None:
            raise ValueError("history_compression variants must set history_compression_ratio")
        if variant.recent_window_size > raw["max_seq_len"]:
            raise ValueError("recent_window_size cannot exceed max_seq_len")
    return ModelConfig(variant=variant, **raw)
