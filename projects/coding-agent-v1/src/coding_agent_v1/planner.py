from __future__ import annotations

from pathlib import Path
import re

from .models import TaskFlow, TaskFlowCandidate
from .tools import is_ignored_path


def append_task_flow_candidate(
    candidates: list[TaskFlowCandidate],
    *,
    task_flow: TaskFlow,
    score: int,
    priority: int,
    reason: str,
) -> None:
    candidates.append(
        TaskFlowCandidate(
            task_flow=task_flow,
            score=score,
            priority=priority,
            reason=reason,
        )
    )


def select_task_flow_from_candidates(
    candidates: list[TaskFlowCandidate],
) -> tuple[TaskFlow, list[str]]:
    if not candidates:
        return TaskFlow.INSPECT, [
            "planner selected `inspect` because no stronger task-flow evidence was found"
        ]

    candidates.sort(key=lambda item: (-item.score, item.priority))
    selected = candidates[0]
    score_summary = ", ".join(
        f"{candidate.task_flow.value}={candidate.score}" for candidate in candidates
    )
    reasons = [
        f"planner selected `{selected.task_flow.value}` from scored task-flow candidates ({score_summary})",
        selected.reason,
    ]
    return selected.task_flow, reasons


def looks_like_test_failure_context(lowered: str) -> bool:
    test_markers = ("test", "tests", "pytest", "suite", "error", "errors", "failure", "failures")
    failure_markers = ("fail", "fails", "failing", "failed", "broken", "red")
    return any(marker in lowered for marker in test_markers) and any(marker in lowered for marker in failure_markers)


def looks_like_diagnose_request(lowered: str) -> bool:
    diagnose_terms = ("diagnose", "why", "investigate", "debug", "explain", "look into")
    if any(term in lowered for term in diagnose_terms) and (
        "fail" in lowered or "test" in lowered or "error" in lowered
    ):
        return True
    return any(
        phrase in lowered
        for phrase in (
            "investigate the failing tests",
            "investigate why the tests",
            "look into the failing tests",
            "look into why the tests",
        )
    )


def looks_like_fix_request(lowered: str) -> bool:
    fix_terms = ("fix", "repair", "resolve")
    if any(term in lowered for term in fix_terms):
        return True
    if any(
        phrase in lowered
        for phrase in (
            "run the tests",
            "run tests",
            "run the suite",
            "run suite",
            "run unit tests",
            "run pytest",
            "rerun tests",
            "rerun the suite",
            "rerun suite",
            "rerun unit tests",
            "rerun pytest",
            "re-run tests",
            "re-run the suite",
            "re-run suite",
            "re-run unit tests",
            "re-run pytest",
            "run the test suite",
            "run test suite",
            "rerun the test suite",
            "rerun test suite",
            "re-run the test suite",
            "re-run test suite",
        )
    ):
        return True
    if not looks_like_test_failure_context(lowered):
        return False
    return any(
        phrase in lowered
        for phrase in (
            "make the failing tests pass",
            "make the tests pass",
            "get the tests passing",
            "get tests passing",
            "make tests green",
            "turn the tests green",
        )
    )


def looks_like_failure_report_request(lowered: str) -> bool:
    return any(
        phrase in lowered
        for phrase in (
            "is failing",
            "are failing",
            "is broken",
            "are broken",
            "is red",
            "are red",
        )
    ) and ("test" in lowered or "tests" in lowered)


def find_python_test_paths(workspace_root: Path) -> list[Path]:
    return [
        path
        for path in sorted(workspace_root.rglob("*.py"))
        if not is_ignored_path(path, workspace_root)
        and (path.name.startswith("test_") or path.name.endswith("_test.py"))
    ]


def _normalize_test_reference_candidate(raw: str) -> str:
    candidate = raw.strip()
    if candidate.startswith("<") and candidate.endswith(">"):
        candidate = candidate[1:-1]
    candidate = re.sub(r"#L\d+(?:-L\d+)?$", "", candidate)
    candidate = re.sub(r":\d+(?::\d+)?$", "", candidate)
    return candidate


