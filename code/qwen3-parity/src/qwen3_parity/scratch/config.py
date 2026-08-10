from __future__ import annotations

from dataclasses import asdict, dataclass
from dataclasses import replace
from typing import Any


@dataclass(frozen=True)
class Qwen3DenseConfig:
    model_id: str
    architecture: str
    model_type: str
    vocab_size: int
    hidden_size: int
    intermediate_size: int
    num_hidden_layers: int
    num_attention_heads: int
    num_key_value_heads: int
    head_dim: int
    hidden_act: str
    max_position_embeddings: int
    max_window_layers: int
    rms_norm_eps: float
    rope_theta: float | None
    rope_scaling: Any | None
    attention_bias: bool
    attention_dropout: float
    use_cache: bool
    use_sliding_window: bool
    sliding_window: int | None
    tie_word_embeddings: bool
    bos_token_id: int
    eos_token_id: int
    torch_dtype: str
    transformers_version: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def effective_rope_theta(self) -> float:
        if self.rope_theta is not None:
            return float(self.rope_theta)
        if isinstance(self.rope_scaling, dict) and "rope_theta" in self.rope_scaling:
            return float(self.rope_scaling["rope_theta"])
        raise ValueError("No rope theta is available in the config")


QWEN3_0_6B_CONFIG = Qwen3DenseConfig(
    model_id="Qwen/Qwen3-0.6B",
    architecture="Qwen3ForCausalLM",
    model_type="qwen3",
    vocab_size=151_936,
    hidden_size=1_024,
    intermediate_size=3_072,
    num_hidden_layers=28,
    num_attention_heads=16,
    num_key_value_heads=8,
    head_dim=128,
    hidden_act="silu",
    max_position_embeddings=40_960,
    max_window_layers=28,
    rms_norm_eps=1e-6,
    rope_theta=None,
    rope_scaling={"rope_theta": 1_000_000, "rope_type": "default"},
    attention_bias=False,
    attention_dropout=0.0,
    use_cache=True,
    use_sliding_window=False,
    sliding_window=None,
    tie_word_embeddings=True,
    bos_token_id=151_643,
    eos_token_id=151_645,
    torch_dtype="bfloat16",
    transformers_version="4.51.0",
)


def build_tiny_test_config() -> Qwen3DenseConfig:
    return replace(
        QWEN3_0_6B_CONFIG,
        model_id="local/qwen3-tiny-test",
        vocab_size=256,
        hidden_size=64,
        intermediate_size=128,
        num_hidden_layers=2,
        num_attention_heads=4,
        num_key_value_heads=2,
        head_dim=16,
        max_position_embeddings=128,
        max_window_layers=2,
        bos_token_id=1,
        eos_token_id=2,
        tie_word_embeddings=False,
    )


def build_prefix_test_config(num_hidden_layers: int) -> Qwen3DenseConfig:
    if num_hidden_layers <= 0:
        raise ValueError(f"num_hidden_layers must be positive, got {num_hidden_layers}")
    if num_hidden_layers > QWEN3_0_6B_CONFIG.num_hidden_layers:
        raise ValueError(
            "num_hidden_layers exceeds the reference model depth: "
            f"{num_hidden_layers} > {QWEN3_0_6B_CONFIG.num_hidden_layers}"
        )
    return replace(
        QWEN3_0_6B_CONFIG,
        model_id=f"{QWEN3_0_6B_CONFIG.model_id}-prefix-{num_hidden_layers}l",
        num_hidden_layers=num_hidden_layers,
        max_window_layers=min(QWEN3_0_6B_CONFIG.max_window_layers, num_hidden_layers),
    )
