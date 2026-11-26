"""Small, auditable mechanism proxies for the frontier architecture study.

These functions model accounting boundaries only. They are not implementations
of DeepSeek, Qwen, Nemotron, or Inkling checkpoints.
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class CacheOwnershipReport:
    policy: str
    selection_mode: str
    layers: int
    owner_layers: int
    sequence_length: int
    kv_heads: int
    head_dim: int
    bytes_per_element: int
    bytes_per_token_per_owner: int
    stored_bytes: int
    cache_read_bytes: int
    index_work_units: int
    selection_queries: int


@dataclass(frozen=True, slots=True)
class RecurrentLookupReport:
    layers: int
    sequence_length: int
    state_width: int
    state_bytes_per_element: int
    lookup_period: int
    selected_tokens_per_lookup: int
    fixed_recurrent_state_bytes: int
    lookup_events: int
    lookup_bytes: int
    state_updates: int


@dataclass(frozen=True, slots=True)
class SharedWeightDepthReport:
    stored_layers: int
    looped_layers: int
    loop_passes: int
    layer_applications_per_token: int
    stored_weight_depth: int
    application_to_storage_ratio: float


@dataclass(frozen=True, slots=True)
class DistractorSelectionReport:
    sequence_length: int
    selected_budget: int
    query_count: int
    target_indices: tuple[int, ...]
    fresh_selected_indices: tuple[tuple[int, ...], ...]
    reused_selected_indices: tuple[tuple[int, ...], ...]
    fresh_target_hits: int
    reused_target_hits: int
    selection_disagreement_count: int
    fresh_index_work_units: int
    reused_index_work_units: int


def causal_visible_compressed_positions(
    *, position: int, compress_ratio: int, available_entries: int
) -> tuple[int, ...]:
    """Return completed compressed groups visible at one causal position.

    This mirrors only the visibility/accounting boundary in the released
    DeepSeek reference code: a compressed entry representing ``ratio`` tokens
    is not visible until the query has passed the group's final token. It is a
    pure toy helper, not a compressor, sparse-attention kernel, or checkpoint
    implementation.
    """

    for name, value in (
        ("position", position),
        ("compress_ratio", compress_ratio),
        ("available_entries", available_entries),
    ):
        if value < 0:
            raise ValueError(f"{name} cannot be negative")
    visible_count = min(available_entries, (position + 1) // compress_ratio)
    return tuple(range(visible_count))


def _positive(name: str, value: int) -> int:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def cache_ownership_report(
    *,
    policy: str,
    layers: int,
    sequence_length: int,
    kv_heads: int,
    head_dim: int,
    bytes_per_element: int = 2,
    share_every: int = 1,
    selected_tokens_per_layer: int = 0,
    selection_mode: str = "fresh",
) -> CacheOwnershipReport:
    """Count storage, reads, and index work for one cache-ownership policy.

    ``share_every`` changes cache ownership only. Fresh selection chooses a
    subset independently for every consumer layer; reused selection chooses it
    once per owner group. Cache reads remain per consumer layer in both modes.
    """

    for name, value in (
        ("layers", layers),
        ("sequence_length", sequence_length),
        ("kv_heads", kv_heads),
        ("head_dim", head_dim),
        ("bytes_per_element", bytes_per_element),
        ("share_every", share_every),
    ):
        _positive(name, value)
    if selection_mode not in {"fresh", "reused"}:
        raise ValueError("selection_mode must be 'fresh' or 'reused'")
    if selected_tokens_per_layer < 0:
        raise ValueError("selected_tokens_per_layer cannot be negative")

    owner_layers = math.ceil(layers / share_every)
    bytes_per_token = 2 * kv_heads * head_dim * bytes_per_element
    stored_bytes = owner_layers * sequence_length * bytes_per_token
    cache_read_bytes = layers * selected_tokens_per_layer * bytes_per_token
    selection_queries = layers if selection_mode == "fresh" else owner_layers
    index_work_units = selection_queries * selected_tokens_per_layer
    return CacheOwnershipReport(
        policy=policy,
        selection_mode=selection_mode,
        layers=layers,
        owner_layers=owner_layers,
        sequence_length=sequence_length,
        kv_heads=kv_heads,
        head_dim=head_dim,
        bytes_per_element=bytes_per_element,
        bytes_per_token_per_owner=bytes_per_token,
        stored_bytes=stored_bytes,
        cache_read_bytes=cache_read_bytes,
        index_work_units=index_work_units,
        selection_queries=selection_queries,
    )


def recurrent_lookup_report(
    *,
    layers: int,
    sequence_length: int,
    state_width: int,
    state_bytes_per_element: int = 2,
    lookup_period: int,
    selected_tokens_per_lookup: int,
) -> RecurrentLookupReport:
    """Contrast fixed recurrent state with periodic explicit history lookup."""

    for name, value in (
        ("layers", layers),
        ("sequence_length", sequence_length),
        ("state_width", state_width),
        ("state_bytes_per_element", state_bytes_per_element),
        ("lookup_period", lookup_period),
        ("selected_tokens_per_lookup", selected_tokens_per_lookup),
    ):
        _positive(name, value)
    return RecurrentLookupReport(
        layers=layers,
        sequence_length=sequence_length,
        state_width=state_width,
        state_bytes_per_element=state_bytes_per_element,
        lookup_period=lookup_period,
        selected_tokens_per_lookup=selected_tokens_per_lookup,
        fixed_recurrent_state_bytes=layers * state_width * state_bytes_per_element,
        lookup_events=math.ceil(sequence_length / lookup_period),
        lookup_bytes=math.ceil(sequence_length / lookup_period)
        * selected_tokens_per_lookup
        * state_width
        * state_bytes_per_element,
        state_updates=layers * sequence_length,
    )


def shared_weight_depth_report(*, stored_layers: int, looped_layers: int, loop_passes: int) -> SharedWeightDepthReport:
    """Count applications when a subset of stored layers is looped."""

    for name, value in (("stored_layers", stored_layers), ("looped_layers", looped_layers), ("loop_passes", loop_passes)):
        _positive(name, value)
    if looped_layers > stored_layers:
        raise ValueError("looped_layers cannot exceed stored_layers")
    applications = stored_layers - looped_layers + looped_layers * loop_passes
    return SharedWeightDepthReport(
        stored_layers=stored_layers,
        looped_layers=looped_layers,
        loop_passes=loop_passes,
        layer_applications_per_token=applications,
        stored_weight_depth=stored_layers,
        application_to_storage_ratio=applications / stored_layers,
    )


def distractor_selection_report(*, selected_budget: int = 2) -> DistractorSelectionReport:
    """Run a deterministic changing-query selection probe.

    The fixture has two distant targets. Query 0 favors the first target and
    query 1 favors the second. Reused selection intentionally keeps query 0's
    indices for query 1, exposing the quality trade-off hidden by storage-only
    accounting. Scores are synthetic and do not model a learned indexer.
    """

    _positive("selected_budget", selected_budget)
    # (index, score for query 0, score for query 1); the remaining rows are
    # distractors with stable but lower scores.
    rows = [
        (0, 0.12, 0.08),
        (1, 0.15, 0.11),
        (2, 0.99, 0.05),  # target for query 0
        (3, 0.13, 0.12),
        (4, 0.17, 0.14),
        (5, 0.10, 0.96),  # target for query 1
        (6, 0.16, 0.13),
        (7, 0.14, 0.10),
        (8, 0.11, 0.09),
        (9, 0.18, 0.16),
        (10, 0.13, 0.15),
        (11, 0.09, 0.07),
    ]
    queries = (0, 1)

    def select(query: int) -> tuple[int, ...]:
        return tuple(
            index
            for index, _score0, _score1 in sorted(
                rows,
                key=lambda row: (row[1 + query], -row[0]),
                reverse=True,
            )[:selected_budget]
        )

    fresh = tuple(select(query) for query in queries)
    reused = (fresh[0], fresh[0])
    targets = (2, 5)
    return DistractorSelectionReport(
        sequence_length=len(rows),
        selected_budget=selected_budget,
        query_count=len(queries),
        target_indices=targets,
        fresh_selected_indices=fresh,
        reused_selected_indices=reused,
        fresh_target_hits=sum(1 for query, target in zip(fresh, targets) if target in query),
        reused_target_hits=sum(1 for query, target in zip(reused, targets) if target in query),
        selection_disagreement_count=sum(1 for left, right in zip(fresh, reused) if left != right),
        fresh_index_work_units=len(rows) * len(queries),
        reused_index_work_units=len(rows),
    )


def build_frontier_mechanism_demo() -> dict[str, object]:
    """Return the first fixed comparison matrix used by the study."""

    cache = [
        asdict(
            cache_ownership_report(
                policy="gqa_baseline",
                layers=32,
                sequence_length=131_072,
                kv_heads=8,
                head_dim=128,
                selected_tokens_per_layer=2_048,
                selection_mode="fresh",
            )
        ),
        asdict(
            cache_ownership_report(
                policy="shared_kv_fresh_selection",
                layers=32,
                sequence_length=131_072,
                kv_heads=8,
                head_dim=128,
                share_every=2,
                selected_tokens_per_layer=2_048,
                selection_mode="fresh",
            )
        ),
        asdict(
            cache_ownership_report(
                policy="shared_kv_reused_selection",
                layers=32,
                sequence_length=131_072,
                kv_heads=8,
                head_dim=128,
                share_every=2,
                selected_tokens_per_layer=2_048,
                selection_mode="reused",
            )
        ),
    ]
    return {
        "evidence_level": "executable_toy_proxy",
        "not_a_frontier_model_implementation": True,
        "cache_ownership": cache,
        "recurrent_plus_lookup": asdict(
            recurrent_lookup_report(
                layers=12,
                sequence_length=131_072,
                state_width=128,
                lookup_period=256,
                selected_tokens_per_lookup=32,
            )
        ),
        "shared_weight_depth": asdict(
            shared_weight_depth_report(stored_layers=24, looped_layers=12, loop_passes=3)
        ),
        "distractor_selection": asdict(distractor_selection_report()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run auditable frontier architecture accounting proxies.")
    parser.add_argument("--artifact", type=str)
    args = parser.parse_args()
    result = build_frontier_mechanism_demo()
    if args.artifact:
        from pathlib import Path

        path = Path(args.artifact)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
