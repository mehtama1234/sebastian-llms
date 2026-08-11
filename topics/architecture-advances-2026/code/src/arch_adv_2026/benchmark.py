from __future__ import annotations

import statistics
import time
from dataclasses import dataclass
from typing import Any

from .config import ModelConfig, compression_falls_back_to_baseline
from .numeric_runtime import describe_numeric_demo, prepare_numeric_demo, run_numeric_demo, run_prepared_numeric_demo
from .torch_model import check_torch, run_torch_demo


@dataclass(slots=True)
class BenchmarkResult:
    name: str
    variant: str
    batch_size: int
    seq_len: int
    warmup_runs: int
    measured_runs: int
    timings_ms: list[float]
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    owner_cache_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "variant": self.variant,
            "batch_size": self.batch_size,
            "seq_len": self.seq_len,
            "warmup_runs": self.warmup_runs,
            "measured_runs": self.measured_runs,
            "timings_ms": self.timings_ms,
            "mean_ms": self.mean_ms,
            "median_ms": self.median_ms,
            "min_ms": self.min_ms,
            "max_ms": self.max_ms,
            "owner_cache_count": self.owner_cache_count,
        }


def _numeric_timer_repeats(batch_size: int, seq_len: int) -> int:
    # Tiny CPU-side NumPy runs can be dominated by timer jitter and dispatcher overhead.
    # Repeat small/medium measured executions and normalize back to per-execution ms.
    # This keeps benchmark rows nearer the architecture signal instead of timer granularity noise,
    # especially on compressed-attention cells where one execution can be only a few milliseconds.
    work_units = max(1, batch_size * seq_len)
    return max(4, min(32, 2048 // work_units))


def benchmark_numeric_demo(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
) -> BenchmarkResult:
    if measured_runs <= 0:
        raise ValueError("measured_runs must be positive")
    if warmup_runs < 0:
        raise ValueError("warmup_runs cannot be negative")

    for idx in range(warmup_runs):
        prepared = prepare_numeric_demo(config, batch_size=batch_size, seq_len=seq_len, seed=seed + idx)
        run_prepared_numeric_demo(prepared)

    timings_ms: list[float] = []
    result = None
    for idx in range(measured_runs):
        prepared = prepare_numeric_demo(
            config,
            batch_size=batch_size,
            seq_len=seq_len,
            seed=seed + warmup_runs + idx,
        )
        repeats = _numeric_timer_repeats(batch_size, seq_len)
        start = time.perf_counter()
        for _ in range(repeats):
            result = run_prepared_numeric_demo(prepared)
        elapsed_ms = ((time.perf_counter() - start) * 1000.0) / repeats
        timings_ms.append(elapsed_ms)

    return BenchmarkResult(
        name=config.name,
        variant=config.variant.kind,
        batch_size=batch_size,
        seq_len=seq_len,
        warmup_runs=warmup_runs,
        measured_runs=measured_runs,
        timings_ms=timings_ms,
        mean_ms=statistics.fmean(timings_ms),
        median_ms=statistics.median(timings_ms),
        min_ms=min(timings_ms),
        max_ms=max(timings_ms),
        owner_cache_count=result.owner_cache_count,
    )


def compare_numeric_benchmarks(
    baseline: ModelConfig,
    variant: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
) -> dict[str, Any]:
    baseline_result = benchmark_numeric_demo(
        baseline,
        batch_size=batch_size,
        seq_len=seq_len,
        seed=seed,
        warmup_runs=warmup_runs,
        measured_runs=measured_runs,
    )
    baseline_demo = describe_numeric_demo(baseline, batch_size=batch_size, seq_len=seq_len, seed=seed)
    if compression_falls_back_to_baseline(variant, seq_len):
        variant_result = BenchmarkResult(
            name=variant.name,
            variant=variant.variant.kind,
            batch_size=baseline_result.batch_size,
            seq_len=baseline_result.seq_len,
            warmup_runs=baseline_result.warmup_runs,
            measured_runs=baseline_result.measured_runs,
            timings_ms=list(baseline_result.timings_ms),
            mean_ms=baseline_result.mean_ms,
            median_ms=baseline_result.median_ms,
            min_ms=baseline_result.min_ms,
            max_ms=baseline_result.max_ms,
            owner_cache_count=baseline_result.owner_cache_count,
        )
        variant_demo = {
            **baseline_demo,
            "name": variant.name,
            "variant": variant.variant.kind,
        }
    else:
        variant_result = benchmark_numeric_demo(
            variant,
            batch_size=batch_size,
            seq_len=seq_len,
            seed=seed,
            warmup_runs=warmup_runs,
            measured_runs=measured_runs,
        )
        variant_demo = describe_numeric_demo(variant, batch_size=batch_size, seq_len=seq_len, seed=seed)

    delta_ms = variant_result.mean_ms - baseline_result.mean_ms
    ratio = variant_result.mean_ms / baseline_result.mean_ms if baseline_result.mean_ms else None

    return {
        "baseline": baseline_result.to_dict(),
        "variant": variant_result.to_dict(),
        "comparison": {
            "mean_delta_ms": delta_ms,
            "mean_ratio_variant_over_baseline": ratio,
            "owner_cache_delta": variant_result.owner_cache_count - baseline_result.owner_cache_count,
        },
        "demo_context": {
            "baseline": baseline_demo,
            "variant": variant_demo,
        },
        "notes": [
            "These timings come from tiny NumPy random-weight runs on the local CPU.",
            "They are useful for harness regression and rough directionality, not for hardware-optimized performance claims.",
        ],
    }


def benchmark_torch_demo(
    config: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
) -> BenchmarkResult:
    availability = check_torch()
    if not availability.available:
        raise RuntimeError(availability.reason or "torch is not available")
    if measured_runs <= 0:
        raise ValueError("measured_runs must be positive")
    if warmup_runs < 0:
        raise ValueError("warmup_runs cannot be negative")

    for idx in range(warmup_runs):
        run_torch_demo(config, batch_size=batch_size, seq_len=seq_len, seed=seed + idx)

    timings_ms: list[float] = []
    for idx in range(measured_runs):
        start = time.perf_counter()
        result = run_torch_demo(config, batch_size=batch_size, seq_len=seq_len, seed=seed + warmup_runs + idx)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        timings_ms.append(elapsed_ms)

    return BenchmarkResult(
        name=config.name,
        variant=config.variant.kind,
        batch_size=batch_size,
        seq_len=seq_len,
        warmup_runs=warmup_runs,
        measured_runs=measured_runs,
        timings_ms=timings_ms,
        mean_ms=statistics.fmean(timings_ms),
        median_ms=statistics.median(timings_ms),
        min_ms=min(timings_ms),
        max_ms=max(timings_ms),
        owner_cache_count=result["torch_run"]["owner_cache_count"],
    )


def compare_torch_benchmarks(
    baseline: ModelConfig,
    variant: ModelConfig,
    *,
    batch_size: int = 1,
    seq_len: int = 8,
    seed: int = 0,
    warmup_runs: int = 1,
    measured_runs: int = 5,
) -> dict[str, Any]:
    baseline_result = benchmark_torch_demo(
        baseline,
        batch_size=batch_size,
        seq_len=seq_len,
        seed=seed,
        warmup_runs=warmup_runs,
        measured_runs=measured_runs,
    )
    baseline_demo = run_torch_demo(baseline, batch_size=batch_size, seq_len=seq_len, seed=seed)
    if compression_falls_back_to_baseline(variant, seq_len):
        variant_result = BenchmarkResult(
            name=variant.name,
            variant=variant.variant.kind,
            batch_size=baseline_result.batch_size,
            seq_len=baseline_result.seq_len,
            warmup_runs=baseline_result.warmup_runs,
            measured_runs=baseline_result.measured_runs,
            timings_ms=list(baseline_result.timings_ms),
            mean_ms=baseline_result.mean_ms,
            median_ms=baseline_result.median_ms,
            min_ms=baseline_result.min_ms,
            max_ms=baseline_result.max_ms,
            owner_cache_count=baseline_result.owner_cache_count,
        )
        variant_demo = {
            **baseline_demo,
            "name": variant.name,
            "variant": variant.variant.kind,
        }
    else:
        variant_result = benchmark_torch_demo(
            variant,
            batch_size=batch_size,
            seq_len=seq_len,
            seed=seed,
            warmup_runs=warmup_runs,
            measured_runs=measured_runs,
        )
        variant_demo = run_torch_demo(variant, batch_size=batch_size, seq_len=seq_len, seed=seed)

    delta_ms = variant_result.mean_ms - baseline_result.mean_ms
    ratio = variant_result.mean_ms / baseline_result.mean_ms if baseline_result.mean_ms else None

    return {
        "baseline": baseline_result.to_dict(),
        "variant": variant_result.to_dict(),
        "comparison": {
            "mean_delta_ms": delta_ms,
            "mean_ratio_variant_over_baseline": ratio,
            "owner_cache_delta": variant_result.owner_cache_count - baseline_result.owner_cache_count,
        },
        "demo_context": {
            "baseline": baseline_demo,
            "variant": variant_demo,
        },
        "notes": [
            "These timings come from tiny Torch random-weight runs on the local machine.",
            "They are useful for harness regression and rough directionality, not for hardware-optimized performance claims.",
        ],
    }
