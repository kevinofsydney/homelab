# Ordered installation guide

All commands that change Proxmox, QNAP, VM packages, network policy or services are operator-reviewed steps. The repository creates no infrastructure automatically.

## 1. Hardware and management

Verify RAM/SSD health, Intel virtualization in BIOS, firmware, Ethernet link, router DHCP reservation capability, UPS and QNAP free capacity. Install Proxmox from USB using its official installer. Record the actual node name, bridge, storage ID and management address. Apply updates and MFA through a trusted connection. Do not expose its web UI or SSH to the public internet. Confirm QNAP Plex remains healthy.

## 2. Site configuration and preflight

Copy `config/site.example.json` to ignored `config/site.json`; fill the real values. Use an existing SSH **public** key path. Run `python3 scripts/preflight.py --config config/site.json`. The script performs local validation only; complete its manual checks. No key or token belongs in Git.

## 3. Cloud template and VM

For the approved initial SSH bootstrap, see [development bootstrap](development-bootstrap.md). It records the exact procedure, deployed state and remaining gates. Do not recreate existing template/VM IDs or reinstall the host. The API path below remains the alternative for later narrowly scoped provisioning.

Follow `proxmox/template.md` on the Proxmox host. Download and checksum the official Ubuntu 24.04 cloud image. Create a dedicated Proxmox API token with reviewed minimal rights. On the trusted laptop:

```sh
export PVE_TOKEN_ID='<token-id>'
export PVE_TOKEN_SECRET='<secret>'
# For a private Proxmox CA, obtain its public CA certificate over a trusted path:
export PVE_CA_FILE='<absolute-path-to-trusted-proxmox-ca.pem>'
python3 scripts/provision_vm.py --config config/site.json
# After reviewing the plan and approving the change:
python3 scripts/provision_vm.py --config config/site.json --apply
unset PVE_TOKEN_ID PVE_TOKEN_SECRET PVE_CA_FILE
```

The script refuses an existing VM. Use the Proxmox console to confirm boot, DHCP lease, `cloud-init status --wait`, disk size and SSH access. Keep the VM on a private bridge/LAN segment. Restrict access at router/host level before treating it as isolated.

## 4. Guest baseline and AI CLIs

Copy `ansible/inventory/hosts.example.yml` to ignored `ansible/inventory/hosts.yml`; fill address/user/key. On a Linux or WSL operator environment with Python 3.12+, run `bash scripts/bootstrap-ansible.sh`. Check SSH host key out of band, then:

```sh
ANSIBLE_CONFIG=ansible/ansible.cfg .local/venv/bin/ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/development.yml --check --diff
# After reviewing changes and confirming an alternate SSH session:
ANSIBLE_CONFIG=ansible/ansible.cfg .local/venv/bin/ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/development.yml
```

On the VM, select an official Node.js Linux x64 tarball and SHA256 from the published checksum list, plus reviewed exact Codex and OpenCode 2 package versions. SSH as `devops`, then switch to the non-sudo `coder` account with `sudo -iu coder`. Ansible places the reviewed installer at `~/.local/ai-tools/install-ai-cli.sh`. Export `NODE_TARBALL_URL`, `NODE_SHA256`, `CODEX_VERSION`, `OPENCODE_VERSION`, `DSH_VERSION` and `DSH_SHA512`, then run that installer as `coder`. The DeepSeek Harness tarball is downloaded from the npm registry and verified against the pinned SHA-512 before npm installs it. Run the installer with `--check` to verify installed versions and launchers without changing files; this does not re-hash installed package contents. All CLI binaries live under that user's `~/.local/ai-tools`. Add its `node/bin` and `npm/node_modules/.bin` to PATH, sign in interactively and run a harmless test in a disposable repository. Codex and OpenCode subscription eligibility and models should be confirmed in their current product UI. Never copy session files into a worker. Hermes/Telegram is deferred until its maturity and permissions are reviewed.

The separate `private-access.yml` playbook installs the reviewed Tailscale client; [private access](private-access.md) describes its check/apply and interactive enrollment sequence with DNS and route acceptance disabled. Tailnet policy and LAN firewall restrictions remain separate reviewed changes. Do not enable a subnet router on the development VM. `assistant-tools.yml` prepares the pinned Hermes CLI under a separate non-sudo account; provider configuration and its messaging gateway remain disabled until their controls are reviewed. The earlier Hermes deferral above refers to activation; this optional CLI preparation is now documented in the private-access guide.

## 5. QNAP backup and restore

Superseded 2026-10-28: the owner requested backups and they are live. The current procedure, evidence and restore steps are in [Proxmox backups](proxmox-backups.md). The text below is the earlier proposal.

Create a dedicated NFS backup export; preserve Plex shares. Add it to Proxmox as backup storage. To configure it on the development VM, fill `qnap_backup_server` and `qnap_backup_export` in the ignored Ansible inventory, check `ansible/playbooks/qnap-backup-mount.yml` with `--check --diff`, then apply only after reviewing the network/storage change. The role writes a reviewed fstab entry; on the guest run `sudo mount /mnt/qnap-backups` and `scripts/validate-backup.sh /mnt/qnap-backups '<QNAP_HOST>:<BACKUP_EXPORT>'`. Configure a Proxmox backup schedule and restore a test VM as described in `docs/disaster-recovery.md`. Record results. Add encrypted off-NAS backup before storing irreplaceable data.

## 6. Private applications

The existing application VM runs Paperless and Uptime Kuma. Read the [Paperless handoff](../agents/handoffs/paperless-deployment.md), [Paperless runbook](../compose/paperless/README.md) and [Uptime Kuma runbook](../compose/uptime-kuma/README.md) before changing them. Both use private Tailscale bindings and separately enabled guest startup services; the Proxmox VM is enabled for host autostart and was verified through a host reboot on 2026-10-27. Check current container health and mount identity before any changes. QNAP backups and recovery testing remain outside scope until the operator requests them.
