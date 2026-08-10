from pathlib import Path

import pytest

from coding_agent_v1.agent_loop import run_session
from coding_agent_v1.models import ProceduralRepairRecord
from coding_agent_v1.models import SessionEvent, SessionRecord
from coding_agent_v1.session_store import COMPACTION_EVENT_COUNT_THRESHOLD, SessionStore


def test_session_store_load_round_trips_saved_session(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session("summarize this repo", tmp_path, store)
    loaded = store.load(record.session_id)

    assert loaded.session_id == record.session_id
    assert loaded.status == record.status
    assert loaded.workspace_root == record.workspace_root
    assert loaded.final_report == record.final_report
    assert loaded.task_plan is not None
    assert loaded.task_plan.task_flow == record.task_plan.task_flow
    assert loaded.task_plan.planner_strategy == "deterministic_heuristic"
    assert loaded.task_plan.planner_strategy_reason == record.task_plan.planner_strategy_reason
    assert loaded.task_plan.feature_strategy == record.task_plan.feature_strategy
    assert loaded.working_memory.task_flow == record.working_memory.task_flow
    assert loaded.working_memory.next_step == record.working_memory.next_step
    assert loaded.working_memory.belief == record.working_memory.belief
    assert loaded.working_memory.progress == record.working_memory.progress
    assert loaded.working_memory.experience == record.working_memory.experience
    assert loaded.events


def test_session_store_saves_loads_and_summarizes_compact_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session("summarize this repo", tmp_path, store)
    compact_path = tmp_path / "sessions" / "compactions" / f"{record.session_id}.compact.json"
    compact = store.load_compact_context(record.session_id)
    summary = store.build_compact_context_review_summary(compact)

    assert compact_path.exists()
    assert compact.session_id == record.session_id
    assert compact.request == "summarize this repo"
    assert compact.status == "completed"
    assert compact.task_flow == "inspect"
    assert compact.compaction_trigger == "checkpoint"
    assert compact.source_event_count == len(record.events)
    assert compact.source_context_chars > 0
    assert compact.belief == record.working_memory.belief
    assert compact.progress == record.working_memory.progress
    assert compact.next_step == record.working_memory.next_step
    assert "compact_session_id:" in summary
    assert "compaction_trigger: checkpoint" in summary
    assert "source_event_count:" in summary
    assert "source_context_chars:" in summary
    assert "belief:" in summary
    assert "progress:" in summary
    assert "summary:" in summary


def test_session_store_marks_long_session_compaction_trigger(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions")
    record = SessionRecord(
        session_id="s1",
        request="summarize a long session",
        workspace_root=tmp_path,
        events=[
            SessionEvent(kind="tool", message=f"event {index}")
            for index in range(COMPACTION_EVENT_COUNT_THRESHOLD)
        ],
    )

    path = store.save_compact_context(record)
    compact = store.load_compact_context("s1")
    payload = path.read_text(encoding="utf-8")

    assert compact.compaction_trigger == "size_triggered:event_count"
    assert compact.source_event_count == COMPACTION_EVENT_COUNT_THRESHOLD
    assert '"compaction_trigger": "size_triggered:event_count"' in payload


def test_session_store_lists_and_prunes_compact_contexts_conservatively(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions")
    for index in range(3):
        record = SessionRecord(
            session_id=f"s{index}",
            request=f"summarize session {index}",
            workspace_root=tmp_path,
            events=[
                SessionEvent(kind="tool", message=f"event {event_index}")
                for event_index in range(COMPACTION_EVENT_COUNT_THRESHOLD if index == 0 else 1)
            ],
        )
        store.save_compact_context(record)

    entries = store.list_compact_context_index()
    summary = store.build_compact_context_prune_summary(keep_newest=1)
    text = store.summarize_compact_context_prune_summary(summary)
    deleted = store.apply_compact_context_prune_summary(summary)

    assert len(entries) == 3
    assert any(entry.compaction_trigger.startswith("size_triggered:") for entry in entries)
    assert summary.kept_count == 2
    assert summary.prunable_count == 1
    assert "size-triggered compaction is protected by default" in text
    assert len(deleted) == 1
    assert deleted[0].name.endswith(".compact.json")


def test_session_store_can_prune_size_triggered_compactions_when_explicitly_included(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions")
    for index in range(2):
        record = SessionRecord(
            session_id=f"s{index}",
            request=f"summarize session {index}",
            workspace_root=tmp_path,
            events=[
                SessionEvent(kind="tool", message=f"event {event_index}")
                for event_index in range(COMPACTION_EVENT_COUNT_THRESHOLD)
            ],
        )
        store.save_compact_context(record)

    summary = store.build_compact_context_prune_summary(
        keep_newest=1,
        include_size_triggered=True,
    )

    assert summary.kept_count == 1
    assert summary.prunable_count == 1


def test_session_store_build_review_summary_includes_resume_metadata(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    first = run_session("summarize this repo", tmp_path, store)
    second = run_session(
        "summarize this repo again",
        tmp_path,
        store,
        resume_from_session_id=first.session_id,
    )

    summary = store.build_review_summary(store.load(second.session_id))

    assert f"session_id: {second.session_id}" in summary
    assert f"resumed_from: {first.session_id}" in summary
    assert "task_plan:" in summary
    assert "working_memory_focus:" in summary
    assert "working_memory_next:" in summary
    assert "working_memory_belief:" in summary
    assert "working_memory_progress:" in summary
    assert "working_summary:" in summary
    assert "final_report:" in summary


def test_session_store_review_summary_includes_feature_strategy(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add APP_PROFILE environment variable with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    summary = store.build_review_summary(store.load(record.session_id))

    assert "task_plan:" in summary
    assert "feature_strategy=env_var" in summary
    assert "feature_arguments=env_name=APP_PROFILE" in summary


def test_session_store_round_trips_task_plan_behavior_index_fields(tmp_path: Path) -> None:
    harness = tmp_path / "src" / "coding_agent_v1"
    harness.mkdir(parents=True)
    (harness / "agent_loop.py").write_text(
        "def build_task_plan(): pass\n"
        "def build_initial_actions(): pass\n"
        "def _choose_validation_command(): pass\n"
        "def _validation_reason(): pass\n",
        encoding="utf-8",
    )
    (harness / "planner.py").write_text("def find_python_test_paths(): pass\n", encoding="utf-8")
    (harness / "models.py").write_text("class TaskPlan: pass\nclass WorkingMemory: pass\n", encoding="utf-8")
    (tmp_path / "test_agent_loop.py").write_text("def test_validation():\n    assert True\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "improve validation selection for rename tasks",
        tmp_path,
        store,
        auto_approve_commands=True,
    )
    loaded = store.load(record.session_id)
    summary = store.build_review_summary(loaded)

    assert loaded.task_plan is not None
    assert "validation_selection" in loaded.task_plan.affected_behavior_ids
    assert "src/coding_agent_v1/agent_loop.py" in loaded.task_plan.implementation_surfaces
    assert "behaviors=task_planning,validation_selection" in summary
    assert "surfaces=src/coding_agent_v1/agent_loop.py" in summary


def test_session_store_saves_and_loads_handoff_artifact(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run the tests", tmp_path, store)
    handoff_path = tmp_path / "sessions" / "handoffs" / f"{record.session_id}.handoff.json"
    handoff = store.load_handoff(record.session_id)

    assert handoff_path.exists()
    assert handoff.session_id == record.session_id
    assert handoff.request == "run the tests"
    assert handoff.reason == "approval_required"
    assert handoff.status == "failed"
    assert handoff.task_flow == "fix"
    assert handoff.blocker == record.final_report
    assert handoff.next_step == record.working_memory.next_step
    assert handoff.belief == record.working_memory.belief
    assert handoff.progress == record.working_memory.progress
    assert handoff.experience == record.working_memory.experience


def test_session_store_build_handoff_review_summary_includes_bpe_state(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run the tests", tmp_path, store)
    summary = store.build_handoff_review_summary(store.load_handoff(record.session_id))

    assert f"handoff_session_id: {record.session_id}" in summary
    assert "reason: approval_required" in summary
    assert "belief:" in summary
    assert "progress:" in summary
    assert "blocker:" in summary
    assert "next_step:" in summary


def test_session_store_saves_loads_and_summarizes_procedural_repair_record(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_broken():\n    assert False\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run tests", tmp_path, store, auto_approve_commands=True)
    repairs = store.list_procedural_repair_records(task_class="fix", status="candidate")
    loaded = store.load_procedural_repair_record(repairs[0].repair_id)
    summary = store.build_procedural_repair_review_summary(loaded)

    assert len(repairs) == 1
    assert loaded.source_session_id == record.session_id
    assert loaded.failure_pattern == "validation_failed"
    assert loaded.recommended_recovery
    assert "repair_id:" in summary
    assert "failure_pattern: validation_failed" in summary
    assert "recommended_recovery:" in summary


def test_session_store_filters_procedural_repair_records_by_behavior(tmp_path: Path) -> None:
    harness = tmp_path / "src" / "coding_agent_v1"
    harness.mkdir(parents=True)
    (harness / "agent_loop.py").write_text(
        "def build_task_plan(): pass\n"
        "def build_initial_actions(): pass\n"
        "def _choose_validation_command(): pass\n"
        "def _validation_reason(): pass\n",
        encoding="utf-8",
    )
    (harness / "planner.py").write_text("def find_python_test_paths(): pass\n", encoding="utf-8")
    (harness / "models.py").write_text("class TaskPlan: pass\nclass WorkingMemory: pass\n", encoding="utf-8")
    (tmp_path / "test_agent_loop.py").write_text("def test_broken():\n    assert False\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    run_session(
        "run tests for validation selection",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    repairs = store.list_procedural_repair_records(behavior_id="validation_selection")

    assert len(repairs) == 1
    assert "validation_selection" in repairs[0].affected_behavior_ids


def test_session_store_updates_procedural_repair_record_status(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions")
    repair = ProceduralRepairRecord(
        repair_id="r1",
        source_session_id="s1",
        task_class="fix",
        trigger_condition="validation failed",
        failure_pattern="validation_failed",
        recommended_recovery="inspect failure output",
    )
    store.save_procedural_repair_record(repair)

    updated = store.update_procedural_repair_status(
        "r1",
        "accepted",
        actor="reviewer",
        reason="validated on repeated failure",
    )
    loaded = store.load_procedural_repair_record("r1")
    audits = store.list_procedural_repair_status_audits(repair_id="r1")
    audit_summary = store.build_procedural_repair_status_audit_review_summary(audits[0])

    assert updated.status == "accepted"
    assert loaded.status == "accepted"
    assert store.list_procedural_repair_records(status="accepted")[0].repair_id == "r1"
    assert len(audits) == 1
    assert audits[0].previous_status == "candidate"
    assert audits[0].new_status == "accepted"
    assert audits[0].actor == "reviewer"
    assert audits[0].reason == "validated on repeated failure"
    assert "previous_status: candidate" in audit_summary
    assert "new_status: accepted" in audit_summary
    assert "reason: validated on repeated failure" in audit_summary


def test_session_store_rejects_invalid_procedural_repair_record_status(tmp_path: Path) -> None:
    store = SessionStore(tmp_path / "sessions")
    repair = ProceduralRepairRecord(
        repair_id="r1",
        source_session_id="s1",
        task_class="fix",
        trigger_condition="validation failed",
        failure_pattern="validation_failed",
        recommended_recovery="inspect failure output",
    )
    store.save_procedural_repair_record(repair)

    with pytest.raises(ValueError, match="invalid repair status"):
        store.update_procedural_repair_status("r1", "promoted")
