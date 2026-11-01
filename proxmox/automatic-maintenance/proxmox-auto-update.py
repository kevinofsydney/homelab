#!/usr/bin/python3
"""Update one Proxmox host in its overnight maintenance window."""
import datetime
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys
from zoneinfo import ZoneInfo

ZONE = ZoneInfo('Australia/Sydney')
STATE = Path('/var/lib/proxmox-auto-update/reboot.json')

def in_window(cutoff=50):
    now = datetime.datetime.now(ZONE)
    return now.hour == 3 and now.minute < cutoff

def run(*args, **kwargs):
    print('+', ' '.join(args), flush=True)
    return subprocess.run(args, check=True, **kwargs)

def guests_idle():
    node = os.uname().nodename
    guests = json.loads(subprocess.check_output(
        ['pvesh', 'get', f'/nodes/{node}/qemu', '--output-format', 'json'], text=True))
    check = ('command -v fuser >/dev/null || exit 2; '
             'systemctl is-active --quiet apt-daily.service apt-daily-upgrade.service && exit 1; '
             'fuser -s /var/lib/dpkg/lock /var/lib/dpkg/lock-frontend && exit 1; exit 0')
    for guest in guests:
        if guest.get('status') != 'running':
            continue
        result = json.loads(subprocess.check_output(
            ['qm', 'guest', 'exec', str(guest['vmid']), '--timeout', '10', '--',
             'sh', '-c', check], text=True, timeout=20))
        if not result.get('exited') or result.get('exitcode') != 0:
            return False
    return True

def main():
    if os.geteuid() != 0 or not in_window():
        raise RuntimeError('Requires root and the 03:00–03:49 Sydney window')
    # This is the same flock used by vzdump. Keep it through package work.
    with open('/run/vzdump.lock', 'a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        env = dict(os.environ, DEBIAN_FRONTEND='noninteractive')
        run('apt-get', '-o', 'APT::Update::Error-Mode=any', 'update', env=env)
        if not in_window(40):
            raise RuntimeError('Window ended before package installation')
        run('apt-get', '-y', '--no-remove', '-o', 'Dpkg::Options::=--force-confdef',
            '-o', 'Dpkg::Options::=--force-confold', 'dist-upgrade', env=env)
        audit = subprocess.check_output(['dpkg', '--audit'], text=True)
        if audit.strip():
            raise RuntimeError('Package audit reports unfinished work: ' + audit)
        images = [p.name.removeprefix('vmlinuz-') for p in Path('/boot').glob('vmlinuz-*-pve')]
        if not images:
            raise RuntimeError('No Proxmox kernel images found')
        kernel = subprocess.check_output(['sort', '-V'], input='\n'.join(images) + '\n', text=True).splitlines()[-1]
        running = os.uname().release
        reboot = os.path.exists('/var/run/reboot-required') or kernel != running
        if reboot:
            if not in_window():
                print('Reboot deferred: outside maintenance window', flush=True)
                return
            if not guests_idle():
                raise RuntimeError('Reboot deferred: a guest update is running or cannot be checked')
            boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
            if STATE.exists():
                previous = json.loads(STATE.read_text())
                if previous.get('boot_id') == boot_id or (kernel != running and previous.get('kernel') == kernel):
                    raise RuntimeError('Reboot already attempted for this boot or kernel; inspect boot configuration')
            STATE.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            temporary = STATE.with_suffix('.tmp')
            temporary.write_text(json.dumps({'kernel': kernel, 'boot_id': boot_id}) + '\n')
            os.chmod(temporary, 0o600)
            os.replace(temporary, STATE)
            run('systemctl', 'reboot')
        else:
            print('No reboot required', flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(f'Automatic maintenance failed: {exc}', file=sys.stderr, flush=True)
        sys.exit(1)
