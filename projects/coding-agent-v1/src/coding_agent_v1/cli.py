from __future__ import annotations

import argparse
from pathlib import Path

from .agent_loop import run_session
from .eval_harness import (
    apply_eval_decision_artifact_prune_summary,
    apply_eval_artifact_prune_summary,
    auto_promote_eval_baseline,
    build_eval_baseline_audit_summary,
    build_eval_decision_artifact_index,
    build_eval_decision_artifact_prune_summary,
    build_eval_expectation_check_summary,
    build_eval_artifact_prune_summary,
    build_eval_artifact_index,
    build_eval_comparison_task_class_summary,
    build_eval_failure_mode_summary,
    build_eval_history,
    build_eval_task_class_summary,
    build_eval_trace_summary,
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
    summarize_eval_promotion_decision,
    summarize_eval_history,
    summarize_eval_summary,
    summarize_eval_task_class_summary,
    summarize_eval_trace_summary,
    write_eval_comparison_summary,
    write_eval_promotion_decision,
)
from .session_store import SessionStore


def _default_eval_pack_path() -> Path:
    return Path(__file__).resolve().parents[4] / "evals" / "coding-agent-v1" / "scenarios" / "core-v1.json"


_EVAL_REFERENCE_HELP = (
    "References can use artifact paths, run-label prefixes, "
    "latest-clean[:PACK], latest-pass[:PACK], or baseline:<NAME>."
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the Coding Agent V1 scaffold.",
        epilog=(
            "Common eval artifact references:\n"
            "  latest-clean            newest fully passing run with no expectation mismatches\n"
            "  latest-clean:core       newest clean run for the core pack\n"
            "  latest-pass             newest passing run, even if expectation checks regressed\n"
            "  baseline:main           named baseline saved in the eval artifact directory"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("request", nargs="?", help="The coding request to run.")
    parser.add_argument(
        "--cwd",
        default=".",
        help="Workspace path to inspect. Defaults to the current directory.",
    )
    parser.add_argument(
        "--session-dir",
        default=".coding-agent-v1/sessions",
        help="Directory where session JSON files will be written.",
    )
    parser.add_argument(
        "--auto-approve-commands",
        action="store_true",
        help="Automatically approve command execution for this session.",
    )
    parser.add_argument(
        "--planner-strategy",
        default="deterministic_heuristic",
        help="Planner strategy to use. Available: deterministic_heuristic, model_guided. model_guided requires model planner configuration.",
    )
    parser.add_argument(
        "--review-session",
        help="Load and print a saved session by id instead of running a new one.",
    )
    parser.add_argument(
        "--resume-session",
        help="Resume from a saved session id when running a new request.",
    )
    parser.add_argument(
        "--review-handoff",
        help="Load and print a saved handoff artifact by source session id.",
    )
    parser.add_argument(
        "--review-compact-context",
        help="Load and print a saved compact BPE continuation artifact by source session id.",
    )
    parser.add_argument(
        "--list-compact-contexts",
        action="store_true",
        help="List saved compact context artifacts.",
    )
    parser.add_argument(
        "--prune-compact-contexts",
        action="store_true",
        help="Plan pruning of compact context artifacts. Dry-run by default.",
    )
    parser.add_argument(
        "--prune-compact-contexts-apply",
        action="store_true",
        help="Apply deletions for --prune-compact-contexts instead of only printing the prune plan.",
    )
    parser.add_argument(
        "--prune-compact-keep-newest",
        type=int,
        default=20,
        help="How many newest compact context artifacts to keep when using --prune-compact-contexts.",
    )
    parser.add_argument(
        "--prune-compact-include-size-triggered",
        action="store_true",
        help="Allow pruning size-triggered compact contexts. By default they are protected.",
    )
    parser.add_argument(
        "--resume-handoff",
        help="Resume from a saved handoff artifact by source session id when running a new request.",
    )
    parser.add_argument(
        "--review-repair-record",
        help="Load and print a procedural repair record by repair id.",
    )
    parser.add_argument(
        "--set-repair-record-status",
        nargs=2,
        metavar=("REPAIR_ID", "STATUS"),
        help="Update a procedural repair record status to candidate, accepted, rejected, or retired.",
    )
    parser.add_argument(
        "--repair-status-reason",
        default="",
        help="Optional reason saved in the repair status audit when using --set-repair-record-status.",
    )
    parser.add_argument(
        "--repair-status-actor",
        default="cli",
        help="Actor saved in the repair status audit when using --set-repair-record-status.",
    )
    parser.add_argument(
        "--list-repair-status-audits",
        nargs="?",
        const="",
        metavar="REPAIR_ID",
        help="List repair status audit records, optionally scoped to one repair id.",
    )
    parser.add_argument(
        "--review-repair-status-audit",
        help="Load and print a repair status audit by audit id.",
    )
    parser.add_argument(
        "--list-repair-records",
        action="store_true",
        help="List saved procedural repair records.",
    )
    parser.add_argument(
        "--run-evals",
        action="store_true",
        help="Run the default external eval benchmark pack and print summaries.",
    )
    parser.add_argument(
        "--run-smoke-evals",
        action="store_true",
        help="Run the built-in smoke eval scenarios and print summaries.",
    )
    parser.add_argument(
        "--run-eval-pack",
        nargs="?",
        const=str(_default_eval_pack_path()),
        metavar="PACK_PATH",
        help="Run an external eval scenario pack. Defaults to the coding-agent-v1 core pack.",
    )
    parser.add_argument(
        "--eval-label",
        help="Optional label to store on a new eval artifact when using --run-evals.",
    )
    parser.add_argument(
        "--eval-planner-strategy",
        help="Override planner_strategy for each scenario when using --run-evals or --run-eval-pack.",
    )
    parser.add_argument(
        "--compare-evals",
        nargs=2,
        metavar=("BASELINE", "CANDIDATE"),
        help=f"Compare two saved eval summary artifacts. {_EVAL_REFERENCE_HELP}",
    )
    parser.add_argument(
        "--history-evals",
        nargs="+",
        metavar="ARTIFACT",
        help=f"Summarize scenario trends across multiple saved eval summary artifacts. {_EVAL_REFERENCE_HELP}",
    )
    parser.add_argument(
        "--list-evals",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="List saved eval artifacts by date, label, and pass rate.",
    )
    parser.add_argument(
        "--eval-pack-filter",
        action="append",
        metavar="PACK",
        help="Filter --list-evals or --history-evals to scenario-pack tiers like built-in, smoke, core, or stress.",
    )
    parser.add_argument(
        "--prune-evals",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Plan pruning of saved eval summary artifacts while protecting named baselines and recent per-pack runs.",
    )
    parser.add_argument(
        "--prune-evals-apply",
        action="store_true",
        help="Apply deletions for --prune-evals instead of only printing the prune plan.",
    )
    parser.add_argument(
        "--prune-keep-per-pack",
        type=int,
        default=1,
        help="How many newest and newest-passing artifacts to retain per scenario pack when using --prune-evals.",
    )
    parser.add_argument(
        "--prune-decision-artifacts",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Plan pruning of decision artifacts while protecting those that reference retained eval summaries.",
    )
    parser.add_argument(
        "--list-decision-artifacts",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="List saved decision artifacts by kind, date, and referenced eval summaries.",
    )
    parser.add_argument(
        "--decision-artifact-kind",
        action="append",
        metavar="KIND",
        help="Filter --list-decision-artifacts or --prune-decision-artifacts to artifact kinds like comparison or promotion.",
    )
    parser.add_argument(
        "--prune-decision-artifacts-apply",
        action="store_true",
        help="Apply deletions for --prune-decision-artifacts instead of only printing the prune plan.",
    )
    parser.add_argument(
        "--prune-decision-keep-per-kind",
        type=int,
        default=1,
        help="How many newest decision artifacts to retain per decision kind when using --prune-decision-artifacts.",
    )
    parser.add_argument(
        "--set-eval-baseline",
        nargs=2,
        metavar=("NAME", "REFERENCE"),
        help=f"Save a named baseline that points to an eval artifact reference. {_EVAL_REFERENCE_HELP}",
    )
    parser.add_argument(
        "--list-eval-baselines",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="List named eval baselines stored for an artifact directory.",
    )
    parser.add_argument(
        "--promote-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help=(
            "Promote an eval artifact reference into a named baseline. "
            "Defaults to latest-pass. Use latest-clean[:PACK] to prefer fully clean runs."
        ),
    )
    parser.add_argument(
        "--compare-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help=(
            "Compare baseline:<NAME> against a reference. Defaults to latest-pass. "
            "Use latest-clean[:PACK] to compare against the newest fully clean run."
        ),
    )
    parser.add_argument(
        "--auto-promote-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help=(
            "Promote a candidate into a baseline only if comparison shows no regressions. "
            "Defaults to latest-pass. Use latest-clean[:PACK] to gate on fully clean runs."
        ),
    )
    parser.add_argument(
        "--repair-eval-baseline",
        nargs="+",
        metavar=("NAME", "REFERENCE"),
        help=(
            "Repair a named baseline by repointing it to a resolved artifact reference. "
            "Defaults to the preferred latest reference for the saved baseline pack, "
            "favoring latest-clean before latest-pass."
        ),
    )
    parser.add_argument(
        "--audit-eval-baselines",
        nargs="?",
        const=".coding-agent-v1/sessions/eval-artifacts",
        metavar="ARTIFACT_DIR",
        help="Audit named eval baselines for missing or stale artifact targets.",
    )
    parser.add_argument(
        "--review-eval-comparison",
        nargs="?",
        const="latest-comparison",
        metavar="ARTIFACT_PATH",
        help="Load and print a saved eval comparison artifact. Defaults to latest-comparison.",
    )
    parser.add_argument(
        "--review-eval-promotion",
        nargs="?",
        const="latest-promotion",
        metavar="ARTIFACT_PATH",
        help="Load and print a saved eval promotion decision artifact. Defaults to latest-promotion.",
    )
    return parser


