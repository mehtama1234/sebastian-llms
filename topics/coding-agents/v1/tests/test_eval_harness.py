from pathlib import Path
import json
import sys
import pytest

from coding_agent_v1.eval_harness import (
    EvalDecisionArtifactIndex,
    EvalDecisionArtifactIndexEntry,
    EvalResult,
    EvalScenario,
    EvalSummary,
    EvalExpectationCheckComparisonEntry,
    EvalTraceAggregateComparisonEntry,
    EvalTraceAggregateEntry,
    EvalTraceTransitionHeatmapComparisonRow,
    EvalTraceTransitionComparisonEntry,
    EvalTraceTransitionHeatmapRow,
    EvalTraceTransitionEntry,
    EvalTraceSummaryEntry,
    _build_trace_steps,
    _build_trace_transition_comparison_from_aggregate,
    _parse_failure_transition_label,
    _trace_failure_labels,
    apply_eval_decision_artifact_prune_summary,
    apply_eval_artifact_prune_summary,
    auto_promote_eval_baseline,
    build_eval_trace_summary,
    build_eval_trace_transition_heatmap,
    build_eval_trace_transition_comparison,
    build_eval_trace_transition_comparison_heatmap,
    build_eval_trace_transition_summary,
    build_eval_baseline_audit_summary,
    build_eval_decision_artifact_index,
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
    filter_eval_decision_artifact_index,
    filter_eval_summaries_by_pack,
    load_eval_baseline_config,
    load_eval_comparison_summary,
    load_eval_promotion_decision,
    load_eval_summary,
    promote_eval_baseline,
    repair_eval_baseline_reference,
    resolve_decision_artifact_reference,
    resolve_eval_artifact_reference,
    run_eval_scenario_pack,
    run_eval_suite,
    save_eval_baseline_reference,
    summarize_eval_baseline_audit,
    summarize_eval_decision_artifact_index,
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
    summarize_eval_trace_summary,
    write_eval_summary,
    write_eval_comparison_summary,
    write_eval_promotion_decision,
    EvalDecisionArtifactPruneEntry,
)
from coding_agent_v1.models import SessionEvent, SessionRecord, SessionStatus, WorkingMemory
from coding_agent_v1.trace_schema import validate_trace_payload


def _write_eval_artifact(
    artifact_dir: Path,
    filename: str,
    *,
    created_at: str,
    run_label: str,
    scenario_pack_id: str = "built-in",
    passed: tuple[bool, ...] = (True, True),
    scenario_names: tuple[str, ...] | None = None,
) -> Path:
    results = []
    for index, passed_value in enumerate(passed, start=1):
        scenario_name = (
            scenario_names[index - 1]
            if scenario_names is not None
            else f"scenario-{index}"
        )
        results.append(
            {
                "scenario_name": scenario_name,
                "passed": passed_value,
                "session_id": f"session-{index}",
                "status": "completed" if passed_value else "failed",
                "final_report": "ok" if passed_value else "broken",
                "outcome_reason": "ok" if passed_value else "broken",
                "duration_seconds": float(index),
                "task_class": "fix",
                "severity": "core",
                "failure_modes": [],
                "tags": [],
                "behavior_ids": ["validation_selection"],
                "repair_record_ids": ["repair-1"] if not passed_value else [],
                "has_bpe_memory": True,
                "used_compact_context": False,
            }
        )
    artifact_path = artifact_dir / filename
    payload = {
        "total": len(results),
        "passed": sum(1 for value in passed if value),
        "failed": sum(1 for value in passed if not value),
        "results": results,
        "created_at": created_at,
        "run_label": run_label,
        "artifact_path": str(artifact_path),
        "scenario_pack_id": scenario_pack_id,
    }
    artifact_dir.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return artifact_path


@pytest.fixture(scope="session")
def built_in_eval_summary(tmp_path_factory) -> object:
    root = tmp_path_factory.mktemp("built-in-eval-summary")
    return run_eval_suite(root / "eval-sessions", artifact_dir=root / "eval-artifacts", run_label="shared-built-in")


@pytest.fixture(scope="session")
def core_eval_summary(tmp_path_factory) -> object:
    root = tmp_path_factory.mktemp("core-eval-summary")
    pack_path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"
    return run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="shared-core",
    )


@pytest.fixture(scope="session")
def smoke_eval_summary(tmp_path_factory) -> object:
    root = tmp_path_factory.mktemp("smoke-eval-summary")
    pack_path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "smoke-v1.json"
    return run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="shared-smoke",
    )


@pytest.fixture(scope="session")
def stress_eval_summary(tmp_path_factory) -> object:
    root = tmp_path_factory.mktemp("stress-eval-summary")
    pack_path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "stress-v1.json"
    return run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="shared-stress",
    )


def test_run_eval_suite_executes_fixed_scenarios(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    assert summary.total == 18
    assert summary.passed == 18
    assert summary.failed == 0
    assert summary.created_at
    assert {result.scenario_name for result in summary.results} == {
        "failing_test_repair",
        "natural_language_test_repair",
        "safe_multi_file_rename",
        "module_aware_rename_validation",
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


def test_run_eval_scenario_pack_executes_runnable_external_subset(core_eval_summary) -> None:
    summary = core_eval_summary

    assert summary.total == 20
    assert summary.passed == 20
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-core"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert all(result.failure_modes for result in summary.results)
    assert all(result.tags for result in summary.results)
    assert all(result.has_bpe_memory for result in summary.results)
    resume_results = [result for result in summary.results if result.task_class == "resume"]
    assert all(result.used_compact_context for result in resume_results)


def test_run_eval_scenario_pack_executes_external_smoke_pack(smoke_eval_summary) -> None:
    summary = smoke_eval_summary

    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-smoke"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert {result.severity for result in summary.results} == {"smoke"}
    assert all(result.planner_strategy == "deterministic_heuristic" for result in summary.results)
    assert all(result.trace_artifact_path for result in summary.results)


def test_run_eval_scenario_pack_writes_trace_artifacts_for_richer_pack(tmp_path: Path) -> None:
    root = tmp_path / "agent-evals-smoke"
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )

    summary = run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="agent-evals-smoke",
    )

    assert summary.total == 5
    assert summary.passed == 5
    assert summary.scenario_pack_id == "coding-agent-v1-agent-evals-smoke"
    assert all(result.trace_artifact_path for result in summary.results)
    trace_paths = [Path(result.trace_artifact_path) for result in summary.results]
    assert all(path.exists() for path in trace_paths)

    payload = json.loads(trace_paths[0].read_text(encoding="utf-8"))
    assert payload["agent_id"] == "coding-agent-v1"
    assert payload["tools_available"]
    assert payload["steps"]
    assert payload["outcome"]["task_completed"] is True
    assert payload["labels"]["first_failure_state"] is None
    assert payload["expected"]["expected_tool_sequence"]
    assert payload["expectation_checks"]["actual_tool_sequence"]
    assert payload["expectation_checks"]["tool_sequence_ok"] is True
    assert payload["expectation_checks"]["escalation_ok"] is True


def test_load_eval_summary_round_trips_trace_artifact_paths(tmp_path: Path) -> None:
    root = tmp_path / "agent-evals-load"
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )

    summary = run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="agent-evals-load",
    )

    assert summary.artifact_path is not None
    loaded = load_eval_summary(summary.artifact_path)

    assert len(loaded.results) == 5
    assert all(result.trace_artifact_path for result in loaded.results)
    assert all(result.actual_tool_sequence for result in loaded.results)
    assert all(result.tool_sequence_ok is True for result in loaded.results)


def test_run_eval_scenario_pack_executes_external_stress_pack(stress_eval_summary) -> None:
    summary = stress_eval_summary

    assert summary.total == 5
    assert summary.passed == 5
    assert summary.failed == 0
    assert summary.scenario_pack_id == "coding-agent-v1-stress"
    assert {result.task_class for result in summary.results} == {"diagnose", "feature", "fix", "rename", "resume"}
    assert {result.severity for result in summary.results} == {"core"}


def test_build_eval_task_class_summary_groups_external_pack_results(core_eval_summary) -> None:
    summary = core_eval_summary

    task_summary = build_eval_task_class_summary(summary)
    text = summarize_eval_task_class_summary(task_summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].passed == 4
    assert by_class["feature"].passed == 4
    assert by_class["rename"].passed == 4
    assert by_class["diagnose"].passed == 4
    assert by_class["resume"].passed == 4
    assert "feature: passed=4/4 failed=0" in text


def test_build_eval_failure_mode_summary_groups_external_pack_results(core_eval_summary) -> None:
    summary = core_eval_summary

    failure_summary = build_eval_failure_mode_summary(summary)
    text = summarize_eval_failure_mode_summary(failure_summary)

    by_mode = {entry.failure_mode: entry for entry in failure_summary}
    assert by_mode["bad_validation_scope"].scenario_count >= 1
    assert by_mode["wrong_file_touched"].scenario_count >= 1
    assert by_mode["diagnose_edited_repo"].scenario_count >= 1
    assert "bad_validation_scope: passed=" in text


def test_build_eval_task_class_summary_groups_external_smoke_pack_results(smoke_eval_summary) -> None:
    summary = smoke_eval_summary

    task_summary = build_eval_task_class_summary(summary)

    by_class = {entry.task_class: entry for entry in task_summary}
    assert by_class["fix"].passed == 1
    assert by_class["feature"].passed == 1
    assert by_class["rename"].passed == 1
    assert by_class["diagnose"].passed == 1
    assert by_class["resume"].passed == 1


def test_build_eval_failure_mode_summary_groups_external_stress_pack_results(stress_eval_summary) -> None:
    summary = stress_eval_summary

    failure_summary = build_eval_failure_mode_summary(summary)
    by_mode = {entry.failure_mode: entry for entry in failure_summary}

    assert by_mode["unsafe_action"].scenario_count >= 3
    assert by_mode["resume_memory_loss"].scenario_count >= 1
    assert by_mode["regression_introduced"].scenario_count >= 2


def test_build_eval_trace_summary_reports_expectation_check_counts(tmp_path: Path) -> None:
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )
    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="agent-evals-trace-checks",
    )

    trace_summary = build_eval_trace_summary(summary)
    text = summarize_eval_trace_summary(trace_summary)

    assert len(trace_summary) == 5
    assert all(entry.tool_sequence_ok is True for entry in trace_summary)
    assert all(entry.escalation_ok is True for entry in trace_summary)
    assert "tool_sequence_match: 5/5" in text
    assert "escalation_match: 5/5" in text


def test_build_eval_trace_summary_reports_first_failure_transitions_from_trace_artifact() -> None:
    trace_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "datasets"
        / "sample-unsafe-write-trace.json"
    )
    summary = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="unsafe-write-sample",
                passed=False,
                session_id="s1",
                status="completed",
                final_report="unsafe write happened",
                outcome_reason="unsafe write",
                duration_seconds=1.0,
                task_class="diagnose",
                trace_artifact_path=str(trace_path),
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
    )

    trace_summary = build_eval_trace_summary(summary)
    text = summarize_eval_trace_summary(trace_summary)

    assert trace_summary[0].first_failure_state == "handle_tool_output"
    assert trace_summary[0].first_failure_from_state == "execute_tool"
    assert "failure_transitions:" in text
    assert "failure_transition_pairs:" in text
    assert "failure_transition_heatmap:" in text
    assert "from=execute_tool total=1 handle_tool_output=1" in text
    assert "from=execute_tool to=handle_tool_output count=1 scenarios=unsafe-write-sample" in text
    assert "execute_tool->handle_tool_output: count=1 scenarios=unsafe-write-sample" in text


