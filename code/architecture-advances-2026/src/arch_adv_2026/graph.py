from __future__ import annotations

from dataclasses import asdict, dataclass

from .config import ModelConfig
from .variants import kv_owner_layers


@dataclass(slots=True)
class LayerSpec:
    index: int
    attention_pattern: str
    is_kv_owner: bool
    kv_source_layer: int
    n_query_heads: int
    n_kv_heads: int
    head_dim: int
    ffn_hidden_dim: int


@dataclass(slots=True)
class ModelGraph:
    name: str
    variant_kind: str
    layers: list[LayerSpec]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "variant_kind": self.variant_kind,
            "layers": [asdict(layer) for layer in self.layers],
        }


def build_model_graph(config: ModelConfig) -> ModelGraph:
    owners = kv_owner_layers(config)
    layers: list[LayerSpec] = []
    last_owner = 0
    for idx, is_owner in enumerate(owners):
        if is_owner:
            last_owner = idx
        layers.append(
            LayerSpec(
                index=idx,
                attention_pattern=config.attention_pattern,
                is_kv_owner=is_owner,
                kv_source_layer=last_owner,
                n_query_heads=config.query_heads_for_layer(idx),
                n_kv_heads=config.n_kv_heads,
                head_dim=config.head_dim,
                ffn_hidden_dim=config.ffn_hidden_dim,
            )
        )
    return ModelGraph(name=config.name, variant_kind=config.variant.kind, layers=layers)
