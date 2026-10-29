# Homelab Blueprint — Decisions, Architecture and Automation

Updated: 2026-10-26. Status: **design specification, not a completed installation**. Lightly generalised on 2026-10-29 before the repository was made public.

## Confirmed choices
- Hardware: Dell OptiPlex 7000 Micro, Intel Core i5-12500T (2022), 32 GB RAM, 512 GB SSD, refurbished; wired Ethernet.
- Hypervisor: Proxmox VE. Fresh installation, no migration from BinaryLane.
- Network: TP-Link BE15000; existing Tailscale on household devices; NextDNS active. Do not replace NextDNS initially.
- NAS: QNAP TS-264-8G, Plex already running; approximately 5–10 TB may be free (**verify**).
- Remote control: Telegram, web UI, SSH and VS Code. AI agent may edit code, run tests and create PRs; **human approval before production deployment**.
- AI access: ChatGPT/OpenAI subscription, OpenCode subscription, DeepSeek API, OpenRouter API. Prefer eligible ChatGPT-based interactive coding and cost-controlled DeepSeek API for unattended work. Keep all credentials out of Git.
- Development: GitHub clone/push/pull; create apps, debug apps, maintain n8n, research and scheduled scripts; issues to draft PRs.
- Apps: Immich phone photo backups; Paperless-ngx for receipts/invoices/manuals; optional document AI; n8n; audiobook and ebook libraries; optional Pi-hole for selected devices; a small public web app.
- Public web app: a small number of users on their own devices; user login; public-facing login but admin private as practical. Requirements **unconfirmed**.
- Domain: owned, registrar/DNS configuration **unconfirmed**.
- Storage preference: QNAP for large files and backups; avoid duplicate bulk media on Dell.
- Backup preference: start with QNAP backups; improve to independent off-site backups for irreplaceable data.
- User experience: guided installation, moderate terminal experience, free/open-source preference and minimal additional API spend.

## Key architecture decisions (proposed, not yet implemented)
- Proxmox host remains a hypervisor, not a Docker/application host.
- Separate Ubuntu Server LTS VMs: (100) AI/development, (110) staging and/or isolated app service, (120) Immich, (130) home services including n8n and Paperless. Separate short-lived coding worker rather than giving a permanent CI runner broad host access.
- Start with RAM allocations of 8–10 GB AI VM, 4 GB staging, 6–8 GB Immich, 4–6 GB home services; reserve 4–6 GB for host and growth. Review real usage, avoid overcommitting RAM.
- NAS bulk storage: Immich photo originals, Paperless media/document archives, audiobook/ebook files, backup files. Dell local SSD: VM OS, PostgreSQL/Valkey/Redis, indexes, hot metadata, coding workspaces. Export consistent application backups to QNAP.
- Do **not** put PostgreSQL database directories on SMB/NFS. Check mount availability and write permissions before starting apps; fail closed on missing media shares.
- QNAP directories/shares (names illustrative): `Homelab/immich`, `Homelab/paperless`, `Homelab/audiobooks`, `Homelab/ebooks`, `Homelab/backups`. Restrict with different NAS service accounts and credentials.
- Plex stays on QNAP.
- Public web app: **prefer managed production hosting** for reliability; Dell hosts development/staging and agent. If self-hosted on Dell, keep it in a tightly isolated production VM, use only approved ingress, monitoring, backups and tested recovery. Decide before live use.
- Private web dashboards/administration via Tailscale and LAN firewall rules. No public Proxmox, SSH, QNAP admin, n8n editor, Paperless or Immich admin interfaces.
- Keep NextDNS initially; optional Pi-hole LXC for manually selected devices, not household single-point-of-failure DNS.

## AI tools and provider policy
1. Interactive coding: OpenCode and/or Codex CLI in the dev VM, using **official supported account login** if eligible. ChatGPT subscription does not imply unlimited API tokens or automated use; confirm current product terms and rate limits.
2. Telegram agent: evaluate Hermes Agent with DeepSeek API; fallback OpenRouter where appropriate. Require Telegram user allowlist, budget alerts and approval checks. Never install an arbitrary unreviewed tool granting root.
3. Grok integration option A (preferred): use Grok Bot's GitHub connector to create/read issues or review PRs; the same GitHub label-based pipeline runs locally on a restricted worker. No direct Grok-to-Proxmox access.
4. Grok integration option B (later): custom **publicly reachable MCP endpoint** or narrowly scoped authenticated HTTPS webhook exposing allowlisted actions such as `create_issue`, `get_job_status`, `request_update_plan`. Require authentication, validation, audit logs and no raw shell command tool.
5. Local LLM inference is optional and not a reason to change the main architecture; CPU-only large coding models are not economical here.

## GitHub issue -> PR -> deployment policy
- Telegram/Hermes/Grok creates issue in an allowlisted repository. `ai-ready` label must be applied by a trusted maintainer/verified workflow, not automatically to any untrusted issue.
- GitHub Actions queues job; run coding task in disposable sandbox/worker without production secrets, NAS mounts or Proxmox credentials. Use pinned actions and scoped short-lived GitHub credentials.
- Agent checks out code, creates feature branch, edits, runs tests, opens **draft PR**. PR reports tests and risks. No automatic merge.
- Owner reviews PR and approves merge. Deployment is a separate, explicit approval event; narrowly scoped deployer validates allowlisted repo, commit SHA, environment and checks.
- Production deploys should include backup, health checks, failure alerts and documented rollback procedure.
- n8n workflow edits follow equivalent staging -> review -> promotion flow. No production workflow secrets in Git.

