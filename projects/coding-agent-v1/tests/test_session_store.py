from pathlib import Path

from coding_agent_v1.agent_loop import run_session
from coding_agent_v1.session_store import SessionStore


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
    assert loaded.task_plan.feature_strategy == record.task_plan.feature_strategy
    assert loaded.working_memory.task_flow == record.working_memory.task_flow
    assert loaded.working_memory.next_step == record.working_memory.next_step
    assert loaded.events


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
