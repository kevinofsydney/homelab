# Development VM bootstrap and verification

## Scope and authorization

On 2026-10-27, the operator explicitly approved creating the Ubuntu template, development VM and guest tools. The operator added the laptop's public key through the Proxmox console after providing its SSH fingerprint. This authorizes this development bootstrap, not public ingress, host network/disk-layout changes, QNAP changes or production deployment. The SSH bootstrap runs only from the trusted operator laptop; no hypervisor credential is copied to a guest or worker.

The host-side script is an alternative to the API-token provisioner for this initial trusted bootstrap. No Proxmox token or automation user was created. Later repeated provisioning should use the reviewed narrowly scoped API workflow. Keep the trusted host key, CA, actual addresses and inventory in ignored local files. A new operator must verify identity rather than trust another session's assertions.

## Repeat on a new, approved host

1. Verify console SSH fingerprint, node, bridge, active image storage, free capacity and both unused VM IDs. Check current PRs and repository instructions. Do not rerun against deployed IDs.
2. Download the dated official Ubuntu 24.04 image checksum over verified HTTPS. Record the date, URL and SHA256 before execution. Copy only the SSH public key and this script to the verified host; no private key is copied.
3. On the host export `PVE_NODE`, `PVE_STORAGE`, `PVE_BRIDGE`, `TEMPLATE_ID`, `DEV_VM_ID`, `SSH_PUBLIC_KEY_FILE` (host-local public-key path), `UBUNTU_IMAGE_URL` and `UBUNTU_IMAGE_SHA256`. Actual values belong in ignored site configuration or the operator environment. Image URL must use the official dated `noble/YYYYMMDD/` path.
4. Run `bash /path/to/bootstrap-proxmox.sh` to inspect the plan. After explicit approval, run with `--apply`. It creates new guests only, verifies the image hash before import, uses host CPU features and leaves the guest stopped with autostart disabled. Check at least 20% SSD headroom for the planned allocation and growth, not just current thin-pool physical use. Partial failure requires inspection; no automatic guest deletion or rollback occurs.
5. Inspect `qm config <new-vmid>`, start the approved guest, and attach `qm terminal <new-vmid>` immediately. Cloud-init prints the DHCP address and SSH host key. Capture/verify those through the trusted host console before guest SSH. Exit the console with Ctrl+O. Never use an unverified keyscan as proof of identity.
6. Fill ignored Ansible inventory with the observed address, `devops`, existing local SSH key and verified known-hosts path. Confirm independent key login and `sudo -n true`. A fresh cloud image may have an empty package index: refresh it with approved `sudo apt-get update` before first check mode. This does not upgrade the guest or host.
7. Run the development playbook with `--check --diff`, review output, then apply within the approved guest scope. First-run check mode skips service/directory steps that depend on packages/users not yet created. A successful apply and a subsequent zero-change check are required evidence. Ansible caches, temporary files and SSH control sockets stay under repository `.local/`.
8. As `coder`, export the four variables in [the reviewed CLI release manifest](../config/ai-cli-versions.json) and run `~/.local/ai-tools/install-ai-cli.sh`. The manifest is public release metadata, not site inventory. All Node/npm assets stay in that account's `.local/ai-tools`. Verify versions in a fresh `sudo -iu coder` login. Do not install these tools as root or add `coder` to sudo/Docker groups.

Use the commands in [installation](install.md) for Ansible and the official [Codex CLI](https://learn.chatgpt.com/docs/codex/cli) and [OpenCode 2](https://dev.opencode.ai/v2/docs/) documentation for supported interactive login. Logins and a model-backed smoke test require the operator's account; no session files are copied from the laptop. Do not assume subscription/API entitlement.

## Dated deployment evidence

2026-10-27: verified SSH host identity against the operator's console fingerprint. Host reports Proxmox VE 9.2.2, i5-12500T, 31,784 MiB RAM, a 512 GB Micron NVMe and active directory/LVM-thin storage. No VMs existed before bootstrap; both chosen IDs were available. Hardware health testing, BIOS audit and power-loss/UPS testing remain pending.

Created template VM 9000 and development VM 100 (`dev`), 4 vCPU, 8192 MiB RAM, 100 GiB virtual disk, existing bridge, DHCP and autostart off. Ubuntu image: `https://cloud-images.ubuntu.com/noble/20261017/noble-server-cloudimg-amd64.img`, SHA256 `04e8f2461a16a44e78a370284471f29616cdd9baf1893df25807b71f985b6c94`. Guest reports Ubuntu 24.04.5 LTS. Cloud-init completed; root filesystem expanded to about 96 GiB usable. Guest host key was obtained through the verified serial console, then key login and administrative sudo were verified.

Ansible baseline applied successfully. Guest-agent ping and network inventory work through Proxmox. `coder` has only its own group, no sudo and no Docker socket access. Effective guest SSH configuration disables root/password/keyboard-interactive login and allows `devops`. Host management TLS now verifies using the public CA obtained over fingerprint-verified SSH. No certificate bypass is needed.

The first OpenCode install failed with the default Common KVM processor. Its installer checks native binary execution; the guest lacked modern CPU instructions. Host CPU passthrough was applied to the new template/VM and the development VM was gracefully restarted before retrying. No host networking, existing disk layout or NAS configuration was altered. This is a single-host choice; review CPU compatibility before migration to other hardware.

The retry installed Node 24.22.1, Codex CLI 0.164.0 and OpenCode 2.1.4 successfully. Version commands and PATH lookup passed in a fresh `coder` login session. `codex login status` reports `Not logged in`, as expected before operator sign-in. These are binary smoke tests, not authenticated model tests.

Final live Ansible check: `ok=11 changed=0 failed=0`. Local source validation: 17 safety tests, 15 parsed JSON/YAML files, Bash syntax, both Ansible playbook syntax checks and whitespace checks passed. The initial dry-run failed on the fresh image's empty package index; an approved index refresh fixed that. First-run check mode now skips service/filesystem operations whose packages or account do not yet exist, while the subsequent live check covers every task without skips.

## Remaining gates

Provider sign-in and authenticated CLI smoke tests, Hermes activation/Telegram policy, Tailscale enrollment/policy, management-route isolation, DHCP reservation, guest security-update review, QNAP inventory, backup and isolated restore are not complete. QNAP backups are explicitly deferred by the operator. [Private access preparation](private-access.md) records the subsequently installed Tailscale client and dormant pinned Hermes CLI. Do not treat this guest as an isolated unattended worker or store irreplaceable/production data here. There is no validated backup yet. Proxmox autostart is enabled for both guests and was verified with a full host reboot on 2026-10-27; inspect service health after any reboot rather than assuming it. Later apps still require their separate approval and acceptance checks.