## Paperless-ngx plan
- Use official Paperless-ngx Docker Compose with PostgreSQL and Valkey/Redis; keep DB/data/index on Dell SSD; put document media/archive on QNAP and regularly export backup bundles to a separate QNAP location.
- Configure paperless `consume` folder, web upload, optional carefully scoped email ingestion. For an NFS-backed `consume` folder enable consumer polling because inotify may not work.
- Start with built-in OCR and classification. As of Oct 2026 Paperless-ngx includes **optional built-in LLM suggestions, document chat and retrieval**, so prefer evaluating first-party AI before adding another container.
- `clusterzx/paperless-ai` is marked **unmaintained** by its author; treat as experimental optional component only after security review. Do not rely on it for critical document ingestion.
- Sensitive receipts, invoices and other documents may leave the network if using DeepSeek or another cloud model; start AI features off, select documents/categories eligible for cloud analysis or use local backend. Use separate credentials, no broad Telegram attachment ingestion initially.

## Initial implementation phases and acceptance tests
### 0. Before delivery
- [ ] Create a **private** GitHub repository (e.g. `homelab-infra`); commit this document and version-controlled templates, never secrets.
- [ ] Record router LAN subnet, Tailscale grant policy, DNS provider, NAS free storage/RAID and recovery status.
- [ ] Download Proxmox ISO; prepare verified installer USB; choose local host address and reserved DHCP entries.
- [ ] Create separate QNAP shares and low-privilege service accounts; plan encrypted backups.

### 1. Manual trust bootstrap
- [ ] Verify Dell RAM, SSD health, BIOS updates, virtualization, power-restoration settings and Dell hardware identifiers.
- [ ] Install Proxmox via console (destroys the target disk), establish host IP, update packages, enable firewall and strong admin authentication.
- [ ] Connect trusted admin machine via Tailscale or restricted LAN; no public management ports.
- [ ] Add QNAP as backup target; create small test VM, back it up and restore it successfully.

### 2. Infrastructure as code (Ansible suggested)
- [ ] Use read-only `plan/check` against current Proxmox before making changes; store inventory with placeholder IPs, hostnames and VM sizing.
- [ ] Provision Ubuntu VM templates through reviewed Proxmox API/cloud-init workflow; restrict automation credentials to necessary VM operations.
- [ ] Configure guest users, SSH public keys, UFW, Docker Engine/Compose, unattended **security** updates where appropriate, monitoring and Tailscale.
- [ ] Never store passwords/tokens in repo. Load from environment, secret manager or encrypted Ansible Vault not committed in plaintext.
- [ ] Require explicit approval for actions that wipe disks, change the router/DNS, expose ports, update Proxmox, modify backup targets or deploy the public app.

### 3. Coding/agent platform
- [ ] Install OpenCode/Codex through reviewed official methods; authenticate with supported accounts.
- [ ] Install Hermes with DeepSeek/OpenRouter credentials and Telegram allowlist, strict permission policy and budget ceiling.
- [ ] Test `Telegram -> issue -> labelled job -> sandbox -> draft PR`; block any deployment without user approval.
- [ ] Test an update-check job producing a report, **not** automatic updates across every application.

### 4. Storage and apps
- [ ] Verify reliable NAS mounts and dependency checks; set up Immich with media on QNAP, database on Dell.
- [ ] Deploy Paperless-ngx and test ingest -> OCR -> search -> original download -> backup/restore. Evaluate built-in AI after privacy choices.
- [ ] Deploy n8n and Audiobookshelf/Kavita privately with separate volumes and service accounts.
- [ ] Retain NextDNS; optionally test Pi-hole with one device.

### 5. Public web app
- [ ] Capture the app's requirements and any integration formats.
- [ ] Define mobile-friendly login, role-based auth, approvals, audit trail and export mapping.
- [ ] Keep production separate from coding agents; test backups, restores and exports with synthetic data before using real user data.
- [ ] Choose managed hosting or a hardened self-hosted production VM before public rollout.

## Repository suggestion
```
homelab-infra/
  README.md
  docs/homelab-blueprint.md
  docs/network-and-threat-model.md
  docs/recovery-runbook.md
  inventory/example.yml
  ansible/playbooks/{base,apps,backup}.yml
  ansible/roles/{common,docker,tailscale,nas-mount}/
  compose/{immich,paperless,n8n,media}/
  policies/{agent-permissions,deploy-approval}.md
  github-workflows/issue-to-pr.example.yml
  scripts/{preflight,verify-backups}.sh
  .env.example
  .gitignore
```
Everything except this Markdown blueprint is a **design suggestion** until generated, reviewed and tested. Do not ask an agent to run an arbitrary 'one-command setup' with unrestricted root access.

## Unresolved facts (fill before deployment)
- Exact Dell MAC, BIOS, storage health and RAM layout; actual Proxmox version.
- TP-Link subnet, DHCP range, VLAN/firewall feature availability; Tailscale grants.
- QNAP actual free space, RAID type, backup availability, share paths, NFS or SMB method, account IDs.
- Domain registrar/DNS, whether managed production hosting is acceptable for the public app.
- Telegram bot approval identity; GitHub org/repositories and permissible agent repository list.
- Exact current API model pricing, rate limits, subscription authentication and Paperless AI privacy policy.

## Helpful official documentation
- Proxmox automated installation: https://github.com/proxmox/pve-docs/blob/master/pve-installation.adoc
- Paperless setup: https://docs.paperless-ngx.com/setup/
- Paperless first-party AI: https://docs.paperless-ngx.com/faq/
- Paperless-AI (external, currently unmaintained): https://github.com/clusterzx/paperless-ai
- Grok connectors and custom MCP: https://docs.x.ai/grok/connectors
- Grok Bot overview: https://docs.x.ai/grok-bot/overview
