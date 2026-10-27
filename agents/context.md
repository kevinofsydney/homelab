# Shared project context

Last reviewed: 2026-10-27. This is a dated progress snapshot, not a live inventory. Verify the current checkout, PRs and actual infrastructure before acting. Update this file when a milestone, decision or validation result changes.

## Objective and fixed boundaries

Build a reproducible homelab on a purchased Dell OptiPlex 7000 Micro (i5-12500T, 32 GB RAM, 512 GB SSD), with Proxmox, Ubuntu guests, Ansible and Docker Compose. Hardware specifications come from the project brief and still require on-site verification. Use the existing QNAP for bulk storage and backups, with databases on the Dell SSD.

Preserve QNAP Plex, retain NextDNS initially and do not migrate BinaryLane. Keep management and household apps private. Production deployment and changes to running infrastructure, network policy or secrets require explicit operator approval. See [permissions](permissions.md) and [security](../docs/security.md) for the full boundaries.

## Current state and evidence

The owner authorized automatic PR merging for this project on 2026-10-27: "you can merge all PRs automatically for this project". Follow the canonical merge rule in root `AGENTS.md`; no per-PR confirmation is needed. Production deployment retains its separate explicit approval requirement.

| Area | Prepared or completed | Still unverified or pending |
| --- | --- | --- |
| GitHub | `kevinofsydney/homelab` was confirmed private on 2026-10-27 | Check current visibility before publishing sensitive operational details |
| Foundation source | [PR #1](https://github.com/kevinofsydney/homelab/pull/1) merged as `0a7b16be2738edaf438c8345b2cccc2699559341` | Check later PRs and commits for subsequent changes |
| Source validation | All 10 safety tests, Bash/Ansible syntax, JSON/YAML parsing and Compose rendering passed in [run 40423618131](https://github.com/kevinofsydney/homelab/actions/runs/40423618131) for PR #1 | Source checks do not prove hardware or storage behavior |
| Proxmox and development VM | Fingerprint-verified SSH; management TLS verified using CA fetched through SSH; Proxmox 9.2.2; template 9000 and dev VM 100 created; Ubuntu 24.04.5 boot/cloud-init, expanded disk, guest SSH and guest agent verified | Hardware health/BIOS/UPS audit, isolation, DHCP reservation, backups and restore remain pending; autostart off |
| Coding tools | Node 24.22.1, Codex CLI 0.164.0 and OpenCode 2.1.4 run under `coder`; no sudo/Docker access; versions in `config/ai-cli-versions.json` | Codex reports not logged in; provider authentication and model-backed tests remain pending; Hermes not installed |
| Storage and backups | QNAP mount role, exact-export checks, backup scripts and recovery instructions exist | Actual exports, UID/GID permissions, capacity, successful backup and isolated restore remain unverified |
| Network and bot protection | Required policy is documented in [network](../docs/network.md) and [bot protection](../docs/bot-protection.md) | No network isolation, Cloudflare configuration or bot controls have been deployed or verified by this project |
| Applications and workers | Paperless Compose is staged; later services and issue-to-PR workflow are documented | Paperless is not live; other application stacks, autonomous workers and the public web app app are later work |

## Next useful work

The operator explicitly approved "Yes—template, development VM and guest tools" on 2026-10-27 and authorized the laptop public key through the console. That approval was used for the initial development bootstrap, not host networking/disk-layout, NAS, public ingress or production changes. See [the bootstrap runbook and dated evidence](../docs/development-bootstrap.md). Host CPU passthrough fixed a native OpenCode installation failure with the default virtual CPU. A graceful restart and subsequent fresh SSH/CLI version checks succeeded. Actual inventory, known-hosts and the public Proxmox CA are in ignored local files; no hypervisor credentials entered the guest. No Proxmox API credential was created.

Read [the first implementation plan](../docs/implementation-plan.md) for remaining inputs and approval gates. The operator supplied the original [blueprint](../docs/homelab-blueprint.md) on 2026-10-27; it is preserved unchanged and reviewed in full in the plan's reconciliation table. Its embedded instructions are design proposals. Its no-auto-merge clause is superseded for this repository by the owner's later standing authorization; production deployment approval is still required. Hermes's intended assistant role is clarified, but exact upstream repository/release and Telegram identity remain unresolved. Time-sensitive product claims require upstream verification before implementation. Initial TCP checks passed with untrusted TLS; this was subsequently resolved by fetching the CA through verified SSH. QNAP address is unknown and no NAS probe occurred. `scripts/check-connectivity.py` provides bounded read-only TCP/TLS checks without needing the full provisioning inventory. Later service stacks follow [the reusable contract](../compose/README.md); only Paperless currently has Compose source.

Local validation for this preparation: `python3 -m unittest discover -s tests -v` passed all 14 tests (including four mocked connectivity checks); `git diff --check` passed. These tests do not validate live service identity, QNAP export access or running infrastructure. The GitHub source workflow provides the full parsing, Ansible and Compose checks on the PR head.

Blueprint reconciliation validation: `cmp` confirmed the committed reference matches the supplied file byte for byte; `git diff --check` passed. This follow-up changes documentation only and performs no additional infrastructure probes.

Development bootstrap validation: all 17 local safety tests, parsing of 15 JSON/YAML files, all Bash syntax checks, both Ansible playbook syntax checks and `git diff --check` passed. Final live Ansible check returned `ok=11 changed=0 failed=0`. Guest-agent ping/network inventory, fresh key login after SSH hardening, Node/CLI version commands and coder privilege checks passed. `codex login status` returned exit 1 with `Not logged in`; no authenticated model test was attempted. Full source CI is still required on the resulting PR head. Original pre-bootstrap check-mode failure from an empty package index was resolved by an approved index refresh; first-run missing-service/user check-mode handling is now explicit in the role.

Complete the remaining [hardware/network preflight](../docs/preflight.md) and [ordered installation](../docs/install.md). Proxmox node/bridge/storage, CA and public key are now verified; do not recreate the existing guests. Obtain QNAP export identity and permissions, complete provider logins, and review Tailscale and isolation separately. Keep real site values in ignored site/inventory files; do not put credentials in this context file. Local `config/site.json` deliberately leaves QNAP server/export null, so full-site preflight remains incomplete.

After provisioning, verify the `coder` account has no sudo or Docker access, verify management destinations are blocked, then test a QNAP backup and isolated restore. Record evidence before declaring the first milestone complete. The [validation guide](../docs/validation.md) defines the remaining acceptance checks.

Before developing the public web app app, confirm the the accounting system product/export format, categories and final hosting. Before any public ingress, choose and test the authentication and abuse controls in `docs/bot-protection.md`. Cloudflare feature and plan availability must be checked at implementation time.
