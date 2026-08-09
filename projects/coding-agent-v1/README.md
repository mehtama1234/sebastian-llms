# Coding Agent V1

This is the implementation workspace for the first serious coding-agent build in this repo.

It follows the design in:

- `../v1-build-plan.md`
- `../v1-architecture.md`
- `../v1-task-breakdown.md`
- `../v1-demo-scenarios.md`

## Goal

Build a local repo-aware coding agent that can take a real coding task from request to verified code change with safe tool use and persistent session state.

## V1 Scope

The first implementation target is a small but complete local loop with:

- session entrypoint
- workspace context gathering
- core tool interfaces
- permission gate
- session memory
- validation and final reporting

## Package Layout

- `src/coding_agent_v1/cli.py`: CLI entrypoint
- `src/coding_agent_v1/models.py`: core dataclasses and enums
- `src/coding_agent_v1/session_store.py`: session persistence
- `src/coding_agent_v1/workspace.py`: repo/workspace summary
- `src/coding_agent_v1/tools.py`: tool definitions and interfaces
- `src/coding_agent_v1/permissions.py`: allow/ask/deny policy
- `src/coding_agent_v1/validator.py`: post-edit verification
- `src/coding_agent_v1/agent_loop.py`: main observe/inspect/choose/act/verify/report loop

## Current State

This is no longer just a scaffold. The repo now has a working local harness with tests.

What exists now:

- workspace summary and repo-root detection
- persistent session records and event logs
- real read/search/edit/command tools
- explicit and natural-language task-flow classification for inspect, fix, feature, rename, and diagnose requests with scored planner selection informed by workspace structure and test evidence
- explicit task plans that persist flow choice, feature strategy, initial actions, validation command, and planning reasons
- task-aware validation selection that can narrow feature and rename flows to matching test files from request text or module-aware workspace evidence, while preserving nested repo-relative test paths
- small feature support for explicit or inferred CLI flags, config-option defaults including inferred and natural-language option requests, and environment-variable-backed config entries including inferred and natural-language env-var requests
- workspace-bound permission decisions
- compact working-memory snapshots that persist focus, touched files, validation state, and next-step hints
- validation summaries and final reporting
- a repair loop for small failing-test cases
- proposal scoring and evidence capture for suggested fixes
- test coverage for the main harness behaviors

What still needs to be built next:

- real LLM integration
- richer approval flow UX
- broader planner quality beyond the current scored evidence-based rules
- smarter validation selection beyond the current text-and-module matching rules
- deeper long-session memory compression beyond the current compact snapshot
- larger eval task sets for repeatable quality measurement

## Current Demonstrated Behaviors

The current harness can already demonstrate:

- read repo instructions like `README.md`
- require approval for risky actions unless auto-approved
- run `pytest -q` for test-oriented tasks
- inspect failure output and search related source files
- classify explicit and natural-language requests into inspect, fix, feature, rename, and diagnose flows with scored planner selection and workspace structure/test evidence before acting
- persist an explicit task plan with a chosen validation command before acting
- narrow feature and rename validation to matching test files when request text or module structure makes the target clear, including nested repo-relative test paths
- repair simple arithmetic, literal-return, and constant-return bugs
- add a small explicit or inferred argparse CLI flag feature, explicit or inferred config option default, or explicit, inferred, or natural-language environment-variable-backed config entry
- perform safe multi-file renames using exact symbol matches
- support a diagnose-only flow that gathers failure evidence without applying edits
- review and resume saved sessions
- carry a compact working-memory snapshot across resumed sessions
- run a built-in fixed eval suite across task success, natural-language bug-intent routing, natural-language feature requests, approval gating, and resume flow
- persist eval summaries as JSON artifacts with timestamps, labels, timing, and outcome reasons
- list saved eval artifacts by date, label, and pass rate
- resolve saved eval artifacts by label for compare and history workflows
- support aliases like `latest`, `latest-pass`, and `latest:<prefix>` for eval selection
- store named baselines like `main`, `release`, or `golden` for stable eval references
- promote a resolved artifact into a named baseline in one step
- compare a named baseline against `latest-pass` or another resolved reference in one step
- auto-promote a candidate into a baseline only when comparison shows no regressions
- compare saved eval artifacts for regressions and improvements
- persist comparison and auto-promotion decisions as JSON artifacts for later audit
- summarize scenario trends across multiple eval artifacts
- rerun validation and summarize the final result

As of Sunday, August 9, 2026, the local test suite passes with:

- `123 passed`

## Immediate Next Steps

1. Add a real model-backed planner that improves on the current scored evidence-based rules.
2. Expand the session model into resumable memory plus compact working summaries.
3. Expand the eval harness into a broader benchmark set with regression checks across each task flow.
4. Improve validation command selection beyond the current text-and-module matching rules.
