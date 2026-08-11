from __future__ import annotations

from pathlib import Path
import sys

from coding_agent_v1 import cli
from coding_agent_v1.models import (
    CompactContextArtifact,
    CompactContextIndexEntry,
    CompactContextPruneEntry,
    CompactContextPruneSummary,
    HandoffArtifact,
    ProceduralRepairRecord,
    ProceduralRepairStatusAudit,
    SessionRecord,
    SessionStatus,
    TaskFlow,
)
from coding_agent_v1.eval_harness import (
    EvalDecisionArtifactIndex,
    EvalDecisionArtifactIndexEntry,
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
    EvalExpectationCheckComparisonEntry,
    EvalHistoryEntry,
    EvalHistorySummary,
    EvalPromotionDecision,
    EvalResult,
    EvalScenarioTrend,
    EvalSummary,
    EvalTraceAggregateEntry,
    EvalTraceAggregateComparisonEntry,
    EvalTraceTransitionHeatmapComparisonRow,
    EvalTraceTransitionHeatmapRow,
    EvalTraceSummaryEntry,
)


def test_build_parser_help_documents_eval_reference_aliases() -> None:
    help_text = cli.build_parser().format_help()

    assert "latest-clean            newest fully passing run with no expectation mismatches" in help_text
    assert "latest-clean[:PACK]" in help_text
    assert "latest-pass[:PACK]" in help_text
    assert "baseline:<NAME>" in help_text
    assert "Use latest-clean[:PACK]" in help_text
    assert "newest fully clean run" in help_text
    assert "favoring" in help_text
    assert "latest-clean before latest-pass" in help_text
    assert "Defaults to latest-comparison." in help_text
    assert "Defaults to latest-promotion." in help_text
    assert "Filter --list-decision-artifacts or --prune-decision-" in help_text
    assert "decision kind when using --prune-decision-artifacts." in help_text


