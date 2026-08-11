# Qwen3 0.6B Parity Goal

## Meaty Goal

Build a reference-vs-scratch Qwen3 0.6B dense implementation project that:

- reimplements the core architecture in PyTorch
- loads official weights into the scratch implementation
- proves parity against the reference model on a bounded evaluation set

## Why This Is The Right Goal

This goal is large enough to force real architectural understanding while still being narrow enough to complete without drifting into open-ended research.

It also produces multiple durable artifacts:

- architecture notes
- implementation code
- weight-loading logic
- evaluation harnesses
- debugging knowledge about reference parity

## Done Criteria

The project is only done when all of the following are true:

1. The repo contains a runnable reference loader for Qwen3 0.6B dense.
2. The repo contains a runnable scratch PyTorch implementation of the dense architecture.
3. The scratch model can accept official weights with documented tensor mapping.
4. The repo includes parity checks for:
   - config alignment
   - tensor shape alignment
   - selected logits on fixed prompts
   - bounded text generation comparisons
5. The repo documents any expected mismatch between educational parity and production parity.
6. The repo contains a short guide explaining how to rerun the parity workflow.

## Explicit Non-Goals For Phase 1

- MoE parity
- training Qwen3 from scratch
- RL or post-training work
- production inference serving
- benchmark chasing across many model families

## Phase 1 Success Condition

If the scratch implementation matches the official reference closely enough on a fixed prompt set to explain any small residual differences, phase 1 is successful.
