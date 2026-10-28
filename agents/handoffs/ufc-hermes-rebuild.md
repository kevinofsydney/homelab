# Task: rebuild Hermes and the UFC agent on the homelab after the VPS loss

Updated: 2026-10-27 (n8n state refreshed after the fight-card fix and pipeline changes; workflow allowlist dropped)
Status: homelab rebuild awaiting input (placement decision, secrets, approvals); nothing built or deployed. The urgent n8n fight-card outage is resolved in cloud n8n (see below)
Branch or worktree: none yet; this document is the plan
Base/current commit: verify with `git log -1` before acting
PR: none for the build itself

## Source and what changed

On 2026-10-27 the operator supplied a handoff, written from a previous agent session, for rebuilding services that ran on the BinaryLane VPS `agent-vps`. That VPS has been **destroyed**. No code, config, state or secrets survived, and no copy of the custom UFC agent's source exists elsewhere. This file records that handoff's requirements adapted to this repository. Where the two conflict, the corrections below apply.

The previous rule "preserve BinaryLane / do not migrate BinaryLane" no longer covers `agent-vps`: the operator has moved these two services to the homelab. Leave any other BinaryLane resources untouched.

### Corrections to the supplied handoff

| Supplied handoff says | Repository reality and adapted plan |
| --- | --- |
| Install Ubuntu Server 26.04 on the OptiPlex's **full disk** | The OptiPlex already runs Proxmox (`pve1`) with dev VM 100 and home-services VM 130 running Paperless. **Do not reinstall the host.** Run the services in new Proxmox guests cloned from the verified template with `scripts/clone-application-vm.sh` (plan first, `--apply` only with approval) |
| Ubuntu 26.04 LTS | The verified template is Ubuntu 24.04.5. Proposed: reuse it. A 26.04 template would need its own image provenance review (`proxmox/template.md`) |
| Hermes v0.22.4; pick the latest stable | v0.22.5 (`bf0203a…`) is already reviewed and pinned in `ansible/roles/hermes_cli`. Reuse it unless a newer stable is at least a few days old and passes the same review. The dormant Hermes on dev VM 100 must **not** be activated: one process per Telegram bot token |
| nftables in one host to keep Hermes off the LAN and off the gateway port | Proposed: separate guests (below), with LAN egress enforced by the Proxmox firewall on the guest NIC, which a compromised guest cannot change. Keep the in-guest checks as defence in depth |
| BIOS sleep, AC recovery and Wake-on-LAN | Still applies to the Proxmox host; record it in `docs/preflight.md` evidence. All guests currently have autostart **off**; the bots need `onboot=1` and a startup order, which is a hypervisor change needing approval |
| Timezone Australia/Melbourne | Set it per guest in Ansible; confirm with the operator, since the host location is not recorded |

### Proposed placement (needs operator decision)

| Guest | Runs | Starting size | Reason |
| --- | --- | --- | --- |
| `ufc-agent` (new VMID, check unused) | `ufc-gateway` and `ufc-bot` system services | 1 vCPU, 1 GiB, 16 GiB | Holds the n8n API key; no Docker, no coding agent |
| `hermes` (new VMID) | Hermes gateway with rootless Docker sandboxes | 4 vCPU, 8 GiB, 80 GiB | Untrusted repository content and shell access; may reach only the internet |

Before cloning, re-check SSD free space and RAM against `docs/architecture.md` (20% SSD headroom, 4–6 GiB host reserve). Expected guest total is 21 GiB RAM. If the operator prefers one guest, follow the supplied handoff's single-host design: separate users, rootless Docker, and nftables blocking RFC1918 and `127.0.0.1:8765` for the `hermes` UID and its slirp4netns traffic.

## Fixed rules carried over

