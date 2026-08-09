from pathlib import Path
import json
import pytest

from coding_agent_v1.eval_harness import (
    apply_eval_decision_artifact_prune_summary,
    apply_eval_artifact_prune_summary,
    auto_promote_eval_baseline,
    build_eval_baseline_audit_summary,
    build_eval_decision_artifact_prune_summary,
    build_eval_artifact_prune_summary,
    build_eval_baseline_summary_entries,
    build_eval_artifact_index,
    build_eval_comparison_task_class_summary,
    build_eval_failure_mode_summary,
    build_eval_history,
    build_eval_task_class_summary,
    compare_eval_baseline_to_reference,
    compare_eval_summaries,
    filter_eval_artifact_index,
    filter_eval_summaries_by_pack,
    load_eval_baseline_config,
    load_eval_summary,
    promote_eval_baseline,
    repair_eval_baseline_reference,
    resolve_eval_artifact_reference,
    run_eval_scenario_pack,
    run_eval_suite,
    save_eval_baseline_reference,
    summarize_eval_baseline_audit,
    summarize_eval_decision_artifact_prune_summary,
    summarize_eval_artifact_index,
    summarize_eval_artifact_prune_summary,
    summarize_eval_baseline_config,
    summarize_eval_comparison,
    summarize_eval_comparison_task_class_summary,
    summarize_eval_failure_mode_summary,
    summarize_eval_history,
    summarize_eval_promotion_decision,
    summarize_eval_summary,
    summarize_eval_task_class_summary,
    write_eval_comparison_summary,
    write_eval_promotion_decision,
)


