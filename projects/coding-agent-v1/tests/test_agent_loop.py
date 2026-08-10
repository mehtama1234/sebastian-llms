from pathlib import Path
import json
import sys

from coding_agent_v1.agent_loop import build_task_plan, classify_task_flow, run_session
from coding_agent_v1.models import TaskFlow
from coding_agent_v1.session_store import SessionStore


def test_classify_task_flow_routes_common_request_types() -> None:
    assert classify_task_flow("fix the failing test") is TaskFlow.FIX
    assert classify_task_flow("make the failing tests pass") is TaskFlow.FIX
    assert classify_task_flow("run tests") is TaskFlow.FIX
    assert classify_task_flow("run pytest") is TaskFlow.FIX
    assert classify_task_flow("rerun tests") is TaskFlow.FIX
    assert classify_task_flow("rerun pytest") is TaskFlow.FIX
    assert classify_task_flow("run the suite") is TaskFlow.FIX
    assert classify_task_flow("run unit tests") is TaskFlow.FIX
    assert classify_task_flow("rerun unit tests") is TaskFlow.FIX
    assert classify_task_flow("run the test suite") is TaskFlow.FIX
    assert classify_task_flow("rerun the test suite") is TaskFlow.FIX
    assert classify_task_flow("add a --verbose flag") is TaskFlow.FEATURE
    assert classify_task_flow("add a timeout config option with default 30") is TaskFlow.FEATURE
    assert classify_task_flow("add APP_PROFILE environment variable with default advanced") is TaskFlow.FEATURE
    assert classify_task_flow("rename add to plus") is TaskFlow.RENAME
    assert classify_task_flow("diagnose why the tests fail") is TaskFlow.DIAGNOSE
    assert classify_task_flow("investigate the failing tests") is TaskFlow.DIAGNOSE
    assert classify_task_flow("summarize this repo") is TaskFlow.INSPECT


