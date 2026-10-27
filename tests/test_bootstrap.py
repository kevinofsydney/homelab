"""Guard rails for the operator-only Proxmox bootstrap, with fake host commands."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/bootstrap-proxmox.sh"


class BootstrapTests(unittest.TestCase):
    def run_bootstrap(self, occupied=False, image_url=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            calls = root / "calls"
            for command, body in {
                "hostname": "echo testnode",
                "ip": ":",
                "ssh-keygen": ":",
                "pvesm": ":",
                "pvesh": "exit 1" if occupied else 'echo "$4"',
                "qm": 'echo qm >> "$CALLS"; exit 99',
                "curl": 'echo curl >> "$CALLS"; exit 99',
            }.items():
                path = root / command
                path.write_text("#!/bin/sh\n" + body + "\n")
                path.chmod(0o755)
            key = root / "public-key"
            key.touch()
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                       CALLS=str(calls), PVE_NODE="testnode", PVE_STORAGE="teststorage",
                       PVE_BRIDGE="testbridge", TEMPLATE_ID="9000", DEV_VM_ID="100",
                       SSH_PUBLIC_KEY_FILE=str(key), UBUNTU_IMAGE_SHA256="0" * 64,
                       UBUNTU_IMAGE_URL=image_url or "https://cloud-images.ubuntu.com/noble/20261017/noble-server-cloudimg-amd64.img")
            result = subprocess.run(["bash", str(SCRIPT)], env=env, capture_output=True, text=True)
            self.assertFalse(calls.exists(), "plan or rejected input must never download/create")
            return result

    def test_plan_has_no_mutations(self):
        result = self.run_bootstrap()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PLAN ONLY", result.stdout)

    def test_occupied_id_refuses_before_download(self):
        self.assertNotEqual(self.run_bootstrap(occupied=True).returncode, 0)

    def test_unapproved_image_origin_refuses(self):
        self.assertNotEqual(self.run_bootstrap(image_url="https://example.invalid/image.img").returncode, 0)
