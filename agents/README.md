# Working in this repository with any coding agent

Assume multiple coding agents, humans and sessions will contribute. A fresh agent with a checkout must be able to discover the intended architecture, actual progress, safety boundaries and next useful action without access to earlier conversations.

## Read in this order

1. Root `AGENTS.md`: shared operating rules, including local-only dependencies and approval boundaries. Tools that do not discover this file automatically should be directed to read it explicitly.
2. [Shared project context](context.md): prepared versus verified state, current evidence and unresolved inputs.
3. [Repository overview](../README.md), [architecture](../docs/architecture.md), [security](../docs/security.md) and the relevant service runbook.
4. The current Git branch, working tree, open PR and any task handoff relevant to the requested change.

## Maintain portable context

Keep durable knowledge in plain Markdown and configuration under version control. Link to canonical documents instead of copying the same policy into several agent instruction files. When a tool needs a provider-specific adapter, keep it small and point it back to these files. A model or account change must not require reconstructing the project from a chat transcript.

Record decisions with their reason, status (confirmed, proposed or superseded) and the relevant PR or source. Record exact validation commands and results, including what was not tested. Keep secrets and real site inventory in their documented ignored locations or secret store; refer to variable names rather than values in handoffs.

Use repository-relative paths and portable command examples in repository documents. Explain the required OS, local dependency location and tool version when they affect execution. Provide equivalent standard CLI instructions when an agent-specific interface is used to carry out repository work.

## Coordinate without losing work

Inspect branch and working-tree state before editing or switching branches. Check whether another agent is already working on the same files. Use separate branches or worktrees for concurrent changes, keep PRs focused and coordinate overlapping edits. Do not force-push, reset, delete or overwrite unfamiliar changes to obtain a clean workspace.

When pausing or handing off unfinished work, use the [handoff template](handoffs/README.md). The handoff identifies the task and evidence; it does not grant new permissions. Honor explicit approval already available in trusted user context and record any approval still needed for the next action.

Use root `AGENTS.md` for the project's standing PR merge authorization. A fresh agent should complete review, validation and merging within that authorization instead of waiting for another approval solely because it changed agents or sessions. Deployment authorization remains separate.
