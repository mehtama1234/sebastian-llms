from __future__ import annotations

from pathlib import Path

from arch_adv_2026.compressed_attention_candidate_probe import (
    build_compressed_attention_candidate_probe,
    materialize_candidate_config,
    parse_candidate_spec,
    render_compressed_attention_candidate_probe_markdown,
)
from arch_adv_2026.config import load_config


ROOT = Path(__file__).resolve().parents[1]


def test_parse_candidate_spec_supports_sparse_fields() -> None:
    spec = parse_candidate_spec("q6::6:24")
    assert spec.label == "q6"
    assert spec.compressed_head_dim is None
    assert spec.query_heads == 6
    assert spec.min_compression_seq_len == 24


def test_materialize_candidate_config_applies_overrides() -> None:
    base = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    candidate = materialize_candidate_config(base, parse_candidate_spec("d10q6:10:6:24"))
    assert candidate.variant.compressed_head_dim == 10
    assert candidate.variant.per_layer_query_heads == [6] * base.n_layers
    assert candidate.variant.min_compression_seq_len == 24


def test_build_candidate_probe_smoke() -> None:
    baseline = load_config(ROOT / "configs" / "micro-baseline.json")
    base = load_config(ROOT / "configs" / "micro-compressed-attention.json")
    probe = build_compressed_attention_candidate_probe(
        baseline,
        base,
        [parse_candidate_spec("current"), parse_candidate_spec("t24:::24")],
        training_batch_sizes=[2],
        training_seq_lens=[16],
        training_steps=[2],
        training_seeds=[5],
        benchmark_batch_sizes=[1],
        benchmark_seq_lens=[16],
        lr=1e-2,
        clip_grad_norm=1.0,
        training_report_runs=1,
        benchmark_warmup_runs=0,
        benchmark_measured_runs=1,
        benchmark_report_runs=1,
    )
    assert probe["candidate_count"] == 2
    assert len(probe["candidates"]) == 2
    assert all("summary" in candidate for candidate in probe["candidates"])
    markdown = render_compressed_attention_candidate_probe_markdown(probe)
    assert "Compressed Attention Candidate Probe" in markdown
    assert "Mean Loss Delta" in markdown
