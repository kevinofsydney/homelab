#!/usr/bin/env python3
"""Archive the Proxmox host configuration to the verified QNAP backup mount."""
import datetime
import os
import pathlib
import re
import sqlite3
import subprocess
import sys
import tempfile

MOUNT = pathlib.Path('/mnt/pve/qnap-backups')
DESTINATION = MOUNT / 'host-config'
CLUSTER_DB = '/var/lib/pve-cluster/config.db'
# /etc/pve is a separate FUSE filesystem, so it must be named as well as /etc.
PATHS = ['etc', 'etc/pve', 'root', 'usr/local', 'var/spool/cron']
KEEP = 15
ARCHIVE_NAME = re.compile(r'^host-config-\d{4}-\d{2}-\d{2}T\d{6}\.tar\.gz$')


def require_mount():
    fstype = subprocess.run(['findmnt', '-n', '-o', 'FSTYPE', '--target', str(MOUNT)], capture_output=True, text=True).stdout.strip()
    if not MOUNT.is_mount() or not fstype.startswith('nfs'):
        raise RuntimeError(f'{MOUNT} is not a mounted NFS export (found {fstype or "nothing"})')


def staged_metadata(directory):
    source = sqlite3.connect(f'file:{CLUSTER_DB}?mode=ro', uri=True)
    target = sqlite3.connect(directory / 'config.db')
    with target:
        source.backup(target)
    source.close()
    target.close()
    (directory / 'packages.txt').write_text(subprocess.check_output(['dpkg', '--get-selections'], text=True))
    (directory / 'pveversion.txt').write_text(subprocess.check_output(['pveversion', '-v'], text=True))


def create_archive(archive):
    with tempfile.TemporaryDirectory(prefix='host-config-') as staging:
        staged_metadata(pathlib.Path(staging))
        # GNU tar exits 1 when a live file changes while it is read; other failures exit 2.
        result = subprocess.run(['tar', '-czf', str(archive), '--one-file-system', '--warning=no-file-changed', '-C', '/', *PATHS, '-C', staging, '.'])
        if result.returncode not in (0, 1):
            raise RuntimeError(f'tar exited {result.returncode}')


def verify_archive(archive):
    names = set(subprocess.check_output(['tar', '-tzf', str(archive)], text=True).splitlines())
    for required in ('./config.db', 'etc/pve/storage.cfg', 'etc/network/interfaces'):
        if required not in names:
            raise RuntimeError(f'{archive} is missing {required}')


def prune():
    archives = sorted(path for path in DESTINATION.iterdir() if ARCHIVE_NAME.match(path.name))
    for path in archives[:-KEEP]:
        path.unlink()


def main():
    os.umask(0o077)
    require_mount()
    # Without parents, so a missing mount cannot become a local fallback destination.
    DESTINATION.mkdir(mode=0o700, exist_ok=True)
    name = f'host-config-{datetime.datetime.now().strftime("%Y-%m-%dT%H%M%S")}.tar.gz'
    temporary = DESTINATION / f'{name}.partial'
    try:
        create_archive(temporary)
        verify_archive(temporary)
        os.replace(temporary, DESTINATION / name)
    finally:
        temporary.unlink(missing_ok=True)
    prune()
    print(f'{DESTINATION / name}: {(DESTINATION / name).stat().st_size} bytes')
    return 0


if __name__ == '__main__':
    sys.exit(main())
