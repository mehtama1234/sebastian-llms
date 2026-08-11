# Coding Agent Current Status

This file explains, in plain language, what we have been doing on the coding-agent topic in this repo.

## Short Version

We are not just collecting notes about coding agents.

We are building a portfolio around them, with one real implementation already working in:

- `projects/coding-agent-v1/`

The current direction is:

1. understand the architecture from `CodingAgents.pdf`
2. use the external Decoding AI course repo as a practical implementation reference
3. turn those ideas into a local coding-agent harness we can evolve, test, and eventually present in git

## What `CodingAgents.pdf` Is Saying

In simple words, `CodingAgents.pdf` is saying:

- a coding agent is not just a model that writes code
- the useful part is the system around the model
- that system needs repo awareness, tools, permissions, memory, and validation
- if those pieces are missing, you mostly have a coding chatbot
- if those pieces exist, you start to have an actual coding agent

So the big lesson is:

the harness matters as much as the model.

## Is It Proposing An Implementation?

Yes, but mostly at the architecture level.

It does not hand us one finished codebase to copy.

What it does give us is the implementation shape:

- inspect the repo
- gather the right context
- choose an action
- use bounded tools
- make or avoid edits
- run validation
- save memory and session state
- review results and continue if needed

That is why we needed a second source besides the PDF.

## What The External Repo Adds

The external repo:

- `sources/external/building-a-coding-agent-from-scratch-course/`

adds the practical code organization that the PDF does not spell out in detail.

It shows how a serious implementation can be split into modules such as:

- planner and runtime flow
- tool registry and tool wrappers
- permissions and approval rules
- memory and context compaction
- session logging
- sandboxing and execution control
- evals and quality checks

So the external repo is useful because it turns theory into a more concrete implementation map.

## What We Have Actually Been Implementing

The main implementation work has been inside:

- `projects/coding-agent-v1/`

This is the first working local coding-agent harness in the repo.

Its job is to prove we can do more than summarize papers.

In plain language, this harness can:

- look at a repository
- read and search files
- decide what kind of task it is handling
- make a small targeted code change when appropriate
- avoid unsafe actions unless approval rules allow them
- run tests or other validation
- save what happened so the session can be resumed or reviewed
- run fixed eval scenarios so progress is measurable

## What `coding-agent-v1` Currently Demonstrates

Right now the implementation already covers:

- inspect flow
- fix flow
- feature flow
- rename flow
- diagnose-only flow
- approval gating
- task planning with recorded reasons
- validation command selection
- session persistence and resume
- compact working-memory snapshots
- eval runs, saved artifacts, and baseline comparison

It also handles small concrete coding tasks such as:

- repairing simple failing-test cases
- adding a small CLI flag
- adding a config option default
- adding an environment-variable-backed setting
- doing a safe multi-file rename

## Verified Current State

As of Sunday, August 9, 2026, the current local test status for `projects/coding-agent-v1/` is:

- `123 passed`

That matters because it shows this is not just a draft architecture.

It is implemented code with a passing test suite.

## What This Work Teaches

At the big-picture level, this topic teaches:

- how an agent loop is structured
- why tool boundaries matter
- why permission systems are part of the product
- why memory and resumability matter for real use
- why evals are necessary if we want to improve the agent systematically

The central lesson is:

the model generates actions, but the harness determines whether those actions become reliable engineering work.

## What The End-To-End Meaty Goal Should Be

The strongest end-to-end goal for this topic is:

build a repo-aware coding agent that can take a software task from request to verified patch with bounded tools, approval rules, resumable state, and regression-aware evaluation.

That is a good flagship goal because it forces the whole system to exist, not just isolated demos.

## What Comes Next

The next serious step is not another summary note.

The next serious step is upgrading `coding-agent-v1` in three directions:

1. stronger planner quality
2. stronger memory and session continuity
3. broader eval and regression coverage

If we do that well, this repo will show a real coding-agent portfolio:

- concept understanding
- implementation understanding
- working code
- test discipline
- clear evolution from V1 to a stronger flagship agent

For how this should be presented in git, see:

- `projects/coding-agent-git-launch-plan.md`
