# Frontier architecture study kickoff

Date: 2026-11-25 (America/Los_Angeles)

## Scope

This is the kickoff receipt for the persistent frontier-architecture study. The
work stays inside `topics/architecture-advances-2026/` and will extend the
existing lab rather than create a replacement implementation. Evidence will be
kept separate as published design, configuration corroboration, executable toy
proxy, exact model/runtime verification, and independent workload reproduction.

## Workspace and base

- Remote: `https://github.com/mehtama1234/sebastian-llms.git`
- Base commit: `3c9b8df089c6ae5e1edfab270c87aab6e8ebea41`
- Upstream check: `git ls-remote ... HEAD refs/heads/master` returned the same SHA.
- Local branch: `codex/frontier-architecture-study`
- Local checkout: `review-the-files-ans-the-goal/sebastian-llms`
- Initial branch state: clean at the pinned base.
- Repository instructions: no `AGENTS.md` file was present in the checkout.

## Baseline checks

| Run | Command/result | Status |
|---|---|---|
| Model summary | `python -m arch_adv_2026.cli --config .../configs/tiny-baseline.json ...` and the KV-sharing companion | `FAILED` — `code/configs/` is absent, so both stop with `FileNotFoundError`. |
| Numeric demo | `scripts/run_numeric_demo.sh` | `SETUP_BLOCKED` — the documented `code/.venv/bin/python` does not exist in this Windows checkout. |
| Config tests | `python -m pytest code/tests/test_config.py -q` | `FAILED` — all 3 tests fail because the required config files are absent. |
| Full lab tests | `python -m pytest code/tests -q` | `FAILED` — the run produced widespread failures/errors before the command timeout; config absence is a confirmed common cause. |

The config absence is a repository-baseline issue, not evidence that the
mechanisms themselves work or fail. The available commit history contains no
tracked path under `topics/architecture-advances-2026/code/configs/`, despite
the README, scripts, and tests referencing it. No weights, cloud job, external
upload, deployment, or benchmark spend was attempted.

## First milestone

1. Build a dated primary-source register and four comparable architecture cards
   for DeepSeek-V4.1-Flash, Qwen3.8-Flash-Next, Nemotron 3.5, and Inkling 2
   Mini, with unknown/proprietary fields marked explicitly.
2. Reconstruct prompt-to-token state flow and a lineage diagram before making
   any toy implementation claims.
3. Repair or replace only the minimum missing lab fixtures needed for exact,
   auditable mechanism tests; do not silently treat a toy as a frontier-model
   reproduction.

## Checkpoint 1 — completed

The JSON fixtures are intentionally ignored by the repository's `*.json`
rule, so they are local run inputs rather than publishable source artifacts.
Reconstructed fixtures now cover the tiny/micro harness and the Qwen-shaped
proxy family.

Commands and results:

- `python -m pytest code/tests/test_frontier_mechanisms.py ... test_ple.py -q`
  → `PASSED` — 36 tests.
- `python -m arch_adv_2026.cli` for tiny baseline and tiny KV sharing
  → `PASSED` — both exit 0.
- `python -m arch_adv_2026.numeric_demo` for micro baseline and micro KV sharing
  → `PASSED` — both exit 0.
- `python -m pytest code/tests/test_real_indexer_vs_attention.py -q`
  → `SETUP_BLOCKED` in the clean scoped checkout: its inherited fixture under
  the separate `llm-developments-2026` topic is absent, so the bridge cannot
  be rerun without expanding this study's file scope.
- Full `python -m pytest topics/architecture-advances-2026/code/tests -q`
  → `SETUP_BLOCKED` at the run level: 163 passed, 17 skipped, and 7 failures.
  One is the unguarded Torch training smoke (`torch` is not installed); two
  subprocess tests need an absolute package path on this Windows invocation;
  four real-indexer tests require a fixture in the separate
  `llm-developments-2026` topic. These are not treated as evidence about the
  architecture mechanisms.
- Canonical scoped rerun with an absolute topic-local package path:
  `$env:PYTHONPATH=(Resolve-Path 'topics/architecture-advances-2026/code/src').Path; python -m pytest topics/architecture-advances-2026/code/tests -q`