def test_build_task_plan_selects_targeted_validation_for_single_test_repo(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    (tmp_path / "test_cli.py").write_text("def test_cli():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add a --verbose flag", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.planner_strategy == "deterministic_heuristic"
    assert plan.planner_strategy_reason
    assert plan.feature_strategy == "cli_flag"
    assert plan.feature_arguments["flag_name"] == "--verbose"
    assert plan.validation_command == "pytest -q test_cli.py"
    assert "selected validation command `pytest -q test_cli.py`" in " ".join(plan.reasons)
    assert "planner selected `feature` from scored task-flow candidates" in " ".join(plan.reasons)


def test_build_task_plan_rejects_unsupported_planner_strategy(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")

    try:
        build_task_plan(
            "summarize this repo",
            tmp_path,
            ["README.md"],
            planner_strategy="model_preview",
        )
    except ValueError as exc:
        assert "unsupported planner strategy" in str(exc)
    else:
        raise AssertionError("expected unsupported planner strategy to fail")


def test_build_task_plan_rejects_unconfigured_model_guided_planner_strategy(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    monkeypatch.delenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", raising=False)

    try:
        build_task_plan(
            "summarize this repo",
            tmp_path,
            ["README.md"],
            planner_strategy="model_guided",
        )
    except ValueError as exc:
        assert "requires CODING_AGENT_V1_MODEL_PLANNER_COMMAND" in str(exc)
        assert "no tool action was taken" in str(exc)
    else:
        raise AssertionError("expected unconfigured model planner strategy to fail")


def test_build_task_plan_accepts_valid_model_guided_planner_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    planner_script = tmp_path / "planner.py"
    planner_script.write_text(
        "import json, sys\n"
        "payload = json.loads(sys.stdin.read())\n"
        "assert payload['deterministic_baseline']['task_flow'] == 'diagnose'\n"
        "print(json.dumps({'task_flow': 'diagnose', 'reasons': ['model saw failure language']}))\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", f"{sys.executable} {planner_script}")

    plan = build_task_plan(
        "why are the tests failing?",
        tmp_path,
        ["README.md"],
        planner_strategy="model_guided",
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.planner_strategy == "model_guided"
    assert "model-guided planner selected" in plan.planner_strategy_reason
    assert "model planner command selected `diagnose`" in " ".join(plan.reasons)
    assert "model saw failure language" in " ".join(plan.reasons)


def test_build_task_plan_rejects_invalid_model_guided_planner_output(
    monkeypatch,
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    planner_script = tmp_path / "planner.py"
    planner_script.write_text("print('not json')\n", encoding="utf-8")
    monkeypatch.setenv("CODING_AGENT_V1_MODEL_PLANNER_COMMAND", f"{sys.executable} {planner_script}")

    try:
        build_task_plan(
            "summarize this repo",
            tmp_path,
            ["README.md"],
            planner_strategy="model_guided",
        )
    except ValueError as exc:
        assert "did not return valid JSON" in str(exc)
        assert "no tool action was taken" in str(exc)
    else:
        raise AssertionError("expected invalid model planner output to fail")


def test_build_task_plan_selects_matching_feature_tests_in_multi_test_repo(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    (tmp_path / "test_cli.py").write_text(
        "def test_verbose_flag():\n    assert '--verbose' == '--verbose'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add a --verbose flag", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.validation_command == "pytest -q test_cli.py"
    assert (
        "selected validation command `pytest -q test_cli.py` "
        "from matching test content for `--verbose`"
    ) in " ".join(plan.reasons)


def test_build_task_plan_keeps_nested_relative_test_paths_for_targeted_feature_validation(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    nested_tests = tmp_path / "tests" / "unit"
    nested_tests.mkdir(parents=True, exist_ok=True)
    (nested_tests / "test_cli.py").write_text(
        "def test_verbose_flag():\n    assert '--verbose' == '--verbose'\n",
        encoding="utf-8",
    )
    sibling_tests = tmp_path / "tests" / "integration"
    sibling_tests.mkdir(parents=True, exist_ok=True)
    (sibling_tests / "test_cli.py").write_text(
        "def test_integration_cli():\n    assert True\n",
        encoding="utf-8",
    )

    plan = build_task_plan("add a --verbose flag", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.validation_command == "PYTHONPATH=. pytest -q tests/unit/test_cli.py"


def test_build_task_plan_prefers_explicit_test_reference_over_feature_heuristics(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    (tmp_path / "test_cli.py").write_text(
        "def test_verbose_flag():\n    assert '--verbose' == '--verbose'\n",
        encoding="utf-8",
    )
    referenced_tests = tmp_path / "tests" / "regression"
    referenced_tests.mkdir(parents=True, exist_ok=True)
    (referenced_tests / "test_targeted_cli.py").write_text(
        "def test_targeted_cli_regression():\n    assert True\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "add a --verbose flag so [target](tests/regression/test_targeted_cli.py) passes",
        tmp_path,
        ["README.md"],
    )

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.validation_command == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py"
    assert (
        "selected validation command "
        "`PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py` "
        "from explicit referenced test `test_targeted_cli.py`"
    ) in " ".join(plan.reasons)


def test_build_task_plan_uses_multiple_explicit_test_references_for_validation(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    first_tests = tmp_path / "tests" / "regression"
    first_tests.mkdir(parents=True, exist_ok=True)
    (first_tests / "test_targeted_cli.py").write_text(
        "def test_targeted_cli_regression():\n    assert True\n",
        encoding="utf-8",
    )
    second_tests = tmp_path / "tests" / "smoke"
    second_tests.mkdir(parents=True, exist_ok=True)
    (second_tests / "test_cli_smoke.py").write_text(
        "def test_cli_smoke():\n    assert True\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        (
            "add a --verbose flag so "
            "[first](tests/regression/test_targeted_cli.py) and "
            "[second](tests/smoke/test_cli_smoke.py) pass"
        ),
        tmp_path,
        ["README.md"],
    )

    assert plan.task_flow is TaskFlow.FEATURE
    assert (
        plan.validation_command
        == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py"
    )
    assert (
        "selected validation command "
        "`PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py` "
        "from explicit referenced tests `test_targeted_cli.py`, `test_cli_smoke.py`"
    ) in " ".join(plan.reasons)


def test_build_task_plan_keeps_all_explicit_test_references_even_beyond_three_paths(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    paths = [
        "tests/regression/test_targeted_cli.py",
        "tests/smoke/test_cli_smoke.py",
        "tests/unit/test_cli_unit.py",
        "tests/integration/test_cli_integration.py",
    ]
    for relative in paths:
        test_path = tmp_path / relative
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_marker():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan(
        (
            "add a --verbose flag so "
            "[one](tests/regression/test_targeted_cli.py), "
            "[two](tests/smoke/test_cli_smoke.py), "
            "[three](tests/unit/test_cli_unit.py), and "
            "[four](tests/integration/test_cli_integration.py) pass"
        ),
        tmp_path,
        ["README.md"],
    )

    assert plan.task_flow is TaskFlow.FEATURE
    assert (
        plan.validation_command
        == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py tests/unit/test_cli_unit.py tests/integration/test_cli_integration.py"
    )


def test_build_task_plan_preserves_request_order_for_mixed_test_reference_formats(
    tmp_path: Path,
) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text("import argparse\n", encoding="utf-8")
    first_path = tmp_path / "tests" / "quoted" / "test_first.py"
    first_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("def test_first():\n    assert True\n", encoding="utf-8")
    second_path = tmp_path / "tests" / "linked" / "test_second.py"
    second_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.write_text("def test_second():\n    assert True\n", encoding="utf-8")
    third_path = tmp_path / "tests" / "plain" / "test_third.py"
    third_path.parent.mkdir(parents=True, exist_ok=True)
    third_path.write_text("def test_third():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan(
        (
            "add a --verbose flag so "
            "'tests/quoted/test_first.py', "
            "[second](tests/linked/test_second.py), and "
            "tests/plain/test_third.py pass"
        ),
        tmp_path,
        ["README.md"],
    )

    assert plan.task_flow is TaskFlow.FEATURE
    assert (
        plan.validation_command
        == "PYTHONPATH=. pytest -q tests/quoted/test_first.py tests/linked/test_second.py tests/plain/test_third.py"
    )


def test_build_task_plan_falls_back_to_module_aware_cli_test_selection(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_has_verbose_action():\n"
            "    parser = build_parser()\n"
            "    assert any(action.dest == 'verbose' for action in parser._actions)\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add a --verbose flag", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.validation_command == "pytest -q test_cli.py"
    assert (
        "selected validation command `pytest -q test_cli.py` "
        "from module-aware CLI parser test evidence"
    ) in " ".join(plan.reasons)


def test_build_task_plan_includes_behavior_index_evidence_for_harness_workspace(
    tmp_path: Path,
) -> None:
    harness = tmp_path / "src" / "coding_agent_v1"
    harness.mkdir(parents=True)
    (harness / "agent_loop.py").write_text(
        "def build_task_plan(): pass\n"
        "def build_initial_actions(): pass\n"
        "def _choose_validation_command(): pass\n"
        "def _validation_reason(): pass\n",
        encoding="utf-8",
    )
    (harness / "planner.py").write_text("def find_python_test_paths(): pass\n", encoding="utf-8")
    (harness / "models.py").write_text("class TaskPlan: pass\nclass WorkingMemory: pass\n", encoding="utf-8")
    (tmp_path / "test_agent_loop.py").write_text("def test_validation():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan(
        "improve validation selection for rename tasks",
        tmp_path,
        [],
    )

    assert "task_planning" in plan.affected_behavior_ids
    assert "validation_selection" in plan.affected_behavior_ids
    assert "src/coding_agent_v1/agent_loop.py" in plan.implementation_surfaces
    assert "behavior index selected affected behavior(s):" in " ".join(plan.reasons)


def test_build_task_plan_inferrs_natural_cli_request_from_workspace_parser_shape(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )

    plan = build_task_plan("make the parser support verbose mode", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "cli_flag"
    assert plan.feature_arguments["flag_name"] == "--verbose"
    assert plan.validation_command == "pytest -q test_cli.py"
    assert "feature strategy inferred from workspace: `cli_flag`" in " ".join(plan.reasons)
    assert "planner selected `feature` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "workspace contains 1 argparse parser file(s)" in " ".join(plan.reasons)


def test_build_task_plan_selects_matching_rename_tests_in_multi_test_repo(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("rename add to plus", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.RENAME
    assert plan.validation_command == "pytest -q test_calc.py"
    assert "workspace contains" in " ".join(plan.reasons)
    assert "exact symbol match(es)" in " ".join(plan.reasons)


def test_build_task_plan_falls_back_to_module_aware_rename_test_selection(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "report.py").write_text(
        "def render_summary(value):\n    return value.upper()\n",
        encoding="utf-8",
    )
    (tmp_path / "test_report.py").write_text(
        (
            "import report\n\n"
            "def test_render_report_uses_uppercase_output():\n"
            "    assert report.render_report('ok') == 'OK'\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("rename render_summary to render_report", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.RENAME
    assert plan.validation_command == "pytest -q test_report.py"
    assert "selected validation command `pytest -q test_report.py` from module-aware rename test evidence" in " ".join(
        plan.reasons
    )


def test_build_task_plan_selects_matching_config_option_tests_in_multi_test_repo(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text('DEFAULT_CONFIG = {"mode": "basic"}\n', encoding="utf-8")
    (tmp_path / "test_config.py").write_text(
        'from config import DEFAULT_CONFIG\n\n\ndef test_timeout():\n    assert DEFAULT_CONFIG["timeout"] == 30\n',
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add a timeout config option with default 30", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "config_option"
    assert plan.feature_arguments["option_name"] == "timeout"
    assert plan.validation_command == "pytest -q test_config.py"


def test_build_task_plan_supports_string_default_config_option_request(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text('DEFAULT_CONFIG = {"mode": "basic"}\n', encoding="utf-8")
    (tmp_path / "test_config.py").write_text(
        'from config import DEFAULT_CONFIG\n\n\ndef test_mode():\n    assert DEFAULT_CONFIG["profile"] == "advanced"\n',
        encoding="utf-8",
    )

    plan = build_task_plan("add a profile config option with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "config_option"
    assert plan.feature_arguments["value_literal"] == '"advanced"'
    assert plan.validation_command == "pytest -q test_config.py"


def test_build_task_plan_inferrs_generic_option_request_from_workspace_config_shape(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text('DEFAULT_CONFIG = {"mode": "basic"}\n', encoding="utf-8")
    (tmp_path / "test_config.py").write_text(
        'from config import DEFAULT_CONFIG\n\n\ndef test_mode():\n    assert DEFAULT_CONFIG["profile"] == "advanced"\n',
        encoding="utf-8",
    )

    plan = build_task_plan("add a profile option with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "config_option"
    assert plan.feature_arguments["option_name"] == "profile"
    assert plan.feature_arguments["value_literal"] == '"advanced"'
    assert plan.validation_command == "pytest -q test_config.py"
    assert "feature strategy inferred from workspace: `config_option`" in " ".join(plan.reasons)


def test_build_task_plan_falls_back_to_module_aware_config_test_selection(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "app_config.py").write_text('DEFAULT_CONFIG = {"mode": "basic"}\n', encoding="utf-8")
    (tmp_path / "test_app_config.py").write_text(
        (
            "from app_config import DEFAULT_CONFIG\n\n"
            "def test_config_gains_one_more_default():\n"
            "    assert len(DEFAULT_CONFIG) == 2\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add a profile option with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "config_option"
    assert plan.validation_command == "pytest -q test_app_config.py"


def test_build_task_plan_inferrs_natural_config_request_from_workspace_shape(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text('DEFAULT_CONFIG = {"mode": "basic"}\n', encoding="utf-8")
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_profile_config():\n"
            '    assert DEFAULT_CONFIG["profile"] == "advanced"\n'
        ),
        encoding="utf-8",
    )

    plan = build_task_plan("make config support profile with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "config_option"
    assert plan.feature_arguments["option_name"] == "profile"
    assert plan.feature_arguments["value_literal"] == '"advanced"'
    assert plan.validation_command == "pytest -q test_config.py"
    assert "feature strategy inferred from workspace: `config_option`" in " ".join(plan.reasons)
    assert "planner selected `feature` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "workspace contains 1 config-style mapping file(s)" in " ".join(plan.reasons)


def test_build_task_plan_selects_matching_env_var_tests_in_multi_test_repo(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add APP_PROFILE environment variable with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "env_var"
    assert plan.feature_arguments["env_name"] == "APP_PROFILE"
    assert plan.feature_arguments["option_name"] == "profile"
    assert plan.validation_command == "pytest -q test_config.py"


def test_build_task_plan_falls_back_to_module_aware_env_var_test_selection(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "runtime_config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_runtime_config.py").write_text(
        (
            "from runtime_config import DEFAULT_CONFIG\n\n"
            "def test_config_gains_a_second_value():\n"
            "    assert len(DEFAULT_CONFIG.values()) == 2\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")

    plan = build_task_plan("add APP_PROFILE with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "env_var"
    assert plan.validation_command == "pytest -q test_runtime_config.py"


def test_build_task_plan_inferrs_generic_env_var_request_from_workspace_config_shape(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )

    plan = build_task_plan("add APP_PROFILE with default advanced", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "env_var"
    assert plan.feature_arguments["env_name"] == "APP_PROFILE"
    assert plan.feature_arguments["option_name"] == "profile"
    assert plan.feature_arguments["value_literal"] == '"advanced"'
    assert plan.validation_command == "pytest -q test_config.py"
    assert "feature strategy inferred from workspace: `env_var`" in " ".join(plan.reasons)


def test_build_task_plan_inferrs_natural_env_request_from_workspace_shape(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )

    plan = build_task_plan(
        "make config read profile from APP_PROFILE with default advanced",
        tmp_path,
        ["README.md"],
    )

    assert plan.task_flow is TaskFlow.FEATURE
    assert plan.feature_strategy == "env_var"
    assert plan.feature_arguments["env_name"] == "APP_PROFILE"
    assert plan.feature_arguments["option_name"] == "profile"
    assert plan.feature_arguments["value_literal"] == '"advanced"'
    assert plan.validation_command == "pytest -q test_config.py"
    assert "feature strategy inferred from workspace: `env_var`" in " ".join(plan.reasons)
    assert "planner selected `feature` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "workspace contains 1 environment-backed config mapping file(s)" in " ".join(plan.reasons)


def test_build_task_plan_scores_natural_fix_request_into_fix_flow(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan("make the failing tests pass", tmp_path, [])

    assert plan.task_flow is TaskFlow.FIX
    assert "planner selected `fix` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "fix evidence:" in " ".join(plan.reasons)


def test_build_task_plan_scores_natural_diagnose_request_into_diagnose_flow(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan("investigate the failing tests", tmp_path, [])

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert "planner selected `diagnose` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "diagnose evidence:" in " ".join(plan.reasons)


def test_build_task_plan_uses_workspace_test_reference_for_passive_failure_report(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan("test_calc.py is failing", tmp_path, [])

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "pytest -q test_calc.py"
    assert "planner selected `diagnose` from scored task-flow candidates" in " ".join(plan.reasons)
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_quoted_test_reference_with_spaces_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan("'tests with spaces/unit/test_calc.py' is failing", tmp_path, [])

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_backticked_test_reference_with_spaces_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan("`tests with spaces/unit/test_calc.py` is failing", tmp_path, [])

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_markdown_linked_test_reference_with_spaces_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "[failing test](tests with spaces/unit/test_calc.py) is failing",
        tmp_path,
        [],
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_angle_bracket_markdown_linked_test_reference_with_spaces_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "[failing test](<tests with spaces/unit/test_calc.py>) is failing",
        tmp_path,
        [],
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_line_suffixed_markdown_linked_test_reference_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "[failing test](<tests with spaces/unit/test_calc.py:12>) is failing",
        tmp_path,
        [],
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_github_anchor_markdown_linked_test_reference_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "[failing test](tests with spaces/unit/test_calc.py#L12-L15) is failing",
        tmp_path,
        [],
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_uses_absolute_markdown_linked_test_reference_with_line_suffix_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    test_path = spaced_tests / "test_calc.py"
    test_path.write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(f"[failing test](<{test_path}:12>) is failing", tmp_path, [])

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert plan.validation_command == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    assert "references existing test `test_calc.py`" in " ".join(plan.reasons)


def test_build_task_plan_reports_multiple_referenced_tests_for_passive_failure_report(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text("def add(a, b):\n    return a - b\n", encoding="utf-8")
    first_tests = tmp_path / "tests" / "quoted"
    first_tests.mkdir(parents=True, exist_ok=True)
    (first_tests / "test_first.py").write_text(
        "from calc import add\n\n\ndef test_first():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    second_tests = tmp_path / "tests" / "linked"
    second_tests.mkdir(parents=True, exist_ok=True)
    (second_tests / "test_second.py").write_text(
        "from calc import add\n\n\ndef test_second():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )

    plan = build_task_plan(
        "'tests/quoted/test_first.py' and [second](tests/linked/test_second.py) are failing",
        tmp_path,
        [],
    )

    assert plan.task_flow is TaskFlow.DIAGNOSE
    assert (
        plan.validation_command
        == "PYTHONPATH=. pytest -q tests/quoted/test_first.py tests/linked/test_second.py"
    )
    assert "references existing tests `test_first.py`, `test_second.py`" in " ".join(plan.reasons)


def test_build_task_plan_reports_full_suite_fallback_for_run_tests_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text(
        "def test_other():\n    assert True\n",
        encoding="utf-8",
    )

    plan = build_task_plan("run tests", tmp_path, [])

    assert plan.task_flow is TaskFlow.FIX
    assert plan.validation_command == "pytest -q"
    assert (
        "selected validation command `pytest -q` "
        "from full-suite fallback because no narrower test target was justified"
    ) in " ".join(plan.reasons)


def test_build_task_plan_scores_repo_summary_request_into_inspect_flow(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")

    plan = build_task_plan("summarize this repo", tmp_path, ["README.md"])

    assert plan.task_flow is TaskFlow.INSPECT
    assert plan.validation_command == ""
    assert "planner selected `inspect` from scored task-flow candidates" in " ".join(plan.reasons)
    assert (
        "inspect evidence: request asks for repo inspection and README.md is available for context"
        in " ".join(plan.reasons)
    )


def test_run_session_reads_repo_instructions(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session("summarize this repo", tmp_path, store)

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.INSPECT
    assert record.task_plan is not None
    assert record.task_plan.task_flow is TaskFlow.INSPECT
    assert "Task flow: inspect." in record.final_report
    assert "No validation was run." in record.final_report
    assert "Inspected:" in record.final_report
    assert any("read_file:" in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_runs_validation_for_test_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run the tests", tmp_path, store)

    assert record.status.value == "failed"
    assert "approval is required" in record.final_report.lower()
    handoff = store.load_handoff(record.session_id)
    assert handoff.reason == "approval_required"
    assert handoff.status == "failed"
    assert handoff.task_flow == "fix"
    assert handoff.next_step
    assert any(item == "task_flow=fix" for item in handoff.belief)
    assert any(item.startswith("next=") for item in handoff.progress)


def test_run_session_runs_validation_for_run_tests_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run tests", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert any(
        "selected validation command `pytest -q` "
        "from full-suite fallback because no narrower test target was justified"
        in reason
        for reason in record.task_plan.reasons
    )


def test_run_session_writes_handoff_after_failed_validation(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_broken():\n    assert False\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run tests", tmp_path, store, auto_approve_commands=True)
    handoff = store.load_handoff(record.session_id)

    assert record.status.value == "failed"
    assert handoff.reason == "validation_failed"
    assert handoff.validation_summary.startswith("Validation failed via run_command")
    assert handoff.blocker
    assert any(item.startswith("validation=") for item in handoff.belief)
    assert any(item.startswith("validation_state=") for item in handoff.progress)


def test_run_session_writes_procedural_repair_after_failed_validation(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_broken():\n    assert False\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run tests", tmp_path, store, auto_approve_commands=True)
    repairs = store.list_procedural_repair_records(task_class="fix")

    assert record.status.value == "failed"
    assert len(repairs) == 1
    assert repairs[0].source_session_id == record.session_id
    assert repairs[0].failure_pattern == "validation_failed"
    assert repairs[0].status == "candidate"
    assert repairs[0].validation_evidence


def test_run_session_recalls_matching_procedural_repair_into_experience(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_broken():\n    assert False\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    failed = run_session("run tests", tmp_path, store, auto_approve_commands=True)
    recalled = run_session("run tests", tmp_path, store, auto_approve_commands=True)

    assert any(event.kind == "repair_memory" for event in recalled.events)
    assert any(
        item.startswith(f"recalled_repair={failed.session_id}-validation-failed")
        for item in recalled.working_memory.experience
    )


def test_run_session_recalls_accepted_procedural_repair_into_experience(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_broken():\n    assert False\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    failed = run_session("run tests", tmp_path, store, auto_approve_commands=True)
    repair_id = f"{failed.session_id}-validation-failed"
    store.update_procedural_repair_status(repair_id, "accepted")
    recalled = run_session("run tests", tmp_path, store, auto_approve_commands=True)

    assert any(event.kind == "repair_memory" for event in recalled.events)
    assert any(
        item.startswith(f"recalled_repair={repair_id}")
        for item in recalled.working_memory.experience
    )


def test_run_session_runs_validation_for_run_pytest_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run pytest", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_run_the_suite_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run the suite", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_rerun_tests_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("rerun tests", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_run_unit_tests_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run unit tests", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_rerun_pytest_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("rerun pytest", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_rerun_unit_tests_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("rerun unit tests", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_run_test_suite_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("run the test suite", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_runs_validation_for_rerun_test_suite_request(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session("rerun the test suite", tmp_path, store)

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.FIX
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q"
    assert "approval is required" in record.final_report.lower()


def test_run_session_auto_approves_and_runs_test_diagnosis(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.task_flow is TaskFlow.FIX
    assert any(event.kind == "diagnosis" for event in record.events)
    assert any("search_code:" in event.message for event in record.events if event.kind == "tool_result")
    assert all(".pytest_cache" not in path for path in record.inspected_files)
    assert all("__pycache__" not in path for path in record.inspected_files)


def test_run_session_auto_repairs_simple_arithmetic_bug(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FIX
    assert "Validation passed via run_command." in record.final_report
    assert "[score=" in record.final_report
    assert "Candidates:" in record.final_report
    assert "Proposed:" in record.final_report
    assert "Changed: calc.py." in record.final_report
    assert "Why:" in record.final_report
    assert "return a + b" in (tmp_path / "calc.py").read_text(encoding="utf-8")
    assert "calc.py" in record.changed_files
    assert record.candidate_proposals[0].file == "calc.py"
    assert record.candidate_proposals[0].score > 0
    assert record.candidate_proposals[0].evidence
    assert record.proposed_changes[0].file == "calc.py"
    assert record.proposed_changes[0].new_text == "return a + b"
    assert "test_calc.py" in record.inspected_files
    assert any(event.kind == "repair_candidates" for event in record.events)
    assert any(event.kind == "repair_plan" for event in record.events)
    assert any(event.kind == "diagnosis" for event in record.events)
    assert any("edit_file:" in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_repairs_from_natural_fix_request(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "make the failing tests pass",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FIX
    assert "return a + b" in (tmp_path / "calc.py").read_text(encoding="utf-8")
    assert "Validation passed via run_command." in record.final_report


def test_saved_session_json_includes_proposal_and_evidence(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    session_dir = tmp_path / "sessions"
    store = SessionStore(session_dir)

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    saved_path = session_dir / f"{record.session_id}.json"
    payload = json.loads(saved_path.read_text(encoding="utf-8"))

    assert payload["status"] == "completed"
    assert payload["task_flow"] == "fix"
    assert payload["task_plan"]["task_flow"] == "fix"
    assert payload["task_plan"]["validation_command"] == "pytest -q"
    assert payload["working_memory"]["task_flow"] == "fix"
    assert payload["working_memory"]["changed_files"] == ["calc.py"]
    assert "next_step" in payload["working_memory"]
    assert any(item == "task_flow=fix" for item in payload["working_memory"]["belief"])
    assert any(item.startswith("validation=") for item in payload["working_memory"]["belief"])
    assert any(item == "changed=calc.py" for item in payload["working_memory"]["progress"])
    assert any(item.startswith("validation_state=") for item in payload["working_memory"]["progress"])
    assert any(item == "candidate_repairs=1" for item in payload["working_memory"]["experience"])
    assert payload["changed_files"] == ["calc.py"]
    assert "test_calc.py" in payload["inspected_files"]
    assert payload["candidate_proposals"][0]["file"] == "calc.py"
    assert payload["candidate_proposals"][0]["score"] > 0
    assert "asserted-callable" in " ".join(payload["candidate_proposals"][0]["evidence"])
    assert payload["proposed_changes"][0]["file"] == "calc.py"
    assert payload["proposed_changes"][0]["new_text"] == "return a + b"
    assert "Validation passed via run_command." in payload["final_report"]


def test_run_session_repairs_wrong_literal_return(tmp_path: Path) -> None:
    (tmp_path / "greet.py").write_text(
        "def greeting():\n    return 'bye'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_greet.py").write_text(
        "from greet import greeting\n\n\ndef test_greeting():\n    assert greeting() == 'hello'\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert "return 'hello'" in (tmp_path / "greet.py").read_text(encoding="utf-8")
    assert record.proposed_changes[0].file == "greet.py"
    assert record.proposed_changes[0].new_text == "return 'hello'"
    assert "Proposed:" in record.final_report
    assert "Changed: greet.py." in record.final_report


def test_run_session_chooses_asserted_function_when_multiple_imports_exist(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "greet.py").write_text(
        "def greeting():\n    return 'bye'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_multi.py").write_text(
        (
            "from calc import add\n"
            "from greet import greeting\n\n"
            "def test_greeting():\n"
            "    assert greeting() == 'hello'\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert "return 'hello'" in (tmp_path / "greet.py").read_text(encoding="utf-8")
    assert "return a - b" in (tmp_path / "calc.py").read_text(encoding="utf-8")
    assert record.proposed_changes[0].file == "greet.py"


def test_run_session_records_multiple_candidates_and_selects_one(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "greet.py").write_text(
        "def greeting():\n    return 'bye'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_dual.py").write_text(
        (
            "from calc import add\n"
            "from greet import greeting\n\n"
            "def test_add():\n"
            "    assert add(1, 2) == 3\n\n"
            "def test_greeting():\n"
            "    assert greeting() == 'hello'\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert len(record.candidate_proposals) >= 2
    assert {proposal.file for proposal in record.candidate_proposals} == {"calc.py", "greet.py"}
    assert len(record.proposed_changes) == 1
    assert record.proposed_changes[0].file in {"calc.py", "greet.py"}
    assert all(proposal.score > 0 for proposal in record.candidate_proposals)
    assert "Candidates:" in record.final_report


def test_run_session_supports_module_import_style_in_tests(tmp_path: Path) -> None:
    (tmp_path / "greet.py").write_text(
        "def greeting():\n    return 'bye'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_greet.py").write_text(
        (
            "import greet\n\n"
            "def test_greeting():\n"
            "    assert greet.greeting() == 'hello'\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert "return 'hello'" in (tmp_path / "greet.py").read_text(encoding="utf-8")
    assert record.proposed_changes[0].file == "greet.py"
    assert any(
        "asserted-callable:greet.greeting" in " ".join(proposal.evidence)
        for proposal in record.candidate_proposals
    )


def test_run_session_supports_aliased_from_import_in_tests(tmp_path: Path) -> None:
    (tmp_path / "greet.py").write_text(
        "def greeting():\n    return 'bye'\n",
        encoding="utf-8",
    )
    (tmp_path / "test_greet.py").write_text(
        (
            "from greet import greeting as say_hi\n\n"
            "def test_greeting():\n"
            "    assert say_hi() == 'hello'\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert "return 'hello'" in (tmp_path / "greet.py").read_text(encoding="utf-8")
    assert record.proposed_changes[0].file == "greet.py"
    assert any(
        "asserted-callable:say_hi" in " ".join(proposal.evidence)
        for proposal in record.candidate_proposals
    )


def test_run_session_repairs_wrong_module_constant_return(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        "DEFAULT_GREETING = 'bye'\n\n\ndef greeting():\n    return DEFAULT_GREETING\n",
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import greeting\n\n"
            "def test_greeting():\n"
            "    assert greeting() == 'hello'\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "fix the failing test",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert "DEFAULT_GREETING = 'hello'" in (tmp_path / "config.py").read_text(encoding="utf-8")
    assert record.proposed_changes[0].file == "config.py"
    assert record.proposed_changes[0].new_text == "DEFAULT_GREETING = 'hello'"
    assert any(
        "behavior-match:constant" in " ".join(proposal.evidence)
        for proposal in record.candidate_proposals
    )


def test_run_session_performs_safe_multi_file_rename_and_reruns_tests(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        (
            "def add(a, b):\n"
            "    return a + b\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        (
            "from calc import add\n\n"
            "def test_add():\n"
            "    assert add(1, 2) == 3\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "rename add to plus",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q test_calc.py"
    assert "Validation passed via run_command." in record.final_report
    assert "calc.py" in record.changed_files
    assert "test_calc.py" in record.changed_files
    assert len(record.proposed_changes) == 2
    assert any(event.kind == "rename_plan" for event in record.events)
    assert any("rename_symbol_in_file:" in event.message for event in record.events if event.kind == "tool_result")
    calc_text = (tmp_path / "calc.py").read_text(encoding="utf-8")
    test_text = (tmp_path / "test_calc.py").read_text(encoding="utf-8")
    assert "def plus(a, b):" in calc_text
    assert "from calc import plus" in test_text
    assert "assert plus(1, 2) == 3" in test_text
    assert " add(" not in test_text


def test_run_session_adds_cli_flag_and_reruns_tests(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a --verbose flag",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "cli_flag"
    assert record.task_plan.validation_command == "pytest -q test_cli.py"
    assert "Validation passed via run_command." in record.final_report
    assert "cli.py" in record.changed_files
    assert len(record.proposed_changes) == 1
    assert record.proposed_changes[0].file == "cli.py"
    assert any(event.kind == "feature_plan" for event in record.events)
    cli_text = (tmp_path / "cli.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' in cli_text


def test_run_session_adds_cli_flag_from_natural_parser_request(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "make the parser support verbose mode",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "cli_flag"
    assert record.task_plan.feature_arguments["flag_name"] == "--verbose"
    assert record.task_plan.validation_command == "pytest -q test_cli.py"
    assert any(
        "feature strategy inferred from workspace: `cli_flag`" in reason
        for reason in record.task_plan.reasons
    )
    cli_text = (tmp_path / "cli.py").read_text(encoding="utf-8")
    assert 'parser.add_argument("--verbose", action="store_true", help="Enable verbose mode.")' in cli_text


def test_run_session_uses_nested_relative_test_path_for_targeted_feature_validation(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    nested_tests = tmp_path / "tests" / "unit"
    nested_tests.mkdir(parents=True, exist_ok=True)
    (nested_tests / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a --verbose flag",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "PYTHONPATH=. pytest -q tests/unit/test_cli.py"
    assert "Validation passed via run_command." in record.final_report


def test_run_session_prefers_explicit_test_reference_over_feature_heuristics(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    referenced_tests = tmp_path / "tests" / "regression"
    referenced_tests.mkdir(parents=True, exist_ok=True)
    (referenced_tests / "test_targeted_cli.py").write_text(
        "def test_targeted_cli_regression():\n    assert True\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a --verbose flag so [target](tests/regression/test_targeted_cli.py) passes",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py"
    )


def test_run_session_uses_multiple_explicit_test_references_for_validation(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    first_tests = tmp_path / "tests" / "regression"
    first_tests.mkdir(parents=True, exist_ok=True)
    (first_tests / "test_targeted_cli.py").write_text(
        "def test_targeted_cli_regression():\n    assert True\n",
        encoding="utf-8",
    )
    second_tests = tmp_path / "tests" / "smoke"
    second_tests.mkdir(parents=True, exist_ok=True)
    (second_tests / "test_cli_smoke.py").write_text(
        "def test_cli_smoke():\n    assert True\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        (
            "add a --verbose flag so "
            "[first](tests/regression/test_targeted_cli.py) and "
            "[second](tests/smoke/test_cli_smoke.py) pass"
        ),
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py"
    )


def test_run_session_keeps_all_explicit_test_references_even_beyond_three_paths(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    paths = [
        "tests/regression/test_targeted_cli.py",
        "tests/smoke/test_cli_smoke.py",
        "tests/unit/test_cli_unit.py",
        "tests/integration/test_cli_integration.py",
    ]
    for relative in paths:
        test_path = tmp_path / relative
        test_path.parent.mkdir(parents=True, exist_ok=True)
        test_path.write_text("def test_marker():\n    assert True\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        (
            "add a --verbose flag so "
            "[one](tests/regression/test_targeted_cli.py), "
            "[two](tests/smoke/test_cli_smoke.py), "
            "[three](tests/unit/test_cli_unit.py), and "
            "[four](tests/integration/test_cli_integration.py) pass"
        ),
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q tests/regression/test_targeted_cli.py tests/smoke/test_cli_smoke.py tests/unit/test_cli_unit.py tests/integration/test_cli_integration.py"
    )


def test_run_session_preserves_request_order_for_mixed_test_reference_formats(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    first_path = tmp_path / "tests" / "quoted" / "test_first.py"
    first_path.parent.mkdir(parents=True, exist_ok=True)
    first_path.write_text("def test_first():\n    assert True\n", encoding="utf-8")
    second_path = tmp_path / "tests" / "linked" / "test_second.py"
    second_path.parent.mkdir(parents=True, exist_ok=True)
    second_path.write_text("def test_second():\n    assert True\n", encoding="utf-8")
    third_path = tmp_path / "tests" / "plain" / "test_third.py"
    third_path.parent.mkdir(parents=True, exist_ok=True)
    third_path.write_text("def test_third():\n    assert True\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        (
            "add a --verbose flag so "
            "'tests/quoted/test_first.py', "
            "[second](tests/linked/test_second.py), and "
            "tests/plain/test_third.py pass"
        ),
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q tests/quoted/test_first.py tests/linked/test_second.py tests/plain/test_third.py"
    )


def test_run_session_quotes_targeted_validation_paths_with_spaces(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a --verbose flag",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_cli.py'"
    )
    assert "Validation passed via run_command." in record.final_report


def test_run_session_adds_config_option_and_reruns_matching_tests(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'DEFAULT_CONFIG = {"mode": "basic"}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_timeout_config():\n"
            '    assert DEFAULT_CONFIG["timeout"] == 30\n'
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a timeout config option with default 30",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "config_option"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert "Validation passed via run_command." in record.final_report
    assert "config.py" in record.changed_files
    assert len(record.proposed_changes) == 1
    assert record.proposed_changes[0].file == "config.py"
    assert any(event.kind == "feature_plan" for event in record.events)
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"timeout": 30' in config_text


def test_run_session_adds_string_default_config_option_and_reruns_matching_tests(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'DEFAULT_CONFIG = {"mode": "basic"}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_profile_config():\n"
            '    assert DEFAULT_CONFIG["profile"] == "advanced"\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a profile config option with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "config_option"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert "Validation passed via run_command." in record.final_report
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": "advanced"' in config_text


def test_run_session_adds_inferred_generic_config_option_and_reruns_matching_tests(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'DEFAULT_CONFIG = {"mode": "basic"}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_profile_config():\n"
            '    assert DEFAULT_CONFIG["profile"] == "advanced"\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a profile option with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "config_option"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert "Validation passed via run_command." in record.final_report
    assert any(
        "feature strategy inferred from workspace: `config_option`" in reason
        for reason in record.task_plan.reasons
    )
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": "advanced"' in config_text


def test_run_session_adds_config_option_from_natural_config_request(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'DEFAULT_CONFIG = {"mode": "basic"}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\n\n"
            "def test_profile_config():\n"
            '    assert DEFAULT_CONFIG["profile"] == "advanced"\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "make config support profile with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "config_option"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert any(
        "feature strategy inferred from workspace: `config_option`" in reason
        for reason in record.task_plan.reasons
    )
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": "advanced"' in config_text


def test_run_session_adds_env_var_config_option_and_reruns_matching_tests(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add APP_PROFILE environment variable with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "env_var"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert "Validation passed via run_command." in record.final_report
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": os.getenv("APP_PROFILE", "advanced")' in config_text


def test_run_session_adds_inferred_generic_env_var_config_option_and_reruns_matching_tests(
    tmp_path: Path,
) -> None:
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add APP_PROFILE with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "env_var"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert "Validation passed via run_command." in record.final_report
    assert any(
        "feature strategy inferred from workspace: `env_var`" in reason
        for reason in record.task_plan.reasons
    )
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": os.getenv("APP_PROFILE", "advanced")' in config_text


def test_run_session_adds_env_var_config_option_from_natural_request(tmp_path: Path) -> None:
    (tmp_path / "config.py").write_text(
        'import os\n\nDEFAULT_CONFIG = {"mode": os.getenv("APP_MODE", "basic")}\n',
        encoding="utf-8",
    )
    (tmp_path / "test_config.py").write_text(
        (
            "from config import DEFAULT_CONFIG\nimport os\n\n"
            "def test_profile_env_var():\n"
            '    assert DEFAULT_CONFIG["profile"] == os.getenv("APP_PROFILE", "advanced")\n'
        ),
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "make config read profile from APP_PROFILE with default advanced",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_flow is TaskFlow.FEATURE
    assert record.task_plan is not None
    assert record.task_plan.feature_strategy == "env_var"
    assert record.task_plan.validation_command == "pytest -q test_config.py"
    assert any(
        "feature strategy inferred from workspace: `env_var`" in reason
        for reason in record.task_plan.reasons
    )
    config_text = (tmp_path / "config.py").read_text(encoding="utf-8")
    assert '"profile": os.getenv("APP_PROFILE", "advanced")' in config_text


def test_run_session_feature_flow_prefers_matching_test_files_in_multi_test_repo(tmp_path: Path) -> None:
    (tmp_path / "cli.py").write_text(
        (
            "import argparse\n\n"
            "def build_parser():\n"
            '    parser = argparse.ArgumentParser(description="demo")\n'
            "    return parser\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_cli.py").write_text(
        (
            "from cli import build_parser\n\n"
            "def test_parser_accepts_verbose_flag():\n"
            "    parser = build_parser()\n"
            "    args = parser.parse_args(['--verbose'])\n"
            "    assert args.verbose is True\n"
        ),
        encoding="utf-8",
    )
    (tmp_path / "test_other.py").write_text("def test_other():\n    assert True\n", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "add a --verbose flag",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "completed"
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q test_cli.py"


def test_run_session_resume_carries_prior_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    first = run_session("summarize this repo", tmp_path, store)
    second = run_session(
        "summarize this repo again",
        tmp_path,
        store,
        resume_from_session_id=first.session_id,
    )

    assert second.status.value == "completed"
    assert second.resumed_from_session_id == first.session_id
    assert "README.md" in second.inspected_files
    assert any(event.kind == "resume" for event in second.events)
    assert any(event.kind == "task_plan" for event in second.events)
    assert f"Resumed from session {first.session_id}." in second.final_report
    assert first.session_id in second.working_summary
    assert second.working_memory.resume_context.startswith(f"from={first.session_id}")
    assert second.working_memory.task_flow == "inspect"
    assert second.working_memory.focus
    assert any(item == "task_flow=inspect" for item in second.working_memory.belief)
    assert any(item.startswith("next=") for item in second.working_memory.progress)
    assert any(item == f"resumed_from={first.session_id}" for item in second.working_memory.experience)


def test_run_session_resume_prefers_compact_context_when_available(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    store = SessionStore(tmp_path / "sessions")

    first = run_session("summarize this repo", tmp_path, store)
    compact_path = tmp_path / "sessions" / "compactions" / f"{first.session_id}.compact.json"
    payload = json.loads(compact_path.read_text(encoding="utf-8"))
    payload["inspected_files"] = ["compact-only.md"]
    payload["belief"] = ["compact-belief"]
    payload["progress"] = ["compact-progress"]
    payload["experience"] = ["compact-experience"]
    payload["summary"] = "compact-summary"
    compact_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    second = run_session(
        "summarize this repo again",
        tmp_path,
        store,
        resume_from_session_id=first.session_id,
    )

    assert "compact-only.md" in second.inspected_files
    assert any(event.kind == "compact_resume" for event in second.events)
    assert "resumed_from_compact=" + first.session_id in second.working_memory.experience
    assert "compact-experience" in second.working_memory.experience


def test_run_session_resume_from_handoff_carries_bpe_context(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("project intro", encoding="utf-8")
    (tmp_path / "test_sample.py").write_text(
        "def test_ok():\n    assert 1 == 1\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    failed = run_session("run the tests", tmp_path, store)
    resumed = run_session(
        "continue by summarizing this repo",
        tmp_path,
        store,
        resume_from_handoff_id=failed.session_id,
    )

    assert resumed.status.value == "completed"
    assert resumed.resumed_from_session_id == failed.session_id
    assert any(event.kind == "handoff_resume" for event in resumed.events)
    assert resumed.working_memory.resume_context.startswith(f"handoff={failed.session_id}")
    assert any(
        item == f"resumed_from_handoff={failed.session_id}"
        for item in resumed.working_memory.experience
    )
    assert f"handoff_belief={failed.working_memory.belief[0]}" in resumed.working_summary


def test_run_session_diagnose_flow_gathers_evidence_without_editing(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "diagnose why the tests fail",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.changed_files == []
    assert record.proposed_changes == []
    assert any(event.kind == "diagnosis" for event in record.events)
    assert any("search_code:" in event.message for event in record.events if event.kind == "tool_result")
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")
    assert "Task flow: diagnose." in record.final_report
    assert "Failure hints:" in record.final_report
    assert "without applying edits" in record.final_report


def test_run_session_diagnose_flow_supports_natural_investigation_request(tmp_path: Path) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "investigate the failing tests",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")
    assert "Task flow: diagnose." in record.final_report


def test_run_session_diagnose_flow_supports_passive_failure_report_with_existing_test_reference(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    (tmp_path / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "test_calc.py is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert record.task_plan.validation_command == "pytest -q test_calc.py"
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_quoted_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "'tests with spaces/unit/test_calc.py' is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_backticked_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "`tests with spaces/unit/test_calc.py` is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_markdown_linked_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "[failing test](tests with spaces/unit/test_calc.py) is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_angle_bracket_markdown_linked_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "[failing test](<tests with spaces/unit/test_calc.py>) is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_line_suffixed_markdown_linked_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "[failing test](<tests with spaces/unit/test_calc.py:12>) is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_github_anchor_markdown_linked_existing_test_reference_with_spaces(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    (spaced_tests / "test_calc.py").write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "[failing test](tests with spaces/unit/test_calc.py#L12-L15) is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_supports_absolute_markdown_linked_existing_test_reference_with_line_suffix(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    spaced_tests = tmp_path / "tests with spaces" / "unit"
    spaced_tests.mkdir(parents=True, exist_ok=True)
    test_path = spaced_tests / "test_calc.py"
    test_path.write_text(
        "from calc import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        f"[failing test](<{test_path}:12>) is failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q 'tests with spaces/unit/test_calc.py'"
    )
    assert any(
        "references existing test `test_calc.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")


def test_run_session_diagnose_flow_reports_multiple_referenced_tests(
    tmp_path: Path,
) -> None:
    (tmp_path / "calc.py").write_text(
        "def add(a, b):\n    return a - b\n",
        encoding="utf-8",
    )
    first_tests = tmp_path / "tests" / "quoted"
    first_tests.mkdir(parents=True, exist_ok=True)
    (first_tests / "test_first.py").write_text(
        "from calc import add\n\n\ndef test_first():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    second_tests = tmp_path / "tests" / "linked"
    second_tests.mkdir(parents=True, exist_ok=True)
    (second_tests / "test_second.py").write_text(
        "from calc import add\n\n\ndef test_second():\n    assert add(1, 2) == 3\n",
        encoding="utf-8",
    )
    store = SessionStore(tmp_path / "sessions")

    record = run_session(
        "'tests/quoted/test_first.py' and [second](tests/linked/test_second.py) are failing",
        tmp_path,
        store,
        auto_approve_commands=True,
    )

    assert record.status.value == "failed"
    assert record.task_flow is TaskFlow.DIAGNOSE
    assert record.task_plan is not None
    assert (
        record.task_plan.validation_command
        == "PYTHONPATH=. pytest -q tests/quoted/test_first.py tests/linked/test_second.py"
    )
    assert any(
        "references existing tests `test_first.py`, `test_second.py`" in reason
        for reason in record.task_plan.reasons
    )
    assert record.changed_files == []
    assert all("edit_file:" not in event.message for event in record.events if event.kind == "tool_result")
