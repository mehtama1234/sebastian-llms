from __future__ import annotations

from pathlib import Path
import sys

from coding_agent_v1 import cli
from coding_agent_v1.eval_harness import (
    EvalDecisionArtifactPruneEntry,
    EvalDecisionArtifactPruneSummary,
    EvalArtifactPruneEntry,
    EvalArtifactPruneSummary,
    EvalBaselineAuditEntry,
    EvalBaselineAuditSummary,
    EvalArtifactIndex,
    EvalArtifactIndexEntry,
    EvalComparisonResult,
    EvalComparisonSummary,
    EvalHistoryEntry,
    EvalHistorySummary,
    EvalResult,
    EvalScenarioTrend,
    EvalSummary,
)


def test_cli_run_eval_pack_prints_summary_and_breakdowns(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalSummary(
        total=2,
        passed=2,
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
                severity="smoke",
                failure_modes=("no_op",),
                tags=("repair",),
            ),
            EvalResult(
                scenario_name="feature-001",
                passed=True,
                session_id="s2",
                status="completed",
                final_report="ok",
                outcome_reason="feature ok",
                duration_seconds=1.0,
                task_class="feature",
                severity="core",
                failure_modes=("partial_fix",),
                tags=("feature",),
            ),
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="catalog",
        scenario_pack_id="coding-agent-v1-core",
    )

    called: dict[str, object] = {}

    def fake_run_eval_scenario_pack(path: Path, base_session_dir: Path, *, artifact_dir: Path | None = None, run_label: str | None = None):
        called["path"] = path
        called["base_session_dir"] = base_session_dir
        called["artifact_dir"] = artifact_dir
        called["run_label"] = run_label
        return summary

    monkeypatch.setattr(cli, "run_eval_scenario_pack", fake_run_eval_scenario_pack)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--eval-label",
            "catalog",
            "--run-eval-pack",
            str(tmp_path / "pack.json"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["path"] == tmp_path / "pack.json"
    assert called["base_session_dir"] == tmp_path / "sessions"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["run_label"] == "catalog"
    assert "scenario_pack_id: coding-agent-v1-core" in output
    assert "task_class_summary:" in output
    assert "fix: passed=1/1 failed=0" in output
    assert "failure_mode_summary:" in output
    assert "no_op: passed=1/1 failed=0" in output


def test_cli_run_eval_pack_smoke_catalog_prints_smoke_pack_id(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalSummary(
        total=5,
        passed=5,
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
                severity="smoke",
                failure_modes=("no_op",),
                tags=("repair",),
            ),
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke-v1",
        scenario_pack_id="coding-agent-v1-smoke",
    )

    monkeypatch.setattr(cli, "run_eval_scenario_pack", lambda *args, **kwargs: summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--run-eval-pack",
            str(Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "smoke-v1.json"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "scenario_pack_id: coding-agent-v1-smoke" in output


def test_cli_run_eval_pack_stress_catalog_prints_stress_pack_id(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalSummary(
        total=5,
        passed=5,
        failed=0,
        results=[
            EvalResult(
                scenario_name="diagnose-003",
                passed=True,
                session_id="s1",
                status="failed",
                final_report="ok",
                outcome_reason="stopped at approval boundary",
                duration_seconds=1.0,
                task_class="diagnose",
                severity="core",
                failure_modes=("unsafe_action",),
                tags=("approval",),
            ),
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="stress-v1",
        scenario_pack_id="coding-agent-v1-stress",
    )

    monkeypatch.setattr(cli, "run_eval_scenario_pack", lambda *args, **kwargs: summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--run-eval-pack",
            str(Path(__file__).resolve().parents[3] / "evals" / "coding-agent-v1" / "scenarios" / "stress-v1.json"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "scenario_pack_id: coding-agent-v1-stress" in output


def test_cli_run_evals_uses_default_external_pack(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalSummary(
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
                severity="smoke",
                failure_modes=("no_op",),
                tags=("repair",),
            ),
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="default-pack",
        scenario_pack_id="coding-agent-v1-core",
    )

    called: dict[str, object] = {}

    def fake_run_eval_scenario_pack(path: Path, base_session_dir: Path, *, artifact_dir: Path | None = None, run_label: str | None = None):
        called["path"] = path
        called["base_session_dir"] = base_session_dir
        called["artifact_dir"] = artifact_dir
        called["run_label"] = run_label
        return summary

    monkeypatch.setattr(cli, "run_eval_scenario_pack", fake_run_eval_scenario_pack)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--eval-label",
            "default-pack",
            "--run-evals",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["path"] == cli._default_eval_pack_path()
    assert called["base_session_dir"] == tmp_path / "sessions"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["run_label"] == "default-pack"
    assert "scenario_pack_id: coding-agent-v1-core" in output


def test_cli_run_smoke_evals_uses_builtin_suite(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[
            EvalResult(
                scenario_name="failing_test_repair",
                passed=True,
                session_id="s1",
                status="completed",
                final_report="ok",
                outcome_reason="repair ok",
                duration_seconds=1.0,
                task_class="fix",
                severity="smoke",
                failure_modes=("no_op",),
                tags=("repair",),
            ),
        ],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="smoke",
        scenario_pack_id="built-in",
    )

    called: dict[str, object] = {}

    def fake_run_eval_suite(base_session_dir: Path, *, artifact_dir: Path | None = None, run_label: str | None = None):
        called["base_session_dir"] = base_session_dir
        called["artifact_dir"] = artifact_dir
        called["run_label"] = run_label
        return summary

    monkeypatch.setattr(cli, "run_eval_suite", fake_run_eval_suite)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--eval-label",
            "smoke",
            "--run-smoke-evals",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["base_session_dir"] == tmp_path / "sessions"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["run_label"] == "smoke"
    assert "scenario_pack_id: built-in" in output


def test_cli_compare_evals_prints_task_class_comparison_breakdown(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "baseline.json"
    candidate_path = tmp_path / "candidate.json"
    comparison = EvalComparisonSummary(
        baseline_artifact_path=baseline_path,
        candidate_artifact_path=candidate_path,
        baseline_scenario_pack_id="coding-agent-v1-core",
        candidate_scenario_pack_id="coding-agent-v1-stress",
        regressions=1,
        improvements=0,
        unchanged=0,
        results=[
            EvalComparisonResult(
                scenario_name="fix-001",
                task_class="fix",
                baseline_passed=True,
                candidate_passed=False,
                classification="regression",
                duration_delta_seconds=0.5,
                baseline_reason="ok",
                candidate_reason="regressed",
                failure_modes=("no_op",),
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
    )

    monkeypatch.setattr(cli, "load_eval_summary", lambda path: object())
    monkeypatch.setattr(cli, "resolve_eval_artifact_reference", lambda ref, artifact_dir: tmp_path / f"{ref}.json")
    monkeypatch.setattr(cli, "compare_eval_summaries", lambda baseline, candidate: comparison)
    monkeypatch.setattr(cli, "write_eval_comparison_summary", lambda summary, artifact_dir: artifact_dir / "comparison.json")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--compare-evals",
            "baseline",
            "candidate",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "regressions: 1" in output
    assert "baseline_scenario_pack_id: coding-agent-v1-core" in output
    assert "candidate_scenario_pack_id: coding-agent-v1-stress" in output
    assert "task_class_comparison_summary:" in output
    assert "fix: regressions=1 improvements=0 unchanged=0" in output


def test_cli_rejects_multiple_eval_mode_flags_together(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--run-evals",
            "--run-smoke-evals",
            "--run-eval-pack",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--run-evals, --run-smoke-evals, and --run-eval-pack are mutually exclusive" in err


def test_cli_list_evals_applies_eval_pack_filter(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    index = EvalArtifactIndex(
        artifact_dir=tmp_path / "artifacts",
        pack_counts={
            "built-in": 1,
            "coding-agent-v1-stress": 1,
        },
        entries=[
            EvalArtifactIndexEntry(
                artifact_path=tmp_path / "eval-summary-a.json",
                created_at="2026-08-09T00:00:00+00:00",
                run_label="built-in-v1",
                scenario_pack_id="built-in",
                passed=17,
                total=17,
                pass_rate=100.0,
            ),
            EvalArtifactIndexEntry(
                artifact_path=tmp_path / "eval-summary-b.json",
                created_at="2026-08-09T01:00:00+00:00",
                run_label="stress-v1",
                scenario_pack_id="coding-agent-v1-stress",
                passed=5,
                total=5,
                pass_rate=100.0,
            ),
        ],
    )

    called: dict[str, object] = {}

    monkeypatch.setattr(cli, "build_eval_artifact_index", lambda artifact_dir: index)

    def fake_filter_eval_artifact_index(received_index, selectors):
        called["index"] = received_index
        called["selectors"] = selectors
        return EvalArtifactIndex(
            artifact_dir=received_index.artifact_dir,
            pack_counts={"coding-agent-v1-stress": 1},
            entries=[received_index.entries[1]],
        )

    monkeypatch.setattr(cli, "filter_eval_artifact_index", fake_filter_eval_artifact_index)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--list-evals",
            str(tmp_path / "artifacts"),
            "--eval-pack-filter",
            "stress",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["index"] is index
    assert called["selectors"] == ["stress"]
    assert "coding-agent-v1-stress: 1" in output


def test_cli_history_evals_applies_eval_pack_filter(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    built_in = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[],
        created_at="2026-08-09T00:00:00+00:00",
        run_label="built-in-v1",
        artifact_path=tmp_path / "built-in.json",
        scenario_pack_id="built-in",
    )
    stress = EvalSummary(
        total=1,
        passed=1,
        failed=0,
        results=[],
        created_at="2026-08-09T01:00:00+00:00",
        run_label="stress-v1",
        artifact_path=tmp_path / "stress.json",
        scenario_pack_id="coding-agent-v1-stress",
    )
    history = EvalHistorySummary(
        artifact_paths=[stress.artifact_path],
        pack_counts={"coding-agent-v1-stress": 1},
        scenario_trends=[
            EvalScenarioTrend(
                scenario_name="diagnose-003",
                runs=1,
                pass_count=1,
                fail_count=0,
                latest_passed=True,
                latest_duration_seconds=1.0,
                average_duration_seconds=1.0,
                trend="insufficient-data",
                history=[
                    EvalHistoryEntry(
                        artifact_path=stress.artifact_path,
                        created_at="2026-08-09T01:00:00+00:00",
                        run_label="stress-v1",
                        scenario_pack_id="coding-agent-v1-stress",
                        passed=True,
                        duration_seconds=1.0,
                        outcome_reason="ok",
                    )
                ],
            )
        ],
    )

    called: dict[str, object] = {}
    summaries_by_path = {
        tmp_path / "built-in.json": built_in,
        tmp_path / "stress.json": stress,
    }

    monkeypatch.setattr(cli, "resolve_eval_artifact_reference", lambda ref, artifact_dir: tmp_path / f"{ref}.json")
    monkeypatch.setattr(cli, "load_eval_summary", lambda path: summaries_by_path[path])

    def fake_filter_eval_summaries_by_pack(summaries, selectors):
        called["summaries"] = summaries
        called["selectors"] = selectors
        return [stress]

    monkeypatch.setattr(cli, "filter_eval_summaries_by_pack", fake_filter_eval_summaries_by_pack)
    monkeypatch.setattr(cli, "build_eval_history", lambda summaries: history)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--history-evals",
            "built-in",
            "stress",
            "--eval-pack-filter",
            "stress",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["summaries"] == [built_in, stress]
    assert called["selectors"] == ["stress"]
    assert "coding-agent-v1-stress: 1" in output


def test_cli_rejects_eval_pack_filter_without_list_or_history(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--eval-pack-filter",
            "stress",
            "--run-evals",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--eval-pack-filter can only be used with --list-evals or --history-evals" in err


def test_cli_repair_eval_baseline_uses_default_reference(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    called: dict[str, object] = {}

    def fake_repair_eval_baseline_reference(artifact_dir: Path, name: str, *, reference: str | None = None):
        called["artifact_dir"] = artifact_dir
        called["name"] = name
        called["reference"] = reference
        return tmp_path / "repaired.json", tmp_path / "named-baselines.json", "latest-pass:coding-agent-v1-smoke"

    monkeypatch.setattr(cli, "repair_eval_baseline_reference", fake_repair_eval_baseline_reference)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--repair-eval-baseline",
            "smoke-main",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["name"] == "smoke-main"
    assert called["reference"] is None
    assert "repaired_baseline: smoke-main" in output
    assert "reference_used: latest-pass:coding-agent-v1-smoke" in output


def test_cli_repair_eval_baseline_accepts_explicit_reference(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    called: dict[str, object] = {}

    def fake_repair_eval_baseline_reference(artifact_dir: Path, name: str, *, reference: str | None = None):
        called["artifact_dir"] = artifact_dir
        called["name"] = name
        called["reference"] = reference
        return tmp_path / "repaired.json", tmp_path / "named-baselines.json", "main-v2"

    monkeypatch.setattr(cli, "repair_eval_baseline_reference", fake_repair_eval_baseline_reference)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--repair-eval-baseline",
            "main",
            "main-v2",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["name"] == "main"
    assert called["reference"] == "main-v2"
    assert "repaired_baseline: main" in output
    assert "reference_used: main-v2" in output


def test_cli_audit_eval_baselines_prints_summary(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalBaselineAuditSummary(
        artifact_dir=tmp_path / "artifacts",
        entries=[
            EvalBaselineAuditEntry(
                name="main",
                artifact_path=tmp_path / "baseline.json",
                status="stale",
                scenario_pack_id="coding-agent-v1-core",
                recommended_reference="latest-pass:coding-agent-v1-core",
                recommended_artifact_path=tmp_path / "latest.json",
            )
        ],
    )

    monkeypatch.setattr(cli, "load_eval_baseline_config", lambda artifact_dir: object())
    monkeypatch.setattr(cli, "build_eval_baseline_audit_summary", lambda config: summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--audit-eval-baselines",
            str(tmp_path / "artifacts"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "baselines: 1" in output
    assert "main:" in output
    assert "status=stale" in output
    assert "recommended_reference=latest-pass:coding-agent-v1-core" in output


def test_cli_prune_evals_prints_plan_without_deleting(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalArtifactPruneSummary(
        artifact_dir=tmp_path / "artifacts",
        keep_per_pack=1,
        protected_count=1,
        prunable_count=1,
        entries=[
            EvalArtifactPruneEntry(
                artifact_path=tmp_path / "old.json",
                action="prune",
                reasons=(),
                scenario_pack_id="built-in",
                run_label="old",
            ),
            EvalArtifactPruneEntry(
                artifact_path=tmp_path / "new.json",
                action="protect",
                reasons=("latest-pack:built-in:1",),
                scenario_pack_id="built-in",
                run_label="new",
            ),
        ],
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(cli, "build_eval_artifact_prune_summary", lambda artifact_dir, keep_per_pack=1: summary)

    def fake_apply_eval_artifact_prune_summary(received_summary):
        called["applied"] = True
        return []

    monkeypatch.setattr(cli, "apply_eval_artifact_prune_summary", fake_apply_eval_artifact_prune_summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-evals",
            str(tmp_path / "artifacts"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "prunable: 1" in output
    assert "old.json: action=prune" in output
    assert "deleted:" not in output
    assert "applied" not in called


def test_cli_prune_evals_apply_deletes_reported_artifacts(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalArtifactPruneSummary(
        artifact_dir=tmp_path / "artifacts",
        keep_per_pack=1,
        protected_count=1,
        prunable_count=1,
        entries=[],
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(cli, "build_eval_artifact_prune_summary", lambda artifact_dir, keep_per_pack=1: summary)

    def fake_apply_eval_artifact_prune_summary(received_summary):
        called["summary"] = received_summary
        return [tmp_path / "old.json"]

    monkeypatch.setattr(cli, "apply_eval_artifact_prune_summary", fake_apply_eval_artifact_prune_summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-evals",
            str(tmp_path / "artifacts"),
            "--prune-evals-apply",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["summary"] is summary
    assert "deleted: 1" in output
    assert f"deleted_artifact: {tmp_path / 'old.json'}" in output


def test_cli_rejects_prune_apply_without_prune(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-evals-apply",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--prune-evals-apply requires --prune-evals" in err
