from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.benchmark_loader import load_benchmark_manifest
from llm_dev_2026.config import InstructionMode
from llm_dev_2026.provider import LocalEvidenceProvider, ProviderResponse
from llm_dev_2026.real_task_verify_cli import main as real_task_verify_main
from llm_dev_2026.real_task_verifier import run_real_task_with_verifier


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


class UngroundedProvider:
    def run(self, request):
        return ProviderResponse(
            provider_name="ungrounded_test_provider",
            output_text="Unsupported answer with no file citations.",
            cited_paths=[],
            grounded=False,
            token_estimate=6,
            notes=["forced_ungrounded"],
        )


def test_real_task_with_verifier_accepts_grounded_local_task():
    manifest = load_benchmark_manifest(_sample_path())
    artifact = run_real_task_with_verifier(
        manifest,
        "topics.inspect.deepseek_architecture_lane",
        LocalEvidenceProvider(),
        instruction_mode=InstructionMode.ROOT,
        run_validation_checks=False,
    )
    assert artifact.accepted is True
    assert artifact.escalated is False
    assert artifact.verifier["accepted"] is True
    assert artifact.meta_verifier["accepted"] is True
    assert artifact.final_stage == "ok"


def test_real_task_with_verifier_runs_validation_commands():
    manifest = load_benchmark_manifest(_sample_path())
    artifact = run_real_task_with_verifier(
        manifest,
        "topics.bug_fix.sample_benchmark_loader_tests",
        LocalEvidenceProvider(),
        instruction_mode=InstructionMode.ROOT,
        run_validation_checks=True,
    )
    assert artifact.accepted is True
    assert artifact.validation_results
    assert all(result["passed"] for result in artifact.validation_results)


def test_real_task_with_verifier_accepts_task_aware_retrieval_for_architecture_lane():
    manifest = load_benchmark_manifest(_sample_path())
    artifact = run_real_task_with_verifier(
        manifest,
        "topics.inspect.deepseek_architecture_lane",
        LocalEvidenceProvider(),
        evidence_source="retrieval",
        retrieval_mode="task_aware",
        run_validation_checks=False,
    )
    assert artifact.accepted is True
    assert artifact.runtime["response"]["grounded"] is True


def test_real_task_with_verifier_escalates_ungrounded_provider():
    manifest = load_benchmark_manifest(_sample_path())
    artifact = run_real_task_with_verifier(
        manifest,
        "topics.diagnose.llm_dev_verifier_flow",
        UngroundedProvider(),
        instruction_mode=InstructionMode.NONE,
        run_validation_checks=False,
    )
    assert artifact.accepted is False
    assert artifact.escalated is True
    assert artifact.final_stage == "runtime_ungrounded"
    assert artifact.verifier["reason"].startswith("ungrounded")


def test_real_task_verify_cli_writes_json(tmp_path):
    out = tmp_path / "verified.json"
    assert real_task_verify_main(
        [
            str(_sample_path()),
            "topics.inspect.deepseek_architecture_lane",
            "--skip-validation",
            "--out",
            str(out),
        ]
    ) == 0
    payload = json.loads(out.read_text())
    assert payload["task_id"] == "topics.inspect.deepseek_architecture_lane"
    assert payload["accepted"] is True
