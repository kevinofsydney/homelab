# Hermes credential setup

The interactive helper is installed on VM 101; it does not configure or start the gateway. Keep the bot token and OpenRouter key out of chat, Git, shell command lines and logs. Configure these only after the externally enforced isolation and sandbox gates in the [Hermes plan](hermes-n8n-telegram-plan.md) have been met. The owner must also set the OpenRouter key's agreed monthly spending limit at the provider.

Connect as `devops` to the guest's currently verified address using its verified SSH host key. The address may change until its DHCP reservation is verified. In an interactive SSH terminal, switch to the unprivileged account:

```sh
sudo -iu hermes
hermes-secret owner
hermes-secret telegram
hermes-secret openrouter
```

Enter the numeric Telegram user ID for `owner`, and the token/key only at each hidden prompt. The helper rejects non-terminal input, validates basic format, writes only to `~/.hermes/.env` with mode 0600, preserves unrelated lines, refuses duplicate entries or symlinks and never prints values. Use `--replace` only to rotate an existing value. The helper does not validate the credentials against Telegram or OpenRouter or prove the spending limit. It sets `TELEGRAM_ALLOWED_USERS` but does not itself establish a private-chat-only policy, prevent other configuration from granting access, or authorize a gateway start. Review all gateway authorization settings before activation.

To provision the helper without configuring secrets, use `ansible/playbooks/hermes-credential-helper.yml` with the private `hermes_agents` inventory. The helper source is `scripts/hermes/set-credentials.py`; the installed command is `/usr/local/bin/hermes-secret`. Do not use it from a shared or recorded terminal. If a token appears in a log or chat, revoke it with its provider and replace it.

## Telegram scope acceptance

The pinned Hermes source explicitly applies `TELEGRAM_ALLOWED_USERS` to both private and group conversations. An owner allowlist alone therefore does **not** meet the private-chat-only requirement. Before starting the gateway, verify all group-related adapter settings and paired-user grants, prevent the bot from joining groups where applicable, and test both a group message from the owner and a private message from an unauthorized sender. Both must be rejected. Do not treat an untested configuration setting or BotFather membership setting as sufficient proof on its own.

### Offline adapter diagnostic (2026-10-28)

Against the installed pinned Hermes code, `scripts/hermes/audit-telegram-auth.py` uses synthetic IDs and a mocked adapter, with `allow_from` set to one user and `group_allow_from` set to an empty list. It observed: owner private message allowed, another user's private message denied, and owner group message denied. However, the adapter's **environment-only callback fallback** accepted an owner callback with a group chat type. The diagnostic therefore exits 1, as intended for this failure. This is not an end-to-end gateway test: it does not exercise the real runner's injected authorization callback, config merging, Telegram itself, or every event type, and it does not prove that the fallback is reachable in the eventual deployment. It does show that an empty group allowlist on its own is insufficient evidence for private-chat-only enforcement.

Before activating the gateway, choose and implement a verifiable private-chat boundary covering text, commands, callback buttons, reactions and other event paths; test the actual configured gateway with authorized and unauthorized identities. Check any existing group memberships and BotFather settings, but do not rely solely on membership settings. Re-run the diagnostic using the installed Hermes runtime and synthetic data, without loading a bot token; a passing isolated diagnostic is still not an end-to-end acceptance test.

### Runner predicate follow-up

A further offline test constructed the pinned `GatewayRunner` without adapters or profile routing and patched its authorization environment to a synthetic single-owner allowlist. The owner private case was accepted, a stranger private case rejected, and the owner group case **accepted** by the real runner predicate. This is a bare runner test, not the live configured gateway. Importing the full runner also changed the earlier mocked adapter callback result, so the standalone fallback diagnostic and this runner case must not be treated as equivalent execution contexts. Test actual adapter configuration merging, injected callbacks and every message/event path before claiming a private-chat-only gateway.
