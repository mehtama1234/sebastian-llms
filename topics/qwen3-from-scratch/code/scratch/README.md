# Scratch Side

This subdirectory is for the educational PyTorch reimplementation of the Qwen3 0.6B dense architecture.

Current assets:

- `qwen3_parity.scratch.config`
- `qwen3_parity.scratch.config_snapshot`
- `qwen3_parity.scratch.layers`
- `qwen3_parity.scratch.model`

The first step on the scratch side is to make the local model assumptions explicit and serializable before implementing layers and weight mapping.

The repo now also contains a first dense-model skeleton:

- RMSNorm
- RoPE cache construction and application
- grouped-query attention
- feed-forward block
- decoder layer
- top-level model shell

This is still an educational skeleton, not a verified weight-compatible implementation yet.

The next explicit contract is the weight map:

- official Hugging Face parameter names
- corresponding scratch-model parameter names

That mapping lives in `qwen3_parity.weight_map` and is the bridge to a future tensor-loading utility.

That future tensor-loading utility is now scaffolded in `qwen3_parity.load_weights`.
It still needs a real runtime with model weights available, but the assignment and shape-checking contract is defined.

There is also now a tiny-runtime smoke path via `qwen3_parity.smoke`, which exercises:

- tiny config construction
- scratch model initialization
- partial official-to-scratch load assignment
- synthetic forward pass
