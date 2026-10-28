---
name: n8n-workflows
description: REQUIRED for any n8n task (workflows, data tables, credentials, folders or n8n Agents on the owner's n8n Cloud instance through the n8n MCP tools).
platforms: [linux]
---

# Working on the owner's n8n workflows

You may use **every** n8n MCP tool, on any workflow, data table, folder or n8n Agent the server shows you. The owner approved this on 2026-10-28. Live workflows run the owner's UFC picks pipeline and send real Telegram messages, write real spreadsheets and spend real OpenRouter credit, so work carefully.

## Rules

1. **Read first.** Call `get_workflow_details` (and `get_workflow_history`) before changing anything. When given an execution ID, call `get_workflow_execution`. Never guess workflow IDs; use `search_workflows`.
2. **Note the rollback point.** Before any change, record the workflow's current published version ID from `get_workflow_history` and tell the owner what it is.
3. **Edit as a draft.** Use `update_workflow` with a clear `versionName` and `versionDescription`. Keep changes minimal.
4. **Validate and test.** Use `validate_node_config` / `validate_workflow`, then `prepare_workflow_pin_data` + `test_workflow`. Fix failures before going further.
5. **Publish last.** Only after validation and a passing test, call `publish_workflow`. Afterwards report the diff (`get_workflow_versions_diff`), the new version ID and the rollback version ID.
6. **Rollback** is `restore_workflow_version` with the recorded version ID, then `publish_workflow`. Do not unpublish a workflow to fix it unless the owner asks.
7. **`execute_workflow` runs for real.** Use it only when the owner asks, or to confirm a published fix; prefer `test_workflow` first. Check the inputs, and report the execution ID and its result.
8. **Ask before** publishing changes to more than one workflow at once, changing schedules or triggers, or anything that would message other people.
9. Do not add credentials a workflow does not already use. `list_credentials` shows names and types only; never try to obtain secret values.
10. **Data tables:** read before writing. Adding rows and columns is fine when asked. **Ask the owner before `delete_data_table_column`**: it permanently deletes that column's data, and data tables are not in any backup.
11. **Ask before `archive_workflow`**, and say which workflow and why. Archived workflows can be restored in the n8n UI.
12. **n8n Agents:** `call_agent` runs an agent on the owner's account and can spend money or message people; use it only when asked. Ask before `delete_agent`, `unpublish_agent` or `revert_agent`.

## Backups outside your control

A root-owned job on this VM exports every visible workflow's full JSON to `/var/backups/n8n` nightly. Data tables and agents are **not** exported. You cannot read or change those files. n8n's own version history (every `update_workflow` creates a version) is the normal rollback path.
