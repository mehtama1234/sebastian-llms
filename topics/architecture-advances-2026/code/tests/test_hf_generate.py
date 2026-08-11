from __future__ import annotations

from arch_adv_2026.hf_generate import build_messages, prepare_inputs


class FakeTokenizer:
    def apply_chat_template(
        self,
        messages,
        tokenize,
        add_generation_prompt,
        enable_thinking,
        return_tensors,
        return_dict,
    ):
        assert tokenize is True
        assert add_generation_prompt is True
        assert enable_thinking is False
        assert return_tensors == "pt"
        assert return_dict is True
        self.seen_messages = messages
        return {"input_ids": [[1, 2, 3]]}

    def decode(self, ids, skip_special_tokens=False):
        return "<chat>"

    def __call__(self, prompt, return_tensors):
        assert return_tensors == "pt"
        return {"input_ids": [[4, 5]]}


def test_build_messages_includes_optional_system_prompt() -> None:
    messages = build_messages("user prompt", "system rule")
    assert messages[0] == {"role": "system", "content": "system rule"}
    assert messages[1] == {"role": "user", "content": "user prompt"}


def test_prepare_inputs_uses_chat_template_when_requested() -> None:
    tokenizer = FakeTokenizer()
    encoded, rendered = prepare_inputs(
        tokenizer,
        "hello",
        prompt_mode="chat",
        system_prompt="be concise",
        enable_thinking=False,
    )
    assert tokenizer.seen_messages[0]["role"] == "system"
    assert encoded["input_ids"] == [[1, 2, 3]]
    assert rendered == "<chat>"


def test_prepare_inputs_falls_back_to_plain_prompt() -> None:
    tokenizer = FakeTokenizer()
    encoded, rendered = prepare_inputs(
        tokenizer,
        "plain prompt",
        prompt_mode="plain",
        system_prompt=None,
        enable_thinking=False,
    )
    assert encoded["input_ids"] == [[4, 5]]
    assert rendered == "plain prompt"
