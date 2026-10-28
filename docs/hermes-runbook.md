# Hermes runbook

Operating guide for the Hermes agent on VM 101 (`hermes-agent`). Design and decisions: [Hermes plan](hermes-n8n-telegram-plan.md). Build evidence: [sandbox plan](hermes-rootless-sandbox-plan.md), [credential setup](hermes-credential-setup.md). Open work: [todo](../agents/todo.md).

## What runs where

| Piece | Where | Starts at boot |
| --- | --- | --- |
| VM 101 | Proxmox `pve1`, `onboot: 1`, `startup: order=3` | Yes, after VMs 100 and 130 |
| Telegram gateway | `hermes` user service `hermes-gateway.service` (`hermes gateway run`, `Restart=always`) | Yes, through user lingering |
| Sandbox | Rootless Docker (`systemctl --user` `docker`) under `hermes`; a fresh `nousresearch/hermes-sandbox@sha256:c7d8607d…` container per session, 2 CPU / 4 GiB | Yes, through user lingering |
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

Not yet configured: GitHub App (todo 10) and n8n MCP token (todo 11). Add each here when it is.

To rotate: create the new value at the provider, run `sudo -iu hermes hermes-secret <name> --replace`, restart the gateway, then revoke the old value.

## Configuration

`ansible/playbooks/hermes-sandbox-config.yml` holds the reviewed settings: sandbox image digest and limits, approvals (`manual` plus a deny list), checkpoints, redaction, telemetry off, Exa web search and the model. Change settings there first, then apply. The pre-hardening config is kept as `~/.hermes/config.yaml.pre-hardening-20261028`.

Command approvals arrive as Telegram buttons. **Always** adds a permanent entry to `command_allowlist`: the owner kept `script execution via -e/-c` on 2026-10-28. Clear all such entries with `hermes config set command_allowlist '[]'`.

## Recovery

- **After a reboot:** nothing to do. Verified 2026-10-28: VM back in about 21 s, gateway active in about 22 s with no restarts and reconnected to Telegram, rootless Docker and the pinned image present, firewall rules intact, and the owner's next message answered.
- **Gateway crash-looping:** `journalctl --user -u hermes-gateway -b`; a bad config or credential is the usual cause. Restore the previous config or rotate the credential.
- **Rebuild from scratch:** clone the template (`scripts/clone-application-vm.sh` with the Hermes sizing), apply `proxmox/firewall/hermes.fw.example` as `101.fw`, then run `hermes-agent.yml`, `hermes-credential-helper.yml`, `hermes-rootless-packages.yml`, `hermes-rootless-user.yml`, `hermes-terminal-backend.yml` and `hermes-sandbox-config.yml`; re-enter credentials and run `hermes gateway install --start-on-login`. Memory and session history are lost unless backed up (todo 1).
