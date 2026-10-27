# Hermes agent with Telegram, Git and n8n MCP: deployment plan

Status: owner decisions recorded 2026-10-27. **No guest, firewall rule, bot, provider credential or service has been created**, and this plan does not authorize execution. Workflow IDs and prior requirements remain in the [UFC/Hermes handoff](../agents/handoffs/ufc-hermes-rebuild.md); self-hosted n8n and QNAP backups stay out of scope.

## Decisions

| Topic | Decision |
| --- | --- |
| Runtime | Hermes, pinned release, using the existing `ansible/roles/hermes_cli` |
| Model | Latest DeepSeek flash. The exact model identifier is resolved from the provider catalogue at deploy time and is not assumed here; `deepseek-v4.1-flash` in the handoff is the last recorded value, not a promise |
| Provider and budget | OpenRouter in front of that model, chosen for a **hard $10/month key limit**. DeepSeek direct is prepaid balance, which caps spend only while auto-top-up stays off |
| Availability | 24/7 with `onboot 1` and `startup order=3` on the new guest, gateway supervised as a systemd unit |
| Git authority | GitHub App installation scoped to this repository: contents and pull requests only. **Opens pull requests and does not merge them** |
| n8n authority | Inspect, edit, test and **publish** workflows in the `UFC | ` scope. No freeze window. Export before publish is mandatory |
| Chat | Telegram, owner's numeric ID only, private chat, long polling |

## Goal

The owner talks to one agent over Telegram and it: clones and pulls repositories, edits and tests them, commits and pushes a branch, opens a pull request, and inspects or changes `UFC | ` n8n workflows.

## Placement and sizing

A dedicated guest (next unused VM ID) cloned from the proven Ubuntu 24.04.5 template — not the development VM and not the application VM. Proposed 4 vCPU / 8 GiB / 80 GiB, confirmed against real capacity first; with 8 GiB on VM 100 and 4 GiB on VM 130 that leaves roughly 12 GiB of the host's 32 GiB for Proxmox.

The plan-first `scripts/clone-application-vm.sh` supports explicit `APP_VM_CORES`, `APP_VM_MEMORY_MIB` and `APP_VM_DISK_GIB` values; defaults remain 2 vCPU / 4 GiB / 60 GiB. For the proposed allocation use `4`, `8192` and `80` respectively. Its capacity check uses the requested disk size; separately verify live host memory and storage capacity before applying. It leaves the VM stopped and autostart disabled. `ansible/playbooks/hermes-agent.yml` prepares the existing pinned CLI in a separate non-administrative account on Ubuntu 24.04; it does not configure credentials or start a gateway. Both are prepared only: creating or configuring a VM and changing firewall rules require operator approval.

## Isolation

Host-enforced, outside the agent's control, following the pattern proven on the development VM on 2026-10-27 (host firewall applied, VM blocked from private addresses, verified after a reboot; see [dev VM isolation plan](dev-vm-isolation-plan.md)):

- Deny every private address, including Proxmox management, the NAS, the router and the application VM.
- Allow only the destinations the agent needs: `api.telegram.org`, `api.github.com`, the OpenRouter endpoint and the n8n host.
- Do **not** enrol this guest in Tailscale. Telegram long polling needs no inbound path, and a tailnet route would bypass address-based rules.
- Verify from inside the guest and from inside the agent's sandbox, not from a prompt or the agent's own report.

## Credentials

| Secret | Scope | Notes |
| --- | --- | --- |
| GitHub App installation token | This repository only, contents + pull requests | Short-lived and revocable per installation; no Actions, workflow or secret administration |
| Telegram bot token | Owner's numeric ID, private chat | One process per token; entered through hidden input or a secret store, never chat, Git or shell arguments |
| n8n MCP credential | The UFC project, workflows named `UFC | ` | Scope checked server-side on the workflow name returned by n8n, never on a caller-supplied name |
| Model provider key | $10/month hard limit | Plus agent-side job budget, timeouts and telemetry off |

`GITHUB_TOKEN` is forwarded into the sandbox only, as recorded in the handoff; it never reaches the host shell or logs.

## Git workflow

Clone into `/home/hermes/workspaces`, branch, commit, push **its own branch**, open a pull request, stop. `main` stays protected against the agent identity, so a bad edit costs a closed PR rather than a broken `main`. Deny force-push, branch deletion and `curl | sh`/`wget | sh`, per the handoff's approval configuration.

## n8n workflow authority

Edit and publish are authorised. Because publishing is immediate and there is no freeze window, the guardrails are per-change rather than calendar-based:

1. Export the current workflow JSON to a dated file **before** any publish; the change is not made if the export fails.
2. Publish as the final step, after the edit and any test, and log a one-line diff summary first.
3. Rollback is re-importing the previous export. Version history is a convenience, not the recovery plan.
4. Inspect the instance's real MCP tool schemas first: publishing may be a parameter of an update tool rather than a separate one, and every tool that runs, tests or executes is side-effecting until proven otherwise.
5. A bad publish during a UFC card is possible by design; the owner accepted that risk with the export-before-publish requirement and no freeze window.

## Telegram

Owner-only numeric ID in a private chat, never allow-all. Long polling means no published service and no inbound port, so [bot protection](bot-protection.md) does not apply. Test with an unauthorised sender without sending unsolicited messages, and have the owner initiate the first conversation.

## Phases and gates

| Phase | Work | Gate before proceeding |
| --- | --- | --- |
| 0 | Backups exist (todo #1), DHCP reservation, App installed, provider key with the $10 limit, model ID confirmed | Owner decisions complete; a backup exists before an agent holds push rights |
| 1 | Clone the guest, baseline, host firewall, isolation acceptance, rollback test | Private addresses unreachable from guest and sandbox |
| 2 | Pinned Hermes, `hermes` user, rootless Docker, pinned sandbox image, approvals `manual`, checkpoints, redaction, telemetry off | No host socket, no LAN route, sandbox cannot see management addresses |
| 3 | GitHub App + scratch repository: clone → branch → commit → push → pull request | Cannot push `main`, cannot force-push, no token in logs |
| 4 | Telegram gateway unit, owner allowlist, spend cap, kill switch | Unauthorised sender refused; an injection attempt to push to `main` refused |
| 5 | n8n MCP read-only inspection, then edit and publish with the export step | Denied IDs fail server-side; an export is proven restorable |
| 6 | `onboot 1` order 3, gateway restart policy, workspace backup, runbook | A guest reboot brings the bot back without intervention |

## Acceptance evidence

Record command output and journal lines, not summaries, in [open work](../agents/todo.md) and [shared context](../agents/context.md): isolation probes, `git` refusal on `main`, Telegram allowlist denial, a restored workflow export, and the reboot recovery.

## References

- [UFC/Hermes handoff](../agents/handoffs/ufc-hermes-rebuild.md) — pinned Hermes configuration and prior requirements.
- [Agent permission model](../agents/permissions.md) — what the Hermes actor may and may not do.
- [Private access](private-access.md), [security](security.md), [dev VM isolation plan](dev-vm-isolation-plan.md).
