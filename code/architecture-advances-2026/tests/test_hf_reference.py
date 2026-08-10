from __future__ import annotations

from arch_adv_2026.hf_reference import DEFAULT_MODEL_ID, build_parser, check_transformers


def test_hf_parser_defaults_to_qwen_reference() -> None:
    parser = build_parser()
    args = parser.parse_args(["--stdout"])
    assert args.model_id == DEFAULT_MODEL_ID
    assert args.config_only is False


def test_check_transformers_returns_structured_result() -> None:
    availability = check_transformers()
    assert isinstance(availability.available, bool)