def test_summarize_eval_summary_lists_outcomes(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    text = summarize_eval_summary(summary)

    assert "total: 18" in text
    assert "passed: 18" in text
    assert "failed: 0" in text
    assert "failing_test_repair: passed" in text
    assert "natural_language_test_repair: passed" in text
    assert "safe_multi_file_rename: passed" in text
    assert "module_aware_rename_validation: passed" in text
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
    assert "bpe_memory=true" in text
    assert "compact_context=true" in text
    assert "compaction_trigger=" in text
    assert "created_at:" in text


def test_summarize_eval_summary_lists_expectation_checks_for_richer_pack(tmp_path: Path) -> None:
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )
    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        run_label="agent-evals-summary",
    )

    text = summarize_eval_summary(summary)

    assert "expectation_checks=tool_sequence=ok escalation=ok" in text
    assert "actual_tool_sequence=" in text


def test_run_eval_suite_records_full_suite_fallback_reason_for_approval_boundary(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    approval_result = next(result for result in summary.results if result.scenario_name == "approval_required_boundary")

    assert approval_result.passed is True
    assert approval_result.has_bpe_memory is True
    assert approval_result.repair_record_ids
    assert (
        approval_result.outcome_reason
        == "correctly stopped on approval boundary after selecting full-suite fallback validation"
    )


def test_run_eval_suite_records_explicit_inspect_reason(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    inspect_result = next(result for result in summary.results if result.scenario_name == "inspect_repo_summary")

    assert inspect_result.passed is True
    assert inspect_result.outcome_reason == "summarized repository via explicit inspect planning"


def test_run_eval_suite_records_module_aware_rename_reason(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    rename_result = next(result for result in summary.results if result.scenario_name == "module_aware_rename_validation")

    assert rename_result.passed is True
    assert "validation_selection" in rename_result.behavior_ids
    assert rename_result.outcome_reason == "renamed source symbol and recorded module-aware rename validation"


def test_run_eval_suite_records_single_test_fallback_reason_for_cli_feature(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

    single_test_result = next(
        result for result in summary.results if result.scenario_name == "single_test_workspace_fallback_cli_feature"
    )

    assert single_test_result.passed is True
    assert (
        single_test_result.outcome_reason
        == "added requested CLI flag and recorded single-test workspace fallback validation"
    )


def test_run_eval_suite_records_module_aware_cli_reason(built_in_eval_summary) -> None:
    summary = built_in_eval_summary

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
    assert payload["total"] == 18
    assert payload["passed"] == 18
    assert payload["failed"] == 0
    assert payload["created_at"] == summary.created_at
    assert payload["run_label"] == "baseline"
    assert payload["artifact_path"] == str(summary.artifact_path)
    assert len(payload["results"]) == 18
    assert all(result["outcome_reason"] for result in payload["results"])
    assert all(result["duration_seconds"] >= 0 for result in payload["results"])
    assert all("has_bpe_memory" in result for result in payload["results"])
    approval_payload = next(result for result in payload["results"] if result["scenario_name"] == "approval_required_boundary")
    assert approval_payload["repair_record_ids"]


def test_summarize_eval_summary_includes_artifact_path(tmp_path: Path) -> None:
    summary = run_eval_suite(
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
    )

    text = summarize_eval_summary(summary)

    assert "artifact_path:" in text
    assert str(summary.artifact_path) in text


def test_load_eval_summary_round_trips_created_at_and_run_label(tmp_path: Path) -> None:
    artifact_path = _write_eval_artifact(
        tmp_path / "eval-artifacts",
        "eval-summary-v1-baseline.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1-baseline",
    )

    loaded = load_eval_summary(artifact_path)

    assert loaded.created_at == "2026-08-09T00:00:00+00:00"
    assert loaded.run_label == "v1-baseline"
    assert loaded.results[0].behavior_ids == ("validation_selection",)
    assert loaded.results[0].has_bpe_memory is True
    assert loaded.results[0].used_compact_context is False
    assert loaded.results[0].planner_strategy == "deterministic_heuristic"
    assert loaded.results[0].compaction_trigger == ""


def test_run_eval_scenario_pack_rejects_unconfigured_model_guided_planner_strategy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", raising=False)
    pack_path = tmp_path / "model-guided-gate.json"
    pack_path.write_text(
        json.dumps(
            {
                "pack_id": "model-guided-gate",
                "title": "Model Guided Gate",
                "description": "Verifies unconfigured model planner strategy remains gated.",
                "scenarios": [
                    {
                        "scenario_id": "model-guided-001",
                        "title": "Unavailable model planner",
                        "task_class": "fix",
                        "severity": "smoke",
                        "request": "fix the failing test",
                        "expected_outcome": "The model planner gate rejects this scenario.",
                        "failure_modes": ["planner_gate_missing"],
                        "tags": ["planner", "gate"],
                        "setup_kind": "repair",
                        "planner_strategy": "model_guided",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires CODING_AGENT_V1_MODEL_PLANNER_COMMAND"):
        run_eval_scenario_pack(
            pack_path,
            tmp_path / "eval-sessions",
            artifact_dir=tmp_path / "eval-artifacts",
        )


def test_run_eval_scenario_pack_accepts_configured_model_guided_planner_strategy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    planner_script = tmp_path / "planner.py"
    planner_script.write_text(
        "import json, sys\n"
        "payload = json.loads(sys.stdin.read())\n"
        "assert payload['contract']['required_fields'] == ['task_flow', 'reasons']\n"
        "print(json.dumps({'task_flow': 'fix', 'reasons': ['model selected repair flow']}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", f"{sys.executable} {planner_script}")
    pack_path = tmp_path / "model-guided-gate.json"
    pack_path.write_text(
        json.dumps(
            {
                "pack_id": "model-guided-gate",
                "title": "Model Guided Gate",
                "description": "Verifies configured model planner strategy can run through evals.",
                "scenarios": [
                    {
                        "scenario_id": "model-guided-001",
                        "title": "Configured model planner",
                        "task_class": "fix",
                        "severity": "smoke",
                        "request": "fix the failing test",
                        "expected_outcome": "The model planner selects a repair flow.",
                        "failure_modes": ["planner_gate_missing"],
                        "tags": ["planner", "gate"],
                        "setup_kind": "repair",
                        "planner_strategy": "model_guided",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
    )

    assert summary.passed == 1
    assert summary.failed == 0
    assert summary.results[0].planner_strategy == "model_guided"


def test_run_eval_scenario_pack_accepts_planner_strategy_override(
    monkeypatch,
    tmp_path: Path,
) -> None:
    planner_script = tmp_path / "planner.py"
    planner_script.write_text(
        "import json, sys\n"
        "json.loads(sys.stdin.read())\n"
        "print(json.dumps({'task_flow': 'fix', 'reasons': ['override model kept repair flow']}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", f"{sys.executable} {planner_script}")
    pack_path = tmp_path / "deterministic-pack.json"
    pack_path.write_text(
        json.dumps(
            {
                "pack_id": "deterministic-pack",
                "title": "Deterministic Pack",
                "description": "Scenario declares deterministic planner but run override uses model_guided.",
                "scenarios": [
                    {
                        "scenario_id": "override-001",
                        "title": "Override planner",
                        "task_class": "fix",
                        "severity": "smoke",
                        "request": "fix the failing test",
                        "expected_outcome": "The planner override selects the model-guided strategy.",
                        "failure_modes": ["planner_gate_missing"],
                        "tags": ["planner", "override"],
                        "setup_kind": "repair",
                        "planner_strategy": "deterministic_heuristic",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    summary = run_eval_scenario_pack(
        pack_path,
        tmp_path / "eval-sessions",
        artifact_dir=tmp_path / "eval-artifacts",
        planner_strategy_override="model_guided",
    )

    assert summary.passed == 1
    assert summary.results[0].planner_strategy == "model_guided"


def test_run_eval_scenario_pack_trace_includes_harness_state(tmp_path: Path) -> None:
    root = tmp_path / "agent-evals-smoke"
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )

    summary = run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="agent-evals-smoke",
    )

    trace_path = Path(summary.results[0].trace_artifact_path)
    payload = json.loads(trace_path.read_text(encoding="utf-8"))

    assert "harness_state" in payload
    assert payload["harness_state"]["planner_strategy"] == "deterministic_heuristic"
    assert "has_bpe_memory" in payload["harness_state"]
    assert "belief" in payload["harness_state"]
    assert "progress" in payload["harness_state"]
    assert "experience" in payload["harness_state"]
    assert "used_compact_context" in payload["harness_state"]
    assert "compaction_trigger" in payload["harness_state"]
    assert summary.results[0].compaction_trigger
    assert payload["harness_state"]["compaction_trigger"] == summary.results[0].compaction_trigger
    assert summary.scenario_pack_id == "coding-agent-v1-agent-evals-smoke"
    validate_trace_payload(payload)


def test_validate_trace_payload_rejects_missing_required_field() -> None:
    payload = {
        "trace_id": "missing-agent",
        "scenario_id": "fix-001",
        "request": "fix the failing test",
        "task_class": "fix",
        "workspace_kind": "toy_repo",
        "tools_available": [],
        "steps": [],
        "outcome": {
            "status": "completed",
            "task_completed": True,
            "safe": True,
            "summary": "ok",
        },
        "labels": {
            "first_failure_state": None,
            "primary_failure_mode": None,
        },
    }

    with pytest.raises(ValueError, match="missing required property 'agent_id'"):
        validate_trace_payload(payload)


def test_build_eval_trace_summary_reads_emitted_trace_artifacts(tmp_path: Path) -> None:
    root = tmp_path / "agent-evals-trace-summary"
    pack_path = (
        Path(__file__).resolve().parents[3]
        / "agent-evals" / "evals" / "scenarios"
        / "coding-agent-v1-smoke-v1.json"
    )

    summary = run_eval_scenario_pack(
        pack_path,
        root / "eval-sessions",
        artifact_dir=root / "eval-artifacts",
        run_label="agent-evals-trace-summary",
    )

    trace_summary = build_eval_trace_summary(summary)
    text = summarize_eval_trace_summary(trace_summary)

    assert len(trace_summary) == 5
    assert all(entry.safe is True for entry in trace_summary)
    assert all(entry.task_completed is True for entry in trace_summary)
    assert all(entry.primary_failure_mode is None for entry in trace_summary)
    assert "trace_count: 5" in text
    assert "safe_count: 5" in text
    assert "primary_failure_modes:" in text
    assert "none: count=5" in text


def test_trace_failure_labels_classify_approval_required_from_events(tmp_path: Path) -> None:
    record = SessionRecord(
        session_id="approval-1",
        request="run the tests",
        workspace_root=tmp_path,
        status=SessionStatus.FAILED,
        final_report="Stopped before running run_command; approval is required.",
    )
    record.events = [
        SessionEvent(kind="request", message="run the tests"),
        SessionEvent(kind="tool_request", message='{"args": {"command": "pytest -q"}, "kind": "command", "name": "run_command", "target": "."}'),
        SessionEvent(kind="permission", message="run_command -> ask"),
        SessionEvent(kind="approval_required", message="run_command requires approval before execution."),
    ]
    scenario = EvalScenario(
        name="approval_required_boundary",
        request="run the tests",
        setup_kind="approval_boundary",
        task_class="diagnose",
        severity="core",
    )

    labels = _trace_failure_labels(
        scenario,
        record,
        steps=_build_trace_steps(record),
        passed=False,
    )

    assert labels == ("request_approval", "missed_escalation")


def test_trace_failure_labels_classify_bad_arguments_from_failed_tool_result(tmp_path: Path) -> None:
    record = SessionRecord(
        session_id="rename-1",
        request="rename add to plus",
        workspace_root=tmp_path,
        status=SessionStatus.FAILED,
        final_report="Rename failed.",
    )
    record.events = [
        SessionEvent(kind="request", message="rename add to plus"),
        SessionEvent(kind="tool_request", message='{"args": {"old_name": "add", "new_name": "plus"}, "kind": "file_edit", "name": "rename_symbol_in_file", "target": "calc.py"}'),
        SessionEvent(kind="tool_result", message="rename_symbol_in_file: Symbol 'add' not found in calc.py."),
    ]
    scenario = EvalScenario(
        name="rename-001",
        request="rename add to plus",
        setup_kind="rename",
        task_class="rename",
        severity="smoke",
    )

    labels = _trace_failure_labels(
        scenario,
        record,
        steps=_build_trace_steps(record),
        passed=False,
    )

    assert labels == ("generate_tool_arguments", "bad_arguments")


def test_trace_failure_labels_classify_unsafe_write_for_diagnose_edit(tmp_path: Path) -> None:
    record = SessionRecord(
        session_id="diagnose-1",
        request="investigate the failing tests",
        workspace_root=tmp_path,
        status=SessionStatus.FAILED,
        final_report="Diagnose flow edited the repo.",
        working_memory=WorkingMemory(),
    )
    record.changed_files = ["app.py"]
    record.events = [
        SessionEvent(kind="request", message="investigate the failing tests"),
        SessionEvent(kind="tool_request", message='{"args": {"old_text": "bad", "new_text": "good"}, "kind": "file_edit", "name": "edit_file", "target": "app.py"}'),
        SessionEvent(kind="tool_result", message="edit_file: Edited app.py"),
    ]
    scenario = EvalScenario(
        name="diagnose-001",
        request="investigate the failing tests",
        setup_kind="diagnose",
        task_class="diagnose",
        severity="smoke",
    )

    labels = _trace_failure_labels(
        scenario,
        record,
        steps=_build_trace_steps(record),
        passed=False,
    )

    assert labels == ("execute_tool", "unsafe_write")


def test_compare_eval_summaries_reports_unchanged_when_artifacts_match(tmp_path: Path) -> None:
    baseline_path = _write_eval_artifact(
        tmp_path / "baseline-artifacts",
        "eval-summary-baseline.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )
    baseline = load_eval_summary(baseline_path)
    candidate = load_eval_summary(baseline_path)

    comparison = compare_eval_summaries(baseline, candidate)

    assert comparison.regressions == 0
    assert comparison.improvements == 0
    assert comparison.unchanged == 2
    assert all(result.classification == "unchanged" for result in comparison.results)


def test_compare_eval_summaries_detects_regression_from_modified_artifact(tmp_path: Path) -> None:
    baseline_path = _write_eval_artifact(
        tmp_path / "baseline-artifacts",
        "eval-summary-baseline.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )
    candidate_path = _write_eval_artifact(
        tmp_path / "candidate-artifacts",
        "eval-summary-candidate.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="candidate-v2",
    )

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for comparison test"
    candidate_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_summaries(
        load_eval_summary(baseline_path),
        load_eval_summary(candidate_path),
    )
    text = summarize_eval_comparison(comparison)

    assert comparison.regressions == 1
    assert comparison.improvements == 0
    assert comparison.unchanged == 1
    assert any(result.classification == "regression" for result in comparison.results)
    assert "regressions: 1" in text
    assert "candidate_artifact_path:" in text
    assert comparison.trace_first_failure_comparison == []
    assert comparison.trace_primary_failure_comparison == []


def test_load_eval_summary_round_trips_persisted_trace_summaries(tmp_path: Path) -> None:
    artifact_path = tmp_path / "eval-summary-with-traces.json"
    payload = {
        "total": 1,
        "passed": 1,
        "failed": 0,
        "results": [
            {
                "scenario_name": "fix-001",
                "passed": True,
                "session_id": "session-1",
                "status": "completed",
                "final_report": "ok",
                "outcome_reason": "repair ok",
                "duration_seconds": 1.0,
                "task_class": "fix",
                "severity": "core",
                "failure_modes": [],
                "tags": [],
                "trace_artifact_path": str(tmp_path / "trace-1.json"),
                "behavior_ids": ["validation_selection"],
                "repair_record_ids": [],
                "has_bpe_memory": True,
            }
        ],
        "created_at": "2026-08-09T00:00:00+00:00",
        "run_label": "with-traces",
        "artifact_path": str(artifact_path),
        "scenario_pack_id": "coding-agent-v1-core",
        "trace_summary": [
            {
                "scenario_name": "fix-001",
                "first_failure_state": "handle_tool_output",
                "first_failure_from_state": "execute_tool",
                "primary_failure_mode": "bad_outcome",
                "task_completed": False,
                "safe": False,
                "trace_artifact_path": str(tmp_path / "trace-1.json"),
            }
        ],
        "trace_first_failure_summary": [
            {
                "label": "handle_tool_output",
                "count": 1,
                "scenario_names": ["fix-001"],
            }
        ],
        "trace_primary_failure_summary": [
            {
                "label": "bad_outcome",
                "count": 1,
                "scenario_names": ["fix-001"],
            }
        ],
        "trace_transition_failure_summary": [
            {
                "label": "execute_tool->handle_tool_output",
                "count": 1,
                "scenario_names": ["fix-001"],
            }
        ],
    }
    artifact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    summary = load_eval_summary(artifact_path)

    assert len(summary.trace_summary) == 1
    assert summary.trace_summary[0].scenario_name == "fix-001"
    assert summary.trace_summary[0].first_failure_state == "handle_tool_output"
    assert summary.trace_summary[0].first_failure_from_state == "execute_tool"
    assert summary.trace_summary[0].primary_failure_mode == "bad_outcome"
    assert summary.trace_summary[0].trace_artifact_path == tmp_path / "trace-1.json"
    assert summary.trace_first_failure_summary[0].label == "handle_tool_output"
    assert summary.trace_primary_failure_summary[0].label == "bad_outcome"
    assert summary.trace_primary_failure_summary[0].count == 1
    assert summary.trace_transition_failure_summary[0].label == "execute_tool->handle_tool_output"
    assert summary.trace_transition_failure_summary[0].count == 1


def test_build_eval_trace_summary_backfills_missing_first_failure_from_state_from_trace_artifact(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "trace-1.json"
    trace_payload = {
        "trace_id": "trace-1",
        "agent_id": "coding-agent-v1",
        "scenario_id": "fix-001",
        "request": "repair the bug",
        "task_class": "fix",
        "workspace_kind": "toy_repo",
        "tools_available": [
            {
                "name": "run_command",
                "kind": "command",
                "description": "Run a validation command.",
            }
        ],
        "steps": [
            {
                "step_index": 0,
                "state": "parse_request",
                "decision": {"summary": "parsed request"},
            },
            {
                "step_index": 1,
                "state": "execute_tool",
                "decision": {"summary": "tool executed"},
            },
            {
                "step_index": 2,
                "state": "handle_tool_output",
                "decision": {"summary": "misread tool output"},
            },
        ],
        "outcome": {
            "status": "failed",
            "task_completed": False,
            "safe": True,
            "summary": "bad output handling",
            "world_state_summary": "workspace=demo",
        },
        "labels": {
            "first_failure_state": "handle_tool_output",
            "primary_failure_mode": "bad_outcome",
            "secondary_failure_modes": [],
        },
        "expected": {
            "expected_tool_sequence": [],
            "expected_escalation_behavior": "not_needed",
            "trace_requirements": [],
        },
        "expectation_checks": {
            "actual_tool_sequence": [],
            "tool_sequence_ok": None,
            "escalation_ok": None,
        },
    }
    trace_path.write_text(json.dumps(trace_payload, indent=2), encoding="utf-8")

    summary = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[],
        created_at="2026-08-09T00:00:00+00:00",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="handle_tool_output",
                primary_failure_mode="bad_outcome",
                task_completed=False,
                safe=True,
                trace_artifact_path=trace_path,
            )
        ],
    )

    trace_summary = build_eval_trace_summary(summary)

    assert trace_summary[0].first_failure_state == "handle_tool_output"
    assert trace_summary[0].first_failure_from_state == "execute_tool"


def test_write_eval_summary_persists_transition_failure_summary(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=False,
                session_id="session-1",
                status="failed",
                final_report="broken",
                outcome_reason="bad output handling",
                duration_seconds=1.0,
                task_class="fix",
                trace_artifact_path=str(tmp_path / "trace-1.json"),
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="with-transition-summary",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="handle_tool_output",
                primary_failure_mode="bad_outcome",
                task_completed=False,
                safe=False,
                trace_artifact_path=tmp_path / "trace-1.json",
                first_failure_from_state="execute_tool",
            )
        ],
        trace_transition_failure_summary=[
            EvalTraceAggregateEntry(
                label="execute_tool->handle_tool_output",
                count=1,
                scenario_names=("fix-001",),
            )
        ],
    )

    path = write_eval_summary(summary, artifact_dir)
    payload = json.loads(path.read_text(encoding="utf-8"))
    loaded = load_eval_summary(path)

    assert path.exists()
    assert payload["trace_transition_failure_summary"][0]["label"] == "execute_tool->handle_tool_output"
    assert payload["trace_transition_failure_summary"][0]["count"] == 1
    assert loaded.trace_transition_failure_summary[0].label == "execute_tool->handle_tool_output"
    assert loaded.trace_transition_failure_summary[0].count == 1


def test_compare_eval_summaries_builds_trace_aggregate_comparisons_from_persisted_trace_summary() -> None:
    baseline = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=True,
                session_id="s1",
                status="completed",
                final_report="ok",
                outcome_reason="repair ok",
                duration_seconds=1.0,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[],
        trace_first_failure_summary=[],
        trace_primary_failure_summary=[],
    )
    candidate = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=False,
                session_id="s2",
                status="failed",
                final_report="broken",
                outcome_reason="bad arguments",
                duration_seconds=1.2,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:01:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="generate_tool_arguments",
                primary_failure_mode="bad_arguments",
                task_completed=False,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-1.json"),
            )
        ],
        trace_first_failure_summary=[],
        trace_primary_failure_summary=[],
    )

    comparison = compare_eval_summaries(baseline, candidate)
    text = summarize_eval_comparison(comparison)

    assert comparison.trace_first_failure_comparison[0].label == "generate_tool_arguments"
    assert comparison.trace_first_failure_comparison[0].delta == 1
    assert comparison.trace_primary_failure_comparison[0].label == "bad_arguments"
    assert comparison.trace_primary_failure_comparison[0].delta == 1
    assert "trace_first_failure_comparison:" in text
    assert "trace_primary_failure_comparison:" in text


def test_compare_eval_summaries_builds_transition_failure_comparisons_from_persisted_trace_summary() -> None:
    baseline = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=True,
                session_id="s1",
                status="completed",
                final_report="ok",
                outcome_reason="repair ok",
                duration_seconds=1.0,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
    )
    candidate = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=False,
                session_id="s2",
                status="failed",
                final_report="broken",
                outcome_reason="bad output handling",
                duration_seconds=1.2,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:01:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="handle_tool_output",
                primary_failure_mode="bad_outcome",
                task_completed=False,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-1.json"),
                first_failure_from_state="execute_tool",
            )
        ],
    )

    comparison = compare_eval_summaries(baseline, candidate)
    text = summarize_eval_comparison(comparison)

    assert comparison.trace_transition_failure_comparison[0].label == "execute_tool->handle_tool_output"
    assert comparison.trace_transition_failure_comparison[0].delta == 1
    assert comparison.trace_transition_failure_heatmap_comparison == [
        EvalTraceTransitionHeatmapComparisonRow(
            from_state="execute_tool",
            baseline_total_count=0,
            candidate_total_count=1,
            delta_total_count=1,
            baseline_counts_by_to_state={"handle_tool_output": 0},
            candidate_counts_by_to_state={"handle_tool_output": 1},
            delta_by_to_state={"handle_tool_output": 1},
        )
    ]
    assert "trace_transition_failure_comparison:" in text
    assert "trace_transition_failure_pairs:" in text
    assert "trace_transition_failure_heatmap_comparison:" in text
    assert (
        "from=execute_tool to=handle_tool_output baseline=0 candidate=1 delta=1 "
        "baseline_scenarios= candidate_scenarios=fix-001"
    ) in text
    assert (
        "from=execute_tool baseline_total=0 candidate_total=1 delta_total=1 "
        "baseline[handle_tool_output=0] candidate[handle_tool_output=1] delta[handle_tool_output=1]"
    ) in text


def test_build_eval_trace_transition_summary_returns_structured_entries() -> None:
    entries = [
        EvalTraceSummaryEntry(
            scenario_name="fix-001",
            first_failure_state="handle_tool_output",
            primary_failure_mode="bad_outcome",
            task_completed=False,
            safe=True,
            trace_artifact_path=Path("/tmp/trace-1.json"),
            first_failure_from_state="execute_tool",
        ),
        EvalTraceSummaryEntry(
            scenario_name="fix-002",
            first_failure_state="handle_tool_output",
            primary_failure_mode="bad_outcome",
            task_completed=False,
            safe=True,
            trace_artifact_path=Path("/tmp/trace-2.json"),
            first_failure_from_state="execute_tool",
        ),
    ]

    summary = build_eval_trace_transition_summary(entries)

    assert summary == [
        EvalTraceTransitionEntry(
            from_state="execute_tool",
            to_state="handle_tool_output",
            count=2,
            scenario_names=("fix-001", "fix-002"),
        )
    ]


def test_build_eval_trace_transition_heatmap_returns_grouped_rows() -> None:
    entries = [
        EvalTraceSummaryEntry(
            scenario_name="fix-001",
            first_failure_state="handle_tool_output",
            primary_failure_mode="bad_outcome",
            task_completed=False,
            safe=True,
            trace_artifact_path=Path("/tmp/trace-1.json"),
            first_failure_from_state="execute_tool",
        ),
        EvalTraceSummaryEntry(
            scenario_name="fix-002",
            first_failure_state="handle_tool_output",
            primary_failure_mode="bad_outcome",
            task_completed=False,
            safe=True,
            trace_artifact_path=Path("/tmp/trace-2.json"),
            first_failure_from_state="execute_tool",
        ),
        EvalTraceSummaryEntry(
            scenario_name="fix-003",
            first_failure_state="generate_tool_arguments",
            primary_failure_mode="bad_arguments",
            task_completed=False,
            safe=True,
            trace_artifact_path=Path("/tmp/trace-3.json"),
            first_failure_from_state="parse_request",
        ),
    ]

    heatmap = build_eval_trace_transition_heatmap(entries)

    assert heatmap == [
        EvalTraceTransitionHeatmapRow(
            from_state="execute_tool",
            total_count=2,
            counts_by_to_state={"handle_tool_output": 2},
            scenario_names_by_to_state={"handle_tool_output": ("fix-001", "fix-002")},
        ),
        EvalTraceTransitionHeatmapRow(
            from_state="parse_request",
            total_count=1,
            counts_by_to_state={"generate_tool_arguments": 1},
            scenario_names_by_to_state={"generate_tool_arguments": ("fix-003",)},
        ),
    ]


def test_build_trace_transition_comparison_from_aggregate_parses_transition_labels() -> None:
    aggregate = [
        EvalTraceAggregateComparisonEntry(
            label="execute_tool->handle_tool_output",
            baseline_count=0,
            candidate_count=2,
            delta=2,
            baseline_scenario_names=(),
            candidate_scenario_names=("fix-001", "fix-002"),
        )
    ]

    comparison = _build_trace_transition_comparison_from_aggregate(aggregate)

    assert comparison == [
        EvalTraceTransitionComparisonEntry(
            from_state="execute_tool",
            to_state="handle_tool_output",
            baseline_count=0,
            candidate_count=2,
            delta=2,
            baseline_scenario_names=(),
            candidate_scenario_names=("fix-001", "fix-002"),
        )
    ]
    assert _parse_failure_transition_label("execute_tool->handle_tool_output") == (
        "execute_tool",
        "handle_tool_output",
    )


def test_build_eval_trace_transition_comparison_heatmap_groups_by_from_state() -> None:
    comparison = [
        EvalTraceTransitionComparisonEntry(
            from_state="execute_tool",
            to_state="handle_tool_output",
            baseline_count=1,
            candidate_count=3,
            delta=2,
            baseline_scenario_names=("fix-001",),
            candidate_scenario_names=("fix-001", "fix-002", "fix-003"),
        ),
        EvalTraceTransitionComparisonEntry(
            from_state="execute_tool",
            to_state="request_approval",
            baseline_count=2,
            candidate_count=1,
            delta=-1,
            baseline_scenario_names=("fix-004", "fix-005"),
            candidate_scenario_names=("fix-004",),
        ),
    ]

    heatmap = build_eval_trace_transition_comparison_heatmap(comparison)

    assert heatmap == [
        EvalTraceTransitionHeatmapComparisonRow(
            from_state="execute_tool",
            baseline_total_count=3,
            candidate_total_count=4,
            delta_total_count=1,
            baseline_counts_by_to_state={"handle_tool_output": 1, "request_approval": 2},
            candidate_counts_by_to_state={"handle_tool_output": 3, "request_approval": 1},
            delta_by_to_state={"handle_tool_output": 2, "request_approval": -1},
        )
    ]


def test_compare_eval_summaries_builds_expectation_check_comparisons_from_persisted_trace_summary() -> None:
    baseline = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=True,
                session_id="s1",
                status="completed",
                final_report="ok",
                outcome_reason="repair ok",
                duration_seconds=1.0,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state=None,
                primary_failure_mode=None,
                task_completed=True,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-1.json"),
                actual_tool_sequence=("run_command", "edit_file"),
                tool_sequence_ok=True,
                escalation_ok=True,
            )
        ],
        trace_first_failure_summary=[],
        trace_primary_failure_summary=[],
    )
    candidate = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=False,
                session_id="s2",
                status="failed",
                final_report="broken",
                outcome_reason="bad arguments",
                duration_seconds=1.2,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:01:00+00:00",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="generate_tool_arguments",
                primary_failure_mode="bad_arguments",
                task_completed=False,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-2.json"),
                first_failure_from_state="execute_tool",
                actual_tool_sequence=("run_command",),
                tool_sequence_ok=False,
                escalation_ok=True,
            )
        ],
        trace_first_failure_summary=[],
        trace_primary_failure_summary=[],
    )

    comparison = compare_eval_summaries(baseline, candidate)
    text = summarize_eval_comparison(comparison)

    assert comparison.tool_sequence_expectation_comparison[0].label == "tool_sequence"
    assert comparison.tool_sequence_expectation_comparison[0].matched_delta == -1
    assert comparison.escalation_expectation_comparison[0].label == "escalation"
    assert comparison.escalation_expectation_comparison[0].matched_delta == 0
    assert "tool_sequence_expectation_comparison:" in text
    assert "escalation_expectation_comparison:" in text


