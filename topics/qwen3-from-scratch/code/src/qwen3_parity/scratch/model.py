from __future__ import annotations

import torch
from torch import Tensor, nn

from qwen3_parity.scratch.config import QWEN3_0_6B_CONFIG, Qwen3DenseConfig
from qwen3_parity.scratch.layers import Qwen3DecoderLayer, RMSNorm, RopeCache, build_rope_cache


def build_causal_mask(seq_len: int, *, device: torch.device | None = None) -> Tensor:
    mask = torch.full((seq_len, seq_len), float("-inf"), device=device)
    mask = torch.triu(mask, diagonal=1)
    return mask.unsqueeze(0).unsqueeze(0)


class Qwen3ScratchModel(nn.Module):
    def __init__(self, config: Qwen3DenseConfig = QWEN3_0_6B_CONFIG) -> None:
        super().__init__()
        self.config = config

        self.embed_tokens = nn.Embedding(config.vocab_size, config.hidden_size)
        self.layers = nn.ModuleList(
            Qwen3DecoderLayer(config) for _ in range(config.num_hidden_layers)
        )
        self.norm = RMSNorm(config.hidden_size, config.rms_norm_eps)
        self.lm_head = nn.Linear(config.hidden_size, config.vocab_size, bias=False)

        if config.tie_word_embeddings:
            self.lm_head.weight = self.embed_tokens.weight

        self._rope_cache: RopeCache | None = None

    def _get_rope_cache(self, device: torch.device) -> RopeCache:
        if self._rope_cache is None or self._rope_cache.cos.device != device:
            self._rope_cache = build_rope_cache(
                head_dim=self.config.head_dim,
                max_position_embeddings=self.config.max_position_embeddings,
                rope_theta=self.config.effective_rope_theta(),
                device=device,
            )
        return self._rope_cache

    def forward(self, input_ids: Tensor) -> Tensor:
        x = self.embed_tokens(input_ids)
        rope_cache = self._get_rope_cache(x.device)
        attention_mask = build_causal_mask(input_ids.shape[1], device=x.device)

        for layer in self.layers:
            x = layer(x, rope_cache=rope_cache, attention_mask=attention_mask)

        x = self.norm(x)
        return self.lm_head(x)
