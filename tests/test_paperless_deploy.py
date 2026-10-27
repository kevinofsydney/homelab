"""Paperless plan remains usable without enabling deferred backups."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class PaperlessPlanTests(unittest.TestCase):
    def test_compose_enables_polling_for_the_reviewed_paperless_release(self):
        compose = yaml.safe_load((ROOT / "compose/paperless/compose.yml").read_text())
        environment = compose["services"]["webserver"]["environment"]
        self.assertGreater(float(environment["PAPERLESS_CONSUMER_POLLING_INTERVAL"]), 0)
        self.assertNotIn("PAPERLESS_CONSUMER_POLLING", environment)

    def run_plan(self, application_source="nas:/documents", mount_ok=True):
        temp_root = ROOT / ".local" / "test-tmp"
        temp_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_root) as directory:
            root = Path(directory)
            (root / "scripts").mkdir()
            (root / "compose/paperless").mkdir(parents=True)
            shutil.copy(ROOT / "scripts/deploy-paperless.sh", root / "scripts")
            gate = root / "scripts/check-mount.sh"
            gate.write_text("#!/bin/sh\n" + ("exit 0\n" if mount_ok else "exit 1\n"))
            gate.chmod(0o755)
            nas = root / "nas"
            local = root / "ssd"
            for path in (nas / "media", nas / "consume", nas / "export", local / "postgres", local / "valkey", local / "data"):
                path.mkdir(parents=True)
            (root / "compose/paperless/.env").write_text(
                f"PAPERLESS_NAS_ROOT={nas}\nPAPERLESS_NAS_SOURCE={application_source}\n"
                f"PAPERLESS_LOCAL_ROOT={local}\nPAPERLESS_BACKUP_MOUNT=/mnt/REPLACE_BACKUP\n"
                "PAPERLESS_BACKUP_SOURCE=REPLACE_NAS:/REPLACE_EXPORT\n"
            )
            calls = root / "docker-calls"
            docker = root / "docker"
            docker.write_text('#!/bin/sh\necho "$*" >> "$MOCK_DOCKER_CALLS"\n')
            docker.chmod(0o755)
            env = dict(os.environ, PATH=str(root) + os.pathsep + os.environ["PATH"], MOCK_DOCKER_CALLS=str(calls))
            result = subprocess.run(["bash", str(root / "scripts/deploy-paperless.sh")], env=env,
                                    capture_output=True, text=True, timeout=20)
            return result, calls.read_text() if calls.exists() else ""

    def test_backup_placeholders_do_not_block_application_plan(self):
        result, calls = self.run_plan()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PLAN ONLY", result.stdout)
        self.assertIn("config --quiet", calls)
        self.assertNotIn("up -d", calls)

    def test_application_storage_placeholder_still_blocks(self):
        result, calls = self.run_plan(application_source="REPLACE_NAS:/REPLACE_EXPORT")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, "")

    def test_failed_nas_mount_still_blocks(self):
        result, calls = self.run_plan(mount_ok=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(calls, "")
