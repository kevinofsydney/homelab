"""Immich must fail closed when private access or storage is unavailable."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ImmichGateTests(unittest.TestCase):
    def run_plan(self, mount_ok=True, tailscale_state="Running", fstype="ext4", apply=False):
        temp_root = ROOT / ".local/test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            root = Path(tmp)
            (root / "scripts").mkdir()
            (root / "compose/immich").mkdir(parents=True)
            shutil.copy(ROOT / "scripts/deploy-immich.sh", root / "scripts")
            gate = root / "scripts/check-mount.sh"
            gate.write_text("#!/bin/sh\nexit " + ("0" if mount_ok else "1") + "\n")
            gate.chmod(0o755)
            for item in ("postgres", "thumbs", "encoded-video", "model-cache"):
                (root / "ssd" / item).mkdir(parents=True)
            (root / "nas").mkdir()
            (root / "nas/library").mkdir()
            for item in ("thumbs", "encoded-video"):
                (root / "nas/library" / item).mkdir()
            (root / "compose/immich/.env").write_text(
                f"IMMICH_NAS_ROOT={root / 'nas'}\nIMMICH_NAS_SOURCE=nas:/photos\n"
                f"IMMICH_LOCAL_ROOT={root / 'ssd'}\nIMMICH_BIND_IP=100.81.1.2\n"
                "IMMICH_UID=1000\nIMMICH_GID=1000\nDB_PASSWORD=syntheticsecret\n")
            tailscale = root / "tailscale"
            tailscale.write_text("#!/bin/sh\nprintf '%s' '" + json.dumps({"BackendState": tailscale_state, "TailscaleIPs": ["100.81.1.2"]}) + "'\n")
            tailscale.chmod(0o755)
            findmnt = root / "findmnt"
            findmnt.write_text("#!/bin/sh\necho " + fstype + "\n")
            findmnt.chmod(0o755)
            docker = root / "docker"
            docker.write_text('#!/bin/sh\necho "$*" >> "$MOCK_CALLS"\n')
            docker.chmod(0o755)
            calls = root / "calls"
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"], MOCK_CALLS=str(calls))
            command = ["bash", str(root / "scripts/deploy-immich.sh")]
            if apply:
                command.append("--apply")
            result = subprocess.run(command, env=env, capture_output=True, text=True, timeout=20)
            return result, calls.read_text() if calls.exists() else ""

    def test_plan_does_not_start_containers(self):
        result, calls = self.run_plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("config --quiet", calls)
        self.assertNotIn("up -d", calls)

    def test_mount_failure_blocks_apply(self):
        result, calls = self.run_plan(mount_ok=False, apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, "")

    def test_tailnet_offline_blocks_apply(self):
        result, calls = self.run_plan(tailscale_state="NeedsLogin", apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, "")

    def test_network_database_filesystem_blocks_apply(self):
        result, calls = self.run_plan(fstype="nfs4", apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, "")
