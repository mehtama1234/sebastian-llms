from __future__ import annotations

import pytest

from llm_dev_2026.config import (
    ContextPolicy,
    HarnessConfig,
    InstructionMode,
    RetrievalMode,
    load_config,
    load_matrix,
)


def test_defaults_and_roundtrip():
    cfg = HarnessConfig("c1")
    assert cfg.retrieval_mode is RetrievalMode.LEXICAL
    assert cfg.context_policy is ContextPolicy.INLINE_FULL
    restored = HarnessConfig.from_dict(cfg.to_dict())
    assert restored == cfg


def test_string_enums_are_normalized():
    cfg = HarnessConfig.from_dict(
        {"name": "c", "retrieval_mode": "hybrid", "context_policy": "pointer", "instruction_mode": "root"}
    )
    assert cfg.retrieval_mode is RetrievalMode.HYBRID
    assert cfg.context_policy is ContextPolicy.POINTER
    assert cfg.instruction_mode is InstructionMode.ROOT


@pytest.mark.parametrize(
    "kwargs",
    [
        {"top_k": 0},
        {"snippet_window": 0},
        {"candidate_count": 0},
        {"confidence_threshold": 1.5},
        {"max_retries": -1},
        {"max_retries": 2},  # retries without verifier
    ],
)
def test_invalid_configs_raise(kwargs):
    with pytest.raises(ValueError):
        HarnessConfig("bad", **kwargs)


def test_retries_allowed_with_verifier():
    cfg = HarnessConfig("ok", verifier_enabled=True, max_retries=2)
    assert cfg.max_retries == 2


def test_load_config_and_matrix(tmp_path):
    import json

    cfg_path = tmp_path / "c.json"
    cfg_path.write_text(json.dumps(HarnessConfig("c", verifier_enabled=True).to_dict()))
    assert load_config(cfg_path).verifier_enabled is True

    matrix_path = tmp_path / "m.json"
    matrix_path.write_text(
        json.dumps(
            {
                "label": "m",
                "configs": [HarnessConfig("a").to_dict(), HarnessConfig("b", top_k=5).to_dict()],
            }
        )
    )
    matrix = load_matrix(matrix_path)
    assert matrix.label == "m"
    assert [c.name for c in matrix.configs] == ["a", "b"]
    assert matrix.configs[1].top_k == 5
