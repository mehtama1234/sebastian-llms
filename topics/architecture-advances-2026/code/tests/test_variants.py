from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.variants import kv_owner_layers


ROOT = Path(__file__).resolve().parents[1]


def test_baseline_owns_all_kv_layers() -> None:
    config = load_config(ROOT / "configs" / "tiny-baseline.json")
    assert kv_owner_layers(config) == [True] * config.n_layers


def test_kv_sharing_every_other_layer() -> None:
    config = load_config(ROOT / "configs" / "tiny-kv-sharing.json")
    assert kv_owner_layers(config) == [
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
        True,
        False,
    ]
