# Hermes rootless sandbox: installation proposal

Status: **review-only; not deployed**. The owner wants Hermes to work on code and recover after reboots. The guest has no Docker daemon, Docker socket, `newuidmap` or `slirp4netns`. The `hermes` account has a 65,536-entry subordinate UID range and GID range, but no lingering user manager. The guest has cgroup v2 and AppArmor active. The VM-specific Proxmox firewall is applied, but unrestricted public IPv4 egress and the absence of a tested sandbox prevent gateway activation.

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
