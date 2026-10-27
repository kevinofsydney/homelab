# Private n8n staging stack

This is staged, not running. It uses the [official n8n Docker configuration](https://docs.n8n.io/deploy/host-n8n/install-options/install-with-docker.md) as its baseline, with a verified immutable stable image, SQLite data on the app VM's SSD and no public webhooks. Its loopback-only port is intended for an authenticated SSH tunnel. It does not include the optional n8n Assistant sandbox or a privileged Docker-in-Docker container.

The Compose file binds `/srv/n8n/data` to `/home/node/.n8n` with `create_host_path: false`; the staged role requires a local filesystem, a non-symlinked data path and the image's expected numeric UID/GID 1000. n8n normally generates and stores its encryption key in that directory alongside its database. Do not delete, replace or lose that key: encrypted credentials depend on it. The operator deferred QNAP backups; no backup or restore has been verified. Treat loss of the VM/disk as potential loss of the database, workflows, credentials and encryption key.

The daemon and socket remain disabled pending explicit approval of Docker's guest bridge/firewall changes. After approval, enable Docker on the application VM, then run `/opt/homelab/n8n/deploy-n8n.sh` for validation and `--apply` to pull/start the pinned image. The wrapper checks the existing data directory and filesystem and refuses to start a container if Docker is inactive. It defaults to a plan. The container has no automatic restart in this first phase; the VM itself also has autostart disabled.

Before use, check the running container, `curl -fsS http://127.0.0.1:5678/healthz` locally and confirm port 5678 is not reachable through the guest's LAN address. From an authorized Windows operator computer, open an SSH tunnel to the observed app VM address:

```powershell
ssh -L 5678:127.0.0.1:5678 devops@<application-vm-address>
```

Keep the SSH window open and visit `http://localhost:5678` on that computer. Verify the app VM's SSH host key against the trusted Proxmox console before accepting it. Complete n8n's initial owner setup yourself; do not send account passwords or service credentials to the coding agent. Confirm owner login and a harmless test workflow. The first setup and authenticated application behavior remain untested until then.

The application VM is not a worker isolation boundary: its management-LAN reachability has not been restricted. Do not add unattended workflows, sensitive credentials or production integrations before their access and recovery requirements are reviewed. Public webhooks and ingress require separate review and approval.

## Upgrade and recovery

Review upstream release notes and pin a new tag and digest together. Before upgrading or enabling real workflows, take an application-consistent copy of the SQLite database and encryption key to an approved backup destination, test an isolated restore, and record rollback steps. A database migration can make downgrading the image alone unsafe. Until a restore has been tested, report recovery as unverified.
