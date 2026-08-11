from __future__ import annotations

import json

from llm_dev_2026 import cli, memo_cli, scorecard_cli
from llm_dev_2026.experiment import BASELINE, PRODUCTION, default_matrix, run_experiment
from llm_dev_2026.memo import generate_memo, render_markdown
from llm_dev_2026.scorecard import build_scorecard, compare_scorecards
from llm_dev_2026.harness import run_config


def test_default_matrix_names_unique():
    names = [c.name for c in default_matrix().configs]
    assert len(names) == len(set(names))


def test_experiment_covers_all_configs_and_comparisons():
    report = run_experiment()
    for c in default_matrix().configs:
        assert c.name in report.scorecards
    assert report.comparisons
    for c in report.comparisons:
        assert 0.0 <= report.scorecards[c.candidate].task_success_rate <= 1.0


def test_scorecard_rates_are_bounded(bench):
    sc = build_scorecard("x", run_config(bench, default_matrix().configs[0]))
    for rate in (sc.task_success_rate, sc.reported_success_rate, sc.hallucination_rate, sc.escalation_rate):
        assert 0.0 <= rate <= 1.0
    assert sc.scenario_count == len(bench.scenarios)


def test_production_candidate_beats_baseline():
    report = run_experiment()
    prod = report.scorecards[PRODUCTION]
    base = report.scorecards[BASELINE]
    assert prod.task_success_rate >= base.task_success_rate
    assert prod.hallucination_rate <= base.hallucination_rate


def test_compare_flags_pure_cost_increase_as_regression():
    report = run_experiment()
    base = report.scorecards[BASELINE]
    hybrid = report.scorecards["retrieval_hybrid"]
    delta = compare_scorecards(base, hybrid)
    # Hybrid matched baseline success here but paid more retrieval ops.
    if abs(delta.task_success_delta) < 1e-9 and delta.latency_delta > 0:
        assert delta.verdict == "regressed"


def test_memo_has_decision_for_every_axis():
    memo = generate_memo(run_experiment())
    axes = {d["axis"] for d in memo["decisions"]}
    assert {"retrieval", "context", "instructions", "verifier", "test_time_scaling"} <= axes
    assert memo["verifier_recommended"] is True
    md = render_markdown(memo)
    assert "Adoption Memo" in md and "verifier" in md


def test_cli_entry_points_write_artifacts(tmp_path):
    report_path = tmp_path / "report.json"
    assert cli.main(["--out", str(report_path), "--quiet"]) == 0
    payload = json.loads(report_path.read_text())
    assert "scorecards" in payload and "comparisons" in payload

    sc_path = tmp_path / "sc.json"
    assert scorecard_cli.main(["--out", str(sc_path)]) == 0
    assert json.loads(sc_path.read_text())[BASELINE]["config_name"] == BASELINE

    memo_path = tmp_path / "memo.md"
    assert memo_cli.main(["--out", str(memo_path)]) == 0
    assert "Adoption Memo" in memo_path.read_text()