def test_run_eval_suite_executes_fixed_scenarios(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    assert summary.total == 17
    assert summary.passed == 17
    assert summary.failed == 0
    assert summary.created_at
    assert {result.scenario_name for result in summary.results} == {
        "failing_test_repair",
        "natural_language_test_repair",
        "safe_multi_file_rename",
        "cli_flag_feature",
        "natural_language_cli_flag_feature",
        "module_aware_cli_feature",
        "single_test_workspace_fallback_cli_feature",
        "explicit_multi_test_cli_flag_feature",
        "config_option_feature",
        "natural_language_config_option_feature",
        "env_var_feature",
        "natural_language_env_var_feature",
        "inspect_repo_summary",
        "approval_required_boundary",
        "natural_language_diagnose_flow",
        "mixed_format_multi_test_diagnose_flow",
        "resume_session_flow",
    }
    status_by_name = {result.scenario_name: result.status for result in summary.results}
    assert status_by_name["approval_required_boundary"] == "failed"
    assert status_by_name["natural_language_diagnose_flow"] == "failed"
    assert status_by_name["mixed_format_multi_test_diagnose_flow"] == "failed"
    assert status_by_name["resume_session_flow"] == "completed"
    assert all(result.passed is True for result in summary.results)
    assert all(result.outcome_reason for result in summary.results)
    assert all(result.duration_seconds >= 0 for result in summary.results)


def test_run_eval_scenario_pack_executes_runnable_external_subset(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"

    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="catalog-v1",
    )

    assert summary.total == 20
    assert summary.passed == 20
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-core"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert all(result.failure_modes for result in summary.results)
    assert all(result.tags for result in summary.results)


def test_run_eval_scenario_pack_executes_external_smoke_pack(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"

    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="smoke-v1",
    )

    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-smoke"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert {result.severity for result in summary.results} == {"smoke"}


def test_run_eval_scenario_pack_executes_external_stress_pack(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"

    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="stress-v1",
    )

    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-stress"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert {result.severity for result in summary.results} == {"core"}


def test_build_eval_task_class_summary_groups_external_pack_results(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"
    summary = run_eval_scenario_pack(pack_path, tmp_path / "eval-sessions")

    task_summary = build_eval_task_class_summary(summary)
    text = summarize_eval_task_class_summary(task_summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].passed == 4
    assert by_class["feature"].passed == 4
    assert by_class["rename"].passed == 4
    assert by_class["diagnose"].passed == 4
    assert by_class["resume"].passed == 4
    assert "feature: passed=4/4 failed=0" in text


def test_build_eval_failure_mode_summary_groups_external_pack_results(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"
    summary = run_eval_scenario_pack(pack_path, tmp_path / "eval-sessions")

    failure_summary = build_eval_failure_mode_summary(summary)
    text = summarize_eval_failure_mode_summary(failure_summary)

    by_mode = {entry.failure_mode: entry for entry in failure_summary}
    assert by_mode["bad_validation_scope"].scenario_count >= 1
    assert by_mode["wrong_file_touched"].scenario_count >= 1
    assert by_mode["diagnose_edited_repo"].scenario_count >= 1
    assert "bad_validation_scope: passed=" in text


def test_build_eval_task_class_summary_groups_external_smoke_pack_results(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    summary = run_eval_scenario_pack(pack_path, tmp_path / "eval-sessions")

    task_summary = build_eval_task_class_summary(summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].passed == 1
    assert by_class["feature"].passed == 1
    assert by_class["rename"].passed == 1
    assert by_class["diagnose"].passed == 1
    assert by_class["resume"].passed == 1


def test_build_eval_failure_mode_summary_groups_external_stress_pack_results(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"
    summary = run_eval_scenario_pack(pack_path, tmp_path / "eval-sessions")

    failure_summary = build_eval_failure_mode_summary(summary)
    by_mode = {entry.failure_mode: entry for entry in failure_summary}

    assert by_mode["unsafe_action"].scenario_count >= 3
    assert by_mode["resume_memory_loss"].scenario_count >= 1
    assert by_mode["regression_introduced"].scenario_count >= 2


def test_summarize_eval_summary_lists_outcomes(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    text = summarize_eval_summary(summary)

    assert "total: 17" in text
    assert "passed: 17" in text
    assert "failed: 0" in text
    assert "failing_test_repair: passed" in text
    assert "natural_language_test_repair: passed" in text
    assert "safe_multi_file_rename: passed" in text
    assert "cli_flag_feature: passed" in text
    assert "natural_language_cli_flag_feature: passed" in text
    assert "module_aware_cli_feature: passed" in text
    assert "single_test_workspace_fallback_cli_feature: passed" in text
    assert "explicit_multi_test_cli_flag_feature: passed" in text
    assert "config_option_feature: passed" in text
    assert "natural_language_config_option_feature: passed" in text
    assert "env_var_feature: passed" in text
    assert "natural_language_env_var_feature: passed" in text
    assert "inspect_repo_summary: passed status=completed" in text
    assert "approval_required_boundary: passed status=failed" in text
    assert "natural_language_diagnose_flow: passed status=failed" in text
    assert "mixed_format_multi_test_diagnose_flow: passed status=failed" in text
    assert "resume_session_flow: passed status=completed" in text
    assert "duration_seconds=" in text
    assert "reason=" in text
    assert "created_at:" in text


def test_run_eval_suite_records_full_suite_fallback_reason_for_approval_boundary(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    approval_result = next(result for result in summary.results if result.scenario_name == "approval_required_boundary")

    assert approval_result.passed is True
    assert (
        approval_result.outcome_reason
        == "correctly stopped on approval boundary after selecting full-suite fallback validation"
    )


def test_run_eval_suite_records_explicit_inspect_reason(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    inspect_result = next(result for result in summary.results if result.scenario_name == "inspect_repo_summary")

    assert inspect_result.passed is True
    assert inspect_result.outcome_reason == "summarized repository via explicit inspect planning"


def test_run_eval_suite_records_single_test_fallback_reason_for_cli_feature(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    single_test_result = next(
        result for result in summary.results if result.scenario_name == "single_test_workspace_fallback_cli_feature"
    )

    assert single_test_result.passed is True
    assert (
        single_test_result.outcome_reason
        == "added requested CLI flag and recorded single-test workspace fallback validation"
    )


def test_run_eval_suite_records_module_aware_cli_reason(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    module_aware_result = next(
        result for result in summary.results if result.scenario_name == "module_aware_cli_feature"
    )

    assert module_aware_result.passed is True
    assert (
        module_aware_result.outcome_reason
        == "added requested CLI flag and recorded module-aware CLI validation"
    )


def test_run_eval_suite_writes_json_artifact_when_requested(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline",
    )

    assert summary.artifact_path is not None
    assert summary.artifact_path.exists()
    assert summary.artifact_path.parent == artifact_dir

    payload = json.loads(summary.artifact_path.read_text(encoding="utf-8"))
    assert payload["total"] == 17
    assert payload["passed"] == 17
    assert payload["failed"] == 0
    assert payload["created_at"] == summary.created_at
    assert payload["run_label"] == "baseline"
    assert payload["artifact_path"] == str(summary.artifact_path)
    assert len(payload["results"]) == 17
    assert all(result["outcome_reason"] for result in payload["results"])
    assert all(result["duration_seconds"] >= 0 for result in payload["results"])


def test_summarize_eval_summary_includes_artifact_path(tmp_path: Path) -> None:
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
    )

    text = summarize_eval_summary(summary)

    assert "artifact_path:" in text
    assert str(summary.artifact_path) in text


def test_load_eval_summary_round_trips_created_at_and_run_label(tmp_path: Path) -> None:
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="v1-baseline",
    )

    loaded = load_eval_summary(summary.artifact_path)

    assert loaded.created_at == summary.created_at
    assert loaded.run_label == "v1-baseline"
    assert loaded.scenario_pack_id == "built-in"


def test_compare_eval_summaries_reports_unchanged_when_artifacts_match(tmp_path: Path) -> None:
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=tmp_path / "baseline-artifacts",
    )
    candidate = load_eval_summary(baseline.artifact_path)

    comparison = compare_eval_summaries(baseline, candidate)

    assert comparison.regressions == 0
    assert comparison.improvements == 0
    assert comparison.unchanged == 17
    assert all(result.classification == "unchanged" for result in comparison.results)


def test_compare_eval_summaries_detects_regression_from_modified_artifact(tmp_path: Path) -> None:
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=tmp_path / "baseline-artifacts",
    )
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=tmp_path / "candidate-artifacts",
    )

    payload = json.loads(candidate.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 15
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for comparison test"
    candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_summaries(
        load_eval_summary(baseline.artifact_path),
        load_eval_summary(candidate.artifact_path),
    )
    text = summarize_eval_comparison(comparison)

    assert comparison.regressions == 1
    assert comparison.improvements == 0
    assert comparison.unchanged == 16
    assert any(result.classification == "regression" for result in comparison.results)
    assert "regressions: 1" in text
    assert "candidate_artifact_path:" in text


def test_build_eval_comparison_task_class_summary_groups_regressions_by_task_class(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"
    baseline = run_eval_scenario_pack(
        pack_path,
        tmp_path / "baseline-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="catalog-v1",
    )
    candidate = run_eval_scenario_pack(
        pack_path,
        tmp_path / "candidate-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="catalog-v2",
    )

    payload = json.loads(candidate.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = payload["passed"] - 1
    payload["failed"] = payload["failed"] + 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced fix regression for task-class summary test"
    candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_summaries(
        load_eval_summary(baseline.artifact_path),
        load_eval_summary(candidate.artifact_path),
    )
    task_summary = build_eval_comparison_task_class_summary(comparison)
    text = summarize_eval_comparison_task_class_summary(task_summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].regressions == 1
    assert by_class["feature"].regressions == 0
    assert "fix: regressions=1 improvements=0" in text


def test_write_eval_comparison_summary_persists_json_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v1",
    )
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="candidate-v2",
    )

    comparison = compare_eval_summaries(baseline, candidate)
    path = write_eval_comparison_summary(comparison, artifact_dir / "decision-artifacts")
    payload = json.loads(path.read_text(encoding="utf-8"))
    text = summarize_eval_comparison(comparison)

    assert path.exists()
    assert comparison.artifact_path == path
    assert payload["regressions"] == 0
    assert payload["created_at"] == comparison.created_at
    assert payload["artifact_path"] == str(path)
    assert "artifact_path:" in text


def test_build_eval_history_summarizes_runs_across_multiple_artifacts(tmp_path: Path) -> None:
    first = run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=tmp_path / "first-artifacts",
        run_label="v1",
    )
    second = run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=tmp_path / "second-artifacts",
        run_label="v2",
    )
    third = run_eval_suite(
        tmp_path / "third-sessions",
        artifact_dir=tmp_path / "third-artifacts",
        run_label="v3",
    )

    payload = json.loads(third.artifact_path.read_text(encoding="utf-8"))
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced history regression"
    payload["results"][0]["duration_seconds"] = 999.0
    third.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    history = build_eval_history(
        [
            load_eval_summary(first.artifact_path),
            load_eval_summary(second.artifact_path),
            load_eval_summary(third.artifact_path),
        ]
    )
    text = summarize_eval_history(history)

    assert len(history.artifact_paths) == 3
    assert history.pack_counts == {"built-in": 3}
    repair_trend = next(item for item in history.scenario_trends if item.scenario_name == "failing_test_repair")
    assert repair_trend.runs == 3
    assert repair_trend.pass_count == 2
    assert repair_trend.fail_count == 1
    assert repair_trend.latest_passed is False
    assert repair_trend.trend == "slower"
    assert repair_trend.history[-1].run_label == "v3"
    assert repair_trend.history[-1].scenario_pack_id == "built-in"
    assert repair_trend.history[-1].created_at
    assert "artifacts: 3" in text
    assert "scenario_packs:" in text
    assert "  built-in: 3" in text
    assert "failing_test_repair: runs=3 pass_count=2 fail_count=1 latest_passed=False" in text
    assert "latest_run_label=v3" in text
    assert "latest_scenario_pack_id=built-in" in text
    assert "latest_created_at=" in text


def test_build_eval_artifact_index_lists_runs_by_label_date_and_pass_rate(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first = run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )
    second = run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=artifact_dir,
        run_label="v2",
    )

    index = build_eval_artifact_index(artifact_dir)
    text = summarize_eval_artifact_index(index)

    assert len(index.entries) == 2
    assert index.pack_counts == {"built-in": 2}
    assert index.entries[0].created_at >= index.entries[1].created_at
    assert {entry.run_label for entry in index.entries} == {"v1", "v2"}
    assert {entry.scenario_pack_id for entry in index.entries} == {"built-in"}
    assert all(entry.passed == 17 for entry in index.entries)
    assert all(entry.total == 17 for entry in index.entries)
    assert all(entry.pass_rate == 100.0 for entry in index.entries)
    assert first.artifact_path.name in text
    assert second.artifact_path.name in text
    assert "scenario_packs:" in text
    assert "  built-in: 2" in text
    assert "run_label=v1" in text
    assert "run_label=v2" in text
    assert "scenario_pack_id=built-in" in text
    assert "pass_rate=100.0%" in text


def test_build_eval_artifact_index_tracks_multiple_pack_tiers(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    stress_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"

    run_eval_suite(
        tmp_path / "built-in-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v1",
    )
    run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    run_eval_scenario_pack(
        stress_pack,
        tmp_path / "stress-sessions",
        artifact_dir=artifact_dir,
        run_label="stress-v1",
    )

    index = build_eval_artifact_index(artifact_dir)
    text = summarize_eval_artifact_index(index)

    assert index.pack_counts == {
        "built-in": 1,
        "coding-agent-v1-smoke": 1,
        "coding-agent-v1-stress": 1,
    }
    assert "  built-in: 1" in text
    assert "  coding-agent-v1-smoke: 1" in text
    assert "  coding-agent-v1-stress: 1" in text


def test_filter_eval_artifact_index_by_pack_selector(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    stress_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"

    run_eval_suite(
        tmp_path / "built-in-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v1",
    )
    run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    run_eval_scenario_pack(
        stress_pack,
        tmp_path / "stress-sessions",
        artifact_dir=artifact_dir,
        run_label="stress-v1",
    )

    filtered = filter_eval_artifact_index(build_eval_artifact_index(artifact_dir), ["smoke", "stress"])

    assert len(filtered.entries) == 2
    assert filtered.pack_counts == {
        "coding-agent-v1-smoke": 1,
        "coding-agent-v1-stress": 1,
    }


def test_filter_eval_summaries_by_pack_selector(tmp_path: Path) -> None:
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    stress_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"

    summaries = [
        run_eval_suite(
            tmp_path / "built-in-sessions",
            run_label="built-in-v1",
        ),
        run_eval_scenario_pack(
            smoke_pack,
            tmp_path / "smoke-sessions",
            run_label="smoke-v1",
        ),
        run_eval_scenario_pack(
            stress_pack,
            tmp_path / "stress-sessions",
            run_label="stress-v1",
        ),
    ]

    filtered = filter_eval_summaries_by_pack(summaries, ["built-in", "stress"])

    assert [summary.scenario_pack_id for summary in filtered] == ["built-in", "coding-agent-v1-stress"]


def test_resolve_eval_artifact_reference_accepts_label_or_path(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )

    resolved_by_label = resolve_eval_artifact_reference("v1", artifact_dir)
    resolved_by_path = resolve_eval_artifact_reference(str(summary.artifact_path), artifact_dir)

    assert resolved_by_label == summary.artifact_path
    assert resolved_by_path == summary.artifact_path


def test_resolve_eval_artifact_reference_fails_for_missing_label(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )

    with pytest.raises(ValueError, match="No eval artifact found for label: missing"):
        resolve_eval_artifact_reference("missing", artifact_dir)


def test_resolve_eval_artifact_reference_fails_for_ambiguous_label(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=artifact_dir,
        run_label="shared",
    )
    run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=artifact_dir,
        run_label="shared",
    )

    with pytest.raises(ValueError, match="Multiple eval artifacts found for label: shared"):
        resolve_eval_artifact_reference("shared", artifact_dir)


def test_resolve_eval_artifact_reference_supports_latest_aliases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first = run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v1",
    )
    second = run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v2",
    )

    assert resolve_eval_artifact_reference("latest", artifact_dir) == second.artifact_path
    assert resolve_eval_artifact_reference("latest-pass", artifact_dir) == second.artifact_path
    assert resolve_eval_artifact_reference("latest:baseline", artifact_dir) == second.artifact_path
    assert resolve_eval_artifact_reference("latest-pass:baseline", artifact_dir) == second.artifact_path
    assert first.artifact_path != second.artifact_path


def test_resolve_eval_artifact_reference_supports_latest_aliases_by_pack_tier(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    built_in = run_eval_suite(
        tmp_path / "built-in-sessions",
        artifact_dir=artifact_dir,
        run_label="shared-v1",
    )
    smoke = run_eval_suite(
        tmp_path / "smoke-sessions",
        artifact_dir=artifact_dir,
        run_label="shared-v2",
    )
    stress = run_eval_suite(
        tmp_path / "stress-sessions",
        artifact_dir=artifact_dir,
        run_label="shared-v3",
    )

    for artifact_path, pack_id in (
        (built_in.artifact_path, "built-in"),
        (smoke.artifact_path, "coding-agent-v1-smoke"),
        (stress.artifact_path, "coding-agent-v1-stress"),
    ):
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        payload["scenario_pack_id"] = pack_id
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest:built-in", artifact_dir) == built_in.artifact_path
    assert resolve_eval_artifact_reference("latest:builtin", artifact_dir) == built_in.artifact_path
    assert resolve_eval_artifact_reference("latest:smoke", artifact_dir) == smoke.artifact_path
    assert resolve_eval_artifact_reference("latest:stress", artifact_dir) == stress.artifact_path
    assert resolve_eval_artifact_reference("latest:coding-agent-v1-stress", artifact_dir) == stress.artifact_path
    assert resolve_eval_artifact_reference("latest:shared", artifact_dir) == stress.artifact_path


def test_resolve_eval_artifact_reference_latest_pass_skips_failing_newer_run(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    passing = run_eval_suite(
        tmp_path / "passing-sessions",
        artifact_dir=artifact_dir,
        run_label="series-v1",
    )
    failing = run_eval_suite(
        tmp_path / "failing-sessions",
        artifact_dir=artifact_dir,
        run_label="series-v2",
    )

    payload = json.loads(failing.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 4
    payload["failed"] = 1
    failing.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest", artifact_dir) == failing.artifact_path
    assert resolve_eval_artifact_reference("latest-pass", artifact_dir) == passing.artifact_path
    assert resolve_eval_artifact_reference("latest-pass:series", artifact_dir) == passing.artifact_path


def test_resolve_eval_artifact_reference_latest_pass_supports_pack_tier_filter(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    passing = run_eval_suite(
        tmp_path / "passing-sessions",
        artifact_dir=artifact_dir,
        run_label="shared-v1",
    )
    failing = run_eval_suite(
        tmp_path / "failing-sessions",
        artifact_dir=artifact_dir,
        run_label="shared-v2",
    )

    for artifact_path, passed_count, failed_count in (
        (passing.artifact_path, 17, 0),
        (failing.artifact_path, 4, 1),
    ):
        payload = json.loads(artifact_path.read_text(encoding="utf-8"))
        payload["scenario_pack_id"] = "coding-agent-v1-stress"
        payload["passed"] = passed_count
        payload["failed"] = failed_count
        artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest:stress", artifact_dir) == failing.artifact_path
    assert resolve_eval_artifact_reference("latest-pass:stress", artifact_dir) == passing.artifact_path
    assert resolve_eval_artifact_reference("latest-pass:coding-agent-v1-stress", artifact_dir) == passing.artifact_path
    assert resolve_eval_artifact_reference("latest-pass:shared", artifact_dir) == passing.artifact_path


def test_resolve_eval_artifact_reference_latest_aliases_fail_cleanly(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="No eval artifacts are available."):
        resolve_eval_artifact_reference("latest", artifact_dir)

    run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v1",
    )

    with pytest.raises(ValueError, match="No eval artifact found for label prefix: missing"):
        resolve_eval_artifact_reference("latest:missing", artifact_dir)

    failing = run_eval_suite(
        tmp_path / "failing-sessions",
        artifact_dir=artifact_dir,
        run_label="broken-v1",
    )
    payload = json.loads(failing.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 4
    payload["failed"] = 1
    failing.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="No fully passing eval artifact found for label prefix: broken"):
        resolve_eval_artifact_reference("latest-pass:broken", artifact_dir)

    payload["scenario_pack_id"] = "coding-agent-v1-stress"
    failing.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="No fully passing eval artifact found for scenario pack: stress"):
        resolve_eval_artifact_reference("latest-pass:stress", artifact_dir)


def test_filter_eval_artifact_index_rejects_unknown_pack_selector(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )

    with pytest.raises(ValueError, match="Unknown scenario pack selector: unknown-pack"):
        filter_eval_artifact_index(build_eval_artifact_index(artifact_dir), ["unknown-pack"])


def test_save_and_load_eval_baseline_config_round_trip(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )

    config_path = save_eval_baseline_reference(artifact_dir, "main", summary.artifact_path)
    config = load_eval_baseline_config(artifact_dir)
    entries = build_eval_baseline_summary_entries(config)
    text = summarize_eval_baseline_config(config)

    assert config_path.exists()
    assert config.baselines["main"] == summary.artifact_path
    assert len(entries) == 1
    assert entries[0].name == "main"
    assert entries[0].status == "ok"
    assert entries[0].scenario_pack_id == "built-in"
    assert entries[0].run_label == "v1"
    assert "baselines: 1" in text
    assert f"main: {summary.artifact_path} status=ok" in text
    assert "scenario_pack_id=built-in" in text
    assert "run_label=v1" in text


def test_build_eval_baseline_summary_entries_marks_missing_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", summary.artifact_path)
    missing_path = artifact_dir / "missing-summary.json"
    save_eval_baseline_reference(artifact_dir, "missing", missing_path)
    config = load_eval_baseline_config(artifact_dir)

    entries = build_eval_baseline_summary_entries(config)
    text = summarize_eval_baseline_config(config)

    by_name = {entry.name: entry for entry in entries}
    assert by_name["main"].status == "ok"
    assert by_name["main"].scenario_pack_id == "built-in"
    assert by_name["missing"].status == "missing"
    assert by_name["missing"].scenario_pack_id is None
    assert f"missing: {missing_path} status=missing" in text


def test_build_eval_baseline_summary_entries_preserves_pack_id_for_missing_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    summary = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", summary.artifact_path)
    summary.artifact_path.unlink()
    config = load_eval_baseline_config(artifact_dir)

    entries = build_eval_baseline_summary_entries(config)
    by_name = {entry.name: entry for entry in entries}

    assert by_name["smoke-main"].status == "missing"
    assert by_name["smoke-main"].scenario_pack_id == "coding-agent-v1-smoke"


def test_build_eval_baseline_audit_summary_reports_current_stale_and_missing(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"

    built_in_old = run_eval_suite(
        tmp_path / "built-in-old-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v1",
    )
    built_in_new = run_eval_suite(
        tmp_path / "built-in-new-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v2",
    )
    smoke_old = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-old-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    smoke_new = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-new-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v2",
    )

    save_eval_baseline_reference(artifact_dir, "built-in-main", built_in_new.artifact_path)
    save_eval_baseline_reference(artifact_dir, "smoke-main", smoke_old.artifact_path)
    save_eval_baseline_reference(artifact_dir, "missing-main", smoke_old.artifact_path)
    smoke_old.artifact_path.unlink()

    config = load_eval_baseline_config(artifact_dir)
    summary = build_eval_baseline_audit_summary(config)
    text = summarize_eval_baseline_audit(summary)
    by_name = {entry.name: entry for entry in summary.entries}

    assert by_name["built-in-main"].status == "current"
    assert by_name["built-in-main"].recommended_reference == "latest-pass:built-in"
    assert by_name["built-in-main"].recommended_artifact_path == built_in_new.artifact_path

    assert by_name["smoke-main"].status == "missing"
    assert by_name["smoke-main"].scenario_pack_id == "coding-agent-v1-smoke"
    assert by_name["smoke-main"].recommended_artifact_path == smoke_new.artifact_path

    assert by_name["missing-main"].status == "missing"
    assert by_name["missing-main"].scenario_pack_id == "coding-agent-v1-smoke"
    assert by_name["missing-main"].recommended_reference == "latest-pass:coding-agent-v1-smoke"

    assert "built-in-main:" in text
    assert "status=current" in text
    assert "recommended_reference=latest-pass:built-in" in text
    assert "status=missing" in text


def test_build_eval_baseline_audit_summary_reports_stale_when_newer_same_pack_exists(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"

    smoke_old = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-old-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    smoke_new = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-new-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v2",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", smoke_old.artifact_path)

    summary = build_eval_baseline_audit_summary(load_eval_baseline_config(artifact_dir))
    entry = next(item for item in summary.entries if item.name == "smoke-main")

    assert entry.status == "stale"
    assert entry.recommended_artifact_path == smoke_new.artifact_path


def test_build_eval_artifact_prune_summary_protects_baselines_and_recent_per_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"

    built_in_old = run_eval_suite(
        tmp_path / "built-in-old-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v1",
    )
    built_in_new = run_eval_suite(
        tmp_path / "built-in-new-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v2",
    )
    smoke_old = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-old-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    smoke_new = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-new-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v2",
    )

    save_eval_baseline_reference(artifact_dir, "legacy", built_in_old.artifact_path)

    summary = build_eval_artifact_prune_summary(artifact_dir, keep_per_pack=1)
    text = summarize_eval_artifact_prune_summary(summary)
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[built_in_old.artifact_path].action == "protect"
    assert "named-baseline:legacy" in by_path[built_in_old.artifact_path].reasons
    assert by_path[built_in_new.artifact_path].action == "protect"
    assert by_path[smoke_new.artifact_path].action == "protect"
    assert by_path[smoke_old.artifact_path].action == "prune"
    assert summary.protected_count == 3
    assert summary.prunable_count == 1
    assert "action=prune" in text
    assert "action=protect" in text


def test_apply_eval_artifact_prune_summary_deletes_only_prunable_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first = run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v1",
    )
    second = run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v2",
    )

    summary = build_eval_artifact_prune_summary(artifact_dir, keep_per_pack=1)
    deleted_paths = apply_eval_artifact_prune_summary(summary)

    assert first.artifact_path in deleted_paths
    assert not first.artifact_path.exists()
    assert second.artifact_path.exists()


def test_resolve_eval_artifact_reference_supports_named_baseline_prefix(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="release-v1",
    )
    save_eval_baseline_reference(artifact_dir, "golden", summary.artifact_path)

    resolved = resolve_eval_artifact_reference("baseline:golden", artifact_dir)

    assert resolved == summary.artifact_path


def test_resolve_eval_artifact_reference_supports_named_baseline_prefix_with_pack_selector(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="release-v1",
    )
    save_eval_baseline_reference(artifact_dir, "golden", summary.artifact_path)

    resolved = resolve_eval_artifact_reference("baseline:golden:built-in", artifact_dir)

    assert resolved == summary.artifact_path


def test_resolve_eval_artifact_reference_fails_for_missing_named_baseline(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="No named baseline found: golden"):
        resolve_eval_artifact_reference("baseline:golden", artifact_dir)


def test_resolve_eval_artifact_reference_fails_for_named_baseline_pack_mismatch(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="release-v1",
    )
    save_eval_baseline_reference(artifact_dir, "golden", summary.artifact_path)

    with pytest.raises(ValueError, match="Named baseline golden does not match scenario pack selector: stress"):
        resolve_eval_artifact_reference("baseline:golden:stress", artifact_dir)


def test_resolve_eval_artifact_reference_supports_pack_selector_for_missing_named_baseline_target(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    summary = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "smoke-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", summary.artifact_path)
    summary.artifact_path.unlink()

    resolved = resolve_eval_artifact_reference("baseline:smoke-main:smoke", artifact_dir)

    assert resolved == summary.artifact_path


def test_promote_eval_baseline_defaults_to_latest_pass(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    passing = run_eval_suite(
        tmp_path / "passing-sessions",
        artifact_dir=artifact_dir,
        run_label="series-v1",
    )
    failing = run_eval_suite(
        tmp_path / "failing-sessions",
        artifact_dir=artifact_dir,
        run_label="series-v2",
    )
    payload = json.loads(failing.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 4
    payload["failed"] = 1
    failing.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    artifact_path, config_path = promote_eval_baseline(artifact_dir, "main")
    config = load_eval_baseline_config(artifact_dir)

    assert artifact_path == passing.artifact_path
    assert config_path.exists()
    assert config.baselines["main"] == passing.artifact_path


def test_promote_eval_baseline_accepts_explicit_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="release-v1",
    )

    artifact_path, _ = promote_eval_baseline(
        artifact_dir,
        "release",
        reference="release-v1",
    )
    resolved = resolve_eval_artifact_reference("baseline:release", artifact_dir)

    assert artifact_path == summary.artifact_path
    assert resolved == summary.artifact_path


def test_compare_eval_baseline_to_reference_defaults_to_latest_pass(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="candidate-v2",
    )

    comparison = compare_eval_baseline_to_reference(artifact_dir, "main")

    assert comparison.baseline_artifact_path == baseline.artifact_path
    assert comparison.candidate_artifact_path == candidate.artifact_path
    assert comparison.regressions == 0
    assert comparison.improvements == 0


def test_compare_eval_baseline_to_reference_defaults_to_latest_pass_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="baseline-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    same_pack_candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="built-in-v2",
    )
    other_pack_candidate = run_eval_suite(
        tmp_path / "other-pack-sessions",
        artifact_dir=artifact_dir,
        run_label="stress-v3",
    )

    payload = json.loads(other_pack_candidate.artifact_path.read_text(encoding="utf-8"))
    payload["scenario_pack_id"] = "coding-agent-v1-stress"
    other_pack_candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_baseline_to_reference(artifact_dir, "main")

    assert comparison.baseline_artifact_path == baseline.artifact_path
    assert comparison.candidate_artifact_path == same_pack_candidate.artifact_path
    assert comparison.baseline_scenario_pack_id == "built-in"
    assert comparison.candidate_scenario_pack_id == "built-in"


def test_compare_eval_baseline_to_reference_accepts_explicit_candidate_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="release-v1",
    )
    save_eval_baseline_reference(artifact_dir, "release", baseline.artifact_path)
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="candidate-v2",
    )

    payload = json.loads(candidate.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 4
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for baseline comparison test"
    candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_baseline_to_reference(
        artifact_dir,
        "release",
        candidate_reference="candidate-v2",
    )

    assert comparison.baseline_artifact_path == baseline.artifact_path
    assert comparison.candidate_artifact_path == candidate.artifact_path
    assert comparison.regressions == 1


def test_auto_promote_eval_baseline_promotes_when_comparison_is_clean(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v2",
    )

    decision = auto_promote_eval_baseline(
        artifact_dir,
        "main",
        candidate_reference="main-v2",
    )
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is True
    assert decision.comparison.regressions == 0
    assert decision.artifact_path == candidate.artifact_path
    assert decision.config_path is not None and decision.config_path.exists()
    assert resolved == candidate.artifact_path


def test_auto_promote_eval_baseline_blocks_on_regressions(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v2",
    )
    payload = json.loads(candidate.artifact_path.read_text(encoding="utf-8"))
    payload["passed"] = 4
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for auto-promotion test"
    candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    decision = auto_promote_eval_baseline(
        artifact_dir,
        "main",
        candidate_reference="main-v2",
    )
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is False
    assert decision.comparison.regressions == 1
    assert decision.artifact_path == candidate.artifact_path
    assert decision.config_path is None
    assert resolved == baseline.artifact_path


def test_auto_promote_eval_baseline_defaults_to_latest_pass_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    same_pack_candidate = run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v2",
    )
    other_pack_candidate = run_eval_suite(
        tmp_path / "other-pack-sessions",
        artifact_dir=artifact_dir,
        run_label="stress-v3",
    )

    payload = json.loads(other_pack_candidate.artifact_path.read_text(encoding="utf-8"))
    payload["scenario_pack_id"] = "coding-agent-v1-stress"
    other_pack_candidate.artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    decision = auto_promote_eval_baseline(artifact_dir, "main")
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is True
    assert decision.artifact_path == same_pack_candidate.artifact_path
    assert resolved == same_pack_candidate.artifact_path


