from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .config import ModelConfig, compression_active_for_seq_len
from .graph import ModelGraph, build_model_graph


@dataclass(slots=True)
class TorchAvailability:
    available: bool
    reason: str | None = None


def check_torch() -> TorchAvailability:
    try:
        import torch  # noqa: F401
    except (ModuleNotFoundError, OSError) as exc:
        return TorchAvailability(
            available=False,
            reason=f"torch is not usable in this environment: {exc}",
        )
    return TorchAvailability(available=True)


def describe_runtime_shape(config: ModelConfig) -> dict:
    graph = build_model_graph(config)
    return {
        "variant": config.variant.kind,
        "kv_owner_layers": [layer.is_kv_owner for layer in graph.layers],
        "kv_source_layers": [layer.kv_source_layer for layer in graph.layers],
        "intended_modules": [
            "token_embedding",
            "decoder_blocks",
            "attention",
            "ffn",
            "norm",
        ],
        "status": "torch runtime available when torch is installed",
    }


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


def _require_torch():
    try:
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
    except ModuleNotFoundError as exc:  # pragma: no cover - guarded by tests
        raise RuntimeError("torch runtime requested but torch is not installed") from exc
    return torch, nn, F


def _repeat_kv(torch_mod, x, repeats: int):
    if repeats == 1:
        return x
    return torch_mod.repeat_interleave(x, repeats, dim=1)


def _causal_mask(torch_mod, seq_len: int, device):
    return torch_mod.triu(torch_mod.ones(seq_len, seq_len, dtype=torch_mod.bool, device=device), diagonal=1)


def _compress_history_cache(torch_mod, cache, *, recent_window: int, compression_ratio: int):
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
        blocks.append(block.mean(dim=2, keepdim=True))
    compressed_old = torch_mod.cat(blocks, dim=2) if blocks else old_cache[:, :, :0, :]
    return torch_mod.cat([compressed_old, recent_cache], dim=2)


