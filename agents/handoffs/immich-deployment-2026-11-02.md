# Immich deployment: interrupted 2026-11-02

The owner authorized a dedicated Immich VM, a dedicated QNAP share and private access. This is an incomplete deployment. Site addresses and credentials belong only in ignored inventory or on the guest, never in this handoff.

## Observed

- VM 120 was cloned from the existing template with 4 vCPU, 8 GiB RAM and an 80 GiB thin disk; autostart was left disabled and it has not been added to the existing VM backup job.
- The owner made the VM's DHCP reservation; router UI showed the reservation enabled. Tailscale enrollment succeeded under the owner's identity. Docker and the NFS client were installed on the guest.
- A new QNAP share was created; NFS export listing showed it restricted to the VM's reserved address. The guest mounted that exact export using NFSv4.0, and the configured non-root service identity created a restricted `library` directory there. Existing QNAP shares were not changed.
- The local SSD directories and private guest `.env` were prepared. The deployment script's plan passed its mount, private address, local filesystem and Compose checks. Starting the pinned images was initiated, but connectivity was lost during downloads; the outcome is unknown. No photos were imported by this deployment.
- The router and QNAP NFS port remained reachable, whereas connections to the host and VMs failed. This does not establish the cause. The host has a previously recorded NIC issue; diagnose rather than assume.

## Resume safely

1. Restore and verify host/guest connectivity with the owner. Inspect VM state, Docker containers and logs, disk space, mount identity and image pull status before retrying anything. Do not re-create the VM, share, account, private `.env` or library directory.
2. The mounted export is currently temporary: no persistent automount or Immich systemd unit has been installed. Containers have `restart: no`; a prepared unit exists in `systemd/` but is not evidence of deployment. Verify the exact mount gate and private bind, configure and test controlled boot recovery, then enable VM autostart only after validation.
3. Include the VM in an appropriate backup job and verify a successful backup and restore. VM backups alone do not back up the NFS photo library. Arrange independently recoverable copies of both database and original photos, including an off-NAS copy, and test recovery. Do not alter backup retention without explicit approval.
4. Verify all containers, local-only LAN exposure, authorized tailnet access and an identity-specific synthetic upload. Have the owner create the administrator account and use the mobile app only after the backup limitations are understood. Test NAS loss and restart fail-closed behavior before declaring the service reliable.

The Compose configuration and deployment gate are prepared and need live runtime validation. NFS uses the NAS's supported v4.0, not v4.1. The project requires exact source verification before app starts and forbids creating a missing mount point as a fallback destination.