→ `SETUP_BLOCKED`: 169 passed, 17 skipped, 5 failures. The remaining five
  are the missing-Torch smoke and the four out-of-scope real-indexer fixtures.
- Local runtime inventory: NumPy is installed; `torch`, `transformers`, and
  `huggingface_hub` are unavailable; no local Hugging Face cache was found.
  Exact reference/frontier model execution is therefore `UNRUN`, not a failed
  quality result.

New executable proxy: `code/src/arch_adv_2026/frontier_mechanisms.py`.
It records storage bytes, cache reads, selection queries/index work, fixed
recurrent state, periodic lookup events, and shared-weight layer applications.
Generated artifact: `code/artifacts/frontier/mechanism-demo.json`.

The proxy now also includes a deterministic changing-query distractor probe:
fresh selection hits 2/2 synthetic targets, reused selection hits 1/2, while
index work falls from 24 to 12 units. This is an executable toy falsifier for
the “reuse is always safe” hypothesis, not a trained-model result.

## Checkpoint 2 — later controls and pinned source revisions

Status: `PASSED` for source/config inspection; exact runs remain `UNRUN`.

Added separately from the four starting families:

- Kimi K2, pinned to Hugging Face revision `fd1984e`, as an MLA plus large-MoE
  control.
- Gemma 3 12B, pinned to Google DeepMind Gemma commit `19e2a139` and Google
  Gemma PyTorch commit `014acb7`, as a dense GQA/local-global control.

The additions have their own source-register rows, model-card rows, lineage
edges, and prompt-to-token diagrams. They remain published-design/config
evidence, not independent performance measurements. Checkpoint commands:

```text
git ls-remote https://github.com/google-deepmind/gemma.git refs/heads/main
  -> 19e2a13999ba10b818ee128dfe33a8d50afa1684
git ls-remote https://github.com/google/gemma_pytorch.git refs/heads/main
  -> 014acb7ac4563a5f77c76d7ff98f31b568c16508
python -m pytest tests/test_frontier_mechanisms.py tests/test_long_context_plan.py tests/test_long_context_variant_plan.py -q
  -> 14 passed in 0.56s at the checkpoint-2 run
python -m compileall -q src tests
  -> PASSED
git diff --check
  -> PASSED
```

No checkpoint weights were downloaded, and no push, publish, merge, deploy,
spend, or credential change occurred.

## Checkpoint 3 — explicit state/dataflow trace

Status: `PASSED` for the documentation milestone; runtime state handoff remains
`UNRUN`.

Added [`frontier-architecture-state-trace-2026-11-25.md`](frontier-architecture-state-trace-2026-11-25.md), which traces prompt prefill, one generated token, and the next multi-turn handoff for all four starting families plus Kimi and Gemma. It labels stored, read, updated, routed, reused, serialized, and unknown state separately, and defines a future cold/prefix-reused/tool-append/recurrent-handoff workload contract.

This does not promote published prefix-cache or hybrid-state claims to local
measurements. Exact engine serialization and frontier checkpoint runs remain
`UNRUN`.

## Checkpoint 4 — proxy boundary and repeatability tests

Status: `PASSED`.

The mechanism suite now checks a one-token/zero-selection boundary, the
partial lookup-period ceiling (`ceil(17/16) == 2`), and deterministic repeated
selection output in addition to the storage, read, selection-disagreement,
recurrent-state, and shared-depth checks.

```text
python -m pytest tests/test_frontier_mechanisms.py tests/test_long_context_plan.py tests/test_long_context_variant_plan.py -q
  -> 18 passed in 0.42s
git diff --check
  -> PASSED
```

These remain accounting/proxy tests. The new causal-visibility check covers a
compressed-group boundary, not tensor-level attention quality. They do not
establish trained-model quality, device timing, or engine state serialization.

## Checkpoint 5 — Nemotron 3.5 config corroboration

Status: `PASSED` for pinned config inspection; exact model execution remains
`UNRUN`.

Read-only HF metadata/config inspection resolved the previously unknown block
schedules without downloading weights:

