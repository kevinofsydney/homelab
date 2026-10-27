# Homelab infrastructure

Reproducible starting point for a single Dell OptiPlex Proxmox host. The first milestone is one Ubuntu development VM, private CLI access, and a verified QNAP backup target. Application stacks are staged separately. Nothing in this repository deploys when cloned.

## Start here

Read [the supplied blueprint](docs/homelab-blueprint.md) with [the first implementation plan](docs/implementation-plan.md) for its reconciliation, current gaps, connectivity evidence and approval gates. The blueprint is a design reference; current repository safety rules and explicit operator authorization govern execution.

The initial development VM has been created under explicit operator approval. Read [its bootstrap evidence and remaining gates](docs/development-bootstrap.md) before provisioning; do not recreate existing guests. Backups, isolation and application deployment are still pending.

A separate [home-services VM](docs/application-vm.md) now has Docker packages and a private n8n configuration staged. Docker network activation and the first container remain pending explicit firewall-change approval.

For any coding agent, read [AGENTS.md](AGENTS.md), the [agent collaboration guide](agents/README.md) and [shared project context](agents/context.md) first. The repository is the durable source of context across tools, sessions and contributors.

1. Read [the installation guide](docs/install.md), [preflight checklist](docs/preflight.md) and [architecture decisions](docs/architecture.md).
2. Fill `config/site.example.json` as `config/site.json`. Fill no example with real secrets. `config/site.json` is ignored.
3. On a trusted laptop with Python 3.10+, run `python scripts/preflight.py --config config/site.json`. This performs read-only local checks.
4. Install Proxmox manually and build the Ubuntu cloud-image template using `proxmox/template.md`.
5. Export the Proxmox token and run `python scripts/provision_vm.py --config config/site.json` to inspect the plan. `--apply` is an explicit infrastructure change and requires your approval.
6. After VM boot, install local Ansible dependencies with `bash scripts/bootstrap-ansible.sh`, then run the playbook as shown in `docs/install.md` with `--check --diff`. Apply only after review.
7. QNAP backup setup is deferred at the operator's request on 2026-10-27. Continue development access/tool setup using [the private-access guide](docs/private-access.md); backup and restore acceptance remain unfinished.

`docs/install.md` has the full sequence, commands, checkpoints, and recovery steps.

The GitHub repository is private. Continue keeping actual inventory and secrets outside Git. Source validation runs in GitHub Actions; see [validation and hardware acceptance](docs/validation.md) for what those checks prove and what must be tested on the Dell.

## Repository map

- `config/`: example site configuration; actual configuration is ignored.
- `proxmox/`: template procedure and VM definition.
- `ansible/`: guest baseline plus separate private-access and dormant assistant-tool playbooks.
- `compose/paperless/`: first private application stack, gated on its NAS mount.
- `compose/n8n/`: loopback-only private n8n stack, staged without starting containers.
- `scripts/`: preflight, provisioning, deployment and backup validation.
- `docs/`: architecture, security, storage, recovery and upstream source notes.
- `agents/`: permission boundaries and issue-to-PR design.
- [Bot protection](docs/bot-protection.md): required private-service boundaries and future public-ingress controls.

## Boundaries

No secrets in Git. Production deployment, firewall/network changes, NAS share creation, hypervisor operations and software installed with elevated privileges require explicit review and approval. No BinaryLane migration, QNAP Plex changes, public ingress or public web app user launch is included.
