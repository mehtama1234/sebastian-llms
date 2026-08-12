from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol
from urllib import request as urllib_request


@dataclass(slots=True)
class EvidenceSnippet:
    path: str
    start_line: int
    end_line: int
    text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "start_line": self.start_line,
            "end_line": self.end_line,
            "text": self.text,
        }


@dataclass(slots=True)
class ProviderRequest:
    task_id: str
    repo_root: str
    prompt: str
    expected_artifact_type: str
    allowed_tools: list[str]
    instruction_mode: str
    instruction_tokens: int
    context_snippets: list[EvidenceSnippet] = field(default_factory=list)
    gold_files: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "repo_root": self.repo_root,
            "prompt": self.prompt,
            "expected_artifact_type": self.expected_artifact_type,
            "allowed_tools": self.allowed_tools,
            "instruction_mode": self.instruction_mode,
            "instruction_tokens": self.instruction_tokens,
            "context_snippets": [snippet.to_dict() for snippet in self.context_snippets],
            "gold_files": self.gold_files,
        }


@dataclass(slots=True)
class ProviderResponse:
    provider_name: str
    output_text: str
    cited_paths: list[str]
    grounded: bool
    token_estimate: int
    response_id: str = ""
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider_name": self.provider_name,
            "output_text": self.output_text,
            "cited_paths": self.cited_paths,
            "grounded": self.grounded,
            "token_estimate": self.token_estimate,
            "response_id": self.response_id,
            "notes": self.notes,
        }


class AttemptProvider(Protocol):
    def run(self, request: ProviderRequest) -> ProviderResponse:
        ...


class LocalEvidenceProvider:
    """Deterministic local provider over benchmark evidence.

    This is not a model. It is a real runtime seam that consumes the same request
    shape a future live provider will use, but answers only from the prepared
    evidence snippets. That makes the runtime and artifact contract real before
    the repo commits to a specific model backend.
    """

    name = "local_evidence_provider"

    def run(self, request: ProviderRequest) -> ProviderResponse:
        cited_paths = [snippet.path for snippet in request.context_snippets]
        summary_parts: list[str] = []
        for snippet in request.context_snippets[:2]:
            preview = " ".join(snippet.text.strip().split())
            summary_parts.append(f"{Path(snippet.path).name}:{snippet.start_line}-{snippet.end_line} {preview}")
        if summary_parts:
            output = (
                f"Task {request.task_id}: grounded draft for {request.expected_artifact_type}. "
                f"Evidence: {' | '.join(summary_parts)}"
            )
            grounded = True
            notes = ["used_context_snippets", "deterministic_local_provider"]
        else:
            output = f"Task {request.task_id}: no usable evidence snippets were available."
            grounded = False
            notes = ["missing_context_snippets", "deterministic_local_provider"]
        token_estimate = max(1, len(output.split()))
        return ProviderResponse(
            provider_name=self.name,
            output_text=output,
            cited_paths=cited_paths,
            grounded=grounded,
            token_estimate=token_estimate,
            response_id="",
            notes=notes,
        )


def _default_instructions(request: ProviderRequest) -> str:
    allowed_tools = ", ".join(request.allowed_tools) if request.allowed_tools else "read-only reasoning"
    return (
        "You are a grounded coding-agent experiment runner. "
        "Use only the provided context snippets and explicitly cite relevant file paths. "
        f"Allowed tools for this task: {allowed_tools}. "
        f"Produce a concise artifact suitable for {request.expected_artifact_type}."
    )


def _default_input(request: ProviderRequest) -> str:
    parts = [f"Task: {request.prompt}"]
    if request.gold_files:
        parts.append("Relevant files:\n- " + "\n- ".join(request.gold_files))
    if request.context_snippets:
        formatted = []
        for snippet in request.context_snippets:
            formatted.append(
                f"[{snippet.path}:{snippet.start_line}-{snippet.end_line}]\n{snippet.text}"
            )
        parts.append("Context snippets:\n" + "\n\n".join(formatted))
    return "\n\n".join(parts)


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text:
        return output_text
    texts: list[str] = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                texts.append(content["text"])
    return "\n".join(texts).strip()


class OpenAIResponsesProvider:
    """Live provider backed by the OpenAI Responses API.

    Official OpenAI docs recommend the Responses API as the primary text
    generation interface and show `instructions` plus `input` for direct model
    requests. This provider uses that shape while preserving the local artifact
    contract used elsewhere in the harness.
    """

    name = "openai_responses_provider"

    def __init__(
        self,
        *,
        model: str = "gpt-5.6",
        api_key: str | None = None,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: str = "https://api.openai.com/v1/responses",
        timeout_seconds: float = 60.0,
    ) -> None:
        self.model = model
        self.api_key_env = api_key_env
        self.api_key = api_key or os.environ.get(api_key_env, "")
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        if not self.api_key:
            raise ValueError(f"missing API key; set {api_key_env}")

    def _request_json(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            self.base_url,
            data=data,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urllib_request.urlopen(req, timeout=self.timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))

    def run(self, request: ProviderRequest) -> ProviderResponse:
        payload = {
            "model": self.model,
            "instructions": _default_instructions(request),
            "input": _default_input(request),
        }
        raw = self._request_json(payload)
        output_text = _extract_output_text(raw)
        snippet_paths = [snippet.path for snippet in request.context_snippets]
        cited_paths = [path for path in snippet_paths if path in output_text]
        grounded = bool(snippet_paths) and len(cited_paths) == len(snippet_paths)
        token_estimate = max(1, len(output_text.split())) if output_text else 1
        notes = ["live_openai_provider", f"model:{self.model}", f"api_key_env:{self.api_key_env}"]
        return ProviderResponse(
            provider_name=self.name,
            output_text=output_text,
            cited_paths=cited_paths,
            grounded=grounded,
            token_estimate=token_estimate,
            response_id=str(raw.get("id", "")),
            notes=notes,
        )


def build_provider(
    backend: str,
    *,
    model: str = "gpt-5.6",
    api_key_env: str = "OPENAI_API_KEY",
) -> AttemptProvider:
    if backend == "local":
        return LocalEvidenceProvider()
    if backend == "openai":
        return OpenAIResponsesProvider(model=model, api_key_env=api_key_env)
    raise ValueError(f"unknown provider backend: {backend}")
