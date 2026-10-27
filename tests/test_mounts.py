import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TMP = ROOT / ".local" / "test-tmp"
TMP.mkdir(parents=True, exist_ok=True)


@unittest.skipIf(os.name == "nt", "NFS mount gate tests run on the Linux CI runner")
class MountGateTests(unittest.TestCase):
    def probe(self, fstype, source, lower_layer=""):
        with tempfile.TemporaryDirectory(dir=TMP) as tmp:
            folder = Path(tmp)
            mount = folder / "mount"
            mount.mkdir()
            fake = folder / "findmnt"
            fake.write_text('#!/usr/bin/env python3\nimport os, sys\nprint(os.environ["MOCK_LOWER"] + os.environ["MOCK_SOURCE"] + " " + os.environ["MOCK_FSTYPE"])\n')
            fake.chmod(0o755)
            env = dict(os.environ, PATH=str(folder) + os.pathsep + os.environ["PATH"],
                       MOCK_FSTYPE=fstype, MOCK_SOURCE=source, MOCK_LOWER=lower_layer)
            return subprocess.run(["bash", str(ROOT / "scripts/check-mount.sh"), str(mount), "nas:/approved"],
                                  env=env, capture_output=True, text=True, timeout=20)

    def test_refuses_local_directory_fallback(self):
        result = self.probe("ext4", "/dev/local")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("wrong filesystem", result.stderr)

    def test_refuses_wrong_nas_export(self):
        result = self.probe("nfs4", "nas:/wrong-share")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("source mismatch", result.stderr)

    def test_accepts_verified_export(self):
        result = self.probe("nfs4", "nas:/approved")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_accepts_nfs_over_automount(self):
        result = self.probe("nfs4", "nas:/approved", "systemd-1 autofs\n")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_refuses_local_mount_covering_nfs(self):
        result = self.probe("ext4", "/dev/local", "nas:/approved nfs4\n")
        self.assertNotEqual(result.returncode, 0)

    def test_refuses_wrong_export_over_automount(self):
        result = self.probe("nfs4", "nas:/wrong-share", "systemd-1 autofs\n")
        self.assertNotEqual(result.returncode, 0)
