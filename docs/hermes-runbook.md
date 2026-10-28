# Hermes runbook

Operating guide for the Hermes agent on VM 101 (`hermes-agent`). Design and decisions: [Hermes plan](hermes-n8n-telegram-plan.md). Build evidence: [sandbox plan](hermes-rootless-sandbox-plan.md), [credential setup](hermes-credential-setup.md). Open work: [todo](../agents/todo.md).

## What runs where

| Piece | Where | Starts at boot |
| --- | --- | --- |
| VM 101 | Proxmox `pve1`, `onboot: 1`, `startup: order=3` | Yes, after VMs 100 and 130 |
| Telegram gateway | `hermes` user service `hermes-gateway.service` (`hermes gateway run`, `Restart=always`) | Yes, through user lingering |
| Commands | Run directly on VM 101 as `hermes` (Hermes `local` terminal backend), with passwordless sudo (`/etc/sudoers.d/60-hermes-admin`) and approval prompts off. Hermes manages its own packages and upgrades; see its `vm-self-admin` skill. Rootless Docker under `hermes` remains for Hermes's own use | Yes, through user lingering |
| Network wall | Proxmox VM firewall `/etc/pve/firewall/101.fw`: private ranges, CGNAT and IPv6 rejected; public internet open | Yes, with the host |
| In-guest guard | `hermes-egress.service` loads `/etc/hermes-egress.nft`: the `hermes` account and its sandboxes cannot reach private addresses, including the VM's own LAN address (router DNS allowed). Disable for diagnosis with `systemctl stop hermes-egress` | Yes |

The guest's address and SSH host key are in ignored site inventory. Administrators connect as `devops` (key-only) and act on the agent as `hermes`:

```bash
sudo -iu hermes
```

Inside that shell, user-service commands need `export XDG_RUNTIME_DIR=/run/user/$(id -u)` when not started from a login session.

## Everyday checks

```bash
systemctl --user status hermes-gateway docker
journalctl --user -u hermes-gateway -f
hermes sessions list
hermes config get model
```

Logs also live in `~/.hermes/logs/` (`gateway.log`, `agent.log`). Lines `inbound message: platform=telegram user=…` show who reached the bot; anything from an unlisted user should be refused there.

From the Proxmox host without SSH into the guest: `qm guest exec 101 -- runuser -l hermes -c "<command>"`.

## Start, stop and restart

```bash
systemctl --user restart hermes-gateway   # after config or .env changes
systemctl --user stop hermes-gateway      # stop until next boot
systemctl --user start hermes-gateway
```

## Kill switch

Use the first that fits; each is reversible.

1. **Stop the bot and keep it stopped across reboots:** `systemctl --user disable --now hermes-gateway`.
2. **Cut the bot off at Telegram** (works even if the VM is unreachable): BotFather → `/mybots` → the Hermes bot → API Token → **Revoke current token**.
3. **Stop the whole VM** from the Proxmox host: `qm stop 101` (or `qm shutdown 101`). To keep it down after host reboots: `qm set 101 --onboot 0`.
4. **Cut spending:** disable or delete the OpenRouter key on openrouter.ai.

## Credentials and where to revoke them

Stored in `/home/hermes/.hermes/.env` (owner `hermes`, mode 600), entered only through `hermes-secret <name>` with hidden input. Check presence by name and length, never by value.

| `hermes-secret` name | Variable | Limits | Revoke at |
| --- | --- | --- | --- |
| `telegram` | `TELEGRAM_BOT_TOKEN` | Bot `the Hermes bot`, groups disabled | BotFather → API Token → Revoke |
| `owner` | `TELEGRAM_ALLOWED_USERS` | Owner's numeric ID only (not secret) | Edit with `--replace` |
| `openrouter` | `OPENROUTER_API_KEY` | $10/month key limit | openrouter.ai → Keys |
| `exa` | `EXA_API_KEY` | Exa account limits | dashboard.exa.ai → API keys |
| `github` | `GITHUB_TOKEN` | Fine-grained PAT `hermes-homelab`: all repositories, Contents and Pull requests read/write, no Workflows/Administration/Secrets/Webhooks, 90-day expiry. Acts as the owner | GitHub → Settings → Developer settings → Fine-grained tokens |
| `n8n-mcp` | `N8N_MCP_TOKEN` | Instance-level MCP token (JWT `aud: mcp-server-api`); all 58 tools | n8n → Settings → Instance-level MCP → revoke the access token |

Git: `hermes`'s global git config has a credential helper that reads `GITHUB_TOKEN` from `~/.hermes/.env`, plus a credential helper on `https://github.com` and the commit identity `Hermes (kevinofsydney)` with the owner's no-reply email. `gh` is not installed; Hermes may install it, otherwise pull requests go through the REST API.

To rotate: create the new value at the provider, run `sudo -iu hermes hermes-secret <name> --replace`, restart the gateway, then revoke the old value.

## Configuration

