# Development VM: coder capabilities and package maintenance

Date: 2026-10-28. Decision record for changes made to VM 100 (`dev`) so the coding account can execute commands and maintain packages, without granting general root. Rollback for every change is listed at the end.

## Symptoms reported

- `opencode` "cannot run" on `dev`.
- Codex cannot execute shell commands as `coder`, including `sudo apt-get update`.

## What was actually wrong

The two symptoms have unrelated causes.

**1. Codex's sandbox cannot initialise on this guest.** `codex sandbox -- /bin/true` fails with `Error: Permission denied (os error 13)` for every command, which is why it looked like a blanket refusal.

Evidence gathered:

- `codex doctor` is otherwise clean (install, disk, git, search all pass).
- Codex shells out to `bwrap` (bubblewrap 0.11.1). `bwrap --dev-bind / / -- <codex> --version` works as `coder`, so bubblewrap itself is fine.
- `kernel.apparmor_restrict_unprivileged_userns` is `1` (Ubuntu 26.04 default) and `unshare -Ur` fails while it is set.
- Setting it to `0` makes `unshare -Ur` succeed, but **codex still fails**, so the AppArmor userns restriction is not the cause.
- An AppArmor profile granting `userns` to the vendored binaries (`codex-vendor`, `codex-mode-host`) loaded successfully and changed nothing; both profiles were removed again.
- `/etc/apparmor.d/bwrap-userns-restrict` and the `bwrap` profile are present and loaded.
- No seccomp filter on the account (`Seccomp: 0`), `unprivileged_userns_clone=1`, `max_user_namespaces=26216`, `NoNewPrivs: 0`.

The sandbox failure is therefore **unresolved**. It is not a configured policy, and it is not the userns restriction.

**2. `sudo` for `coder` is absent by design.** There is no `/etc/sudoers.d` entry; the "I'm sorry, coder. I'm afraid I can't do that" message is Ubuntu 26.04 `sudo-rs`'s default denial, not a custom joke. This matches [permissions](../agents/permissions.md).

**3. `opencode` is installed and works, but is not signed in.** `opencode --version` and `opencode --help` run fine as `coder`; `opencode auth list` reports "No authenticated integrations" and `opencode run` produces nothing. Sign-in was explicitly deferred earlier and remains an operator action. Note that `.124` is the application VM, not this one — it has no `coder` account at all.

## Changes applied

| Change | Purpose | Risk |
| --- | --- | --- |
| `~/.codex/config.toml`: `sandbox_mode = "danger-full-access"`, `approval_policy = "on-request"` | Lets codex run commands at all, given the sandbox fault | Model-generated commands now run unconfined **as `coder`**: no sudo, no Docker group, no management routes. The OS account and the host firewall are the boundary, not codex's sandbox |
| `/usr/local/sbin/homelab-apt-maintenance` (root:root 0755) | `apt-get update` + `-y upgrade` (+ `--force-confdef/confold`), refuses arguments, refuses non-root | An upgrade can still break the guest; recoverable from backup, and it cannot install arbitrary packages |
| `/etc/sudoers.d/60-coder-apt-maintenance` — `coder ALL=(root) NOPASSWD: /usr/local/sbin/homelab-apt-maintenance ""` | On-demand package maintenance without general sudo | The `""` form denies arguments, so `coder` cannot pass package names or apt options. Verified: `sudo -n <wrapper> install nc` is refused, bare `sudo -n true` is refused, and the wrapper itself runs |

General `sudo` remains denied. `coder` still cannot install arbitrary software, edit the firewall, read root-only files, or join Docker.

## Verified

- `sudo -n /usr/local/sbin/homelab-apt-maintenance` as `coder` runs and reports `0 upgraded, 0 newly installed`.
- `sudo -n /usr/local/sbin/homelab-apt-maintenance install nc` as `coder` is refused by sudo.
- `sudo -n true` as `coder` is still refused.
- `visudo -c` parses both `/etc/sudoers` and the new drop-in.
- No AppArmor profiles, sysctls or other tuning remain from the failed experiments (`aa-status` shows no `codex` profiles; `apparmor_restrict_unprivileged_userns` is back to `1`).

**Not verified:** a live codex command. The config is in place, but proving it needs one model-backed run by the operator (for example a throwaway prompt asking to run `id`). Do not record this as fixed until that run shows a command actually executing.

## Tooling installed

- **DeepSeek Harness (`dsh`) 0.2.1-rc.2** — installed 2026-10-28 as `coder` into the existing tree with `npm install --prefix ~/.local/ai-tools/npm --cache ~/.local/ai-tools/npm-cache --no-audit --no-fund @deepseek-ai/dsh@0.2.1-rc.2`. Source is the npm package published from `github.com/deepseek-ai/deepseek-harness`. `dsh --version` reports `0.2.1-rc.2` and `dsh --profile web --help` boots, so the CLI itself is functional.
- It is a **developer preview** (`latest` currently points at an rc): expect breaking changes, and treat upgrades as reviewed changes rather than following `latest` blindly.
- npm 11 gated the install scripts. `node-pty` needs `npm install-scripts approve node-pty` and then provides `node_modules/node-pty/prebuilds/linux-x64/pty.node`; the same is needed for `@deepseek-ai/dsh-subprocess-local`, whose `ensure-spawn-helper` postinstall materialises the spawn helper. Without those two approvals the agent can boot but cannot run subprocesses or open a terminal.
- `build-essential` was installed to make a source build possible; the prebuilt `node-pty` binary means it was not needed for this package, and it remains available for future native modules.
- Not configured: any model credential. `dsh` will need a DeepSeek (or other provider) key in `~/.dsh/.credentials.yaml`, which is an operator action.
- The pinned installer (`config/ai-cli-versions.json` plus `scripts/install-ai-cli.sh`) now covers `dsh` with a verified top-level tarball SHA-512. Its read-only `--check` verifies installed package versions and launchers, but does not hash installed contents or pin transitive dependencies.

## Risks this creates

- A prompt-injected agent can run any command that `coder` can: read the repository and any credentials in that account, use the internet, and overwrite its own files. It cannot escalate to root, but it no longer gets even the weak protection codex's sandbox would have provided.
- The apt wrapper is a standing root path. It is argument-free and fixed, but every nightly-style upgrade carries normal package-upgrade risk; the guest is also updated automatically at 03:00 by `unattended-upgrades`, so the wrapper is for on-demand use.
- Both changes are guest-local. The host firewall, the `tag:dev` tailnet policy with no grants, and the absence of management routes are unchanged and remain the real containment.

## Open items

1. Root-cause the codex/bwrap sandbox failure (strace or `bwrap` argument capture on the failing invocation) so `danger-full-access` can be reverted to `workspace-write`.
2. `opencode auth login` remains an operator action; until then opencode is unusable regardless of this change.

## Rollback

```bash
# codex: restore the previous minimal config
sudo install -o coder -g coder -m 0600 /dev/null /home/coder/.codex/config.toml
# on-demand apt maintenance
sudo rm -f /etc/sudoers.d/60-coder-apt-maintenance /usr/local/sbin/homelab-apt-maintenance
sudo visudo -c
```

Removing the sudoers drop-in restores the previous boundary immediately; no service restarts are involved.

## Related

- [Agent permission model](../agents/permissions.md)
- [Open work](../agents/todo.md)
- [Shared context](../agents/context.md)
