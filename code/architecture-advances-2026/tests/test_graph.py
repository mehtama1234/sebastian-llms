from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.graph import build_model_graph


ROOT = Path(__file__).resolve().parents[1]


def test_graph_kv_sources_follow_last_owner() -> None:
    config = load_config(ROOT / "configs" / "tiny-kv-sharing.json")
    graph = build_model_graph(config)
    assert [layer.kv_source_layer for layer in graph.layers] == [0, 0, 2, 2, 4, 4, 6, 6, 8, 8, 10, 10]
    assert graph.layers[1].is_kv_owner is False
    assert graph.layers[2].is_kv_owner is True
