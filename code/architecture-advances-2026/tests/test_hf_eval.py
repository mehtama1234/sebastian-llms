from __future__ import annotations

from arch_adv_2026.hf_eval import PromptCase, _longest_common_prefix_chars


def test_prompt_case_defaults_to_chat_mode() -> None:
    case = PromptCase(name="demo", prompt="hello")
    assert case.prompt_mode == "chat"
    assert case.max_new_tokens == 48


def test_longest_common_prefix_chars_counts_shared_prefix() -> None:
    assert _longest_common_prefix_chars("hello world", "hello there") == 6
    assert _longest_common_prefix_chars("abc", "xyz") == 0
