# First implementation plan

Status: prepared source only, 2026-10-27. No infrastructure deployment is authorized by this plan.

## Blueprint review boundary

`docs/homelab-blueprint.md` is absent from the tracked checkout and was not supplied with the request. A complete blueprint review is blocked pending that document. This plan uses the operator's brief and existing architecture, security, storage and installation guides; it must be reconciled with the original blueprint before deployment. Do not reconstruct the missing document and present it as the original.

The existing repository already contains root `AGENTS.md`, cloud-init/template instructions, a plan-by-default Proxmox API provisioner, Ansible development and backup-mount roles, a non-sudo coding account, pinned-version CLI installer, Paperless Compose and backup scripts, CI and an issue-to-PR design. Preserve these foundations. They are prepared configuration, not evidence of installed services.

## Confirmed inputs and missing information

The operator reports Proxmox installed on the Dell (i5-12500T, 32 GB RAM, 512 GB SSD), node name `pve1`, a TP-Link BE15000 router, QNAP TS-264 and an existing tailnet. Actual addresses belong in ignored site configuration. Router capability, installed software versions and hardware health have not been independently verified.

| Input required | Why it blocks deployment |
| --- | --- |
| Complete original blueprint | Reconcile intended services, priorities and resource allocation |
| Proxmox version, trusted CA or independently verified host key, actual node/bridge/storage IDs | Identify the host and avoid altering the wrong resource |
| Available VM/template IDs, Ubuntu image checksum, SSH public key, guest DHCP reservation | Prepare a specific clone plan without collisions or invented values |
| QNAP address, QTS version, existing shares, free space, dedicated export paths and numeric ownership | Probe the correct NAS and preserve Plex/storage |
| Tailnet administrators, intended private service identities and current policy | Confirm access boundaries without changing the existing tailnet |
| Reviewed CLI versions and provider login choices | Reproducible Codex/OpenCode installs and controlled costs |
| Exact Hermes project/repository and desired capabilities | Avoid installing an ambiguous package; review tool, messaging and credential access |
| App priorities, user count, library sizes, media application choices and recovery targets | Size the SSD/RAM and choose backup retention only after approval |
| Router/firewall isolation capabilities and worker egress policy | Prove workers cannot reach management or production before unattended execution |

## Read-only observations

On 2026-10-27, `python3 scripts/check-connectivity.py --proxmox-host <intended-management-address>` reached TCP 22 and 8006 from the operator machine. Verified TLS failed with `SSLCertVerificationError`. This does not establish that the endpoint is node `pve1`, nor prove that the management IP is reserved or persistent. No credentials were sent, no TLS bypass was used and no host settings were changed. QNAP was not probed because its address is unknown. The command correctly returned nonzero for incomplete preflight.

Obtain the public CA certificate or host fingerprint through a trusted console before authenticated inventory. A valid CA must also match the hostname/address used. Do not solve a hostname mismatch by disabling certificate verification. Router connectivity and hardware health remain untested.

## Ordered delivery and acceptance gates

| Stage | Preparation | Acceptance before proceeding |
| --- | --- | --- |
| 1. Repository and inventory | Existing safety policy; this plan; config examples; read-only probes | Blueprint reconciled; required inventory confirmed; local checks pass |
| 2. Trusted management inventory | Check installed-version API and read actual node/storage/template state using narrowly scoped read access | CA/host identity trusted; IDs, capacity and resource plan reviewed; no existing VM selected as a new target |
| 3. Ubuntu development VM | Review `proxmox/template.md`, cloud-init and plan-only provisioner; initially 4 vCPU/8 GiB/100 GiB | Explicit template/VM-change approval; boot, DHCP, SSH, guest agent and cloud-init verified after execution |
| 4. Guest and coding tools | Ansible syntax and check-mode review; exact Codex/OpenCode artifacts; separate Hermes release review | Explicit package/account/service approval; `coder` has no sudo/Docker/production credentials; harmless CLI smoke tests pass |
| 5. Backup and recovery | Dedicated QNAP export proposal and mount role; backup and isolated restore procedure | Explicit NAS/mount/backup approval; exact export identity, access and isolated restore verified; Plex unaffected |
| 6. Private application VM | Resource review and per-service pattern below; Paperless first | Explicit provisioning/app approval; health, unauthorized-access rejection, NAS-loss and restore tests pass |
| 7. Disposable workers | Implement dispatcher and worker lifecycle from `agents/workflows/issue-to-pr.md` on a disposable test repository | Hostile-input, token scope/expiry, timeout, management-route blocking and cleanup tests pass before activation |

Check mode and source validation do not authorize applying a plan. Reconfirm SSD free space and peak RAM before each additional VM. Do not allocate all proposed services at once.

## Service and coding-tool preparation

Codex and OpenCode already have a version-controlled installer and separate unprivileged account. Review their exact releases and supported authentication before execution. Hermes remains a blocked installation target until its identity and required permissions are confirmed; do not execute a generic curl installer or grant it a messaging token. An interactive trusted-operator VM and unattended issue worker have different trust boundaries.

Paperless already has the initial Compose implementation. Immich, n8n and selected media applications should each use the [reusable service contract](../compose/README.md), their own runbook and the then-current official upstream Compose baseline. These later stacks are planned, not implemented or validated. Do not invent image tags, hardware-acceleration paths or NAS exports just to produce runnable YAML.

The worker dispatcher remains a design rather than an enabled automation. Use immutable approved source references, single-use workers, narrow expiring credentials and a separate PR publisher. Keep deployment credentials outside workers; test isolation before giving workers issue content. Source PR merge authorization never authorizes production deployment.

## Next operator review

Supply the missing blueprint and inventory above, then review the trusted read-only inventory results and a specific VM/template plan. Infrastructure execution stays paused until explicit approval. Follow [installation](install.md) for commands and [validation](validation.md) for post-change evidence.
