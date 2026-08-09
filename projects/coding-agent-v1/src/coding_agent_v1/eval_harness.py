from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from .eval_catalog import list_executable_eval_scenarios, load_eval_scenario_pack
from .agent_loop import run_session
from .models import SessionRecord
from .session_store import SessionStore


@dataclass(slots=True)
class EvalScenario:
    name: str
    request: str
    setup_kind: str
    auto_approve_commands: bool = True
    task_class: str = "unknown"
    severity: str = "core"
    failure_modes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalResult:
    scenario_name: str
    passed: bool
    session_id: str
    status: str
    final_report: str
    outcome_reason: str
    duration_seconds: float
    task_class: str = "unknown"
    severity: str = "core"
    failure_modes: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalSummary:
    total: int
    passed: int
    failed: int
    results: list[EvalResult]
    created_at: str
    run_label: str | None = None
    artifact_path: Path | None = None
    scenario_pack_id: str | None = None


@dataclass(slots=True)
class EvalComparisonResult:
    scenario_name: str
    task_class: str
    baseline_passed: bool
    candidate_passed: bool
    classification: str
    duration_delta_seconds: float
    baseline_reason: str
    candidate_reason: str
    failure_modes: tuple[str, ...] = ()


@dataclass(slots=True)
class EvalComparisonSummary:
    baseline_artifact_path: Path | None
    candidate_artifact_path: Path | None
    baseline_scenario_pack_id: str | None
    candidate_scenario_pack_id: str | None
    regressions: int
    improvements: int
    unchanged: int
    results: list[EvalComparisonResult]
    created_at: str
    artifact_path: Path | None = None


@dataclass(slots=True)
class EvalPromotionDecision:
    baseline_name: str
    candidate_reference: str
    promoted: bool
    comparison: EvalComparisonSummary
    artifact_path: Path | None = None
    config_path: Path | None = None
    created_at: str = ""
    decision_artifact_path: Path | None = None


@dataclass(slots=True)
class EvalHistoryEntry:
    artifact_path: Path | None
    created_at: str | None
    run_label: str | None
    scenario_pack_id: str | None
    passed: bool
    duration_seconds: float
    outcome_reason: str


@dataclass(slots=True)
class EvalScenarioTrend:
    scenario_name: str
    runs: int
    pass_count: int
    fail_count: int
    latest_passed: bool
    latest_duration_seconds: float
    average_duration_seconds: float
    trend: str
    history: list[EvalHistoryEntry]


@dataclass(slots=True)
class EvalHistorySummary:
    artifact_paths: list[Path]
    pack_counts: dict[str, int]
    scenario_trends: list[EvalScenarioTrend]


@dataclass(slots=True)
class EvalArtifactIndexEntry:
    artifact_path: Path
    created_at: str
    run_label: str | None
    scenario_pack_id: str | None
    passed: int
    total: int
    pass_rate: float


@dataclass(slots=True)
class EvalArtifactIndex:
    artifact_dir: Path
    pack_counts: dict[str, int]
    entries: list[EvalArtifactIndexEntry]


@dataclass(slots=True)
class EvalBaselineConfig:
    artifact_dir: Path
    baselines: dict[str, Path]
    baseline_pack_ids: dict[str, str | None]


@dataclass(slots=True)
class EvalBaselineSummaryEntry:
    name: str
    artifact_path: Path
    status: str
    scenario_pack_id: str | None
    run_label: str | None
    created_at: str | None
    passed: int | None
    total: int | None
    pass_rate: float | None


@dataclass(slots=True)
class EvalBaselineAuditEntry:
    name: str
    artifact_path: Path
    status: str
    scenario_pack_id: str | None
    recommended_reference: str | None
    recommended_artifact_path: Path | None


@dataclass(slots=True)
class EvalBaselineAuditSummary:
    artifact_dir: Path
    entries: list[EvalBaselineAuditEntry]


@dataclass(slots=True)
class EvalArtifactPruneEntry:
    artifact_path: Path
    action: str
    reasons: tuple[str, ...]
    scenario_pack_id: str | None
    run_label: str | None


@dataclass(slots=True)
class EvalArtifactPruneSummary:
    artifact_dir: Path
    keep_per_pack: int
    protected_count: int
    prunable_count: int
    entries: list[EvalArtifactPruneEntry]


@dataclass(slots=True)
class EvalDecisionArtifactPruneEntry:
    artifact_path: Path
    artifact_kind: str
    action: str
    reasons: tuple[str, ...]
    referenced_artifact_paths: tuple[Path, ...]


@dataclass(slots=True)
class EvalDecisionArtifactPruneSummary:
    artifact_dir: Path
    keep_per_kind: int
    protected_count: int
    prunable_count: int
    entries: list[EvalDecisionArtifactPruneEntry]


@dataclass(slots=True)
class EvalTaskClassSummaryEntry:
    task_class: str
    total: int
    passed: int
    failed: int
    scenario_names: tuple[str, ...]


@dataclass(slots=True)
class EvalFailureModeSummaryEntry:
    failure_mode: str
    scenario_count: int
    passed: int
    failed: int
    scenario_names: tuple[str, ...]


@dataclass(slots=True)
class EvalTaskClassComparisonEntry:
    task_class: str
    regressions: int
    improvements: int
    unchanged: int
    scenario_names: tuple[str, ...]


SCENARIOS = [
    EvalScenario(
        name="failing_test_repair",
        request="fix the failing test",
        setup_kind="repair",
        task_class="fix",
        severity="smoke",
        failure_modes=("no_op", "bad_validation_scope", "wrong_file_touched"),
        tags=("pytest", "repair", "single-module"),
    ),
    EvalScenario(
        name="natural_language_test_repair",
        request="make the failing tests pass",
        setup_kind="repair",
        task_class="fix",
        severity="core",
        failure_modes=("no_op", "partial_fix", "bad_validation_scope"),
        tags=("pytest", "natural-language", "repair"),
    ),
    EvalScenario(
        name="safe_multi_file_rename",
        request="rename add to plus",
        setup_kind="rename",
        task_class="rename",
        severity="smoke",
        failure_modes=("wrong_file_touched", "partial_fix", "regression_introduced"),
        tags=("rename", "symbol", "multi-file"),
    ),
    EvalScenario(
        name="cli_flag_feature",
        request="add a --verbose flag",
        setup_kind="cli_flag",
        task_class="feature",
        severity="smoke",
        failure_modes=("no_op", "partial_fix", "bad_validation_scope"),
        tags=("cli", "argparse", "feature"),
    ),
    EvalScenario(
        name="natural_language_cli_flag_feature",
        request="make the parser support verbose mode",
        setup_kind="cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("no_op", "partial_fix", "wrong_file_touched"),
        tags=("natural-language", "cli", "feature"),
    ),
    EvalScenario(
        name="module_aware_cli_feature",
        request="add a --verbose flag",
        setup_kind="module_aware_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "module-aware", "feature"),
    ),
    EvalScenario(
        name="single_test_workspace_fallback_cli_feature",
        request="add a --verbose flag",
        setup_kind="single_test_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "single-test", "feature"),
    ),
    EvalScenario(
        name="explicit_multi_test_cli_flag_feature",
        request=(
            "add a --verbose flag so "
            "[first](tests/regression/test_targeted_cli.py) and "
            "[second](tests/smoke/test_cli_smoke.py) pass"
        ),
        setup_kind="explicit_multi_test_cli_flag",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("cli", "multi-test", "feature"),
    ),
    EvalScenario(
        name="config_option_feature",
        request="add a timeout config option with default 30",
        setup_kind="config_option",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("config", "defaults", "feature"),
    ),
    EvalScenario(
        name="natural_language_config_option_feature",
        request="make config support timeout with default 30",
        setup_kind="config_option",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "bad_validation_scope", "wrong_file_touched"),
        tags=("config", "natural-language", "feature"),
    ),
    EvalScenario(
        name="env_var_feature",
        request="add APP_PROFILE environment variable with default advanced",
        setup_kind="env_var",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "regression_introduced", "bad_validation_scope"),
        tags=("env-var", "config", "feature"),
    ),
    EvalScenario(
        name="natural_language_env_var_feature",
        request="make config read profile from APP_PROFILE with default advanced",
        setup_kind="env_var",
        task_class="feature",
        severity="core",
        failure_modes=("partial_fix", "regression_introduced", "bad_validation_scope"),
        tags=("env-var", "natural-language", "feature"),
    ),
    EvalScenario(
        name="inspect_repo_summary",
        request="summarize this repo",
        setup_kind="inspect",
        task_class="inspect",
        severity="smoke",
        failure_modes=("wrong_file_touched", "no_op", "bad_validation_scope"),
        tags=("inspect", "summary", "no-edit"),
    ),
    EvalScenario(
        name="approval_required_boundary",
        request="run the tests",
        setup_kind="approval_boundary",
        auto_approve_commands=False,
        task_class="diagnose",
        severity="core",
        failure_modes=("unsafe_action", "no_op", "bad_validation_scope"),
        tags=("approval", "boundary", "diagnose"),
    ),
    EvalScenario(
        name="natural_language_diagnose_flow",
        request="investigate the failing tests",
        setup_kind="diagnose",
        task_class="diagnose",
        severity="smoke",
        failure_modes=("diagnose_edited_repo", "no_op", "bad_validation_scope"),
        tags=("diagnose", "natural-language", "no-edit"),
    ),
    EvalScenario(
        name="mixed_format_multi_test_diagnose_flow",
        request="'tests/quoted/test_first.py' and [second](tests/linked/test_second.py) are failing",
        setup_kind="diagnose_multi_test",
        task_class="diagnose",
        severity="core",
        failure_modes=("diagnose_edited_repo", "wrong_file_touched", "bad_validation_scope"),
        tags=("diagnose", "multi-test", "path-parsing"),
    ),
    EvalScenario(
        name="resume_session_flow",
        request="summarize this repo again",
        setup_kind="resume_flow",
        task_class="resume",
        severity="smoke",
        failure_modes=("resume_memory_loss", "no_op", "wrong_file_touched"),
        tags=("resume", "session", "memory"),
    ),
]


