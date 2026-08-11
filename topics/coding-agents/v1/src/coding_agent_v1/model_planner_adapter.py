from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from typing import Any

from .models import TaskFlow


MODEL_COMMAND_ENV = "CODING_AGENT_V1_MODEL_COMMAND"


class ModelPlannerAdapterError(ValueError):
    """Raised when the external model command cannot produce a valid planner decision."""


def build_model_planner_prompt(payload: dict[str, Any]) -> str:
    contract = payload.get("contract", {})
    allowed_flows = contract.get("allowed_task_flows") or [item.value for item in TaskFlow]
    baseline = payload.get("deterministic_baseline", {})
    request = payload.get("request", "")
    return "\n".join(
        [
            "You are choosing a bounded coding-agent planner decision.",
            "Return only JSON. Do not include prose outside the JSON object.",
            "",
            "Required JSON shape:",
            '{"task_flow": "<flow>", "reasons": ["short decision reason"]}',
            "",
            "Allowed task_flow values:",
            ", ".join(str(item) for item in allowed_flows),
            "",
            "Optional fields:",
            '- "feature_strategy": string',
            '- "feature_arguments": object with string-compatible values',
            "",
            "Rules:",
            "- Choose the safest task_flow for the request.",
            "- Preserve the deterministic baseline unless there is strong request evidence to change it.",
            "- Do not choose tools, commands, files, or validation directly; the harness recomputes those.",
            "- Do not include chain-of-thought. Reasons must be concise decision evidence.",
            "",
            "Request:",
            str(request),
            "",
            "Deterministic baseline TaskPlan:",
            json.dumps(baseline, indent=2, sort_keys=True),
            "",
            "Full planner payload:",
            json.dumps(payload, indent=2, sort_keys=True),
        ]
    )


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = _strip_json_fence(stripped)
    decoder = json.JSONDecoder()
    parsed_objects: list[dict[str, Any]] = []
    for index, character in enumerate(stripped):
        if character != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(stripped[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            parsed_objects.append(parsed)
    if not parsed_objects:
        raise ModelPlannerAdapterError("model output JSON must be an object")
    planner_decisions = [
        item for item in parsed_objects if "task_flow" in item and "reasons" in item
    ]
    if planner_decisions:
        return planner_decisions[-1]
    return parsed_objects[-1]


def normalize_model_decision(decision: dict[str, Any]) -> dict[str, Any]:
    raw_task_flow = decision.get("task_flow")
    if not isinstance(raw_task_flow, str):
        raise ModelPlannerAdapterError("model decision must include string field `task_flow`")
    try:
        task_flow = TaskFlow(raw_task_flow)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in TaskFlow)
        raise ModelPlannerAdapterError(
            f"model decision task_flow `{raw_task_flow}` is unsupported; expected one of: {allowed}"
        ) from exc

    raw_reasons = decision.get("reasons")
    if isinstance(raw_reasons, str):
        raw_reasons = [raw_reasons]
    if not isinstance(raw_reasons, list):
        raise ModelPlannerAdapterError("model decision must include `reasons` as a string or list")
    reasons = [str(item).strip() for item in raw_reasons if str(item).strip()]
    if not reasons:
        raise ModelPlannerAdapterError("model decision must include at least one non-empty reason")

    normalized: dict[str, Any] = {
        "task_flow": task_flow.value,
        "reasons": reasons,
    }
    feature_strategy = decision.get("feature_strategy")
    if feature_strategy is not None:
        normalized["feature_strategy"] = str(feature_strategy)
    feature_arguments = decision.get("feature_arguments")
    if feature_arguments is not None:
        if not isinstance(feature_arguments, dict):
            raise ModelPlannerAdapterError("model decision `feature_arguments` must be an object")
        normalized["feature_arguments"] = {
            str(key): str(value) for key, value in feature_arguments.items()
        }
    return normalized


def run_model_planner_adapter(payload: dict[str, Any], model_command: str) -> dict[str, Any]:
    if not model_command.strip():
        raise ModelPlannerAdapterError(f"{MODEL_COMMAND_ENV} is required")
    prompt = build_model_planner_prompt(payload)
    try:
        completed = subprocess.run(
            shlex.split(model_command),
            input=prompt,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ModelPlannerAdapterError(f"model command failed: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or f"exit code {completed.returncode}"
        raise ModelPlannerAdapterError(f"model command failed: {detail}")
    return normalize_model_decision(extract_json_object(completed.stdout))


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Adapter from a generic model CLI to the coding-agent-v1 planner JSON contract."
    )
    parser.add_argument(
        "--model-command",
        default=os.environ.get(MODEL_COMMAND_ENV, ""),
        help=f"External model command. Defaults to ${MODEL_COMMAND_ENV}.",
    )
    args = parser.parse_args(argv)
    try:
        payload = json.loads(sys.stdin.read())
        if not isinstance(payload, dict):
            raise ModelPlannerAdapterError("planner payload must be a JSON object")
        decision = run_model_planner_adapter(payload, args.model_command)
    except (json.JSONDecodeError, ModelPlannerAdapterError) as exc:
        print(f"model planner adapter error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    print(json.dumps(decision, sort_keys=True))


def _strip_json_fence(text: str) -> str:
    lines = text.splitlines()
    if not lines:
        return text
    if lines[0].strip().startswith("```"):
        lines = lines[1:]
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]
    return "\n".join(lines).strip()


if __name__ == "__main__":
    main()