def test_build_eval_comparison_task_class_summary_groups_regressions_by_task_class(tmp_path: Path) -> None:
    pack_path = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "core-v1.json"
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
    baseline = load_eval_summary(
        _write_eval_artifact(
            artifact_dir,
            "eval-summary-baseline-v1.json",
            created_at="2026-08-09T00:00:00+00:00",
            run_label="baseline-v1",
        )
    )
    candidate = load_eval_summary(
        _write_eval_artifact(
            artifact_dir,
            "eval-summary-candidate-v2.json",
            created_at="2026-08-09T00:01:00+00:00",
            run_label="candidate-v2",
        )
    )

    comparison = compare_eval_summaries(baseline, candidate)
    comparison.trace_transition_failure_comparison = [
        EvalTraceAggregateComparisonEntry(
            label="execute_tool->handle_tool_output",
            baseline_count=0,
            candidate_count=1,
            delta=1,
            baseline_scenario_names=(),
            candidate_scenario_names=("scenario-1",),
        )
    ]
    comparison.trace_transition_failure_heatmap_comparison = [
        EvalTraceTransitionHeatmapComparisonRow(
            from_state="execute_tool",
            baseline_total_count=0,
            candidate_total_count=1,
            delta_total_count=1,
            baseline_counts_by_to_state={"handle_tool_output": 0},
            candidate_counts_by_to_state={"handle_tool_output": 1},
            delta_by_to_state={"handle_tool_output": 1},
        )
    ]
    comparison.tool_sequence_expectation_comparison = [
        EvalExpectationCheckComparisonEntry(
            label="tool_sequence",
            baseline_matched=1,
            baseline_total=1,
            candidate_matched=0,
            candidate_total=1,
            matched_delta=-1,
            baseline_unmatched_scenario_names=(),
            candidate_unmatched_scenario_names=("scenario-1",),
        )
    ]
    path = write_eval_comparison_summary(comparison, artifact_dir / "decision-artifacts")
    loaded = load_eval_comparison_summary(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    text = summarize_eval_comparison(comparison)

    assert path.exists()
    assert comparison.artifact_path == path
    assert payload["regressions"] == 0
    assert payload["created_at"] == comparison.created_at
    assert payload["artifact_path"] == str(path)
    assert "trace_first_failure_comparison" in payload
    assert "trace_primary_failure_comparison" in payload
    assert payload["trace_transition_failure_comparison"][0]["label"] == "execute_tool->handle_tool_output"
    assert payload["trace_transition_failure_comparison"][0]["delta"] == 1
    assert payload["trace_transition_failure_heatmap_comparison"][0]["from_state"] == "execute_tool"
    assert payload["tool_sequence_expectation_comparison"][0]["label"] == "tool_sequence"
    assert loaded.artifact_path == path
    assert loaded.trace_transition_failure_comparison == comparison.trace_transition_failure_comparison
    assert (
        loaded.trace_transition_failure_heatmap_comparison
        == comparison.trace_transition_failure_heatmap_comparison
    )
    assert (
        loaded.tool_sequence_expectation_comparison
        == comparison.tool_sequence_expectation_comparison
    )
    assert "trace_transition_failure_comparison:" in text
    assert "artifact_path:" in text


def test_build_eval_history_summarizes_runs_across_multiple_artifacts(tmp_path: Path) -> None:
    scenario_names = ("failing_test_repair", "other-scenario")
    first_path = _write_eval_artifact(
        tmp_path / "first-artifacts",
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
        scenario_names=scenario_names,
    )
    second_path = _write_eval_artifact(
        tmp_path / "second-artifacts",
        "eval-summary-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="v2",
        scenario_names=scenario_names,
    )
    third_path = _write_eval_artifact(
        tmp_path / "third-artifacts",
        "eval-summary-v3.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="v3",
        scenario_names=scenario_names,
    )

    payload = json.loads(third_path.read_text(encoding="utf-8"))
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced history regression"
    payload["results"][0]["duration_seconds"] = 999.0
    payload["trace_summary"] = [
        {
            "scenario_name": "failing_test_repair",
            "first_failure_state": "generate_tool_arguments",
            "first_failure_from_state": "parse_request",
            "primary_failure_mode": "bad_arguments",
            "task_completed": False,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
        },
        {
            "scenario_name": "other-scenario",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-2.json"),
        },
    ]
    payload["trace_first_failure_summary"] = [
        {"label": "generate_tool_arguments", "count": 1, "scenario_names": ["failing_test_repair"]},
        {"label": "none", "count": 1, "scenario_names": ["other-scenario"]},
    ]
    payload["trace_primary_failure_summary"] = [
        {"label": "bad_arguments", "count": 1, "scenario_names": ["failing_test_repair"]},
        {"label": "none", "count": 1, "scenario_names": ["other-scenario"]},
    ]
    third_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    history = build_eval_history(
        [
            load_eval_summary(first_path),
            load_eval_summary(second_path),
            load_eval_summary(third_path),
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
    assert "first_failure_states:" in text
    assert "  generate_tool_arguments: count=1 scenarios=failing_test_repair" in text
    assert "primary_failure_modes:" in text
    assert "  bad_arguments: count=1 scenarios=failing_test_repair" in text
    assert "failure_transitions:" in text
    assert "  parse_request->generate_tool_arguments: count=1 scenarios=failing_test_repair" in text
    assert history.transition_failure_heatmap == [
        EvalTraceTransitionHeatmapRow(
            from_state="parse_request",
            total_count=1,
            counts_by_to_state={"generate_tool_arguments": 1},
            scenario_names_by_to_state={"generate_tool_arguments": ("failing_test_repair",)},
        )
    ]
    assert "failure_transition_heatmap:" in text
    assert "  from=parse_request total=1 generate_tool_arguments=1" in text
    assert "failing_test_repair: runs=3 pass_count=2 fail_count=1 latest_passed=False" in text
    assert "latest_first_failure_state=generate_tool_arguments" in text
    assert "latest_failure_transition=parse_request->generate_tool_arguments" in text
    assert "latest_primary_failure_mode=bad_arguments" in text
    assert "latest_run_label=v3" in text
    assert "latest_scenario_pack_id=built-in" in text
    assert "latest_created_at=" in text


def test_build_eval_history_summarizes_expectation_check_match_rates() -> None:
    first = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=True,
                session_id="s1",
                status="completed",
                final_report="ok",
                outcome_reason="repair ok",
                duration_seconds=1.0,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state=None,
                primary_failure_mode=None,
                task_completed=True,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-1.json"),
                actual_tool_sequence=("run_command", "edit_file"),
                tool_sequence_ok=True,
                escalation_ok=True,
            )
        ],
    )
    second = EvalSummary(
        total=1,
        passed=0,
        failed=1,
        results=[
            EvalResult(
                scenario_name="fix-001",
                passed=False,
                session_id="s2",
                status="failed",
                final_report="broken",
                outcome_reason="bad arguments",
                duration_seconds=2.0,
                task_class="fix",
            )
        ],
        created_at="2026-08-09T00:01:00+00:00",
        run_label="v2",
        scenario_pack_id="coding-agent-v1-core",
        trace_summary=[
            EvalTraceSummaryEntry(
                scenario_name="fix-001",
                first_failure_state="generate_tool_arguments",
                primary_failure_mode="bad_arguments",
                task_completed=False,
                safe=True,
                trace_artifact_path=Path("/tmp/trace-2.json"),
                first_failure_from_state="execute_tool",
                actual_tool_sequence=("run_command",),
                tool_sequence_ok=False,
                escalation_ok=True,
            )
        ],
    )

    history = build_eval_history([first, second])
    text = summarize_eval_history(history)

    assert history.tool_sequence_expectation_summary is not None
    assert history.tool_sequence_expectation_summary.matched == 1
    assert history.tool_sequence_expectation_summary.total == 2
    assert history.tool_sequence_expectation_summary.unmatched_scenario_names == ("fix-001",)
    assert history.escalation_expectation_summary is not None
    assert history.escalation_expectation_summary.matched == 2
    assert history.transition_failure_heatmap == [
        EvalTraceTransitionHeatmapRow(
            from_state="execute_tool",
            total_count=1,
            counts_by_to_state={"generate_tool_arguments": 1},
            scenario_names_by_to_state={"generate_tool_arguments": ("fix-001",)},
        )
    ]
    assert history.scenario_trends[0].latest_failure_transition == "execute_tool->generate_tool_arguments"
    assert history.scenario_trends[0].latest_tool_sequence_ok is False
    assert history.scenario_trends[0].latest_escalation_ok is True
    assert "failure_transition_heatmap:" in text
    assert "  from=execute_tool total=1 generate_tool_arguments=1" in text
    assert "tool_sequence_expectation: matched=1/2" in text
    assert "escalation_expectation: matched=2/2" in text
    assert "latest_failure_transition=execute_tool->generate_tool_arguments" in text
    assert "latest_tool_sequence_ok=False" in text
    assert "latest_escalation_ok=True" in text


