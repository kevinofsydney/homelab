# `nic0` offload mitigation

Source artifacts for the [e1000e hang mitigation](../../docs/proxmox-nic-recovery-plan.md). Status and evidence live in [todo 3](../../agents/todo.md). Copying, enabling or arming these on the host requires the owner's explicit approval.

| Command | Effect |
| --- | --- |
| `homelab-nic-offload check` | Read-only: prints driver-checked settings, the recorded baseline and unit state |
| `homelab-nic-offload arm` | Records the baseline, enables the rollback timer and checks it, then enables and applies the candidate. The 2026-11-02 run logged no link drop, but allow for a brief interruption |
| `homelab-nic-offload ack` | Cancels the rollback. Refuses unless the candidate is active with all three offloads off |
| `homelab-nic-offload rollback` | Restores the recorded baseline and disables the candidate and the timer. The timer runs this 30 minutes after arming and after each boot until acknowledged |

## Deployment

Run on the host, from a local console or SSH, after the prerequisites in the plan:

```bash
install -m 755 homelab-nic-offload.py /usr/local/sbin/homelab-nic-offload
install -m 644 homelab-nic-offload.service homelab-nic-offload-rollback.service homelab-nic-offload-rollback.timer /etc/systemd/system/
systemctl daemon-reload
systemd-analyze verify homelab-nic-offload.service homelab-nic-offload-rollback.service homelab-nic-offload-rollback.timer
homelab-nic-offload check
homelab-nic-offload arm
```

Check connectivity, reboot, then repeat `check` and the plan's service checks inside the 30-minute window before running `ack`. An unacknowledged reboot gets a fresh 30 minutes, including one caused by the [scheduled host maintenance](../automatic-maintenance/README.md).

## Recovery from the console

If the host is reachable only at its console, and the timer has not already recovered it:

```bash
homelab-nic-offload rollback
```

If that fails, run `systemctl disable homelab-nic-offload.service homelab-nic-offload-rollback.timer`, then set the values in `/var/lib/homelab-nic-offload/baseline.json` with `ethtool -K nic0 tso <value> gso <value> gro <value>`.

## Tests

Run `python3 test_nic_offload.py` from this directory. The tests mock `ethtool` and `systemctl`; they do not prove behavior on the host or that the hang is fixed.
