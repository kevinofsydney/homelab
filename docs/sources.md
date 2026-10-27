# Upstream documentation reviewed 2026-10-27

- [Proxmox VE administration guide](https://pve.proxmox.com/pve-docs/pve-admin-guide.pdf): cloud-init, VM management, roles, API tokens and backup storage. Verify installed version's docs before using token permissions or template commands.
- [Proxmox QEMU API source](https://git.proxmox.com/?p=qemu-server.git;a=blob;f=src/PVE/API2/Qemu.pm;hb=HEAD): resize uses PUT; POST configuration updates return an asynchronous task that must finish before the next operation.
- [Ubuntu cloud images](https://cloud-images.ubuntu.com/noble/current/): official Noble image and checksums.
- [Docker Engine on Ubuntu](https://docs.docker.com/engine/install/ubuntu/) and [Compose plugin](https://docs.docker.com/compose/install/linux/): official apt repository and Compose plugin.
- [Paperless setup](https://docs.paperless-ngx.com/setup/) and [configuration](https://docs.paperless-ngx.com/configuration/): PostgreSQL engine, broker, media/data paths and secret key. Current v3 configuration explicitly needs `PAPERLESS_DBENGINE=postgresql`.
- [Tailscale Linux install](https://tailscale.com/docs/install/linux) and [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh): interactive join and access rules. Tailscale rules do not firewall other paths on the local LAN.
- [OpenCode CLI](https://dev.opencode.ai/v2/docs/) and [tool permissions](https://opencode.ai/docs/tools/): CLI package and shell tool boundary.
- [Official OpenAI documentation for Codex](https://developers.openai.com/learn/codex) and [Codex install example](https://developers.openai.com/cookbook/examples/codex/using_goals_in_codex): Codex CLI and interactive setup. Do not assume API entitlement from a ChatGPT subscription.
- [Ansible Proxmox collection](https://docs.ansible.com/projects/ansible/latest/collections/community/proxmox/index.html): available integration; the first milestone's Python provisioner avoids collection drift and third-party Python API dependencies.
- [Ansible support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html) and [pinned ansible-core 2.21.5 release](https://pypi.org/project/ansible-core/2.21.5/): control-node Python 3.12+.

The project deliberately does not pin unknown release digests. The operator must choose and review exact image/package versions, record them in ignored configuration, and update them through a change review. Hermes, Paperless-AI, Grok and the accounting system integration require fresh compatibility checks before implementation.
