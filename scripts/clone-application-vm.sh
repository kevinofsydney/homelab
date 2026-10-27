#!/usr/bin/env bash
# Run on the verified Proxmox host. Creates only a new, initially stopped guest.
set -euo pipefail
[[ $# -eq 0 || ( $# -eq 1 && "$1" == --apply ) ]] || { echo 'Usage: clone-application-vm.sh [--apply]' >&2; exit 2; }
: "${PVE_NODE:?Set verified Proxmox node}"
: "${PVE_STORAGE:?Set verified image storage}"
: "${PVE_BRIDGE:?Set existing bridge}"
: "${TEMPLATE_ID:?Set existing template ID}"
: "${APP_VM_ID:?Set an available VM ID}"
: "${APP_VM_NAME:?Set a reviewed guest name}"
: "${SSH_PUBLIC_KEYS_FILE:?Set host-local file containing approved public keys}"
for name in "$PVE_NODE" "$PVE_STORAGE" "$PVE_BRIDGE" "$APP_VM_NAME"; do
  [[ "$name" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || exit 2
done
[[ "$TEMPLATE_ID" =~ ^[1-9][0-9]{2,8}$ && "$APP_VM_ID" =~ ^[1-9][0-9]{2,8}$ && "$TEMPLATE_ID" != "$APP_VM_ID" ]] || exit 2
[[ -f "$SSH_PUBLIC_KEYS_FILE" ]] || exit 2
key_count=0
while IFS= read -r key || [[ -n "$key" ]]; do
  [[ -n "$key" ]] || continue
  printf '%s\n' "$key" | ssh-keygen -lf /dev/stdin >/dev/null || exit 2
  key_count=$((key_count + 1))
done < "$SSH_PUBLIC_KEYS_FILE"
(( key_count > 0 )) || exit 2
[[ "$(hostname -s)" == "$PVE_NODE" ]] || exit 2
ip link show "$PVE_BRIDGE" >/dev/null || exit 2
available=$(pvesh get /cluster/nextid --vmid "$APP_VM_ID") || exit 2
[[ "$available" == "$APP_VM_ID" ]] || exit 2
config=$(qm config "$TEMPLATE_ID") || exit 2
[[ "$config" == *$'\ntemplate: 1'* || "$config" == template:\ 1* ]] || { echo 'Not a template' >&2; exit 2; }
[[ "$config" == *cloudinit* && "$config" == *scsi0:* ]] || exit 2
[[ "$config" != *cicustom:* && "$config" != *hookscript:* ]] || exit 2
disk_volume=$(printf '%s\n' "$config" | awk -F ': ' '$1 == "scsi0" {split($2,a,","); print a[1]}')
[[ -n "$disk_volume" ]] || exit 2
disk_path=$(pvesm path "$disk_volume") || exit 2
disk_bytes=$(qemu-img info --output=json "$disk_path" | python3 -c 'import json,sys; print(json.load(sys.stdin)["virtual-size"])') || exit 2
[[ "$disk_bytes" =~ ^[0-9]+$ ]] && (( disk_bytes <= 60 * 1024 * 1024 * 1024 )) || { echo 'Template disk is larger than 60 GiB' >&2; exit 2; }
# Keep 20% of the thin-pool capacity after allowing for the full 60 GiB virtual disk.
pvesm status --storage "$PVE_STORAGE" | awk 'NR==2 { if ($3 != "active" || ($6 - 60*1024*1024) < ($4 * 0.20)) exit 1; seen=1 } END { if (!seen) exit 1 }' || { echo 'Insufficient reviewed storage headroom' >&2; exit 2; }
echo "PLAN: clone template $TEMPLATE_ID to $APP_VM_ID ($APP_VM_NAME); 2 vCPU, 4096 MiB, 60 GiB, DHCP, existing bridge $PVE_BRIDGE; leave stopped and autostart off."
[[ "${1:-}" == --apply ]] || { echo 'PLAN ONLY; no writes made.'; exit 0; }
qm clone "$TEMPLATE_ID" "$APP_VM_ID" --full 1 --name "$APP_VM_NAME" --storage "$PVE_STORAGE"
qm set "$APP_VM_ID" --cores 2 --memory 4096 --net0 "virtio,bridge=$PVE_BRIDGE,firewall=1" --ciuser devops --sshkeys "$SSH_PUBLIC_KEYS_FILE" --ipconfig0 ip=dhcp --ciupgrade 0 --onboot 0
qm disk resize "$APP_VM_ID" scsi0 60G
echo "Created VM $APP_VM_ID stopped. Inspect configuration; capture the serial console when starting it."
