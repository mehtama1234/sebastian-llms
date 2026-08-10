# Qwen3 0.6B Parity Plan

## Scope

Target model:

- Qwen3 0.6B dense

Project mode:

- educational from-scratch rebuild
- official reference integration
- bounded parity evaluation

## Workstreams

### 1. Architecture Spec Extraction

Outputs:

- cleaned architecture summary
- config field list
- component dependency graph

Key questions:

- exact dense-model config fields
- attention layout and grouped-query settings
- RoPE and RMSNorm details
- weight naming expectations

### 2. Reference Model Integration

Outputs:

- reference load script
- model metadata snapshot
- prompt runner for the official model

Key questions:

- which exact upstream package and model identifier to pin
- tokenizer behavior
- generation defaults that must be frozen for parity runs

### 3. Scratch Implementation

Outputs:

- config object
- RMSNorm
- RoPE utilities
- grouped-query attention
- feed-forward module
- transformer block
- full dense model class
- KV cache support
- generation loop

### 4. Weight Mapping

Outputs:

- documented tensor map
- load-time validation
- failure report for mismatches

### 5. Evaluation

Outputs:

- smoke prompts
- parity checks
- artifact format for results
- regression notes

### 6. Documentation

Outputs:

- implementation guide
- lessons learned
- known gaps and next-step plan

## Milestones

1. Capture the architecture spec from the PDF.
2. Load the official Qwen3 0.6B model and freeze a reference configuration.
3. Implement the scratch dense architecture.
4. Load official weights into the scratch model.
5. Run parity checks on fixed prompts.
6. Document mismatches, tradeoffs, and next steps.
