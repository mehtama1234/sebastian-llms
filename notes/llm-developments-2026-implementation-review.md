# LLM Developments 2026 Implementation Review

Source:

- `../LLMDevelopments.pdf`

## Purpose

This note treats `LLMDevelopments.pdf` as an implementation triage document, not a general reading summary.

The question is:

which papers from this list should turn into production-scale experiments, writeups, or code in this repo?

## Working rule

Only promote papers that help us build one of these four things:

- better agent harnesses
- better coding-agent workflows
- better long-context and retrieval systems
- better test-time reasoning control and evaluation

Papers that mainly require frontier-scale model training are lower priority for this repo unless they unlock a cheap reduced prototype.

## Highest-priority implementation lanes

### 1. Agent harness and retrieval systems

#### Implement now

`Is Grep All You Need? How Agent Harnesses Reshape Agentic Search`

- Why it matters:
  lexical search versus vector search is a direct production decision for repo agents and long-session memory systems.
- What to build:
  a retrieval adapter that supports lexical, vector, and hybrid search plus inline-result and file-pointer delivery.
- Cheapest experiment:
  replay a fixed benchmark over long repo sessions and compare cost, latency, tokens inserted, and task success.

`Natural-Language Agent Harnesses`

- Why it matters:
  the harness itself can become a product surface instead of a pile of ad hoc wrappers.
- What to build:
  an explicit harness schema for tools, memory, context assembly, and execution policy that can be serialized and compared between runs.

`Meta-Harness: End-to-End Optimization of Model Harnesses`

- Why it matters:
  model quality is increasingly constrained by harness quality.
- What to build:
  a harness configuration space plus an evaluator that can sweep retrieval mode, tool-result formatting, planning depth, validation policy, and retry policy.

`Agentic Harness Engineering: Observability-Driven Automatic Evolution of Coding-Agent Harnesses`

- Why it matters:
  it points toward a closed-loop harness improvement system instead of manual tuning.
- What to build:
  failure clustering over traces, then automated harness-rule proposals.

#### Prototype later

`AI for Auto-Research: Roadmap & User Guide`

- Useful for deeper research-agent workflow design, but secondary until the core harness is measurable.

`A Methodology for Selecting and Composing Runtime Architecture Patterns for Production LLM Agents`

- Useful as a decision framework after we have multiple harness variants worth comparing.

### 2. Coding-agent workflow design

#### Implement now

`Evaluating AGENTS.md: Are Repository-Level Context Files Helpful for Coding Agents?`

- Why it matters:
  directly relevant to this repo and to any future path changes or repo reorganization.
- What to build:
  hierarchical repo guidance files with targeted loading rules instead of one giant root instruction file.

`LongCLI-Bench: A Preliminary Benchmark and Study for Long-Horizon Agentic Programming in Command-Line Interfaces`

- Why it matters:
  terminal agents are the most relevant practical surface for this repo.
- What to build:
  a local long-horizon CLI scenario pack with multi-step repair, rename, refactor, and diagnose-only tasks.

`AutoHarness: Improving LLM Agents by Automatically Synthesizing a Code Harness`

- Why it matters:
  suggests systematic harness construction instead of hand-assembled prompts.
- What to build:
  task-specific harness presets chosen by task class.

`Coding Agents Are Effective Long-Context Processors`

- Why it matters:
  supports treating repo agents as long-context retrieval-and-compression systems, not just code generators.
- What to build:
  context-budget accounting and context-compaction policies.

`Effective Strategies for Asynchronous Software Engineering Agents`

- Why it matters:
  long-running tasks need resumability, queueing, and artifact-based handoff.
- What to build:
  a background-job model for tasks that do not need a live conversational loop.

#### Prototype later

`Code as Agent Harness`

- Useful if we choose to formalize harness assembly as code-first config, but not the first bottleneck.

### 3. Reasoning and test-time control

#### Implement now

`Test-Time Scaling Makes Overtraining Compute-Optimal`

- Why it matters:
  it forces us to measure training versus inference tradeoffs instead of assuming one-shot generation is ideal.
- What to build:
  a test-time scaling harness with multiple candidate attempts, verifier scoring, selection policy, and stop-on-confidence policy.

`Learning to Self-Verify Makes Language Models Better Reasoners`

- Why it matters:
  verification loops are one of the cheapest ways to improve task reliability without retraining.
