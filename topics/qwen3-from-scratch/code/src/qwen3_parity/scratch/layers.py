from __future__ import annotations

import math
from dataclasses import dataclass

import torch
from torch import Tensor, nn

from qwen3_parity.scratch.config import Qwen3DenseConfig


class RMSNorm(nn.Module):
    def __init__(self, hidden_size: int, eps: float) -> None:
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(hidden_size))

    def forward(self, x: Tensor) -> Tensor:
        input_dtype = x.dtype
        x = x.float()
        variance = x.pow(2).mean(dim=-1, keepdim=True)
        x = x * torch.rsqrt(variance + self.eps)
        return (self.weight * x).to(input_dtype)


@dataclass(frozen=True)
class RopeCache:
    cos: Tensor
    sin: Tensor


def build_rope_cache(
    *,
    head_dim: int,
    max_position_embeddings: int,
    rope_theta: float,
    device: torch.device | None = None,
) -> RopeCache:
    if head_dim % 2 != 0:
        raise ValueError(f"RoPE requires an even head_dim, got {head_dim}")

    inv_freq = 1.0 / (
        rope_theta ** (torch.arange(0, head_dim, 2, device=device).float() / head_dim)
    )
    positions = torch.arange(max_position_embeddings, device=device).float()
    freqs = torch.outer(positions, inv_freq)
    emb = torch.cat((freqs, freqs), dim=-1)
    return RopeCache(cos=emb.cos(), sin=emb.sin())


def rotate_half(x: Tensor) -> Tensor:
    half = x.shape[-1] // 2
    x1 = x[..., :half]
    x2 = x[..., half:]
    return torch.cat((-x2, x1), dim=-1)


def apply_rope(x: Tensor, rope_cache: RopeCache, *, offset: int = 0) -> Tensor:
    seq_len = x.shape[-2]
    cos = rope_cache.cos[offset : offset + seq_len].to(dtype=x.dtype, device=x.device)
    sin = rope_cache.sin[offset : offset + seq_len].to(dtype=x.dtype, device=x.device)
    cos = cos.unsqueeze(0).unsqueeze(0)
    sin = sin.unsqueeze(0).unsqueeze(0)
    return (x * cos) + (rotate_half(x) * sin)


class Qwen3MLP(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)
        self.act = nn.SiLU()

    def forward(self, x: Tensor) -> Tensor:
        return self.down_proj(self.act(self.gate_proj(x)) * self.up_proj(x))


class GroupedQueryAttention(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        if config.num_attention_heads % config.num_key_value_heads != 0:
            raise ValueError("num_attention_heads must be divisible by num_key_value_heads")

        self.hidden_size = config.hidden_size
        self.num_attention_heads = config.num_attention_heads
        self.num_key_value_heads = config.num_key_value_heads
        self.head_dim = config.head_dim
        self.group_size = config.num_attention_heads // config.num_key_value_heads
        self.q_out_dim = config.num_attention_heads * config.head_dim
        self.kv_out_dim = config.num_key_value_heads * config.head_dim
        self.scale = 1.0 / math.sqrt(config.head_dim)

        self.q_proj = nn.Linear(config.hidden_size, self.q_out_dim, bias=config.attention_bias)
        self.k_proj = nn.Linear(config.hidden_size, self.kv_out_dim, bias=config.attention_bias)
        self.v_proj = nn.Linear(config.hidden_size, self.kv_out_dim, bias=config.attention_bias)
        self.q_norm = RMSNorm(config.head_dim, config.rms_norm_eps)
        self.k_norm = RMSNorm(config.head_dim, config.rms_norm_eps)
        self.o_proj = nn.Linear(self.q_out_dim, config.hidden_size, bias=False)

    def _reshape_q(self, x: Tensor) -> Tensor:
        batch, seq_len, _ = x.shape
        return x.view(batch, seq_len, self.num_attention_heads, self.head_dim).transpose(1, 2)

    def _reshape_kv(self, x: Tensor) -> Tensor:
        batch, seq_len, _ = x.shape
        return x.view(batch, seq_len, self.num_key_value_heads, self.head_dim).transpose(1, 2)

    def forward(
        self,
        x: Tensor,
        *,
        rope_cache: RopeCache,
        attention_mask: Tensor | None = None,
        offset: int = 0,
    ) -> Tensor:
        q = self._reshape_q(self.q_proj(x))
        k = self._reshape_kv(self.k_proj(x))
        v = self._reshape_kv(self.v_proj(x))

        q = self.q_norm(q)
        k = self.k_norm(k)

        q = apply_rope(q, rope_cache, offset=offset)
        k = apply_rope(k, rope_cache, offset=offset)

        if self.group_size > 1:
            k = k.repeat_interleave(self.group_size, dim=1)
            v = v.repeat_interleave(self.group_size, dim=1)

        attn_scores = torch.matmul(q, k.transpose(-1, -2)) * self.scale
        if attention_mask is not None:
            attn_scores = attn_scores + attention_mask
        attn_probs = torch.softmax(attn_scores, dim=-1, dtype=torch.float32).to(q.dtype)
        attn_output = torch.matmul(attn_probs, v)
        attn_output = attn_output.transpose(1, 2).contiguous()
        batch, seq_len, _, _ = attn_output.shape
        attn_output = attn_output.view(batch, seq_len, self.num_attention_heads * self.head_dim)
        return self.o_proj(attn_output)


class Qwen3DecoderLayer(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        self.input_layernorm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.self_attn = GroupedQueryAttention(config)
        self.mlp = Qwen3MLP(config)

    def forward(
        self,
        x: Tensor,
        *,
        rope_cache: RopeCache,
        attention_mask: Tensor | None = None,
        offset: int = 0,
    ) -> Tensor:
        x = x + self.self_attn(
            self.input_layernorm(x),
            rope_cache=rope_cache,
            attention_mask=attention_mask,
            offset=offset,
        )
        x = x + self.mlp(self.post_attention_layernorm(x))
        return x