- n8n scope: **all workflows** (owner decision 2026-10-28). The earlier `UFC | ` name scope and workflow ID allowlist no longer apply to Hermes. The custom UFC agent's read-only gateway, if it is ever rebuilt, keeps its own narrower design.
- Never print secrets or ask for them in chat; never commit them. The operator enters each one on the guest through a hidden-input helper. Report name, set/unset and length only.
- Do not change the operator's local `ufc_dashboard` repository. Put the new UFC agent source in its own private repository only if the operator asks.
- Hermes gets no root, sudo, `docker` group, `/etc/ufc-agent` access, gateway token, or ability to edit the gateway or policy.
- One machine or process per Telegram bot token.
- Confirm before outward-facing or hard-to-reverse steps: publishing an n8n workflow, revoking old keys, sending Telegram messages.
- Repository rules still apply: explicit approval for new VMs, firewall changes, credential changes and production deployment.

Site values: keep the n8n tenant base URL (`N8N_BASE_URL`) and the owner's numeric Telegram ID (`OWNER_TELEGRAM_ID`) in ignored `config/site.json` or on the guest, not in this repository. The supplied handoff has both.

## Resolved: n8n fight-card outage (superseded fix)

Status: resolved in cloud n8n on 26–27 Oct 2026 (UTC) by an agent session with an n8n MCP token, each publish approved by the operator in that session. Transcripts are captured and analysed again for UFC Fight Night: Moicano vs Nolan. This needed no homelab work.

The fix described in the earlier handoff (new extraction selectors plus [build-verified-ufc-card-v3.js](ufc-hermes-rebuild/build-verified-ufc-card-v3.js)) was **not applied and should not be**. Its diagnosis was incomplete, and the live builder now covers the same cases plus more. v3 also labels cards `ufc-fight-card-v3`, which the card readiness check (**Classify Existing Fight Card**, which only accepts `ufc-fight-card-v2`) would reject, and it would drop the bout-ID and change-detection logic described below. The file is kept for history only.

Actual diagnosis:
- n8n Cloud runs in Frankfurt. ufc.com picks its edition from a geo cookie, `STYXKEY_region=GERMANY.DE.de.Default`, and its cache varies on that cookie (`Vary: Cookie`). The **German edition** listed the card without `#main-card`/`#prelims-card` sections, left the broadcaster `data-timestamp` empty, and later left out one bout (Erosa vs Lee). The English editions had the sections. `Accept-Language` has no effect.
- The empty timestamp made **Build Verified UFC Card** throw "Official UFC card date does not match the selected event". That failed `svc.ensure_event_spreadsheet` and so `UFC | 2.` twice a day from 25 Oct.
- Separately, a Google Drive per-minute quota error failed `UFC | 1.` and `svc.ensure_event_spreadsheet` once on 25 Oct. It cleared on its own.

What is live now (verify in n8n before relying on it):
- **English edition:** every ufc.com fetch sends `Cookie: STYXKEY_region=USA.US.en.Default`. These are the official-card and athlete-profile fetches in `svc.populate_fight_card`, the card fetch in `svc.detect_card_changes`, and the events page in `UFC | 4.`. They were checked from n8n's servers: the English edition returned 7 prelims, against 6 without the cookie.
- **Card builder** (`svc.populate_fight_card` → **Build Verified UFC Card**, still `ufc-fight-card-v2`):
  - Uses UFC's sections when present.
  - Otherwise uses the flat list, with ESPN start times deciding main card vs prelims.
  - UFC is the source of truth for bouts, names and order. ESPN supplies rounds and weight class.
  - Fighters match on full name, then on surname when that is unique (for example Zachary/Zach).
  - ESPN-only bouts are reported, not added.
  - It reports "pending" (no write) only if ESPN cannot separate the segments.