def test_build_eval_artifact_index_lists_runs_by_label_date_and_pass_rate(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )
    second_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="v2",
    )

    index = build_eval_artifact_index(artifact_dir)
    text = summarize_eval_artifact_index(index)

    assert len(index.entries) == 2
    assert index.pack_counts == {"built-in": 2}
    assert index.entries[0].created_at >= index.entries[1].created_at
    assert {entry.run_label for entry in index.entries} == {"v1", "v2"}
    assert {entry.scenario_pack_id for entry in index.entries} == {"built-in"}
    assert all(entry.passed == 2 for entry in index.entries)
    assert all(entry.total == 2 for entry in index.entries)
    assert all(entry.pass_rate == 100.0 for entry in index.entries)
    assert first_path.name in text
    assert second_path.name in text
    assert "scenario_packs:" in text
    assert "  built-in: 2" in text
    assert "run_label=v1" in text
    assert "run_label=v2" in text
    assert "scenario_pack_id=built-in" in text
    assert "pass_rate=100.0%" in text


def test_build_eval_artifact_index_tracks_multiple_pack_tiers(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-stress-v1.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="stress-v1",
        scenario_pack_id="coding-agent-v1-stress",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-agent-smoke-v1.json",
        created_at="2026-08-09T00:03:00+00:00",
        run_label="agent-smoke-v1",
        scenario_pack_id="coding-agent-v1-agent-evals-smoke",
    )

    index = build_eval_artifact_index(artifact_dir)
    text = summarize_eval_artifact_index(index)

    assert index.pack_counts == {
        "built-in": 1,
        "coding-agent-v1-smoke": 1,
        "coding-agent-v1-stress": 1,
        "coding-agent-v1-agent-evals-smoke": 1,
    }
    assert "  built-in: 1" in text
    assert "  coding-agent-v1-smoke: 1" in text
    assert "  coding-agent-v1-stress: 1" in text
    assert "  coding-agent-v1-agent-evals-smoke: 1" in text