def run_eval_suite(
    base_session_dir: Path | None = None,
    *,
    artifact_dir: Path | None = None,
    run_label: str | None = None,
) -> EvalSummary:
    return _run_eval_scenarios(
        SCENARIOS,
        base_session_dir=base_session_dir,
        artifact_dir=artifact_dir,
        run_label=run_label,
        scenario_pack_id="built-in",
    )


def run_eval_scenario_pack(
    scenario_pack_path: Path,
    base_session_dir: Path | None = None,
    *,
    artifact_dir: Path | None = None,
    run_label: str | None = None,
) -> EvalSummary:
    pack = load_eval_scenario_pack(scenario_pack_path)
    scenarios = [
        EvalScenario(
            name=scenario.scenario_id,
            request=scenario.request,
            setup_kind=scenario.setup_kind,
            auto_approve_commands=scenario.auto_approve_commands,
            task_class=scenario.task_class,
            severity=scenario.severity,
            failure_modes=scenario.failure_modes,
            tags=scenario.tags,
        )
        for scenario in list_executable_eval_scenarios(pack)
    ]
    return _run_eval_scenarios(
        scenarios,
        base_session_dir=base_session_dir,
        artifact_dir=artifact_dir,
        run_label=run_label,
        scenario_pack_id=pack.pack_id,
    )


def _run_eval_scenarios(
    scenarios: list[EvalScenario],
    *,
    base_session_dir: Path | None,
    artifact_dir: Path | None,
    run_label: str | None,
    scenario_pack_id: str | None,
) -> EvalSummary:
    results: list[EvalResult] = []
    with TemporaryDirectory(prefix="coding-agent-v1-evals-") as tmp_dir:
        root = Path(tmp_dir)
        for scenario in scenarios:
            workspace = root / scenario.name
            workspace.mkdir(parents=True, exist_ok=True)
            _setup_workspace(workspace, scenario.setup_kind)
            session_dir = (
                base_session_dir / scenario.name
                if base_session_dir is not None
                else workspace / "sessions"
            )
            store = SessionStore(session_dir)
            started_at = time.monotonic()
            record = _run_scenario(scenario, workspace, store)
            duration_seconds = time.monotonic() - started_at
            passed, outcome_reason = _evaluate_scenario_outcome(scenario, workspace, record)
            results.append(
                EvalResult(
                    scenario_name=scenario.name,
                    passed=passed,
                    session_id=record.session_id,
                    status=record.status.value,
                    final_report=record.final_report,
                    outcome_reason=outcome_reason,
                    duration_seconds=round(duration_seconds, 6),
                    task_class=scenario.task_class,
                    severity=scenario.severity,
                    failure_modes=scenario.failure_modes,
                    tags=scenario.tags,
                )
            )
    passed_count = sum(1 for result in results if result.passed)
    summary = EvalSummary(
        total=len(results),
        passed=passed_count,
        failed=len(results) - passed_count,
        results=results,
        created_at=datetime.now(timezone.utc).isoformat(),
        run_label=run_label,
        scenario_pack_id=scenario_pack_id,
    )
    if artifact_dir is not None:
        summary.artifact_path = write_eval_summary(summary, artifact_dir)
    return summary


def summarize_eval_summary(summary: EvalSummary) -> str:
    lines = [
        f"total: {summary.total}",
        f"passed: {summary.passed}",
        f"failed: {summary.failed}",
        f"created_at: {summary.created_at}",
    ]
    if summary.scenario_pack_id is not None:
        lines.append(f"scenario_pack_id: {summary.scenario_pack_id}")
    if summary.run_label is not None:
        lines.append(f"run_label: {summary.run_label}")
    if summary.artifact_path is not None:
        lines.append(f"artifact_path: {summary.artifact_path}")
    for result in summary.results:
        outcome = "passed" if result.passed else "failed"
        lines.append(
            (
                f"{result.scenario_name}: {outcome} status={result.status} "
                f"task_class={result.task_class} duration_seconds={result.duration_seconds} "
                f"reason={result.outcome_reason} "
                f"session_id={result.session_id}"
            )
        )
    return "\n".join(lines)