def build_tiny_torch_model(config: ModelConfig, *, active_seq_len: int | None = None):
    torch, nn, _ = _require_torch()
    graph = build_model_graph(config)
    resolved_seq_len = active_seq_len or config.max_seq_len
    attn_head_dim = _effective_head_dim(config, resolved_seq_len)
    attn_output_scale = _compressed_attention_output_scale(config, resolved_seq_len)
    front_block_value_scale = _compressed_attention_front_block_value_scale(config, resolved_seq_len)
    mhc_rank = _mhc_mix_rank(config)

    class TinyAttention(nn.Module):
        def __init__(self, layer_spec):
            super().__init__()
            self.layer_spec = layer_spec
            self.q_proj = nn.Linear(config.d_model, layer_spec.n_query_heads * attn_head_dim, bias=False)
            self.out_proj = nn.Linear(layer_spec.n_query_heads * attn_head_dim, config.d_model, bias=False)
            if layer_spec.index == 0 and front_block_value_scale != 1.0:
                with torch.no_grad():
                    self.out_proj.weight.mul_(front_block_value_scale)
            if layer_spec.is_kv_owner:
                self.k_proj = nn.Linear(config.d_model, config.n_kv_heads * attn_head_dim, bias=False)
                self.v_proj = nn.Linear(config.d_model, config.n_kv_heads * attn_head_dim, bias=False)
                if layer_spec.index == 0 and front_block_value_scale != 1.0:
                    with torch.no_grad():
                        self.v_proj.weight.mul_(front_block_value_scale)
            else:
                self.k_proj = None
                self.v_proj = None

        def forward(self, x, kv_cache):
            batch_size, seq_len, _ = x.shape
            q = self.q_proj(x)
            q = q.view(batch_size, seq_len, self.layer_spec.n_query_heads, attn_head_dim).permute(0, 2, 1, 3)

            if self.layer_spec.is_kv_owner:
                k = self.k_proj(x)
                v = self.v_proj(x)
                k = k.view(batch_size, seq_len, config.n_kv_heads, attn_head_dim).permute(0, 2, 1, 3)
                v = v.view(batch_size, seq_len, config.n_kv_heads, attn_head_dim).permute(0, 2, 1, 3)
                if config.variant.kind == "history_compression":
                    k = _compress_history_cache(
                        torch,
                        k,
                        recent_window=_history_recent_window(config) or seq_len,
                        compression_ratio=_history_compression_ratio(config) or 1,
                    )
                    v = _compress_history_cache(
                        torch,
                        v,
                        recent_window=_history_recent_window(config) or seq_len,
                        compression_ratio=_history_compression_ratio(config) or 1,
                    )
                kv_cache[self.layer_spec.index] = (k, v)
            else:
                k, v = kv_cache[self.layer_spec.kv_source_layer]

            q_repeat = self.layer_spec.n_query_heads // config.n_kv_heads
            if q_repeat * config.n_kv_heads != self.layer_spec.n_query_heads:
                raise ValueError("per-layer query heads must be divisible by kv heads")
            k_for_q = _repeat_kv(torch, k, q_repeat)
            v_for_q = _repeat_kv(torch, v, q_repeat)

            scores = torch.matmul(q, k_for_q.transpose(-2, -1)) / (attn_head_dim ** 0.5)
            if k_for_q.shape[-2] == seq_len and config.variant.kind != "history_compression":
                mask = _causal_mask(torch, seq_len, x.device)
                scores = scores.masked_fill(mask.unsqueeze(0).unsqueeze(0), float("-inf"))
            attn = torch.softmax(scores, dim=-1)
            context = torch.matmul(attn, v_for_q)
            context = context.permute(0, 2, 1, 3).contiguous().view(
                batch_size,
                seq_len,
                self.layer_spec.n_query_heads * attn_head_dim,
            )
            return self.out_proj(context) * attn_output_scale, kv_cache

    class TinyFFN(nn.Module):
        def __init__(self):
            super().__init__()
            self.up = nn.Linear(config.d_model, config.ffn_hidden_dim, bias=False)
            self.gate = nn.Linear(config.d_model, config.ffn_hidden_dim, bias=False)
            self.down = nn.Linear(config.ffn_hidden_dim, config.d_model, bias=False)

        def forward(self, x):
            return self.down(self.up(x) * torch.sigmoid(self.gate(x)))

    class TinyDecoderBlock(nn.Module):
        def __init__(self, layer_spec):
            super().__init__()
            self.layer_spec = layer_spec
            self.attn_norm = nn.LayerNorm(config.d_model)
            self.ffn_norm = nn.LayerNorm(config.d_model)
            self.attn = TinyAttention(layer_spec)
            self.ffn = TinyFFN()
            if mhc_rank is not None:
                streams = config.variant.residual_stream_count
                self.mhc_in = nn.Linear(config.d_model, streams * mhc_rank, bias=False)
                self.mhc_out = nn.Parameter(torch.zeros(streams, mhc_rank, config.d_model))
                self.mhc_gate = nn.Linear(config.d_model, streams, bias=False)
                nn.init.normal_(self.mhc_out, mean=0.0, std=0.02)
            else:
                self.mhc_in = None
                self.mhc_out = None
                self.mhc_gate = None

        def forward(self, x, kv_cache):
            attn_out, kv_cache = self.attn(self.attn_norm(x), kv_cache)
            x = x + attn_out
            x = x + self.ffn(self.ffn_norm(x))
            if self.mhc_in is not None and self.mhc_out is not None and self.mhc_gate is not None:
                batch_size, seq_len, _ = x.shape
                streams = config.variant.residual_stream_count
                mixed_basis = self.mhc_in(x).view(batch_size, seq_len, streams, mhc_rank)
                stream_updates = torch.einsum("bsur,urd->bsud", mixed_basis, self.mhc_out)
                stream_weights = torch.softmax(self.mhc_gate(x), dim=-1)
                mhc_update = torch.einsum("bsu,bsud->bsd", stream_weights, stream_updates)
                x = x + mhc_update
            return x, kv_cache

    class TinyTransformer(nn.Module):
        def __init__(self):
            super().__init__()
            self.graph: ModelGraph = graph
            self.embedding = nn.Embedding(config.vocab_size, config.d_model)
            self.blocks = nn.ModuleList([TinyDecoderBlock(layer) for layer in graph.layers])
            self.final_norm = nn.LayerNorm(config.d_model)

        def forward(self, token_ids):
            x = self.embedding(token_ids)
            kv_cache = {}
            layer_means = []
            for block in self.blocks:
                x, kv_cache = block(x, kv_cache)
                layer_means.append(float(x.detach().mean().item()))
            x = self.final_norm(x)
            return x, kv_cache, layer_means

    return TinyTransformer()


def run_torch_demo(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
) -> dict[str, Any]:
    if seq_len > config.max_seq_len:
        raise ValueError(f"seq_len {seq_len} exceeds config.max_seq_len {config.max_seq_len}")

    torch, _, _ = _require_torch()
    torch.manual_seed(seed)
    graph = build_model_graph(config)
    model = build_tiny_torch_model(config, active_seq_len=seq_len)
    token_ids = torch.randint(0, config.vocab_size, (batch_size, seq_len))
    with torch.no_grad():
        output, kv_cache, layer_means = model(token_ids)

    cache_shapes = []
    for layer in graph.layers:
        if layer.index not in kv_cache:
            cache_shapes.append(None)
        else:
            k, _ = kv_cache[layer.index]
            cache_shapes.append([int(v) for v in k.shape])

    return {
        "name": config.name,
        "variant": config.variant.kind,
        "input_shape": [batch_size, seq_len],
        "graph": graph.to_dict(),
        "torch_run": {
            "output_shape": [int(v) for v in output.shape],
            "owner_cache_count": len(kv_cache),
            "cache_shapes": cache_shapes,
            "layer_means": layer_means,
        },
        "notes": [
            "This is a tiny random-weight torch path for graph/runtime validation.",
            "It is not a trained model and is not intended as a quality benchmark.",
        ],
    }
