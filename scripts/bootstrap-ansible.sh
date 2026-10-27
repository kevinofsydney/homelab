#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 -m venv .local/venv
.local/venv/bin/python -m pip install -r ansible/requirements.txt
echo 'Use .local/venv/bin/ansible-playbook; all Python packages are under .local/venv.'