def extract_existing_test_file_references(request: str, workspace_root: Path) -> list[Path]:
    matches: list[Path] = []
    seen: set[Path] = set()

    def add_match(raw: str) -> None:
        candidate = workspace_root / _normalize_test_reference_candidate(raw)
        if candidate.exists() and candidate not in seen:
            seen.add(candidate)
            matches.append(candidate)

    combined_pattern = re.compile(
        r"\[[^\]]+\]\((?P<markdown>(?:<[^>]*test[^>]*\.py(?:#L\d+(?:-L\d+)?)?(?::\d+(?::\d+)?)?>)|(?:[^)]*test[^)]*\.py(?:#L\d+(?:-L\d+)?)?(?::\d+(?::\d+)?)?))\)"
        r"|[`'\"](?P<quoted>[^`'\"]*test[^`'\"]*\.py(?:#L\d+(?:-L\d+)?)?(?::\d+(?::\d+)?)?)[`'\"]"
        r"|\b(?P<plain>[A-Za-z0-9_./-]*test[A-Za-z0-9_./-]*\.py(?:#L\d+(?:-L\d+)?)?(?::\d+(?::\d+)?)?)\b"
    )
    for match in combined_pattern.finditer(request):
        raw = match.group("markdown") or match.group("quoted") or match.group("plain")
        if raw:
            add_match(raw)
    return matches


def extract_existing_test_file_reference(request: str, workspace_root: Path) -> Path | None:
    matches = extract_existing_test_file_references(request, workspace_root)
    if matches:
        return matches[0]
    return None


def _format_referenced_test_evidence(referenced_tests: list[Path]) -> str:
    if len(referenced_tests) == 1:
        return f"existing test `{referenced_tests[0].name}`"
    names = ", ".join(f"`{path.name}`" for path in referenced_tests)
    return f"existing tests {names}"


def diagnose_reason(has_tests: bool, referenced_tests: list[Path]) -> str:
    if referenced_tests:
        return (
            "diagnose evidence: request asks for investigation and references "
            f"{_format_referenced_test_evidence(referenced_tests)}"
        )
    if has_tests:
        return "diagnose evidence: request asks for investigation and workspace contains runnable tests"
    return "diagnose evidence: request asks for investigation without edits"


def fix_reason(has_tests: bool, referenced_tests: list[Path]) -> str:
    if referenced_tests:
        return (
            "fix evidence: request asks for a fix and references "
            f"{_format_referenced_test_evidence(referenced_tests)}"
        )
    if has_tests:
        return "fix evidence: request asks to make failing tests pass and workspace contains runnable tests"
    return "fix evidence: request asks to make failing tests pass"


def failure_report_reason(referenced_tests: list[Path]) -> str:
    if referenced_tests:
        return (
            "diagnose evidence: passive failure report references "
            f"{_format_referenced_test_evidence(referenced_tests)}, "
            "so investigation is safer than direct edits"
        )
    return "diagnose evidence: passive failure report plus workspace tests suggests investigation first"


def count_symbol_occurrences(workspace_root: Path, symbol: str) -> int:
    count = 0
    pattern = re.compile(rf"\b{re.escape(symbol)}\b")
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        count += len(pattern.findall(text))
    return count


def rename_reason(symbol: str, match_count: int) -> str:
    if match_count > 0:
        return (
            f"rename evidence: exact rename request for `{symbol}` and workspace contains "
            f"{match_count} exact symbol match(es)"
        )
    return f"rename evidence: exact rename request for `{symbol}`"


def feature_workspace_score(
    feature_strategy: str,
    *,
    cli_parser_count: int,
    config_mapping_count: int,
    env_config_mapping_count: int,
) -> int:
    if feature_strategy == "cli_flag":
        return min(cli_parser_count, 2)
    if feature_strategy == "config_option":
        return min(config_mapping_count, 2)
    if feature_strategy == "env_var":
        return min(env_config_mapping_count, 2)
    return 0


def feature_reason(
    feature_strategy: str,
    strategy_reason: str,
    *,
    cli_parser_count: int,
    config_mapping_count: int,
    env_config_mapping_count: int,
) -> str:
    if feature_strategy == "cli_flag":
        return (
            f"feature evidence: {strategy_reason}; workspace contains {cli_parser_count} argparse parser file(s)"
        )
    if feature_strategy == "config_option":
        return (
            f"feature evidence: {strategy_reason}; workspace contains {config_mapping_count} config-style mapping file(s)"
        )
    if feature_strategy == "env_var":
        return (
            f"feature evidence: {strategy_reason}; workspace contains "
            f"{env_config_mapping_count} environment-backed config mapping file(s)"
        )
    return f"feature evidence: {strategy_reason}"


