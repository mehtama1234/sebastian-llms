from __future__ import annotations

import json
from pathlib import Path

import arch_adv_2026.final_memo_cli as final_memo_cli
from arch_adv_2026.final_memo_cli import build_parser


def test_final_memo_cli_accepts_optional_benchmark_matrix() -> None:
    parser = build_parser()
    args = parser.parse_args(
        [
            "--micro-report",
            "micro.json",
            "--benchmark-matrix",
            "benchmark.json",
            "--long-context-selector",
            "selector.json",
            "--long-context-execution",
            "execution.json",
            "--training-benchmark",
            "training.json",
            "--review-plan",
            "review.json",
            "--validate-audit",
            "audit.json",
            "--validate-review-plan",
            "validate-review.json",
        ]
    )

    assert args.micro_report == "micro.json"
    assert args.benchmark_matrix == "benchmark.json"
    assert args.long_context_selector == "selector.json"
    assert args.long_context_execution == "execution.json"
    assert args.training_benchmark == "training.json"
    assert args.review_plan == "review.json"
    assert args.validate_audit == "audit.json"
    assert args.validate_review_plan == "validate-review.json"


def test_final_memo_cli_forwards_benchmark_matrix_to_generator(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    micro_path = tmp_path / "micro.json"
    benchmark_path = tmp_path / "benchmark.json"
    selector_path = tmp_path / "selector.json"
    execution_path = tmp_path / "execution.json"
    training_path = tmp_path / "training.json"
    review_path = tmp_path / "review.json"
    artifact_json = tmp_path / "memo.json"
    artifact_md = tmp_path / "memo.md"

    micro_path.write_text(json.dumps({"micro": True}), encoding="utf-8")
    benchmark_path.write_text(json.dumps({"benchmark": True}), encoding="utf-8")
    selector_path.write_text(json.dumps({"selector": True}), encoding="utf-8")
    execution_path.write_text(json.dumps({"execution": True}), encoding="utf-8")
    training_path.write_text(json.dumps({"training": True}), encoding="utf-8")
    review_path.write_text(json.dumps({"review": True}), encoding="utf-8")

    captured: dict[str, object] = {}

    def fake_generate(
        micro_report,
        long_context_selector,
        long_context_execution,
        training_benchmark,
        review_plan=None,
        benchmark_matrix=None,
    ):
        captured["micro_report"] = micro_report
        captured["long_context_selector"] = long_context_selector
        captured["long_context_execution"] = long_context_execution
        captured["training_benchmark"] = training_benchmark
        captured["review_plan"] = review_plan
        captured["benchmark_matrix"] = benchmark_matrix
        return {"headline": "memo", "summary_lines": [], "recommendations": []}

    monkeypatch.setattr(final_memo_cli, "generate_final_decision_memo", fake_generate)
    monkeypatch.setattr(final_memo_cli, "render_final_decision_memo_markdown", lambda memo: "memo-markdown")
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_memo_cli",
            "--micro-report",
            str(micro_path),
            "--benchmark-matrix",
            str(benchmark_path),
            "--long-context-selector",
            str(selector_path),
            "--long-context-execution",
            str(execution_path),
            "--training-benchmark",
            str(training_path),
            "--review-plan",
            str(review_path),
            "--artifact-json",
            str(artifact_json),
            "--artifact-md",
            str(artifact_md),
            "--stdout",
        ],
    )

    assert final_memo_cli.main() == 0
    stdout = capsys.readouterr().out

    assert captured["micro_report"] == {"micro": True}
    assert captured["benchmark_matrix"] == {"benchmark": True}
    assert captured["long_context_selector"] == {"selector": True}
    assert captured["long_context_execution"] == {"execution": True}
    assert captured["training_benchmark"] == {"training": True}
    assert captured["review_plan"] == {"review": True}
    assert artifact_json.read_text(encoding="utf-8") == '{\n  "headline": "memo",\n  "summary_lines": [],\n  "recommendations": []\n}\n'
    assert artifact_md.read_text(encoding="utf-8") == "memo-markdown"
    assert stdout.strip() == "memo-markdown"