def test_repair_eval_baseline_reference_defaults_to_latest_pass_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_pack = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"
    original = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "original-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v1",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", original.artifact_path)
    repaired = run_eval_scenario_pack(
        smoke_pack,
        tmp_path / "repaired-sessions",
        artifact_dir=artifact_dir,
        run_label="smoke-v2",
    )
    original.artifact_path.unlink()

    artifact_path, config_path, reference_used = repair_eval_baseline_reference(artifact_dir, "smoke-main")
    resolved = resolve_eval_artifact_reference("baseline:smoke-main", artifact_dir)

    assert reference_used == "latest-pass:coding-agent-v1-smoke"
    assert artifact_path == repaired.artifact_path
    assert config_path.exists()
    assert resolved == repaired.artifact_path


def test_repair_eval_baseline_reference_accepts_explicit_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first = run_eval_suite(
        tmp_path / "first-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", first.artifact_path)
    second = run_eval_suite(
        tmp_path / "second-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v2",
    )
    first.artifact_path.unlink()

    artifact_path, _, reference_used = repair_eval_baseline_reference(
        artifact_dir,
        "main",
        reference="main-v2",
    )

    assert reference_used == "main-v2"
    assert artifact_path == second.artifact_path


def test_write_eval_promotion_decision_persists_json_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline.artifact_path)
    run_eval_suite(
        tmp_path / "candidate-sessions",
        artifact_dir=artifact_dir,
        run_label="main-v2",
    )

    decision = auto_promote_eval_baseline(artifact_dir, "main", candidate_reference="main-v2")
    path = write_eval_promotion_decision(decision, artifact_dir / "decision-artifacts")
    payload = json.loads(path.read_text(encoding="utf-8"))
    text = summarize_eval_promotion_decision(decision)

    assert path.exists()
    assert decision.decision_artifact_path == path
    assert payload["promoted"] is True
    assert payload["decision_artifact_path"] == str(path)
    assert payload["comparison"]["regressions"] == 0
    assert "decision_artifact_path:" in text
