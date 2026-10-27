# Validation and remaining hardware gates

The GitHub Actions workflow uses an ephemeral hosted runner with read-only repository permissions. It runs no infrastructure deployment and receives no Proxmox, NAS or model-provider secrets. It checks Python provisioning safety, parses JSON/YAML, checks Bash syntax, performs Ansible syntax checks and renders the Paperless Compose configuration with synthetic values.

For local Python tests, run `python -m unittest discover -s tests -v`. On Linux, use the project-local Ansible environment from `scripts/bootstrap-ansible.sh`; install `scripts/requirements-validation.txt` into that same environment and run `scripts/validate_repo.py`. All dependencies stay in `.local`.

Passing source validation does not confirm a working Proxmox deployment. Before the first milestone is accepted, record:

- Actual Dell hardware, firmware, SSD health and free capacity.
- Successful cloud-image template import, VM boot, cloud-init completion and SSH login.
- Working CLI sign-in under `coder`; `coder` cannot run sudo or access the Docker socket.
- Verified LAN and Tailscale rules that block development access to management interfaces.
- QNAP export identity, write permissions, successful backup, and an isolated VM restore.

Application acceptance additionally requires OCR/upload tests, failure tests with NAS unavailable, authenticated private access, a complete backup and an isolated restore.
