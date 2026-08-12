from __future__ import annotations

import json
from pathlib import Path

from llm_dev_2026.benchmark_loader import load_benchmark_manifest
from llm_dev_2026.config import InstructionMode
from llm_dev_2026.provider import LocalEvidenceProvider, OpenAIResponsesProvider, ProviderRequest, build_provider
from llm_dev_2026.real_task_cli import main as real_task_main
from llm_dev_2026.runtime import build_provider_request, run_real_task


def _sample_path() -> Path:
    return Path(__file__).resolve().parents[2] / "evals" / "datasets" / "real-repos" / "sample-benchmark.json"


def test_build_provider_request_reads_evidence_snippets():
    manifest = load_benchmark_manifest(_sample_path())
    task = next(task for task in manifest.tasks if task.task_id == "topics.diagnose.llm_dev_verifier_flow")
    request, instruction, missing = build_provider_request(
        manifest,
        task,
        instruction_mode=InstructionMode.HIERARCHICAL,
    )
    assert missing == []
    assert instruction.mode == "hierarchical"
    assert request.context_snippets
    assert "ScenarioRun" in request.context_snippets[0].text


def test_build_provider_request_supports_evidence_selection_modes():
    manifest = load_benchmark_manifest(_sample_path())
    task = next(task for task in manifest.tasks if task.task_id == "topics.diagnose.llm_dev_verifier_flow")

    all_request, _, _ = build_provider_request(manifest, task, evidence_selection="all")
    first_request, _, _ = build_provider_request(manifest, task, evidence_selection="first")
    sparse_request, _, _ = build_provider_request(manifest, task, evidence_selection="sparse", evidence_top_k=1)

    assert len(all_request.context_snippets) == 2
    assert len(first_request.context_snippets) == 1
    assert len(sparse_request.context_snippets) == 1
    assert sparse_request.context_snippets[0].path.endswith("meta_verifier.py")


def test_build_provider_request_supports_task_aware_retrieval():
    manifest = load_benchmark_manifest(_sample_path())
    task = next(task for task in manifest.tasks if task.task_id == "topics.inspect.deepseek_architecture_lane")
    request, _, missing = build_provider_request(
        manifest,
        task,
        evidence_source="retrieval",
        retrieval_mode="task_aware",
        retrieval_top_k=2,
    )
    assert missing == []
    assert len(request.context_snippets) == 2
    assert any(snippet.path.endswith("long_context_eval.py") for snippet in request.context_snippets)


def test_run_real_task_returns_grounded_attempt_artifact():
    manifest = load_benchmark_manifest(_sample_path())
    artifact = run_real_task(
        manifest,
        "topics.inspect.deepseek_architecture_lane",
        LocalEvidenceProvider(),
        instruction_mode=InstructionMode.ROOT,
    )
    assert artifact.ready is True
    assert artifact.response["grounded"] is True
    assert artifact.request["context_snippets"]
    assert artifact.response["provider_name"] == "local_evidence_provider"
    assert artifact.retrieval_diagnostics["has_any_gold_hit"] is True
    assert artifact.retrieval_diagnostics["gold_file_recall"] > 0.0


def test_real_task_cli_writes_artifact(tmp_path):
    out = tmp_path / "attempt.json"
    assert real_task_main(
        [
            str(_sample_path()),
            "topics.research.production_experiment_goal",
            "--instruction-mode",
            "root",
            "--out",
            str(out),
        ]
    ) == 0
    payload = json.loads(out.read_text())
    assert payload["task_id"] == "topics.research.production_experiment_goal"
    assert payload["response"]["grounded"] is True


def test_build_provider_returns_local_backend():
    provider = build_provider("local")
    assert isinstance(provider, LocalEvidenceProvider)


def test_openai_provider_parses_response_without_network(monkeypatch):
    provider = OpenAIResponsesProvider(api_key="test-key")

    def fake_request_json(payload):
        assert payload["model"] == "gpt-5.6"
        return {
            "id": "resp_123",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {
                            "type": "output_text",
                            "text": "Grounded answer citing llm-developments-2026/code/src/llm_dev_2026/harness.py",
                        }
                    ],
                }
            ],
        }

    monkeypatch.setattr(provider, "_request_json", fake_request_json)
    response = provider.run(
        ProviderRequest(
            task_id="t1",
            repo_root="/tmp/repo",
            prompt="Explain the harness",
            expected_artifact_type="memo",
            allowed_tools=["read"],
            instruction_mode="none",
            instruction_tokens=0,
            context_snippets=[],
            gold_files=["llm-developments-2026/code/src/llm_dev_2026/harness.py"],
        )
    )
    assert response.provider_name == "openai_responses_provider"
    assert response.response_id == "resp_123"
    assert "Grounded answer citing" in response.output_text


def test_real_task_cli_openai_backend_writes_artifact(tmp_path, monkeypatch):
    def fake_run(self, request):
        return type(
            "Resp",
            (),
            {
                "to_dict": lambda self: {
                    "provider_name": "openai_responses_provider",
                    "output_text": "Uses llm-developments-2026/projects/production-scale-real-experiment-checklist.md",
                    "cited_paths": ["llm-developments-2026/projects/production-scale-real-experiment-checklist.md"],
                    "grounded": True,
                    "token_estimate": 12,
                    "response_id": "resp_fake",
                    "notes": ["live_openai_provider"],
                }
            },
        )()

    monkeypatch.setattr("llm_dev_2026.provider.OpenAIResponsesProvider.run", fake_run)
    monkeypatch.setenv("TEST_OPENAI_KEY", "test-key")
    out = tmp_path / "attempt-openai.json"
    assert real_task_main(
        [
            str(_sample_path()),
            "topics.research.production_experiment_goal",
            "--provider",
            "openai",
            "--api-key-env",
            "TEST_OPENAI_KEY",
            "--out",
            str(out),
        ]
    ) == 0
    payload = json.loads(out.read_text())
    assert payload["response"]["provider_name"] == "openai_responses_provider"