def test_cli_review_handoff_prints_summary(monkeypatch, capsys, tmp_path: Path) -> None:
    handoff = HandoffArtifact(
        session_id="s1",
        request="run tests",
        workspace_root=str(tmp_path),
        status="failed",
        reason="approval_required",
        task_flow="fix",
        belief=["task_flow=fix"],
        progress=["next=approve validation"],
        blocker="approval required",
        next_step="approve validation",
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def load_handoff(self, session_id: str) -> HandoffArtifact:
            assert session_id == "s1"
            return handoff

        def build_handoff_review_summary(self, artifact: HandoffArtifact) -> str:
            assert artifact is handoff
            return "handoff_session_id: s1\nreason: approval_required"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-handoff",
            "s1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "handoff_session_id: s1" in output
    assert "reason: approval_required" in output


def test_cli_review_compact_context_prints_summary(monkeypatch, capsys, tmp_path: Path) -> None:
    compact_context = CompactContextArtifact(
        session_id="s1",
        request="summarize this repo",
        workspace_root=str(tmp_path),
        status="completed",
        task_flow="inspect",
        belief=["task_flow=inspect"],
        progress=["next=review"],
        summary="compact summary",
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def load_compact_context(self, session_id: str) -> CompactContextArtifact:
            assert session_id == "s1"
            return compact_context

        def build_compact_context_review_summary(self, artifact: CompactContextArtifact) -> str:
            assert artifact is compact_context
            return "compact_session_id: s1\nsummary: compact summary"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-compact-context",
            "s1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "compact_session_id: s1" in output
    assert "summary: compact summary" in output


def test_cli_list_compact_contexts_prints_index(monkeypatch, capsys, tmp_path: Path) -> None:
    entries = [
        CompactContextIndexEntry(
            artifact_path=tmp_path / "sessions" / "compactions" / "s1.compact.json",
            session_id="s1",
            status="completed",
            task_flow="inspect",
            compaction_trigger="checkpoint",
            source_event_count=3,
            source_context_chars=120,
            modified_at=1.0,
        )
    ]

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def list_compact_context_index(self):
            return entries

        def summarize_compact_context_index(self, loaded):
            assert loaded is entries
            return "compact_contexts: 1\ns1: trigger=checkpoint"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--list-compact-contexts",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "compact_contexts: 1" in output
    assert "trigger=checkpoint" in output


def test_cli_prune_compact_contexts_prints_plan_without_deleting(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = CompactContextPruneSummary(
        base_dir=tmp_path / "sessions",
        keep_newest=1,
        include_size_triggered=False,
        kept_count=1,
        prunable_count=1,
        entries=[
            CompactContextPruneEntry(
                artifact_path=tmp_path / "sessions" / "compactions" / "s1.compact.json",
                session_id="s1",
                compaction_trigger="checkpoint",
                modified_at=1.0,
                action="prune",
                reason="old",
            )
        ],
    )
    called: dict[str, object] = {}

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def build_compact_context_prune_summary(
            self,
            *,
            keep_newest: int = 20,
            include_size_triggered: bool = False,
        ):
            called["keep_newest"] = keep_newest
            called["include_size_triggered"] = include_size_triggered
            return summary

        def summarize_compact_context_prune_summary(self, loaded):
            assert loaded is summary
            return "compact_context_prune_plan\ns1.compact.json: action=prune"

        def apply_compact_context_prune_summary(self, loaded):
            raise AssertionError("dry run should not delete")

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--prune-compact-contexts",
            "--prune-compact-keep-newest",
            "1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["keep_newest"] == 1
    assert called["include_size_triggered"] is False
    assert "action=prune" in output


def test_cli_prune_compact_contexts_apply_deletes_reported_artifacts(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    path = tmp_path / "sessions" / "compactions" / "s1.compact.json"
    summary = CompactContextPruneSummary(
        base_dir=tmp_path / "sessions",
        keep_newest=1,
        include_size_triggered=True,
        kept_count=0,
        prunable_count=1,
        entries=[],
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def build_compact_context_prune_summary(
            self,
            *,
            keep_newest: int = 20,
            include_size_triggered: bool = False,
        ):
            assert include_size_triggered is True
            return summary

        def summarize_compact_context_prune_summary(self, loaded):
            assert loaded is summary
            return "compact_context_prune_plan"

        def apply_compact_context_prune_summary(self, loaded):
            assert loaded is summary
            return [path]

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--prune-compact-contexts",
            "--prune-compact-contexts-apply",
            "--prune-compact-include-size-triggered",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "deleted: 1" in output
    assert f"deleted_path: {path}" in output


def test_cli_rejects_prune_compact_keep_newest_less_than_one(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-compact-contexts",
            "--prune-compact-keep-newest",
            "0",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--prune-compact-keep-newest must be at least 1" in err


def test_cli_resume_handoff_passes_handoff_id_to_run_session(monkeypatch, capsys, tmp_path: Path) -> None:
    called: dict[str, object] = {}

    def fake_run_session(
        request: str,
        start_path: Path,
        store,
        *,
        auto_approve_commands: bool = False,
        resume_from_session_id: str | None = None,
        resume_from_handoff_id: str | None = None,
        planner_strategy: str | None = None,
    ) -> SessionRecord:
        called["request"] = request
        called["start_path"] = start_path
        called["auto_approve_commands"] = auto_approve_commands
        called["resume_from_session_id"] = resume_from_session_id
        called["resume_from_handoff_id"] = resume_from_handoff_id
        called["planner_strategy"] = planner_strategy
        return SessionRecord(
            session_id="s2",
            request=request,
            workspace_root=start_path,
            task_flow=TaskFlow.INSPECT,
            resumed_from_session_id=resume_from_handoff_id,
            status=SessionStatus.COMPLETED,
            final_report="continued",
        )

    monkeypatch.setattr(cli, "run_session", fake_run_session)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--cwd",
            str(tmp_path),
            "--session-dir",
            str(tmp_path / "sessions"),
            "--resume-handoff",
            "s1",
            "continue the task",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["request"] == "continue the task"
    assert called["start_path"] == tmp_path
    assert called["resume_from_session_id"] is None
    assert called["resume_from_handoff_id"] == "s1"
    assert called["planner_strategy"] == "deterministic_heuristic"
    assert "resumed_from: s1" in output


def test_cli_rejects_unsupported_planner_strategy(monkeypatch, capsys, tmp_path: Path) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--cwd",
            str(tmp_path),
            "--session-dir",
            str(tmp_path / "sessions"),
            "--planner-strategy",
            "model_preview",
            "summarize this repo",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "unsupported planner strategy" in err


def test_cli_rejects_eval_planner_strategy_without_eval_run(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--eval-planner-strategy",
            "model_guided",
            "summarize this repo",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--eval-planner-strategy can only be used with --run-evals or --run-eval-pack" in err


def test_cli_rejects_unconfigured_model_guided_planner_strategy(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", raising=False)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--cwd",
            str(tmp_path),
            "--session-dir",
            str(tmp_path / "sessions"),
            "--planner-strategy",
            "model_guided",
            "summarize this repo",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "requires CODING_AGENT_V1_MODEL_PLANNER_COMMAND" in err
    assert "no tool action was taken" in err


def test_cli_rejects_session_and_handoff_resume_together(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--resume-session",
            "s1",
            "--resume-handoff",
            "s2",
            "continue",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--resume-session and --resume-handoff are mutually exclusive" in err


def test_cli_review_repair_record_prints_summary(monkeypatch, capsys, tmp_path: Path) -> None:
    repair = ProceduralRepairRecord(
        repair_id="r1",
        source_session_id="s1",
        task_class="fix",
        trigger_condition="validation failed",
        failure_pattern="validation_failed",
        recommended_recovery="inspect failure output",
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def load_procedural_repair_record(self, repair_id: str) -> ProceduralRepairRecord:
            assert repair_id == "r1"
            return repair

        def build_procedural_repair_review_summary(self, loaded: ProceduralRepairRecord) -> str:
            assert loaded is repair
            return "repair_id: r1\nfailure_pattern: validation_failed"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-repair-record",
            "r1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "repair_id: r1" in output
    assert "failure_pattern: validation_failed" in output


def test_cli_list_repair_records_prints_compact_index(monkeypatch, capsys, tmp_path: Path) -> None:
    repairs = [
        ProceduralRepairRecord(
            repair_id="r1",
            source_session_id="s1",
            task_class="fix",
            trigger_condition="validation failed",
            failure_pattern="validation_failed",
            recommended_recovery="inspect failure output",
        )
    ]

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def list_procedural_repair_records(self):
            return repairs

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--list-repair-records",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "repair_records: 1" in output
    assert "r1: task_class=fix status=candidate failure_pattern=validation_failed" in output


def test_cli_set_repair_record_status_prints_updated_summary(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    repair = ProceduralRepairRecord(
        repair_id="r1",
        source_session_id="s1",
        task_class="fix",
        trigger_condition="validation failed",
        failure_pattern="validation_failed",
        recommended_recovery="inspect failure output",
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def update_procedural_repair_status(
            self,
            repair_id: str,
            status: str,
            *,
            actor: str = "cli",
            reason: str = "",
        ) -> ProceduralRepairRecord:
            assert repair_id == "r1"
            assert status == "accepted"
            assert actor == "reviewer"
            assert reason == "validated repeated fix"
            repair.status = status
            return repair

        def build_procedural_repair_review_summary(self, loaded: ProceduralRepairRecord) -> str:
            assert loaded is repair
            return "repair_id: r1\nstatus: accepted"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--set-repair-record-status",
            "r1",
            "accepted",
            "--repair-status-actor",
            "reviewer",
            "--repair-status-reason",
            "validated repeated fix",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "repair_id: r1" in output
    assert "status: accepted" in output


def test_cli_list_repair_status_audits_prints_compact_index(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    audits = [
        ProceduralRepairStatusAudit(
            audit_id="a1",
            repair_id="r1",
            previous_status="candidate",
            new_status="accepted",
            actor="reviewer",
            reason="validated",
        )
    ]

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def list_procedural_repair_status_audits(self, *, repair_id: str | None = None):
            assert repair_id == "r1"
            return audits

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--list-repair-status-audits",
            "r1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "repair_status_audits: 1" in output
    assert "a1: repair_id=r1 candidate->accepted actor=reviewer" in output


def test_cli_review_repair_status_audit_prints_summary(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    audit = ProceduralRepairStatusAudit(
        audit_id="a1",
        repair_id="r1",
        previous_status="candidate",
        new_status="accepted",
        actor="reviewer",
        reason="validated",
    )

    class FakeStore:
        def __init__(self, base_dir: Path) -> None:
            self.base_dir = base_dir

        def load_procedural_repair_status_audit(self, audit_id: str) -> ProceduralRepairStatusAudit:
            assert audit_id == "a1"
            return audit

        def build_procedural_repair_status_audit_review_summary(
            self,
            loaded: ProceduralRepairStatusAudit,
        ) -> str:
            assert loaded is audit
            return "audit_id: a1\nrepair_id: r1\nnew_status: accepted"

    monkeypatch.setattr(cli, "SessionStore", FakeStore)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-repair-status-audit",
            "a1",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "audit_id: a1" in output
    assert "new_status: accepted" in output


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

    def fake_run_eval_scenario_pack(
        path: Path,
        base_session_dir: Path,
        *,
        artifact_dir: Path | None = None,
        run_label: str | None = None,
        planner_strategy_override: str | None = None,
    ):
        called["path"] = path
        called["base_session_dir"] = base_session_dir
        called["artifact_dir"] = artifact_dir
        called["run_label"] = run_label
        called["planner_strategy_override"] = planner_strategy_override
        return summary

    monkeypatch.setattr(cli, "run_eval_scenario_pack", fake_run_eval_scenario_pack)
    monkeypatch.setattr(cli, "build_eval_trace_summary", lambda summary: ["trace-summary"])
    monkeypatch.setattr(
        cli,
        "build_eval_expectation_check_summary",
        lambda label, entries: type(
            "ExpectationSummary",
            (),
            {
                "matched": 2 if label == "tool_sequence" else 1,
                "total": 2,
                "unmatched_scenario_names": () if label == "tool_sequence" else ("feature-001",),
            },
        )(),
    )
    monkeypatch.setattr(
        cli,
        "summarize_eval_trace_summary",
        lambda entries: (
            "trace_count: 2\n"
            "primary_failure_modes:\n"
            "  none: count=2 scenarios=feature-001,fix-001\n"
            "failure_transitions:\n"
            "  parse_request->generate_tool_arguments: count=1 scenarios=feature-001"
        ),
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--eval-label",
            "catalog",
            "--eval-planner-strategy",
            "model_guided",
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
    assert called["planner_strategy_override"] == "model_guided"
    assert "scenario_pack_id: coding-agent-v1-core" in output
    assert "task_class_summary:" in output
    assert "fix: passed=1/1 failed=0" in output
    assert "failure_mode_summary:" in output
    assert "no_op: passed=1/1 failed=0" in output
    assert "trace_summary:" in output
    assert "trace_count: 2" in output
    assert "failure_transitions:" in output
    assert "parse_request->generate_tool_arguments: count=1 scenarios=feature-001" in output
    assert "tool_sequence_expectation_summary:" in output
    assert "matched=2/2 unmatched=" in output
    assert "escalation_expectation_summary:" in output
    assert "matched=1/2 unmatched=feature-001" in output


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
            str(Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "smoke-v1.json"),
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
            str(Path(__file__).resolve().parents[3] / "coding-agents" / "evals" / "scenarios" / "stress-v1.json"),
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

    def fake_run_eval_scenario_pack(
        path: Path,
        base_session_dir: Path,
        *,
        artifact_dir: Path | None = None,
        run_label: str | None = None,
        planner_strategy_override: str | None = None,
    ):
        called["path"] = path
        called["base_session_dir"] = base_session_dir
        called["artifact_dir"] = artifact_dir
        called["run_label"] = run_label
        called["planner_strategy_override"] = planner_strategy_override
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
    assert called["planner_strategy_override"] is None
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
        expectation_regressions=0,
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
        trace_transition_failure_comparison=[
            EvalTraceAggregateComparisonEntry(
                label="execute_tool->handle_tool_output",
                baseline_count=0,
                candidate_count=1,
                delta=1,
                baseline_scenario_names=(),
                candidate_scenario_names=("fix-001",),
            )
        ],
        trace_transition_failure_heatmap_comparison=[
            EvalTraceTransitionHeatmapComparisonRow(
                from_state="execute_tool",
                baseline_total_count=0,
                candidate_total_count=1,
                delta_total_count=1,
                baseline_counts_by_to_state={"handle_tool_output": 0},
                candidate_counts_by_to_state={"handle_tool_output": 1},
                delta_by_to_state={"handle_tool_output": 1},
            )
        ],
        tool_sequence_expectation_comparison=[
            EvalExpectationCheckComparisonEntry(
                label="tool_sequence",
                baseline_matched=1,
                baseline_total=1,
                candidate_matched=0,
                candidate_total=1,
                matched_delta=-1,
                baseline_unmatched_scenario_names=(),
                candidate_unmatched_scenario_names=("fix-001",),
            )
        ],
        escalation_expectation_comparison=[
            EvalExpectationCheckComparisonEntry(
                label="escalation",
                baseline_matched=1,
                baseline_total=1,
                candidate_matched=1,
                candidate_total=1,
                matched_delta=0,
                baseline_unmatched_scenario_names=(),
                candidate_unmatched_scenario_names=(),
            )
        ],
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
    assert "trace_transition_failure_comparison:" in output
    assert (
        "execute_tool->handle_tool_output: baseline=0 candidate=1 delta=1 "
        "baseline_scenarios= candidate_scenarios=fix-001"
    ) in output
    assert "trace_transition_failure_heatmap_comparison:" in output
    assert (
        "from=execute_tool baseline_total=0 candidate_total=1 delta_total=1 "
        "baseline[handle_tool_output=0] candidate[handle_tool_output=1] delta[handle_tool_output=1]"
    ) in output
    assert "task_class_comparison_summary:" in output
    assert "fix: regressions=1 improvements=0 unchanged=0" in output
    assert "tool_sequence_expectation_comparison_summary:" in output
    assert "tool_sequence: baseline=1/1 candidate=0/1 matched_delta=-1" in output
    assert "escalation_expectation_comparison_summary:" in output
    assert "escalation: baseline=1/1 candidate=1/1 matched_delta=0" in output


def test_cli_review_eval_comparison_prints_summary(monkeypatch, capsys, tmp_path: Path) -> None:
    comparison = EvalComparisonSummary(
        baseline_artifact_path=tmp_path / "baseline.json",
        candidate_artifact_path=tmp_path / "candidate.json",
        baseline_scenario_pack_id="coding-agent-v1-core",
        candidate_scenario_pack_id="coding-agent-v1-core",
        regressions=1,
        expectation_regressions=0,
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
                candidate_reason="bad output",
                failure_modes=("bad_outcome",),
            )
        ],
        created_at="2026-08-09T00:00:00+00:00",
        trace_transition_failure_comparison=[
            EvalTraceAggregateComparisonEntry(
                label="execute_tool->handle_tool_output",
                baseline_count=0,
                candidate_count=1,
                delta=1,
                baseline_scenario_names=(),
                candidate_scenario_names=("fix-001",),
            )
        ],
    )

    called: dict[str, Path] = {}

    def fake_resolve_decision_artifact_reference(reference: str, artifact_dir: Path, *, artifact_kind: str | None = None):
        called["reference"] = reference
        called["artifact_dir"] = artifact_dir
        called["artifact_kind"] = artifact_kind
        return tmp_path / "decision-artifacts" / "eval-comparison-1.json"

    def fake_load_eval_comparison_summary(path: Path):
        called["path"] = path
        return comparison

    monkeypatch.setattr(cli, "resolve_decision_artifact_reference", fake_resolve_decision_artifact_reference)
    monkeypatch.setattr(cli, "load_eval_comparison_summary", fake_load_eval_comparison_summary)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-eval-comparison",
            "latest-comparison",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["reference"] == "latest-comparison"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["artifact_kind"] == "comparison"
    assert called["path"] == tmp_path / "decision-artifacts" / "eval-comparison-1.json"
    assert "regressions: 1" in output
    assert "trace_transition_failure_comparison:" in output
    assert "task_class_comparison_summary:" in output


def test_cli_review_eval_comparison_defaults_to_latest_alias(monkeypatch, capsys, tmp_path: Path) -> None:
    comparison = EvalComparisonSummary(
        baseline_artifact_path=tmp_path / "baseline.json",
        candidate_artifact_path=tmp_path / "candidate.json",
        baseline_scenario_pack_id="coding-agent-v1-core",
        candidate_scenario_pack_id="coding-agent-v1-core",
        regressions=0,
        expectation_regressions=0,
        improvements=0,
        unchanged=1,
        results=[],
        created_at="2026-08-09T00:00:00+00:00",
    )
    called: dict[str, object] = {}

    def fake_resolve_decision_artifact_reference(reference: str, artifact_dir: Path, *, artifact_kind: str | None = None):
        called["reference"] = reference
        called["artifact_dir"] = artifact_dir
        called["artifact_kind"] = artifact_kind
        return tmp_path / "decision-artifacts" / "eval-comparison-1.json"

    monkeypatch.setattr(cli, "resolve_decision_artifact_reference", fake_resolve_decision_artifact_reference)
    monkeypatch.setattr(cli, "load_eval_comparison_summary", lambda path: comparison)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-eval-comparison",
        ],
    )

    cli.main()
    capsys.readouterr()

    assert called["reference"] == "latest-comparison"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["artifact_kind"] == "comparison"


def test_cli_review_eval_promotion_prints_summary(monkeypatch, capsys, tmp_path: Path) -> None:
    comparison = EvalComparisonSummary(
        baseline_artifact_path=tmp_path / "baseline.json",
        candidate_artifact_path=tmp_path / "candidate.json",
        baseline_scenario_pack_id="coding-agent-v1-core",
        candidate_scenario_pack_id="coding-agent-v1-core",
        regressions=0,
        expectation_regressions=0,
        improvements=1,
        unchanged=0,
        results=[],
        created_at="2026-08-09T00:00:00+00:00",
    )
    decision = EvalPromotionDecision(
        baseline_name="main",
        candidate_reference="main-v2",
        promoted=True,
        comparison=comparison,
        artifact_path=tmp_path / "candidate.json",
        config_path=tmp_path / "named-baselines.json",
        created_at="2026-08-09T00:01:00+00:00",
        decision_artifact_path=tmp_path / "decision-artifacts" / "eval-promotion-1.json",
    )

    called: dict[str, Path] = {}

    def fake_resolve_decision_artifact_reference(reference: str, artifact_dir: Path, *, artifact_kind: str | None = None):
        called["reference"] = reference
        called["artifact_dir"] = artifact_dir
        called["artifact_kind"] = artifact_kind
        return tmp_path / "decision-artifacts" / "eval-promotion-1.json"

    def fake_load_eval_promotion_decision(path: Path):
        called["path"] = path
        return decision

    monkeypatch.setattr(cli, "resolve_decision_artifact_reference", fake_resolve_decision_artifact_reference)
    monkeypatch.setattr(cli, "load_eval_promotion_decision", fake_load_eval_promotion_decision)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-eval-promotion",
            "latest-promotion",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["reference"] == "latest-promotion"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["artifact_kind"] == "promotion"
    assert called["path"] == tmp_path / "decision-artifacts" / "eval-promotion-1.json"
    assert "baseline_name: main" in output
    assert "promoted: True" in output
    assert "decision_artifact_path:" in output
    assert "improvements: 1" in output


def test_cli_review_eval_promotion_defaults_to_latest_alias(monkeypatch, capsys, tmp_path: Path) -> None:
    decision = EvalPromotionDecision(
        baseline_name="main",
        candidate_reference="main-v2",
        promoted=True,
        comparison=EvalComparisonSummary(
            baseline_artifact_path=tmp_path / "baseline.json",
            candidate_artifact_path=tmp_path / "candidate.json",
            baseline_scenario_pack_id="coding-agent-v1-core",
            candidate_scenario_pack_id="coding-agent-v1-core",
            regressions=0,
            expectation_regressions=0,
            improvements=1,
            unchanged=0,
            results=[],
            created_at="2026-08-09T00:00:00+00:00",
        ),
        artifact_path=tmp_path / "candidate.json",
        config_path=tmp_path / "named-baselines.json",
        created_at="2026-08-09T00:01:00+00:00",
        decision_artifact_path=tmp_path / "decision-artifacts" / "eval-promotion-1.json",
    )
    called: dict[str, object] = {}

    def fake_resolve_decision_artifact_reference(reference: str, artifact_dir: Path, *, artifact_kind: str | None = None):
        called["reference"] = reference
        called["artifact_dir"] = artifact_dir
        called["artifact_kind"] = artifact_kind
        return tmp_path / "decision-artifacts" / "eval-promotion-1.json"

    monkeypatch.setattr(cli, "resolve_decision_artifact_reference", fake_resolve_decision_artifact_reference)
    monkeypatch.setattr(cli, "load_eval_promotion_decision", lambda path: decision)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--session-dir",
            str(tmp_path / "sessions"),
            "--review-eval-promotion",
        ],
    )

    cli.main()
    capsys.readouterr()

    assert called["reference"] == "latest-promotion"
    assert called["artifact_dir"] == tmp_path / "sessions" / "eval-artifacts"
    assert called["artifact_kind"] == "promotion"


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


def test_cli_rejects_review_eval_comparison_and_promotion_together(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--review-eval-comparison",
            "comparison.json",
            "--review-eval-promotion",
            "promotion.json",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2

    err = capsys.readouterr().err
    assert "--review-eval-comparison and --review-eval-promotion are mutually exclusive" in err


def test_cli_rejects_decision_artifact_kind_without_list(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--decision-artifact-kind",
            "promotion",
            "--run-evals",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2

    err = capsys.readouterr().err
    assert (
        "--decision-artifact-kind can only be used with --list-decision-artifacts or --prune-decision-artifacts"
        in err
    )


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


def test_cli_list_decision_artifacts_prints_index(monkeypatch, capsys, tmp_path: Path) -> None:
    index = EvalDecisionArtifactIndex(
        artifact_dir=tmp_path / "artifacts" / "decision-artifacts",
        kind_counts={"comparison": 1, "promotion": 1},
        entries=[
            EvalDecisionArtifactIndexEntry(
                artifact_path=tmp_path / "artifacts" / "decision-artifacts" / "eval-promotion-1.json",
                artifact_kind="promotion",
                created_at="2026-08-09T01:00:00+00:00",
                promoted=True,
                referenced_artifact_paths=(tmp_path / "artifacts" / "eval-summary-a.json",),
            ),
            EvalDecisionArtifactIndexEntry(
                artifact_path=tmp_path / "artifacts" / "decision-artifacts" / "eval-comparison-1.json",
                artifact_kind="comparison",
                created_at="2026-08-09T00:00:00+00:00",
                promoted=None,
                referenced_artifact_paths=(tmp_path / "artifacts" / "eval-summary-b.json",),
            ),
        ],
    )

    called: dict[str, Path] = {}

    def fake_build_eval_decision_artifact_index(artifact_dir: Path):
        called["artifact_dir"] = artifact_dir
        return index

    monkeypatch.setattr(cli, "build_eval_decision_artifact_index", fake_build_eval_decision_artifact_index)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--list-decision-artifacts",
            str(tmp_path / "artifacts"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == tmp_path / "artifacts"
    assert "artifacts: 2" in output
    assert "kinds:" in output
    assert "  comparison: 1" in output
    assert "  promotion: 1" in output
    assert "promotion eval-promotion-1.json promoted=True" in output


def test_cli_list_decision_artifacts_applies_kind_filter(monkeypatch, capsys, tmp_path: Path) -> None:
    index = EvalDecisionArtifactIndex(
        artifact_dir=tmp_path / "artifacts" / "decision-artifacts",
        kind_counts={"comparison": 1, "promotion": 1},
        entries=[
            EvalDecisionArtifactIndexEntry(
                artifact_path=tmp_path / "artifacts" / "decision-artifacts" / "eval-promotion-1.json",
                artifact_kind="promotion",
                created_at="2026-08-09T01:00:00+00:00",
                promoted=True,
                referenced_artifact_paths=(),
            ),
            EvalDecisionArtifactIndexEntry(
                artifact_path=tmp_path / "artifacts" / "decision-artifacts" / "eval-comparison-1.json",
                artifact_kind="comparison",
                created_at="2026-08-09T00:00:00+00:00",
                promoted=None,
                referenced_artifact_paths=(),
            ),
        ],
    )

    called: dict[str, object] = {}

    monkeypatch.setattr(cli, "build_eval_decision_artifact_index", lambda artifact_dir: index)

    def fake_filter_eval_decision_artifact_index(received_index, artifact_kinds):
        called["index"] = received_index
        called["artifact_kinds"] = artifact_kinds
        return EvalDecisionArtifactIndex(
            artifact_dir=received_index.artifact_dir,
            kind_counts={"promotion": 1},
            entries=[received_index.entries[0]],
        )

    monkeypatch.setattr(cli, "filter_eval_decision_artifact_index", fake_filter_eval_decision_artifact_index)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--list-decision-artifacts",
            str(tmp_path / "artifacts"),
            "--decision-artifact-kind",
            "promotion",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["index"] is index
    assert called["artifact_kinds"] == ["promotion"]
    assert "  promotion: 1" in output
    assert "comparison" not in output


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
        transition_failure_summary=[
            EvalTraceAggregateEntry(
                label="execute_tool->handle_tool_output",
                count=1,
                scenario_names=("diagnose-003",),
            )
        ],
        transition_failure_heatmap=[
            EvalTraceTransitionHeatmapRow(
                from_state="execute_tool",
                total_count=1,
                counts_by_to_state={"handle_tool_output": 1},
                scenario_names_by_to_state={"handle_tool_output": ("diagnose-003",)},
            )
        ],
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
                latest_failure_transition="execute_tool->handle_tool_output",
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
    assert "failure_transitions:" in output
    assert "execute_tool->handle_tool_output: count=1 scenarios=diagnose-003" in output
    assert "failure_transition_heatmap:" in output
    assert "from=execute_tool total=1 handle_tool_output=1" in output
    assert "latest_failure_transition=execute_tool->handle_tool_output" in output


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


def test_cli_prune_decision_artifacts_prints_plan_without_deleting(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalDecisionArtifactPruneSummary(
        artifact_dir=tmp_path / "decision-artifacts",
        keep_per_kind=1,
        artifact_kinds=(),
        protected_count=1,
        prunable_count=1,
        entries=[
            EvalDecisionArtifactPruneEntry(
                artifact_path=tmp_path / "eval-comparison-old.json",
                artifact_kind="comparison",
                action="prune",
                reasons=(),
                referenced_artifact_paths=(),
            ),
            EvalDecisionArtifactPruneEntry(
                artifact_path=tmp_path / "eval-promotion-new.json",
                artifact_kind="promotion",
                action="protect",
                reasons=("latest-kind:promotion:1",),
                referenced_artifact_paths=(tmp_path / "eval-summary-new.json",),
            ),
        ],
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "build_eval_decision_artifact_prune_summary",
        lambda artifact_dir, keep_per_kind=1, keep_per_pack=1, artifact_kinds=None: summary,
    )

    def fake_apply_eval_decision_artifact_prune_summary(received_summary):
        called["applied"] = True
        return []

    monkeypatch.setattr(
        cli,
        "apply_eval_decision_artifact_prune_summary",
        fake_apply_eval_decision_artifact_prune_summary,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
            str(tmp_path / "artifacts"),
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert "prunable: 1" in output
    assert "kind=comparison action=prune" in output
    assert "deleted:" not in output
    assert "applied" not in called


def test_cli_prune_decision_artifacts_apply_deletes_reported_artifacts(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalDecisionArtifactPruneSummary(
        artifact_dir=tmp_path / "decision-artifacts",
        keep_per_kind=1,
        artifact_kinds=(),
        protected_count=1,
        prunable_count=1,
        entries=[],
    )
    called: dict[str, object] = {}

    monkeypatch.setattr(
        cli,
        "build_eval_decision_artifact_prune_summary",
        lambda artifact_dir, keep_per_kind=1, keep_per_pack=1, artifact_kinds=None: summary,
    )

    def fake_apply_eval_decision_artifact_prune_summary(received_summary):
        called["summary"] = received_summary
        return [tmp_path / "eval-comparison-old.json"]

    monkeypatch.setattr(
        cli,
        "apply_eval_decision_artifact_prune_summary",
        fake_apply_eval_decision_artifact_prune_summary,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
            str(tmp_path / "artifacts"),
            "--prune-decision-artifacts-apply",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["summary"] is summary
    assert "deleted: 1" in output
    assert f"deleted_artifact: {tmp_path / 'eval-comparison-old.json'}" in output


def test_cli_prune_decision_artifacts_forwards_custom_retention_args(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalDecisionArtifactPruneSummary(
        artifact_dir=tmp_path / "decision-artifacts",
        keep_per_kind=2,
        artifact_kinds=(),
        protected_count=0,
        prunable_count=0,
        entries=[],
    )
    called: dict[str, object] = {}

    def fake_build_eval_decision_artifact_prune_summary(
        artifact_dir: Path,
        keep_per_kind: int = 1,
        keep_per_pack: int = 1,
        artifact_kinds=None,
    ):
        called["artifact_dir"] = artifact_dir
        called["keep_per_kind"] = keep_per_kind
        called["keep_per_pack"] = keep_per_pack
        called["artifact_kinds"] = artifact_kinds
        return summary

    monkeypatch.setattr(
        cli,
        "build_eval_decision_artifact_prune_summary",
        fake_build_eval_decision_artifact_prune_summary,
    )
    monkeypatch.setattr(
        cli,
        "apply_eval_decision_artifact_prune_summary",
        lambda received_summary: [],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
            str(tmp_path / "artifacts"),
            "--prune-decision-keep-per-kind",
            "2",
            "--prune-keep-per-pack",
            "3",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == tmp_path / "artifacts"
    assert called["keep_per_kind"] == 2
    assert called["keep_per_pack"] == 3
    assert called["artifact_kinds"] is None
    assert "keep_per_kind: 2" in output


def test_cli_prune_decision_artifacts_uses_default_artifact_dir_when_omitted(
    monkeypatch,
    capsys,
) -> None:
    summary = EvalDecisionArtifactPruneSummary(
        artifact_dir=Path(".coding-agent-v1/sessions/eval-artifacts") / "decision-artifacts",
        keep_per_kind=1,
        artifact_kinds=(),
        protected_count=0,
        prunable_count=0,
        entries=[],
    )
    called: dict[str, object] = {}

    def fake_build_eval_decision_artifact_prune_summary(
        artifact_dir: Path,
        keep_per_kind: int = 1,
        keep_per_pack: int = 1,
        artifact_kinds=None,
    ):
        called["artifact_dir"] = artifact_dir
        called["keep_per_kind"] = keep_per_kind
        called["keep_per_pack"] = keep_per_pack
        called["artifact_kinds"] = artifact_kinds
        return summary

    monkeypatch.setattr(
        cli,
        "build_eval_decision_artifact_prune_summary",
        fake_build_eval_decision_artifact_prune_summary,
    )
    monkeypatch.setattr(
        cli,
        "apply_eval_decision_artifact_prune_summary",
        lambda received_summary: [],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == Path(".coding-agent-v1/sessions/eval-artifacts")
    assert called["keep_per_kind"] == 1
    assert called["keep_per_pack"] == 1
    assert called["artifact_kinds"] is None
    assert "artifact_dir: .coding-agent-v1/sessions/eval-artifacts/decision-artifacts" in output


def test_cli_prune_decision_artifacts_forwards_kind_filter(
    monkeypatch,
    capsys,
    tmp_path: Path,
) -> None:
    summary = EvalDecisionArtifactPruneSummary(
        artifact_dir=tmp_path / "decision-artifacts",
        keep_per_kind=1,
        artifact_kinds=("promotion",),
        protected_count=1,
        prunable_count=0,
        entries=[],
    )
    called: dict[str, object] = {}

    def fake_build_eval_decision_artifact_prune_summary(
        artifact_dir: Path,
        keep_per_kind: int = 1,
        keep_per_pack: int = 1,
        artifact_kinds=None,
    ):
        called["artifact_dir"] = artifact_dir
        called["keep_per_kind"] = keep_per_kind
        called["keep_per_pack"] = keep_per_pack
        called["artifact_kinds"] = artifact_kinds
        return summary

    monkeypatch.setattr(
        cli,
        "build_eval_decision_artifact_prune_summary",
        fake_build_eval_decision_artifact_prune_summary,
    )
    monkeypatch.setattr(
        cli,
        "apply_eval_decision_artifact_prune_summary",
        lambda received_summary: [],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
            str(tmp_path / "artifacts"),
            "--decision-artifact-kind",
            "promotion",
        ],
    )

    cli.main()
    output = capsys.readouterr().out

    assert called["artifact_dir"] == tmp_path / "artifacts"
    assert called["artifact_kinds"] == ["promotion"]
    assert "artifact_kinds: promotion" in output


def test_cli_rejects_prune_decision_apply_without_prune(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts-apply",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--prune-decision-artifacts-apply requires --prune-decision-artifacts" in err


def test_cli_rejects_prune_keep_per_pack_less_than_one(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-evals",
            "artifacts",
            "--prune-keep-per-pack",
            "0",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--prune-keep-per-pack must be at least 1" in err


def test_cli_rejects_prune_decision_keep_per_kind_less_than_one(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coding-agent-v1",
            "--prune-decision-artifacts",
            "artifacts",
            "--prune-decision-keep-per-kind",
            "0",
        ],
    )

    try:
        cli.main()
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected parser error")

    err = capsys.readouterr().err
    assert "--prune-decision-keep-per-kind must be at least 1" in err
