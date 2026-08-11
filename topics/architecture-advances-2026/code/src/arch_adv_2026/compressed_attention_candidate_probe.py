from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any

from .config import ModelConfig, VariantConfig, load_config
from .report import generate_variant_report
from .training_report import generate_training_report


@dataclass(slots=True)
class CandidateSpec:
    label: str
    compressed_head_dim: int | None = None
    query_heads: int | None = None
    min_compression_seq_len: int | None = None


DEFAULT_CANDIDATES = (
    "current",
    "d10:10",
    "d12:12",
    "q6::6",
    "q8::8",
    "t24:::24",
    "d10q6:10:6",
)

DEFAULT_TRAINING_BATCH_SIZES = [2, 4]
DEFAULT_TRAINING_SEQ_LENS = [16]
DEFAULT_TRAINING_STEPS = [4, 8]
DEFAULT_TRAINING_SEEDS = [17, 23]
DEFAULT_BENCHMARK_BATCH_SIZES = [1, 2, 4]
DEFAULT_BENCHMARK_SEQ_LENS = [16, 32]
DEFAULT_TRAINING_REPORT_RUNS = 2
DEFAULT_BENCHMARK_WARMUP_RUNS = 1
DEFAULT_BENCHMARK_MEASURED_RUNS = 3
DEFAULT_BENCHMARK_REPORT_RUNS = 3


def parse_candidate_spec(raw: str) -> CandidateSpec:
    parts = raw.split(":")
    if not parts or not parts[0]:
        raise ValueError("candidate label must not be empty")
    if len(parts) > 4:
        raise ValueError("candidate specs support at most four colon-separated fields")

    label = parts[0]
    values = parts[1:] + [""] * (3 - len(parts[1:]))

    def _parse_optional_int(value: str, field_name: str) -> int | None:
        if value == "":
            return None
        parsed = int(value)
        if parsed <= 0:
            raise ValueError(f"{field_name} must be positive")
        return parsed

    return CandidateSpec(
        label=label,
        compressed_head_dim=_parse_optional_int(values[0], "compressed_head_dim"),
        query_heads=_parse_optional_int(values[1], "query_heads"),
        min_compression_seq_len=_parse_optional_int(values[2], "min_compression_seq_len"),
    )


def materialize_candidate_config(base: ModelConfig, spec: CandidateSpec) -> ModelConfig:
    variant = base.variant
    if spec.query_heads is not None and spec.query_heads % base.n_kv_heads != 0:
        raise ValueError("query_heads must be divisible by n_kv_heads")
    per_layer_query_heads = variant.per_layer_query_heads
    if spec.query_heads is not None:
        per_layer_query_heads = [spec.query_heads] * base.n_layers
    updated_variant = replace(
        variant,
        compressed_head_dim=spec.compressed_head_dim if spec.compressed_head_dim is not None else variant.compressed_head_dim,
        per_layer_query_heads=per_layer_query_heads,
        min_compression_seq_len=(
            spec.min_compression_seq_len
            if spec.min_compression_seq_len is not None
            else variant.min_compression_seq_len
        ),
    )
    return replace(base, name=f"{base.name}-{spec.label}", variant=updated_variant)