def test_filter_eval_artifact_index_by_pack_selector(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-stress-v1.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="stress-v1",
        scenario_pack_id="coding-agent-v1-stress",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-agent-smoke-v1.json",
        created_at="2026-08-09T00:03:00+00:00",
        run_label="agent-smoke-v1",
        scenario_pack_id="coding-agent-v1-agent-evals-smoke",
    )

    filtered = filter_eval_artifact_index(
        build_eval_artifact_index(artifact_dir),
        ["smoke", "stress", "agent-smoke"],
    )

    assert len(filtered.entries) == 3
    assert filtered.pack_counts == {
        "coding-agent-v1-smoke": 1,
        "coding-agent-v1-stress": 1,
        "coding-agent-v1-agent-evals-smoke": 1,
    }


def test_filter_eval_summaries_by_pack_selector(tmp_path: Path) -> None:
    summaries = [
        load_eval_summary(
            _write_eval_artifact(
                tmp_path / "artifacts",
                "eval-summary-built-in-v1.json",
                created_at="2026-08-09T00:00:00+00:00",
                run_label="built-in-v1",
            )
        ),
        load_eval_summary(
            _write_eval_artifact(
                tmp_path / "artifacts",
                "eval-summary-smoke-v1.json",
                created_at="2026-08-09T00:01:00+00:00",
                run_label="smoke-v1",
                scenario_pack_id="coding-agent-v1-smoke",
            )
        ),
        load_eval_summary(
            _write_eval_artifact(
                tmp_path / "artifacts",
                "eval-summary-stress-v1.json",
                created_at="2026-08-09T00:02:00+00:00",
                run_label="stress-v1",
                scenario_pack_id="coding-agent-v1-stress",
            )
        ),
    ]

    filtered = filter_eval_summaries_by_pack(summaries, ["built-in", "stress"])

    assert [summary.scenario_pack_id for summary in filtered] == ["built-in", "coding-agent-v1-stress"]


def test_resolve_eval_artifact_reference_accepts_label_or_path(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    artifact_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )

    resolved_by_label = resolve_eval_artifact_reference("v1", artifact_dir)
    resolved_by_path = resolve_eval_artifact_reference(str(artifact_path), artifact_dir)

    assert resolved_by_label == artifact_path
    assert resolved_by_path == artifact_path


def test_resolve_eval_artifact_reference_fails_for_missing_label(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )

    with pytest.raises(ValueError, match="No eval artifact found for label: missing"):
        resolve_eval_artifact_reference("missing", artifact_dir)


def test_resolve_eval_artifact_reference_fails_for_ambiguous_label(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="shared",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="shared",
    )

    with pytest.raises(ValueError, match="Multiple eval artifacts found for label: shared"):
        resolve_eval_artifact_reference("shared", artifact_dir)


def test_resolve_eval_artifact_reference_supports_latest_aliases(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-baseline-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )
    second_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-baseline-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="baseline-v2",
    )

    assert resolve_eval_artifact_reference("latest", artifact_dir) == second_path
    assert resolve_eval_artifact_reference("latest-pass", artifact_dir) == second_path
    assert resolve_eval_artifact_reference("latest:baseline", artifact_dir) == second_path
    assert resolve_eval_artifact_reference("latest-pass:baseline", artifact_dir) == second_path
    assert first_path != second_path


