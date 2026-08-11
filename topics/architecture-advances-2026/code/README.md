# Architecture Advances 2026 Workspace

This directory is the implementation workspace for the long-context architecture lab described in:

- `../../docs/architecture-advances-2026/README.md`
- `../../projects/architecture-advances-2026/README.md`

## Purpose

This is the `Phase 0` harness for architecture experiments.

It is intentionally small and controlled:

- one baseline decoder-only model spec
- one config system for toggling architecture ideas
- one summary/eval surface for estimating parameter count and KV-cache cost
- one per-layer graph describing KV ownership and reuse
- one tiny NumPy execution path for runtime sanity checks
- one place to add progressively more real implementations

Current concept coverage:

- `baseline`
- `kv_sharing`
- `attention_budgeting`
- `per_layer_embeddings`
- `compressed_attention`
- `history_compression` (recent full window plus compressed older-history prototype)
- `mhc` (simplified DeepSeek-style multi-stream residual mixing prototype)

Reference model coverage:

- `Qwen/Qwen3-0.6B` config inspection
- `Qwen/Qwen3-0.6B` prompt-generation smoke path

## Intended Layout

- `configs/`: baseline and variant configs
- `src/arch_adv_2026/`: package code
- `scripts/`: reproducible entrypoints
- `artifacts/`: generated summaries and experiment outputs

## Current Executable Surface

The first runnable target is a config-driven architecture summary.

Set up the local environment first:

```bash
./scripts/setup_venv.sh
```

Run:

```bash
./scripts/run_model_summary.sh
```

This writes JSON summaries under `artifacts/summaries/` for:

- a baseline decoder-only model
- a KV-sharing variant

The script uses `PYTHONPATH=src` directly, so it works without requiring a global editable install.

## Numeric Demo Surface

After creating the local venv and installing dependencies, run:

```bash
./scripts/run_numeric_demo.sh
```

This executes tiny random-weight forward passes for:

- `configs/micro-baseline.json`
- `configs/micro-kv-sharing.json`

The point is not model quality. The point is to validate:

- graph-to-runtime wiring
- KV reuse behavior
- layer-by-layer cache ownership
- a future path toward a real Torch implementation

## Torch Demo Surface

If Torch is installed in the local venv, run:

```bash
./scripts/run_torch_demo.sh
```

This executes the same micro baseline and KV-sharing configs through a tiny random-weight Torch model that respects the same per-layer KV-owner graph.

The Torch proxy now also covers:

- compressed attention head-dimension changes
- `history_compression` cache shortening on older context
- `mhc` residual-mixing blocks

## Qwen Reference Surface

The workspace now also has a real Hugging Face reference path for `Qwen/Qwen3-0.6B`.

Install the extra runtime once:

```bash
./scripts/setup_venv.sh
```

Inspect the reference config/tokenizer metadata without loading the full weights:

```bash
./scripts/run_qwen_reference_inspect.sh
```

This writes a reference snapshot to `artifacts/reference/qwen3_0_6b_reference_snapshot.json`.

Run one real prompt-generation smoke test:

```bash
./scripts/run_qwen_reference_generate.sh
```

This writes a generation artifact to `artifacts/reference/qwen3_0_6b_generation.json`.

Run a small multi-prompt reference eval:

```bash
./scripts/run_qwen_reference_eval.sh
```

This uses the prompt cases in `../../evals/architecture-advances-2026/qwen-reference-prompts.jsonl` and writes `artifacts/reference/qwen3_0_6b_eval.json`.

## Synthetic Long-Context Surface

Generate synthetic passkey/needle retrieval cases:

```bash
./scripts/generate_long_context_cases.sh
```

This writes `artifacts/long_context/synthetic_cases.jsonl`.

Run the real-model long-context retrieval eval:

```bash
./scripts/run_long_context_eval.sh
```

This writes `artifacts/long_context/qwen3_long_context_eval.json`.

Run a context-length sweep with timing:

```bash
./scripts/run_long_context_sweep.sh
```

This writes `artifacts/long_context/qwen3_long_context_sweep.json` with per-case results plus aggregate buckets by filler length.
The default script now runs multiple sweep seeds so each length bucket reports aggregated behavior rather than a single draw.

Run a same-cases variant proxy comparison across the Qwen-shaped config family:

