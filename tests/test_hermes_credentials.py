"""Credential helper file handling; no real credentials are used."""
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
import unittest

PATH = Path(__file__).resolve().parents[1] / "scripts/hermes/set-credentials.py"
spec = importlib.util.spec_from_file_location("hermes_credentials", PATH)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CredentialsTests(unittest.TestCase):
    def test_private_atomic_write_and_preserve(self):
        with tempfile.TemporaryDirectory() as directory:
            module.write_value(directory, "OPENROUTER_API_KEY", "sk-or-test")
            module.write_value(directory, "TELEGRAM_ALLOWED_USERS", "123456")
            path = Path(directory) / ".hermes/.env"
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
            self.assertEqual(path.read_text(), "OPENROUTER_API_KEY=sk-or-test\nTELEGRAM_ALLOWED_USERS=123456\n")
            with self.assertRaises(ValueError):
                module.write_value(directory, "OPENROUTER_API_KEY", "sk-or-other")
            module.write_value(directory, "OPENROUTER_API_KEY", "sk-or-other", True)
            self.assertIn("TELEGRAM_ALLOWED_USERS=123456", path.read_text())

    def test_refuses_symlinks_and_duplicate_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / ".hermes"
            root.mkdir()
            target = root / ".env"
            target.symlink_to(Path(directory) / "elsewhere")
            with self.assertRaises(ValueError):
                module.write_value(directory, "TELEGRAM_BOT_TOKEN", "1:test")
            target.unlink()
            target.write_text("export TELEGRAM_BOT_TOKEN=a\nTELEGRAM_BOT_TOKEN=b\n")
            with self.assertRaises(ValueError):
                module.write_value(directory, "TELEGRAM_BOT_TOKEN", "1:test", True)

    def test_format_rejects_multiline_or_shell_syntax(self):
        for _, pattern in module.FIELDS.values():
            self.assertIsNone(pattern.fullmatch("unsafe\nEVIL=yes"))
            self.assertIsNone(pattern.fullmatch("$(whoami)"))


    def test_exa_key_format(self):
        key, pattern = module.FIELDS["exa"]
        self.assertEqual(key, "EXA_API_KEY")
        self.assertIsNotNone(pattern.fullmatch("0123abcd-4567-89ef-0123-456789abcdef"))
        self.assertIsNone(pattern.fullmatch("short"))
        self.assertIsNone(pattern.fullmatch("has space in it 1234567890"))

if __name__ == "__main__":
    unittest.main()
