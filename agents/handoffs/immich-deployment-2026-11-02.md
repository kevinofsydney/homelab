# Immich deployment: 2026-11-02

The owner authorized a dedicated Immich VM, QNAP share and private access. Site addresses and credentials belong only in ignored inventory or on the guest, never in this handoff.

## Observed

- VM 120 has 4 vCPU, 8 GiB RAM and an 80 GiB thin disk. Its reserved address and Tailscale enrollment were confirmed. Proxmox autostart is enabled, and it was added to the existing scheduled VM backup job without changing retention.
- The dedicated QNAP NFSv4.0 export was restricted to the VM. The guest uses an exact-source mount gate and a separate service identity; originals are under `library` on the share, and the database, thumbnails, encoded video and model cache are on local SSD. The library root is mode 0711 so root-squashed Docker can traverse to the pre-created empty nested mount targets; application data directories remain owned by the service identity. Do not replace root squash with unrestricted root access.
- After image downloads were interrupted by the documented host NIC hang, the owner's separate NIC mitigation was deployed and the download resumed. All four pinned containers reported healthy, the Tailscale-bound page returned HTTP 200 locally, and a probe to the guest's LAN address failed. External client authorization and mobile upload remain unverified.
- The NFS automount, gated systemd startup service, and VM autostart were enabled. A guest reboot triggered the exact NFS mount and the gated service successfully started all four containers. A NAS-loss test remains outstanding. Container restart policies are disabled so a Docker restart cannot bypass the gate.
- An initial snapshot VM backup completed successfully on the existing QNAP backup target, without pruning. The archive passed `zstd -t` and restored to a stopped test VM; a read-only filesystem inspection found the app configuration, startup unit and PostgreSQL data directory. The temporary VM was removed. Database application-level recovery is not yet tested. The VM backup does not contain the NFS photo library. An independent photo backup and an off-NAS copy are still needed before the library should be relied upon. Do not change backup retention without explicit approval.

## Continue

Confirm administrator setup with the owner and private client access, then test a synthetic upload once backup expectations are clear. Test application-level database recovery, establish a separate independent original-photo backup with the owner, and test NAS-loss behavior. Continue the 24-hour NIC soak; a short clean workload does not prove the mitigation. Existing QNAP shares and Plex were not changed.
