from __future__ import annotations

import json
from pathlib import Path

from arch_adv_2026.long_context_variant_execute import execute_variant_run_plan
from arch_adv_2026.long_context_variant_plan import (
    EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
    EXECUTION_MODE_SUMMARY_ONLY,
)


def _write_config(path: Path, *, name: str, variant: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "name": name,
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
                "variant": variant,
            }
        ),
        encoding="utf-8",
    )


def test_execute_variant_run_plan_materializes_focused_proxy_compare(tmp_path: Path) -> None:
    baseline_config = tmp_path / "configs" / "qwen3-baseline.json"
    selected_config = tmp_path / "configs" / "qwen3-compressed-attention.json"
    _write_config(baseline_config, name="qwen3-baseline", variant={"kind": "baseline"})
    _write_config(
        selected_config,
        name="qwen3-compressed-attention",
        variant={"kind": "compressed_attention", "compressed_head_dim": 4},
    )

    plan = {
        "workflow": "long_context_variant_proxy",
        "objective": "quality_preserving_memory",
        "config_family": "qwen3",
        "execution_mode": EXECUTION_MODE_FOCUSED_PROXY_COMPARE,
        "selected_variant_kind": "compressed_attention",
        "selected_config_path": str(selected_config),
        "baseline_config_path": str(baseline_config),
        "planned_selected_summary_artifact_path": str(tmp_path / "artifacts" / "selected-summary.json"),
        "planned_baseline_summary_artifact_path": str(tmp_path / "artifacts" / "baseline-summary.json"),
        "planned_focused_compare_artifact_path": str(tmp_path / "artifacts" / "focused-compare.json"),
        "focused_compare_params": {
            "filler_repeat_values": [32, 64],
            "cases_per_length": 1,
            "seed": 17,
            "sweep_runs": 1,
        },
    }

    execution = execute_variant_run_plan(plan)
    assert Path(execution["selected_summary_artifact_path"]).exists()
    assert Path(execution["baseline_summary_artifact_path"]).exists()
    assert Path(execution["focused_compare_artifact_path"]).exists()
    assert execution["focused_compare_result"] is not None
    assert execution["focused_compare_summary"]["selected_bucket"]["variant_kind"] == "compressed_attention"
    assert execution["delta"]["kv_cache_saving_ratio_vs_baseline"] > 0.0


def test_execute_variant_run_plan_supports_summary_only_mode(tmp_path: Path) -> None:
    baseline_config = tmp_path / "configs" / "qwen3-baseline.json"
    selected_config = tmp_path / "configs" / "qwen3-mhc.json"
    _write_config(baseline_config, name="qwen3-baseline", variant={"kind": "baseline"})
    _write_config(
        selected_config,
        name="qwen3-mhc",
        variant={"kind": "mhc", "residual_stream_count": 2},
    )

    plan = {
        "workflow": "long_context_variant_proxy",
        "objective": "quality",
        "config_family": "qwen3",
        "execution_mode": EXECUTION_MODE_SUMMARY_ONLY,
        "selected_variant_kind": "mhc",
        "selected_config_path": str(selected_config),
        "baseline_config_path": str(baseline_config),
        "planned_selected_summary_artifact_path": str(tmp_path / "artifacts" / "selected-summary.json"),
        "planned_baseline_summary_artifact_path": str(tmp_path / "artifacts" / "baseline-summary.json"),
        "planned_focused_compare_artifact_path": str(tmp_path / "artifacts" / "focused-compare.json"),
        "focused_compare_params": None,
    }

    execution = execute_variant_run_plan(plan)
    assert execution["execution_mode"] == EXECUTION_MODE_SUMMARY_ONLY
    assert execution["focused_compare_result"] is None
    assert execution["focused_compare_summary"] is None
    assert not Path(execution["focused_compare_artifact_path"]).exists()
