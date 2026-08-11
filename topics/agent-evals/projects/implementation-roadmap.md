# Agent Evals Implementation Roadmap

## Phase 0: Canonical framing

Deliverables:

- docs topic folder
- project brief
- eval folder with rubric and benchmark plan

Question answered:

what exactly are we trying to evaluate, and how is the space divided?

## Phase 1: Trace schema

Deliverables:

- JSON trace schema for multi-step runs
- required fields for tool choice, arguments, execution result, and final action
- sample traces for success and failure

Question answered:

what must every run log so failures are debuggable later?

## Phase 2: Gold scenarios

Deliverables:

- synthetic scenario packs for:
  - read-only tool tasks
  - write-tool tasks
  - multi-step planning tasks
  - conversation continuity tasks
- expected outcomes and failure labels

Question answered:

what fixed tasks will we use to compare one agent build against another?

## Phase 3: Stage evaluators

Deliverables:

- tool-selection grader
- argument-validation grader
- execution-status checker
- output-handling grader

Question answered:

which stage is failing most often?

## Phase 4: Runtime checks

Deliverables:

- cheap pre-action checks
- escalation policy for risky actions
- grounding requirements for write tools

Question answered:

what can the system verify before it is allowed to do harm?

## Phase 5: First integration target

Deliverable:

- connect the trace and evaluation layer to `projects/coding-agent-v1/`

Question answered:

can one real agent in this repo use the whole evaluation stack?