def find_cli_parser_files(workspace_root: Path) -> list[Path]:
    matches: list[Path] = []
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "ArgumentParser(" in text:
            matches.append(path)
    return matches


def find_config_mapping_files(workspace_root: Path, *, require_env_var: bool = False) -> list[Path]:
    matches: list[Path] = []
    assignment_pattern = re.compile(
        r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*\{(.*?)\}",
        flags=re.MULTILINE | re.DOTALL,
    )
    for path in sorted(workspace_root.rglob("*.py")):
        if is_ignored_path(path, workspace_root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if require_env_var and "import os" not in text and "os.getenv(" not in text:
            continue
        for match in assignment_pattern.finditer(text):
            variable_name = match.group(1)
            if re.search(r"(config|settings|options)", variable_name, flags=re.IGNORECASE):
                matches.append(path)
                break
    return matches


def extract_flag_token(request: str) -> str | None:
    match = re.search(r"(--[A-Za-z0-9-]+)", request)
    if match:
        return match.group(1)
    return None


def extract_cli_flag_request(request: str) -> str | None:
    lowered = request.lower()
    if "flag" not in lowered:
        return None
    return extract_flag_token(request)


def extract_generic_cli_flag_request(request: str) -> str | None:
    lowered = request.lower()
    if not any(term in lowered for term in ("parser", "cli", "command line", "command-line")):
        return None
    patterns = [
        r"\b(?:support|enable|add)\s+([A-Za-z][A-Za-z0-9_-]*)\s+mode\b",
        r"\b(?:support|enable|add)\s+([A-Za-z][A-Za-z0-9_-]*)\s+option\b",
        r"\bmake (?:the )?(?:parser|cli|command line|command-line)\s+(?:support|accept|handle)\s+([A-Za-z][A-Za-z0-9_-]*)\s+mode\b",
        r"\bmake (?:the )?(?:parser|cli|command line|command-line)\s+(?:support|accept|handle)\s+([A-Za-z][A-Za-z0-9_-]*)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if not match:
            continue
        flag_name = match.group(1).lower().replace("_", "-")
        return f"--{flag_name}"
    return None


def extract_config_option_request(request: str) -> tuple[str, str] | None:
    patterns = [
        r"\badd (?:a |an )?([A-Za-z_][A-Za-z0-9_]*) config option with default ([A-Za-z0-9_.'\"-]+)\b",
        r"\badd config option ([A-Za-z_][A-Za-z0-9_]*)=([A-Za-z0-9_.'\"-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if not match:
            continue
        option_name = match.group(1)
        literal = normalize_config_value_literal(match.group(2))
        if literal is None:
            continue
        return option_name, literal
    return None


def extract_generic_option_request(request: str) -> tuple[str, str] | None:
    patterns = [
        r"\badd (?:a |an )?([A-Za-z_][A-Za-z0-9_]*) option with default ([A-Za-z0-9_.'\"-]+)\b",
        r"\badd option ([A-Za-z_][A-Za-z0-9_]*)=([A-Za-z0-9_.'\"-]+)\b",
        r"\bmake (?:the )?(?:config|settings|options)\s+(?:support|include|accept)\s+([A-Za-z_][A-Za-z0-9_]*)\s+with default ([A-Za-z0-9_.'\"-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if not match:
            continue
        option_name = match.group(1)
        literal = normalize_config_value_literal(match.group(2))
        if literal is None:
            continue
        return option_name, literal
    return None


def extract_env_var_request(request: str) -> tuple[str, str, str] | None:
    patterns = [
        r"\badd ([A-Z_][A-Z0-9_]*) environment variable with default ([A-Za-z0-9_.'\"-]+)\b",
        r"\badd environment variable ([A-Z_][A-Z0-9_]*) with default ([A-Za-z0-9_.'\"-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if not match:
            continue
        env_name = match.group(1).upper()
        literal = normalize_config_value_literal(match.group(2))
        if literal is None:
            continue
        option_name = env_name.lower().split("_")[-1]
        return env_name, option_name, literal
    return None


def extract_generic_env_var_request(request: str) -> tuple[str, str, str] | None:
    patterns = [
        r"\badd ([A-Z_][A-Z0-9_]*) with default ([A-Za-z0-9_.'\"-]+)\b",
        r"\bset ([A-Z_][A-Z0-9_]*) default to ([A-Za-z0-9_.'\"-]+)\b",
        r"\bmake (?:the )?(?:config|settings|options)\s+(?:read|use|load)\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+([A-Z_][A-Z0-9_]*)\s+with default ([A-Za-z0-9_.'\"-]+)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, request, flags=re.IGNORECASE)
        if not match:
            continue
        if match.lastindex == 3:
            option_name = match.group(1)
            env_name = match.group(2).upper()
            literal_raw = match.group(3)
        else:
            env_name = match.group(1).upper()
            option_name = env_name.lower().split("_")[-1]
            literal_raw = match.group(2)
        literal = normalize_config_value_literal(literal_raw)
        if literal is None:
            continue
        return env_name, option_name, literal
    return None


def select_feature_strategy(request: str, workspace_root: Path) -> tuple[str, dict[str, str], str]:
    cli_flag_request = extract_cli_flag_request(request)
    if cli_flag_request is not None:
        return "cli_flag", {"flag_name": cli_flag_request}, (
            f"feature strategy selected: `cli_flag` for `{cli_flag_request}`"
        )
    env_var_request = extract_env_var_request(request)
    if env_var_request is not None:
        env_name, option_name, value_literal = env_var_request
        return "env_var", {
            "env_name": env_name,
            "option_name": option_name,
            "value_literal": value_literal,
        }, f"feature strategy selected: `env_var` for `{env_name}`"
    config_option_request = extract_config_option_request(request)
    if config_option_request is not None:
        option_name, value_literal = config_option_request
        return "config_option", {
            "option_name": option_name,
            "value_literal": value_literal,
        }, f"feature strategy selected: `config_option` for `{option_name}`"
    generic_option_request = extract_generic_option_request(request)
    if generic_option_request is not None and workspace_supports_config_mapping(workspace_root):
        option_name, value_literal = generic_option_request
        return "config_option", {
            "option_name": option_name,
            "value_literal": value_literal,
        }, (
            f"feature strategy inferred from workspace: `config_option` for `{option_name}` "
            "because the repo contains a config-style mapping."
        )
    generic_env_var_request = extract_generic_env_var_request(request)
    if generic_env_var_request is not None and workspace_supports_env_var_config_mapping(workspace_root):
        env_name, option_name, value_literal = generic_env_var_request
        return "env_var", {
            "env_name": env_name,
            "option_name": option_name,
            "value_literal": value_literal,
        }, (
            f"feature strategy inferred from workspace: `env_var` for `{env_name}` "
            "because the repo contains an environment-backed config mapping."
        )
    if workspace_supports_cli_parser(workspace_root):
        flag_token = extract_flag_token(request)
        if flag_token is not None:
            return "cli_flag", {"flag_name": flag_token}, (
                f"feature strategy inferred from workspace: `cli_flag` for `{flag_token}` "
                "because the repo contains an argparse parser."
            )
        generic_cli_flag_request = extract_generic_cli_flag_request(request)
        if generic_cli_flag_request is not None:
            return "cli_flag", {"flag_name": generic_cli_flag_request}, (
                f"feature strategy inferred from workspace: `cli_flag` for `{generic_cli_flag_request}` "
                "because the request describes parser behavior and the repo contains an argparse parser."
            )
    return "", {}, ""


def workspace_supports_cli_parser(workspace_root: Path) -> bool:
    return bool(find_cli_parser_files(workspace_root))


def workspace_supports_config_mapping(workspace_root: Path) -> bool:
    return bool(find_config_mapping_files(workspace_root))


def workspace_supports_env_var_config_mapping(workspace_root: Path) -> bool:
    return bool(find_config_mapping_files(workspace_root, require_env_var=True))


def normalize_config_value_literal(raw: str) -> str | None:
    value = raw.strip().rstrip(".,")
    if re.fullmatch(r"-?\d+", value):
        return value
    if re.fullmatch(r"-?\d+\.\d+", value):
        return value
    if value in {"True", "False", "None"}:
        return value
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", value):
        return f'"{value}"'
    return None
