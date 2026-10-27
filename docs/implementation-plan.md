# First implementation plan

Status: initial development bootstrap approved and executed on 2026-10-27; later infrastructure remains gated. See [deployment evidence and remaining gates](development-bootstrap.md). This plan itself grants no authorization beyond the operator's explicit approval.

## Blueprint review boundary

The operator supplied the original [blueprint](homelab-blueprint.md), dated 2026-10-26, on 2026-10-27. It is preserved unchanged as a design reference and has now been reviewed in full against the repository. Embedded checklists and commands are proposed work, not authorization to execute infrastructure changes. Current root `AGENTS.md` and explicit operator instructions govern execution.

## Blueprint reconciliation

| Blueprint item | Review decision and remaining work |
| --- | --- |
| Private repository and Proxmox installation | Repository exists; operator reports installation complete. Do not repeat the destructive installer. Verify live identity/version and hardware health |
| Four persistent VMs with illustrative IDs | Retain phased sizing in `docs/architecture.md`: one 8 GiB development guest first. The proposed ranges total 22–28 GiB before host overhead; upper allocations leave insufficient headroom for a 4–6 GiB host reserve and workers. IDs are examples until checked for availability |
| QNAP shares and per-service credentials | Paths in the blueprint are illustrative. Existing NFS pattern requires exact exports, client restrictions and numeric UID/GID mapping; service-account passwords alone do not authenticate traditional NFS. No share creation or Plex change is approved |
| No automatic merge | Superseded for `kevinofsydney/homelab` by the owner's later standing authorization in root `AGENTS.md`. Other repositories keep their own policy; draft worker PRs require trusted review and passing current-head checks. Production deployment still requires explicit approval |
| Guest firewall, Docker, Tailscale and updates | Planned privileged changes, not completed by source scaffolding. Prepare reviewed package versions and change plans; prove a second SSH session before restrictions; do not give `coder` Docker access |
| Hermes Agent and Telegram | Nous Research upstream and stable v0.22.5 are now reviewed; pinned dormant CLI installed in a separate account. Approved Telegram identity, model/provider, spend ceiling and enabled tools remain missing; no gateway activation or bot credential use yet |
| Grok GitHub connector or public MCP/webhook | Optional later integrations. Verify current upstream capabilities before implementation. Prefer issue creation through narrow permissions; public endpoints require separate ingress/security review and explicit approval |
| Paperless built-in AI and external Paperless-AI status | Time-sensitive claims in the source document have not been independently verified in this review. Check official release documentation and upstream maintenance status before selecting features. Keep cloud AI disabled pending document privacy choices |
| Immich, n8n, Audiobookshelf/Kavita | Intended media candidates clarified; final selection and release-compatible stacks remain pending. Use the reusable service contract rather than inventing deployable image sets or exports |
| Public web app production | Preserve managed-hosting preference; hosting, the accounting system edition/import schema, billing rules and privacy/recovery requirements remain undecided. Use synthetic data until approved for users use |
| QNAP-first backups | Initial staging target only. Verify an isolated restore and add independent encrypted backups before relying on it for irreplaceable/public data; retention changes require approval |
| Update reports and optional Pi-hole/local models | Report-only checks can be prepared later; no scheduled jobs or broad automatic upgrades are enabled. Retain NextDNS and defer optional DNS/inference changes |

All blueprint sections, including phase acceptance checklists, suggested structure, unresolved facts and documentation links, were reviewed. External URLs are reference leads, not verified current product guarantees. Source validation does not satisfy the blueprint's live backup, isolation or application acceptance tests.

The existing repository already contains root `AGENTS.md`, cloud-init/template instructions, a plan-by-default Proxmox API provisioner, Ansible development and backup-mount roles, a non-sudo coding account, pinned-version CLI installer, Paperless Compose and backup scripts, CI and an issue-to-PR design. Preserve these foundations. They are prepared configuration, not evidence of installed services.

## Confirmed inputs and missing information

The operator reports Proxmox installed on the Dell (i5-12500T, 32 GB RAM, 512 GB SSD), node name `pve1`, a TP-Link BE15000 router, QNAP TS-264 and an existing tailnet. Actual addresses belong in ignored site configuration. Router capability, installed software versions and hardware health have not been independently verified.

| Input required | Why it blocks deployment |
| --- | --- |
| Proxmox version, trusted CA or independently verified host key, actual node/bridge/storage IDs | Identify the host and avoid altering the wrong resource |
| Available VM/template IDs, Ubuntu image checksum, SSH public key, guest DHCP reservation | Prepare a specific clone plan without collisions or invented values |
| QNAP QTS version, existing shares, free space, dedicated export paths and numeric ownership | Version reported by the operator and recorded locally; authenticated verification and application export paths/ownership remain pending. The operator supplied capacity screenshots and Plex library paths, recorded locally; keep Plex paths untouched. NFS refused connections; verify exports and preserve Plex/storage |
| Tailnet administrators, intended private service identities and current policy | Confirm access boundaries without changing the existing tailnet |
| Reviewed CLI versions and provider login choices | Reproducible Codex/OpenCode installs and controlled costs |
| Hermes provider/model, spend ceiling, Telegram identity and permitted tools | Configure the installed dormant assistant without granting broad tools or unbounded spend |
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
| 5. Backup and recovery | Prepared proposals and procedures retained for reference | Outside current scope until the operator requests QNAP backups; no backup or restore is verified |
| 6. Private application VM | Resource review and per-service pattern below; Paperless first | Explicit provisioning/app approval; health, unauthorized-access rejection, NAS-loss and restore tests pass |
| 7. Disposable workers | Implement dispatcher and worker lifecycle from `agents/workflows/issue-to-pr.md` on a disposable test repository | Hostile-input, token scope/expiry, timeout, management-route blocking and cleanup tests pass before activation |

Check mode and source validation do not authorize applying a plan. Reconfirm SSD free space and peak RAM before each additional VM. Do not allocate all proposed services at once.

## Service and coding-tool preparation

Codex and OpenCode have a version-controlled installer and unprivileged account; the pinned releases are installed. Hermes's pinned, reviewed CLI is now installed dormant under its own non-sudo account. Provider authentication, messaging activation and tool policy remain separate gates; see [private access and provider setup](private-access.md). Do not grant a messaging token before those controls are reviewed. An interactive trusted-operator VM and unattended issue worker have different trust boundaries.

Paperless has an initial Compose implementation; it is not running. Inactive n8n files were staged previously, but self-hosted n8n is now outside scope until the operator requests it. Immich and selected media applications should use the [reusable service contract](../compose/README.md), their own runbook and the then-current official upstream Compose baseline. Those later stacks are planned, not implemented or validated. Do not invent image tags, hardware-acceleration paths or NAS exports just to produce runnable YAML.

The worker dispatcher remains a design rather than an enabled automation. Use immutable approved source references, single-use workers, narrow expiring credentials and a separate PR publisher. Keep deployment credentials outside workers; test isolation before giving workers issue content. Source PR merge authorization never authorizes production deployment.

## Next operator review

Supply the remaining site inventory above, then review the trusted read-only inventory results and a specific VM/template plan. Infrastructure execution stays paused until explicit approval. Follow [installation](install.md) for commands and [validation](validation.md) for post-change evidence.