```bash
./scripts/run_long_context_variant_compare.sh
```

This writes `artifacts/long_context/qwen3_variant_proxy_compare.json`. Unlike the real Hugging Face sweep, this is a proxy comparison surface: it holds the synthetic retrieval cases fixed and scores each architecture config with a deterministic architecture-aware proxy so you can compare likely quality-vs-memory directionality across variants before retraining work exists.

Render a compact markdown decision layer over that artifact:

```bash
./scripts/run_long_context_variant_report.sh
```

This writes `artifacts/long_context/qwen3_variant_proxy_compare.md` and summarizes:

- the highest-quality variant at the longest context
- the lowest-KV variant at the longest context
- the best memory-aware tradeoff that still clears a strong proxy-quality bar

Build a machine-readable selector over the same artifact:

```bash
./scripts/run_long_context_variant_selector.sh
```

This writes `artifacts/long_context/qwen3_variant_proxy_selector.json` with longest-context recommendations for:

- `quality`
- `memory`
- `quality_preserving_memory`
- `balanced`

Generate the final proxy decision memo:

```bash
./scripts/run_long_context_variant_memo.sh
```

This writes:

- `artifacts/long_context/qwen3_variant_proxy_memo.md`
- `artifacts/long_context/qwen3_variant_proxy_memo.json`

The memo turns the selector into an explicit carry-forward recommendation for the next heavier experiment tier.

Render one per-concept scorecard across systems, proxy long-context, training, and final decision surfaces:

```bash
./scripts/run_concept_scorecard.sh
```

This writes:

- `artifacts/reports/architecture-concept-scorecard.md`
- `artifacts/reports/architecture-concept-scorecard.json`

The scorecard is the compact workstream matrix: one row per architecture concept, with the current carry-forward decision plus the supporting systems, long-context, and training signals beside it.

Audit the current memo labels against explicit decision rules:

```bash
./scripts/run_concept_decision_audit.sh
```

This writes:

- `artifacts/reports/architecture-concept-decision-audit.md`
- `artifacts/reports/architecture-concept-decision-audit.json`

The audit does not replace the memo. It checks whether the current `default` / `secondary` / `exploratory` / `drop` labels are actually consistent with the current scorecard thresholds, and flags any mismatches.

Turn the scorecard and audit into a concrete next-experiment queue:

```bash
./scripts/run_concept_review_plan.sh
```

This writes:

- `artifacts/reports/architecture-concept-review-plan.md`
- `artifacts/reports/architecture-concept-review-plan.json`

The review plan is the action layer. It prioritizes variants with unresolved decision mismatches or weak evidence and spells out what to run next to resolve them.
It now separates:

- raw audit mismatches
- mismatches already resolved by focused follow-up evidence
- active unresolved mismatches that still need review

It can also merge multiple focused follow-up surfaces for the same variant, including cases where training and long-context follow-ups disagree.

Refresh the whole layered decision stack in one shot:

```bash
./scripts/run_decision_stack.sh
```

This rewrites, in dependency order:

- `artifacts/reports/micro-variant-report.json`
- `artifacts/reports/micro-benchmark-matrix.{json,md}`
- `artifacts/reports/architecture-concept-scorecard.{json,md}`
- `artifacts/reports/architecture-concept-decision-audit.{json,md}`
- `artifacts/reports/architecture-concept-review-plan.{json,md}`
- `artifacts/reports/final-architecture-memo.{json,md}`

Use this when follow-up evidence changes and you want the scorecard, audit, review queue, and final memo to agree again without manually rerunning each layer.
The runner now refreshes the systems-side micro report and benchmark matrix first, then rebuilds the decision artifacts on top of those refreshed inputs.
It now finishes by validating that the audit, review plan, and final memo agree on raw, resolved, and unresolved mismatch state.

Run that consistency check directly with:

```bash
bash ./scripts/run_decision_stack_validate.sh
```

Build a small systems benchmark matrix instead of relying on one fixed micro setting:

```bash
./scripts/run_benchmark_matrix.sh
```

This writes:

- `artifacts/reports/micro-benchmark-matrix.json`
- `artifacts/reports/micro-benchmark-matrix.md`

