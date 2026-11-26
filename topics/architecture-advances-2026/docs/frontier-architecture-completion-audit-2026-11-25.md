# Frontier architecture goal — completion audit

Audit date: 2026-11-25  
Branch: `codex/frontier-architecture-study`  
Base: `3c9b8df089c6ae5e1edfab270c87aab6e8ebea41`  
Scope: `topics/architecture-advances-2026` only

This audit distinguishes completed evidence from work that is intentionally
unrun or setup-blocked. It does not turn a source inspection or toy proxy into
a frontier-model benchmark.

## Requirement coverage

| Requirement | Evidence | Status | Boundary |
|---|---|---|---|
| Four starting model families | [Source register](frontier-architecture-source-register-2026-11-25.md), [model cards](frontier-architecture-model-cards-2026-11-25.md) | `PASSED` | Public report/card/config evidence; not matched performance |
| Historical controls | GQA, MLA, Gated DeltaNet, Attention Residuals rows in source register and [lineage](frontier-architecture-lineage-2026-11-25.md) | `PASSED` | Attribution is separated from mechanism similarity |
| Later verified additions | [Later additions](frontier-architecture-later-additions-2026-11-25.md) covers Kimi K2 and Gemma 3 12B | `PASSED` | Separate controls; no leaderboard claim |
| Prompt → one-token → multi-turn trace | [State trace](frontier-architecture-state-trace-2026-11-25.md) | `PASSED` | Runtime serialization is `UNKNOWN` unless code/source shows it |
| Cache ownership and GQA/shared KV | `frontier_mechanisms.py`, focused tests, [proxy report](frontier-mechanism-proxy-2026-11-25.md) | `PASSED` | Arithmetic proxy; no device measurement |
| Fresh versus reused selection | Distractor probe: fresh 2/2 targets, reused 1/2; same stored bytes, lower index work | `PASSED` | Synthetic scores; not trained retrieval quality |
| Recurrent state plus periodic lookup | Fixed-state and lookup-event accounting plus state-trace explanation | `PASSED` | No learned state or task quality |
| Shared-weight depth | 24 stored / 48 applications per token toy and Inkling card comparison | `PASSED` | No fixed-compute quality or wall-time result |
| Tests and boundary checks | `18 passed` focused run; deterministic, zero-selection, lookup-ceiling, ownership, selection-disagreement, and causal compressed-group checks | `PASSED` | Full suite is not fully green for setup reasons below |
| Existing lab commands | Tiny summaries and NumPy demos recorded in [kickoff](frontier-architecture-kickoff-2026-11-25.md) | `PASSED` | Torch/HF paths remain unavailable |
| Full topic regression | Absolute-PYTHONPATH run: `169 passed, 17 skipped, 5 failed` | `SETUP_BLOCKED` | 1 missing Torch smoke; 4 inherited fixture failures outside this topic |
| Exact frontier checkpoint execution | No Torch/Transformers/HF runtime and no local approved weights | `UNRUN` | No weights downloaded or dependencies installed |
| Independent workload reproduction | No matched hardware/engine/task run | `UNRUN` | Vendor results are not relabeled as independent evidence |
| Scope and guardrails | `git status`, `git diff --check`, and kickoff guardrails | `PASSED` | No push, publish, merge, deploy, spend, credentials, or weight download |

## Evidence ladder

```text
Published design/report       PASSED for all named families and controls
Pinned config/code             PASSED for DeepSeek, Qwen, Nemotron, Kimi, Gemma
Executable toy proxy          PASSED; 18 focused tests
Exact model/runtime run       UNRUN; local runtime/weights unavailable
Independent workload evidence UNRUN; no matched engine/hardware run
```

## Commands supporting the audit

```text
$env:PYTHONPATH=(Resolve-Path 'topics/architecture-advances-2026/code/src').Path
python -m pytest topics/architecture-advances-2026/code/tests -q
  -> SETUP_BLOCKED: 169 passed, 17 skipped, 5 failed

python -m pytest topics/architecture-advances-2026/code/tests/test_frontier_mechanisms.py topics/architecture-advances-2026/code/tests/test_long_context_plan.py topics/architecture-advances-2026/code/tests/test_long_context_variant_plan.py -q
  -> PASSED: 18 passed in 0.42s

git diff --check
  -> PASSED
```

## Honest conclusion

The requested source-verified architecture study and scoped executable
mechanism lab are complete at the evidence levels available in this
workspace. The goal must not be interpreted as a claim of frontier throughput,
quality, energy, or production state serialization. The next experiment that
could change the decision memo is a fixed-distractor, multi-turn run on an
approved local checkpoint and engine, comparing cold replay, prefix reuse,
fresh selection, reused selection, and recurrent-state handoff with equal
precision and hardware.
