from __future__ import annotations

import json
from pathlib import Path

from arch_adv_2026.long_context_matrix import execute_matrix
from arch_adv_2026.long_context_plan import BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_SUMMARY_ONLY
from arch_adv_2026.long_context_plan import resolve_config_path


def _write_config(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_execute_matrix_materializes_requested_objective_mode_pairs(tmp_path: Path) -> None:
    selector = {
        "reference_model_id": "Qwen/Qwen3-0.6B",
        "selection_policy": {
            "minimum_reference_pass_rate": 0.5,
            "fallback_to_all_rows_if_no_bucket_meets_threshold": True,
            "used_fallback_rows": False,
            "acceptable_row_count": 4,
            "total_row_count": 8,
        },
        "recommendations": {
            "memory": {"variant_kind": "kv_sharing"},
            "speed": {"variant_kind": "compressed_attention"},
            "balanced": {"variant_kind": "compressed_attention"},
        },
    }

    configs = {
        "qwen3-baseline": {
            "name": "qwen3-baseline",
            "vocab_size": 100,
            "max_seq_len": 64,
            "d_model": 32,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 8,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "baseline"},
        },
        "qwen3-kv-sharing": {
            "name": "qwen3-kv-sharing",
            "vocab_size": 100,
            "max_seq_len": 64,
            "d_model": 32,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 8,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "kv_sharing", "share_every": 2},
        },
        "qwen3-compressed-attention": {
            "name": "qwen3-compressed-attention",
            "vocab_size": 100,
            "max_seq_len": 64,
            "d_model": 32,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 8,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "compressed_attention", "compressed_head_dim": 4},
        },
        "micro-baseline": {
            "name": "micro-baseline",
            "vocab_size": 64,
            "max_seq_len": 32,
            "d_model": 16,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 4,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "baseline"},
        },
        "micro-kv-sharing": {
            "name": "micro-kv-sharing",
            "vocab_size": 64,
            "max_seq_len": 32,
            "d_model": 16,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 4,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "kv_sharing", "share_every": 2},
        },
        "micro-compressed-attention": {
            "name": "micro-compressed-attention",
            "vocab_size": 64,
            "max_seq_len": 32,
            "d_model": 16,
            "n_layers": 4,
            "n_query_heads": 4,
            "n_kv_heads": 2,
            "head_dim": 4,
            "ffn_mult": 2.0,
            "attention_pattern": "full",
            "window_size": None,
            "variant": {"kind": "compressed_attention", "compressed_head_dim": 2},
        },
    }

    for key, payload in configs.items():
        if key.startswith("qwen3-"):
            variant_kind = key.removeprefix("qwen3-").replace("-", "_")
            if variant_kind == "compressed_attention":
                variant_kind = "compressed_attention"
            elif variant_kind == "kv_sharing":
                variant_kind = "kv_sharing"
            else:
                variant_kind = "baseline"
            path = resolve_config_path(root_dir=tmp_path, config_family="qwen3", variant_kind=variant_kind)
        else:
            variant_kind = key.removeprefix("micro-").replace("-", "_")
            if variant_kind == "compressed_attention":
                variant_kind = "compressed_attention"
            elif variant_kind == "kv_sharing":
                variant_kind = "kv_sharing"
            else:
                variant_kind = "baseline"
            path = resolve_config_path(root_dir=tmp_path, config_family="micro", variant_kind=variant_kind)
        _write_config(path, payload)

    matrix = execute_matrix(
        selector,
        config_family="qwen3",
        root_dir=tmp_path,
        objectives=["memory", "speed"],
        benchmark_modes=[BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_SUMMARY_ONLY],
    )

    assert matrix["objectives"] == ["memory", "speed"]
    assert matrix["benchmark_modes"] == [BENCHMARK_MODE_PROXY_NUMERIC, BENCHMARK_MODE_SUMMARY_ONLY]
    assert matrix["row_count"] == 4

    rows = {(row["objective"], row["benchmark_mode"]): row for row in matrix["rows"]}
    memory_proxy = rows[("memory", BENCHMARK_MODE_PROXY_NUMERIC)]
    speed_summary = rows[("speed", BENCHMARK_MODE_SUMMARY_ONLY)]

    assert Path(memory_proxy["plan_artifact_path"]).exists()
    assert Path(memory_proxy["execution_artifact_path"]).exists()
    assert Path(memory_proxy["benchmark_artifact_path"]).exists()
    assert memory_proxy["selected_variant_kind"] == "kv_sharing"
    assert memory_proxy["benchmark_summary"] is not None

    assert Path(speed_summary["plan_artifact_path"]).exists()
    assert Path(speed_summary["execution_artifact_path"]).exists()
    assert not Path(speed_summary["benchmark_artifact_path"]).exists()
    assert speed_summary["selected_variant_kind"] == "compressed_attention"
    assert speed_summary["benchmark_summary"] is None
