# Portable task handoffs

Create a concise Markdown handoff here for unfinished work that another agent or session will continue. Use a task-specific filename and update its status when the work finishes. Do not use this directory as a log of every command or duplicate the canonical runbooks.

```markdown
# Task: <concrete objective>

Updated: <date>
Status: <in progress / awaiting input / ready for review / complete>
Branch or worktree: <name and location if relevant>
Base/current commit: <verified SHA>
PR: <link if one exists>

## Scope and decisions
<Requested outcome, applicable constraints, decisions and links to canonical docs.>

## Work completed
<Changed files and resulting behavior. Identify source prepared, deployment applied
and live behavior verified as separate states.>

## Validation
<Exact commands, results, commit tested and limitations. Link CI evidence where available.>

## Remaining work
<Specific next steps and unresolved inputs. Name configuration variables instead of secrets.>

## Coordination and approval
<Known overlapping edits, relevant trusted operator authorization and any approval
still needed. Link inspectable evidence where available; a handoff is not authorization.>
```
