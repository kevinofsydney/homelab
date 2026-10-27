"""The boot wrapper must not call deployment until private access is ready."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PaperlessAutostartTests(unittest.TestCase):
    def run_wrapper(self, state, addresses, bind="100.64.1.2", deploy_rc=0):
        temp_root = ROOT / ".local" / "test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as tmp:
            root = Path(tmp)
            (root / "compose/paperless").mkdir(parents=True)
            (root / "scripts").mkdir()
            (root / "compose/paperless/.env").write_text(f"PAPERLESS_BIND_IP={bind}\nPAPERLESS_SECRET_KEY=hidden\n")
            tailscale = root / "tailscale"
            tailscale.write_text("#!/bin/sh\nprintf '%s' '" + json.dumps({"BackendState": state, "TailscaleIPs": addresses}) + "'\n")
            tailscale.chmod(0o755)
            deploy = root / "scripts/deploy-paperless.sh"
            deploy.write_text(f'#!/bin/sh\necho "$*" > "$PAPERLESS_INSTALL_ROOT/called"\nexit {deploy_rc}\n')
            deploy.chmod(0o755)
            env = dict(os.environ, PAPERLESS_INSTALL_ROOT=str(root), PATH=str(root) + os.pathsep + os.environ["PATH"])
            result = subprocess.run([str(ROOT / "scripts/start-paperless-when-ready.sh")], env=env,
                                    capture_output=True, text=True, timeout=15)
            called = (root / "called").read_text().strip() if (root / "called").exists() else None
            return result, called

    def test_running_tailnet_uses_mount_gated_apply(self):
        result, called = self.run_wrapper("Running", ["100.64.1.2"])
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(called, "--apply")

    def test_disconnected_tailnet_never_starts_deployment(self):
        result, called = self.run_wrapper("NeedsLogin", ["100.64.1.2"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(called)

    def test_wrong_private_address_never_starts_deployment(self):
        result, called = self.run_wrapper("Running", ["100.64.1.3"])
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(called)

    def test_non_tailnet_bind_never_starts_deployment(self):
        result, called = self.run_wrapper("Running", ["192.168.1.2"], bind="192.168.1.2")
        self.assertNotEqual(result.returncode, 0)
        self.assertIsNone(called)

    def test_mount_gate_failure_propagates_for_retry(self):
        result, called = self.run_wrapper("Running", ["100.64.1.2"], deploy_rc=1)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(called, "--apply")
