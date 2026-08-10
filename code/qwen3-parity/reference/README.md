# Reference Side

This subdirectory is for scripts and helpers that load the official Qwen3 0.6B dense model and expose a stable comparison surface for parity tests.

Current entrypoint:

- `qwen3_parity.reference.inspect`

Current model target:

- `Qwen/Qwen3-0.6B`

The first artifact produced from this side should be a stable config-and-parameter snapshot that later parity checks can compare against the scratch implementation.