The matrix sweeps the current micro benchmark across multiple batch sizes and sequence lengths, then summarizes which variants stay fastest on average, which hold up best in the worst cell, and which keep the lowest KV cache footprint across the grid.
The canonical runner uses a slightly heavier setting here on purpose: warmup `1`, measured runs `3`, report runs `3`. That is still fast enough to refresh locally, but much less noisy than the earlier one-shot timing sweep.

Run the first focused follow-up experiment from that queue:

```bash
./scripts/run_attention_budgeting_training_followup.sh
```

This writes:

- `artifacts/reports/attention-budgeting-training-followup.json`

It reruns the training matrix for `attention_budgeting` only, over a wider schedule/seed grid than the default matrix, so the current `drop` vs `secondary` raw mismatch can be judged with stronger training evidence.

Turn that focused artifact into a decision call:

```bash
./scripts/run_attention_budgeting_training_assessment.sh
```

This writes:

- `artifacts/reports/attention-budgeting-training-assessment.json`
- `artifacts/reports/attention-budgeting-training-assessment.md`

The assessment answers one narrow question: does the focused `attention_budgeting` training follow-up support keeping the current `drop` label, or does it support upgrading the variant toward `secondary`? If it supports the current label, the audit can still show a raw threshold mismatch while also marking that mismatch resolved by follow-up.

Run the next focused training follow-up for the current `secondary` keep candidate:

```bash
./scripts/run_kv_sharing_training_followup.sh
./scripts/run_kv_sharing_training_assessment.sh
```

These write:

- `artifacts/reports/kv-sharing-training-followup.json`
- `artifacts/reports/kv-sharing-training-assessment.json`
- `artifacts/reports/kv-sharing-training-assessment.md`

This pair answers the matching narrow question for `kv_sharing`: does the focused training evidence still support keeping the current `secondary` label, or is a more conservative label warranted?

Run the matching focused long-context check for the same variant:

```bash
./scripts/run_kv_sharing_long_context_assessment.sh
```

This writes:

- `artifacts/reports/kv-sharing-long-context-assessment.json`
- `artifacts/reports/kv-sharing-long-context-assessment.md`

This surface asks the complementary narrow question for `kv_sharing`: does the focused long-context proxy evidence support keeping the current label, or does it justify a stronger long-context keep? When the training and long-context follow-ups disagree, the review plan holds the current label, marks the variant high-priority, and records the conflict explicitly instead of pretending the disagreement is already resolved.

Run the full promotion pass for the current default carry-forward candidate:

```bash
./scripts/run_compressed_attention_promotion_pass.sh
```

This refreshes:

- the selected long-context proxy execution artifact
- the broader `compressed_attention` training follow-up
- the focused short-context stress and speed-tail training artifacts
- the wider systems benchmark matrix
- the promotion assessment itself
- the remediation plan and its targeted execution results

It writes:

- `artifacts/reports/compressed-attention-training-followup.json`
- `artifacts/reports/compressed-attention-training-diagnosis.json`
- `artifacts/reports/compressed-attention-training-diagnosis.md`
- `artifacts/reports/compressed-attention-training-stress-followup.json`
- `artifacts/reports/compressed-attention-training-stress-assessment.json`
- `artifacts/reports/compressed-attention-training-stress-assessment.md`
- `artifacts/reports/compressed-attention-speed-tail-assessment.json`
- `artifacts/reports/compressed-attention-speed-tail-assessment.md`
- `artifacts/reports/compressed-attention-promotion-benchmark-matrix.json`
- `artifacts/reports/compressed-attention-promotion-benchmark-matrix.md`
- `artifacts/reports/compressed-attention-promotion-assessment.json`
- `artifacts/reports/compressed-attention-promotion-assessment.md`
- `artifacts/reports/compressed-attention-promotion-memo.json`
- `artifacts/reports/compressed-attention-promotion-memo.md`
- `artifacts/reports/compressed-attention-remediation-plan.json`
- `artifacts/reports/compressed-attention-remediation-plan.md`
- `artifacts/reports/compressed-attention-remediation-execution.json`
- `artifacts/reports/compressed-attention-remediation-execution.md`

It also validates that those artifacts agree with the refreshed long-context execution artifact:

- `./scripts/run_compressed_attention_promotion_validate.sh`

Use the underlying subcommands only when you want to rerun a single surface in isolation:

