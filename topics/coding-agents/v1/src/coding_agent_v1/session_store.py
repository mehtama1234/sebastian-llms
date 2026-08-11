from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from uuid import uuid4

from .models import (
    CompactContextArtifact,
    CompactContextIndexEntry,
    CompactContextPruneEntry,
    CompactContextPruneSummary,
    HandoffArtifact,
    ProceduralRepairRecord,
    ProceduralRepairStatusAudit,
    RepairProposal,
    SessionEvent,
    SessionRecord,
    SessionStatus,
    TaskFlow,
    TaskPlan,
    WorkingMemory,
)


ALLOWED_PROCEDURAL_REPAIR_STATUSES = ("candidate", "accepted", "rejected", "retired")
COMPACTION_EVENT_COUNT_THRESHOLD = 25
COMPACTION_CONTEXT_CHAR_THRESHOLD = 8_000


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
    if memory.belief:
        parts.append(f"belief={'; '.join(memory.belief)}")
    if memory.progress:
        parts.append(f"progress={'; '.join(memory.progress)}")
    if memory.experience:
        parts.append(f"experience={'; '.join(memory.experience)}")
    return " | ".join(parts)


def summarize_task_plan(plan: TaskPlan | None) -> str:
    if plan is None:
        return ""
    parts = [f"flow={plan.task_flow.value}"]
    if plan.planner_strategy:
        parts.append(f"planner_strategy={plan.planner_strategy}")
    if plan.planner_strategy_reason:
        parts.append(f"planner_strategy_reason={plan.planner_strategy_reason}")
    if plan.feature_strategy:
        parts.append(f"feature_strategy={plan.feature_strategy}")
    if plan.feature_arguments:
        arguments = ",".join(f"{key}={value}" for key, value in sorted(plan.feature_arguments.items()))
        parts.append(f"feature_arguments={arguments}")
    if plan.affected_behavior_ids:
        parts.append(f"behaviors={','.join(plan.affected_behavior_ids)}")
    if plan.implementation_surfaces:
        parts.append(f"surfaces={','.join(plan.implementation_surfaces)}")
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

    def save_compact_context(self, record: SessionRecord) -> Path:
        artifact = self.build_compact_context_artifact(record)
        compact_dir = self.base_dir / "compactions"
        compact_dir.mkdir(parents=True, exist_ok=True)
        path = compact_dir / f"{record.session_id}.compact.json"
        path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
        return path

    def save_handoff(self, record: SessionRecord, *, reason: str) -> Path:
        artifact = self.build_handoff_artifact(record, reason=reason)
        handoff_dir = self.base_dir / "handoffs"
        handoff_dir.mkdir(parents=True, exist_ok=True)
        path = handoff_dir / f"{record.session_id}.handoff.json"
        path.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
        return path

    def save_procedural_repair_record(self, repair: ProceduralRepairRecord) -> Path:
        repair_dir = self.base_dir / "repair-records"
        repair_dir.mkdir(parents=True, exist_ok=True)
        path = repair_dir / f"{repair.repair_id}.json"
        path.write_text(json.dumps(asdict(repair), indent=2), encoding="utf-8")
        return path

    def load_procedural_repair_record(self, repair_id: str) -> ProceduralRepairRecord:
        path = self.base_dir / "repair-records" / f"{repair_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._procedural_repair_from_payload(payload)

    def update_procedural_repair_status(
        self,
        repair_id: str,
        status: str,
        *,
        actor: str = "cli",
        reason: str = "",
    ) -> ProceduralRepairRecord:
        if status not in ALLOWED_PROCEDURAL_REPAIR_STATUSES:
            allowed = ", ".join(ALLOWED_PROCEDURAL_REPAIR_STATUSES)
            raise ValueError(f"invalid repair status '{status}'; expected one of: {allowed}")
        repair = self.load_procedural_repair_record(repair_id)
        previous_status = repair.status
        repair.status = status
        self.save_procedural_repair_record(repair)
        self.save_procedural_repair_status_audit(
            ProceduralRepairStatusAudit(
                audit_id=uuid4().hex,
                repair_id=repair_id,
                previous_status=previous_status,
                new_status=status,
                actor=actor,
                reason=reason,
            )
        )
        return repair

    def save_procedural_repair_status_audit(self, audit: ProceduralRepairStatusAudit) -> Path:
        audit_dir = self.base_dir / "repair-status-audits"
        audit_dir.mkdir(parents=True, exist_ok=True)
        path = audit_dir / f"{audit.audit_id}.json"
        payload = asdict(audit)
        payload["created_at"] = audit.created_at.isoformat()
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def load_procedural_repair_status_audit(self, audit_id: str) -> ProceduralRepairStatusAudit:
        path = self.base_dir / "repair-status-audits" / f"{audit_id}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._procedural_repair_status_audit_from_payload(payload)

    def list_procedural_repair_status_audits(
        self,
        *,
        repair_id: str | None = None,
    ) -> list[ProceduralRepairStatusAudit]:
        audit_dir = self.base_dir / "repair-status-audits"
        if not audit_dir.exists():
            return []
        audits = [
            self._procedural_repair_status_audit_from_payload(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(audit_dir.glob("*.json"))
        ]
        if repair_id is not None:
            audits = [audit for audit in audits if audit.repair_id == repair_id]
        return audits

    def list_procedural_repair_records(
        self,
        *,
        task_class: str | None = None,
        behavior_id: str | None = None,
        status: str | None = None,
    ) -> list[ProceduralRepairRecord]:
        repair_dir = self.base_dir / "repair-records"
        if not repair_dir.exists():
            return []
        records = [
            self._procedural_repair_from_payload(json.loads(path.read_text(encoding="utf-8")))
            for path in sorted(repair_dir.glob("*.json"))
        ]
        if task_class is not None:
            records = [record for record in records if record.task_class == task_class]
        if behavior_id is not None:
            records = [record for record in records if behavior_id in record.affected_behavior_ids]
        if status is not None:
            records = [record for record in records if record.status == status]
        return records

    def load_handoff(self, session_id: str) -> HandoffArtifact:
        path = self.base_dir / "handoffs" / f"{session_id}.handoff.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return HandoffArtifact(
            session_id=str(payload["session_id"]),
            request=str(payload["request"]),
            workspace_root=str(payload["workspace_root"]),
            status=str(payload["status"]),
            reason=str(payload["reason"]),
            task_flow=str(payload["task_flow"]),
            affected_behavior_ids=[str(item) for item in payload.get("affected_behavior_ids", [])],
            belief=[str(item) for item in payload.get("belief", [])],
            progress=[str(item) for item in payload.get("progress", [])],
            experience=[str(item) for item in payload.get("experience", [])],
            inspected_files=[str(item) for item in payload.get("inspected_files", [])],
            changed_files=[str(item) for item in payload.get("changed_files", [])],
            validation_summary=str(payload.get("validation_summary", "")),
            blocker=str(payload.get("blocker", "")),
            next_step=str(payload.get("next_step", "")),
        )

    def load_compact_context(self, session_id: str) -> CompactContextArtifact:
        path = self.base_dir / "compactions" / f"{session_id}.compact.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        return self._compact_context_from_payload(payload)

    def maybe_load_compact_context(self, session_id: str) -> CompactContextArtifact | None:
        path = self.base_dir / "compactions" / f"{session_id}.compact.json"
        if not path.exists():
            return None
        return self._compact_context_from_payload(json.loads(path.read_text(encoding="utf-8")))

    def list_compact_context_index(self) -> list[CompactContextIndexEntry]:
        compact_dir = self.base_dir / "compactions"
        if not compact_dir.exists():
            return []
        entries: list[CompactContextIndexEntry] = []
        for path in sorted(compact_dir.glob("*.compact.json")):
            artifact = self._compact_context_from_payload(json.loads(path.read_text(encoding="utf-8")))
            entries.append(
                CompactContextIndexEntry(
                    artifact_path=path,
                    session_id=artifact.session_id,
                    status=artifact.status,
                    task_flow=artifact.task_flow,
                    compaction_trigger=artifact.compaction_trigger,
                    source_event_count=artifact.source_event_count,
                    source_context_chars=artifact.source_context_chars,
                    modified_at=path.stat().st_mtime,
                )
            )
        return sorted(entries, key=lambda entry: (-entry.modified_at, entry.session_id))

    def build_compact_context_prune_summary(
        self,
        *,
        keep_newest: int = 20,
        include_size_triggered: bool = False,
    ) -> CompactContextPruneSummary:
        entries = self.list_compact_context_index()
        newest_paths = {entry.artifact_path for entry in entries[:keep_newest]}
        prune_entries: list[CompactContextPruneEntry] = []
        kept_count = 0
        prunable_count = 0
        for entry in entries:
            action = "prune"
            reason = f"older than newest {keep_newest} compact context artifact(s)"
            if entry.artifact_path in newest_paths:
                action = "keep"
                reason = f"within newest {keep_newest} compact context artifact(s)"
            elif (
                entry.compaction_trigger.startswith("size_triggered:")
                and not include_size_triggered
            ):
                action = "keep"
                reason = "size-triggered compaction is protected by default"
            if action == "keep":
                kept_count += 1
            else:
                prunable_count += 1
            prune_entries.append(
                CompactContextPruneEntry(
                    artifact_path=entry.artifact_path,
                    session_id=entry.session_id,
                    compaction_trigger=entry.compaction_trigger,
                    modified_at=entry.modified_at,
                    action=action,
                    reason=reason,
                )
            )
        return CompactContextPruneSummary(
            base_dir=self.base_dir,
            keep_newest=keep_newest,
            include_size_triggered=include_size_triggered,
            kept_count=kept_count,
            prunable_count=prunable_count,
            entries=prune_entries,
        )

    def apply_compact_context_prune_summary(self, summary: CompactContextPruneSummary) -> list[Path]:
        deleted_paths: list[Path] = []
        for entry in summary.entries:
            if entry.action != "prune":
                continue
            if entry.artifact_path.exists():
                entry.artifact_path.unlink()
                deleted_paths.append(entry.artifact_path)
        return deleted_paths

    def summarize_compact_context_index(self, entries: list[CompactContextIndexEntry]) -> str:
        if not entries:
            return "compact_contexts: none"
        lines = [f"compact_contexts: {len(entries)}"]
        for entry in entries:
            lines.append(
                f"{entry.session_id}: status={entry.status} task_flow={entry.task_flow} "
                f"trigger={entry.compaction_trigger} events={entry.source_event_count} "
                f"chars={entry.source_context_chars} path={entry.artifact_path}"
            )
        return "\n".join(lines)

    def summarize_compact_context_prune_summary(self, summary: CompactContextPruneSummary) -> str:
        lines = [
            f"compact_context_prune_plan: {summary.base_dir}",
            f"keep_newest: {summary.keep_newest}",
            f"include_size_triggered: {summary.include_size_triggered}",
            f"kept: {summary.kept_count}",
            f"prunable: {summary.prunable_count}",
        ]
        for entry in summary.entries:
            lines.append(
                f"{entry.artifact_path}: action={entry.action} "
                f"session_id={entry.session_id} trigger={entry.compaction_trigger} "
                f"reason={entry.reason}"
            )
        return "\n".join(lines)

    def build_compact_context_artifact(self, record: SessionRecord) -> CompactContextArtifact:
        affected_behavior_ids: list[str] = []
        implementation_surfaces: list[str] = []
        if record.task_plan is not None:
            affected_behavior_ids = list(record.task_plan.affected_behavior_ids)
            implementation_surfaces = list(record.task_plan.implementation_surfaces)
        blocker = ""
        if record.status is SessionStatus.FAILED:
            blocker = record.final_report or record.validation_summary
        source_context_chars = self._source_context_chars(record)
        return CompactContextArtifact(
            session_id=record.session_id,
            request=record.request,
            workspace_root=str(record.workspace_root),
            status=record.status.value,
            task_flow=record.task_flow.value,
            compaction_trigger=self._compact_context_trigger(
                record,
                source_context_chars=source_context_chars,
            ),
            source_event_count=len(record.events),
            source_context_chars=source_context_chars,
            affected_behavior_ids=affected_behavior_ids,
            implementation_surfaces=implementation_surfaces,
            belief=list(record.working_memory.belief[:6]),
            progress=list(record.working_memory.progress[:6]),
            experience=list(record.working_memory.experience[:6]),
            inspected_files=list(record.inspected_files[:8]),
            changed_files=list(record.changed_files[:8]),
            validation_summary=record.validation_summary,
            blocker=blocker,
            next_step=record.working_memory.next_step,
            summary=summarize_working_memory(record.working_memory),
        )

    def build_compact_context_review_summary(self, artifact: CompactContextArtifact) -> str:
        parts = [
            f"compact_session_id: {artifact.session_id}",
            f"status: {artifact.status}",
            f"workspace_root: {artifact.workspace_root}",
            f"task_flow: {artifact.task_flow}",
            f"compaction_trigger: {artifact.compaction_trigger}",
            f"source_event_count: {artifact.source_event_count}",
            f"source_context_chars: {artifact.source_context_chars}",
            f"request: {artifact.request}",
        ]
        if artifact.affected_behavior_ids:
            parts.append(f"affected_behaviors: {', '.join(artifact.affected_behavior_ids)}")
        if artifact.implementation_surfaces:
            parts.append(f"implementation_surfaces: {', '.join(artifact.implementation_surfaces)}")
        if artifact.belief:
            parts.append(f"belief: {'; '.join(artifact.belief)}")
        if artifact.progress:
            parts.append(f"progress: {'; '.join(artifact.progress)}")
        if artifact.experience:
            parts.append(f"experience: {'; '.join(artifact.experience)}")
        if artifact.inspected_files:
            parts.append(f"inspected_files: {', '.join(artifact.inspected_files)}")
        if artifact.changed_files:
            parts.append(f"changed_files: {', '.join(artifact.changed_files)}")
        if artifact.validation_summary:
            parts.append(f"validation: {artifact.validation_summary}")
        if artifact.blocker:
            parts.append(f"blocker: {artifact.blocker}")
        if artifact.next_step:
            parts.append(f"next_step: {artifact.next_step}")
        if artifact.summary:
            parts.append(f"summary: {artifact.summary}")
        return "\n".join(parts)

    def build_handoff_artifact(self, record: SessionRecord, *, reason: str) -> HandoffArtifact:
        affected_behavior_ids: list[str] = []
        if record.task_plan is not None:
            affected_behavior_ids = list(record.task_plan.affected_behavior_ids)
        blocker = record.final_report or record.validation_summary or "session did not complete cleanly"
        return HandoffArtifact(
            session_id=record.session_id,
            request=record.request,
            workspace_root=str(record.workspace_root),
            status=record.status.value,
            reason=reason,
            task_flow=record.task_flow.value,
            affected_behavior_ids=affected_behavior_ids,
            belief=list(record.working_memory.belief),
            progress=list(record.working_memory.progress),
            experience=list(record.working_memory.experience),
            inspected_files=list(record.inspected_files),
            changed_files=list(record.changed_files),
            validation_summary=record.validation_summary,
            blocker=blocker,
            next_step=record.working_memory.next_step,
        )

    def build_handoff_review_summary(self, artifact: HandoffArtifact) -> str:
        parts = [
            f"handoff_session_id: {artifact.session_id}",
            f"status: {artifact.status}",
            f"reason: {artifact.reason}",
            f"workspace_root: {artifact.workspace_root}",
            f"task_flow: {artifact.task_flow}",
            f"request: {artifact.request}",
        ]
        if artifact.affected_behavior_ids:
            parts.append(f"affected_behaviors: {', '.join(artifact.affected_behavior_ids)}")
        if artifact.belief:
            parts.append(f"belief: {'; '.join(artifact.belief)}")
        if artifact.progress:
            parts.append(f"progress: {'; '.join(artifact.progress)}")
        if artifact.experience:
            parts.append(f"experience: {'; '.join(artifact.experience)}")
        if artifact.inspected_files:
            parts.append(f"inspected_files: {', '.join(artifact.inspected_files)}")
        if artifact.changed_files:
            parts.append(f"changed_files: {', '.join(artifact.changed_files)}")
        if artifact.validation_summary:
            parts.append(f"validation: {artifact.validation_summary}")
        if artifact.blocker:
            parts.append(f"blocker: {artifact.blocker}")
        if artifact.next_step:
            parts.append(f"next_step: {artifact.next_step}")
        return "\n".join(parts)

    def build_procedural_repair_review_summary(self, repair: ProceduralRepairRecord) -> str:
        parts = [
            f"repair_id: {repair.repair_id}",
            f"source_session_id: {repair.source_session_id}",
            f"status: {repair.status}",
            f"task_class: {repair.task_class}",
            f"trigger_condition: {repair.trigger_condition}",
            f"failure_pattern: {repair.failure_pattern}",
            f"recommended_recovery: {repair.recommended_recovery}",
            f"support_count: {repair.support_count}",
        ]
        if repair.affected_behavior_ids:
            parts.append(f"affected_behaviors: {', '.join(repair.affected_behavior_ids)}")
        if repair.source_evidence:
            parts.append(f"source_evidence: {'; '.join(repair.source_evidence)}")
        if repair.validation_evidence:
            parts.append(f"validation_evidence: {'; '.join(repair.validation_evidence)}")
        return "\n".join(parts)

    def build_procedural_repair_status_audit_review_summary(
        self,
        audit: ProceduralRepairStatusAudit,
    ) -> str:
        parts = [
            f"audit_id: {audit.audit_id}",
            f"repair_id: {audit.repair_id}",
            f"previous_status: {audit.previous_status}",
            f"new_status: {audit.new_status}",
            f"actor: {audit.actor}",
            f"created_at: {audit.created_at.isoformat()}",
        ]
        if audit.reason:
            parts.append(f"reason: {audit.reason}")
        return "\n".join(parts)

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
        if record.working_memory.belief:
            parts.append(f"working_memory_belief: {'; '.join(record.working_memory.belief)}")
        if record.working_memory.progress:
            parts.append(f"working_memory_progress: {'; '.join(record.working_memory.progress)}")
        if record.working_memory.experience:
            parts.append(f"working_memory_experience: {'; '.join(record.working_memory.experience)}")
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
            belief=[str(item) for item in working_memory_payload.get("belief", [])],
            progress=[str(item) for item in working_memory_payload.get("progress", [])],
            experience=[str(item) for item in working_memory_payload.get("experience", [])],
        )
        task_plan_payload = payload.get("task_plan")
        task_plan = None
        if isinstance(task_plan_payload, dict):
            task_plan = TaskPlan(
                task_flow=TaskFlow(str(task_plan_payload.get("task_flow", TaskFlow.INSPECT.value))),
                planner_strategy=str(task_plan_payload.get("planner_strategy", "deterministic_heuristic")),
                planner_strategy_reason=str(task_plan_payload.get("planner_strategy_reason", "")),
                feature_strategy=str(task_plan_payload.get("feature_strategy", "")),
                feature_arguments={
                    str(key): str(value)
                    for key, value in dict(task_plan_payload.get("feature_arguments", {})).items()
                },
                affected_behavior_ids=[
                    str(item) for item in task_plan_payload.get("affected_behavior_ids", [])
                ],
                implementation_surfaces=[
                    str(item) for item in task_plan_payload.get("implementation_surfaces", [])
                ],
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

    def _procedural_repair_from_payload(self, payload: dict[str, object]) -> ProceduralRepairRecord:
        return ProceduralRepairRecord(
            repair_id=str(payload["repair_id"]),
            source_session_id=str(payload["source_session_id"]),
            task_class=str(payload["task_class"]),
            trigger_condition=str(payload["trigger_condition"]),
            failure_pattern=str(payload["failure_pattern"]),
            recommended_recovery=str(payload["recommended_recovery"]),
            source_evidence=[str(item) for item in payload.get("source_evidence", [])],
            validation_evidence=[str(item) for item in payload.get("validation_evidence", [])],
            affected_behavior_ids=[str(item) for item in payload.get("affected_behavior_ids", [])],
            support_count=int(payload.get("support_count", 1)),
            status=str(payload.get("status", "candidate")),
        )

    def _procedural_repair_status_audit_from_payload(
        self,
        payload: dict[str, object],
    ) -> ProceduralRepairStatusAudit:
        return ProceduralRepairStatusAudit(
            audit_id=str(payload["audit_id"]),
            repair_id=str(payload["repair_id"]),
            previous_status=str(payload["previous_status"]),
            new_status=str(payload["new_status"]),
            actor=str(payload.get("actor", "cli")),
            reason=str(payload.get("reason", "")),
            created_at=datetime.fromisoformat(str(payload["created_at"])),
        )

    def _compact_context_trigger(
        self,
        record: SessionRecord,
        *,
        source_context_chars: int,
    ) -> str:
        triggers: list[str] = []
        if len(record.events) >= COMPACTION_EVENT_COUNT_THRESHOLD:
            triggers.append("event_count")
        if source_context_chars >= COMPACTION_CONTEXT_CHAR_THRESHOLD:
            triggers.append("context_chars")
        if record.status is SessionStatus.FAILED:
            triggers.append("blocked_state")
        if record.resumed_from_session_id:
            triggers.append("resume_checkpoint")
        if triggers:
            return "size_triggered:" + ",".join(triggers)
        return "checkpoint"

    def _source_context_chars(self, record: SessionRecord) -> int:
        parts = [
            record.request,
            record.working_summary,
            record.validation_summary,
            record.final_report,
            *record.inspected_files,
            *record.changed_files,
            *record.rationale,
            *record.working_memory.belief,
            *record.working_memory.progress,
            *record.working_memory.experience,
        ]
        parts.extend(event.message for event in record.events)
        return sum(len(part) for part in parts)

    def _compact_context_from_payload(self, payload: dict[str, object]) -> CompactContextArtifact:
        return CompactContextArtifact(
            session_id=str(payload["session_id"]),
            request=str(payload["request"]),
            workspace_root=str(payload["workspace_root"]),
            status=str(payload["status"]),
            task_flow=str(payload["task_flow"]),
            compaction_trigger=str(payload.get("compaction_trigger", "checkpoint")),
            source_event_count=int(payload.get("source_event_count", 0)),
            source_context_chars=int(payload.get("source_context_chars", 0)),
            affected_behavior_ids=[str(item) for item in payload.get("affected_behavior_ids", [])],
            implementation_surfaces=[str(item) for item in payload.get("implementation_surfaces", [])],
            belief=[str(item) for item in payload.get("belief", [])],
            progress=[str(item) for item in payload.get("progress", [])],
            experience=[str(item) for item in payload.get("experience", [])],
            inspected_files=[str(item) for item in payload.get("inspected_files", [])],
            changed_files=[str(item) for item in payload.get("changed_files", [])],
            validation_summary=str(payload.get("validation_summary", "")),
            blocker=str(payload.get("blocker", "")),
            next_step=str(payload.get("next_step", "")),
            summary=str(payload.get("summary", "")),
        )
