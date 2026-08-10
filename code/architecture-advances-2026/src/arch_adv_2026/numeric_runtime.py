from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np

from .config import ModelConfig, compression_active_for_seq_len
from .graph import ModelGraph, build_model_graph


def _effective_head_dim(config: ModelConfig, seq_len: int) -> int:
    if compression_active_for_seq_len(config, seq_len):
        return config.variant.compressed_head_dim or config.head_dim
    return config.head_dim


def _compressed_attention_output_scale(config: ModelConfig, seq_len: int) -> float:
    return 1.0


def _compressed_attention_front_block_value_scale(config: ModelConfig, seq_len: int) -> float:
    if not compression_active_for_seq_len(config, seq_len):
        return 1.0
    if config.variant.compressed_head_dim is None:
        return 1.0
    return 0.9


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


@dataclass(slots=True)
class NumericRunResult:
    output_shape: tuple[int, int, int]
    cache_shapes: list[tuple[int, int, int] | None]
    owner_cache_count: int
    layer_means: list[float]
    estimated_flops: int
    estimated_kv_cache_bytes: int
    estimated_kv_cache_bytes_with_no_sharing: int
    estimated_kv_projection_bytes_written: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "output_shape": list(self.output_shape),
            "cache_shapes": [list(shape) if shape is not None else None for shape in self.cache_shapes],
            "owner_cache_count": self.owner_cache_count,
            "layer_means": self.layer_means,
            "estimated_flops": self.estimated_flops,
            "estimated_kv_cache_bytes": self.estimated_kv_cache_bytes,
            "estimated_kv_cache_bytes_with_no_sharing": self.estimated_kv_cache_bytes_with_no_sharing,
            "estimated_kv_cache_bytes_saved": (
                self.estimated_kv_cache_bytes_with_no_sharing - self.estimated_kv_cache_bytes
            ),
            "estimated_kv_projection_bytes_written": self.estimated_kv_projection_bytes_written,
        }


@dataclass(slots=True)
class PreparedNumericLayer:
    q_proj: np.ndarray
    out_proj: np.ndarray
    up: np.ndarray
    gate: np.ndarray
    down: np.ndarray
    k_proj: np.ndarray | None = None
    v_proj: np.ndarray | None = None
    mix_in: np.ndarray | None = None
    mix_out: np.ndarray | None = None
    gate_proj: np.ndarray | None = None


@dataclass(slots=True)
class PreparedNumericDemo:
    config: ModelConfig
    graph: ModelGraph
    batch_size: int
    seq_len: int
    x: np.ndarray
    attn_head_dim: int
    estimated_flops: int
    ple_table: np.ndarray | None
    ple_gate_proj: np.ndarray | None
    token_ids: np.ndarray | None
    layers: list[PreparedNumericLayer]


def _repeat_kv(x: np.ndarray, repeats: int) -> np.ndarray:
    if repeats == 1:
        return x
    return np.repeat(x, repeats, axis=1)


def _causal_mask(seq_len: int) -> np.ndarray:
    mask = np.triu(np.ones((seq_len, seq_len), dtype=bool), k=1)
    return mask


def _estimate_kv_cache_bytes(config: ModelConfig, batch_size: int, seq_len: int, owner_cache_count: int) -> int:
    cached_tokens = _effective_history_tokens(config, seq_len)
    return batch_size * owner_cache_count * config.n_kv_heads * cached_tokens * _effective_head_dim(config, seq_len) * 2 * 4


def _estimate_kv_cache_bytes_without_history_compression(
    config: ModelConfig,
    batch_size: int,
    seq_len: int,
    owner_cache_count: int,
) -> int:
    return batch_size * owner_cache_count * config.n_kv_heads * seq_len * _effective_head_dim(config, seq_len) * 2 * 4


