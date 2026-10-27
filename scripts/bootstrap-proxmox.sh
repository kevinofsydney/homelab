#!/usr/bin/env bash
# Run on the verified Proxmox host. Never alters an existing guest or host networking.
set -euo pipefail
[[ $# -eq 0 || ( $# -eq 1 && "$1" == --apply ) ]] || { echo 'Usage: bootstrap-proxmox.sh [--apply]' >&2; exit 2; }
: "${PVE_NODE:?Set verified node name}"
: "${PVE_STORAGE:?Set verified VM storage ID}"
: "${PVE_BRIDGE:?Set verified existing bridge}"
: "${TEMPLATE_ID:?Set available template ID}"
: "${DEV_VM_ID:?Set available guest ID}"
: "${SSH_PUBLIC_KEY_FILE:?Set existing public key file on this host}"
: "${UBUNTU_IMAGE_URL:?Set official dated Ubuntu image URL}"
: "${UBUNTU_IMAGE_SHA256:?Set reviewed published SHA256}"
for name in "$PVE_NODE" "$PVE_STORAGE" "$PVE_BRIDGE"; do
  [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || exit 2
done
[[ "$TEMPLATE_ID" =~ ^[1-9][0-9]{2,8}$ && "$DEV_VM_ID" =~ ^[1-9][0-9]{2,8}$ && "$TEMPLATE_ID" != "$DEV_VM_ID" ]] || exit 2
[[ "$UBUNTU_IMAGE_URL" =~ ^https://cloud-images\.ubuntu\.com/noble/[0-9]{8}/noble-server-cloudimg-amd64\.img$ ]] || exit 2
[[ "$UBUNTU_IMAGE_SHA256" =~ ^[a-f0-9]{64}$ ]] || exit 2
[[ -f "$SSH_PUBLIC_KEY_FILE" ]] || exit 2
ssh-keygen -lf "$SSH_PUBLIC_KEY_FILE" >/dev/null || exit 2
[[ "$(hostname -s)" == "$PVE_NODE" ]] || exit 2
ip link show "$PVE_BRIDGE" >/dev/null
pvesm status --storage "$PVE_STORAGE"
for vmid in "$TEMPLATE_ID" "$DEV_VM_ID"; do
  available=$(pvesh get /cluster/nextid --vmid "$vmid") || exit 2
  [[ "$available" == "$vmid" ]] || exit 2
done
echo "PLAN: new Ubuntu template $TEMPLATE_ID and dev VM $DEV_VM_ID on $PVE_STORAGE/$PVE_BRIDGE; 4 cores, 8192 MiB, 100 GiB, DHCP, no autostart."
[[ "${1:-}" == --apply ]] || { echo 'PLAN ONLY; no writes made.'; exit 0; }
cache=$(mktemp -d /var/tmp/homelab-image.XXXXXXXX)
trap 'rm -f "$cache/ubuntu.img"; rmdir "$cache"' EXIT
curl --fail --location --proto '=https' --proto-redir '=https' --tlsv1.2 "$UBUNTU_IMAGE_URL" -o "$cache/ubuntu.img"
printf '%s  %s\n' "$UBUNTU_IMAGE_SHA256" "$cache/ubuntu.img" | sha256sum --check --status
# Recheck IDs after the download; partial failures deliberately remain for inspection.
for vmid in "$TEMPLATE_ID" "$DEV_VM_ID"; do
  available=$(pvesh get /cluster/nextid --vmid "$vmid") || exit 2
  [[ "$available" == "$vmid" ]] || exit 2
done
qm create "$TEMPLATE_ID" --name ubuntu-2404-cloud-template --memory 2048 --cores 2 --cpu host --net0 "virtio,bridge=$PVE_BRIDGE,firewall=1" --scsihw virtio-scsi-single --onboot 0
qm disk import "$TEMPLATE_ID" "$cache/ubuntu.img" "$PVE_STORAGE" --target-disk scsi0
qm set "$TEMPLATE_ID" --ide2 "$PVE_STORAGE:cloudinit" --boot order=scsi0 --serial0 socket --vga serial0 --agent enabled=1
qm template "$TEMPLATE_ID"
qm clone "$TEMPLATE_ID" "$DEV_VM_ID" --full 1 --name dev --storage "$PVE_STORAGE"
qm set "$DEV_VM_ID" --cores 4 --memory 8192 --ciuser devops --sshkeys "$SSH_PUBLIC_KEY_FILE" --ipconfig0 ip=dhcp --ciupgrade 0 --onboot 0
qm disk resize "$DEV_VM_ID" scsi0 100G
echo "Created VM $DEV_VM_ID stopped. Review qm config; start separately with qm start after attaching a console for first-boot evidence."