```bash
./scripts/run_compressed_attention_training_followup.sh
./scripts/run_compressed_attention_training_diagnosis.sh
./scripts/run_compressed_attention_training_stress_followup.sh
./scripts/run_compressed_attention_training_stress_assessment.sh
./scripts/run_compressed_attention_speed_tail_assessment.sh
./scripts/run_compressed_attention_promotion_benchmark_matrix.sh
./scripts/run_compressed_attention_promotion_assessment.sh
./scripts/run_compressed_attention_promotion_validate.sh
./scripts/run_compressed_attention_promotion_memo.sh
./scripts/run_compressed_attention_remediation_plan.sh
```

To stress the diagnosed weak training slices for `compressed_attention`, run:

```bash
./scripts/run_compressed_attention_training_stress_followup.sh
./scripts/run_compressed_attention_training_stress_assessment.sh
```

These write:

- `artifacts/reports/compressed-attention-training-stress-followup.json`
- `artifacts/reports/compressed-attention-training-stress-assessment.json`
- `artifacts/reports/compressed-attention-training-stress-assessment.md`
- `artifacts/reports/compressed-attention-speed-tail-assessment.json`
- `artifacts/reports/compressed-attention-speed-tail-assessment.md`

This focused lane answers the next narrower question after the diagnosis: do the short-context, small-batch training failures reproduce when we stress the bad slices with more seeds and repeated runs, or do they collapse under rerun?

To isolate the short-context speed tail inside that stress grid, run:

```bash
./scripts/run_compressed_attention_speed_tail_assessment.sh
```

To turn the current blocker state into one concrete next-experiment queue, run:

```bash
./scripts/run_compressed_attention_remediation_plan.sh
```

To execute the targeted slices from that remediation plan, run:

```bash
./scripts/run_compressed_attention_remediation_execute.sh
```

This flow answers the next-stage question for `compressed_attention`: does the current winner have enough long-context, training, and systems evidence to justify promotion into the next heavier experiment stage, or should it remain the default carry-forward candidate while promotion stays deferred?

Resolve that selector into one concrete focused follow-up plan:

```bash
./scripts/run_long_context_variant_plan.sh
./scripts/run_long_context_variant_plan.sh --objective quality
./scripts/run_long_context_variant_plan.sh --execution-mode summary_only
```

This writes a mode-specific plan artifact:

- `focused_proxy_compare` → `artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-plan.json`
- `summary_only` → `artifacts/plans/qwen3-quality_preserving_memory-summary_only-variant-proxy-plan.json`

The variant-proxy run plan resolves:

- the selected proxy recommendation to one concrete config path
- the matching baseline config
- the source selector and compare artifacts
- the focused compare schedule needed to rerun only baseline vs selected

Execute that focused plan:

```bash
./scripts/run_long_context_variant_execute.sh
./scripts/run_long_context_variant_execute.sh --objective quality
./scripts/run_long_context_variant_execute.sh --execution-mode summary_only
```

This writes the matching execution artifact:

- `focused_proxy_compare` → `artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-execution.json`
- `summary_only` → `artifacts/plans/qwen3-quality_preserving_memory-summary_only-variant-proxy-execution.json`

The execution artifact materializes:

- the selected summary artifact
- the matching baseline summary artifact
- a direct KV-cache and parameter delta between them
- a focused baseline-vs-selected proxy long-context compare artifact when `focused_proxy_compare` is enabled

Supported execution modes:

- `focused_proxy_compare`: rerun the proxy long-context compare using only baseline plus the selected variant
- `summary_only`: materialize only the selected and baseline summaries

Render a compact markdown report from a sweep artifact:

```bash
./scripts/run_long_context_report.sh
```

This writes `artifacts/long_context/qwen3_long_context_sweep_agg_smoke.md`.

Project architecture variant KV-costs onto a real sweep artifact:

```bash
./scripts/run_long_context_projection.sh
./scripts/run_long_context_projection_report.sh
```

These write:

- `artifacts/long_context/qwen3_long_context_medium_qwen_projection.json`
- `artifacts/long_context/qwen3_long_context_medium_qwen_projection.md`

The projection scripts now use a Qwen-shaped config family rather than the tiny micro configs, so the KV and compute ratios are closer to the real model geometry.

