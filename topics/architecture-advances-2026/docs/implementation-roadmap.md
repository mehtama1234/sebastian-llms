# Implementation Roadmap

Goal: turn the paper into a sequence of prototypeable concepts instead of a pile of architecture trivia.

## Order of work

### 1. KV-sharing baseline

Why first:

- smallest architectural delta
- easiest to reason about
- directly tied to long-context memory savings

Deliverables:

- baseline transformer
- cross-layer KV-sharing variant
- memory and latency instrumentation

### 2. Attention budgeting

Why second:

- also relatively simple
- layer-wise systems tradeoff is easy to isolate

Deliverables:

- hybrid local/global attention baseline
- per-layer query-head budget config
- per-layer cost accounting

### 3. Per-layer embeddings

Why third:

- different kind of efficiency lever
- mostly orthogonal to KV/cache work

Deliverables:

- PLE residual path
- compute-versus-parameter comparison runs

### 4. Compressed attention prototypes

Why fourth:

- more complex
- worth doing only after simpler levers are instrumented

Deliverables:

- latent compression baseline
- compressed-space attention variant
- optional convolutional mixing variant

### 5. DeepSeek-style advanced prototypes

Why last:

- highest implementation complexity
- strongest risk of confusion without earlier baselines

Deliverables:

- small mHC experiment
- compressed-history memory experiment
- explicit "not full reproduction" note

## Shared engineering requirements

Every prototype should include:

- config-driven toggles
- parameter count reporting
- KV-cache size reporting
- context-length scaling tests
- latency and memory profiling
- at least one quality metric against a baseline

## Non-goals

- replicating vendor-scale training recipes
- reproducing published benchmark tables
- mixing all ideas at once before isolated ablations exist