def _estimate_layer_flops(
    config: ModelConfig,
    batch_size: int,
    seq_len: int,
    layer_is_owner: bool,
    q_heads: int,
) -> int:
    d_model = config.d_model
    attn_head_dim = _effective_head_dim(config, seq_len)
    d_q = q_heads * attn_head_dim
    d_kv = config.n_kv_heads * attn_head_dim
    hidden = config.ffn_hidden_dim
    memory_tokens = _effective_history_tokens(config, seq_len)

    q_proj = 2 * batch_size * seq_len * d_model * d_q
    kv_proj = 2 * batch_size * seq_len * d_model * d_kv * 2 if layer_is_owner else 0
    attn_scores = 2 * batch_size * q_heads * seq_len * memory_tokens * attn_head_dim
    attn_reduce = 2 * batch_size * q_heads * seq_len * memory_tokens * attn_head_dim
    out_proj = 2 * batch_size * seq_len * (q_heads * attn_head_dim) * d_model
    ffn_up = 2 * batch_size * seq_len * d_model * hidden
    ffn_gate = 2 * batch_size * seq_len * d_model * hidden
    ffn_down = 2 * batch_size * seq_len * hidden * d_model
    ple = 0
    if config.variant.ple_enabled:
        ple = 2 * batch_size * seq_len * d_model * d_model
    mhc = 0
    rank = _mhc_mix_rank(config)
    if rank is not None:
        streams = config.variant.residual_stream_count
        mhc = (
            (2 * batch_size * seq_len * d_model * rank * streams)
            + (2 * batch_size * seq_len * rank * streams * d_model)
            + (2 * batch_size * seq_len * d_model * streams)
        )
    history_compress = 0
    history_ratio = _history_compression_ratio(config)
    if history_ratio is not None:
        old_tokens = max(0, seq_len - min(_history_recent_window(config) or seq_len, seq_len))
        history_compress = 2 * batch_size * old_tokens * d_kv
    return q_proj + kv_proj + attn_scores + attn_reduce + out_proj + ffn_up + ffn_gate + ffn_down + ple + mhc + history_compress


def _compress_history_cache(cache: np.ndarray, *, recent_window: int, compression_ratio: int) -> np.ndarray:
    batch_size, kv_heads, seq_len, head_dim = cache.shape
    recent = min(recent_window, seq_len)
    old_len = max(0, seq_len - recent)
    if old_len == 0:
        return cache
    old_cache = cache[:, :, :old_len, :]
    recent_cache = cache[:, :, old_len:, :]
    blocks = []
    for start in range(0, old_len, compression_ratio):
        block = old_cache[:, :, start : start + compression_ratio, :]
        blocks.append(np.mean(block, axis=2, keepdims=True))
    compressed_old = np.concatenate(blocks, axis=2) if blocks else old_cache[:, :, :0, :]
    return np.concatenate([compressed_old, recent_cache], axis=2)


def estimate_numeric_flops(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
) -> int:
    if seq_len > config.max_seq_len:
        raise ValueError(f"seq_len {seq_len} exceeds config.max_seq_len {config.max_seq_len}")

    graph = build_model_graph(config)
    total = 0
    for layer in graph.layers:
        total += _estimate_layer_flops(
            config,
            batch_size=batch_size,
            seq_len=seq_len,
            layer_is_owner=layer.is_kv_owner,
            q_heads=layer.n_query_heads,
        )
    return total