def write_eval_summary(summary: EvalSummary, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-summary-{uuid4().hex}.json"
    payload = asdict(summary)
    payload["artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def load_eval_summary(path: Path) -> EvalSummary:
    payload = json.loads(path.read_text(encoding="utf-8"))
    results = [
        EvalResult(
            scenario_name=result["scenario_name"],
            passed=bool(result["passed"]),
            session_id=result["session_id"],
            status=result["status"],
            final_report=result["final_report"],
            outcome_reason=result["outcome_reason"],
            duration_seconds=float(result["duration_seconds"]),
            task_class=result.get("task_class", "unknown"),
            severity=result.get("severity", "core"),
            failure_modes=tuple(result.get("failure_modes", [])),
            tags=tuple(result.get("tags", [])),
        )
        for result in payload["results"]
    ]
    artifact_path_value = payload.get("artifact_path")
    return EvalSummary(
        total=int(payload["total"]),
        passed=int(payload["passed"]),
        failed=int(payload["failed"]),
        results=results,
        created_at=str(payload.get("created_at", "")),
        run_label=payload.get("run_label"),
        artifact_path=Path(artifact_path_value) if artifact_path_value else None,
        scenario_pack_id=payload.get("scenario_pack_id"),
    )


def compare_eval_summaries(
    baseline: EvalSummary,
    candidate: EvalSummary,
) -> EvalComparisonSummary:
    baseline_by_name = {result.scenario_name: result for result in baseline.results}
    candidate_by_name = {result.scenario_name: result for result in candidate.results}
    scenario_names = sorted(set(baseline_by_name) | set(candidate_by_name))
    results: list[EvalComparisonResult] = []
    regressions = 0
    improvements = 0
    unchanged = 0
    for scenario_name in scenario_names:
        baseline_result = baseline_by_name.get(scenario_name)
        candidate_result = candidate_by_name.get(scenario_name)
        baseline_passed = baseline_result.passed if baseline_result is not None else False
        candidate_passed = candidate_result.passed if candidate_result is not None else False
        if baseline_passed and not candidate_passed:
            classification = "regression"
            regressions += 1
        elif not baseline_passed and candidate_passed:
            classification = "improvement"
            improvements += 1
        else:
            classification = "unchanged"
            unchanged += 1
        baseline_duration = baseline_result.duration_seconds if baseline_result is not None else 0.0
        candidate_duration = candidate_result.duration_seconds if candidate_result is not None else 0.0
        results.append(
            EvalComparisonResult(
                scenario_name=scenario_name,
                task_class=(
                    baseline_result.task_class
                    if baseline_result is not None
                    else candidate_result.task_class
                    if candidate_result is not None
                    else "unknown"
                ),
                baseline_passed=baseline_passed,
                candidate_passed=candidate_passed,
                classification=classification,
                duration_delta_seconds=round(candidate_duration - baseline_duration, 6),
                baseline_reason=baseline_result.outcome_reason if baseline_result is not None else "missing from baseline",
                candidate_reason=candidate_result.outcome_reason if candidate_result is not None else "missing from candidate",
                failure_modes=(
                    baseline_result.failure_modes
                    if baseline_result is not None and baseline_result.failure_modes
                    else candidate_result.failure_modes
                    if candidate_result is not None
                    else ()
                ),
            )
        )
    return EvalComparisonSummary(
        baseline_artifact_path=baseline.artifact_path,
        candidate_artifact_path=candidate.artifact_path,
        baseline_scenario_pack_id=baseline.scenario_pack_id,
        candidate_scenario_pack_id=candidate.scenario_pack_id,
        regressions=regressions,
        improvements=improvements,
        unchanged=unchanged,
        results=results,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def compare_eval_baseline_to_reference(
    artifact_dir: Path,
    baseline_name: str,
    *,
    candidate_reference: str = "latest-pass",
) -> EvalComparisonSummary:
    baseline_path = resolve_eval_artifact_reference(f"baseline:{baseline_name}", artifact_dir)
    baseline = load_eval_summary(baseline_path)
    candidate_path = resolve_eval_artifact_reference(
        _default_candidate_reference_for_baseline(baseline, candidate_reference),
        artifact_dir,
    )
    candidate = load_eval_summary(candidate_path)
    return compare_eval_summaries(baseline, candidate)


def auto_promote_eval_baseline(
    artifact_dir: Path,
    baseline_name: str,
    *,
    candidate_reference: str = "latest-pass",
) -> EvalPromotionDecision:
    baseline_path = resolve_eval_artifact_reference(f"baseline:{baseline_name}", artifact_dir)
    baseline = load_eval_summary(baseline_path)
    effective_candidate_reference = _default_candidate_reference_for_baseline(baseline, candidate_reference)
    comparison = compare_eval_baseline_to_reference(
        artifact_dir,
        baseline_name,
        candidate_reference=effective_candidate_reference,
    )
    if comparison.regressions > 0:
        return EvalPromotionDecision(
            baseline_name=baseline_name,
            candidate_reference=candidate_reference,
            promoted=False,
            comparison=comparison,
            artifact_path=comparison.candidate_artifact_path,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
    artifact_path, config_path = promote_eval_baseline(
        artifact_dir,
        baseline_name,
        reference=effective_candidate_reference,
    )
    return EvalPromotionDecision(
        baseline_name=baseline_name,
        candidate_reference=candidate_reference,
        promoted=True,
        comparison=comparison,
        artifact_path=artifact_path,
        config_path=config_path,
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def summarize_eval_comparison(summary: EvalComparisonSummary) -> str:
    lines = [
        f"regressions: {summary.regressions}",
        f"improvements: {summary.improvements}",
        f"unchanged: {summary.unchanged}",
        f"created_at: {summary.created_at}",
    ]
    if summary.baseline_scenario_pack_id is not None:
        lines.append(f"baseline_scenario_pack_id: {summary.baseline_scenario_pack_id}")
    if summary.candidate_scenario_pack_id is not None:
        lines.append(f"candidate_scenario_pack_id: {summary.candidate_scenario_pack_id}")
    if summary.artifact_path is not None:
        lines.append(f"artifact_path: {summary.artifact_path}")
    if summary.baseline_artifact_path is not None:
        lines.append(f"baseline_artifact_path: {summary.baseline_artifact_path}")
    if summary.candidate_artifact_path is not None:
        lines.append(f"candidate_artifact_path: {summary.candidate_artifact_path}")
    for result in summary.results:
        lines.append(
            (
                f"{result.scenario_name}: {result.classification} "
                f"task_class={result.task_class} "
                f"baseline_passed={result.baseline_passed} candidate_passed={result.candidate_passed} "
                f"duration_delta_seconds={result.duration_delta_seconds}"
            )
        )
    return "\n".join(lines)


def summarize_eval_promotion_decision(decision: EvalPromotionDecision) -> str:
    lines = [
        f"baseline_name: {decision.baseline_name}",
        f"candidate_reference: {decision.candidate_reference}",
        f"promoted: {decision.promoted}",
        f"created_at: {decision.created_at}",
    ]
    if decision.artifact_path is not None:
        lines.append(f"artifact_path: {decision.artifact_path}")
    if decision.config_path is not None:
        lines.append(f"config_path: {decision.config_path}")
    if decision.decision_artifact_path is not None:
        lines.append(f"decision_artifact_path: {decision.decision_artifact_path}")
    lines.append(summarize_eval_comparison(decision.comparison))
    return "\n".join(lines)


def write_eval_comparison_summary(summary: EvalComparisonSummary, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-comparison-{uuid4().hex}.json"
    payload = _jsonify_paths(asdict(summary))
    payload["artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    summary.artifact_path = path
    return path


def write_eval_promotion_decision(decision: EvalPromotionDecision, artifact_dir: Path) -> Path:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    path = artifact_dir / f"eval-promotion-{uuid4().hex}.json"
    payload = _jsonify_paths(asdict(decision))
    payload["decision_artifact_path"] = str(path)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    decision.decision_artifact_path = path
    return path


def summarize_eval_history(summary: EvalHistorySummary) -> str:
    lines = [f"artifacts: {len(summary.artifact_paths)}"]
    for path in summary.artifact_paths:
        lines.append(f"artifact_path: {path}")
    if summary.pack_counts:
        lines.append("scenario_packs:")
        for pack_id in sorted(summary.pack_counts):
            lines.append(f"  {pack_id}: {summary.pack_counts[pack_id]}")
    for trend in summary.scenario_trends:
        latest_entry = trend.history[-1]
        lines.append(
            (
                f"{trend.scenario_name}: runs={trend.runs} pass_count={trend.pass_count} "
                f"fail_count={trend.fail_count} latest_passed={trend.latest_passed} "
                f"latest_duration_seconds={trend.latest_duration_seconds} "
                f"average_duration_seconds={trend.average_duration_seconds} trend={trend.trend} "
                f"latest_created_at={latest_entry.created_at} latest_run_label={latest_entry.run_label} "
                f"latest_scenario_pack_id={latest_entry.scenario_pack_id}"
            )
        )
    return "\n".join(lines)


def build_eval_artifact_index(artifact_dir: Path) -> EvalArtifactIndex:
    entries: list[EvalArtifactIndexEntry] = []
    pack_counts: dict[str, int] = {}
    for path in sorted(artifact_dir.glob("eval-summary-*.json")):
        summary = load_eval_summary(path)
        total = summary.total
        pass_rate = round((summary.passed / total) * 100, 2) if total else 0.0
        pack_id = summary.scenario_pack_id or "unknown"
        pack_counts[pack_id] = pack_counts.get(pack_id, 0) + 1
        entries.append(
            EvalArtifactIndexEntry(
                artifact_path=path,
                created_at=summary.created_at,
                run_label=summary.run_label,
                scenario_pack_id=summary.scenario_pack_id,
                passed=summary.passed,
                total=summary.total,
                pass_rate=pass_rate,
            )
        )
    entries.sort(key=lambda entry: entry.created_at, reverse=True)
    return EvalArtifactIndex(artifact_dir=artifact_dir, pack_counts=pack_counts, entries=entries)


def summarize_eval_artifact_index(index: EvalArtifactIndex) -> str:
    lines = [
        f"artifact_dir: {index.artifact_dir}",
        f"artifacts: {len(index.entries)}",
    ]
    if index.pack_counts:
        lines.append("scenario_packs:")
        for pack_id in sorted(index.pack_counts):
            lines.append(f"  {pack_id}: {index.pack_counts[pack_id]}")
    for entry in index.entries:
        lines.append(
            (
                f"{entry.artifact_path.name}: created_at={entry.created_at} "
                f"run_label={entry.run_label} scenario_pack_id={entry.scenario_pack_id} "
                f"passed={entry.passed}/{entry.total} "
                f"pass_rate={entry.pass_rate}%"
            )
        )
    return "\n".join(lines)


def filter_eval_artifact_index(index: EvalArtifactIndex, selectors: list[str]) -> EvalArtifactIndex:
    allowed_pack_ids = _resolve_scenario_pack_selectors(selectors, index.pack_counts.keys())
    entries = [entry for entry in index.entries if (entry.scenario_pack_id or "unknown") in allowed_pack_ids]
    pack_counts: dict[str, int] = {}
    for entry in entries:
        pack_id = entry.scenario_pack_id or "unknown"
        pack_counts[pack_id] = pack_counts.get(pack_id, 0) + 1
    return EvalArtifactIndex(
        artifact_dir=index.artifact_dir,
        pack_counts=pack_counts,
        entries=entries,
    )


def load_eval_baseline_config(artifact_dir: Path) -> EvalBaselineConfig:
    path = _baseline_config_path(artifact_dir)
    if not path.exists():
        return EvalBaselineConfig(artifact_dir=artifact_dir, baselines={}, baseline_pack_ids={})
    payload = json.loads(path.read_text(encoding="utf-8"))
    baselines = {name: Path(value) for name, value in payload.get("baselines", {}).items()}
    baseline_pack_ids = {
        name: value
        for name, value in payload.get("baseline_pack_ids", {}).items()
    }
    return EvalBaselineConfig(
        artifact_dir=artifact_dir,
        baselines=baselines,
        baseline_pack_ids=baseline_pack_ids,
    )


def save_eval_baseline_reference(artifact_dir: Path, name: str, artifact_path: Path) -> Path:
    config = load_eval_baseline_config(artifact_dir)
    config.baselines[name] = artifact_path
    if artifact_path.exists():
        config.baseline_pack_ids[name] = load_eval_summary(artifact_path).scenario_pack_id
    elif name not in config.baseline_pack_ids:
        config.baseline_pack_ids[name] = None
    path = _baseline_config_path(artifact_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "baselines": {
            baseline_name: str(baseline_path)
            for baseline_name, baseline_path in sorted(config.baselines.items())
        },
        "baseline_pack_ids": {
            baseline_name: baseline_pack_id
            for baseline_name, baseline_pack_id in sorted(config.baseline_pack_ids.items())
            if baseline_pack_id is not None
        },
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def promote_eval_baseline(
    artifact_dir: Path,
    name: str,
    *,
    reference: str = "latest-pass",
) -> tuple[Path, Path]:
    artifact_path = resolve_eval_artifact_reference(reference, artifact_dir)
    config_path = save_eval_baseline_reference(artifact_dir, name, artifact_path)
    return artifact_path, config_path


def repair_eval_baseline_reference(
    artifact_dir: Path,
    name: str,
    *,
    reference: str | None = None,
) -> tuple[Path, Path, str]:
    config = load_eval_baseline_config(artifact_dir)
    existing_path = config.baselines.get(name)
    if existing_path is None:
        raise ValueError(f"No named baseline found: {name}")
    resolved_reference = reference
    if resolved_reference is None:
        baseline_pack_id = config.baseline_pack_ids.get(name)
        if baseline_pack_id is not None:
            resolved_reference = f"latest-pass:{baseline_pack_id}"
        else:
            resolved_reference = "latest-pass"
    artifact_path = resolve_eval_artifact_reference(resolved_reference, artifact_dir)
    config_path = save_eval_baseline_reference(artifact_dir, name, artifact_path)
    return artifact_path, config_path, resolved_reference


def summarize_eval_baseline_config(config: EvalBaselineConfig) -> str:
    lines = [
        f"artifact_dir: {config.artifact_dir}",
        f"baselines: {len(config.baselines)}",
    ]
    for entry in build_eval_baseline_summary_entries(config):
        line = f"{entry.name}: {entry.artifact_path} status={entry.status}"
        if entry.scenario_pack_id is not None:
            line += f" scenario_pack_id={entry.scenario_pack_id}"
        if entry.run_label is not None:
            line += f" run_label={entry.run_label}"
        if entry.created_at is not None:
            line += f" created_at={entry.created_at}"
        if entry.passed is not None and entry.total is not None and entry.pass_rate is not None:
            line += f" passed={entry.passed}/{entry.total} pass_rate={entry.pass_rate}%"
        lines.append(line)
    return "\n".join(lines)


def build_eval_baseline_summary_entries(config: EvalBaselineConfig) -> list[EvalBaselineSummaryEntry]:
    entries: list[EvalBaselineSummaryEntry] = []
    for name, path in sorted(config.baselines.items()):
        if not path.exists():
            entries.append(
                EvalBaselineSummaryEntry(
                    name=name,
                    artifact_path=path,
                    status="missing",
                    scenario_pack_id=config.baseline_pack_ids.get(name),
                    run_label=None,
                    created_at=None,
                    passed=None,
                    total=None,
                    pass_rate=None,
                )
            )
            continue
        summary = load_eval_summary(path)
        total = summary.total
        pass_rate = round((summary.passed / total) * 100, 2) if total else 0.0
        entries.append(
            EvalBaselineSummaryEntry(
                name=name,
                artifact_path=path,
                status="ok",
                scenario_pack_id=summary.scenario_pack_id,
                run_label=summary.run_label,
                created_at=summary.created_at,
                passed=summary.passed,
                total=summary.total,
                pass_rate=pass_rate,
            )
        )
    return entries


def build_eval_baseline_audit_summary(config: EvalBaselineConfig) -> EvalBaselineAuditSummary:
    entries: list[EvalBaselineAuditEntry] = []
    for name, path in sorted(config.baselines.items()):
        stored_pack_id = config.baseline_pack_ids.get(name)
        scenario_pack_id = stored_pack_id
        if path.exists():
            scenario_pack_id = load_eval_summary(path).scenario_pack_id
        recommended_reference = None
        recommended_artifact_path = None
        if scenario_pack_id is not None:
            recommended_reference = f"latest-pass:{scenario_pack_id}"
            try:
                recommended_artifact_path = resolve_eval_artifact_reference(recommended_reference, config.artifact_dir)
            except ValueError:
                recommended_artifact_path = None
        else:
            recommended_reference = "latest-pass"
            try:
                recommended_artifact_path = resolve_eval_artifact_reference(recommended_reference, config.artifact_dir)
            except ValueError:
                recommended_artifact_path = None

        if not path.exists():
            status = "missing" if recommended_artifact_path is not None else "missing-no-candidate"
        elif recommended_artifact_path is None:
            status = "no-candidate"
        elif path == recommended_artifact_path:
            status = "current"
        else:
            status = "stale"

        entries.append(
            EvalBaselineAuditEntry(
                name=name,
                artifact_path=path,
                status=status,
                scenario_pack_id=scenario_pack_id,
                recommended_reference=recommended_reference,
                recommended_artifact_path=recommended_artifact_path,
            )
        )
    return EvalBaselineAuditSummary(artifact_dir=config.artifact_dir, entries=entries)


def summarize_eval_baseline_audit(summary: EvalBaselineAuditSummary) -> str:
    lines = [
        f"artifact_dir: {summary.artifact_dir}",
        f"baselines: {len(summary.entries)}",
    ]
    for entry in summary.entries:
        line = f"{entry.name}: {entry.artifact_path} status={entry.status}"
        if entry.scenario_pack_id is not None:
            line += f" scenario_pack_id={entry.scenario_pack_id}"
        if entry.recommended_reference is not None:
            line += f" recommended_reference={entry.recommended_reference}"
        if entry.recommended_artifact_path is not None:
            line += f" recommended_artifact_path={entry.recommended_artifact_path}"
        lines.append(line)
    return "\n".join(lines)


def build_eval_artifact_prune_summary(
    artifact_dir: Path,
    *,
    keep_per_pack: int = 1,
) -> EvalArtifactPruneSummary:
    index = build_eval_artifact_index(artifact_dir)
    config = load_eval_baseline_config(artifact_dir)
    protected_reasons_by_path: dict[Path, list[str]] = {}

    for name, path in sorted(config.baselines.items()):
        if path.exists():
            protected_reasons_by_path.setdefault(path, []).append(f"named-baseline:{name}")

    per_pack_entries: dict[str, list[EvalArtifactIndexEntry]] = {}
    for entry in index.entries:
        pack_id = entry.scenario_pack_id or "unknown"
        per_pack_entries.setdefault(pack_id, []).append(entry)

    for pack_id, entries in per_pack_entries.items():
        for position, entry in enumerate(entries[:keep_per_pack], start=1):
            protected_reasons_by_path.setdefault(entry.artifact_path, []).append(
                f"latest-pack:{pack_id}:{position}"
            )
        passing_entries = [entry for entry in entries if entry.passed == entry.total]
        for position, entry in enumerate(passing_entries[:keep_per_pack], start=1):
            protected_reasons_by_path.setdefault(entry.artifact_path, []).append(
                f"latest-pass-pack:{pack_id}:{position}"
            )

    summary_entries: list[EvalArtifactPruneEntry] = []
    protected_count = 0
    prunable_count = 0
    for entry in index.entries:
        reasons = tuple(protected_reasons_by_path.get(entry.artifact_path, ()))
        if reasons:
            action = "protect"
            protected_count += 1
        else:
            action = "prune"
            prunable_count += 1
        summary_entries.append(
            EvalArtifactPruneEntry(
                artifact_path=entry.artifact_path,
                action=action,
                reasons=reasons,
                scenario_pack_id=entry.scenario_pack_id,
                run_label=entry.run_label,
            )
        )

    return EvalArtifactPruneSummary(
        artifact_dir=artifact_dir,
        keep_per_pack=keep_per_pack,
        protected_count=protected_count,
        prunable_count=prunable_count,
        entries=summary_entries,
    )


def summarize_eval_artifact_prune_summary(summary: EvalArtifactPruneSummary) -> str:
    lines = [
        f"artifact_dir: {summary.artifact_dir}",
        f"keep_per_pack: {summary.keep_per_pack}",
        f"protected: {summary.protected_count}",
        f"prunable: {summary.prunable_count}",
    ]
    for entry in summary.entries:
        line = f"{entry.artifact_path.name}: action={entry.action}"
        if entry.scenario_pack_id is not None:
            line += f" scenario_pack_id={entry.scenario_pack_id}"
        if entry.run_label is not None:
            line += f" run_label={entry.run_label}"
        if entry.reasons:
            line += f" reasons={','.join(entry.reasons)}"
        lines.append(line)
    return "\n".join(lines)


def apply_eval_artifact_prune_summary(summary: EvalArtifactPruneSummary) -> list[Path]:
    deleted_paths: list[Path] = []
    for entry in summary.entries:
        if entry.action != "prune":
            continue
        if entry.artifact_path.exists():
            entry.artifact_path.unlink()
            deleted_paths.append(entry.artifact_path)
    return deleted_paths


def build_eval_decision_artifact_prune_summary(
    artifact_dir: Path,
    *,
    keep_per_kind: int = 1,
    keep_per_pack: int = 1,
) -> EvalDecisionArtifactPruneSummary:
    decision_artifact_dir = artifact_dir / "decision-artifacts"
    eval_prune_summary = build_eval_artifact_prune_summary(artifact_dir, keep_per_pack=keep_per_pack)
    protected_eval_paths = {
        entry.artifact_path
        for entry in eval_prune_summary.entries
        if entry.action == "protect"
    }

    decision_entries: list[tuple[str, Path, tuple[Path, ...]]] = []
    for artifact_kind, pattern in (
        ("comparison", "eval-comparison-*.json"),
        ("promotion", "eval-promotion-*.json"),
    ):
        for path in sorted(decision_artifact_dir.glob(pattern)):
            decision_entries.append(
                (artifact_kind, path, _extract_referenced_eval_artifact_paths(path))
            )

    decision_entries.sort(key=lambda item: item[1].name, reverse=True)

    protected_reasons_by_path: dict[Path, list[str]] = {}
    by_kind: dict[str, list[Path]] = {}
    for artifact_kind, path, _ in decision_entries:
        by_kind.setdefault(artifact_kind, []).append(path)
    for artifact_kind, paths in by_kind.items():
        for position, path in enumerate(paths[:keep_per_kind], start=1):
            protected_reasons_by_path.setdefault(path, []).append(f"latest-kind:{artifact_kind}:{position}")

    for artifact_kind, path, referenced_paths in decision_entries:
        matched = [ref for ref in referenced_paths if ref in protected_eval_paths]
        if matched:
            protected_reasons_by_path.setdefault(path, []).append(
                "references-protected-eval"
            )

    summary_entries: list[EvalDecisionArtifactPruneEntry] = []
    protected_count = 0
    prunable_count = 0
    for artifact_kind, path, referenced_paths in decision_entries:
        reasons = tuple(protected_reasons_by_path.get(path, ()))
        if reasons:
            action = "protect"
            protected_count += 1
        else:
            action = "prune"
            prunable_count += 1
        summary_entries.append(
            EvalDecisionArtifactPruneEntry(
                artifact_path=path,
                artifact_kind=artifact_kind,
                action=action,
                reasons=reasons,
                referenced_artifact_paths=referenced_paths,
            )
        )

    return EvalDecisionArtifactPruneSummary(
        artifact_dir=decision_artifact_dir,
        keep_per_kind=keep_per_kind,
        protected_count=protected_count,
        prunable_count=prunable_count,
        entries=summary_entries,
    )


def summarize_eval_decision_artifact_prune_summary(summary: EvalDecisionArtifactPruneSummary) -> str:
    lines = [
        f"artifact_dir: {summary.artifact_dir}",
        f"keep_per_kind: {summary.keep_per_kind}",
        f"protected: {summary.protected_count}",
        f"prunable: {summary.prunable_count}",
    ]
    for entry in summary.entries:
        line = f"{entry.artifact_path.name}: kind={entry.artifact_kind} action={entry.action}"
        if entry.reasons:
            line += f" reasons={','.join(entry.reasons)}"
        if entry.referenced_artifact_paths:
            line += " referenced=" + ",".join(str(path) for path in entry.referenced_artifact_paths)
        lines.append(line)
    return "\n".join(lines)


def apply_eval_decision_artifact_prune_summary(summary: EvalDecisionArtifactPruneSummary) -> list[Path]:
    deleted_paths: list[Path] = []
    for entry in summary.entries:
        if entry.action != "prune":
            continue
        if entry.artifact_path.exists():
            entry.artifact_path.unlink()
            deleted_paths.append(entry.artifact_path)
    return deleted_paths


def resolve_eval_artifact_reference(reference: str, artifact_dir: Path) -> Path:
    candidate_path = Path(reference)
    if candidate_path.exists():
        return candidate_path
    baseline_match = _resolve_eval_baseline_reference(reference, artifact_dir)
    if baseline_match is not None:
        return baseline_match
    index = build_eval_artifact_index(artifact_dir)
    alias_match = _resolve_eval_artifact_alias(reference, index)
    if alias_match is not None:
        return alias_match
    matches = [entry for entry in index.entries if entry.run_label == reference]
    if not matches:
        raise ValueError(f"No eval artifact found for label: {reference}")
    if len(matches) > 1:
        raise ValueError(f"Multiple eval artifacts found for label: {reference}")
    return matches[0].artifact_path


def build_eval_history(summaries: list[EvalSummary]) -> EvalHistorySummary:
    scenario_names = sorted({result.scenario_name for summary in summaries for result in summary.results})
    trends: list[EvalScenarioTrend] = []
    artifact_paths = [summary.artifact_path for summary in summaries if summary.artifact_path is not None]
    pack_counts: dict[str, int] = {}
    for summary in summaries:
        pack_id = summary.scenario_pack_id or "unknown"
        pack_counts[pack_id] = pack_counts.get(pack_id, 0) + 1
    for scenario_name in scenario_names:
        history: list[EvalHistoryEntry] = []
        durations: list[float] = []
        for summary in summaries:
            result = next((item for item in summary.results if item.scenario_name == scenario_name), None)
            if result is None:
                continue
            history.append(
                EvalHistoryEntry(
                    artifact_path=summary.artifact_path,
                    created_at=summary.created_at or None,
                    run_label=summary.run_label,
                    scenario_pack_id=summary.scenario_pack_id,
                    passed=result.passed,
                    duration_seconds=result.duration_seconds,
                    outcome_reason=result.outcome_reason,
                )
            )
            durations.append(result.duration_seconds)
        pass_count = sum(1 for entry in history if entry.passed)
        fail_count = len(history) - pass_count
        latest = history[-1]
        average_duration_seconds = round(sum(durations) / len(durations), 6)
        trend = _duration_trend(history)
        trends.append(
            EvalScenarioTrend(
                scenario_name=scenario_name,
                runs=len(history),
                pass_count=pass_count,
                fail_count=fail_count,
                latest_passed=latest.passed,
                latest_duration_seconds=latest.duration_seconds,
                average_duration_seconds=average_duration_seconds,
                trend=trend,
                history=history,
            )
        )
    return EvalHistorySummary(
        artifact_paths=[path for path in artifact_paths],
        pack_counts=pack_counts,
        scenario_trends=trends,
    )


def filter_eval_summaries_by_pack(summaries: list[EvalSummary], selectors: list[str]) -> list[EvalSummary]:
    available_pack_ids = [(summary.scenario_pack_id or "unknown") for summary in summaries]
    allowed_pack_ids = _resolve_scenario_pack_selectors(selectors, available_pack_ids)
    return [summary for summary in summaries if (summary.scenario_pack_id or "unknown") in allowed_pack_ids]


def build_eval_task_class_summary(summary: EvalSummary) -> list[EvalTaskClassSummaryEntry]:
    grouped: dict[str, list[EvalResult]] = {}
    for result in summary.results:
        grouped.setdefault(result.task_class, []).append(result)
    entries: list[EvalTaskClassSummaryEntry] = []
    for task_class in sorted(grouped):
        results = grouped[task_class]
        entries.append(
            EvalTaskClassSummaryEntry(
                task_class=task_class,
                total=len(results),
                passed=sum(1 for result in results if result.passed),
                failed=sum(1 for result in results if not result.passed),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_task_class_summary(entries: list[EvalTaskClassSummaryEntry]) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.task_class}: passed={entry.passed}/{entry.total} "
                f"failed={entry.failed} scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def build_eval_failure_mode_summary(summary: EvalSummary) -> list[EvalFailureModeSummaryEntry]:
    grouped: dict[str, list[EvalResult]] = {}
    for result in summary.results:
        for failure_mode in result.failure_modes:
            grouped.setdefault(failure_mode, []).append(result)
    entries: list[EvalFailureModeSummaryEntry] = []
    for failure_mode in sorted(grouped):
        results = grouped[failure_mode]
        entries.append(
            EvalFailureModeSummaryEntry(
                failure_mode=failure_mode,
                scenario_count=len(results),
                passed=sum(1 for result in results if result.passed),
                failed=sum(1 for result in results if not result.passed),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_failure_mode_summary(entries: list[EvalFailureModeSummaryEntry]) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.failure_mode}: passed={entry.passed}/{entry.scenario_count} "
                f"failed={entry.failed} scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def build_eval_comparison_task_class_summary(
    comparison: EvalComparisonSummary,
) -> list[EvalTaskClassComparisonEntry]:
    grouped: dict[str, list[EvalComparisonResult]] = {}
    for result in comparison.results:
        grouped.setdefault(result.task_class, []).append(result)
    entries: list[EvalTaskClassComparisonEntry] = []
    for task_class in sorted(grouped):
        results = grouped[task_class]
        entries.append(
            EvalTaskClassComparisonEntry(
                task_class=task_class,
                regressions=sum(1 for result in results if result.classification == "regression"),
                improvements=sum(1 for result in results if result.classification == "improvement"),
                unchanged=sum(1 for result in results if result.classification == "unchanged"),
                scenario_names=tuple(sorted(result.scenario_name for result in results)),
            )
        )
    return entries


def summarize_eval_comparison_task_class_summary(
    entries: list[EvalTaskClassComparisonEntry],
) -> str:
    lines: list[str] = []
    for entry in entries:
        lines.append(
            (
                f"{entry.task_class}: regressions={entry.regressions} "
                f"improvements={entry.improvements} unchanged={entry.unchanged} "
                f"scenarios={','.join(entry.scenario_names)}"
            )
        )
    return "\n".join(lines)


def _setup_workspace(workspace: Path, setup_kind: str) -> None:
    if setup_kind == "repair":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "repair_nested_literal":
        (workspace / "parser.py").write_text(
            'def parse_status():\n    return "FAIL"\n',
            encoding="utf-8",
        )
        tests_dir = workspace / "tests" / "api"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_parser.py").write_text(
            (
                "from parser import parse_status\n\n\n"
                "def test_parse_status():\n"
                '    assert parse_status() == "OK"\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "repair_literal_regression_guard":
        (workspace / "status.py").write_text(
            (
                'def status_label():\n'
                '    return "bad"\n\n'
                "def format_output(value):\n"
                '    return f\"[{value}]\"\n'
            ),
            encoding="utf-8",
        )
        (workspace / "test_status.py").write_text(
            (
                "from status import status_label\n\n\n"
                "def test_status_label():\n"
                '    assert status_label() == "good"\n'
            ),
            encoding="utf-8",
        )
        (workspace / "test_formatting.py").write_text(
            (
                "from status import format_output\n\n\n"
                "def test_format_output():\n"
                '    assert format_output("x") == "[x]"\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "diagnose":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "inspect":
        (workspace / "README.md").write_text("demo project", encoding="utf-8")
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "rename":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a + b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "rename_fixture_refs":
        (workspace / "config.py").write_text(
            (
                "def parse_config(text):\n"
                "    return text.strip().split('=')\n"
            ),
            encoding="utf-8",
        )
        (workspace / "conftest.py").write_text(
            (
                "from config import parse_config\n\n\n"
                "def sample_config():\n"
                "    return parse_config('mode=debug')\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_config.py").write_text(
            (
                "from config import parse_config\n"
                "from conftest import sample_config\n\n\n"
                "def test_parse_config():\n"
                "    assert parse_config('mode=debug') == ['mode', 'debug']\n\n\n"
                "def test_sample_config_fixture():\n"
                "    assert sample_config() == ['mode', 'debug']\n"
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "rename_nested_package":
        package_dir = workspace / "reports"
        package_dir.mkdir(parents=True, exist_ok=True)
        (package_dir / "__init__.py").write_text("", encoding="utf-8")
        (package_dir / "render.py").write_text(
            (
                "def render_summary(value):\n"
                '    return f"summary:{value}"\n'
            ),
            encoding="utf-8",
        )
        tests_dir = workspace / "tests" / "unit"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_render.py").write_text(
            (
                "from reports.render import render_summary\n\n\n"
                "def test_render_summary():\n"
                '    assert render_summary("x") == "summary:x"\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "rename_ambiguous_mentions":
        (workspace / "status_tools.py").write_text(
            (
                "def status(value):\n"
                "    return value.upper()\n\n"
                "def status_code(value):\n"
                "    return f'status:{value}'\n"
            ),
            encoding="utf-8",
        )
        (workspace / "README.md").write_text(
            (
                "This repo documents status_code handling.\n"
                "The exact status symbol should be renamed, but status_code should stay unchanged.\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_status_tools.py").write_text(
            (
                "from status_tools import status, status_code\n\n\n"
                "def test_status():\n"
                '    assert status("ok") == "OK"\n\n\n'
                "def test_status_code():\n"
                '    assert status_code("x") == "status:x"\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_parser_accepts_verbose_flag():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "single_test_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_placeholder.py").write_text(
            "def test_placeholder():\n    assert True\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "module_aware_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_parser_has_verbose_action():\n"
                "    parser = build_parser()\n"
                "    assert any(action.dest == 'verbose' for action in parser._actions)\n"
            ),
            encoding="utf-8",
        )
        (workspace / "test_other.py").write_text(
            "def test_other():\n    assert True\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "diagnose_multi_test":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        first_tests = workspace / "tests" / "quoted"
        first_tests.mkdir(parents=True, exist_ok=True)
        (first_tests / "test_first.py").write_text(
            "from calc import add\n\n\ndef test_first():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        second_tests = workspace / "tests" / "linked"
        second_tests.mkdir(parents=True, exist_ok=True)
        (second_tests / "test_second.py").write_text(
            "from calc import add\n\n\ndef test_second():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "explicit_multi_test_cli_flag":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        first_tests = workspace / "tests" / "regression"
        first_tests.mkdir(parents=True, exist_ok=True)
        (first_tests / "test_targeted_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_targeted_cli_regression():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        second_tests = workspace / "tests" / "smoke"
        second_tests.mkdir(parents=True, exist_ok=True)
        (second_tests / "test_cli_smoke.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_cli_smoke():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "config_option":
        (workspace / "config.py").write_text(
            'DEFAULT_CONFIG = {"mode": "basic"}\n',
            encoding="utf-8",
        )
        (workspace / "test_config.py").write_text(
            (
                "from config import DEFAULT_CONFIG\n\n"
                "def test_timeout_config():\n"
                '    assert DEFAULT_CONFIG["timeout"] == 30\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "env_var":
        (workspace / "config.py").write_text(
            'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
            encoding="utf-8",
        )
        (workspace / "test_config.py").write_text(
            (
                "from config import DEFAULT_CONFIG\nimport os\n\n"
                "def test_profile_env_var():\n"
                '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
            ),
            encoding="utf-8",
        )
        return
    if setup_kind == "approval_boundary":
        (workspace / "test_sample.py").write_text(
            "def test_ok():\n    assert 1 == 1\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "diagnose_repo_fallback":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "resume_flow":
        (workspace / "README.md").write_text("project intro", encoding="utf-8")
        return
    if setup_kind == "resume_repair_flow":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "resume_diagnose_flow":
        (workspace / "calc.py").write_text(
            "def add(a, b):\n    return a - b\n",
            encoding="utf-8",
        )
        (workspace / "test_calc.py").write_text(
            "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
            encoding="utf-8",
        )
        return
    if setup_kind == "resume_validation_reminder":
        (workspace / "cli.py").write_text(
            (
                "import argparse\n\n"
                "def build_parser():\n"
                '    parser = argparse.ArgumentParser(description="demo")\n'
                "    return parser\n"
            ),
            encoding="utf-8",
        )
        tests_dir = workspace / "tests" / "regression"
        tests_dir.mkdir(parents=True, exist_ok=True)
        (tests_dir / "test_targeted_cli.py").write_text(
            (
                "from cli import build_parser\n\n"
                "def test_targeted_cli_regression():\n"
                "    parser = build_parser()\n"
                "    args = parser.parse_args(['--verbose'])\n"
                "    assert args.verbose is True\n"
            ),
            encoding="utf-8",
        )
        return
    raise ValueError(f"Unknown eval setup kind: {setup_kind}")


def _evaluate_scenario_outcome(
    scenario: EvalScenario,
    workspace: Path,
    record: SessionRecord,
) -> tuple[bool, str]:
    final_report = record.final_report
    if scenario.setup_kind == "repair":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after repair attempt"
        if "return a + b" in (workspace / "calc.py").read_text(encoding="utf-8"):
            return True, "repaired arithmetic bug and passed validation"
        return False, "expected arithmetic fix was not applied"
    if scenario.setup_kind == "repair_nested_literal":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after nested repair attempt"
        parser_text = (workspace / "parser.py").read_text(encoding="utf-8")
        if 'return "OK"' not in parser_text:
            return False, "expected nested literal repair was not applied"
        if "tests/api/test_parser.py" not in final_report:
            return False, "nested test path was not preserved in validation output"
        return True, "repaired nested-path literal bug and preserved targeted validation"
    if scenario.setup_kind == "repair_literal_regression_guard":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after regression-guard repair attempt"
        status_text = (workspace / "status.py").read_text(encoding="utf-8")
        if 'return "good"' not in status_text:
            return False, "expected literal repair was not applied"
        if 'return f"[{value}]"' not in status_text:
            return False, "formatting helper was unexpectedly changed"
        return True, "repaired literal bug without breaking formatting behavior"
    if scenario.setup_kind == "rename":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after rename attempt"
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        test_text = (workspace / "test_calc.py").read_text(encoding="utf-8")
        if "def plus(a, b):" in calc_text and "from calc import plus" in test_text:
            return True, "renamed symbol across source and test files and passed validation"
        return False, "expected rename edits were not applied"
    if scenario.setup_kind == "rename_fixture_refs":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after fixture-reference rename"
        config_text = (workspace / "config.py").read_text(encoding="utf-8")
        fixture_text = (workspace / "conftest.py").read_text(encoding="utf-8")
        test_text = (workspace / "test_config.py").read_text(encoding="utf-8")
        if "def load_config(text):" not in config_text:
            return False, "expected source rename was not applied"
        if "from config import load_config" not in fixture_text:
            return False, "fixture import was not updated"
        if "from config import load_config" not in test_text:
            return False, "test import was not updated"
        if "load_config('mode=debug')" not in test_text:
            return False, "test call site was not updated"
        if "sample_config() == ['mode', 'debug']" not in test_text:
            return False, "test references were not updated consistently"
        return True, "renamed source, fixture, and test references consistently"
    if scenario.setup_kind == "rename_nested_package":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after nested-package rename"
        render_text = (workspace / "reports" / "render.py").read_text(encoding="utf-8")
        test_text = (workspace / "tests" / "unit" / "test_render.py").read_text(encoding="utf-8")
        if "def render_report(value):" not in render_text:
            return False, "expected nested source rename was not applied"
        if "from reports.render import render_report" not in test_text:
            return False, "nested test import was not updated"
        if "tests/unit/test_render.py" not in final_report:
            return False, "nested test validation path was not preserved"
        return True, "renamed nested-package symbol and preserved nested test validation"
    if scenario.setup_kind == "rename_ambiguous_mentions":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after ambiguous rename"
        source_text = (workspace / "status_tools.py").read_text(encoding="utf-8")
        readme_text = (workspace / "README.md").read_text(encoding="utf-8")
        test_text = (workspace / "test_status_tools.py").read_text(encoding="utf-8")
        if "def state(value):" not in source_text:
            return False, "expected primary symbol rename was not applied"
        if "status_code" not in source_text or "status_code" not in readme_text:
            return False, "ambiguous status_code references were changed unexpectedly"
        if "from status_tools import state, status_code" not in test_text:
            return False, "test import was not updated consistently"
        return True, "renamed the intended symbol while preserving ambiguous status_code references"
    if scenario.setup_kind == "cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after feature edit"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' in cli_text:
            return True, "added requested CLI flag and passed validation"
        return False, "expected CLI flag edit was not applied"
    if scenario.setup_kind == "single_test_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after single-test fallback feature edit"
        if record.task_plan is None:
            return False, "single-test fallback task plan was missing"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "selected validation command `pytest -q test_placeholder.py` from single-test workspace fallback"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "single-test fallback reasoning was not recorded in the task plan"
        return True, "added requested CLI flag and recorded single-test workspace fallback validation"
    if scenario.setup_kind == "module_aware_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after module-aware CLI feature edit"
        if record.task_plan is None:
            return False, "module-aware CLI task plan was missing"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "selected validation command `pytest -q test_cli.py` from module-aware CLI parser test evidence"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "module-aware CLI reasoning was not recorded in the task plan"
        return True, "added requested CLI flag and recorded module-aware CLI validation"
    if scenario.setup_kind == "explicit_multi_test_cli_flag":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after explicit multi-test feature edit"
        cli_text = (workspace / "cli.py").read_text(encoding="utf-8")
        if 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' not in cli_text:
            return False, "expected CLI flag edit was not applied"
        if (
            "tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py"
            not in final_report
        ):
            return False, "explicit multi-test validation command was not preserved in the report"
        return True, "added requested CLI flag and preserved explicit multi-test validation"
    if scenario.setup_kind == "config_option":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after config feature edit"
        config_text = (workspace / "config.py").read_text(encoding="utf-8")
        if '"timeout": 30' in config_text:
            return True, "added requested config option and passed validation"
        return False, "expected config option edit was not applied"
    if scenario.setup_kind == "env_var":
        if "Validation passed via run_command." not in final_report:
            return False, "validation did not pass after env var feature edit"
        config_text = (workspace / "config.py").read_text(encoding="utf-8")
        if '"profile": os.getenv("APP_PROFILE", "advanced")' in config_text:
            return True, "added requested environment-variable config option and passed validation"
        return False, "expected environment-variable config edit was not applied"
    if scenario.setup_kind == "inspect":
        if "Task flow: inspect." not in final_report:
            return False, "inspect flow report marker was missing"
        if "No validation was run." not in final_report:
            return False, "inspect flow did not report skipped validation"
        if "README.md" not in final_report:
            return False, "inspect flow did not report README inspection"
        if record.task_plan is None:
            return False, "inspect scenario task plan was missing"
        if (
            "inspect evidence: request asks for repo inspection and README.md is available for context"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "inspect scenario did not record explicit inspect reasoning"
        return True, "summarized repository via explicit inspect planning"
    if scenario.setup_kind == "approval_boundary":
        if "approval is required" not in final_report.lower():
            return False, "expected approval boundary message was missing"
        if record.task_plan is None:
            return False, "approval-boundary task plan was missing"
        if (
            "selected validation command `pytest -q` from full-suite fallback because no narrower test target was justified"
            not in " ".join(record.task_plan.reasons)
        ):
            return False, "approval-boundary scenario did not record full-suite fallback reasoning"
        if record.task_plan.validation_command == "pytest -q":
            return True, "correctly stopped on approval boundary after selecting full-suite fallback validation"
        return False, "expected approval boundary message was missing"
    if scenario.setup_kind == "diagnose":
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose flow report marker was missing"
        if "without applying edits" not in final_report:
            return False, "diagnose flow did not report no-edit completion"
        if "return a - b" in calc_text:
            return True, "gathered failure evidence without editing files"
        return False, "diagnose flow unexpectedly edited source files"
    if scenario.setup_kind == "diagnose_multi_test":
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose flow report marker was missing"
        if "without applying edits" not in final_report:
            return False, "diagnose flow did not report no-edit completion"
        if "tests/quoted/test_first.py tests/linked/test_second.py" not in final_report:
            return False, "mixed-format multi-test diagnose validation command was not preserved in the report"
        if "return a - b" in calc_text:
            return True, "gathered multi-test failure evidence without editing files"
        return False, "diagnose flow unexpectedly edited source files"
    if scenario.setup_kind == "diagnose_repo_fallback":
        calc_text = (workspace / "calc.py").read_text(encoding="utf-8")
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose flow report marker was missing"
        if "without applying edits" not in final_report:
            return False, "diagnose flow did not report no-edit completion"
        if "return a - b" in calc_text:
            return True, "produced bounded diagnosis from workspace context without editing files"
        return False, "diagnose fallback unexpectedly edited source files"
    if scenario.setup_kind == "resume_flow":
        if (
            "Resumed from session " in final_report
            and "README.md" in final_report
        ):
            return True, "resumed prior session context and produced a resumed report"
        return False, "resume flow did not carry prior session context into the report"
    if scenario.setup_kind == "resume_repair_flow":
        if "Resumed from session " not in final_report:
            return False, "repair resume did not reference the prior session"
        if "Task flow: fix." not in final_report:
            return False, "repair resume did not stay in the fix flow"
        if "Validation passed via run_command." not in final_report:
            return False, "repair resume did not rerun validation"
        return True, "resumed prior repair context and reran validation in fix flow"
    if scenario.setup_kind == "resume_diagnose_flow":
        if "Resumed from session " not in final_report:
            return False, "diagnose resume did not reference the prior session"
        if "Task flow: diagnose." not in final_report:
            return False, "diagnose resume did not stay in the diagnose flow"
        if "without applying edits" not in final_report:
            return False, "diagnose resume did not preserve no-edit behavior"
        return True, "resumed prior diagnose context without switching into edit mode"
    if scenario.setup_kind == "resume_validation_reminder":
        if "Resumed from session " not in final_report:
            return False, "validation-reminder resume did not reference the prior session"
        if "Validation passed via run_command." not in final_report:
            return False, "validation-reminder resume did not rerun validation"
        if "tests/regression/test_targeted_cli.py" not in final_report:
            return False, "targeted validation path was not preserved on resume"
        return True, "resumed prior feature work and reran the targeted validation command"
    return False, "unknown eval scenario kind"


def _run_scenario(scenario: EvalScenario, workspace: Path, store: SessionStore):
    if scenario.setup_kind == "resume_flow":
        first = run_session(
            "summarize this repo",
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
        )
        return run_session(
            scenario.request,
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
            resume_from_session_id=first.session_id,
        )
    if scenario.setup_kind == "resume_repair_flow":
        first = run_session(
            "fix the failing test",
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
        )
        return run_session(
            scenario.request,
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
            resume_from_session_id=first.session_id,
        )
    if scenario.setup_kind == "resume_diagnose_flow":
        first = run_session(
            "investigate the failing tests",
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
        )
        return run_session(
            scenario.request,
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
            resume_from_session_id=first.session_id,
        )
    if scenario.setup_kind == "resume_validation_reminder":
        first = run_session(
            "add a --verbose flag",
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
        )
        return run_session(
            scenario.request,
            workspace,
            store,
            auto_approve_commands=scenario.auto_approve_commands,
            resume_from_session_id=first.session_id,
        )
    return run_session(
        scenario.request,
        workspace,
        store,
        auto_approve_commands=scenario.auto_approve_commands,
    )


def _duration_trend(history: list[EvalHistoryEntry]) -> str:
    if len(history) < 2:
        return "insufficient-data"
    first = history[0].duration_seconds
    last = history[-1].duration_seconds
    delta = last - first
    if abs(delta) < 0.000001:
        return "flat"
    if delta < 0:
        return "faster"
    return "slower"


_SCENARIO_PACK_ALIASES = {
    "built-in": "built-in",
    "builtin": "built-in",
    "smoke": "coding-agent-v1-smoke",
    "core": "coding-agent-v1-core",
    "stress": "coding-agent-v1-stress",
}


def _resolve_scenario_pack_selector(selector: str, index: EvalArtifactIndex) -> str | None:
    normalized = selector.strip().lower()
    alias_match = _SCENARIO_PACK_ALIASES.get(normalized)
    if alias_match is not None:
        return alias_match
    available_pack_ids = {entry.scenario_pack_id for entry in index.entries if entry.scenario_pack_id is not None}
    if selector in available_pack_ids:
        return selector
    return None


def _resolve_scenario_pack_selectors(selectors: list[str], available_pack_ids: list[str] | set[str]) -> set[str]:
    available = set(available_pack_ids)
    resolved: set[str] = set()
    for selector in selectors:
        normalized = selector.strip().lower()
        alias_match = _SCENARIO_PACK_ALIASES.get(normalized)
        if alias_match is not None:
            resolved.add(alias_match)
            continue
        if selector in available:
            resolved.add(selector)
            continue
        raise ValueError(f"Unknown scenario pack selector: {selector}")
    return resolved


def _resolve_eval_artifact_alias(reference: str, index: EvalArtifactIndex) -> Path | None:
    if reference == "latest":
        if not index.entries:
            raise ValueError("No eval artifacts are available.")
        return index.entries[0].artifact_path
    if reference == "latest-pass":
        passing_entries = [entry for entry in index.entries if entry.passed == entry.total]
        if not passing_entries:
            raise ValueError("No fully passing eval artifacts are available.")
        return passing_entries[0].artifact_path
    if reference.startswith("latest-pass:"):
        selector = reference.split(":", 1)[1]
        pack_id = _resolve_scenario_pack_selector(selector, index)
        if pack_id is not None:
            matching_entries = [
                entry
                for entry in index.entries
                if entry.passed == entry.total and entry.scenario_pack_id == pack_id
            ]
            if not matching_entries:
                raise ValueError(f"No fully passing eval artifact found for scenario pack: {selector}")
            return matching_entries[0].artifact_path
        matching_entries = [
            entry
            for entry in index.entries
            if entry.passed == entry.total and entry.run_label is not None and entry.run_label.startswith(selector)
        ]
        if not matching_entries:
            raise ValueError(f"No fully passing eval artifact found for label prefix: {selector}")
        return matching_entries[0].artifact_path
    if reference.startswith("latest:"):
        selector = reference.split(":", 1)[1]
        pack_id = _resolve_scenario_pack_selector(selector, index)
        if pack_id is not None:
            matching_entries = [
                entry
                for entry in index.entries
                if entry.scenario_pack_id == pack_id
            ]
            if not matching_entries:
                raise ValueError(f"No eval artifact found for scenario pack: {selector}")
            return matching_entries[0].artifact_path
        matching_entries = [
            entry
            for entry in index.entries
            if entry.run_label is not None and entry.run_label.startswith(selector)
        ]
        if not matching_entries:
            raise ValueError(f"No eval artifact found for label prefix: {selector}")
        return matching_entries[0].artifact_path
    return None


def _resolve_eval_baseline_reference(reference: str, artifact_dir: Path) -> Path | None:
    if not reference.startswith("baseline:"):
        return None
    body = reference.split(":", 1)[1]
    if ":" in body:
        name, selector = body.split(":", 1)
    else:
        name, selector = body, None
    config = load_eval_baseline_config(artifact_dir)
    path = config.baselines.get(name)
    if path is None:
        raise ValueError(f"No named baseline found: {name}")
    if selector is not None:
        if path.exists():
            baseline_summary = load_eval_summary(path)
            baseline_pack_id = baseline_summary.scenario_pack_id or "unknown"
        else:
            baseline_pack_id = config.baseline_pack_ids.get(name) or "unknown"
        allowed_pack_ids = _resolve_scenario_pack_selectors([selector], [baseline_pack_id])
        if baseline_pack_id not in allowed_pack_ids:
            raise ValueError(f"Named baseline {name} does not match scenario pack selector: {selector}")
    return path


def _default_candidate_reference_for_baseline(baseline: EvalSummary, candidate_reference: str) -> str:
    if candidate_reference == "latest-pass" and baseline.scenario_pack_id is not None:
        return f"latest-pass:{baseline.scenario_pack_id}"
    return candidate_reference


def _baseline_config_path(artifact_dir: Path) -> Path:
    return artifact_dir / "named-baselines.json"


def _jsonify_paths(value):
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _jsonify_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonify_paths(item) for item in value]
    return value


def _extract_referenced_eval_artifact_paths(path: Path) -> tuple[Path, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    matches: list[Path] = []
    seen: set[Path] = set()

    def visit(value, *, key: str | None = None) -> None:
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                visit(nested_value, key=nested_key)
            return
        if isinstance(value, list):
            for item in value:
                visit(item, key=key)
            return
        if not isinstance(value, str):
            return
        if key is None or not key.endswith("_artifact_path"):
            return
        if key == "decision_artifact_path":
            return
        candidate = Path(value)
        if candidate.name.startswith("eval-summary-") and candidate not in seen:
            seen.add(candidate)
            matches.append(candidate)

    visit(payload)
    return tuple(matches)