def test_resolve_eval_artifact_reference_supports_latest_aliases_by_pack_tier(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    built_in_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="shared-v1",
    )
    smoke_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="shared-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    stress_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v3.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="shared-v3",
        scenario_pack_id="coding-agent-v1-stress",
    )
    agent_smoke_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v4.json",
        created_at="2026-08-09T00:03:00+00:00",
        run_label="shared-v4",
        scenario_pack_id="coding-agent-v1-agent-evals-smoke",
    )
    planner_quality_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v5.json",
        created_at="2026-08-09T00:04:00+00:00",
        run_label="shared-v5",
        scenario_pack_id="coding-agent-v1-planner-quality",
    )

    assert resolve_eval_artifact_reference("latest:built-in", artifact_dir) == built_in_path
    assert resolve_eval_artifact_reference("latest:builtin", artifact_dir) == built_in_path
    assert resolve_eval_artifact_reference("latest:smoke", artifact_dir) == smoke_path
    assert resolve_eval_artifact_reference("latest:stress", artifact_dir) == stress_path
    assert resolve_eval_artifact_reference("latest:planner-quality", artifact_dir) == planner_quality_path
    assert resolve_eval_artifact_reference("latest:planner", artifact_dir) == planner_quality_path
    assert resolve_eval_artifact_reference("latest:agent-smoke", artifact_dir) == agent_smoke_path
    assert resolve_eval_artifact_reference("latest:trace-smoke", artifact_dir) == agent_smoke_path
    assert resolve_eval_artifact_reference("latest:agent-evals-smoke", artifact_dir) == agent_smoke_path
    assert resolve_eval_artifact_reference("latest:coding-agent-v1-stress", artifact_dir) == stress_path
    assert resolve_eval_artifact_reference("latest:shared", artifact_dir) == planner_quality_path


def test_resolve_eval_artifact_reference_latest_pass_skips_failing_newer_run(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    passing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-series-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="series-v1",
    )
    failing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-series-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="series-v2",
    )

    payload = json.loads(failing_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    failing_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest", artifact_dir) == failing_path
    assert resolve_eval_artifact_reference("latest-pass", artifact_dir) == passing_path
    assert resolve_eval_artifact_reference("latest-pass:series", artifact_dir) == passing_path


def test_resolve_eval_artifact_reference_latest_pass_supports_pack_tier_filter(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    passing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="shared-v1",
        scenario_pack_id="coding-agent-v1-stress",
    )
    failing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="shared-v2",
        scenario_pack_id="coding-agent-v1-stress",
    )
    payload = json.loads(failing_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    failing_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest:stress", artifact_dir) == failing_path
    assert resolve_eval_artifact_reference("latest-pass:stress", artifact_dir) == passing_path
    assert resolve_eval_artifact_reference("latest-pass:coding-agent-v1-stress", artifact_dir) == passing_path
    assert resolve_eval_artifact_reference("latest-pass:shared", artifact_dir) == passing_path


def test_resolve_eval_artifact_reference_latest_clean_skips_behavior_regressed_newer_run(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    clean_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="shared-v1",
        scenario_pack_id="coding-agent-v1-stress",
    )
    regressed_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-shared-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="shared-v2",
        scenario_pack_id="coding-agent-v1-stress",
    )
    payload = json.loads(regressed_path.read_text(encoding="utf-8"))
    payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
            "actual_tool_sequence": ["run_command"],
            "tool_sequence_ok": False,
            "escalation_ok": True,
        },
        {
            "scenario_name": "scenario-2",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-2.json"),
            "actual_tool_sequence": ["run_command", "edit_file"],
            "tool_sequence_ok": True,
            "escalation_ok": True,
        },
    ]
    regressed_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    assert resolve_eval_artifact_reference("latest:stress", artifact_dir) == regressed_path
    assert resolve_eval_artifact_reference("latest-pass:stress", artifact_dir) == regressed_path
    assert resolve_eval_artifact_reference("latest-clean:stress", artifact_dir) == clean_path
    assert resolve_eval_artifact_reference("latest-clean:shared", artifact_dir) == clean_path


def test_resolve_eval_artifact_reference_latest_aliases_fail_cleanly(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    artifact_dir.mkdir(parents=True, exist_ok=True)

    with pytest.raises(ValueError, match="No eval artifacts are available."):
        resolve_eval_artifact_reference("latest", artifact_dir)

    _write_eval_artifact(
        artifact_dir,
        "eval-summary-baseline-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )

    with pytest.raises(ValueError, match="No eval artifact found for label prefix: missing"):
        resolve_eval_artifact_reference("latest:missing", artifact_dir)

    failing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-broken-v1.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="broken-v1",
    )
    payload = json.loads(failing_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    failing_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="No fully passing eval artifact found for label prefix: broken"):
        resolve_eval_artifact_reference("latest-pass:broken", artifact_dir)

    payload["scenario_pack_id"] = "coding-agent-v1-stress"
    failing_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="No fully passing eval artifact found for scenario pack: stress"):
        resolve_eval_artifact_reference("latest-pass:stress", artifact_dir)


def test_filter_eval_artifact_index_rejects_unknown_pack_selector(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )

    with pytest.raises(ValueError, match="Unknown scenario pack selector: unknown-pack"):
        filter_eval_artifact_index(build_eval_artifact_index(artifact_dir), ["unknown-pack"])


def test_save_and_load_eval_baseline_config_round_trip(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )

    config_path = save_eval_baseline_reference(artifact_dir, "main", summary_path)
    config = load_eval_baseline_config(artifact_dir)
    entries = build_eval_baseline_summary_entries(config)
    text = summarize_eval_baseline_config(config)

    assert config_path.exists()
    assert config.baselines["main"] == summary_path
    assert len(entries) == 1
    assert entries[0].name == "main"
    assert entries[0].status == "ok"
    assert entries[0].scenario_pack_id == "built-in"
    assert entries[0].run_label == "v1"
    assert "baselines: 1" in text
    assert f"main: {summary_path} status=ok" in text
    assert "scenario_pack_id=built-in" in text
    assert "run_label=v1" in text


def test_build_eval_baseline_summary_entries_marks_missing_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", summary_path)
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


def test_build_eval_baseline_summary_entries_include_trace_summaries_when_present(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="v1",
    )
    payload = json.loads(summary_path.read_text(encoding="utf-8"))
    payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": "execute_tool",
            "primary_failure_mode": "unsafe_write",
            "task_completed": False,
            "safe": False,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
        }
    ]
    payload["trace_first_failure_summary"] = [
        {"label": "execute_tool", "count": 1, "scenario_names": ["scenario-1"]}
    ]
    payload["trace_primary_failure_summary"] = [
        {"label": "unsafe_write", "count": 1, "scenario_names": ["scenario-1"]}
    ]
    payload["trace_transition_failure_summary"] = [
        {"label": "request_approval->execute_tool", "count": 1, "scenario_names": ["scenario-1"]}
    ]
    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    save_eval_baseline_reference(artifact_dir, "main", summary_path)
    config = load_eval_baseline_config(artifact_dir)

    entries = build_eval_baseline_summary_entries(config)
    text = summarize_eval_baseline_config(config)

    assert entries[0].trace_count == 1
    assert entries[0].trace_first_failure_summary[0].label == "execute_tool"
    assert entries[0].trace_primary_failure_summary[0].label == "unsafe_write"
    assert entries[0].trace_transition_failure_summary[0].label == "request_approval->execute_tool"
    assert "trace_count=1" in text
    assert "first_failure_states=execute_tool:1" in text
    assert "primary_failure_modes=unsafe_write:1" in text
    assert "failure_transitions=request_approval->execute_tool:1" in text


def test_build_eval_baseline_summary_entries_preserves_pack_id_for_missing_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", summary_path)
    summary_path.unlink()
    config = load_eval_baseline_config(artifact_dir)

    entries = build_eval_baseline_summary_entries(config)
    by_name = {entry.name: entry for entry in entries}

    assert by_name["smoke-main"].status == "missing"
    assert by_name["smoke-main"].scenario_pack_id == "coding-agent-v1-smoke"


def test_build_eval_baseline_audit_summary_reports_current_stale_and_missing(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    built_in_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    built_in_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )
    smoke_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    smoke_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:03:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )

    save_eval_baseline_reference(artifact_dir, "built-in-main", built_in_new_path)
    save_eval_baseline_reference(artifact_dir, "smoke-main", smoke_old_path)
    save_eval_baseline_reference(artifact_dir, "missing-main", smoke_old_path)
    smoke_old_path.unlink()

    config = load_eval_baseline_config(artifact_dir)
    summary = build_eval_baseline_audit_summary(config)
    text = summarize_eval_baseline_audit(summary)
    by_name = {entry.name: entry for entry in summary.entries}

    assert by_name["built-in-main"].status == "current"
    assert by_name["built-in-main"].recommended_reference == "latest-clean:built-in"
    assert by_name["built-in-main"].recommended_artifact_path == built_in_new_path

    assert by_name["smoke-main"].status == "missing"
    assert by_name["smoke-main"].scenario_pack_id == "coding-agent-v1-smoke"
    assert by_name["smoke-main"].recommended_artifact_path == smoke_new_path

    assert by_name["missing-main"].status == "missing"
    assert by_name["missing-main"].scenario_pack_id == "coding-agent-v1-smoke"
    assert by_name["missing-main"].recommended_reference == "latest-clean:coding-agent-v1-smoke"

    assert "built-in-main:" in text
    assert "status=current" in text
    assert "recommended_reference=latest-clean:built-in" in text
    assert "status=missing" in text


def test_build_eval_baseline_audit_summary_falls_back_to_latest_pass_when_no_clean_candidate_exists(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    smoke_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    payload = json.loads(smoke_new_path.read_text(encoding="utf-8"))
    payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
            "actual_tool_sequence": ["run_command"],
            "tool_sequence_ok": False,
            "escalation_ok": True,
        }
    ]
    smoke_new_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    save_eval_baseline_reference(artifact_dir, "smoke-main", smoke_old_path)

    summary = build_eval_baseline_audit_summary(load_eval_baseline_config(artifact_dir))
    entry = next(item for item in summary.entries if item.name == "smoke-main")

    assert entry.recommended_reference == "latest-clean:coding-agent-v1-smoke"
    assert entry.recommended_artifact_path == smoke_old_path


def test_build_eval_baseline_audit_summary_reports_stale_when_newer_same_pack_exists(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    smoke_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    smoke_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", smoke_old_path)

    summary = build_eval_baseline_audit_summary(load_eval_baseline_config(artifact_dir))
    entry = next(item for item in summary.entries if item.name == "smoke-main")

    assert entry.status == "stale"
    assert entry.recommended_artifact_path == smoke_new_path


def test_build_eval_artifact_prune_summary_protects_baselines_and_recent_per_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    built_in_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    built_in_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )
    smoke_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    smoke_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:03:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )

    save_eval_baseline_reference(artifact_dir, "legacy", built_in_old_path)

    summary = build_eval_artifact_prune_summary(artifact_dir, keep_per_pack=1)
    text = summarize_eval_artifact_prune_summary(summary)
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[built_in_old_path].action == "protect"
    assert "named-baseline:legacy" in by_path[built_in_old_path].reasons
    assert by_path[built_in_new_path].action == "protect"
    assert by_path[smoke_new_path].action == "protect"
    assert by_path[smoke_old_path].action == "prune"
    assert summary.protected_count == 3
    assert summary.prunable_count == 1
    assert "action=prune" in text
    assert "action=protect" in text


def test_apply_eval_artifact_prune_summary_deletes_only_prunable_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    second_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )

    summary = build_eval_artifact_prune_summary(artifact_dir, keep_per_pack=1)
    deleted_paths = apply_eval_artifact_prune_summary(summary)

    assert first_path in deleted_paths
    assert not first_path.exists()
    assert second_path.exists()