def prepare_numeric_demo(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
) -> PreparedNumericDemo:
    if seq_len > config.max_seq_len:
        raise ValueError(f"seq_len {seq_len} exceeds config.max_seq_len {config.max_seq_len}")

    graph = build_model_graph(config)
    rng = np.random.default_rng(seed)
    x = rng.normal(0.0, 0.02, size=(batch_size, seq_len, config.d_model)).astype(np.float32)
    attn_head_dim = _effective_head_dim(config, seq_len)
    front_block_value_scale = _compressed_attention_front_block_value_scale(config, seq_len)
    ple_table = None
    ple_gate_proj = None
    if config.variant.ple_enabled:
        ple_table = rng.normal(
            0.0,
            0.02,
            size=(config.n_layers, config.vocab_size, config.d_model),
        ).astype(np.float32)
        ple_gate_proj = rng.normal(0.0, 0.02, size=(config.d_model, config.d_model)).astype(np.float32)
        token_ids = rng.integers(0, config.vocab_size, size=(batch_size, seq_len))

    cached_k: list[np.ndarray | None] = [None] * config.n_layers
    cached_v: list[np.ndarray | None] = [None] * config.n_layers
    layer_means: list[float] = []
    estimated_flops = estimate_numeric_flops(config, batch_size=batch_size, seq_len=seq_len)
    mhc_rank = _mhc_mix_rank(config)
    layers: list[PreparedNumericLayer] = []

    for layer in graph.layers:
        q_heads = layer.n_query_heads
        if (q_heads // config.n_kv_heads) * config.n_kv_heads != q_heads:
            raise ValueError("per-layer n_query_heads must be divisible by n_kv_heads for the numeric demo")
        q_proj = rng.normal(0.0, 0.02, size=(config.d_model, q_heads * attn_head_dim)).astype(np.float32)
        out_proj = rng.normal(0.0, 0.02, size=(q_heads * attn_head_dim, config.d_model)).astype(np.float32)
        if layer.index == 0 and front_block_value_scale != 1.0:
            out_proj = out_proj * front_block_value_scale
        hidden = config.ffn_hidden_dim
        up = rng.normal(0.0, 0.02, size=(config.d_model, hidden)).astype(np.float32)
        gate = rng.normal(0.0, 0.02, size=(config.d_model, hidden)).astype(np.float32)
        down = rng.normal(0.0, 0.02, size=(hidden, config.d_model)).astype(np.float32)
        k_proj = None
        v_proj = None
        if layer.is_kv_owner:
            k_proj = rng.normal(0.0, 0.02, size=(config.d_model, config.n_kv_heads * attn_head_dim)).astype(np.float32)
            v_proj = rng.normal(0.0, 0.02, size=(config.d_model, config.n_kv_heads * attn_head_dim)).astype(np.float32)
            if layer.index == 0 and front_block_value_scale != 1.0:
                v_proj = v_proj * front_block_value_scale
        mix_in = None
        mix_out = None
        gate_proj = None
        if mhc_rank is not None:
            streams = config.variant.residual_stream_count
            mix_in = rng.normal(0.0, 0.02, size=(config.d_model, streams * mhc_rank)).astype(np.float32)
            mix_out = rng.normal(0.0, 0.02, size=(streams, mhc_rank, config.d_model)).astype(np.float32)
            gate_proj = rng.normal(0.0, 0.02, size=(config.d_model, streams)).astype(np.float32)
        layers.append(
            PreparedNumericLayer(
                q_proj=q_proj,
                out_proj=out_proj,
                up=up,
                gate=gate,
                down=down,
                k_proj=k_proj,
                v_proj=v_proj,
                mix_in=mix_in,
                mix_out=mix_out,
                gate_proj=gate_proj,
            )
        )

    return PreparedNumericDemo(
        config=config,
        graph=graph,
        batch_size=batch_size,
        seq_len=seq_len,
        x=x,
        attn_head_dim=attn_head_dim,
        estimated_flops=estimated_flops,
        ple_table=ple_table,
        ple_gate_proj=ple_gate_proj,
        token_ids=token_ids if config.variant.ple_enabled else None,
        layers=layers,
    )


def run_prepared_numeric_demo(prepared: PreparedNumericDemo) -> NumericRunResult:
    config = prepared.config
    seq_len = prepared.seq_len
    batch_size = prepared.batch_size
    x = prepared.x.copy()
    attn_head_dim = prepared.attn_head_dim
    attn_output_scale = _compressed_attention_output_scale(config, seq_len)
    cached_k: list[np.ndarray | None] = [None] * config.n_layers
    cached_v: list[np.ndarray | None] = [None] * config.n_layers
    layer_means: list[float] = []
    estimated_kv_projection_bytes_written = 0
    mhc_rank = _mhc_mix_rank(config)

    for layer, layer_weights in zip(prepared.graph.layers, prepared.layers, strict=True):
        resid = x
        q_heads = layer.n_query_heads
        q_repeat = q_heads // config.n_kv_heads
        q = x @ layer_weights.q_proj
        q = q.reshape(batch_size, seq_len, q_heads, attn_head_dim).transpose(0, 2, 1, 3)

        if layer.is_kv_owner:
            if layer_weights.k_proj is None or layer_weights.v_proj is None:
                raise RuntimeError(f"layer {layer.index} missing KV projections")
            k = x @ layer_weights.k_proj
            v = x @ layer_weights.v_proj
            k = k.reshape(batch_size, seq_len, config.n_kv_heads, attn_head_dim).transpose(0, 2, 1, 3)
            v = v.reshape(batch_size, seq_len, config.n_kv_heads, attn_head_dim).transpose(0, 2, 1, 3)
            if config.variant.kind == "history_compression":
                k = _compress_history_cache(
                    k,
                    recent_window=_history_recent_window(config) or seq_len,
                    compression_ratio=_history_compression_ratio(config) or 1,
                )
                v = _compress_history_cache(
                    v,
                    recent_window=_history_recent_window(config) or seq_len,
                    compression_ratio=_history_compression_ratio(config) or 1,
                )
            cached_k[layer.index] = k
            cached_v[layer.index] = v
            estimated_kv_projection_bytes_written += k.nbytes + v.nbytes
        else:
            k = cached_k[layer.kv_source_layer]
            v = cached_v[layer.kv_source_layer]
            if k is None or v is None:
                raise RuntimeError(f"layer {layer.index} expected cached KV from {layer.kv_source_layer}")

        k_for_q = _repeat_kv(k, q_repeat)
        v_for_q = _repeat_kv(v, q_repeat)
        memory_len = k_for_q.shape[2]
        scores = np.einsum("bhid,bhjd->bhij", q, k_for_q) / np.sqrt(attn_head_dim)
        if memory_len == seq_len and config.variant.kind != "history_compression":
            mask = _causal_mask(seq_len)
            scores = np.where(mask[None, None, :, :], -1.0e9, scores)
        scores = scores - scores.max(axis=-1, keepdims=True)
        attn = np.exp(scores)
        attn = attn / attn.sum(axis=-1, keepdims=True)
        context = np.einsum("bhij,bhjd->bhid", attn, v_for_q)
        context = context.transpose(0, 2, 1, 3).reshape(batch_size, seq_len, q_heads * attn_head_dim)
        attn_out = (context @ layer_weights.out_proj) * attn_output_scale

        up_x = attn_out @ layer_weights.up
        gate_x = attn_out @ layer_weights.gate
        ff = (up_x * (1.0 / (1.0 + np.exp(-gate_x)))) @ layer_weights.down

        x = resid + attn_out + ff
        if config.variant.ple_enabled and prepared.ple_table is not None and prepared.ple_gate_proj is not None and prepared.token_ids is not None:
            ple_vec = prepared.ple_table[layer.index][prepared.token_ids]
            ple_gate = 1.0 / (1.0 + np.exp(-(x @ prepared.ple_gate_proj)))
            x = x + (ple_vec * ple_gate)
        if mhc_rank is not None:
            if layer_weights.mix_in is None or layer_weights.mix_out is None or layer_weights.gate_proj is None:
                raise RuntimeError(f"layer {layer.index} missing MHC weights")
            stream_logits = x @ layer_weights.gate_proj
            stream_logits = stream_logits - stream_logits.max(axis=-1, keepdims=True)
            stream_weights = np.exp(stream_logits)
            stream_weights = stream_weights / stream_weights.sum(axis=-1, keepdims=True)
            streams = config.variant.residual_stream_count
            mixed_basis = (x @ layer_weights.mix_in).reshape(batch_size, seq_len, streams, mhc_rank)
            stream_updates = np.einsum("bsur,urd->bsud", mixed_basis, layer_weights.mix_out)
            mhc_update = np.einsum("bsu,bsud->bsd", stream_weights, stream_updates)
            x = x + mhc_update
        layer_means.append(float(np.mean(x)))

    cache_shapes = []
    for idx in range(config.n_layers):
        if cached_k[idx] is None:
            cache_shapes.append(None)
        else:
            cache_shapes.append(tuple(int(v) for v in cached_k[idx].shape))

    owner_cache_count = sum(shape is not None for shape in cache_shapes)
    return NumericRunResult(
        output_shape=tuple(int(v) for v in x.shape),
        cache_shapes=cache_shapes,
        owner_cache_count=owner_cache_count,
        layer_means=layer_means,
        estimated_flops=prepared.estimated_flops,
        estimated_kv_cache_bytes=_estimate_kv_cache_bytes(config, batch_size, seq_len, owner_cache_count),
        estimated_kv_cache_bytes_with_no_sharing=_estimate_kv_cache_bytes_without_history_compression(
            config,
            batch_size,
            seq_len,
            config.n_layers,
        ),
        estimated_kv_projection_bytes_written=estimated_kv_projection_bytes_written,
    )


def run_numeric_demo(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
) -> NumericRunResult:
    prepared = prepare_numeric_demo(config, batch_size=batch_size, seq_len=seq_len, seed=seed)
    return run_prepared_numeric_demo(prepared)


def describe_numeric_demo(config: ModelConfig, *, batch_size: int = 1, seq_len: int = 8, seed: int = 0) -> dict[str, Any]:
    graph: ModelGraph = build_model_graph(config)
    run = run_numeric_demo(config, batch_size=batch_size, seq_len=seq_len, seed=seed)
    return {
        "name": config.name,
        "variant": config.variant.kind,
        "input_shape": [batch_size, seq_len],
        "graph": graph.to_dict(),
        "numeric_run": run.to_dict(),
        "notes": [
            "This is a tiny NumPy execution path for shape/runtime sanity, not a trained model.",
            "Weights are random and regenerated per run from the provided seed.",
        ],
    }
