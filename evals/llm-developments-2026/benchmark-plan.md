# LLM Developments 2026 Benchmark Plan

## Retrieval benchmark

Compare:

- lexical search
- vector search
- hybrid search

Measure:

- task success
- retrieval latency
- prompt-token expansion
- number of retrieved files or snippets
- total run cost proxy

## Tool-result delivery benchmark

Compare:

- inline result injection
- file-pointer delivery

Measure:

- follow-up tool calls
- prompt-token expansion
- completion rate
- error recovery rate

## Repo-context benchmark

Compare:

- no context file
- root context file
- hierarchical context files

Measure:

- task success
- tokens consumed before first edit
- unnecessary file reads
- validation overrun

## Test-time scaling benchmark

Compare:

- single-attempt baseline
- multi-attempt planning
- multi-attempt planning plus verifier
- shared-evidence branch planning

Measure:

- success rate
- bad-edit rate
- ungrounded-claim rate
- runtime inflation

## Long-horizon CLI benchmark

Task families:

- inspect and summarize
- diagnose without edit
- bug fix
- feature edit
- safe rename
- interrupted task resume

Measure:

- completed tasks
- destructive or unsafe actions
- retries per task
- validation pass rate
- artifact completeness

## Long-context systems benchmark

Compare:

- baseline cache policy
- heuristic eviction
- lookahead-style eviction proxy
- compressed-history memory
- local-window plus compressed-history

Measure:

- memory use
- throughput proxy
- retrieval fidelity
- long-context task quality
