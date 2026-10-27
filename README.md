# Homelab infrastructure

Reproducible starting point for a single Dell OptiPlex Proxmox host. The first milestone is one Ubuntu development VM, private CLI access, and a verified QNAP backup target. Application stacks are staged separately. Nothing in this repository deploys when cloned.

## Start here

1. Read [the installation guide](docs/install.md), [preflight checklist](docs/preflight.md) and [architecture decisions](docs/architecture.md).
2. Fill `config/site.example.json` as `config/site.json`. Fill no example with real secrets. `config/site.json` is ignored.
3. On a trusted laptop with Python 3.10+, run `python scripts/preflight.py --config config/site.json`. This performs read-only local checks.
4. Install Proxmox manually and build the Ubuntu cloud-image template using `proxmox/template.md`.
5. Export the Proxmox token and run `python scripts/provision_vm.py --config config/site.json` to inspect the plan. `--apply` is an explicit infrastructure change and requires your approval.
6. After VM boot, install local Ansible dependencies with `bash scripts/bootstrap-ansible.sh`, then run the playbook as shown in `docs/install.md` with `--check --diff`. Apply only after review.
7. Configure QNAP backups and complete a restore test before deploying applications.

`docs/install.md` has the full sequence, commands, checkpoints, and recovery steps.

The GitHub repository is private. Continue keeping actual inventory and secrets outside Git. Source validation runs in GitHub Actions; see [validation and hardware acceptance](docs/validation.md) for what those checks prove and what must be tested on the Dell.

## Repository map

- `config/`: example site configuration; actual configuration is ignored.
- `proxmox/`: template procedure and VM definition.
- `ansible/`: development VM configuration.
- `compose/paperless/`: first private application stack, gated on its NAS mount.
- `scripts/`: preflight, provisioning, deployment and backup validation.
- `docs/`: architecture, security, storage, recovery and upstream source notes.
- `agents/`: permission boundaries and issue-to-PR design.

## Boundaries

No secrets in Git. Production deployment, firewall/network changes, NAS share creation, hypervisor operations and software installed with elevated privileges require explicit review and approval. No BinaryLane migration, QNAP Plex changes, public ingress or public web app user launch is included.
