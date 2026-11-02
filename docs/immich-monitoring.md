# Immich monitoring and Hermes triage

**Status: prepared, not deployed.** The code and tests are in the repository. Nothing here has run on the Immich VM, on VM 101, in the tailnet policy or in Uptime Kuma. Deploying it needs the owner's approval and the owner's actions in the Tailscale console. Replace this status line with the evidence when it is applied.

## Goal and design

The owner wants Hermes to help monitor and triage Immich. Hermes has passwordless sudo, approvals off and open internet, and the owner accepted the risk that a prompt injection could control VM 101. So Hermes gets no route to Immich itself and no Immich credential: an admin API key, SSH or port 2283 would each put the photo library within reach of a hijacked agent.

| Piece | Where | What it does |
| --- | --- | --- |
| Collector (`scripts/immich-status-collect.py`, one-minute timer) | Immich VM, as root | Writes `/run/immich-status/status.json`: fixed keys, allow-listed states and numbers. No logs, paths or NAS source. It loads only four named settings from `.env`, never the database password |
| Status server (`scripts/immich-status-server.py`) | Immich VM, `DynamicUser` with no capabilities | Serves `GET /status` on the Tailscale address, port 2284. No other route, no inputs and no actions. Reports `overall: stale` if the snapshot is over five minutes old |
| Tailnet grant | Tailscale policy | `tag:hermes` may reach only `tcp:2284` on the Immich VM |
| Egress exception (`config/hermes/hermes-egress.nft.j2`) | VM 101 | Lets the `hermes` account reach only that address and port. Hermes has sudo and could remove this guard, so the tailnet policy is the real limit |
| `/immich` skill (`config/hermes/skills/immich`) | VM 101 | Reads the status and suggests a fix for the owner to run. Runs on request, so idle monitoring spends no model budget |
| Uptime Kuma monitors | VM 130 | Detect outages and send Telegram alerts through the alerts bot, independently of Hermes and the Immich VM |

The queue-count API key is optional, stays on the Immich VM and needs only `queue.read` (`GET /api/queues` in the v3.3.5 API spec). Raw logs are excluded on purpose: filenames can appear in them, and a crafted filename could be a prompt injection aimed at an agent with sudo.

**Limits.** A hijacked Hermes could read the snapshot but not photos, accounts or credentials. Kuma runs on the same host, so a whole-host or home-network outage produces no alert. The snapshot doesn't prove that uploads work or that photos are intact.

**Decision status.** Proposed by this change, and takes effect on deployment: enrolling VM 101 in Tailscale as `tag:hermes` supersedes "do not enrol this guest in Tailscale" in the [Hermes plan](hermes-n8n-telegram-plan.md). The [dev VM isolation plan](dev-vm-isolation-plan.md) allows tagged agent guests a specific approved destination.

## Deploy, after approval

Keep this order: the policy comes before enrolment, so VM 101 never joins with more access than intended. Site values go in ignored `ansible/inventory/hosts.yml`.

### 1. Status path on the Immich VM

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/immich-status.yml --check --diff
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/immich-status.yml
```

On the VM, start it and check it:

```bash
sudo systemctl enable --now homelab-immich-status-collect.timer homelab-immich-status.service
curl -s "http://$(tailscale ip -4):2284/status"
```

Optional queue counts: in Immich, create an API key with only the `queue.read` permission, then store it with hidden input.

```bash
sudo sh -c 'umask 077; read -rs key; printf %s "$key" > /etc/homelab/immich-status-api-key'
```

### 2. Tailnet policy (owner, admin console)

Merge these into the existing policy, using the Immich VM's Tailscale address, and keep the existing tests. Tailscale runs the tests on save and rejects the policy if any fails.

```json
{
  "tagOwners": {"tag:hermes": ["autogroup:admin"]},
  "hosts": {"immich-vm": "REPLACE_IMMICH_TAILSCALE_IP"},
  "grants": [{"src": ["tag:hermes"], "dst": ["immich-vm"], "ip": ["tcp:2284"]}],
  "tests": [{
    "src": "tag:hermes",
    "accept": ["immich-vm:2284"],
    "deny": ["immich-vm:2283", "immich-vm:22", "REPLACE_HOME_SERVICES:443", "REPLACE_NAS:443", "REPLACE_TITAN:445"]
  }]
}
```

The existing default grant has `autogroup:member` as its source, so it doesn't apply to tagged devices. Don't add any grant with `*` as its source.

### 3. Enrol VM 101

The `tailscale_client` role is pinned to Ubuntu 24.04 and VM 101 runs 26.04.1, so it refuses this guest. Install from Tailscale's signed repository for the guest's release, after confirming that repository exists. Then enrol, with the owner approving the login:

```bash
sudo tailscale up --advertise-tags=tag:hermes --accept-dns=false --accept-routes=false --ssh=false
```

The Proxmox firewall sees only the encrypted tunnel, not the traffic inside it. Direct LAN paths stay rejected, so the connection may use a public path or Tailscale's relay.

### 4. Give Hermes access

Add `hermes_immich_status_ip` to the `hermes_agent` host in the inventory, then:

```bash
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/hermes-egress-guard.yml --check --diff
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/hermes-egress-guard.yml
ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/hermes-immich-status-access.yml
```

The access playbook refuses to run unless the guest has `tag:hermes` and has DNS, routes, an exit node and Tailscale SSH all off. Restart the gateway afterwards so the skill and menu load: `systemctl --user restart hermes-gateway` as `hermes`.

### 5. Uptime Kuma (owner, web UI)

Use the alerts bot (`telegram.alerts_bot` in ignored `config/site.json`), not the Hermes bot, so VM 130 never holds Hermes's token. Add two monitors with Telegram notifications:

| Monitor | Type | URL | Match |
| --- | --- | --- | --- |
| Immich API | HTTP keyword | `http://<Immich Tailscale address>:2283/api/server/ping` | `pong` |
| Immich health | HTTP keyword | `http://<Immich Tailscale address>:2284/status` | `"overall":"ok"` |

Confirm first that the Kuma container can reach those addresses; this path hasn't been tested.

## Acceptance checks

Run these from VM 101 as `hermes`, not from Hermes's own report, and record the results here:

1. `curl` to the status URL returns JSON.
2. These fail: `curl -m 5 http://<Immich address>:2283/`, and connections to port 22 on the Immich VM, home-services, the NAS and Titan. Repeat them as root, because the `hermes` account can gain root.
3. `tailscale status` on VM 101 shows no route or exit node in use.
4. Tailscale's policy tests passed on save.
5. `/immich` in Telegram gives a correct summary.
6. With the owner's approval, briefly stop one non-essential container: `overall` becomes `degraded`, Kuma alerts, and `/immich` names it. Restart through `deploy-immich.sh --apply`.
7. Stop the collector timer: `overall` becomes `stale` within about five minutes and Kuma alerts. Start it again.

## Roll back

Each step can be undone on its own.

- **Cut Hermes off:** remove the grant from the tailnet policy. This takes effect without touching either VM.
- **Remove VM 101 from the tailnet:** `sudo tailscale logout`, then delete the device in the console.
- **Remove the egress exception:** delete `hermes_immich_status_ip` from the inventory and rerun `hermes-egress-guard.yml`.
- **Stop the status path:** `sudo systemctl disable --now homelab-immich-status.service homelab-immich-status-collect.timer`. Immich itself doesn't depend on it.
- **Revoke queue access:** delete the API key in Immich and remove `/etc/homelab/immich-status-api-key`.