Render one combined comparison view:

```bash
./scripts/run_long_context_compare.sh
```

This writes:

- `artifacts/long_context/qwen3_long_context_medium_compare.md`
- `artifacts/long_context/qwen3_long_context_medium_selector.json`

The markdown report is for human review. The selector artifact is the machine-readable recommendation surface for downstream automation. It records the pass-rate threshold, whether fallback was needed, and the current best `memory`, `speed`, and `balanced` choices.

Resolve the selector into one concrete next-run plan:

```bash
./scripts/run_long_context_plan.sh
./scripts/run_long_context_plan.sh --benchmark-mode torch_proxy
./scripts/run_long_context_plan.sh --benchmark-mode summary_only
./scripts/run_long_context_plan.sh --objective speed --benchmark-mode torch_proxy
```

This writes a mode-specific plan artifact:

- `proxy_numeric` → `artifacts/plans/qwen3-balanced-run-plan.json`
- `torch_proxy` → `artifacts/plans/qwen3-balanced-torch_proxy-run-plan.json`
- `summary_only` → `artifacts/plans/qwen3-balanced-summary_only-run-plan.json`

The run-plan artifact resolves the selected recommendation to:

- a concrete config path
- the matching baseline config
- the chosen optimization objective
- an explicit benchmark mode
- executable next-step commands that already exist in this workspace

Execute that plan at the config-summary level:

```bash
./scripts/run_long_context_execute.sh
./scripts/run_long_context_execute.sh --benchmark-mode torch_proxy
./scripts/run_long_context_execute.sh --benchmark-mode summary_only
./scripts/run_long_context_execute.sh --objective speed --benchmark-mode torch_proxy
```

This writes the matching mode-specific execution artifact:

- `proxy_numeric` → `artifacts/plans/qwen3-balanced-execution.json`
- `torch_proxy` → `artifacts/plans/qwen3-balanced-torch_proxy-execution.json`
- `summary_only` → `artifacts/plans/qwen3-balanced-summary_only-execution.json`

The execution artifact materializes:

- the selected summary artifact
- the matching baseline summary artifact
- a direct KV-cache and parameter delta between them
- a local numeric benchmark artifact comparing a small proxy version of the selected config against its proxy baseline

Supported benchmark modes:

- `proxy_numeric`: run the micro NumPy proxy benchmark
- `torch_proxy`: run the micro Torch proxy benchmark when Torch is available
- `summary_only`: skip the benchmark and materialize only summaries/deltas

The current default benchmark mode is `proxy_numeric`.

Run both steps in one command:

```bash
./scripts/run_long_context_mode.sh
./scripts/run_long_context_mode.sh --objective speed --benchmark-mode torch_proxy
```

This wrapper simply runs the plan script and then the execute script with the same `objective` and `benchmark_mode`.

Materialize a full matrix across multiple objectives and benchmark modes:

```bash
./scripts/run_long_context_matrix.sh
./scripts/run_long_context_matrix.sh --objective memory --objective balanced --benchmark-mode proxy_numeric --benchmark-mode summary_only
```

This writes `artifacts/plans/qwen3-matrix.json` plus the corresponding per-pair plan and execution artifacts. The matrix is the current workflow surface for turning one selector artifact into a small ablation table you can inspect or hand to later automation.

## Numeric Benchmark Surface

To measure the same tiny runs repeatedly and compare baseline vs KV-sharing, run:

```bash
./scripts/run_numeric_benchmark.sh
```

This writes a comparison artifact under `artifacts/benchmarks/` with:

- per-run timings
- mean/median/min/max timing
- owner-cache count deltas
- embedded demo context for both configs

To compare the micro baseline against the attention-budgeting variant, run:

```bash
./scripts/run_attention_budgeting_benchmark.sh
```

To compare the micro baseline against the PLE variant, run:

```bash
./scripts/run_ple_benchmark.sh
```

To compare the micro baseline against the compressed-attention variant, run:

```bash
./scripts/run_compressed_attention_benchmark.sh
```

To compare the micro baseline against the compressed-attention variant on a tiny Torch training-stability task, run:

```bash
./scripts/run_training_stability_benchmark.sh
```

This writes `artifacts/benchmarks/micro-baseline-vs-compressed_attention-training.json` with:

