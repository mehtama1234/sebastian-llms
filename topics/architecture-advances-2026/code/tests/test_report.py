from __future__ import annotations

from pathlib import Path

from arch_adv_2026.config import load_config
from arch_adv_2026.report import generate_variant_report, resolve_variant_target_config_path, VariantTarget


ROOT = Path(__file__).resolve().parents[1]


def test_report_contains_all_current_variants() -> None:
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
        seed=29,
        report_runs=2,
    )
    assert len(report["variant_rows"]) == 6
    assert report["baseline"]["report_runs"] == 2
    assert set(report["rankings"]["lowest_estimated_flops"]) == {
        "kv_sharing",
        "attention_budgeting",
        "per_layer_embeddings",
        "compressed_attention",
        "history_compression",
        "mhc",
    }


def test_report_captures_expected_directional_deltas() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    variants = [
        load_config(ROOT / "configs" / "micro-kv-sharing.json"),
        load_config(ROOT / "configs" / "micro-ple.json"),
        load_config(ROOT / "configs" / "micro-history-compression.json"),
    ]
    report = generate_variant_report(
        baseline,
        variants,
        seq_len=8,
        warmup_runs=0,
        measured_runs=1,
        seed=31,
        report_runs=2,
    )
    rows = {row["variant"]: row for row in report["variant_rows"]}
    assert rows["kv_sharing"]["estimated_kv_cache_bytes_delta"] < 0
    assert rows["history_compression"]["estimated_kv_cache_bytes_delta"] < 0
    assert rows["per_layer_embeddings"]["estimated_flops_delta"] > 0
    assert "mean_ratio_vs_baseline_stdev" in rows["kv_sharing"]


def test_report_resolves_compressed_attention_override(monkeypatch) -> None:
    monkeypatch.setenv("ARCH_ADV_MICRO_COMPRESSED_ATTENTION_CONFIG", "configs/micro-compressed-attention-d12.json")
    resolved = resolve_variant_target_config_path(str(ROOT), VariantTarget("compressed_attention", "configs/micro-compressed-attention.json"))
    assert resolved.endswith("configs/micro-compressed-attention-d12.json")
