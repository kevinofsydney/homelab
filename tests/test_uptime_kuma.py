"""Kuma must remain private and keep its state on an existing local disk."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class UptimeKumaTests(unittest.TestCase):
    def run_plan(self, bind='100.81.1.2', state='Running', fstype='ext4', source='/dev/sda1', data_exists=True):
        temp_root = ROOT / '.local/test-tmp'
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            root = Path(tmp)
            (root / 'scripts').mkdir()
            (root / 'compose/uptime-kuma').mkdir(parents=True)
            shutil.copy(ROOT / 'scripts/deploy-uptime-kuma.sh', root / 'scripts')
            data = root / 'ssd'
            if data_exists:
                data.mkdir()
            (root / 'compose/uptime-kuma/.env').write_text(
                f'KUMA_BIND_IP={bind}\nKUMA_DATA_ROOT={data}\nKUMA_IMAGE=reviewed\n')
            tailscale = root / 'tailscale'
            tailscale.write_text('#!/bin/sh\nprintf \'{"BackendState":"' + state + '","TailscaleIPs":["100.81.1.2"]}\'\n')
            tailscale.chmod(0o755)
            findmnt = root / 'findmnt'
            findmnt.write_text('#!/bin/sh\nif [ "$5" = FSTYPE ]; then echo "$MOCK_TYPE"; else echo "$MOCK_SOURCE"; fi\n')
            findmnt.chmod(0o755)
            docker = root / 'docker'
            docker.write_text('#!/bin/sh\necho "$*" >> "$MOCK_CALLS"\n')
            docker.chmod(0o755)
            calls = root / 'calls'
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ['PATH'], MOCK_TYPE=fstype,
                       MOCK_SOURCE=source, MOCK_CALLS=str(calls))
            result = subprocess.run(['bash', str(root / 'scripts/deploy-uptime-kuma.sh')], env=env,
                                    capture_output=True, text=True, timeout=20)
            return result, calls.read_text() if calls.exists() else ''

    def test_private_local_plan_never_starts(self):
        result, calls = self.run_plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('config --quiet', calls)
        self.assertNotIn('up -d', calls)

    def test_missing_data_does_not_create_fallback(self):
        result, calls = self.run_plan(data_exists=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, '')

    def test_nas_data_is_refused(self):
        result, calls = self.run_plan(fstype='nfs4', source='nas:/media')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, '')

    def test_offline_tailnet_is_refused(self):
        result, calls = self.run_plan(state='NeedsLogin')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, '')

    def test_lan_bind_is_refused(self):
        result, calls = self.run_plan(bind='192.168.0.1')
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, '')
