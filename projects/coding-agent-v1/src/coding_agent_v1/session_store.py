from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .models import RepairProposal, SessionEvent, SessionRecord, SessionStatus, TaskFlow, TaskPlan, WorkingMemory


def summarize_working_memory(memory: WorkingMemory) -> str:
    parts: list[str] = []
    if memory.task_flow:
        parts.append(f"task_flow={memory.task_flow}")
    if memory.resume_context:
        parts.append(f"resume={memory.resume_context}")
    if memory.focus:
        parts.append(f"focus={'; '.join(memory.focus)}")
    if memory.inspected_files:
        parts.append(f"inspected={', '.join(memory.inspected_files)}")
    if memory.changed_files:
        parts.append(f"changed={', '.join(memory.changed_files)}")
    if memory.last_validation:
        parts.append(f"validation={memory.last_validation}")
    if memory.next_step:
        parts.append(f"next={memory.next_step}")
    return " | ".join(parts)


def summarize_task_plan(plan: TaskPlan | None) -> str:
    if plan is None:
        return ""
    parts = [f"flow={plan.task_flow.value}"]
    if plan.feature_strategy:
        parts.append(f"feature_strategy={plan.feature_strategy}")
    if plan.feature_arguments:
        arguments = ",".join(f"{key}={value}" for key, value in sorted(plan.feature_arguments.items()))
        parts.append(f"feature_arguments={arguments}")
    if plan.initial_actions:
        parts.append(f"initial_actions={','.join(plan.initial_actions)}")
    if plan.validation_command:
        parts.append(f"validation={plan.validation_command}")
    if plan.reasons:
        parts.append(f"reasons={'; '.join(plan.reasons)}")
    return " | ".join(parts)


class SessionStore:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save(self, record: SessionRecord) -> Path:
        path = self.base_dir / f"{record.session_id}.json"
        payload = asdict(record)
        payload["workspace_root"] = str(record.workspace_root)
        payload["events"] = [
            {
                "kind": event.kind,
                "message": event.message,
                "created_at": event.created_at.isoformat(),
            }
            for event in record.events
        ]
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def append_event(self, record: SessionRecord, kind: str, message: str) -> None:
        record.events.append(SessionEvent(kind=kind, message=message))

    def load(self, session_id: str) -> SessionRecord:
        path = self.base_dir / f"{session_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._record_from_payload(payload)

    def list_session_ids(self) -> list[str]:
        return sorted(path.stem for path in self.base_dir.glob("*.json"))

    def build_review_summary(self, record: SessionRecord) -> str:
        parts = [
            f"session_id: {record.session_id}",
            f"status: {record.status.value}",
            f"workspace_root: {record.workspace_root}",
            f"task_flow: {record.task_flow.value}",
            f"request: {record.request}",
        ]
        if record.resumed_from_session_id:
            parts.append(f"resumed_from: {record.resumed_from_session_id}")
        if record.task_plan is not None:
            parts.append(f"task_plan: {summarize_task_plan(record.task_plan)}")
        if record.working_memory.focus:
            parts.append(f"working_memory_focus: {'; '.join(record.working_memory.focus)}")
        if record.working_memory.next_step:
            parts.append(f"working_memory_next: {record.working_memory.next_step}")
        if record.working_summary:
            parts.append(f"working_summary: {record.working_summary}")
        if record.inspected_files:
            parts.append(f"inspected_files: {', '.join(record.inspected_files)}")
        if record.changed_files:
            parts.append(f"changed_files: {', '.join(record.changed_files)}")
        if record.validation_summary:
            parts.append(f"validation: {record.validation_summary}")
        if record.final_report:
            parts.append(f"final_report: {record.final_report}")
        return "\n".join(parts)

    def _record_from_payload(self, payload: dict[str, object]) -> SessionRecord:
        events = [
            SessionEvent(
                kind=event["kind"],
                message=event["message"],
                created_at=datetime.fromisoformat(event["created_at"]),
            )
            for event in payload.get("events", [])
        ]
        candidate_proposals = [
            RepairProposal(**proposal)
            for proposal in payload.get("candidate_proposals", [])
        ]
        proposed_changes = [
            RepairProposal(**proposal)
            for proposal in payload.get("proposed_changes", [])
        ]
        working_memory_payload = payload.get("working_memory", {})
        working_memory = WorkingMemory(
            task_flow=str(working_memory_payload.get("task_flow", "")),
            resume_context=str(working_memory_payload.get("resume_context", "")),
            focus=[str(item) for item in working_memory_payload.get("focus", [])],
            inspected_files=[str(item) for item in working_memory_payload.get("inspected_files", [])],
            changed_files=[str(item) for item in working_memory_payload.get("changed_files", [])],
            last_validation=str(working_memory_payload.get("last_validation", "")),
            next_step=str(working_memory_payload.get("next_step", "")),
        )
        task_plan_payload = payload.get("task_plan")
        task_plan = None
        if isinstance(task_plan_payload, dict):
            task_plan = TaskPlan(
                task_flow=TaskFlow(str(task_plan_payload.get("task_flow", TaskFlow.INSPECT.value))),
                feature_strategy=str(task_plan_payload.get("feature_strategy", "")),
                feature_arguments={
                    str(key): str(value)
                    for key, value in dict(task_plan_payload.get("feature_arguments", {})).items()
                },
                initial_actions=[str(item) for item in task_plan_payload.get("initial_actions", [])],
                validation_command=str(task_plan_payload.get("validation_command", "")),
                reasons=[str(item) for item in task_plan_payload.get("reasons", [])],
            )
        return SessionRecord(
            session_id=str(payload["session_id"]),
            request=str(payload["request"]),
            workspace_root=Path(str(payload["workspace_root"])),
            task_flow=TaskFlow(str(payload.get("task_flow", TaskFlow.INSPECT.value))),
            task_plan=task_plan,
            resumed_from_session_id=payload.get("resumed_from_session_id") or None,
            status=SessionStatus(str(payload.get("status", SessionStatus.STARTED.value))),
            events=events,
            inspected_files=[str(item) for item in payload.get("inspected_files", [])],
            changed_files=[str(item) for item in payload.get("changed_files", [])],
            candidate_proposals=candidate_proposals,
            proposed_changes=proposed_changes,
            rationale=[str(item) for item in payload.get("rationale", [])],
            working_memory=working_memory,
            working_summary=str(payload.get("working_summary", summarize_working_memory(working_memory))),
            validation_summary=str(payload.get("validation_summary", "")),
            final_report=str(payload.get("final_report", "")),
        )
