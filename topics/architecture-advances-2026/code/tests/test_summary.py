from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.summary import build_summary


ROOT = Path(__file__).resolve().parents[1]


def test_kv_sharing_reduces_cache_estimate() -> None:
    baseline = load_config(ROOT / "configs" / "tiny-baseline.json")
    shared = load_config(ROOT / "configs" / "tiny-kv-sharing.json")
    baseline_summary = build_summary(baseline)
    shared_summary = build_summary(shared)
    assert baseline_summary["kv_cache"]["bytes_saved"] == 0
    assert shared_summary["kv_cache"]["bytes_saved"] > 0
    assert shared_summary["kv_cache"]["saving_ratio"] == 0.5


def test_summary_includes_layer_graph() -> None:
    config = load_config(ROOT / "configs" / "tiny-kv-sharing.json")
    summary = build_summary(config)
    assert "graph" in summary
    assert len(summary["graph"]["layers"]) == config.n_layers
