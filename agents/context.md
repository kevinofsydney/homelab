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
| Proxmox and development VM | Template procedure, API provisioner and Ansible roles exist; operator reports Proxmox installed; intended endpoint responds on TCP 22/8006 | TLS identity, installed node inventory, template creation, VM boot and guest SSH remain unverified |
| Coding tools | Installer prepares local Codex and OpenCode 2 binaries under the unprivileged `coder` account | Exact versions, supported provider login and actual CLI execution need operator setup and testing |
| Storage and backups | QNAP mount role, exact-export checks, backup scripts and recovery instructions exist | Actual exports, UID/GID permissions, capacity, successful backup and isolated restore remain unverified |
| Network and bot protection | Required policy is documented in [network](../docs/network.md) and [bot protection](../docs/bot-protection.md) | No network isolation, Cloudflare configuration or bot controls have been deployed or verified by this project |
| Applications and workers | Paperless Compose is staged; later services and issue-to-PR workflow are documented | Paperless is not live; other application stacks, autonomous workers and the public web app app are later work |

## Next useful work

The operator now reports Proxmox installed, node `pve1`; this is reported state, not authenticated inventory. Read [the first implementation plan](../docs/implementation-plan.md) for missing inputs and approval gates. The requested original `docs/homelab-blueprint.md` is absent. On 2026-10-27, the intended management endpoint responded on TCP 22/8006, but TLS trust verification failed. QNAP address is unknown and no NAS probe occurred. No infrastructure changes were executed. `scripts/check-connectivity.py` now provides bounded read-only TCP/TLS checks without needing the full provisioning inventory. Later service stacks follow [the reusable contract](../compose/README.md); only Paperless currently has Compose source. Hermes identity is unresolved.

Local validation for this preparation: `python3 -m unittest discover -s tests -v` passed all 14 tests (including four mocked connectivity checks); `git diff --check` passed. These tests do not validate live service identity, QNAP export access or running infrastructure. The GitHub source workflow provides the full parsing, Ansible and Compose checks on the PR head.

Complete the [hardware/network preflight](../docs/preflight.md) and [ordered installation](../docs/install.md) when the Dell and real site values are available. Obtain the Proxmox address/node/bridge/storage IDs, trusted CA, SSH public key, QNAP export identity and permissions. Keep these values in ignored site/inventory files; do not put credentials in this context file.

After provisioning, verify the `coder` account has no sudo or Docker access, verify management destinations are blocked, then test a QNAP backup and isolated restore. Record evidence before declaring the first milestone complete. The [validation guide](../docs/validation.md) defines the remaining acceptance checks.

Before developing the public web app app, confirm the the accounting system product/export format, categories and final hosting. Before any public ingress, choose and test the authentication and abuse controls in `docs/bot-protection.md`. Cloudflare feature and plan availability must be checked at implementation time.
