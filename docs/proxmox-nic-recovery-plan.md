# Proxmox e1000e hang: proposed mitigation

Status: **not deployed**. A prior short, temporary test of disabling TSO, GSO and GRO succeeded and was rolled back; it did not prove that the intermittent hang was fixed. See [the todo](../agents/todo.md) for evidence and acceptance criteria.

## Scope and prerequisites

The candidate changes only the `nic0` TSO, GSO and GRO settings. The currently observed baseline for all three is `on`. EEE, address configuration, bridges and firewall rules stay unchanged. This is a hypothesis, not a known root-cause fix. Reconfirm interface identity and current baseline before applying; do not blindly restore `on` if the baseline has changed.

Before a production change, confirm the owner's local-console access, current VM backups and the current **host** backup required by [maintenance](maintenance.md). Existing VM backups are not evidence of a full Proxmox host backup. Confirm no backup or other critical operation is underway. Capture current NIC settings, service health, VM status and boot identifiers; record a rollback path accessible from the physical console.

## Proposed application and recovery

Implement and review a small persistent systemd service which applies the candidate after `nic0` exists and before normal network-dependent use. Before applying it, install and enable a separate boot-persistent rollback timer that restores the recorded baseline and disables the candidate service if the operator has not acknowledged a successful boot. The timer must operate locally without DNS, SSH or the network, use a bounded delay long enough for the host and guests to start, and itself be checked for enabled state before reboot. A transient `systemd-run --on-active` timer alone does not survive reboot and is insufficient. Test service and timer syntax and failure paths without touching the live interface first.

On initial application, arm the rollback, apply the settings, verify fresh SSH and the Proxmox UI, firewall, QNAP storage, guest SSH, and private Paperless, Kuma and Hermes services, then reboot. If connectivity is not recovered, allow the local timer to restore the baseline; if that fails, use the host console to disable the candidate service, restore the recorded `ethtool` settings and reboot. Do not cancel the rollback until fresh connections, all VMs, storage and application health have been checked after the reboot. Record exact unit names, commands, baseline and results in the deployment change before use.

## Acceptance

After the reboot, verify the desired settings persist and observe representative VM and QNAP traffic for a defined period, proposed as 24 hours. Check the host journal for new `Detected Hardware Unit Hang` events and inspect interface error counters. A clean short test or a single reboot does not prove the intermittent failure cannot recur. Keep the todo open until the defined soak completes, or the owner explicitly accepts the remaining risk. If errors or service regressions occur, restore the original settings and investigate firmware or kernel alternatives separately.
