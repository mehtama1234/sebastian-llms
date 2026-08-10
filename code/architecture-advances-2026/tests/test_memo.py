from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.memo import generate_decision_memo, render_decision_memo_markdown
from arch_adv_2026.report import generate_variant_report


ROOT = Path(__file__).resolve().parents[1]


def test_decision_memo_contains_core_sections() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variants = [
        load_config(ROOT / "configs" / "micro-kv-sharing.json"),
        load_config(ROOT / "configs" / "micro-attention-budgeting.json"),
        load_config(ROOT / "configs" / "micro-ple.json"),
        load_config(ROOT / "configs" / "micro-compressed-attention.json"),
        load_config(ROOT / "configs" / "micro-history-compression.json"),
        load_config(ROOT / "configs" / "micro-mhc.json"),
    ]
    report = generate_variant_report(
        baseline,
        variants,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=37,
        report_runs=2,
    )
    memo = generate_decision_memo(report)
    markdown = render_decision_memo_markdown(memo, report)
    assert memo["headline"] == "Micro-scale architecture decision memo"
    assert "## Bottom line" in markdown
    assert "## Recommendations" in markdown
    assert "## Variant Matrix" in markdown
    assert "Ratio Stdev" in markdown


def test_decision_memo_mentions_expected_variant_roles() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variants = [
        load_config(ROOT / "configs" / "micro-kv-sharing.json"),
        load_config(ROOT / "configs" / "micro-attention-budgeting.json"),
        load_config(ROOT / "configs" / "micro-ple.json"),
        load_config(ROOT / "configs" / "micro-compressed-attention.json"),
        load_config(ROOT / "configs" / "micro-history-compression.json"),
        load_config(ROOT / "configs" / "micro-mhc.json"),
    ]
    report = generate_variant_report(
        baseline,
        variants,
        seq_len=4,
        warmup_runs=0,
        measured_runs=1,
        seed=41,
        report_runs=2,
    )
    memo = generate_decision_memo(report)
    joined = "\n".join(memo["recommendations"])
    assert "kv_sharing" in joined or "compressed_attention" in joined
    assert "per_layer_embeddings" in joined
