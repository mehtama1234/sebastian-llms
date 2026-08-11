from __future__ import annotations

from types import SimpleNamespace

from torch import nn

from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG, Qwen3DenseConfig
from qwen3_parity.scratch.layers import RMSNorm
from qwen3_parity.weight_map import WeightMappingEntry


class _PartialSelfAttention(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        self.q_proj = nn.Linear(
            config.hidden_size,
            config.num_attention_heads * config.head_dim,
            bias=config.attention_bias,
        )
        self.k_proj = nn.Linear(
            config.hidden_size,
            config.num_key_value_heads * config.head_dim,
            bias=config.attention_bias,
        )
        self.v_proj = nn.Linear(
            config.hidden_size,
            config.num_key_value_heads * config.head_dim,
            bias=config.attention_bias,
        )
        self.q_norm = RMSNorm(config.head_dim, config.rms_norm_eps)
        self.k_norm = RMSNorm(config.head_dim, config.rms_norm_eps)
        self.o_proj = nn.Linear(
            config.num_attention_heads * config.head_dim,
            config.hidden_size,
            bias=False,
        )


class _PartialMLP(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        self.gate_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.up_proj = nn.Linear(config.hidden_size, config.intermediate_size, bias=False)
        self.down_proj = nn.Linear(config.intermediate_size, config.hidden_size, bias=False)


class _PartialLayer(nn.Module):
    def __init__(self, config: Qwen3DenseConfig) -> None:
        super().__init__()
        self.input_layernorm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.post_attention_layernorm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.self_attn = _PartialSelfAttention(config)
        self.mlp = _PartialMLP(config)


class Layer0NormReceiver(nn.Module):
    def __init__(self, config: Qwen3DenseConfig = QWEN3_0_6B_CONFIG) -> None:
        super().__init__()
        self.config = config
        self.layers = nn.ModuleList([_PartialLayer(config)])


class StructuralSliceReceiver(nn.Module):
    def __init__(self, config: Qwen3DenseConfig = QWEN3_0_6B_CONFIG) -> None:
        super().__init__()
        self.config = config
        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = nn.ModuleList([_PartialLayer(config)])
        self.norm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)


def build_layer0_norm_mapping() -> list[WeightMappingEntry]:
    return [
        WeightMappingEntry(
            "model.layers.0.input_layernorm.weight",
            "layers.0.input_layernorm.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.post_attention_layernorm.weight",
            "layers.0.post_attention_layernorm.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.self_attn.q_norm.weight",
            "layers.0.self_attn.q_norm.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.self_attn.k_norm.weight",
            "layers.0.self_attn.k_norm.weight",
        ),
    ]


def build_layer0_structural_mapping() -> list[WeightMappingEntry]:
    return build_layer0_norm_mapping() + [
        WeightMappingEntry(
            "model.layers.0.self_attn.q_proj.weight",
            "layers.0.self_attn.q_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.self_attn.k_proj.weight",
            "layers.0.self_attn.k_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.self_attn.v_proj.weight",
            "layers.0.self_attn.v_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.self_attn.o_proj.weight",
            "layers.0.self_attn.o_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.mlp.gate_proj.weight",
            "layers.0.mlp.gate_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.mlp.up_proj.weight",
            "layers.0.mlp.up_proj.weight",
        ),
        WeightMappingEntry(
            "model.layers.0.mlp.down_proj.weight",
            "layers.0.mlp.down_proj.weight",
        ),
    ]


def build_structural_slice_mapping() -> list[WeightMappingEntry]:
    return [
        WeightMappingEntry("model.embed_tokens.weight", "embed_tokens.weight"),
        WeightMappingEntry("model.norm.weight", "norm.weight"),
        WeightMappingEntry("lm_head.weight", "lm_head.weight"),
    ] + build_layer0_structural_mapping()