def _print_eval_summary_with_breakdowns(summary) -> None:
    print(summarize_eval_summary(summary))
    task_class_summary = build_eval_task_class_summary(summary)
    if task_class_summary:
        print("")
        print("task_class_summary:")
        print(summarize_eval_task_class_summary(task_class_summary))
    failure_mode_summary = build_eval_failure_mode_summary(summary)
    if failure_mode_summary:
        print("")
        print("failure_mode_summary:")
        print(summarize_eval_failure_mode_summary(failure_mode_summary))
    trace_summary = build_eval_trace_summary(summary)
    if trace_summary:
        print("")
        print("trace_summary:")
        print(summarize_eval_trace_summary(trace_summary))
        tool_sequence_summary = build_eval_expectation_check_summary("tool_sequence", trace_summary)
        if tool_sequence_summary is not None:
            print("")
            print("tool_sequence_expectation_summary:")
            print(
                f"matched={tool_sequence_summary.matched}/{tool_sequence_summary.total} "
                f"unmatched={','.join(tool_sequence_summary.unmatched_scenario_names)}"
            )
        escalation_summary = build_eval_expectation_check_summary("escalation", trace_summary)
        if escalation_summary is not None:
            print("")
            print("escalation_expectation_summary:")
            print(
                f"matched={escalation_summary.matched}/{escalation_summary.total} "
                f"unmatched={','.join(escalation_summary.unmatched_scenario_names)}"
            )