def evaluate_candidate(
    baseline: ModelConfig,
    candidate: ModelConfig,
    *,
    training_batch_sizes: list[int],
    training_seq_lens: list[int],
    training_steps: list[int],
    training_seeds: list[int],
    benchmark_batch_sizes: list[int],
    benchmark_seq_lens: list[int],
    lr: float,
    clip_grad_norm: float | None,
    training_report_runs: int,
    benchmark_warmup_runs: int,
    benchmark_measured_runs: int,
    benchmark_report_runs: int,
) -> dict[str, Any]:
    training_rows: list[dict[str, Any]] = []
    for batch_size in training_batch_sizes:
        for seq_len in training_seq_lens:
            for steps in training_steps:
                for seed in training_seeds:
                    row = generate_training_report(
                        baseline,
                        [candidate],
                        batch_size=batch_size,
                        seq_len=seq_len,
                        steps=steps,
                        lr=lr,
                        seed=seed,
                        clip_grad_norm=clip_grad_norm,
                        report_runs=training_report_runs,
                    )["variant_rows"][0]
                    training_rows.append(
                        {
                            "batch_size": batch_size,
                            "seq_len": seq_len,
                            "steps": steps,
                            "seed": seed,
                            "loss_delta": row["final_loss_delta_vs_baseline_mean"],
                            "speed_ratio": row["mean_step_ms_ratio_vs_baseline_mean"],
                        }
                    )

    benchmark_rows: list[dict[str, Any]] = []
    for batch_size in benchmark_batch_sizes:
        for seq_len in benchmark_seq_lens:
            row = generate_variant_report(
                baseline,
                [candidate],
                batch_size=batch_size,
                seq_len=seq_len,
                seed=0,
                warmup_runs=benchmark_warmup_runs,
                measured_runs=benchmark_measured_runs,
                report_runs=benchmark_report_runs,
            )["variant_rows"][0]
            benchmark_rows.append(
                {
                    "batch_size": batch_size,
                    "seq_len": seq_len,
                    "ratio": row["mean_ratio_vs_baseline_mean"],
                    "estimated_flops_delta": row["estimated_flops_delta"],
                    "estimated_kv_cache_bytes_delta": row["estimated_kv_cache_bytes_delta"],
                }
            )

    mean_loss = statistics.fmean(row["loss_delta"] for row in training_rows)
    max_loss = max(row["loss_delta"] for row in training_rows)
    mean_training_speed = statistics.fmean(row["speed_ratio"] for row in training_rows)
    max_training_speed = max(row["speed_ratio"] for row in training_rows)
    mean_benchmark_ratio = statistics.fmean(row["ratio"] for row in benchmark_rows)
    worst_benchmark_ratio = max(row["ratio"] for row in benchmark_rows)

    return {
        "label": candidate.name.removeprefix(f"{baseline.name}-"),
        "config_name": candidate.name,
        "variant": asdict(candidate.variant),
        "training_rows": training_rows,
        "benchmark_rows": benchmark_rows,
        "summary": {
            "mean_loss_delta": mean_loss,
            "max_loss_delta": max_loss,
            "mean_training_speed_ratio": mean_training_speed,
            "max_training_speed_ratio": max_training_speed,
            "mean_benchmark_ratio": mean_benchmark_ratio,
            "worst_benchmark_ratio": worst_benchmark_ratio,
            "training_loss_gate_pass": max_loss < 0.0,
            "training_speed_gate_pass": max_training_speed < 1.0,
            "benchmark_gate_pass": mean_benchmark_ratio <= 1.0 and worst_benchmark_ratio <= 1.10,
        },
    }


def build_compressed_attention_candidate_probe(
    baseline: ModelConfig,
    base_variant: ModelConfig,
    candidate_specs: list[CandidateSpec],
    *,
    training_batch_sizes: list[int],
    training_seq_lens: list[int],
    training_steps: list[int],
    training_seeds: list[int],
    benchmark_batch_sizes: list[int],
    benchmark_seq_lens: list[int],
    lr: float,
    clip_grad_norm: float | None,
    training_report_runs: int,
    benchmark_warmup_runs: int,
    benchmark_measured_runs: int,
    benchmark_report_runs: int,
) -> dict[str, Any]:
    candidates = [
        evaluate_candidate(
            baseline,
            materialize_candidate_config(base_variant, spec),
            training_batch_sizes=training_batch_sizes,
            training_seq_lens=training_seq_lens,
            training_steps=training_steps,
            training_seeds=training_seeds,
            benchmark_batch_sizes=benchmark_batch_sizes,
            benchmark_seq_lens=benchmark_seq_lens,
            lr=lr,
            clip_grad_norm=clip_grad_norm,
            training_report_runs=training_report_runs,
            benchmark_warmup_runs=benchmark_warmup_runs,
            benchmark_measured_runs=benchmark_measured_runs,
            benchmark_report_runs=benchmark_report_runs,
        )
        for spec in candidate_specs
    ]
    candidates.sort(
        key=lambda row: (
            row["summary"]["max_loss_delta"],
            row["summary"]["worst_benchmark_ratio"],
            row["summary"]["mean_loss_delta"],
            row["summary"]["mean_benchmark_ratio"],
            row["label"],
        )
    )
    return {
        "headline": "Compressed Attention Candidate Probe",
        "baseline": {"name": baseline.name, "variant": baseline.variant.kind},
        "base_variant": {"name": base_variant.name, "variant": asdict(base_variant.variant)},
        "training_grid": {
            "batch_sizes": training_batch_sizes,
            "seq_lens": training_seq_lens,
            "steps": training_steps,
            "seeds": training_seeds,
            "report_runs": training_report_runs,
            "lr": lr,
            "clip_grad_norm": clip_grad_norm,
        },
        "benchmark_grid": {
            "batch_sizes": benchmark_batch_sizes,
            "seq_lens": benchmark_seq_lens,
            "warmup_runs": benchmark_warmup_runs,
            "measured_runs": benchmark_measured_runs,
            "report_runs": benchmark_report_runs,
        },
        "candidate_count": len(candidates),
        "candidates": candidates,
    }