`ansible/playbooks/hermes-sandbox-config.yml` holds the reviewed settings: sandbox image digest and limits, approvals (`manual` plus a deny list), checkpoints, redaction, telemetry off, Exa web search and the model. Change settings there first, then apply. The pre-hardening config is kept as `~/.hermes/config.yaml.pre-hardening-20261028`.

**Self-administration (owner decision 2026-10-28).** `ansible/playbooks/hermes-self-admin.yml` gives `hermes` passwordless sudo, switches to the `local` backend and turns approval prompts off. The deny list still applies with approvals off. Accepted risk: a prompt injection or model mistake can do anything on VM 101 and read every Hermes credential; the Proxmox firewall still keeps it off the home network, and recovery is a snapshot or the 3-day backup plus rotating keys. Hermes asks the owner before an Ubuntu release upgrade so a snapshot can be taken first. To revert: restore `~/.hermes/config.yaml.pre-sudo-20261028`, remove `/etc/sudoers.d/60-hermes-admin`, restart the gateway.

**Pull requests need the owner's go-ahead (owner decision 2026-10-28).** The `pr-gate` plugin (`~/.hermes/plugins/pr-gate`, source `config/hermes/plugins/pr-gate`) blocks terminal, code and file-write calls that would open or merge a pull request (`gh pr create/merge`, REST POST/PUT to `/pulls`, `/pulls/<n>/merge`, GraphQL create/merge mutations) unless the owner's latest message in that session starts with "approve". Hermes then messages the repository, branch, summary and size and waits. To approve from Telegram, reply `approve`. A standing rule in `~/.hermes/memories/USER.md` says the same. It is a workflow check, not a boundary: Hermes has sudo and could disable it (`hermes plugins disable pr-gate`), and a PR opened by a script file it wrote earlier is not detected.

Command approvals arrive as Telegram buttons. **Always** adds a permanent entry to `command_allowlist`: the owner kept `script execution via -e/-c` on 2026-10-28. Clear all such entries with `hermes config set command_allowlist '[]'`.

## n8n

- Hermes reaches the owner's n8n Cloud instance over MCP (`mcp_servers.n8n`, token from `N8N_MCP_TOKEN`) with **all 58 tools** (owner decision 2026-10-28; no `tools.include` filter): workflows, executions, versions, data tables, credentials (names and types only), folders, projects, tags, archiving and n8n Agents. Workflow scope is whatever n8n marks "Available in MCP" (22 `UFC | ` workflows); data tables are visible instance-wide (37 on 2026-10-28, of which 27 are `RA | ` research-agent tables kept for reference).
- The skill `~/.hermes/skills/software-development/n8n-workflows/SKILL.md` tells Hermes to read first, note the rollback version, validate and test before publishing, and report the rollback version after. It also requires asking the owner before `delete_data_table_column` (data tables are not backed up), `archive_workflow`, and deleting, unpublishing or reverting n8n Agents, and limits `call_agent` to owner requests.
- Hermes owns its skills and may edit all of them, including this one (owner decision 2026-10-28: self-improvement outweighs keeping the rules read-only, since the skill is advisory and the real limits are the n8n token, the export job and version history). Its edits are logged in `~/.hermes/skills/.curator_ledger.jsonl` and kept by the VM backups. `config/hermes/skills/n8n-workflows/SKILL.md` in this repo is only the seed; copy the live file back here when it changes in a way worth keeping.
- **Rollback a bad publish:** in n8n, open the workflow's version history and restore the previous version, then publish; or ask Hermes to `restore_workflow_version` and `publish_workflow` with the version ID it reported.
- **Exports outside Hermes:** `hermes-n8n-export.timer` (nightly about 03:30 Melbourne, `Persistent=true`) runs `/usr/local/sbin/hermes-n8n-export` as root and writes each workflow's full JSON to `/var/backups/n8n/<UTC timestamp>/<id>.json`, keeping 30 runs. The `hermes` account cannot read that directory. Run one now with `sudo systemctl start hermes-n8n-export`. To restore from an export, copy the file off the VM and use n8n's **Import from File** on the `workflow` object; this creates a new, unpublished workflow.
- **Revoke n8n access:** revoke the MCP token in n8n, or turn instance-level MCP off.

## Recovery

- **After a reboot:** nothing to do. Verified 2026-10-28: VM back in about 21 s, gateway active in about 22 s with no restarts and reconnected to Telegram, rootless Docker and the pinned image present, firewall rules intact, and the owner's next message answered.
- **Gateway crash-looping:** `journalctl --user -u hermes-gateway -b`; a bad config or credential is the usual cause. Restore the previous config or rotate the credential.
- **Rebuild from scratch:** clone the template (`scripts/clone-application-vm.sh` with the Hermes sizing), apply `proxmox/firewall/hermes.fw.example` as `101.fw`, then run `hermes-agent.yml`, `hermes-credential-helper.yml`, `hermes-rootless-packages.yml`, `hermes-rootless-user.yml`, `hermes-terminal-backend.yml` and `hermes-sandbox-config.yml`; re-enter credentials and run `hermes gateway install --start-on-login`. Memory and session history are lost unless backed up (todo 1).
