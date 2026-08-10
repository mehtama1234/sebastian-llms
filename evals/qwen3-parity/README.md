# Qwen3 Parity Evals

This directory is for bounded parity checks between:

- an official Qwen3 0.6B dense reference model
- the local scratch implementation

## Planned Checks

- config parity
- tensor shape parity
- tensor-count parity
- selected weight-name coverage
- logits comparison on fixed prompts
- token-by-token greedy generation comparison on short prompts
- KV-cache smoke tests

## Initial Prompt Set

The first prompt set should be intentionally small and deterministic.

Examples:

- short factual prompt
- short code-completion prompt
- short reasoning prompt

## Acceptance Standard

The point is not to chase numerical perfection blindly.

The point is to be able to classify each result as one of:

- exact parity
- acceptable numerical drift
- implementation bug
- tokenizer or generation-setting mismatch
- unsupported difference that must be documented

## First Required Artifact

Before prompt-level parity begins, the project should write a reference snapshot artifact containing:

- model identifier
- library versions
- core config fields
- parameter counts
- tokenizer and model class names

This snapshot is the baseline the scratch implementation will eventually compare itself against.

The scratch side should also write a config snapshot artifact so the first parity checks can answer:

- do the local hard-coded assumptions match the official config
- are there any field-name, value, or default mismatches before model code exists

The first concrete gate should therefore be:

- both snapshot artifacts exist
- the config comparison script returns success

The next gate after config parity should be:

- the expected weight-map artifact exists
- every required official dense-model tensor name has a declared scratch destination

The next gate after that should be:

- the expected weight manifest exists
- a loader can report whether any official keys are missing
- a loader can report whether any mapped scratch keys are missing