- per-step training loss
- gradient norms before and after clipping
- per-step elapsed time
- non-finite step checks
- baseline-vs-variant training deltas under the same synthetic batch schedule

To generate a training-stability report across the current micro variants, run:

```bash
./scripts/run_training_report.sh
```

This writes `artifacts/reports/micro-training-report.json` and aggregates:

- final-loss delta vs baseline
- training-speed ratio vs baseline
- gradient-stability deltas
- finite/non-finite checks across the current variant set

To expand that into a small training matrix across multiple schedules and seeds, run:

```bash
./scripts/run_training_matrix.sh
```

This writes `artifacts/reports/micro-training-matrix.json` with:

- batch-size, schedule, and seed coverage for each row
- per-schedule / per-seed training reports
- fastest / lowest-loss / lowest-grad-delta winners per row
- per-variant trend rows aggregated across the matrix

To compare the micro baseline against the compressed-history variant, run:

```bash
./scripts/run_history_compression_benchmark.sh
```

The first DeepSeek-inspired prototype is now the simplified `mHC` residual-mixing path. To compare the micro baseline against it, run:

```bash
python -m arch_adv_2026.benchmark_cli \
  --baseline-config ./configs/micro-baseline.json \
  --variant-config ./configs/micro-mhc.json \
  --artifact ./artifacts/benchmarks/micro-baseline-vs-mhc.json
```

To generate one consolidated report across all current micro variants, run:

```bash
./scripts/run_variant_report.sh
```

To generate a markdown decision memo from that consolidated report, run:

```bash
./scripts/run_variant_memo.sh
```

To generate the final cross-surface architecture decision memo, run:

```bash
./scripts/run_final_architecture_memo.sh
```

This writes:

- `artifacts/reports/final-architecture-memo.md`
- `artifacts/reports/final-architecture-memo.json`

The final memo combines:

- the micro runtime / KV tradeoff report
- the systems benchmark matrix
- the long-context proxy selector and focused execution artifact
- the tiny Torch training-stability benchmark
- the focused review-plan state, including:
  - raw audit mismatches
  - mismatches resolved by focused follow-up
  - active unresolved mismatches that still need review

Its job is to say which architecture change is the default carry-forward candidate, which ones stay secondary or exploratory, and which ones do not currently deserve heavier work.
It should also make any still-open review disagreement visible at the top layer rather than hiding it inside the lower-level audit artifacts.
The standalone runner now delegates to the full `run_decision_stack.sh` refresh path so there is only one authoritative rebuild flow for the memo, scorecard, audit, and review-plan artifacts. That avoids drift from separately rerunning stochastic upstream benchmarks in two different shell entrypoints.

If you call the lower-level CLI directly instead of the shell runner, you can also ask it to validate the generated memo against the current audit/review artifacts:

```bash
PYTHONPATH=src ./.venv/bin/python -m arch_adv_2026.final_memo_cli \
  --micro-report artifacts/reports/micro-variant-report.json \
  --benchmark-matrix artifacts/reports/micro-benchmark-matrix.json \
  --long-context-selector artifacts/long_context/qwen3_variant_proxy_selector.json \
  --long-context-execution artifacts/plans/qwen3-quality_preserving_memory-variant-proxy-execution.json \
  --training-benchmark artifacts/reports/micro-training-matrix.json \
  --review-plan artifacts/reports/architecture-concept-review-plan.json \
  --validate-audit artifacts/reports/architecture-concept-decision-audit.json \
  --artifact-json artifacts/reports/final-architecture-memo.json \
  --artifact-md artifacts/reports/final-architecture-memo.md \
  --stdout
```

Use that mode when you want the direct CLI entrypoint but still want the same consistency checks the shell runners apply.

## Current Test Surface

The harness now has lightweight tests for:

- config loading
- KV-owner selection
- per-layer graph construction
- KV-cache savings estimates
- tiny numeric execution
- tiny numeric benchmarking
- tiny torch execution when torch is installed

Run:

```bash
PYTHONPATH=src pytest tests
```

## Phase 0 Objective

Create a small, ownable baseline harness before doing heavier model surgery.

That means:

1. configs are explicit
2. architecture variants are codified
3. memory tradeoffs are measurable
4. future torch implementations have a stable config contract
