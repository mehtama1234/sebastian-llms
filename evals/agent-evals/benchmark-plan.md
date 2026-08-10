# Agent Evals Benchmark Plan

## Benchmark families

### 1. Tool-call stage checks

Goal:

grade one tool call without mixing together unrelated failure causes.

Core measurements:

- tool-selection accuracy
- schema-valid argument rate
- semantically correct argument rate
- execution success rate
- output-handling consistency rate

### 2. Multi-step trace checks

Goal:

find the first state where a failing run actually went wrong.

Core measurements:

- first-failure state counts
- loop frequency
- premature-stop frequency
- recovery-after-error frequency

### 3. End-to-end agent tasks

Goal:

score whether the user goal was achieved safely.

Core measurements:

- task completion rate
- unsafe action rate
- escalation correctness
- write-action grounding rate

### 4. Runtime check quality

Goal:

measure whether cheap checks catch bad actions without blocking too much good work.

Core measurements:

- true risk caught
- false escalation rate
- false allow rate
- time and token overhead

## First scenario families to build

1. read-only lookup tasks
2. write-tool tasks with confirmation requirements
3. multi-tool sequencing tasks
4. conversation continuity tasks
5. document-backed extraction and verification tasks

## Measurement rule

No agent change should be judged on final success rate alone.

Every serious comparison should report:

- stage-level breakdown
- end-to-end success
- safety outcome
- dominant failure modes
