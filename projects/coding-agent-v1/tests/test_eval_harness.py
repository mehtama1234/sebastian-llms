from pathlib import Path
import json
import pytest

from coding_agent_v1.eval_harness import (
    auto_promote_eval_baseline,
    build_eval_artifact_index,
    build_eval_comparison_task_class_summary,
    build_eval_failure_mode_summary,
    build_eval_history,
    build_eval_task_class_summary,
    compare_eval_baseline_to_reference,
    compare_eval_summaries,
    load_eval_baseline_config,
    load_eval_summary,
    promote_eval_baseline,
    resolve_eval_artifact_reference,
    run_eval_scenario_pack,
    run_eval_suite,
    save_eval_baseline_reference,
    summarize_eval_artifact_index,
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

    assert summary.total == 16
    assert summary.passed == 16
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

    assert summary.total == 11
    assert summary.passed == 11
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-core"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert all(result.failure_modes for result in summary.results)
    assert all(result.tags for result in summary.results)


def test_build_eval_task_class_summary_groups_external_pack_results(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"
    summary = run_eval_scenario_pack(pack_path, tmp_path / "eval-sessions")

    task_summary = build_eval_task_class_summary(summary)
    text = summarize_eval_task_class_summary(task_summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].passed == 2
    assert by_class["feature"].passed == 4
    assert by_class["rename"].passed == 1
    assert by_class["diagnose"].passed == 3
    assert by_class["resume"].passed == 1
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


def test_summarize_eval_summary_lists_outcomes(tmp_path: Path) -> None:
    summary = run_eval_suite(tmp_path / "eval-sessions")

    text = summarize_eval_summary(summary)

    assert "total: 16" in text
    assert "passed: 16" in text
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
    assert payload["total"] == 16
    assert payload["passed"] == 16
    assert payload["failed"] == 0
    assert payload["created_at"] == summary.created_at
    assert payload["run_label"] == "baseline"
    assert payload["artifact_path"] == str(summary.artifact_path)
    assert len(payload["results"]) == 16
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


def test_compare_eval_summaries_reports_unchanged_when_artifacts_match(tmp_path: Path) -> None:
    baseline = run_eval_suite(
        tmp_path / "baseline-sessions",
        artifact_dir=tmp_path / "baseline-artifacts",
    )
    candidate = load_eval_summary(baseline.artifact_path)

    comparison = compare_eval_summaries(baseline, candidate)

    assert comparison.regressions == 0
    assert comparison.improvements == 0
    assert comparison.unchanged == 16
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
    assert comparison.unchanged == 15
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
    repair_trend = next(item for item in history.scenario_trends if item.scenario_name == "failing_test_repair")
    assert repair_trend.runs == 3
    assert repair_trend.pass_count == 2
    assert repair_trend.fail_count == 1
    assert repair_trend.latest_passed is False
    assert repair_trend.trend == "slower"
    assert repair_trend.history[-1].run_label == "v3"
    assert repair_trend.history[-1].created_at
    assert "artifacts: 3" in text
    assert "failing_test_repair: runs=3 pass_count=2 fail_count=1 latest_passed=False" in text
    assert "latest_run_label=v3" in text
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
    assert index.entries[0].created_at >= index.entries[1].created_at
    assert {entry.run_label for entry in index.entries} == {"v1", "v2"}
    assert all(entry.passed == 16 for entry in index.entries)
    assert all(entry.total == 16 for entry in index.entries)
    assert all(entry.pass_rate == 100.0 for entry in index.entries)
    assert first.artifact_path.name in text
    assert second.artifact_path.name in text
    assert "run_label=v1" in text
    assert "run_label=v2" in text
    assert "pass_rate=100.0%" in text


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


def test_save_and_load_eval_baseline_config_round_trip(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=artifact_dir,
        run_label="v1",
    )

    config_path = save_eval_baseline_reference(artifact_dir, "main", summary.artifact_path)
    config = load_eval_baseline_config(artifact_dir)
    text = summarize_eval_baseline_config(config)

    assert config_path.exists()
    assert config.baselines["main"] == summary.artifact_path
    assert "baselines: 1" in text
    assert f"main: {summary.artifact_path}" in text


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


def test_resolve_eval_artifact_reference_fails_for_missing_named_baseline(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="No named baseline found: golden"):
        resolve_eval_artifact_reference("baseline:golden", artifact_dir)


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