def render_compressed_attention_candidate_probe_markdown(probe: dict[str, Any]) -> str:
    lines = [f"# {probe['headline']}", ""]
    lines.append("## Summary")
    lines.append("")
    lines.append("| Candidate | Mean Loss Delta | Max Loss Delta | Mean Train Speed | Max Train Speed | Mean Bench Ratio | Worst Bench Ratio |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for candidate in probe["candidates"]:
        summary = candidate["summary"]
        lines.append(
            f"| `{candidate['label']}` | {summary['mean_loss_delta']:.3f} | {summary['max_loss_delta']:.3f} | "
            f"{summary['mean_training_speed_ratio']:.3f} | {summary['max_training_speed_ratio']:.3f} | "
            f"{summary['mean_benchmark_ratio']:.3f} | {summary['worst_benchmark_ratio']:.3f} |"
        )
    lines.append("")
    lines.append("## Selection Heuristic")
    lines.append("- Candidates are sorted by max loss delta first, then worst benchmark ratio, then mean loss delta, then mean benchmark ratio.")
    lines.append("")
    lines.append("## Probe Grids")
    lines.append(
        f"- Training: batch sizes `{probe['training_grid']['batch_sizes']}`, seq lens `{probe['training_grid']['seq_lens']}`, "
        f"steps `{probe['training_grid']['steps']}`, seeds `{probe['training_grid']['seeds']}`, report runs `{probe['training_grid']['report_runs']}`."
    )
    lines.append(
        f"- Benchmark: batch sizes `{probe['benchmark_grid']['batch_sizes']}`, seq lens `{probe['benchmark_grid']['seq_lens']}`, "
        f"warmup `{probe['benchmark_grid']['warmup_runs']}`, measured `{probe['benchmark_grid']['measured_runs']}`, report runs `{probe['benchmark_grid']['report_runs']}`."
    )
    lines.append("")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe candidate compressed_attention config variations on the active training and benchmark slices."
    )
    parser.add_argument("--root-dir", required=True)
    parser.add_argument("--variant-config", default="configs/micro-compressed-attention.json")
    parser.add_argument("--candidate", action="append", dest="candidates")
    parser.add_argument("--training-batch-size", action="append", dest="training_batch_sizes", type=int)
    parser.add_argument("--training-seq-len", action="append", dest="training_seq_lens", type=int)
    parser.add_argument("--training-steps", action="append", dest="training_steps", type=int)
    parser.add_argument("--training-seed", action="append", dest="training_seeds", type=int)
    parser.add_argument("--benchmark-batch-size", action="append", dest="benchmark_batch_sizes", type=int)
    parser.add_argument("--benchmark-seq-len", action="append", dest="benchmark_seq_lens", type=int)
    parser.add_argument("--lr", type=float, default=1e-2)
    parser.add_argument("--clip-grad-norm", type=float, default=1.0)
    parser.add_argument("--training-report-runs", type=int, default=DEFAULT_TRAINING_REPORT_RUNS)
    parser.add_argument("--benchmark-warmup-runs", type=int, default=DEFAULT_BENCHMARK_WARMUP_RUNS)
    parser.add_argument("--benchmark-measured-runs", type=int, default=DEFAULT_BENCHMARK_MEASURED_RUNS)
    parser.add_argument("--benchmark-report-runs", type=int, default=DEFAULT_BENCHMARK_REPORT_RUNS)
    parser.add_argument("--artifact-json")
    parser.add_argument("--artifact-md")
    parser.add_argument("--stdout", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    root_dir = Path(args.root_dir)
    baseline = load_config(root_dir / "configs" / "micro-baseline.json")
    base_variant = load_config(root_dir / args.variant_config)
    candidate_specs = [parse_candidate_spec(raw) for raw in (args.candidates or list(DEFAULT_CANDIDATES))]
    probe = build_compressed_attention_candidate_probe(
        baseline,
        base_variant,
        candidate_specs,
        training_batch_sizes=args.training_batch_sizes or DEFAULT_TRAINING_BATCH_SIZES,
        training_seq_lens=args.training_seq_lens or DEFAULT_TRAINING_SEQ_LENS,
        training_steps=args.training_steps or DEFAULT_TRAINING_STEPS,
        training_seeds=args.training_seeds or DEFAULT_TRAINING_SEEDS,
        benchmark_batch_sizes=args.benchmark_batch_sizes or DEFAULT_BENCHMARK_BATCH_SIZES,
        benchmark_seq_lens=args.benchmark_seq_lens or DEFAULT_BENCHMARK_SEQ_LENS,
        lr=args.lr,
        clip_grad_norm=args.clip_grad_norm,
        training_report_runs=args.training_report_runs,
        benchmark_warmup_runs=args.benchmark_warmup_runs,
        benchmark_measured_runs=args.benchmark_measured_runs,
        benchmark_report_runs=args.benchmark_report_runs,
    )
    markdown = render_compressed_attention_candidate_probe_markdown(probe)
    if args.artifact_json:
        path = Path(args.artifact_json)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(probe, indent=2) + "\n", encoding="utf-8")
    if args.artifact_md:
        path = Path(args.artifact_md)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(markdown, encoding="utf-8")
    if args.stdout or (not args.artifact_json and not args.artifact_md):
        print(markdown)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