- What to build:
  a verifier stage for answer consistency, tool-result grounding, test-result grounding, and patch-risk checks.

`PaCoRe: Learning to Scale Test-Time Compute with Parallel Coordinated Reasoning`

- Why it matters:
  parallel attempts matter for hard tasks where one trajectory is brittle.
- What to build:
  a coordinator that compares multiple candidate plans or patches before execution.

`Share More, Search Less: Collaborative Parallel Thinking for Efficient Test-Time Scaling`

- Why it matters:
  it suggests information sharing across parallel attempts instead of redundant exploration.
- What to build:
  shared scratchpad state across candidate planning branches.

#### Prototype later

`Does Your Reasoning Model Implicitly Know When to Stop Thinking?`

- Useful after basic verifier and candidate-selection loops already exist.

`Single-Agent LLMs Outperform Multi-Agent Systems on Multi-Hop Reasoning Under Equal Thinking Token Budgets`

- Useful as a guardrail against premature multi-agent complexity.

### 4. Long-context and inference systems

#### Implement now

`LookaheadKV: Fast and Accurate KV Cache Eviction by Glimpsing into the Future without Generation`

- Why it matters:
  cache policy becomes important once agent sessions and long documents grow.
- What to build:
  a reduced cache-eviction simulator over long traces.

`IndexCache: Accelerating Sparse Attention via Cross-Layer Index Reuse`

- Why it matters:
  it suggests a systems-oriented way to lower sparse-attention overhead.
- What to build:
  a toy sparse-retrieval or sparse-attention index-reuse prototype in the architecture sandbox.

`FlashAttention-4`

- Why it matters:
  this is mainly a systems benchmark and deployment dependency question.
- What to build:
  a compatibility and benchmark memo for the serving stack we actually use, not a fresh kernel implementation.

`DeepSeek-V4`

- Why it matters:
  compressed history plus local detail is a strong template for long-context systems.
- What to build:
  reduced prototypes for compressed-history memory and local-raw-window retrieval in the architecture lane.

#### Prototype later

`Long Context Pre-Training with Lighthouse Attention`

- Interesting, but more training-heavy than the immediate harness lanes.

`TriAttention`

- Candidate for later long-context compression work once simpler compressed-history ideas are measured first.

## Lower-priority sections from this PDF

These are useful reading but should not dominate implementation time right now:

- general architecture and model-design papers
- diffusion language models
- most RLVR papers
- broad benchmark papers that do not translate into a new measurement surface for this repo

## Immediate implementation stack

If we only pick the most practical experiments from this PDF, the first stack should be:

1. lexical versus vector versus hybrid retrieval for agent harnesses
2. inline tool-output injection versus file-pointer delivery
3. hierarchical repo context files versus no context files
4. test-time scaling with verifier-backed candidate selection
5. long-horizon CLI benchmark tasks
6. long-context cache and compression simulations

## Recommended repo outputs

This paper list should produce the following repo work:

- one canonical writeup lane for `LLMDevelopments.pdf`
- one project roadmap for production-scale experiments
- one eval plan covering retrieval, context pressure, verifier loops, and long-horizon tasks
- one first implementation target wired into `projects/coding-agent-v1/`
- one second implementation target wired into `code/architecture-advances-2026/`

## Decision summary

### Build now

- `Is Grep All You Need?`
- `Natural-Language Agent Harnesses`
- `Meta-Harness`
- `Agentic Harness Engineering`
- `Evaluating AGENTS.md`
- `LongCLI-Bench`
- `AutoHarness`
- `Coding Agents Are Effective Long-Context Processors`
- `Effective Strategies for Asynchronous Software Engineering Agents`
- `Test-Time Scaling Makes Overtraining Compute-Optimal`
- `Learning to Self-Verify`
- `PaCoRe`
- `Share More, Search Less`
- `LookaheadKV`
- `IndexCache`
- `FlashAttention-4` as a benchmark-and-adoption memo, not a kernel project
- `DeepSeek-V4` as reduced long-context prototypes

### Build later

- `AI for Auto-Research`
- runtime architecture pattern methodology paper
- stop-thinking control papers
- Lighthouse Attention
- TriAttention

### Do not prioritize for this repo right now

- diffusion LM implementation work
- frontier-scale RLVR training work
- generic model-architecture papers without a cheap prototype path
