# Private access and provider setup

## Scope

On 2026-10-27 the operator requested: "Let's skip QNAP backups for now, but keep going." QNAP backups and restore testing are deferred; no NAS mount, backup job or retention policy is created by this phase. Continue development-tool setup under that deferral. This does not declare the VM backed up or expand production/public-ingress authorization.

The separate `private-access.yml` playbook installs Tailscale in the development guest from its [official signed Ubuntu repository](https://pkgs.tailscale.com/stable/#ubuntu-noble), pinning 1.104.2 and the reviewed signing-key checksum. It starts only the client daemon. The signing key fingerprint reviewed over HTTPS was `2596A99EAAB33821893C0A79458CA832957F5868`. Check mode skips package/service operations before the repository/package exists; a subsequent full zero-change check is required.

Review with `ANSIBLE_CONFIG=ansible/ansible.cfg .local/venv/bin/ansible-playbook -i ansible/inventory/hosts.yml ansible/playbooks/private-access.yml --check --diff`, then apply only within authorized guest scope. Enrollment is a separate interactive action:

```sh
sudo tailscale up --accept-dns=false --accept-routes=false --ssh=false --timeout=15m
```

Use the printed link to select the existing tailnet. Do not commit enrollment links, one-time codes, node keys or authentication files. These options retain the existing guest DNS path, decline incoming subnet routes, and retain ordinary SSH key authentication. No exit node or subnet routes are advertised. Do not enable Funnel, Serve, Tailscale SSH, subnet routing or change tailnet policy as part of this phase. Verify actual policy before claiming private access is restricted; LAN isolation is a separate pending change.

## Interactive coding accounts

From a terminal in this checkout, `python3 scripts/connect-development.py coder` opens a `coder` login through the admin account. The helper uses the observed IP and verified known-hosts file in ignored `config/site.json`, so it does not require QNAP inventory. It enforces host-key checking and uses the operator's existing SSH identity. It never copies credentials or opens root SSH on a guest. Use the standard `ssh -t` equivalent if working without Python.

For Codex: `python3 scripts/connect-development.py codex-login` starts [official device authentication](https://learn.chatgpt.com/docs/auth). Complete the printed URL/code in your own browser and then run `codex login status` as `coder`. If device authentication is disabled, enable it in your account/workspace settings or use a separately reviewed SSH-forwarded browser login. Do not copy the laptop's cached credentials into this VM. Do not run a second login while one is already waiting.

For OpenCode: `python3 scripts/connect-development.py opencode-login` starts its supported integration login. Confirm which provider/subscription is intended, then follow the [OpenCode provider guide](https://dev.opencode.ai/v2/docs/providers/). Enter API keys only in the supported terminal form; never in chat, shell command arguments or Git. Do not use `auth export`, which prints secrets. No paid model invocation is part of binary/login verification.

The operator explicitly chose to leave OpenCode sign-in for later on 2026-10-27. Preserve that preference; do not launch its login flow unless requested.

## Hermes preparation

The intended upstream was resolved from the official documentation to [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent). Reviewed stable release `v0.22.5` resolves to `bf0203a794a07aac3ff764972ab9087baa4e4f4e`. The exact installer is checksum-verified; its lockfile-driven package manager verifies dependency hashes. The separate `assistant-tools.yml` playbook installs it under a locked, non-sudo `hermes` account with a private home, separate from Codex/OpenCode credentials.

The installer runs unprivileged with `--non-interactive --skip-browser --skip-computer-use`, a fixed source commit and user-local source directory. Those options skip provider/setup prompts, messaging service installation and optional browser/computer-use tools; they are not a sandbox or a tool authorization policy. No model, provider key or Telegram token is supplied by Ansible. An existing complete installation at another commit is refused rather than silently upgraded. Partial installs remain for inspection/retry.

The first install reached the pinned source/runtime but failed because its managed Node needed `libatomic.so.1`. The unprivileged account's attempted sudo fallback was rejected. The role now installs Ubuntu's `libatomic1` explicitly through the administrative package task; the Hermes account retains no sudo access.

Before activating Hermes, choose the model/provider and explicit spend ceiling, obtain the Telegram numeric-user allowlist and bot token through a secret-safe channel, and review the enabled tools. The gateway remains off until those controls and management-route isolation are tested. No infrastructure/deployment credentials, host Docker socket, NAS mounts or administrative groups belong in this account. No outbound Telegram messages are authorized by this installation phase.

## Evidence to record

Record installed versions/commit, account groups, absence of sudo, dormant gateway state, Tailscale backend state, preserved DNS/route/SSH preferences and subsequent zero-change Ansible results. Record only login status, never credentials. Provider login, tailnet enrollment and model-backed checks remain pending until verified. QNAP backup deferral remains explicit in shared context.

2026-10-27 evidence: Tailscale 1.104.2 installed; second installation check returned `ok=8 changed=0 failed=0`. Before browser approval its backend was `NeedsLogin`, with CorpDNS, RouteAll and RunSSH false and no advertised routes. Codex device login was started; latest status remained not logged in. Hermes installer completed at the pinned commit; `hermes --version` reports v0.22.5 and Python 3.14.9 from a fresh `hermes` login. Only the `hermes` group is assigned, sudo is rejected, the home is mode 0700, and no Hermes process/system service was present. No credentials or messages were supplied to Hermes.

Hermes final check returned `ok=8 changed=0 failed=0 skipped=3`; actual source/version verification was performed separately because check mode intentionally skips installer and source-read/assert commands. Source validation passed all 17 safety tests, 21 JSON/YAML parses, four playbook syntax checks and whitespace checks. The guest connection helper was also checked with a mocked SSH subprocess to confirm the fixed guest account, verified known-hosts option and absence of shell interpolation.
