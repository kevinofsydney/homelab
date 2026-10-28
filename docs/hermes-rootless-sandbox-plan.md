# Hermes rootless sandbox: installation proposal

Status: **deployed and verified 2026-10-28** (see [Deployment evidence](#deployment-evidence-2026-10-28)). Original proposal text follows. The owner wants Hermes to work on code and recover after reboots. The guest has no Docker daemon, Docker socket, `newuidmap` or `slirp4netns`. The `hermes` account has a 65,536-entry subordinate UID range and GID range, but no lingering user manager. The guest has cgroup v2 and AppArmor active. The VM-specific Proxmox firewall is applied, but unrestricted public IPv4 egress and the absence of a tested sandbox prevent gateway activation.

## Scope for approval

On VM 101 only, install the reviewed Docker CE packages and rootless dependencies (`docker-ce-rootless-extras`, `uidmap`, `slirp4netns`); enable lingering for the `hermes` user; set up the **user-owned** rootless Docker service and socket. This creates container networking inside the guest. Keep the system-level Docker daemon, socket and containerd stopped and disabled; do not expose the Docker API on TCP or add the user to the rootful `docker` group. Do not alter Proxmox, router or QNAP networking. Do not start the Hermes gateway or enter tokens as part of this change.

The existing `docker_staged` role documents a checksum-pinned Docker signing key and package versions, but it is for a different VM and does not install or verify a rootless setup. Do not apply it unchanged. The prepared `ansible/playbooks/hermes-rootless-packages.yml` uses explicit Docker package versions and `policy_rc_d: 101`, refuses pre-existing running rootful services, and checks that the rootful socket is absent. `ansible/playbooks/hermes-rootless-user.yml` prepares the lingering user manager and rootless service separately. Both are unapproved and have not been applied; review their complete diff before use. Review every package and apt source before applying. The Ubuntu 24.04 AppArmor profile for packaged rootlesskit must be present; do not disable AppArmor or globally relax user namespace policy. Use `DOCKERD_ROOTLESS_ROOTLESSKIT_DISABLE_HOST_LOOPBACK=true` for the user daemon, verified on the installed version.

## Acceptance and rollback

- Verify `docker info` under `hermes` reports rootless operation, that the socket is under `/run/user/<hermes-uid>/` with no TCP listener and no rootful daemon/socket, and that `hermes` has no sudo or rootful Docker group. Verify the user service is enabled and lingering is active.
- Select and pin a reviewed sandbox image by immutable digest. Launch a disposable sandbox with no Docker socket, no extra host bind mounts or production secrets. Verify it cannot reach the host, router administration, QNAP, other VMs or IPv6/CGNAT destinations; verify expected public connectivity. Test the agent's configured CPU, memory and process limits rather than assuming they work: Docker notes rootless resource limits require cgroup v2/systemd and delegated controllers.
- Validate rootless service recovery after a guest reboot before activating a gateway. Verify firewall policy and sandbox isolation again after reboot. A later owner-approved host reboot is needed to verify the full chain.
- Record package versions, service state and commands. On failure, stop and disable only the rootless `hermes` user service, disable lingering if newly enabled, and remove only resources introduced for this VM after review. Keep the currently applied Proxmox firewall and all other VMs unchanged. Package removal needs its own review; do not remove pre-existing dependencies.

This setup does **not** enforce the separate approved-public-destination objective. A host-enforced egress mechanism must be designed, separately approved and tested before activating a network-capable agent. Docker sandboxing is not a substitute for that network boundary, and neither prompts nor a tool allowlist enforce it.

## References

- [Docker rootless mode](https://docs.docker.com/engine/security/rootless/)
- [Rootless troubleshooting, including Ubuntu AppArmor](https://docs.docker.com/engine/security/rootless/troubleshoot/)
- [Rootless tips and resource limits](https://docs.docker.com/engine/security/rootless/tips/)
- [Hermes deployment plan](hermes-n8n-telegram-plan.md) and [initial firewall evidence](hermes-isolation-preparation.md)

## Preparation evidence (2026-10-28)

Both playbooks passed Ansible syntax checks. The package-stage playbook ran in check mode against VM 101: `ok=11 changed=2 failed=0 skipped=2`. It proposed the repository and key, and skipped package installation because the repository is not yet present. This does not verify package installation or start a service. The user-service playbook was syntax-checked only and requires the packages before its live check. Docker's official rootless package for the selected release was inspected locally; its setup tool starts and enables the user service, while the rootless wrapper defaults to rejecting host loopback. The user-service drop-in explicitly requests `slirp4netns` and host-loopback disabling. No sandbox image or digest has yet been selected, and no sandbox or public-destination egress test has been run.

## Image and configuration research (2026-10-28)

The locally installed Hermes source at the pinned commit sets its default sandbox to `nousresearch/hermes-sandbox:desktop`. The default configuration enables networking and persistent container storage, uses one CPU and 5120 MB memory, and forwards no explicitly listed environment variables. These are source defaults, not proof of the live guest's effective settings or any enforced resource limit. The owner-requested design calls for non-persistent sandboxes and a two-CPU/4096-MB limit; [the review-only configuration fragment](../config/hermes-sandbox.example.yml) makes these settings explicit. It deliberately contains no Git token forwarding or host workspace mount: those are separate capabilities that need scoped credential, data and isolation review before the agent can perform Git work.

Read-only official Docker Hub tag metadata returned `v0.21.7-desktop` as the newest sandbox tag and `desktop` pointing to the same manifest index on 2026-10-28: `sha256:c7d8607d076f26a64e0bd6828f74e1764af43fe3281368188459bb693bfa7567`; the Linux AMD64 child digest was `sha256:91001712f321902e61fbd8d89d08700ab3c3b151f801bde1a46fed876f54a5ce`. Docker Hub reported about 1.20 GB compressed for that architecture. No sandbox tag corresponding to the installed Hermes `v0.22.5` appeared in that response. The official [sandbox Dockerfile](https://github.com/NousResearch/hermes-agent/blob/main/docker/sandbox-desktop.Dockerfile) describes a desktop/browser stack; the published image does not include the Hermes runtime itself. This is a candidate, not an approved image: its digest provenance, compatibility, layer contents, vulnerabilities and runtime behavior remain unreviewed. Do not pull or configure it merely because metadata was recorded. Resolve a release-appropriate image and verify it before activation.

The pinned source also distinguishes a persistent shared sandbox from non-persistent per-session isolation. Even with `container_persistent: false`, prove actual lifecycle, mounts, network controls and resource enforcement through container inspection and failure tests; a YAML flag alone is not evidence of isolation.

## Deployment evidence (2026-10-28)

Rootless Docker was installed by an earlier owner-approved session whose own evidence was not committed. The state below was read live from VM 101 through the Proxmox guest agent.

- Docker 29.9.2 rootless under `hermes` (uid 1001, only group `hermes`, no sudo): `systemctl --user` `docker` active and enabled, lingering `yes`, `docker info` security options include `rootless` and `cgroupns`, cgroup driver `systemd`. System `docker.service`, `docker.socket` and `containerd.service` inactive and disabled. Only SSH and the local resolver listen; no Docker TCP listener.
- The guest booted at 22:28 UTC with the rootless service active afterwards, consistent with the earlier session's reboot-recovery report.

Configuration applied with the owner's approval (equivalent to `ansible/playbooks/hermes-sandbox-config.yml`, run through the guest agent because the operator machine had no inventory for VM 101; the previous `config.yaml` is kept as `config.yaml.pre-hardening-20261028`):

- Image pinned by digest: `nousresearch/hermes-sandbox@sha256:c7d8607d076f26a64e0bd6828f74e1764af43fe3281368188459bb693bfa7567` (the `v0.21.7-desktop`/`desktop` index; Docker Hub publishes only desktop builds, none matching Hermes v0.22.5). Pulled into rootless Docker.
- `container_persistent: false`, `container_cpu: 2`, `container_memory: 4096`, `docker_network: true`, workspace `/home/hermes/workspaces` (0700) mounted at `/workspace/projects`, `timeout: 900`.
- Approvals `manual`, timeout 300, deny list from the handoff (force-push, `+refspec`, branch deletion, `curl|sh`, `wget|sh`); checkpoints on; secret redaction on; telemetry off; `web.backend: exa`.
- `hermes-secret` updated to accept `exa` (`EXA_API_KEY`); deployed copy matches the repository file's SHA-256.

Sandbox test (the pinned image, run as `hermes` with `--cpus 2 --memory 4096m` and the workspace mount): cgroup `cpu.max` `200000 100000`, `memory.max` 4294967296; Proxmox 8006, QNAP 443, router 80 and home-services 22 **blocked**; `api.github.com` 200 and `api.exa.ai` reachable.

Finding: the sandbox **can** connect to the Hermes VM's own LAN address on TCP 22. That traffic stays inside the guest, so the Proxmox VM firewall does not see it. **Closed 2026-10-28**; see the guest egress guard below.

Not yet verified: Hermes itself launching a sandbox session (no model provider is configured), the gateway, and any credential other than the owner ID.

## Provider, model and web search (2026-10-28)

- `EXA_API_KEY` entered by the owner via `hermes-secret exa`: one entry, length 36, `.env` owned by `hermes`, mode 600. A direct Exa `/search` call with it returned HTTP 200 and a result.
- `OPENROUTER_API_KEY` entered by the owner via `hermes-secret openrouter`: one entry. OpenRouter `GET /api/v1/key` reported `limit: 10`, `limit_reset: monthly`, `usage: 0`, not free tier.
- `model.provider: openrouter`, `model.default: deepseek/deepseek-v4.1-flash-1017` (added to `hermes-sandbox-config.yml`).
- One-shot test `hermes chat -q "Reply with exactly: HERMES_OK" -t clarify`: reply `HERMES_OK`, 8 s, no tool calls.
- One-shot test with `-t web` asking for the Hermes docs URL: the model called `web_search`, the result came back wrapped as `untrusted_tool_result`, and the reply was `https://hermes-agent.nousresearch.com/docs/`.
- Not yet tested: terminal/sandbox use from a model session, the Telegram gateway, GitHub and n8n.

Guest egress guard (todo 9, applied 2026-10-28 with the owner's approval): `config/hermes/hermes-egress.nft` is installed as `/etc/hermes-egress.nft` and loaded by `hermes-egress.service` (enabled, before the hermes user manager); `ansible/playbooks/hermes-egress-guard.yml` is the reproducible install. It adds only table `inet hermes_egress`: traffic owned by uid 1001 (the `hermes` account, which includes rootless sandboxes via slirp4netns) to 10/8, 100.64/10, 169.254/16, 172.16/12, 192.168/16, fc00::/7 and fe80::/10 is rejected, except DNS to the router on port 53, which rootless Docker uses for sandbox lookups. Loopback stays open. A first version without the DNS exception broke sandbox DNS and was corrected before use. Results, from a sandbox container and from `hermes` directly: the VM's own SSH, Proxmox 8006, router 80 and home-services 22 blocked; DNS and `api.github.com` (200) working; root's access to its own SSH unaffected; the gateway stayed active. After a `qm reboot 101` the table loaded by itself, the same sandbox tests passed and the gateway reconnected to Telegram.

## n8n MCP connection (2026-10-28, todo 11)

- The owner entered an instance-level MCP token with `hermes-secret n8n-mcp` (length 272; the helper now rejects anything whose JWT `aud` is not `mcp-server-api`). A direct MCP probe from VM 101: `n8n MCP Server 1.2.0`, protocol `2025-06-18`, 58 tools; `search_workflows` returned 22 workflows, all `UFC | ` and active.
- Hermes config: `mcp_servers.n8n` with 31 selected tools and `skills.external_dirs: [/etc/hermes-skills]`; `hermes mcp list` shows `n8n … 31 selected, enabled` and `hermes skills list` shows `n8n-workflows` as external and enabled. Previous config kept as `config.yaml.pre-n8n-20261028`. Applied through the guest agent, equivalent to `ansible/playbooks/hermes-n8n-mcp.yml`.
- Read test (`hermes chat -q`, read-only): Hermes viewed the skill, then returned `UFC | 9. OpenRouter Balance` as `f2CKNtQUpZ5Rm80Z`, published, schedule trigger `0 9,21 * * *`, 12 nodes, published version `e962135f-653e-44e7-bb88-36345cffb380`.
- Test run: `prepare_workflow_pin_data` then `test_workflow` on the same workflow produced n8n execution 2214, status success, no failed node; credentialed and HTTP nodes were pinned, so no real message or API call was made.
- Export job: the first run exported all 22 workflows (896 KB) to `/var/backups/n8n/20261028T005633Z`; every file contains a `workflow` object with `nodes` and `connections`; `hermes` gets `Permission denied` on the directory. The timer's next run was 16:35 UTC (03:35 Melbourne).
- Not yet done: importing an export back into n8n (structure checked only), and an edit-and-publish through Hermes.

## All n8n MCP tools enabled (2026-10-28)

- Owner decision: enable every n8n MCP tool. `hermes config unset mcp_servers.n8n.tools` removed the 31-tool filter (previous config kept as `config.yaml.pre-all-tools-20261028`); `hermes mcp list` shows `n8n … all, enabled`. The skill gained ask-first rules for column deletion, archiving and destructive n8n Agent actions.
- Read-only test through Hermes: `search_data_tables` returned 37 tables in project `<n8n-project-id>` and it read rows from `ufc_monitor_state`; nothing changed.
- Finding for the owner: 27 of those tables are named `legacy | …` (settings, prompts, companies, sources, runs, LLM calls and more). The legacy workflows are archived, but their data tables remain and Hermes can now read and change them. Delete or move them, or narrow the tools again, if that data should be out of reach.
- Data tables and n8n Agents are not covered by the nightly export.