def _print_eval_comparison_with_breakdowns(comparison) -> None:
    print(summarize_eval_comparison(comparison))
    task_class_summary = build_eval_comparison_task_class_summary(comparison)
    if task_class_summary:
        print("")
        print("task_class_comparison_summary:")
        print(summarize_eval_comparison_task_class_summary(task_class_summary))
    if comparison.tool_sequence_expectation_comparison:
        print("")
        print("tool_sequence_expectation_comparison_summary:")
        for entry in comparison.tool_sequence_expectation_comparison:
            print(
                f"{entry.label}: baseline={entry.baseline_matched}/{entry.baseline_total} "
                f"candidate={entry.candidate_matched}/{entry.candidate_total} "
                f"matched_delta={entry.matched_delta}"
            )
    if comparison.escalation_expectation_comparison:
        print("")
        print("escalation_expectation_comparison_summary:")
        for entry in comparison.escalation_expectation_comparison:
            print(
                f"{entry.label}: baseline={entry.baseline_matched}/{entry.baseline_total} "
                f"candidate={entry.candidate_matched}/{entry.candidate_total} "
                f"matched_delta={entry.matched_delta}"
            )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    selected_eval_modes = sum(
        1
        for enabled in (
            args.run_evals,
            args.run_smoke_evals,
            bool(args.run_eval_pack),
        )
        if enabled
    )
    if selected_eval_modes > 1:
        parser.error("--run-evals, --run-smoke-evals, and --run-eval-pack are mutually exclusive")
    if args.eval_planner_strategy and not (args.run_evals or args.run_eval_pack):
        parser.error("--eval-planner-strategy can only be used with --run-evals or --run-eval-pack")
    if args.eval_pack_filter and args.list_evals is None and not args.history_evals:
        parser.error("--eval-pack-filter can only be used with --list-evals or --history-evals")
    if (
        args.decision_artifact_kind
        and args.list_decision_artifacts is None
        and args.prune_decision_artifacts is None
    ):
        parser.error(
            "--decision-artifact-kind can only be used with --list-decision-artifacts or --prune-decision-artifacts"
        )
    if args.prune_evals_apply and args.prune_evals is None:
        parser.error("--prune-evals-apply requires --prune-evals")
    if args.prune_decision_artifacts_apply and args.prune_decision_artifacts is None:
        parser.error("--prune-decision-artifacts-apply requires --prune-decision-artifacts")
    if args.prune_compact_contexts_apply and not args.prune_compact_contexts:
        parser.error("--prune-compact-contexts-apply requires --prune-compact-contexts")
    if args.prune_keep_per_pack < 1:
        parser.error("--prune-keep-per-pack must be at least 1")
    if args.prune_decision_keep_per_kind < 1:
        parser.error("--prune-decision-keep-per-kind must be at least 1")
    if args.prune_compact_keep_newest < 1:
        parser.error("--prune-compact-keep-newest must be at least 1")
    if args.resume_session and args.resume_handoff:
        parser.error("--resume-session and --resume-handoff are mutually exclusive")
    if args.review_eval_comparison and args.review_eval_promotion:
        parser.error("--review-eval-comparison and --review-eval-promotion are mutually exclusive")
    store = SessionStore(Path(args.session_dir))
    if args.prune_evals is not None:
        artifact_dir = Path(args.prune_evals)
        summary = build_eval_artifact_prune_summary(
            artifact_dir,
            keep_per_pack=args.prune_keep_per_pack,
        )
        print(summarize_eval_artifact_prune_summary(summary))
        if args.prune_evals_apply:
            deleted_paths = apply_eval_artifact_prune_summary(summary)
            print(f"deleted: {len(deleted_paths)}")
            for path in deleted_paths:
                print(f"deleted_artifact: {path}")
        return
    if args.prune_decision_artifacts is not None:
        artifact_dir = Path(args.prune_decision_artifacts)
        summary = build_eval_decision_artifact_prune_summary(
            artifact_dir,
            keep_per_kind=args.prune_decision_keep_per_kind,
            keep_per_pack=args.prune_keep_per_pack,
            artifact_kinds=args.decision_artifact_kind,
        )
        print(summarize_eval_decision_artifact_prune_summary(summary))
        if args.prune_decision_artifacts_apply:
            deleted_paths = apply_eval_decision_artifact_prune_summary(summary)
            print(f"deleted: {len(deleted_paths)}")
            for path in deleted_paths:
                print(f"deleted_artifact: {path}")
        return
    if args.list_decision_artifacts is not None:
        artifact_dir = Path(args.list_decision_artifacts)
        index = build_eval_decision_artifact_index(artifact_dir)
        if args.decision_artifact_kind:
            index = filter_eval_decision_artifact_index(index, args.decision_artifact_kind)
        print(summarize_eval_decision_artifact_index(index))
        return
    if args.repair_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        if len(args.repair_eval_baseline) == 1:
            name = args.repair_eval_baseline[0]
            reference = None
        elif len(args.repair_eval_baseline) == 2:
            name, reference = args.repair_eval_baseline
        else:
            parser.error("--repair-eval-baseline expects NAME or NAME REFERENCE")
        artifact_path, config_path, reference_used = repair_eval_baseline_reference(
            artifact_dir,
            name,
            reference=reference,
        )
        print(f"repaired_baseline: {name}")
        print(f"artifact_path: {artifact_path}")
        print(f"config_path: {config_path}")
        print(f"reference_used: {reference_used}")
        return
    if args.audit_eval_baselines is not None:
        artifact_dir = Path(args.audit_eval_baselines)
        config = load_eval_baseline_config(artifact_dir)
        summary = build_eval_baseline_audit_summary(config)
        print(summarize_eval_baseline_audit(summary))
        return
    if args.review_eval_comparison:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        comparison = load_eval_comparison_summary(
            resolve_decision_artifact_reference(
                args.review_eval_comparison,
                artifact_dir,
                artifact_kind="comparison",
            )
        )
        _print_eval_comparison_with_breakdowns(comparison)
        return
    if args.review_eval_promotion:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision = load_eval_promotion_decision(
            resolve_decision_artifact_reference(
                args.review_eval_promotion,
                artifact_dir,
                artifact_kind="promotion",
            )
        )
        print(summarize_eval_promotion_decision(decision))
        return
    if args.auto_promote_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        if len(args.auto_promote_eval_baseline) == 1:
            baseline_name = args.auto_promote_eval_baseline[0]
            candidate_reference = "latest-pass"
        elif len(args.auto_promote_eval_baseline) == 2:
            baseline_name, candidate_reference = args.auto_promote_eval_baseline
        else:
            parser.error("--auto-promote-eval-baseline expects NAME or NAME REFERENCE")
        decision = auto_promote_eval_baseline(
            artifact_dir,
            baseline_name,
            candidate_reference=candidate_reference,
        )
        write_eval_promotion_decision(decision, decision_artifact_dir)
        print(summarize_eval_promotion_decision(decision))
        return
    if args.compare_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        if len(args.compare_eval_baseline) == 1:
            baseline_name = args.compare_eval_baseline[0]
            candidate_reference = "latest-pass"
        elif len(args.compare_eval_baseline) == 2:
            baseline_name, candidate_reference = args.compare_eval_baseline
        else:
            parser.error("--compare-eval-baseline expects NAME or NAME REFERENCE")
        comparison = compare_eval_baseline_to_reference(
            artifact_dir,
            baseline_name,
            candidate_reference=candidate_reference,
        )
        write_eval_comparison_summary(comparison, decision_artifact_dir)
        _print_eval_comparison_with_breakdowns(comparison)
        return
    if args.promote_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        if len(args.promote_eval_baseline) == 1:
            name = args.promote_eval_baseline[0]
            reference = "latest-pass"
        elif len(args.promote_eval_baseline) == 2:
            name, reference = args.promote_eval_baseline
        else:
            parser.error("--promote-eval-baseline expects NAME or NAME REFERENCE")
        artifact_path, config_path = promote_eval_baseline(
            artifact_dir,
            name,
            reference=reference,
        )
        print(f"promoted_baseline: {name}")
        print(f"artifact_path: {artifact_path}")
        print(f"config_path: {config_path}")
        return
    if args.list_eval_baselines is not None:
        artifact_dir = Path(args.list_eval_baselines)
        config = load_eval_baseline_config(artifact_dir)
        print(summarize_eval_baseline_config(config))
        return
    if args.set_eval_baseline:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        name, reference = args.set_eval_baseline
        resolved_path = resolve_eval_artifact_reference(reference, artifact_dir)
        config_path = save_eval_baseline_reference(artifact_dir, name, resolved_path)
        print(f"saved_baseline: {name}")
        print(f"artifact_path: {resolved_path}")
        print(f"config_path: {config_path}")
        return
    if args.list_evals is not None:
        artifact_dir = Path(args.list_evals)
        index = build_eval_artifact_index(artifact_dir)
        if args.eval_pack_filter:
            index = filter_eval_artifact_index(index, args.eval_pack_filter)
        print(summarize_eval_artifact_index(index))
        return
    if args.history_evals:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        summaries = [
            load_eval_summary(resolve_eval_artifact_reference(path, artifact_dir))
            for path in args.history_evals
        ]
        if args.eval_pack_filter:
            summaries = filter_eval_summaries_by_pack(summaries, args.eval_pack_filter)
        history = build_eval_history(summaries)
        print(summarize_eval_history(history))
        return
    if args.compare_evals:
        artifact_dir = Path(args.session_dir) / "eval-artifacts"
        decision_artifact_dir = artifact_dir / "decision-artifacts"
        baseline = load_eval_summary(resolve_eval_artifact_reference(args.compare_evals[0], artifact_dir))
        candidate = load_eval_summary(resolve_eval_artifact_reference(args.compare_evals[1], artifact_dir))
        comparison = compare_eval_summaries(baseline, candidate)
        write_eval_comparison_summary(comparison, decision_artifact_dir)
        _print_eval_comparison_with_breakdowns(comparison)
        return
    if args.run_evals:
        summary = run_eval_scenario_pack(
            _default_eval_pack_path(),
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
            planner_strategy_override=args.eval_planner_strategy,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.run_smoke_evals:
        summary = run_eval_suite(
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.run_eval_pack:
        summary = run_eval_scenario_pack(
            Path(args.run_eval_pack),
            Path(args.session_dir),
            artifact_dir=Path(args.session_dir) / "eval-artifacts",
            run_label=args.eval_label,
            planner_strategy_override=args.eval_planner_strategy,
        )
        _print_eval_summary_with_breakdowns(summary)
        return
    if args.review_session:
        record = store.load(args.review_session)
        print(store.build_review_summary(record))
        return
    if args.review_handoff:
        handoff = store.load_handoff(args.review_handoff)
        print(store.build_handoff_review_summary(handoff))
        return
    if args.review_compact_context:
        compact_context = store.load_compact_context(args.review_compact_context)
        print(store.build_compact_context_review_summary(compact_context))
        return
    if args.list_compact_contexts:
        print(store.summarize_compact_context_index(store.list_compact_context_index()))
        return
    if args.prune_compact_contexts:
        summary = store.build_compact_context_prune_summary(
            keep_newest=args.prune_compact_keep_newest,
            include_size_triggered=args.prune_compact_include_size_triggered,
        )
        print(store.summarize_compact_context_prune_summary(summary))
        if args.prune_compact_contexts_apply:
            deleted_paths = store.apply_compact_context_prune_summary(summary)
            print(f"deleted: {len(deleted_paths)}")
            for path in deleted_paths:
                print(f"deleted_path: {path}")
        return
    if args.review_repair_record:
        repair = store.load_procedural_repair_record(args.review_repair_record)
        print(store.build_procedural_repair_review_summary(repair))
        return
    if args.set_repair_record_status:
        repair_id, status = args.set_repair_record_status
        try:
            repair = store.update_procedural_repair_status(
                repair_id,
                status,
                actor=args.repair_status_actor,
                reason=args.repair_status_reason,
            )
        except ValueError as exc:
            parser.error(str(exc))
        print(store.build_procedural_repair_review_summary(repair))
        return
    if args.list_repair_status_audits is not None:
        repair_id = args.list_repair_status_audits or None
        audits = store.list_procedural_repair_status_audits(repair_id=repair_id)
        if not audits:
            print("repair_status_audits: none")
        else:
            print(f"repair_status_audits: {len(audits)}")
            for audit in audits:
                print(
                    f"{audit.audit_id}: repair_id={audit.repair_id} "
                    f"{audit.previous_status}->{audit.new_status} actor={audit.actor}"
                )
        return
    if args.review_repair_status_audit:
        audit = store.load_procedural_repair_status_audit(args.review_repair_status_audit)
        print(store.build_procedural_repair_status_audit_review_summary(audit))
        return
    if args.list_repair_records:
        records = store.list_procedural_repair_records()
        if not records:
            print("repair_records: none")
        else:
            print(f"repair_records: {len(records)}")
            for repair in records:
                print(
                    f"{repair.repair_id}: task_class={repair.task_class} "
                    f"status={repair.status} failure_pattern={repair.failure_pattern}"
                )
        return
    if not args.request:
        parser.error(
            "request is required unless --review-session, --review-handoff, --review-compact-context, --review-repair-record, "
            "--list-compact-contexts, --prune-compact-contexts, --set-repair-record-status, "
            "--list-repair-records, --list-repair-status-audits, "
            "--review-repair-status-audit, --run-evals, "
            "--compare-evals, --history-evals, --list-evals, "
            "--prune-evals, --prune-decision-artifacts, --set-eval-baseline, --list-eval-baselines, "
            "--promote-eval-baseline, --repair-eval-baseline, --audit-eval-baselines, --compare-eval-baseline, or "
            "--auto-promote-eval-baseline is used"
        )
    try:
        record = run_session(
            args.request,
            Path(args.cwd),
            store,
            auto_approve_commands=args.auto_approve_commands,
            resume_from_session_id=args.resume_session,
            resume_from_handoff_id=args.resume_handoff,
            planner_strategy=args.planner_strategy,
        )
    except ValueError as exc:
        parser.error(str(exc))
    print(f"session_id: {record.session_id}")
    print(f"status: {record.status.value}")
    print(f"workspace_root: {record.workspace_root}")
    if record.resumed_from_session_id:
        print(f"resumed_from: {record.resumed_from_session_id}")
    print(f"final_report: {record.final_report}")


if __name__ == "__main__":
    main()