```text
Super revision: 5d80455a9bf1305b898a1088f8824b02ba451c93
  88 blocks = 40 mamba + 40 moe + 8 attention
  512 routed experts, 22 experts/token, 32 Q / 2 KV, 262144 configured positions
Lightning revision: 434456c9a6753f29d24e23c95d622aaf17111b3b
  52 blocks = 23 mamba + 23 moe + 6 attention
  128 routed experts, 6 experts/token, 32 Q / 2 KV, 262144 configured positions
```

The release/card's 1M-context claim is now kept separate from the base
config's 262,144-position field. Exact recurrent/cache tensors, MTP acceptance,
and the long-context extension path remain unknown.

## Checkpoint 6 — DeepSeek and Qwen config corroboration

Status: `PASSED` for pinned config inspection; exact model execution remains
`UNRUN`.

Read-only inspection of the pinned configs added these checks:

```text
DeepSeek-V4.1-Flash `397a64c`: 40 text layers; hidden 5120; 64 Q / 1 KV;
  head dim 512; 384 routed + 1 shared expert; 6 routed experts/token;
  1,048,576 positions; 128-token sliding window; index top-k 512;
  candidate top-k blocks 2048; 3 MTP layers.
Qwen3.8-Flash-Next `812d96e`: 48 layers; repeated 3 linear_attention +
  1 full_attention; linear 16 K / 48 V heads; full 24 Q / 2 KV heads;
  indexer budget 2048; 512 experts; 10 experts/token; 1 MTP layer;
  262144 positions.
```

The configs corroborate the public architecture claims while exposing useful
boundaries: Qwen's `linear_attention` naming still needs mapping to the card's
Gated DeltaNet terminology, and DeepSeek's compression-array semantics do not
by themselves reveal physical serving pages or cross-layer cache transfer.

## Checkpoint 7 — Qwen implementation semantics

Status: `PASSED` for primary implementation inspection; exact model execution
remains `UNRUN`.

The pinned Transformers implementation at
`f3b0be813bab0c3373a548106d9bce0c1a76efc7` maps Qwen's `linear_attention`
layer type to `Qwen4ExpTextGatedDeltaNet`. It explicitly stores a recurrent
matrix state shaped `[batch, value_heads, key_head_dim, value_head_dim]`,
applies a causal mask, and exposes the final state through the runtime cache.
Its QSA indexer uses a 2,048-token budget and compression ratio 4, yielding 512
selected blocks.

This resolves the terminology question at the code level, but does not prove
cross-engine serialization, physical page layout, or workload quality.

## Checkpoint 8 — DeepSeek inference-code semantics

Status: `PASSED` for released implementation inspection; exact model execution
remains `UNRUN`.

The pinned DeepSeek inference code at
`397a64c675dad82ae806e0eb88082da6a5ea4c57/inference/model.py` corroborates the
state graph: a 128-token ring window, compressed-KV buffers only on configured
KV-source layers, shared index-key ownership, causal masking of not-yet-visible
compressed positions, and a second-level candidate-block filter for later
indexers. It also exposes the implementation precision boundary: FP8 window KV
versus FP4 compressed KV.

This is code/config evidence, not a local run or proof that every production
engine uses the same allocator or page layout.

## Checkpoint 9 — compressed-group causal boundary

Status: `PASSED` for the executable toy invariant.

Added `causal_visible_compressed_positions()` to the mechanism proxy. It checks
that a ratio-2 compressed entry is invisible at position 0, becomes visible at
position 1, and never exposes more entries than the available cache. This
mirrors the visibility boundary in the released DeepSeek reference code while
remaining a small pure-Python accounting helper rather than a sparse-attention
implementation.

Focused run:

```text
python -m pytest tests/test_frontier_mechanisms.py tests/test_long_context_plan.py tests/test_long_context_variant_plan.py -q
  -> 18 passed in 0.42s
git diff --check
  -> PASSED
```

## Guardrails

No push, publish, merge, deploy, new credentials, frontier-weight download,
training run, external data upload, or budget change is authorized by this
study.
