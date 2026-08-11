# Qwen3 Parity Workspace

This directory is the implementation workspace for the Qwen3 0.6B parity project.

## Intended Layout

- `reference/`: official-model loading and inspection utilities
- `scratch/`: from-scratch PyTorch implementation
- `scripts/`: reproducible entrypoints for loading, checking, and evaluating
- `artifacts/`: generated parity outputs and debug artifacts

## Phase 1 Objective

Reach dense-model parity against an official Qwen3 0.6B reference model on a small fixed prompt set.

## Current Executable Surface

The first runnable target is the reference-side inspection flow.

After installing dependencies, run:

```bash
./scripts/run_reference_inspect.sh
```

This writes a reference snapshot JSON artifact under `artifacts/reference/` containing the official model's config and tokenizer metadata for the pinned model identifier.

The default script currently uses the lightweight `--config-only` path so the repo can validate official config assumptions before downloading full model weights.

The scratch-side config baseline is also runnable:

```bash
./scripts/run_scratch_config_snapshot.sh
```

This writes the local source-of-truth config artifact under `artifacts/scratch/` so later parity checks can compare scratch assumptions against the official reference snapshot.

Once both artifacts exist, compare them with:

```bash
./scripts/compare_config_snapshots.sh
```

This is the first parity gate before weight loading or generation tests.

You can also emit the expected official-to-scratch weight mapping:

```bash
./scripts/run_weight_mapping_snapshot.sh
```

This writes a JSON inventory of expected tensor-name correspondences under `artifacts/mapping/`.

You can also emit the expected loaded-key manifest:

```bash
./scripts/run_weight_manifest.sh
```

This records the exact official keys and scratch keys the future loader is expected to consume and populate.

For a small runtime proof of the scratch architecture without allocating the full 0.6B model, run:

```bash
./scripts/run_tiny_smoke.sh
```

This uses a tiny config derived from the Qwen3 shape conventions and checks:

- scratch model construction
- weight-map generation
- partial loader assignment
- a forward pass

For a first real-official-weight probe without downloading the full checkpoint, run:

```bash
./scripts/run_real_subset_probe.sh
```

This range-fetches a small set of official layer-0 norm tensors from the live Qwen3 safetensors file and verifies exact copied values inside a partial scratch receiver.

For a first bounded forward-parity gate against the official Transformers implementation, run:

```bash
./scripts/run_layer0_forward_parity.sh
```

This range-fetches the full modeled layer-0 tensor slice, loads it into both the scratch decoder layer and the official `Qwen3DecoderLayer`, and checks for exact output parity on the same causal input.

For a stronger end-to-end bounded parity gate, run:

```bash
./scripts/run_prefix_logits_parity.sh --layers 1
```

This builds a shallow prefix model from real official weights, loads the same slice into both the scratch `Qwen3ScratchModel` and the official `Qwen3ForCausalLM`, and compares full logits on the same prompt.

You can widen the bounded slice as parity holds:

```bash
./scripts/run_prefix_logits_parity.sh --layers 2
./scripts/run_prefix_logits_parity.sh --layers 4
./scripts/run_prefix_logits_parity.sh --layers 8
```

The prefix probe caches fetched official tensor slices under `artifacts/parity/` so repeated runs at the same depth can skip the remote range-fetch path. Use `--refresh-cache` when you want to rebuild a cached slice from the live checkpoint.

For the full Phase 1 gate against a small fixed prompt set, run:

```bash
./scripts/run_full_prompt_set_parity.sh
```

This reuses the cached full 28-layer official slice, tokenizes a fixed set of five prompts, compares scratch and official logits prompt-by-prompt, and writes a JSON artifact under `artifacts/parity/`.
