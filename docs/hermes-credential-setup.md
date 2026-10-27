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
