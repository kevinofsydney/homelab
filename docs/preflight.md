# Hardware and network preflight checklist

Record results before creating the first VM. `scripts/preflight.py` checks configuration syntax; the following checks require the operator on site.

Before full site configuration is available, run the unauthenticated read-only connectivity probe:

```sh
python3 scripts/check-connectivity.py --proxmox-host <intended-host> --ca-file <trusted-ca.pem> --qnap-host <confirmed-nas-host>
```

It checks only Proxmox TCP 22/8006, verified management TLS and QNAP TCP 2049. Omit `--ca-file` to use the system trust store. Omit `--qnap-host` if unknown; the result then remains incomplete and exits nonzero. Each connection has a bounded timeout. No scanning, authentication, mounting or writes occur. Open ports do not prove node identity, NFS export access, ownership, capacity or restore behavior. A closed NFS port is not a reason to enable it without approval. Obtain a trusted CA/host identity before authenticated inventory; never bypass TLS checks. See the dated observations and missing inputs in [the implementation plan](implementation-plan.md).

- [ ] Dell model/CPU/RAM/SSD match the brief; run a memory test and inspect SSD SMART data.
- [ ] BIOS virtualization enabled; firmware updated from a trusted source.
- [ ] Ethernet link stable; router DHCP reservation made for the Proxmox host and planned VM.
- [ ] Proxmox management reachable only from trusted devices; MFA enabled; no public port forward.
- [ ] Proxmox node, bridge and storage IDs recorded from the live host.
- [ ] At least 20% local SSD free after template and first VM; no backups targeting the SSD by mistake.
- [ ] QNAP free capacity verified; existing Plex playback and shares checked before and after new exports.
- [ ] Dedicated NFS export for backup with only intended client access; QNAP firmware and account access reviewed.
- [ ] Backup share read/write probe succeeds; backup and isolated restore test scheduled.
- [ ] UPS/power-loss behavior documented for Dell and QNAP.
- [ ] Trusted laptop can SSH to the development VM with a key; rejected login from an untrusted device verified after network policy is applied.
- [ ] Development VM cannot reach Proxmox/QNAP/router management interfaces once isolation rules are applied.

Record date, firmware versions, capacity, mount/export identity and restore test result in a private operations log. Do not commit private addresses or credentials.
