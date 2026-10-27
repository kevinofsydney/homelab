#!/usr/bin/env python3
"""Validate repository documents without contacting any infrastructure."""
import json
from pathlib import Path
import sys

try:
    import yaml
except ImportError:
    sys.exit("Install scripts/requirements-validation.txt into a project-local environment first")

ROOT = Path(__file__).resolve().parents[1]
SKIP = {".git", ".local", "__pycache__"}


def main():
    count = 0
    for path in ROOT.rglob("*"):
        relative = path.relative_to(ROOT)
        if any(part in SKIP for part in relative.parts) or not path.is_file():
            continue
        if path.suffix == ".json" and path.name != "site.json":
            json.loads(path.read_text(encoding="utf-8"))
            count += 1
        if path.suffix in (".yml", ".yaml") and path.name != "hosts.yml":
            list(yaml.safe_load_all(path.read_text(encoding="utf-8")))
            count += 1
    print(f"PASS: parsed {count} JSON/YAML files")


if __name__ == "__main__":
    main()
