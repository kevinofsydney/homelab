# Dev VM isolation plan (security review item 6)

Status: proposed 2026-10-27, awaiting owner approval. Nothing below has been applied.

## Goal

Code running on dev VM 100, including OpenCode/Codex as `coder` and a fully compromised guest root, cannot open connections to the Proxmox host, the QNAP, the router's admin pages or any other LAN device. The VM keeps internet access, DHCP and DNS through the router, and operators can still SSH in. The rules are enforced by the Proxmox host on the VM's network port, so nothing inside the guest can change them.

## Observed state (read-only, 2026-10-27)

- `pve-firewall status`: `disabled/running`. No `cluster.fw`, `host.fw`, `100.fw` or `130.fw` exist. Host iptables policies are all ACCEPT.
- Both VM NICs already have `firewall=1`, so the per-VM firewall bridges exist and no VM restart is needed.
- From the dev VM: Proxmox 22/8006, QNAP 22/443/445/2049 and router 53/80/443 are reachable. The VM has IPv6 link-local only, but the Proxmox host's link-local address is reachable that way too, so IPv6 must be covered.
- Dev VM DNS server is the router. Tailscale on the dev VM is logged out; Proxmox has no Tailscale.

## Proposed change

Three files, kept in the repo under [`proxmox/firewall/`](../proxmox/firewall/):

| File on the host | Effect |
| --- | --- |
| `/etc/pve/firewall/cluster.fw` | `enable: 1`: turns the firewall framework on |
| `/etc/pve/nodes/pve1/host.fw` | `enable: 0`: **host stays unfiltered**, so SSH and the web UI cannot be locked out by this change |
| `/etc/pve/firewall/100.fw` | Dev VM: inbound unchanged (`policy_in: ACCEPT`); outbound allows DNS to the router, DHCP and IPv6 neighbour discovery, then rejects every private range (192.168/16, 10/8, 172.16/12, link-local IPv4, IPv6 link-local TCP/UDP, IPv6 ULA). Internet traffic passes |

VM 130 gets no `130.fw`, so its firewall stays disabled and Paperless/Uptime Kuma are unaffected. Established connections, such as an operator's SSH session into the dev VM, are always allowed by the Proxmox ruleset. `REJECT` is used instead of `DROP` so blocked tools fail fast instead of hanging.

## Apply procedure (from an operator device, as root on pve1)

1. Back up: `mkdir -p /root/fw-backup && cp -a /etc/pve/firewall /etc/pve/nodes/pve1/host.fw /root/fw-backup/ 2>/dev/null`.
2. Write `host.fw` **first**, then `100.fw`, then `cluster.fw` last, so the host is never filtered even briefly.
3. Before enabling, run `pve-firewall compile` and check the VM 100 chain lists the rules above and the host chain is empty.
4. Arm a dead-man switch: `systemd-run --on-active=600 --unit=fw-rollback sh -c 'sed -i "s/^enable: 1/enable: 0/" /etc/pve/firewall/cluster.fw'`. If anything goes wrong and nobody cancels it, the firewall turns itself off after 10 minutes.
5. Write `cluster.fw`; `pve-firewall status` should report `enabled/running` within about 10 seconds.
6. Run the tests below. If all pass, cancel the switch: `systemctl stop fw-rollback.timer`.

## Rollback

Any one of these, fastest first:
- `pve-firewall stop` on pve1 (stops all filtering immediately; config stays for later).
- Set `enable: 0` in `/etc/pve/firewall/cluster.fw`, or Datacenter → Firewall → Options → Firewall: No in the web UI.
- Delete `/etc/pve/firewall/100.fw` to remove only the dev VM rules.

Because the host itself is never filtered, the web UI, its Shell and root SSH remain available for every rollback.

## Acceptance tests

Run from the dev VM as `coder` (and repeat one as guest root to show it makes no difference):

| Expect blocked | Expect allowed |
| --- | --- |
| Proxmox `<lan-host>` TCP 22, 8006 | DNS lookup through the router (`getent hosts github.com`) |
| Proxmox IPv6 link-local TCP 22 | `curl -sI https://github.com` and an Ubuntu archive URL |
| QNAP TCP 22, 443, 445, 2049 | Operator SSH into the dev VM (new session) |
| Router TCP 80, 443 | DHCP lease renewal (check after the next renewal, or `networkctl renew eth0`) |
| Home-services VM TCP 22 | |

Also confirm from an operator device: Proxmox web UI and root SSH still work, and Paperless and Uptime Kuma still respond on their Tailscale addresses. Record results in `agents/context.md` and mark item 6 in the security review.

## Limits and follow-ups

- **Tailscale bypass.** When the dev VM joins the tailnet, its traffic to other tailnet devices travels inside the encrypted tunnel and these rules cannot see it. Before enrolling it, add a tailnet policy that stops the dev VM reaching the home-services VM, the QNAP and any other admin device on the tailnet.
- **IPv6.** The router currently gives no global IPv6 addresses. If it starts doing so, add a rule for the LAN's global prefix.
- **Router DNS stays reachable** (port 53 only), because the VM needs it. The router's admin pages are blocked.
- **Agent workflow.** After this, an agent on the dev VM cannot SSH to other homelab machines. Changes go through PRs to this repository, with an operator applying them; a narrow, approved exception (for example dev → home-services SSH) can be added later if wanted.
- The same pattern, with its own `<vmid>.fw`, is the planned egress control for the future Hermes guest.