- **Stable bout IDs:** Fight Card column I holds `bout_id` (UFC's own ID, for example `ufc:13133`; `card:<names>` for cards entered by hand). Picks, Props and Fight Analysis rows carry `bout_id`, and their IDs use it (`video|pick|ufc:13133`) rather than `fight_order`. `UFC | svc.sync_bout_ids` keeps this consistent before each analysis run. The template spreadsheet has the `bout_id` headers; the operator added them by hand because the Sheets credential is blocked from HTTP Request nodes, which a grid-widening call would need.
- **Card change handling, run by `UFC | 3.` before analysis:**
  - `svc.detect_card_changes` compares the sheet with the official card and records changes in `ufc_fight_card_state`.
  - `svc.apply_card_changes` applies additions, re-ordering and detail changes at once.
  - A removal waits until two checks in a row agree **and** ESPN has dropped the bout. More than three removals at once need review.
  - Picks for removed bouts are marked `VOID_CARD_CHANGE`; `UFC | 6.` and `UFC | 7.` ignore them.
  - Videos that mention a new bout are flagged `CARD_CHANGED` for re-analysis.
  - One Telegram summary is sent per applied change.
- **Readiness guard:** `UFC | 3.` checks the fight card first and skips analysis, without using attempts, while the card is not ready.
- **Failures and health:**
  - `svc.alert_failure` alerts for every workflow named `UFC | …`.
  - It groups failures into incidents in the `ufc_incidents` data table and suppresses repeats (at most once a day; a sub-workflow and its caller alert once).
  - It retries temporary errors (quota, rate limit, 5xx, timeouts) once after 5 minutes in `UFC | 2.`, `3.` and `7.`.
  - `UFC | svc.health_sweep` runs every 30 minutes for problems that raise no error, and resolves cleared incidents.
  - Only the two Drive nodes in `svc.ensure_event_spreadsheet` have node-level retries. The earlier plan's retries on every read and GET node were not applied.

Not carried over from v3: passing ESPN-only bout warnings into the Telegram summary. The builder records them (`espn_only_bouts`) but no message shows them yet.

Proposed next step (not built): stage 2 of a self-healing design. A read-only n8n Agent diagnoses new incidents through the n8n MCP server and posts its findings to Telegram. Later stages would propose fixes for approval. This partly overlaps the deferred "propose/test/approve/apply pipeline" in the UFC agent specification below; reconcile the two before building either.

## UFC workflow inventory (reference, not an allowlist)

n8n project `<n8n-project-id>`, UFC folder `<n8n-folder-id>`. IDs as of 2026-10-27; search for `UFC | ` for the current set. Temporary `TMP | …` test workflows were archived.

| Workflow | ID |
| --- | --- |
| UFC \| 1. Set Active UFC Event (Sunday nights) | `mxXosIjmMSiItiYM` |
| UFC \| 2. Extract Picker Video Transcripts | `y20ZZYzBVS6y8kC0` |
| UFC \| 3. Analyse Picker Video Transcripts | `BvLnPFMwQ2vhPkgv` |
| UFC \| 4. Add New UFC Events | `MWmlPIyBDUKoheXO` |
| UFC \| 5. Telegram Command Router | `MabSJBF0Vt6sMICp` |
| UFC \| 6. UFC Consensus Picks (weighted) | `VkgPostfkMxFPWj6` |
| UFC \| 7. Grade Picks | `PulwhLsIZhfvCGxl` |
| UFC \| 8. Picker Leaderboard | `YeYpgLGiYlzCTopn` |
| UFC \| 9. OpenRouter Balance | `f2CKNtQUpZ5Rm80Z` |
| UFC \| svc.alert_failure | `SrL8ScYMIBiJ9Gki` |
| UFC \| svc.apply_card_changes (new) | `jWFGMw2faC2zLseh` |
| UFC \| svc.check_event_spreadsheet | `GQs7zaGeF1vZBRaj` |
| UFC \| svc.detect_card_changes (new) | `UDRrGRyeFPL9Lk3S` |
| UFC \| svc.ensure_event_spreadsheet | `LuALxCWYzByUY2Iq` |
| UFC \| svc.health_sweep (new) | `oC1PuXuYb1pdeO0J` |
| UFC \| svc.populate_fight_card | `SBBK0hOGx2uPYpm4` |
| UFC \| svc.retry_video | `G1EMMFVSzpGE4q3Q` |
| UFC \| svc.sync_bout_ids (new) | `ya1uS9XFsrlhq6e3` |

New data table: `ufc_incidents` (`bPLtuvVfcVLTLv2h`). `ufc_fight_card_state` gained the change-tracking columns `change_status`, `change_checked_at`, `pending_change_json`, `pending_change_fingerprint`, `pending_seen_count`, `pending_first_seen_at` and `official_card_json`.

## Secrets to re-issue

All old values were on the destroyed disk; treat them as exposed. The operator creates each new value and loads it with the guest's helper; revoke the old one after the new one works.

| Name | Guest | Notes |
| --- | --- | --- |
| UFC bot Telegram token (`the UFC bot`) | ufc-agent | BotFather → Revoke current token |
| Hermes Telegram token (`the Hermes bot`) | hermes | BotFather → Revoke current token |
| OpenRouter key (UFC) | ufc-agent | Old key revoked 2026-10-27; new key with US$5/month provider limit |
| OpenRouter key (Hermes) | hermes | Old key revoked 2026-10-27; new key with US$10 limit |
| OpenCode Go key(s) | both | Old key revoked by the operator on 2026-10-27; create new key(s) with Extra usage disabled |
| DeepSeek key | hermes | Delete old key |
| GitHub fine-grained PAT | hermes | All repositories, Contents and Pull requests read/write only, ≤90 days. Note: broader than `agents/permissions.md` recommends for workers; the operator approved it for Hermes |
| n8n MCP token | hermes | JWT with `aud: mcp-server-api`; reject `oc_…` and `aud: public-api` |
| n8n API key | ufc-agent | JWT with `aud: public-api`; read scopes only if offered |
| Gateway token | ufc-agent | Generated on the guest; never shown |

Helpers (root, mode 700, Python `getpass`): `hermes-secret` writes `/home/hermes/.hermes/.env` (hermes, 600) for `TELEGRAM_BOT_TOKEN`, `OPENCODE_GO_API_KEY`, `OPENROUTER_API_KEY`, `DEEPSEEK_API_KEY`, `GITHUB_TOKEN`, `N8N_MCP_TOKEN`; `ufc-secret` writes `/etc/ufc-agent/<file>` (root 600, directory 700) for `telegram.token`, `openrouter.key`, `opencode-go.key`, `n8n.key`, `gateway.token`. Both strip a leading `Bearer `, validate shape, write atomically, refuse to overwrite without `--replace`, take no secret on the command line and print length only. `ufc-secret n8n.key` accepts a key only if `GET /api/v1/workflows/mxXosIjmMSiItiYM` returns a name starting `UFC | `. `hermes-secret GITHUB_TOKEN` rejects `ghp_` classic tokens.

## Hermes configuration

Install with the existing role (`ansible/playbooks/assistant-tools.yml`) on the hermes guest, then add as reviewed changes:

- User `hermes`: home 0700, password locked, no sudo, lingering enabled.
- Rootless Docker for `hermes` only; no root daemon (`docker.service`, `docker.socket`, `containerd.service` disabled); `DOCKER_HOST=unix:///run/user/<uid>/docker.sock`; slirp4netns with `--disable-host-loopback`. Note the repository's `docker_staged` role installs rootful Docker CE and must not be reused unchanged.
- `hermes config set` values: model `opencode-go` / `deepseek-v4.1-flash` (verify the ID against the Go catalog); terminal backend `docker` with a `nousresearch/hermes-sandbox` tag pinned to the Hermes release, `docker_forward_env: [GITHUB_TOKEN]`, volume `/home/hermes/workspaces:/workspace/projects`, no extra args, no cwd mount, not host user, non-persistent containers, 2 CPU, 4096 MB, timeout 900; approvals `manual`, timeout 300, deny force-push, `+refspec` push, branch deletion and `curl|sh`/`wget|sh`; checkpoints on; secret redaction on; telemetry off; skills from `/etc/hermes-skills`.
- `.env` non-secret values: `TELEGRAM_ALLOWED_USERS` and `GATEWAY_ALLOWED_USERS` = `OWNER_TELEGRAM_ID`. Never set `GATEWAY_ALLOW_ALL_USERS`.
- n8n MCP server `${N8N_BASE_URL}/mcp-server/http` with `Authorization: Bearer ${N8N_MCP_TOKEN}`, timeout 120, connect 30, and exactly these 19 of 58 tools: `get_workflow_details`, `get_workflow_history`, `get_workflow_version`, `get_workflow_versions_diff`, `get_workflow_execution`, `update_workflow`, `restore_workflow_version`, `prepare_workflow_pin_data`, `test_workflow`, `publish_workflow`, `execute_workflow`, `search_nodes`, `get_node_types`, `get_workflow_sdk_reference`, `get_workflow_best_practices`, `validate_workflow`, `validate_node_config`, `search_workflows`, `search_workflow_executions`. The two search tools were excluded on the VPS only to hide workflows that are now archived; the operator lifted that restriction on 2026-10-27. Still excluded: instance/project/folder/tag tools, credentials, data tables, n8n Agent tools, create/archive/move and `unpublish_workflow`. The operator approved Hermes publishing and executing UFC workflows on its own.
- `ufc-n8n` skill: a static, reviewed `/etc/hermes-skills/ufc-n8n/SKILL.md` (root 644); no generator or policy sync is needed now that there is no workflow allowlist (Hermes must still not read `/etc/ufc-agent`). Content: frontmatter `name: ufc-n8n`, description starting "REQUIRED for any n8n or UFC workflow task", `platforms: [linux]`; work only on workflows named `UFC | ` in the UFC folder, finding them with `search_workflows`; rules: read first (`get_workflow_details`, `get_workflow_history`, `get_workflow_execution`), edit drafts with `update_workflow`, validate and test before publishing, note the previous published version, report diff and new/rollback version IDs, roll back with `restore_workflow_version` + `publish_workflow` and never unpublish, `execute_workflow` only when asked or to confirm a fix, keep the `UFC | ` prefix and add no new credentials.
- Gateway: `hermes gateway install` as a user service; cap `user-<uid>.slice` (for example `MemoryMax` ≈60% of guest RAM, `CPUWeight=40`, `TasksMax=2048`).

## UFC agent specification

No source survived; write it fresh, Python standard library only, with tests first for the security boundaries.

- Two non-root system users and services, `ufc-gateway` and `ufc-bot`, enabled at boot, with `NoNewPrivileges`, `ProtectSystem=strict`, `ProtectHome`, `PrivateTmp` and explicit `ReadWritePaths`. Secrets via `LoadCredential=` from `/etc/ufc-agent/*`; the bot unit must not load `n8n.key`.
- Code `/opt/ufc-agent/` (root, 755/644): `bot.py`, `gateway.py`, `providers.py`, `balances.py`, `test_gateway.py`, `test_provider_menus.py`, `test_balances.py`. Config `/etc/ufc-agent/policy.json` (root 644) and `owner.json` (`owner_id` = `OWNER_TELEGRAM_ID`, `chat_type: private`). State `/var/lib/ufc-bot/`. Record the `gateway.py` SHA-256 after tests pass.
- `policy.json`: `version: 1`, `mode: "read_only"`†, `writes_enabled: false`, `workflow_name_prefix: "UFC | "` (no ID list), `model: "opencode-go/deepseek-v4.1-flash"`, `max_model_calls: 8`†, `per_task_reservation_usd: 0.05`†, `monthly_local_budget_usd: 4.50` (confirmed). † defaults, confirm with the operator.
- Gateway on `127.0.0.1:8765` only: constant-time bearer check; holds the n8n key; read-only endpoints for listing UFC workflows (names starting with the policy prefix), one workflow by ID, recent executions for one UFC workflow, and one execution only after verifying that its workflow is a UFC workflow. Check the name the n8n API returns for that ID; never trust a name supplied by the caller. No credential, data-table, mutation, run or arbitrary-HTTP endpoints. Reload policy on change; log requests without secrets.
- Bot: long-poll `getUpdates` with the offset in state; only the owner in a private chat, silently ignore all else. Commands `/settings`, `/providers`, `/models`, `/models WORD`, `/status`, `/workflows`, `/balance` (alias `/credits` and natural-language balance requests), `/help`. Paginated owner-only inline menus with single-use expiring nonces. Selection in `/var/lib/ufc-bot/selection.json`, default `opencode-go` / `deepseek-v4.1-flash`. Diagnose tasks get only the four gateway tools; the bot proposes changes and never edits, publishes or runs. No automatic provider fallback.
- Providers: OpenRouter chat completions with tools, cached catalog from `/api/v1/models`, US$4.50/month local reservation budget. OpenCode Go: base `https://opencode.ai/zen/go/v1` (verified 26 Oct; the old bot used `/inference/go`, record which works), descriptive User-Agent and stable `x-opencode-session` per conversation, adapters for Chat Completions, Responses, Anthropic and Gemini formats, 300 tasks/month local limit.
- Balance: only `GET /api/v1/credits` and `GET /api/v1/key`, labelled separately; missing or forbidden values show "unavailable", never zero; no model call; 15-second cache; Refresh and Settings buttons; OpenCode Go quota excluded.
- Tests (old suite had 16 balance and 22 provider/menu tests): owner-only, nonce expiry and reuse, pagination, search, unavailable balances, cache window, no model call on balance; gateway wrong token, non-UFC workflow, guessed execution from a non-UFC workflow, non-loopback bind, mutation verbs rejected.
- Deferred: the propose/test/approve/apply pipeline for extensions and workflow fixes. Do not build unless asked.

## Verification (report results, never values)

Secrets set by length only; Telegram `getMe` for both bots (never `getUpdates` while a service polls); OpenRouter `/api/v1/key` limits; DeepSeek `/user/balance`; OpenCode Go model list and a 1-token completion; GitHub `/user` fine-grained with push, and Actions secrets, `/hooks`, `/user/keys` return 403; n8n API key reads a UFC workflow; MCP `initialize`, `tools/list` = 58, `get_workflow_details` works on every `UFC | ` workflow, the gateway refuses a non-UFC or made-up ID, `hermes mcp list` shows 19 selected (mind the ~100-request MCP rate limit). Isolation: hermes cannot read UFC secrets; sandboxes cannot reach the LAN, Proxmox, QNAP or the gateway; no root Docker daemon; the bot unit has no `n8n.key`. UFC tests pass, then live `/status`, `/workflows`, `/balance` and a non-owner negative check. A test message to the Hermes bot works.

## Backups

QNAP backups are out of scope by earlier operator instruction, but this rebuild exists because there were none. Ask the operator for a destination (QNAP, cloud object storage, or Proxmox `vzdump` of both guests) before go-live. Back up `/etc/ufc-agent`, `/opt/ufc-agent`, `/var/lib/ufc-bot`, `/home/hermes/.hermes` (excluding `hermes-agent/`, `cache/`, `tools/`), `/etc/hermes-skills`, the helpers and custom units; encrypt and do one test restore.

## Open inputs

1. ~~Who applies the urgent n8n fix~~ Resolved: applied in cloud n8n by an agent session on 26–27 Oct; see above.
2. Placement: two new guests (proposed), one guest, or another option; VMIDs, sizes and autostart.
3. Ubuntu 24.04 template (proposed) or a new 26.04 template.
4. Hermes version: v0.22.5 or a newer reviewed release.
5. Policy values marked †, timezone, and `N8N_BASE_URL` / `OWNER_TELEGRAM_ID` in ignored site configuration.
6. Backup destination, and whether to bring backups back into scope for these guests.
7. Whether the UFC agent source gets its own private GitHub repository.
8. Whether new UFC workflows should be "Available in MCP" by default. The four created on 26–27 Oct have it on; there is no allowlist to keep it in step with.

## Coordination and approval

The supplied handoff records operator approvals from the earlier session for the n8n fix content (superseded by the fix described above, which the operator approved in its own session), the MCP tool scope (widened to 19 tools on 2026-10-27) and Hermes publishing UFC workflows. This repository has no approval yet to create guests, change the Proxmox firewall, enable autostart, install services, load credentials, publish n8n workflows or send Telegram messages. A handoff is not authorization.
