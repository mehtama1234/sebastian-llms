from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.graph import build_model_graph
from arch_adv_2026.numeric_runtime import describe_numeric_demo
from arch_adv_2026.summary import build_summary
from arch_adv_2026.benchmark import compare_numeric_benchmarks


ROOT = Path(__file__).resolve().parents[1]


def test_attention_budgeting_graph_uses_per_layer_query_heads() -> None:
    config = load_config(ROOT / "configs" / "micro-attention-budgeting.json")
    graph = build_model_graph(config)
    assert [layer.n_query_heads for layer in graph.layers] == [4, 2, 4, 2]


def test_attention_budgeting_summary_reports_per_layer_query_heads() -> None:
    config = load_config(ROOT / "configs" / "tiny-attention-budgeting.json")
    summary = build_summary(config)
    assert summary["shape"]["per_layer_query_heads"] == [8, 8, 6, 6, 8, 8, 6, 6, 8, 8, 6, 6]


def test_attention_budgeting_numeric_demo_runs() -> None:
    config = load_config(ROOT / "configs" / "micro-attention-budgeting.json")
    result = describe_numeric_demo(config, seq_len=4, seed=5)
    assert result["numeric_run"]["output_shape"] == [1, 4, config.d_model]
    assert result["graph"]["layers"][1]["n_query_heads"] == 2


def test_attention_budgeting_reduces_estimated_flops_vs_baseline() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variant = load_config(ROOT / "configs" / "micro-attention-budgeting.json")
    result = compare_numeric_benchmarks(
        baseline,
        variant,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=11,
    )
    assert (
        result["demo_context"]["variant"]["numeric_run"]["estimated_flops"]
        < result["demo_context"]["baseline"]["numeric_run"]["estimated_flops"]
    )
