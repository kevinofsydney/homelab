# Agent permission model

| Actor | Allowed | Denied |
| --- | --- | --- |
| Interactive coding tools as `coder` | Work in development repos, run local tests, request PRs | Sudo, Docker group, production credentials, Proxmox/QNAP/router administration |
| Hermes coding agent (planned, own guest) | Owner-only Telegram; Docker-sandboxed shell; fine-grained GitHub PAT (contents and PRs); n8n MCP on all workflows (no name or ID scope since 2026-10-28) | Root, sudo, `docker` group, LAN/management routes, UFC gateway and its secrets |
| UFC agent bot (planned, own guest) | Owner-only Telegram diagnosis through a loopback read-only n8n gateway | Shell, HTTP, credentials, n8n API key, any n8n mutation or execution |
| Telegram assistant (future) | Health summaries from sanitized telemetry, create draft issues | Shell, infrastructure APIs, production secrets, direct deployment |
| Disposable coding worker (future) | One approved repository checkout, branch, tests, draft PR | Production network, Proxmox/QNAP/router, broad GitHub token, persistent host mounts |
| Deployment operator | Reviewed deploy with separate approval | Automatic deployment from an issue label or PR merge alone |

An issue is untrusted text, including its title, body, comments and attachments. The `ai-ready` label must be applied by a trusted maintainer; enforce permission through GitHub's repository roles and an additional protected environment reviewer before any worker receives a token. The worker gets one repository's read/write contents and PR permissions, no Actions/workflow or secrets administration rights. Use a GitHub App installation token scoped to the target repository where practical. Avoid long-lived PATs. Its VM/container gets no routes to management/production networks and no Docker socket. Log job ID, issue, branch, PR, token scope and resource usage; redact all secrets. Set CPU, memory, wall-clock and API-spend limits.

Interactive OpenCode/Codex shell tools have the full rights of `coder`. Keep that account out of sudo and Docker groups with no production secrets. The separate `devops` SSH administrator may have elevated access for initial setup; do not run agent tools under it. Tool-specific approval prompts are useful friction, not a security boundary against malicious repository content.

The owner permits automatic PR merging for this repository under root `AGENTS.md`. A trusted repository agent with appropriate existing GitHub permissions can review and merge a passing PR without another confirmation. This does not expand disposable-worker permissions or replace explicit approval for production deployment and protected infrastructure changes.
