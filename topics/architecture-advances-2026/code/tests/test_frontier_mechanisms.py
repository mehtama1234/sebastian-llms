from __future__ import annotations

from arch_adv_2026.frontier_mechanisms import (
    build_frontier_mechanism_demo,
    causal_visible_compressed_positions,
    cache_ownership_report,
    distractor_selection_report,
    recurrent_lookup_report,
    shared_weight_depth_report,
)


def test_gqa_sanity_arithmetic_matches_16_gib_example() -> None:
    report = cache_ownership_report(
        policy="gqa",
        layers=32,
        sequence_length=131_072,
        kv_heads=8,
        head_dim=128,
        bytes_per_element=2,
    )
    assert report.bytes_per_token_per_owner == 4096
    assert report.stored_bytes == 16 * 1024**3


def test_shared_cache_preserves_storage_precision_but_changes_ownership() -> None:
    fresh = cache_ownership_report(
        policy="shared",
        layers=32,
        sequence_length=1024,
        kv_heads=8,
        head_dim=128,
        share_every=2,
        selected_tokens_per_layer=64,
        selection_mode="fresh",
    )
    reused = cache_ownership_report(
        policy="shared",
        layers=32,
        sequence_length=1024,
        kv_heads=8,
        head_dim=128,
        share_every=2,
        selected_tokens_per_layer=64,
        selection_mode="reused",
    )
    assert fresh.stored_bytes == reused.stored_bytes
    assert fresh.cache_read_bytes == reused.cache_read_bytes
    assert reused.index_work_units < fresh.index_work_units
    assert reused.selection_queries == 16


def test_recurrent_state_is_fixed_but_lookup_work_scales_in_events() -> None:
    short = recurrent_lookup_report(
        layers=4,
        sequence_length=128,
        state_width=32,
        lookup_period=16,
        selected_tokens_per_lookup=4,
    )
    long = recurrent_lookup_report(
        layers=4,
        sequence_length=256,
        state_width=32,
        lookup_period=16,
        selected_tokens_per_lookup=4,
    )
    assert short.fixed_recurrent_state_bytes == long.fixed_recurrent_state_bytes
    assert long.lookup_events == 2 * short.lookup_events
    assert long.lookup_bytes == 2 * short.lookup_bytes


def test_shared_weight_depth_counts_applications_not_new_weights() -> None:
    report = shared_weight_depth_report(stored_layers=24, looped_layers=12, loop_passes=3)
    assert report.layer_applications_per_token == 48
    assert report.stored_weight_depth == 24
    assert report.application_to_storage_ratio == 2.0


def test_distractor_probe_exposes_reused_selection_quality_tradeoff() -> None:
    report = distractor_selection_report(selected_budget=2)
    assert report.fresh_target_hits == 2
    assert report.reused_target_hits == 1
    assert report.selection_disagreement_count == 1
    assert report.reused_index_work_units < report.fresh_index_work_units


def test_demo_is_explicitly_a_toy_proxy() -> None:
    demo = build_frontier_mechanism_demo()
    assert demo["evidence_level"] == "executable_toy_proxy"
    assert demo["not_a_frontier_model_implementation"] is True


def test_cache_accounting_has_explicit_boundary_and_zero_selection_case() -> None:
    report = cache_ownership_report(
        policy="boundary",
        layers=1,
        sequence_length=1,
        kv_heads=1,
        head_dim=1,
        bytes_per_element=2,
        selected_tokens_per_layer=0,
    )
    assert report.stored_bytes == 4
    assert report.cache_read_bytes == 0
    assert report.index_work_units == 0


def test_recurrent_lookup_uses_ceil_boundary_for_partial_period() -> None:
    report = recurrent_lookup_report(
        layers=1,
        sequence_length=17,
        state_width=1,
        lookup_period=16,
        selected_tokens_per_lookup=1,
    )
    assert report.lookup_events == 2
    assert report.state_updates == 17


def test_distractor_probe_is_deterministic_across_repeated_calls() -> None:
    assert distractor_selection_report(selected_budget=2) == distractor_selection_report(selected_budget=2)


def test_compressed_visibility_is_causal_at_group_boundary() -> None:
    assert causal_visible_compressed_positions(position=0, compress_ratio=2, available_entries=8) == ()
    assert causal_visible_compressed_positions(position=1, compress_ratio=2, available_entries=8) == (0,)
    assert causal_visible_compressed_positions(position=3, compress_ratio=2, available_entries=8) == (0, 1)
    assert causal_visible_compressed_positions(position=99, compress_ratio=2, available_entries=2) == (0, 1)
