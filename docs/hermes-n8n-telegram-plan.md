# Hermes with Telegram and n8n: initial deployment plan

Status: design and read-only discovery, 2026-10-27. No new guest, firewall, n8n, bot, provider credentials or service has been created for this plan. This plan does not authorize execution. The existing [UFC/Hermes handoff](../agents/handoffs/ufc-hermes-rebuild.md) remains the source for workflow IDs and prior requirements; self-hosted n8n and QNAP backups remain outside scope.

## Goal and placement

A Telegram user chats privately with Hermes, which uses an approved hosted model and narrowly scoped n8n MCP capabilities. Start with one separate Hermes guest, rather than enabling the dormant Hermes installation in the development guest. The latter currently has an owner-initiated Ubuntu release upgrade in progress, and the coding account can reach Proxmox and QNAP management. The 2026-10-27 read-only inventory showed the existing template and two VMs, about 19 GiB host memory available and approximately 6.9% thin-pool physical use. These are observations, not reservations or sizing approval; inspect real capacity again before creating a guest. The earlier proposal of 4 vCPU, 8 GiB and 80 GiB is an initial sizing proposal, not a running guest. Select an unused ID, review the disk budget, preserve both existing VMs and leave host disks/network untouched.

The existing clone script hardcodes 2 vCPU, 4 GiB and 60 GiB; it must not be used as though it implements the proposed sizing. Prepare and test a parameterized, plan-by-default provisioning change first, or explicitly choose its existing allocation after capacity review. A separate UFC agent and its API gateway are **not** required merely to install Hermes; deploy those only if the operator requests them.

## Isolation and access

Before any model or Telegram gateway starts, enforce the guest's network isolation outside the agent's control, verify the guest and any nested sandbox cannot reach Proxmox, QNAP, router management, the app VM or other protected LAN hosts, and verify only intended outbound destinations are reachable. The last read-only check showed `pve-firewall status` as disabled/running; enabling it or changing rules is a host/network change requiring explicit approval and an independently verified management path and rollback plan. Do not assert isolation from a process running as the agent or from instructions in a prompt. Dynamic DNS, provider endpoints, TLS and IPv6 need a workable egress design; do not assume a hostname rule is enforced by a firewall that only understands IP addresses.

Use a separate non-sudo `hermes` user and its own credentials, with no host Docker socket, Proxmox/QNAP/router access, infrastructure tokens, or unrestricted production access. Install the pinned CLI using a guest-targeted Ansible playbook and a previously verified release. The existing role is pinned to Ubuntu 24.04 and Hermes v0.22.5; review current release compatibility and version-specific configuration before applying. A rootless sandbox or a tool-disabled initial chat must be tested rather than assumed to be a security boundary. The guest's Proxmox autostart is off by default; enable it only after a separate reviewed/approved host change.

## Provider and Telegram

Recommend OpenRouter initially, with a provider-side spend limit and a reviewed DeepSeek model that is available at deployment time. Direct DeepSeek and OpenCode can be added later; do not assume a specific model identifier, API entitlement, pricing, or automatic fallback. Confirm the operator's provider and model before activation. Use supported Hermes setup/secret storage; the operator enters provider and Telegram credentials via a hidden-input terminal or secret manager, never chat, Git, shell arguments or logs. Do not reuse a token in two running bot processes.

Configure the Telegram gateway to accept only the owner's verified numeric Telegram ID in a private chat; do not enable allow-all. Confirm behavior with an unauthorized sender without sending unsolicited messages. The owner should initiate the test conversation. Recheck the pinned release's actual authorization semantics before declaring the boundary effective.

## n8n access and workflow scope

The operator reported on 2026-10-27 that all non-UFC workflows are archived, and later said a workflow ID allowlist is no longer needed. Scope is the workflows named `UFC | ` in the UFC folder, currently 18 (see the handoff's reference inventory). Make sure any n8n-side account, project and MCP access is scoped to that project. If the UFC gateway enforces scope, it must check the operation and the workflow's name as returned by n8n, never a name supplied by the caller. Do not claim a boundary is enforced until tested, including guessed IDs and execution IDs owned by a non-UFC workflow. Inspect the connected n8n version and actual MCP tool schemas before selecting a proxy design. The currently available session has no n8n connector or MCP credential.

Initial safe default while access preference is unresolved: inspect the approved workflows and propose changes only. Treat MCP tools that run, test, edit, publish, restore or execute workflows as side-effecting until verified. If the operator wants edits, prepare a separate approval-controlled path with diffs, validation and a rollback reference. The user's current request to work on workflows does not by itself establish that arbitrary workflow execution or publishing is authorized.

## Review and acceptance order

1. Confirm desired provider, n8n scope and permitted workflow operations. Record decisions without secrets.
2. Prepare a concrete VM and host-enforced egress policy, verify capacity, known-host access and rollback; obtain explicit approval for VM/firewall changes before applying.
3. Install the agent in the new guest; test guest and sandbox isolation from management targets before adding any credential or connecting MCP.
4. The operator securely enters provider, bot and scoped n8n credentials. Configure owner-only Telegram, spending limits and, in the UFC gateway, server-side scope checks on the `UFC | ` workflow name. Verify exact available MCP tools and supported auth on the actual n8n instance.
5. Test denied IDs, denied mutations, non-owner Telegram access and sandbox egress. With the owner initiating the interaction, test a harmless chat and one approved read-only workflow inspection. Record only status, not token values or message contents.
6. Add systemd/boot recovery only after reviewing required host-autostart approval. Record exact installed versions, tests, status and rollback in shared runbooks. Recovery/backup remains a separately deferred concern.

## References

- [Hermes messaging and model-provider documentation](https://hermes-agent.nousresearch.com/docs), [Telegram configuration](https://hermes-agent.nousresearch.com/docs/user-guide/messaging/telegram), and [model configuration](https://hermes-agent.nousresearch.com/docs/user-guide/configuring-models). Check against the exact installed release; current documentation may describe newer behavior.
- [n8n workflow sharing and permissions](https://docs.n8n.io/workflows/sharing/). Verify feature availability and actual MCP capabilities on the owner's instance.
- [Focused security review](security-review-2026-10-27.md) and [private access runbook](private-access.md).
