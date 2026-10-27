"""Safety checks for application VM clone planning without a Proxmox host."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/clone-application-vm.sh"


class ApplicationVmTests(unittest.TestCase):
    def run_plan(self, occupied=False, free="300000000", template=True, apply=False, disk_bytes=3758096384):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            changes = root / "changes"
            commands = {
                "hostname": "echo testnode",
                "ip": ":",
                "ssh-keygen": ":",
                "pvesh": "exit 1" if occupied else 'echo "$4"',
                "pvesm": f"if [ \"$1\" = path ]; then echo /fake/disk; else printf 'Name Type Status Total Used Available %%\\nstore lvmthin active 350000000 1 {free} 0\\n'; fi",
                "qemu-img": f"printf '{{\"virtual-size\":{disk_bytes}}}\\n'",
                "qm": ('if [ "$1" = config ]; then printf "template: 1\\nide2: store:cloudinit\\nscsi0: store:disk\\n"; '
                       'else echo "$1" >> "$CHANGES"; fi') if template else 'if [ "$1" = config ]; then echo "scsi0: store:disk"; else echo "$1" >> "$CHANGES"; fi',
            }
            for name, body in commands.items():
                path = root / name
                path.write_text("#!/bin/sh\n" + body + "\n")
                path.chmod(0o755)
            key = root / "operators.pub"
            key.write_text("ssh-ed25519 TEST fixture\n")
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"],
                       CHANGES=str(changes), PVE_NODE="testnode", PVE_STORAGE="store",
                       PVE_BRIDGE="testbridge", TEMPLATE_ID="9000", APP_VM_ID="130",
                       APP_VM_NAME="testguest", SSH_PUBLIC_KEYS_FILE=str(key))
            result = subprocess.run(["bash", str(SCRIPT)] + (["--apply"] if apply else []),
                                    env=env, capture_output=True, text=True)
            return result, changes.read_text().splitlines() if changes.exists() else []

    def test_plan_is_read_only(self):
        result, changes = self.run_plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PLAN ONLY", result.stdout)
        self.assertEqual(changes, [])

    def test_occupied_id_blocks_apply(self):
        result, changes = self.run_plan(occupied=True, apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(changes, [])

    def test_low_capacity_blocks_apply(self):
        result, changes = self.run_plan(free="100000000", apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(changes, [])

    def test_non_template_blocks_apply(self):
        result, changes = self.run_plan(template=False, apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(changes, [])

    def test_oversized_template_blocks_apply(self):
        result, changes = self.run_plan(disk_bytes=61 * 1024 ** 3, apply=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(changes, [])
