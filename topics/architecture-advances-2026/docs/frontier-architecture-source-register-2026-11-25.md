# Frontier architecture source register

Verified 2026-11-25. This is an initial register, not a complete literature
review. Vendor/model-card claims remain distinct from local measurements.

## Starting case studies

| Family | Primary source | Source-verified facts | Still unknown or requiring a controlled check |
|---|---|---|---|
| DeepSeek-V4.1-Flash | [Technical report](https://arxiv.org/abs/2609.19969), [pinned card/config at `397a64c`](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/397a64c675dad82ae806e0eb88082da6a5ea4c57/README.md), [pinned config](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/397a64c675dad82ae806e0eb88082da6a5ea4c57/config.json), especially §§2 and 3 | Multimodal MoE; 40-layer CED (20-layer causal encoder + 20-layer decoder); config has 40 text layers, hidden size 5,120, 64 attention heads, 1 KV head, head dimension 512, 384 routed + 1 shared expert, 6 routed experts/token, 1,048,576 max positions, 128-token sliding window, eight index heads, index top-k 512, candidate top-k blocks 2,048, and three MTP layers. Report/card document CSA2 Full/Reindex/Reuse, FP4 global KV, 890 bytes/token global KV, and SWA bounded replay. | The 890-byte number is global HBM KV, not total deployment memory. Config field semantics for the cross-layer compression arrays and the serving page layout, actual reuse boundaries under load, selection/reindex work, and independent latency are unverified here. |
| Qwen3.8-Flash-Next | [Pinned model card/config at `812d96e`](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/tree/812d96e10a0dd82b69d749e68693698cf6c36daa), [raw README](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/raw/812d96e10a0dd82b69d749e68693698cf6c36daa/README.md), [pinned config](https://huggingface.co/Qwen/Qwen3.8-Flash-Next/blob/812d96e10a0dd82b69d749e68693698cf6c36daa/config.json) | Config identifies `Qwen4ExpForConditionalGeneration` / `qwen4_exp`; 48 layers; layer types repeat three `linear_attention` blocks then one `full_attention`; linear state uses 16 key and 48 value heads; full attention uses 24 Q / 2 KV heads; indexer budget 2,048, 512 experts with 10 experts/token, one MTP layer, 262,144 max positions, vocabulary 248,320. README documents 125B total/6B activated plus separate n-gram and MTP parameters and extension to 1M. | “Activated” excludes separately listed n-gram/MTP parameters and is not residency. Exact mapping from `linear_attention` to the card's Gated DeltaNet wording, state ownership, index cost, and runtime support remain to be checked; selection budget is not context length. |
| Nemotron 3.5 Super / Lightning | [NVIDIA release page](https://research.nvidia.com/labs/nemotron/Nemotron-3.5-Super-and-Lightning/), [pinned Super config `5d80455`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Super-VL-120B-A12B-Base-BF16/blob/5d80455a9bf1305b898a1088f8824b02ba451c93/config.json), [pinned Lightning config `434456c`](https://huggingface.co/nvidia/NVIDIA-Nemotron-3.5-Lightning-30B-A3B-Base-BF16/blob/434456c9a6753f29d24e23c95d622aaf17111b3b/config.json) | Super config: 88 LLM blocks (40 Mamba, 40 MoE, 8 attention), 512 routed experts, 22 experts/token, 32 Q / 2 KV heads, 262,144 configured positions, one MTP attention+MoE block pair. Lightning config: 52 blocks (23 Mamba, 23 MoE, 6 attention), 128 routed experts, 6 experts/token, 32 Q / 2 KV heads, one MTP pair, 262,144 configured positions. Super is multimodal; Lightning is text-only. Release/card claims extend context to 1M. | Exact recurrent/attention cache tensor layout, routing traffic, MTP acceptance distribution, and whether the 1M extension is identical to the base config. Published throughput is NVIDIA’s evaluated setup, not an independent local result. |
| Inkling 2 Mini | [Model card](https://thinkingmachines.ai/model-card/inkling-2-mini/), [release article](https://thinkingmachines.ai/news/inkling-2-mini/) | 24-layer looped decoder-only MoE; middle 12 layers run three times, giving 48 applications/token; 26.4B total, 3.4B active and 5.4B effective active after looping; hybrid local/global attention; NVFP4/MXFP8 deployment; model card reports 1M context. | Looping is shared-weight depth, not visible reasoning tokens and not a claim that KV/activation state is halved. Runtime support, per-pass state behavior, and fixed-compute/fixed-time comparisons remain to be tested. |

## Historical mechanism controls

### DeepSeek implementation corroboration

[DeepSeek's pinned inference implementation](https://huggingface.co/deepseek-ai/DeepSeek-V4.1-Flash/blob/397a64c675dad82ae806e0eb88082da6a5ea4c57/inference/model.py)
is stronger than a diagram-only claim. Its `Attention` class allocates a
128-token window cache; only configured KV-source layers create compressed KV,
while intervening layers read the shared cache. The `Indexer` stores shared
index keys, masks positions that are not yet causally visible, and returns
sorted top-k indices. The implementation writes compressed KV in FP4, writes
window KV in FP8, and distinguishes index-source layers from KV-source layers.
Its candidate-block routine is a second-level filter before later Reindex
layers score candidates.

This is released inference code and config corroboration, not an exact run in
our environment; the code's deployment defaults and production page allocator
are not automatically the same as a serving engine's behavior.

### Qwen implementation corroboration

[Hugging Face Transformers implementation at pinned commit `f3b0be8`](https://github.com/huggingface/transformers/blob/f3b0be813bab0c3373a548106d9bce0c1a76efc7/src/transformers/models/qwen4_exp/modeling_qwen4_exp.py)
maps `linear_attention` to `Qwen4ExpTextGatedDeltaNet`. Its recurrent state is
shaped `[batch, value_heads, key_head_dim, value_head_dim]` and is read from
and written to the runtime cache. The implementation applies a causal mask and
can return the final recurrent state. The QSA indexer uses a 2,048-token budget
with compression ratio 4, yielding 512 selected blocks.

This establishes implementation semantics, not a local checkpoint run.

| Mechanism | Original source | What the source establishes | Adoption/connection to verify separately |
|---|---|---|---|
| GQA | [Ainslie et al., 2023](https://arxiv.org/abs/2305.13245) | GQA uses an intermediate number of KV heads between MHA and MQA; the paper reports quality close to MHA with speed comparable to MQA and proposes uptraining from MHA checkpoints. | Later model configs can corroborate head counts, but shared heads do not prove lineage or identical training. |
| MLA | [DeepSeek-V2, §2](https://arxiv.org/abs/2405.04434) | MLA compresses KV cache into a latent vector; the report separately describes sparse MoE activation and KV-cache reduction. | DeepSeek-V4.1-Flash uses a different CSA2/cross-layer cache path; do not equate MLA with CSA2. |
| Gated DeltaNet | [Yang et al., 2024/2025](https://arxiv.org/abs/2412.06464) | Gating supports rapid memory erasure while the delta rule supports targeted updates; hybrid architectures combine Gated DeltaNet with attention/Mamba-like layers. | Qwen's adoption is config/model-card evidence; it does not mean every Qwen layer has explicit token retrieval. |
| Attention Residuals | [Kimi Team, 2026](https://arxiv.org/abs/2603.15031) | AttnRes replaces fixed residual accumulation with content-dependent attention over earlier layer outputs; Block AttnRes reduces the memory/communication burden. | Inkling's release says it uses attention residuals; exact implementation and loop interaction need model-specific inspection. |

## Later verified additions

| Family/control | Primary source or exact code | Source-verified facts | Still unknown or requiring a controlled check |
|---|---|---|---|
| Kimi K2 | [Moonshot model card at `fd1984e`](https://huggingface.co/moonshotai/Kimi-K2-Instruct/tree/fd1984e2b7a3350dbf7305fe73a4ede25c14de50) | 1T total / 32B activated MoE; 61 layers with one dense layer; MLA; 64 attention heads; 384 experts with 8 selected plus 1 shared; 128K context; block-FP8 checkpoint; recommended vLLM/SGLang/KTransformers/TensorRT-LLM engines. | Resident weight footprint, expert skew/all-to-all traffic, exact page layout, and independent engine measurements. |
| Gemma 3 12B dense control | [Google DeepMind architecture code at `19e2a139`](https://github.com/google-deepmind/gemma/blob/19e2a13999ba10b818ee128dfe33a8d50afa1684/gemma/gm/nn/_gemma.py), [Google PyTorch config at `014acb7`](https://github.com/google/gemma_pytorch/blob/014acb7ac4563a5f77c76d7ff98f31b568c16508/gemma/config.py) | Dense 48-layer text backbone; hidden size 3,840; 16 Q / 8 KV heads; head dimension 256; five local sliding layers followed by one global layer; 1,024 local window; 262,144 vocabulary; 131,072-position configuration. | Exact checkpoint revision, runtime memory/page layout, and text-only quality/latency in this workspace. |

## Later verified additions

| Family/control | Primary source or exact code | Source-verified facts | Still unknown or requiring a controlled check |
|---|---|---|---|
| Kimi K2 | [Moonshot model card](https://huggingface.co/moonshotai/Kimi-K2-Instruct) | 1T total / 32B activated MoE; 61 layers with one dense layer; MLA; 64 attention heads; 384 experts with 8 selected plus 1 shared; 128K context; block-FP8 checkpoint; recommended vLLM/SGLang/KTransformers/TensorRT-LLM engines. | Resident weight footprint, expert skew/all-to-all traffic, exact page layout, and independent engine measurements. |
| Gemma 3 12B dense control | [Google DeepMind architecture code](https://github.com/google-deepmind/gemma/blob/main/gemma/gm/nn/_gemma.py), [Google PyTorch config](https://github.com/google/gemma_pytorch/blob/main/gemma/config.py) | Dense 48-layer text backbone; hidden size 3,840; 16 Q / 8 KV heads; head dimension 256; five local sliding layers followed by one global layer; 1,024 local window; 262,144 vocabulary; 131,072-position configuration. | Exact checkpoint revision, runtime memory/page layout, and text-only quality/latency in this workspace. |

## Evidence ladder

1. Published design or release claim.
2. Pinned model card/config corroboration.
3. Executable local proxy with explicit approximation boundaries.
4. Exact checkpoint/runtime verification.
5. Independent workload reproduction.

The current entries are at levels 1–2. No exact frontier model run has been
attempted and no vendor benchmark is being treated as an independent result.

## Immediate research probes

- DeepSeek: compare full-cache production, fresh reindex, and reused selection;
  keep global HBM KV, local SWA state, index work, and persistent replay bytes
  as separate counters.
- Qwen: model recurrent DeltaNet state separately from QSA explicit lookup;
  measure the 512-block/2048-token selector as index budget, not context size.
- Nemotron: log draft acceptance by position and distinguish Mamba checkpoint
  state from attention KV and expert-routing traffic.
- Inkling: compare one pass vs three shared-weight passes at fixed parameters,
  fixed compute, and fixed wall time; count layer applications explicitly.
