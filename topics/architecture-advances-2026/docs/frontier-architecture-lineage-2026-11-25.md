# Frontier architecture lineage — evidence-labeled

Date: 2026-11-25. An arrow is only a documented lineage claim when the source
explicitly attributes the mechanism. Shared names or similar diagrams are
marked as similarity/inference, not ancestry.

```mermaid
flowchart LR
  GQA[GQA paper 2023\noriginal mechanism] -->|mechanism source| GQAC[Later GQA configs\nconfig corroboration]
  MLA[DeepSeek-V2 2024\nMLA latent KV] -->|same organization, documented evolution must be checked| DV4[DeepSeek-V4 family]
  GD[Gated DeltaNet paper\n2024/2025] -->|model card names mechanism| QW[Qwen3.8-Flash-Next]
  AR[Attention Residuals paper\n2026] -->|release explicitly says used| IK[Inkling 2 Mini]
  DV4 -.similar goal: selective/compressed history\nnot proof of direct lineage.-> QW
  QW -.hybrid recurrent + explicit lookup\nnot equivalent to DeepSeek CSA2.-> NE[Nemotron 3.5]
  MLA -->|documented adoption in model card| KK[Kimi K2]
  GQA -->|config corroboration| GM[Gemma 3]
  GM -.dense local/global control, not lineage claim.-> QW
  MLA -->|documented adoption in model card| KK[Kimi K2]
  GQA -->|config corroboration| GM[Gemma 3]
  GM -.dense local/global control, not lineage claim.-> QW
```

## Documented connections

- GQA is the original source for grouped KV heads; a later model using GQA is
  an adoption/config fact only when its config or report confirms the head
  layout.
- DeepSeek-V2 documents MLA. DeepSeek-V4.1-Flash documents CSA2 and cross-layer
  reuse. The study treats these as a historical mechanism path, not as a claim
  that CSA2 is MLA.
- Gated DeltaNet's original paper describes the gated delta rule and hybrid
  architectures. Qwen3.8-Flash-Next's model card explicitly names Gated
  DeltaNet in its 48-layer layout.
- Attention Residuals is the original paper. Inkling's release article
  explicitly states that its looped design uses attention residuals.

## Similarity or inference only

- Selective memory appears in DeepSeek CSA2, Qwen QSA, and Nemotron hybrid
  state, but similar workload motivation does not establish influence.
- “Active parameters” is a reporting convention shared by MoE releases; it is
  not a common definition of resident memory, routing traffic, or latency.
- A model with recurrent state can still include explicit lookup layers; fixed
  state and token-addressable history are different state paths.
- Kimi K2's MLA and Gemma 3's GQA/local-global schedule are comparison
  controls, not evidence of direct influence on the four starting families.
- Kimi K2's MLA and Gemma 3's GQA/local-global schedule are comparison
  controls, not evidence of direct influence on the four starting families.