def test_final_memo_cli_validates_against_audit_and_review_plan(
    monkeypatch,
    tmp_path: Path,
) -> None:
    micro_path = tmp_path / "micro.json"
    benchmark_path = tmp_path / "benchmark.json"
    selector_path = tmp_path / "selector.json"
    execution_path = tmp_path / "execution.json"
    training_path = tmp_path / "training.json"
    review_path = tmp_path / "review.json"
    audit_path = tmp_path / "audit.json"

    for path, payload in [
        (micro_path, {"micro": True}),
        (benchmark_path, {"benchmark": True}),
        (selector_path, {"selector": True}),
        (execution_path, {"execution": True}),
        (training_path, {"training": True}),
        (
            review_path,
            {
                "summary": {
                    "priority_variants": [],
                    "raw_mismatch_variants": [],
                    "resolved_mismatch_variants": [],
                    "unresolved_mismatch_variants": [],
                    "review_count": 1,
                },
                "rows": [{"variant": "compressed_attention", "priority": 0}],
            },
        ),
        (
            audit_path,
            {
                "summary": {
                    "variant_count": 1,
                    "mismatch_variants": [],
                    "mismatch_count": 0,
                    "resolved_mismatch_variants": [],
                    "resolved_mismatch_count": 0,
                    "unresolved_mismatch_variants": [],
                    "unresolved_mismatch_count": 0,
                },
                "rows": [{"variant": "compressed_attention"}],
            },
        ),
    ]:
        path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        final_memo_cli,
        "generate_final_decision_memo",
        lambda *args, **kwargs: {
            "headline": "memo",
            "default_carry_forward_variant": "compressed_attention",
            "secondary_variants": [],
            "exploratory_variants": [],
            "drop_for_now_variants": [],
            "summary_lines": [],
            "recommendations": [],
            "evidence_matrix": [{"variant": "compressed_attention"}],
            "evidence": {
                "review_summary": {
                    "priority_variants": [],
                    "raw_mismatch_variants": [],
                    "resolved_mismatch_variants": [],
                    "unresolved_mismatch_variants": [],
                }
            },
        },
    )
    monkeypatch.setattr(final_memo_cli, "render_final_decision_memo_markdown", lambda memo: "memo-markdown")
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_memo_cli",
            "--micro-report",
            str(micro_path),
            "--benchmark-matrix",
            str(benchmark_path),
            "--long-context-selector",
            str(selector_path),
            "--long-context-execution",
            str(execution_path),
            "--training-benchmark",
            str(training_path),
            "--review-plan",
            str(review_path),
            "--validate-audit",
            str(audit_path),
        ],
    )

    assert final_memo_cli.main() == 0


def test_final_memo_cli_validation_failure_writes_stderr(
    monkeypatch,
    tmp_path: Path,
    capsys,
) -> None:
    micro_path = tmp_path / "micro.json"
    selector_path = tmp_path / "selector.json"
    execution_path = tmp_path / "execution.json"
    training_path = tmp_path / "training.json"
    review_path = tmp_path / "review.json"
    audit_path = tmp_path / "audit.json"

    for path, payload in [
        (micro_path, {"micro": True}),
        (selector_path, {"selector": True}),
        (execution_path, {"execution": True}),
        (training_path, {"training": True}),
        (
            review_path,
            {
                "summary": {
                    "priority_variants": [],
                    "raw_mismatch_variants": [],
                    "resolved_mismatch_variants": [],
                    "unresolved_mismatch_variants": [],
                    "review_count": 1,
                },
                "rows": [{"variant": "compressed_attention", "priority": 0}],
            },
        ),
        (
            audit_path,
            {
                "summary": {
                    "variant_count": 1,
                    "mismatch_variants": [],
                    "mismatch_count": 0,
                    "resolved_mismatch_variants": [],
                    "resolved_mismatch_count": 0,
                    "unresolved_mismatch_variants": [],
                    "unresolved_mismatch_count": 0,
                },
                "rows": [{"variant": "compressed_attention"}],
            },
        ),
    ]:
        path.write_text(json.dumps(payload), encoding="utf-8")

    monkeypatch.setattr(
        final_memo_cli,
        "generate_final_decision_memo",
        lambda *args, **kwargs: {
            "headline": "memo",
            "default_carry_forward_variant": "compressed_attention",
            "secondary_variants": [],
            "exploratory_variants": [],
            "drop_for_now_variants": [],
            "summary_lines": [],
            "recommendations": [],
            "evidence_matrix": [],
            "evidence": {
                "review_summary": {
                    "priority_variants": [],
                    "raw_mismatch_variants": [],
                    "resolved_mismatch_variants": [],
                    "unresolved_mismatch_variants": [],
                }
            },
        },
    )
    monkeypatch.setattr(final_memo_cli, "render_final_decision_memo_markdown", lambda memo: "memo-markdown")
    monkeypatch.setattr(
        "sys.argv",
        [
            "final_memo_cli",
            "--micro-report",
            str(micro_path),
            "--long-context-selector",
            str(selector_path),
            "--long-context-execution",
            str(execution_path),
            "--training-benchmark",
            str(training_path),
            "--review-plan",
            str(review_path),
            "--validate-audit",
            str(audit_path),
        ],
    )

    assert final_memo_cli.main() == 1
    captured = capsys.readouterr()
    assert "final memo variants do not match the audit row variants" in captured.err
