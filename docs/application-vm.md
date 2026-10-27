# Home-services VM and n8n staging

**Current scope:** On 2026-10-27 the operator removed self-hosted n8n and QNAP backups from the current deployment and will raise them when ready. The existing inactive n8n files are retained as historical preparation; do not start the container or request its activation until the operator brings it back into scope. The VM and stopped Docker installation remain available for other separately approved application work.

## Current deployment

On 2026-10-27 the operator asked to continue deployment and deferred QNAP backups. A separate application VM was created from the existing verified Ubuntu template: VM 130, 2 vCPU, 4096 MiB RAM and 60 GiB virtual disk. Its guest is Ubuntu 24.04.5, cloud-init completed, the disk expanded, and the guest agent responds. The three approved operator public keys were provided through cloud-init; key-only `devops` SSH is enabled. VM autostart remains off. Its observed DHCP address and console-verified host key are in ignored site inventory and known-hosts files, not this document.

The clone script was run in plan mode before apply and checked an unused VM ID, existing template/bridge, approved keys and SSD capacity. The initial source image was 3.5 GiB; a subsequent improvement also verifies the template disk cannot exceed the target size and parses every input key before cloning. The clone remains a full independent virtual disk. The 20% SSD headroom test is an operational guard, not a storage reservation; thin-pool usage and future growth still need monitoring.

`application-baseline.yml` installed the guest agent and SSH restrictions. `stage-docker.yml` installed pinned Docker Engine/CLI, containerd and Compose packages from Docker's signed Ubuntu repository with package-service starts suppressed. It kept Docker's service and socket stopped and disabled. `stage-n8n.yml` staged the pinned n8n Compose file and a plan-by-default wrapper, with an initially empty local ext4 data directory. No n8n container has been created or started.

The QNAP address supplied by the operator is recorded in ignored configuration. Read-only TCP checks reached ports 443 and 445; TCP 2049 refused the connection. That confirms neither the QNAP's identity nor a usable export. No NAS settings, shares, backups or Plex data were changed. Paperless and Immich remain blocked on verified storage exports and permissions.

## Reviewable Docker activation

Docker's default Linux bridge setup creates network interfaces, forwarding behavior and firewall rules **inside the application VM**. Its [official documentation](https://docs.docker.com/engine/network/packet-filtering-firewalls/) describes those changes and notes that published ports can bypass ordinary UFW filtering. The project requires explicit approval before network/firewall changes. Future activation for an in-scope application needs a reviewed plan and explicit approval. The previous request to activate n8n is superseded by the operator's deferral.

If the operator later requests self-hosted n8n, review the pinned release and prepare a fresh plan before requesting any applicable approval. The retained n8n procedure binds only to loopback, and includes checks for local health, LAN access rejection and an operator SSH tunnel. Do not use Docker activation as authorization for future network, NAS or production changes. The staged Docker playbook refuses to stop an already-running daemon; do not rerun it after activation as a way to manage an active service.

See [n8n staging](../compose/n8n/README.md) for client access, owner setup, data placement and recovery limitations. n8n account creation and authenticated behavior remain unverified until the user completes setup.

## Source and site configuration

`scripts/clone-application-vm.sh` is plan-only unless given `--apply`. It runs on the verified Proxmox host using reviewed environment variables and approved public keys, refuses an existing VM ID, checks the source template/disk and capacity, and leaves the new guest stopped. Partial clone failures remain for operator inspection. `ansible/playbooks/application-baseline.yml`, `stage-docker.yml` and `stage-n8n.yml` configure the guest in distinct reviewable steps. The Docker playbook intentionally stages rather than activates networking. Actual inventory, IPs, keys and CA stay ignored.

Ubuntu image provenance is recorded in [development bootstrap](development-bootstrap.md). Docker package versions and key checksum are pinned in the role; the n8n image tag and registry digest are pinned in its Compose file. Review upstream releases and rollback/recovery before changing them. Never put private keys, generated n8n data or provider credentials in this repository.

## Verification evidence

The app guest's console host key was recorded before SSH; cloud-init completed and the root filesystem is ext4 with roughly 58 GiB usable. The guest agent ping passed. The three approved operator public keys are present; existing Mac key login and sudo worked after the SSH configuration change. Docker and Compose packages were installed; both Docker service and socket report inactive and disabled. Guest IPv4 forwarding was 0 before and after staging, and `iptables-save` showed no rules both times. The n8n wrapper's plan passed Compose rendering and confirmed ext4 `/dev/sda1` storage and a mode 0700 data directory owned by UID/GID 1000.

All three app guest playbooks returned zero changes in final check mode. Source tests and CI results are recorded in shared context. These checks do not establish that the Docker daemon, n8n image, owner login, SSH tunnel, QNAP storage or backup/restore works.
