# V1 Task Breakdown

Derived from: `projects/v1-build-plan.md`

## Objective

Build a local repo-aware coding agent that can take a real coding task from request to verified code change with safe tool use and persistent session state.

## Milestone 1: Skeleton and Session Flow

### Goal

Create the minimal end-to-end control loop.

### Tasks

1. Define the session entrypoint.
2. Define the per-turn agent loop shape: observe -> inspect -> choose -> act -> verify -> report.
3. Create a basic request/response session object.
4. Define where session logs will be stored.
5. Add a simple CLI or terminal entrypoint for one-task sessions.

### Exit Criteria

- A user can start a session and submit one coding request.
- The system records the session start, request, and final result.

## Milestone 2: Workspace Context

### Goal

Make the agent aware of the repository it is working in.

### Tasks

1. Detect repo root.
2. Capture branch and git status when available.
3. Collect top-level file and folder layout.
4. Discover relevant repo instructions such as `README.md`, `AGENTS.md`, or config files.
5. Build a compact workspace summary object.

### Exit Criteria

- The agent can produce a stable workspace summary before acting.
- The summary is small enough to reuse across turns.

## Milestone 3: Core Tools

### Goal

Give the agent the minimum tools needed to complete coding tasks.

### Tasks

1. Add file read support.
2. Add file search support.
3. Add file edit/write support.
4. Add bounded shell command execution.
5. Standardize tool input/output contracts.

### Exit Criteria

- The agent can inspect files, search code, edit files, and run validation commands.
- Tool outputs are structured enough to feed back into the loop.

## Milestone 4: Permissions and Safety

### Goal

Prevent unsafe or uncontrolled actions.

### Tasks

1. Add workspace path boundaries.
2. Define tool categories such as read-only, file-edit, and command execution.
3. Add allow/ask/deny permission outcomes.
4. Require approval for risky actions.
5. Bound command runtime and output size.

### Exit Criteria

- The agent cannot modify files outside the workspace.
- Risky actions can be blocked or require approval.

## Milestone 5: Editing Quality

### Goal

Make edits targeted and minimally destructive.

### Tasks

1. Prefer patch-style edits over blind overwrites.
2. Add exact-match or anchored edit behavior.
3. Capture edit failures cleanly.
4. Record changed files and edit intent in the session log.

### Exit Criteria

- The agent can make small, precise edits.
- Failed edits return actionable feedback instead of silently corrupting files.

## Milestone 6: Validation

### Goal

Make the agent verify its work before claiming success.

### Tasks

1. Detect likely validation commands from repo context.
2. Run targeted tests or checks after edits.
3. Capture validation outputs in bounded form.
4. Distinguish success, failure, and incomplete verification.

### Exit Criteria

- The agent does not claim a fix without attempting validation when validation is available.
- Final output states whether verification passed.

## Milestone 7: Session Memory

### Goal

Preserve enough state to support continuity and review.

### Tasks

1. Store full transcript events.
2. Maintain a smaller working summary for the current task.
3. Record inspected files, changed files, commands run, and validation outcome.
4. Make sessions reviewable after completion.

### Exit Criteria

- A session log can be reopened and understood without replaying everything manually.
- The working summary stays smaller than the raw transcript.

## Milestone 8: Final Reporting

### Goal

Produce a clear final answer with evidence.

### Tasks

1. Summarize what was inspected.
2. Summarize what changed.
3. Summarize what validation ran.
4. State remaining uncertainty explicitly if verification failed or was unavailable.

### Exit Criteria

- The agent’s final output reads like an engineering handoff, not vague chat output.

## First Demo Tasks

Use these as the initial proving ground:

1. Fix one failing unit test.
2. Add one small CLI flag.
3. Rename one symbol across 2-3 files.
4. Diagnose a failing command before making edits.

## Recommended Build Order

1. Skeleton and session flow
2. Workspace context
3. Core tools
4. Permissions and safety
5. Editing quality
6. Validation
7. Session memory
8. Final reporting

## Bottom Line

The main lesson of this breakdown is that a coding agent should be built as a harness, not as a single prompt wrapped around an LLM.
