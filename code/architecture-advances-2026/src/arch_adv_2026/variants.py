from __future__ import annotations

from .config import ModelConfig


def kv_owner_layers(config: ModelConfig) -> list[bool]:
    if config.variant.kind != "kv_sharing":
        return [True] * config.n_layers

    share_every = config.variant.share_every or 2
    owners: list[bool] = []
    tail_start = config.n_layers // 2 if config.variant.tail_layers_only else 0

    for idx in range(config.n_layers):
        if idx < tail_start:
            owners.append(True)
            continue
        owners.append((idx - tail_start) % share_every == 0)

    if not owners or not owners[0]:
        owners[0] = True
    return owners
