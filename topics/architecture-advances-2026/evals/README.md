# Architecture Advances 2026 Evals

Evaluation scaffolding for prototypes derived from `LLMArchitectureAdvances2026.pdf`.

This topic is primarily about efficiency-quality tradeoffs under long contexts, so the evals must measure both:

- systems wins
- modeling loss

## Primary questions

1. How much memory is saved?
2. How much latency or FLOP reduction is achieved?
3. How does quality degrade as context grows?
4. Which concepts are worth the added architectural complexity?

## Eval categories

- `systems`
  - KV-cache bytes
  - prefill latency
  - decode latency
  - peak memory
- `model quality`
  - perplexity
  - synthetic long-context retrieval
  - passkey/needle-style tests
  - small downstream task probes
- `stability`
  - training divergence
  - optimization sensitivity
  - performance variance by seed

## Current runnable artifacts

- `qwen-reference-prompts.jsonl`
  - small real-model prompt cases for `Qwen/Qwen3-0.6B`
  - intended to catch prompt echo, repeated instruction leakage, and gross response-shape failures before heavier benchmark work
- `../code/architecture-advances-2026/artifacts/long_context/synthetic_cases.jsonl`
  - synthetic passkey and needle retrieval cases generated inside the code workspace
  - intended to check whether the reference model is actually using distant context, not just following short prompts
- `../code/architecture-advances-2026/artifacts/long_context/qwen3_long_context_sweep.json`
  - context-length sweep artifact with pass rate and timing grouped by filler length
  - intended to show how retrieval quality and runtime change together as prompt length grows

## Rule

No concept should be considered "better" based on one benchmark number alone.
Every prototype must report:

- quality at short context
- quality at long context
- memory cost
- latency cost
- implementation complexity notes
