"""The repository is public: tracked files must not carry site values or private names."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]

# Truncated SHA-256 of lowercase words that must never appear (private names, site
# identifiers). Stored as hashes so this file does not publish them. To add one:
# python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.argv[1].lower().encode()).hexdigest()[:16])' WORD
DENIED_WORD_HASHES = {
    "6ce26879750019bc",
    "be7f94bb10c4be7b",
    "2467b93f61fa4c35",
    "96dd98d8b3acd3ca",
    "dc0d200aaebbf548",
    "d1f6f53d41ab1298",
    "60f91a742458ae60",
    "2629e96f1e55248c",
    "a42cbe3d280b5e70",
    "ea2bb2d245a44013",
    "843379e83e735471",
    "973d7f9efc06ba81",
    "b83079c0696abd86",
    "c6a914efe04c0030",
    "5e5f82ca4895a0ec",
    "e77062b5fdabcb71",
    "447ba36c9d25be68",
    "0eaa219e660cf333",
    "43c8107af21beffb",
    "18ab01a40ee63b72",
}

# Documentation ranges, router defaults and synthetic test addresses.
ALLOWED_ADDRESSES = {
    "192.168.0.0", "192.168.0.1", "192.168.1.2",
    "100.64.0.0", "100.64.1.2", "100.64.1.3", "100.81.1.2", "100.100.100.100",
}

PATTERNS = {
    "private LAN address": re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
    "Tailscale address": re.compile(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b"),
    "tailnet name": re.compile(r"\btail[0-9a-f]{6}\b"),
    "Telegram bot handle": re.compile(r"@[A-Za-z0-9_]{3,}[Bb]ot\b"),
    "MAC address": re.compile(r"\b(?:[0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}\b"),
    "SSH public key": re.compile(r"AAAA[BC][0-9A-Za-z+/]{40,}"),
    "token": re.compile(r"\b(?:ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9-]{20,}|\d{8,10}:AA[A-Za-z0-9_-]{30,})"),
    "private key": re.compile(r"BEGIN [A-Z ]*PRIVATE KEY"),
}


def tracked_text_files():
    names = subprocess.run(["git", "ls-files"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.splitlines()
    for name in names:
        path = ROOT / name
        if not path.is_file():
            continue
        try:
            yield name, path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue


class PublicSafetyTests(unittest.TestCase):
    def test_no_site_values_or_secrets(self):
        findings = []
        for name, text in tracked_text_files():
            for label, pattern in PATTERNS.items():
                for match in pattern.finditer(text):
                    if match.group(0) not in ALLOWED_ADDRESSES:
                        line = text.count("\n", 0, match.start()) + 1
                        findings.append(f"{name}:{line}: {label}")
        self.assertEqual(findings, [], "Move site values to ignored config/site.json or .local/")

    def test_no_denied_words(self):
        findings = []
        for name, text in tracked_text_files():
            for number, line in enumerate(text.splitlines(), 1):
                for word in re.findall(r"[A-Za-z0-9_]+", line):
                    if hashlib.sha256(word.lower().encode()).hexdigest()[:16] in DENIED_WORD_HASHES:
                        findings.append(f"{name}:{number}")
        self.assertEqual(findings, [], "A denied private word is present; generalise it")


if __name__ == "__main__":
    unittest.main()
