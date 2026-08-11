# V1 Build Plan: End-to-End Coding Agent

## The Meaty Goal

Build a usable coding agent that can take a real repository task from request to verified result inside a bounded local workspace.

In simple terms, the agent should be able to:

- understand the repo it is in
- inspect files
- search code
- make targeted edits
- run tests or validation commands
- explain what it changed
- stop safely when it lacks permission or confidence

This is the first goal that is big enough to matter, but still small enough to finish without needing distributed runtimes, cloud sandboxes, or swarm orchestration.

## What "End-to-End" Means

The agent is not done just because it can call an LLM or edit a file once.

For this V1, end-to-end means:

1. user gives a coding task
2. agent builds workspace context
3. agent chooses tools to inspect the repo
4. agent proposes or performs edits
5. agent runs validation
6. agent summarizes outcome
7. agent stores enough session state to resume or review later

If any one of those is missing, it is not a full coding agent yet.

## Recommended Product Goal

### Build a Local Single-Repo Coding Agent

Target outcome:

Given a repository and a request like:

- "fix the failing test"
- "add a CLI flag"
- "rename this symbol safely"
- "update this config handling"

the agent should complete the task with tool use, code edits, and validation in one session.

## V1 Scope

### Must Have

- repo-aware workspace summary
- file read tool
- code search tool
- file edit/write tool
- bash/command execution tool with limits
- permission gate for risky actions
- turn transcript/session log
- simple working memory summary
- validation step before final answer
- final change summary

### Nice To Have

- plan mode
- mode switching like `plan`, `edit`, `default`
- skill files
- LSP integration

### Explicitly Out of Scope For V1

- cloud runtime
- distributed agents
- remote sandbox infra
- multi-agent fan-out
- benchmark suite at full scale
- autonomous long-running background jobs

## Architecture Target

### Core Modules

- `agent_loop`
  Purpose: drives observe -> inspect -> choose -> act

- `workspace_context`
  Purpose: repo summary, branch/status, important docs, top-level layout

- `tools`
  Purpose: read, search, edit, bash, ask-for-approval

- `permissions`
  Purpose: decide allow, ask, or deny

- `memory`
  Purpose: keep short task summary plus full transcript

- `validator`
  Purpose: run tests or verification commands before final output

- `session_store`
  Purpose: persist transcript, actions, and final result

## Concrete Success Criteria

The agent should successfully handle at least these task types in a small real repo:

1. fix one failing test
2. add one small feature touching 1-3 files
3. perform a safe rename across multiple files
4. explain why a command or test is failing before editing

## Acceptance Criteria

We should consider V1 done when all of these are true:

1. The agent can inspect a repo and produce a workspace summary.
2. The agent can read and search files without hallucinating file paths.
3. The agent can propose or apply minimal edits to the right files.
4. The agent can run bounded shell commands and capture outputs safely.
5. The agent can require approval for mutating or risky actions.
6. The agent can rerun tests or validation after edits.
7. The agent can produce a final explanation of what changed and whether validation passed.
8. The agent leaves behind a session log that can be reviewed later.

## Build Phases

### Phase 1: Minimal Harness

- create agent loop
- add read/search/edit/bash tools
- add simple repo context gathering
- support one task per session

### Phase 2: Safety and Structure

- add permission gate
- restrict workspace paths
- add bounded command execution
- add structured tool schemas

### Phase 3: Continuity

- add transcript logging
- add working memory summary
- support resume/review flow

### Phase 4: Task Completion Quality

- add validation step
- tighten final reporting
- reduce noisy outputs
- improve edit precision

## Best Demo For V1

The strongest demo is not "chat with code."

The strongest demo is:

"Given a repo with one failing test, the agent finds the failure, edits the correct file, reruns the test, and explains the fix."

That demonstrates:

- repo understanding
- tool use
- editing
- validation
- safe completion

## Best Next Step After V1

Once V1 works, the next meaty extension is:

### V2 Goal

Build a coding agent with:

- permission modes
- prompt compaction
- better memory
- agent personas like `build`, `plan`, and `review`

That would move it from "usable prototype" to "real harness."

## Bottom Line

The best end-to-end meaty goal is:

Build a local repo-aware coding agent that can take a real software task from request to verified code change with safe tool use and a persistent session trail.

That is substantial enough to be worth doing and focused enough to actually finish.
