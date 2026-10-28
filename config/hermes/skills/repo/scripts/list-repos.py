#!/usr/bin/env python3
"""List the GitHub repositories the Hermes token can reach, most recently pushed first.

Prints one line per repository: name, visibility, last push date and description.
Reads GITHUB_TOKEN from ~/.hermes/.env and never prints it.
"""
import json
import pathlib
import re
import sys
import urllib.request

env = pathlib.Path.home().joinpath(".hermes/.env").read_text(encoding="utf-8")
match = re.search(r"^GITHUB_TOKEN=[\"']?([^\"'\n]+)", env, re.M)
if not match:
    sys.exit("GITHUB_TOKEN is not set in ~/.hermes/.env")

request = urllib.request.Request(
    "https://api.github.com/user/repos?per_page=100&affiliation=owner&sort=pushed",
    headers={"Authorization": "Bearer " + match.group(1), "Accept": "application/vnd.github+json"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    repos = json.load(response)

for repo in repos:
    if repo.get("archived"):
        continue
    visibility = "private" if repo["private"] else "public"
    pushed = (repo.get("pushed_at") or "")[:10]
    description = (repo.get("description") or "").replace("\n", " ")[:80]
    print(f"{repo['name']}\t{visibility}\t{pushed}\t{description}")
