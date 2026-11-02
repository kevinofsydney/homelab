#!/usr/bin/env python3
"""Disable TSO, GSO and GRO on the Proxmox NIC, with a boot-persistent rollback."""
import json
import os
import pathlib
import subprocess
import sys

IFACE = 'nic0'
DRIVER = 'e1000e'
FEATURES = {
    'tso': 'tcp-segmentation-offload',
    'gso': 'generic-segmentation-offload',
    'gro': 'generic-receive-offload',
}
BASELINE = pathlib.Path('/var/lib/homelab-nic-offload/baseline.json')
SERVICE = 'homelab-nic-offload.service'
ROLLBACK_TIMER = 'homelab-nic-offload-rollback.timer'


def run(*args):
    subprocess.run(args, check=True)


def succeeds(*args):
    return subprocess.run(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0


def require_expected_nic():
    driver = next(
        (line.split(':', 1)[1].strip() for line in subprocess.check_output(['ethtool', '-i', IFACE], text=True).splitlines() if line.startswith('driver:')),
        None,
    )
    if driver != DRIVER:
        raise RuntimeError(f'{IFACE} uses driver {driver}, expected {DRIVER}')


def current_settings():
    values = {}
    for line in subprocess.check_output(['ethtool', '-k', IFACE], text=True).splitlines():
        name, _, value = line.partition(':')
        values[name.strip()] = value.split()[0] if value.split() else ''
    settings = {flag: values.get(name) for flag, name in FEATURES.items()}
    if not all(value in ('on', 'off') for value in settings.values()):
        raise RuntimeError(f'unexpected offload state: {settings}')
    return settings


def set_features(settings):
    args = ['ethtool', '-K', IFACE]
    for flag, value in settings.items():
        args += [flag, value]
    run(*args)


def apply_candidate():
    require_expected_nic()
    set_features({flag: 'off' for flag in FEATURES})
    settings = current_settings()
    if set(settings.values()) != {'off'}:
        raise RuntimeError(f'offloads did not turn off: {settings}')
    print(f'{IFACE} offloads off: {settings}')


def record_baseline():
    # A repeated arm keeps the first record, so it cannot save the candidate as the baseline.
    if BASELINE.exists():
        return
    settings = current_settings()
    BASELINE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = BASELINE.with_suffix('.tmp')
    with open(temporary, 'w') as handle:
        json.dump(settings, handle)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, BASELINE)


def arm():
    require_expected_nic()
    record_baseline()
    # The rollback is in place and checked before the live interface changes.
    run('systemctl', 'daemon-reload')
    run('systemctl', 'enable', '--now', ROLLBACK_TIMER)
    if not succeeds('systemctl', 'is-enabled', '--quiet', ROLLBACK_TIMER) or not succeeds('systemctl', 'is-active', '--quiet', ROLLBACK_TIMER):
        raise RuntimeError('rollback timer is not enabled and active')
    run('systemctl', 'enable', SERVICE)
    run('systemctl', 'restart', SERVICE)
    print(f'armed; run "ack" after acceptance checks or the baseline returns when {ROLLBACK_TIMER} fires')


def acknowledge():
    settings = current_settings()
    if set(settings.values()) != {'off'} or not succeeds('systemctl', 'is-active', '--quiet', SERVICE):
        raise RuntimeError(f'candidate is not active, refusing to cancel the rollback: {settings}')
    run('systemctl', 'disable', '--now', ROLLBACK_TIMER)
    print('rollback cancelled; candidate stays enabled')


def rollback():
    restored = False
    try:
        require_expected_nic()
        set_features(json.loads(BASELINE.read_text()))
        restored = True
    except Exception as error:
        print(f'baseline not restored: {error}', file=sys.stderr)
    # The candidate must not return at the next boot, even if the restore failed.
    run('systemctl', 'disable', SERVICE)
    run('systemctl', 'disable', '--now', ROLLBACK_TIMER)
    run('systemctl', 'stop', SERVICE)
    if not restored:
        return 1
    BASELINE.unlink()
    print(f'{IFACE} restored: {current_settings()}')
    return 0


def check():
    require_expected_nic()
    print(f'settings: {current_settings()}')
    print(f'baseline: {BASELINE.read_text() if BASELINE.exists() else "not recorded"}')
    for unit in (SERVICE, ROLLBACK_TIMER):
        state = 'enabled' if succeeds('systemctl', 'is-enabled', '--quiet', unit) else 'not enabled'
        print(f'{unit}: {state}')
    return 0


def main(argv):
    actions = {'check': check, 'apply': apply_candidate, 'arm': arm, 'ack': acknowledge, 'rollback': rollback}
    if len(argv) != 2 or argv[1] not in actions:
        print(f'usage: {argv[0]} {{{"|".join(actions)}}}', file=sys.stderr)
        return 2
    return actions[argv[1]]() or 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
