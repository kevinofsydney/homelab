import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock


ROOT = Path(__file__).resolve().parents[1]
TEST_TMP = ROOT / ".local" / "test-tmp"
TEST_TMP.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "scripts"))
from preflight import load_site  # noqa: E402
from provision_vm import provision  # noqa: E402


class ProvisioningSafetyTests(unittest.TestCase):
    def site_file(self, folder):
        key = folder / "id_ed25519.pub"
        key.write_text("ssh-ed25519 AAAATEST test\n", encoding="utf-8")
        site = json.loads((ROOT / "config/site.example.json").read_text(encoding="utf-8"))
        site["proxmox"].update({
            "api_url": "https://pve.example.invalid:8006", "node": "pve", "bridge": "vmbr0",
            "storage": "local-lvm", "ssh_public_key_file": str(key)
        })
        site["qnap"].update({"server": "nas.example.invalid", "nfs_export": "/backup"})
        path = folder / "site.json"
        path.write_text(json.dumps(site), encoding="utf-8")
        return path

    def test_example_requires_configuration(self):
        with self.assertRaisesRegex(ValueError, "proxmox.api_url"):
            load_site(ROOT / "config/site.example.json")

    def test_dry_run_needs_no_token_or_network(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            path = self.site_file(Path(tmp))
            result = subprocess.run(
                [sys.executable, str(ROOT / "scripts/provision_vm.py"), "--config", str(path)],
                capture_output=True, text=True, timeout=5,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("PLAN ONLY", result.stdout)

    def test_rejects_same_template_and_vm_id(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            path = self.site_file(Path(tmp))
            site = json.loads(path.read_text(encoding="utf-8"))
            site["proxmox"]["vmid"] = site["proxmox"]["template_vmid"]
            path.write_text(json.dumps(site), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "must differ"):
                load_site(path)

    def test_unavailable_id_causes_no_mutation(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            site = load_site(self.site_file(Path(tmp)))
            api = MagicMock()
            api.call.return_value = 101
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                provision(api, site)
            self.assertEqual(api.call.call_args_list[0].args[0], "GET")
            self.assertEqual(api.call.call_count, 1)

    def test_oversized_template_causes_no_mutation(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            site = load_site(self.site_file(Path(tmp)))
            api = MagicMock()
            api.call.side_effect = [100, {"template": 1, "ide2": "local:cloudinit", "scsi0": "local:disk,size=200G"}]
            with self.assertRaisesRegex(RuntimeError, "refusing shrink"):
                provision(api, site)
            self.assertTrue(all(c.args[0] == "GET" for c in api.call.call_args_list))

    def test_failed_clone_task_prevents_configuration_or_start(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            site = load_site(self.site_file(Path(tmp)))
            api = MagicMock()
            api.call.side_effect = [100, {"template": 1, "ide2": "local:cloudinit", "scsi0": "local:disk,size=2252M"}, "UPID:clone"]
            api.task.side_effect = RuntimeError("clone failed")
            with self.assertRaisesRegex(RuntimeError, "clone failed"):
                provision(api, site)
            writes = [c for c in api.call.call_args_list if c.args[0] != "GET"]
            self.assertEqual(len(writes), 1)
            self.assertTrue(writes[0].args[1].endswith("/clone"))

    def test_resize_uses_put_and_waits_for_async_configuration(self):
        with tempfile.TemporaryDirectory(dir=TEST_TMP) as tmp:
            site = load_site(self.site_file(Path(tmp)))
            api = MagicMock()
            events = []
            def call(method, path, params=None):
                events.append((method, path))
                if path == "/cluster/nextid": return 100
                if method == "GET": return {"template": 1, "ide2": "local:cloudinit", "scsi0": "local:disk,size=2252M"}
                return "UPID:" + path.rsplit("/", 1)[-1]
            api.call.side_effect = call
            api.task.side_effect = lambda node, upid: events.append(("WAIT", upid))
            provision(api, site)
            resize = next(i for i, e in enumerate(events) if e[1].endswith("/resize"))
            self.assertEqual(events[resize][0], "PUT")
            self.assertEqual(events[resize - 1], ("WAIT", "UPID:config"))


if __name__ == "__main__":
    unittest.main()
