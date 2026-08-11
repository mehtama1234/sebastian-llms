from __future__ import annotations

from dataclasses import asdict

from .config import ModelConfig, compression_active_for_seq_len
from .graph import LayerSpec, build_model_graph
from .variants import kv_owner_layers


BF16_BYTES = 2


def _attn_head_dim(config: ModelConfig) -> int:
    return config.variant.compressed_head_dim or config.head_dim


def _mhc_mix_rank(config: ModelConfig) -> int | None:
    if config.variant.kind != "mhc":
        return None
    return config.variant.residual_mix_rank or max(1, config.d_model // 4)


def _history_recent_window(config: ModelConfig) -> int | None:
    if config.variant.kind != "history_compression":
        return None
    return config.variant.recent_window_size


def _history_compression_ratio(config: ModelConfig) -> int | None:
    if config.variant.kind != "history_compression":
        return None
    return config.variant.history_compression_ratio


def _effective_history_tokens(config: ModelConfig, seq_len: int) -> int:
    if config.variant.kind != "history_compression":
        return seq_len
    recent = min(_history_recent_window(config) or seq_len, seq_len)
    old = max(0, seq_len - recent)
    ratio = _history_compression_ratio(config) or 1
    compressed_old = (old + ratio - 1) // ratio
    return recent + compressed_old


def _embedding_params(config: ModelConfig) -> int:
    base = config.vocab_size * config.d_model
    if config.variant.ple_enabled:
        base += config.n_layers * config.vocab_size * config.d_model
        base += config.d_model * config.d_model
    return base


def _mhc_params_per_layer(config: ModelConfig) -> int:
    rank = _mhc_mix_rank(config)
    if rank is None:
        return 0
    streams = config.variant.residual_stream_count
    return (config.d_model * rank * streams) + (rank * streams * config.d_model) + (config.d_model * streams)


def _history_compression_params_per_layer(config: ModelConfig) -> int:
    ratio = _history_compression_ratio(config)
    if ratio is None:
        return 0
    compressed_dim = max(1, config.d_model // ratio)
    return (config.d_model * compressed_dim * 2) + (compressed_dim * config.d_model)


def _attn_params_per_owner_layer(config: ModelConfig, layer: LayerSpec) -> int:
    attn_dim = _attn_head_dim(config)
    q = config.d_model * layer.n_query_heads * attn_dim
    k = config.d_model * config.n_kv_heads * attn_dim
    v = config.d_model * config.n_kv_heads * attn_dim
    o = layer.n_query_heads * attn_dim * config.d_model
    return q + k + v + o


def _attn_params_per_shared_layer(config: ModelConfig, layer: LayerSpec) -> int:
    attn_dim = _attn_head_dim(config)
    q = config.d_model * layer.n_query_heads * attn_dim
    o = layer.n_query_heads * attn_dim * config.d_model
    return q + o


def _ffn_params_per_layer(config: ModelConfig) -> int:
    hidden = config.ffn_hidden_dim
    # SwiGLU-style rough accounting: gate + up + down
    return (config.d_model * hidden * 2) + (hidden * config.d_model)


def _norm_params_per_layer(config: ModelConfig) -> int:
    return config.d_model * 2


def _layer_param_breakdown(config: ModelConfig) -> tuple[list[bool], int, int]:
    graph = build_model_graph(config)
    owners = kv_owner_layers(config)
    total = 0
    kv_proj_params = 0
    for layer, owner in zip(graph.layers, owners, strict=True):
        total += _ffn_params_per_layer(config) + _norm_params_per_layer(config)
        total += _mhc_params_per_layer(config)
        total += _history_compression_params_per_layer(config)
        if owner:
            total += _attn_params_per_owner_layer(config, layer)
            kv_proj_params += config.d_model * config.n_kv_heads * _attn_head_dim(config) * 2
        else:
            total += _attn_params_per_shared_layer(config, layer)
    return owners, total, kv_proj_params


def _kv_cache_bytes(config: ModelConfig, kv_owner_count: int, seq_len: int | None = None) -> int:
    active_seq = seq_len or config.max_seq_len
    cached_tokens = _effective_history_tokens(config, active_seq)
    elems_per_layer = cached_tokens * config.n_kv_heads * _attn_head_dim(config) * 2
    return elems_per_layer * kv_owner_count * BF16_BYTES


def _kv_cache_bytes_without_history_compression(
    config: ModelConfig,
    kv_owner_count: int,
    seq_len: int | None = None,
) -> int:
    active_seq = seq_len or config.max_seq_len
    elems_per_layer = active_seq * config.n_kv_heads * _attn_head_dim(config) * 2
    return elems_per_layer * kv_owner_count * BF16_BYTES


def build_summary(config: ModelConfig) -> dict:
    owners, layer_params, kv_proj_params = _layer_param_breakdown(config)
    graph = build_model_graph(config)
    embedding_params = _embedding_params(config)
    total_params = embedding_params + layer_params
    owner_count = sum(owners)
    baseline_kv_cache_bytes = _kv_cache_bytes_without_history_compression(config, config.n_layers)
    current_kv_cache_bytes = _kv_cache_bytes(config, owner_count)
    mhc_mix_rank = _mhc_mix_rank(config)
    mhc_params_per_layer = _mhc_params_per_layer(config)
    history_recent_window = _history_recent_window(config)
    history_compression_ratio = _history_compression_ratio(config)
    history_params_per_layer = _history_compression_params_per_layer(config)
    effective_history_tokens = _effective_history_tokens(config, config.max_seq_len)

    return {
        "name": config.name,
        "variant": asdict(config.variant),
        "shape": {
            "vocab_size": config.vocab_size,
            "max_seq_len": config.max_seq_len,
            "d_model": config.d_model,
            "n_layers": config.n_layers,
            "n_query_heads": config.n_query_heads,
            "n_kv_heads": config.n_kv_heads,
            "head_dim": config.head_dim,
            "effective_attn_head_dim": _attn_head_dim(config),
            "ffn_hidden_dim": config.ffn_hidden_dim,
            "per_layer_query_heads": [layer.n_query_heads for layer in graph.layers],
            "ple_enabled": config.variant.ple_enabled,
            "compressed_head_dim": config.variant.compressed_head_dim,
            "min_compression_seq_len": config.variant.min_compression_seq_len,
            "compression_active_at_max_seq": compression_active_for_seq_len(config, config.max_seq_len),
            "residual_stream_count": config.variant.residual_stream_count,
            "residual_mix_rank": mhc_mix_rank,
            "recent_window_size": history_recent_window,
            "history_compression_ratio": history_compression_ratio,
            "effective_history_tokens_at_max_seq": effective_history_tokens,
        },
        "params": {
            "embedding": embedding_params,
            "layers_total": layer_params,
            "kv_projection_params": kv_proj_params,
            "total": total_params,
        },
        "residual_path": {
            "kind": "mhc" if config.variant.kind == "mhc" else "baseline",
            "residual_stream_count": config.variant.residual_stream_count,
            "residual_mix_rank": mhc_mix_rank,
            "extra_params_per_layer": mhc_params_per_layer,
        },
        "history_path": {
            "kind": "history_compression" if config.variant.kind == "history_compression" else "baseline",
            "recent_window_size": history_recent_window,
            "history_compression_ratio": history_compression_ratio,
            "effective_history_tokens_at_max_seq": effective_history_tokens,
            "extra_params_per_layer": history_params_per_layer,
        },
        "kv_sharing": {
            "owner_layers": owners,
            "owner_layer_count": owner_count,
            "shared_layer_count": config.n_layers - owner_count,
        },
        "graph": graph.to_dict(),
        "kv_cache": {
            "dtype": "bf16",
            "baseline_bytes_at_max_seq": baseline_kv_cache_bytes,
            "variant_bytes_at_max_seq": current_kv_cache_bytes,
            "bytes_saved": baseline_kv_cache_bytes - current_kv_cache_bytes,
            "saving_ratio": (
                (baseline_kv_cache_bytes - current_kv_cache_bytes) / baseline_kv_cache_bytes
                if baseline_kv_cache_bytes
                else 0.0
            ),
        },
        "notes": [
            "This is a config-level estimate, not a measured runtime benchmark.",
            "The per-layer graph is the stable contract for future torch execution modules.",
        ],
    }