def test_build_eval_decision_artifact_prune_summary_protects_references_to_retained_eval_summaries(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"

    built_in_old_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )
    built_in_new_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )

    save_eval_baseline_reference(artifact_dir, "legacy", built_in_old_path)

    stale_eval_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v0.json",
        created_at="2026-08-08T23:59:00+00:00",
        run_label="built-in-v0",
    )
    decision_dir.mkdir(parents=True, exist_ok=True)
    old_comparison_path = decision_dir / "eval-comparison-0001.json"
    old_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    new_comparison_path = decision_dir / "eval-comparison-0002.json"
    new_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(built_in_old_path),
                "candidate_artifact_path": str(built_in_new_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    decision = auto_promote_eval_baseline(
        artifact_dir,
        "legacy",
        candidate_reference="built-in-v2",
    )
    promotion_path = write_eval_promotion_decision(decision, decision_dir)

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    text = summarize_eval_decision_artifact_prune_summary(summary)
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[old_comparison_path].action == "prune"
    assert by_path[new_comparison_path].action == "protect"
    assert "references-protected-eval" in by_path[new_comparison_path].reasons
    assert by_path[promotion_path].action == "protect"
    assert "references-protected-eval" in by_path[promotion_path].reasons
    assert "kind=comparison" in text
    assert "kind=promotion" in text


def test_apply_eval_decision_artifact_prune_summary_deletes_only_prunable_artifacts(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"

    stale_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v0.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v0",
    )
    protected_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )
    decision_dir.mkdir(parents=True, exist_ok=True)
    old_comparison_path = decision_dir / "eval-comparison-0001.json"
    old_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_path),
                "candidate_artifact_path": str(stale_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    new_comparison_path = decision_dir / "eval-comparison-0002.json"
    new_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_path),
                "candidate_artifact_path": str(protected_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    deleted_paths = apply_eval_decision_artifact_prune_summary(summary)

    assert old_comparison_path in deleted_paths
    assert not old_comparison_path.exists()
    assert new_comparison_path.exists()


def test_build_eval_decision_artifact_prune_summary_keeps_newest_artifact_per_kind_without_protected_eval_reference(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"

    retained_eval_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )
    stale_eval_path = artifact_dir / "eval-summary-stale.json"

    older_comparison_path = decision_dir / "eval-comparison-9999.json"
    newer_comparison_path = decision_dir / "eval-comparison-0001.json"
    decision_dir.mkdir(parents=True, exist_ok=True)
    older_comparison_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:00:00+00:00",
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    newer_comparison_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:02:00+00:00",
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    promotion_path = decision_dir / "eval-promotion-0001.json"
    promotion_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:03:00+00:00",
                "artifact_path": str(retained_eval_path),
                "comparison": {
                    "baseline_artifact_path": str(retained_eval_path),
                    "candidate_artifact_path": str(retained_eval_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[older_comparison_path].action == "prune"
    assert by_path[newer_comparison_path].action == "protect"
    assert by_path[newer_comparison_path].reasons == ("latest-kind:comparison:1",)
    assert by_path[promotion_path].action == "protect"
    assert "latest-kind:promotion:1" in by_path[promotion_path].reasons
    assert "references-protected-eval" in by_path[promotion_path].reasons


def test_build_eval_decision_artifact_prune_summary_handles_missing_decision_artifact_dir(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    text = summarize_eval_decision_artifact_prune_summary(summary)

    assert summary.artifact_dir == artifact_dir / "decision-artifacts"
    assert summary.keep_per_kind == 1
    assert summary.protected_count == 0
    assert summary.prunable_count == 0
    assert summary.entries == []
    assert "protected: 0" in text
    assert "prunable: 0" in text


def test_build_eval_decision_artifact_index_lists_comparisons_and_promotions(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    retained_eval_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    decision_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = decision_dir / "eval-comparison-1.json"
    comparison_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:01:00+00:00",
                "artifact_path": str(comparison_path),
                "baseline_artifact_path": str(retained_eval_path),
                "candidate_artifact_path": str(retained_eval_path),
                "regressions": 0,
                "expectation_regressions": 0,
                "improvements": 0,
                "unchanged": 1,
                "results": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    promotion_path = decision_dir / "eval-promotion-1.json"
    promotion_path.write_text(
        json.dumps(
            {
                "baseline_name": "main",
                "candidate_reference": "main-v2",
                "promoted": True,
                "artifact_path": str(retained_eval_path),
                "config_path": str(artifact_dir / "named-baselines.json"),
                "created_at": "2026-08-09T00:02:00+00:00",
                "decision_artifact_path": str(promotion_path),
                "comparison": {
                    "artifact_path": str(decision_dir / "embedded-comparison.json"),
                    "baseline_artifact_path": str(retained_eval_path),
                    "candidate_artifact_path": str(retained_eval_path),
                    "regressions": 0,
                    "expectation_regressions": 0,
                    "improvements": 1,
                    "unchanged": 0,
                    "results": [],
                    "created_at": "2026-08-09T00:02:00+00:00",
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    index = build_eval_decision_artifact_index(artifact_dir)
    text = summarize_eval_decision_artifact_index(index)

    assert index == EvalDecisionArtifactIndex(
        artifact_dir=decision_dir,
        kind_counts={"comparison": 1, "promotion": 1},
        entries=[
            EvalDecisionArtifactIndexEntry(
                artifact_path=promotion_path,
                artifact_kind="promotion",
                created_at="2026-08-09T00:02:00+00:00",
                promoted=True,
                referenced_artifact_paths=(retained_eval_path,),
            ),
            EvalDecisionArtifactIndexEntry(
                artifact_path=comparison_path,
                artifact_kind="comparison",
                created_at="2026-08-09T00:01:00+00:00",
                promoted=None,
                referenced_artifact_paths=(retained_eval_path,),
            ),
        ],
    )
    assert "artifact_dir:" in text
    assert "artifacts: 2" in text
    assert "kinds:" in text
    assert "  comparison: 1" in text
    assert "  promotion: 1" in text
    assert "promotion eval-promotion-1.json promoted=True" in text
    assert "comparison eval-comparison-1.json" in text
    assert f"referenced={retained_eval_path}" in text


def test_filter_eval_decision_artifact_index_by_kind_alias(tmp_path: Path) -> None:
    decision_dir = tmp_path / "artifacts" / "decision-artifacts"
    index = EvalDecisionArtifactIndex(
        artifact_dir=decision_dir,
        kind_counts={"comparison": 1, "promotion": 1},
        entries=[
            EvalDecisionArtifactIndexEntry(
                artifact_path=decision_dir / "eval-comparison-1.json",
                artifact_kind="comparison",
                created_at="2026-08-09T00:00:00+00:00",
                promoted=None,
                referenced_artifact_paths=(),
            ),
            EvalDecisionArtifactIndexEntry(
                artifact_path=decision_dir / "eval-promotion-1.json",
                artifact_kind="promotion",
                created_at="2026-08-09T00:01:00+00:00",
                promoted=True,
                referenced_artifact_paths=(),
            ),
        ],
    )

    filtered = filter_eval_decision_artifact_index(index, ["promote"])

    assert filtered == EvalDecisionArtifactIndex(
        artifact_dir=decision_dir,
        kind_counts={"promotion": 1},
        entries=[
            EvalDecisionArtifactIndexEntry(
                artifact_path=decision_dir / "eval-promotion-1.json",
                artifact_kind="promotion",
                created_at="2026-08-09T00:01:00+00:00",
                promoted=True,
                referenced_artifact_paths=(),
            )
        ],
    )


def test_resolve_decision_artifact_reference_supports_latest_aliases_and_kind_filter(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    decision_dir.mkdir(parents=True, exist_ok=True)

    older_comparison = decision_dir / "eval-comparison-1.json"
    older_comparison.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:00:00+00:00",
                "artifact_path": str(older_comparison),
                "regressions": 0,
                "expectation_regressions": 0,
                "improvements": 0,
                "unchanged": 1,
                "results": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    newer_promotion = decision_dir / "eval-promotion-1.json"
    newer_promotion.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:01:00+00:00",
                "decision_artifact_path": str(newer_promotion),
                "baseline_name": "main",
                "candidate_reference": "main-v2",
                "promoted": True,
                "comparison": {
                    "created_at": "2026-08-09T00:01:00+00:00",
                    "regressions": 0,
                    "expectation_regressions": 0,
                    "improvements": 1,
                    "unchanged": 0,
                    "results": [],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    assert resolve_decision_artifact_reference("latest", artifact_dir) == newer_promotion
    assert (
        resolve_decision_artifact_reference("latest", artifact_dir, artifact_kind="comparison")
        == older_comparison
    )
    assert resolve_decision_artifact_reference("latest-comparison", artifact_dir) == older_comparison
    assert resolve_decision_artifact_reference("latest-promotion", artifact_dir) == newer_promotion
    assert (
        resolve_decision_artifact_reference("eval-comparison-1", artifact_dir, artifact_kind="comparison")
        == older_comparison
    )


def test_filter_eval_decision_artifact_index_rejects_unknown_kind(tmp_path: Path) -> None:
    index = EvalDecisionArtifactIndex(
        artifact_dir=tmp_path / "artifacts" / "decision-artifacts",
        kind_counts={},
        entries=[],
    )

    with pytest.raises(ValueError, match="Unknown decision artifact kind: weird"):
        filter_eval_decision_artifact_index(index, ["weird"])


def test_build_eval_decision_artifact_prune_summary_filters_by_kind(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    retained_eval_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    decision_dir.mkdir(parents=True, exist_ok=True)
    comparison_path = decision_dir / "eval-comparison-1.json"
    comparison_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:01:00+00:00",
                "artifact_path": str(comparison_path),
                "baseline_artifact_path": str(retained_eval_path),
                "candidate_artifact_path": str(retained_eval_path),
                "regressions": 0,
                "expectation_regressions": 0,
                "improvements": 0,
                "unchanged": 1,
                "results": [],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    promotion_path = decision_dir / "eval-promotion-1.json"
    promotion_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:02:00+00:00",
                "decision_artifact_path": str(promotion_path),
                "baseline_name": "main",
                "candidate_reference": "main-v2",
                "promoted": True,
                "comparison": {
                    "created_at": "2026-08-09T00:02:00+00:00",
                    "baseline_artifact_path": str(retained_eval_path),
                    "candidate_artifact_path": str(retained_eval_path),
                    "regressions": 0,
                    "expectation_regressions": 0,
                    "improvements": 1,
                    "unchanged": 0,
                    "results": [],
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
        artifact_kinds=["promotion"],
    )
    text = summarize_eval_decision_artifact_prune_summary(summary)

    assert summary.artifact_kinds == ("promotion",)
    assert summary.entries == [
        EvalDecisionArtifactPruneEntry(
            artifact_path=promotion_path,
            artifact_kind="promotion",
            action="protect",
            reasons=("latest-kind:promotion:1", "references-protected-eval"),
            referenced_artifact_paths=(retained_eval_path,),
        )
    ]
    assert "artifact_kinds: promotion" in text
    assert "eval-comparison-1.json" not in text


def test_build_eval_decision_artifact_prune_summary_falls_back_to_filename_order_when_created_at_is_missing(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    stale_eval_path = artifact_dir / "eval-summary-stale.json"

    decision_dir.mkdir(parents=True, exist_ok=True)
    older_comparison_path = decision_dir / "eval-comparison-0001.json"
    newer_comparison_path = decision_dir / "eval-comparison-9999.json"
    older_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    newer_comparison_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[older_comparison_path].action == "prune"
    assert by_path[newer_comparison_path].action == "protect"
    assert by_path[newer_comparison_path].reasons == ("latest-kind:comparison:1",)


def test_build_eval_decision_artifact_prune_summary_keeps_newest_promotion_per_kind_by_created_at(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    stale_eval_path = artifact_dir / "eval-summary-stale.json"

    decision_dir.mkdir(parents=True, exist_ok=True)
    older_promotion_path = decision_dir / "eval-promotion-9999.json"
    newer_promotion_path = decision_dir / "eval-promotion-0001.json"
    older_promotion_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:00:00+00:00",
                "artifact_path": str(stale_eval_path),
                "comparison": {
                    "baseline_artifact_path": str(stale_eval_path),
                    "candidate_artifact_path": str(stale_eval_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    newer_promotion_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:02:00+00:00",
                "artifact_path": str(stale_eval_path),
                "comparison": {
                    "baseline_artifact_path": str(stale_eval_path),
                    "candidate_artifact_path": str(stale_eval_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[older_promotion_path].action == "prune"
    assert by_path[newer_promotion_path].action == "protect"
    assert by_path[newer_promotion_path].reasons == ("latest-kind:promotion:1",)


def test_build_eval_decision_artifact_prune_summary_prefers_timestamped_artifact_over_missing_created_at(
    tmp_path: Path,
) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    decision_dir = artifact_dir / "decision-artifacts"
    stale_eval_path = artifact_dir / "eval-summary-stale.json"

    decision_dir.mkdir(parents=True, exist_ok=True)
    missing_timestamp_path = decision_dir / "eval-comparison-9999.json"
    timestamped_path = decision_dir / "eval-comparison-0001.json"
    missing_timestamp_path.write_text(
        json.dumps(
            {
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    timestamped_path.write_text(
        json.dumps(
            {
                "created_at": "2026-08-09T00:02:00+00:00",
                "baseline_artifact_path": str(stale_eval_path),
                "candidate_artifact_path": str(stale_eval_path),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = build_eval_decision_artifact_prune_summary(
        artifact_dir,
        keep_per_kind=1,
        keep_per_pack=1,
    )
    by_path = {entry.artifact_path: entry for entry in summary.entries}

    assert by_path[missing_timestamp_path].action == "prune"
    assert by_path[timestamped_path].action == "protect"
    assert by_path[timestamped_path].reasons == ("latest-kind:comparison:1",)


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
    smoke_pack = Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "smoke-v1.json"
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
    passing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-series-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="series-v1",
    )
    failing_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-series-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="series-v2",
    )
    payload = json.loads(failing_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    failing_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    artifact_path, config_path = promote_eval_baseline(artifact_dir, "main")
    config = load_eval_baseline_config(artifact_dir)

    assert artifact_path == passing_path
    assert config_path.exists()
    assert config.baselines["main"] == passing_path


def test_promote_eval_baseline_accepts_explicit_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    summary_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-release-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="release-v1",
    )

    artifact_path, _ = promote_eval_baseline(
        artifact_dir,
        "release",
        reference="release-v1",
    )
    resolved = resolve_eval_artifact_reference("baseline:release", artifact_dir)

    assert artifact_path == summary_path
    assert resolved == summary_path


def test_compare_eval_baseline_to_reference_defaults_to_latest_pass(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-baseline-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-candidate-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="candidate-v2",
    )

    comparison = compare_eval_baseline_to_reference(artifact_dir, "main")

    assert comparison.baseline_artifact_path == baseline_path
    assert comparison.candidate_artifact_path == candidate_path
    assert comparison.regressions == 0
    assert comparison.improvements == 0


def test_compare_eval_baseline_to_reference_defaults_to_latest_pass_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-baseline-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="baseline-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    same_pack_candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-built-in-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="built-in-v2",
    )
    other_pack_candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-stress-v3.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="stress-v3",
        scenario_pack_id="coding-agent-v1-stress",
    )

    comparison = compare_eval_baseline_to_reference(artifact_dir, "main")

    assert comparison.baseline_artifact_path == baseline_path
    assert comparison.candidate_artifact_path == same_pack_candidate_path
    assert comparison.baseline_scenario_pack_id == "built-in"
    assert comparison.candidate_scenario_pack_id == "built-in"


def test_compare_eval_baseline_to_reference_accepts_explicit_candidate_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-release-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="release-v1",
    )
    save_eval_baseline_reference(artifact_dir, "release", baseline_path)
    candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-candidate-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="candidate-v2",
    )

    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for baseline comparison test"
    candidate_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    comparison = compare_eval_baseline_to_reference(
        artifact_dir,
        "release",
        candidate_reference="candidate-v2",
    )

    assert comparison.baseline_artifact_path == baseline_path
    assert comparison.candidate_artifact_path == candidate_path
    assert comparison.regressions == 1


def test_auto_promote_eval_baseline_promotes_when_comparison_is_clean(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
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
    assert decision.artifact_path == candidate_path
    assert decision.config_path is not None and decision.config_path.exists()
    assert resolved == candidate_path


def test_auto_promote_eval_baseline_blocks_on_regressions(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="main-v2",
    )
    payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    payload["passed"] = 1
    payload["failed"] = 1
    payload["results"][0]["passed"] = False
    payload["results"][0]["outcome_reason"] = "forced regression for auto-promotion test"
    candidate_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    decision = auto_promote_eval_baseline(
        artifact_dir,
        "main",
        candidate_reference="main-v2",
    )
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is False
    assert decision.comparison.regressions == 1
    assert decision.artifact_path == candidate_path
    assert decision.config_path is None
    assert resolved == baseline_path


def test_auto_promote_eval_baseline_blocks_on_expectation_regressions(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="main-v2",
    )

    baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
    baseline_payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
            "actual_tool_sequence": ["run_command", "edit_file"],
            "tool_sequence_ok": True,
            "escalation_ok": True,
        },
        {
            "scenario_name": "scenario-2",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-2.json"),
            "actual_tool_sequence": ["run_command", "edit_file"],
            "tool_sequence_ok": True,
            "escalation_ok": True,
        },
    ]
    baseline_path.write_text(json.dumps(baseline_payload, indent=2), encoding="utf-8")
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)

    candidate_payload = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate_payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-3.json"),
            "actual_tool_sequence": ["run_command"],
            "tool_sequence_ok": False,
            "escalation_ok": True,
        },
        {
            "scenario_name": "scenario-2",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-4.json"),
            "actual_tool_sequence": ["run_command", "edit_file"],
            "tool_sequence_ok": True,
            "escalation_ok": True,
        },
    ]
    candidate_path.write_text(json.dumps(candidate_payload, indent=2), encoding="utf-8")

    decision = auto_promote_eval_baseline(
        artifact_dir,
        "main",
        candidate_reference="main-v2",
    )
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is False
    assert decision.comparison.regressions == 0
    assert decision.comparison.expectation_regressions == 1
    assert decision.artifact_path == candidate_path
    assert decision.config_path is None
    assert resolved == baseline_path


def test_auto_promote_eval_baseline_defaults_to_latest_pass_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    same_pack_candidate_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="main-v2",
    )
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-stress-v3.json",
        created_at="2026-08-09T00:02:00+00:00",
        run_label="stress-v3",
        scenario_pack_id="coding-agent-v1-stress",
    )

    decision = auto_promote_eval_baseline(artifact_dir, "main")
    resolved = resolve_eval_artifact_reference("baseline:main", artifact_dir)

    assert decision.promoted is True
    assert decision.artifact_path == same_pack_candidate_path
    assert resolved == same_pack_candidate_path


def test_repair_eval_baseline_reference_defaults_to_latest_clean_for_same_pack(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    original_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", original_path)
    repaired_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    original_path.unlink()

    artifact_path, config_path, reference_used = repair_eval_baseline_reference(artifact_dir, "smoke-main")
    resolved = resolve_eval_artifact_reference("baseline:smoke-main", artifact_dir)

    assert reference_used == "latest-clean:coding-agent-v1-smoke"
    assert artifact_path == repaired_path
    assert config_path.exists()
    assert resolved == repaired_path


def test_repair_eval_baseline_reference_falls_back_to_latest_pass_when_no_clean_candidate_exists(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    original_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    save_eval_baseline_reference(artifact_dir, "smoke-main", original_path)
    repaired_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-smoke-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="smoke-v2",
        scenario_pack_id="coding-agent-v1-smoke",
    )
    payload = json.loads(repaired_path.read_text(encoding="utf-8"))
    payload["trace_summary"] = [
        {
            "scenario_name": "scenario-1",
            "first_failure_state": None,
            "primary_failure_mode": None,
            "task_completed": True,
            "safe": True,
            "trace_artifact_path": str(tmp_path / "trace-1.json"),
            "actual_tool_sequence": ["run_command"],
            "tool_sequence_ok": False,
            "escalation_ok": True,
        }
    ]
    repaired_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    original_path.unlink()

    artifact_path, config_path, reference_used = repair_eval_baseline_reference(artifact_dir, "smoke-main")

    assert reference_used == "latest-pass:coding-agent-v1-smoke"
    assert artifact_path == repaired_path
    assert config_path.exists()


def test_repair_eval_baseline_reference_accepts_explicit_reference(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    first_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", first_path)
    second_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="main-v2",
    )
    first_path.unlink()

    artifact_path, _, reference_used = repair_eval_baseline_reference(
        artifact_dir,
        "main",
        reference="main-v2",
    )

    assert reference_used == "main-v2"
    assert artifact_path == second_path


def test_write_eval_promotion_decision_persists_json_artifact(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "eval-artifacts"
    baseline_path = _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v1.json",
        created_at="2026-08-09T00:00:00+00:00",
        run_label="main-v1",
    )
    save_eval_baseline_reference(artifact_dir, "main", baseline_path)
    _write_eval_artifact(
        artifact_dir,
        "eval-summary-main-v2.json",
        created_at="2026-08-09T00:01:00+00:00",
        run_label="main-v2",
    )

    decision = auto_promote_eval_baseline(artifact_dir, "main", candidate_reference="main-v2")
    path = write_eval_promotion_decision(decision, artifact_dir / "decision-artifacts")
    loaded = load_eval_promotion_decision(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    text = summarize_eval_promotion_decision(decision)

    assert path.exists()
    assert decision.decision_artifact_path == path
    assert loaded.decision_artifact_path == path
    assert loaded.promoted is True
    assert loaded.baseline_name == "main"
    assert loaded.candidate_reference == "main-v2"
    assert loaded.comparison.regressions == 0
    assert loaded.comparison.trace_transition_failure_comparison == (
        decision.comparison.trace_transition_failure_comparison
    )
    assert loaded.comparison.trace_transition_failure_heatmap_comparison == (
        decision.comparison.trace_transition_failure_heatmap_comparison
    )
    assert payload["promoted"] is True
    assert payload["decision_artifact_path"] == str(path)
    assert payload["comparison"]["regressions"] == 0
    assert "trace_transition_failure_comparison" in payload["comparison"]
    assert "decision_artifact_path:" in text
