# Issue to draft PR workflow design

1. A maintainer reviews an issue and adds `ai-ready`. Creation alone does nothing. The automation also verifies the current actor's permission and waits for a protected GitHub environment reviewer.
2. A dispatcher creates a single-use job with an immutable repository/issue/commit reference and a strict allowlist. Do not interpolate issue text into shell commands or workflow YAML.
3. The worker starts as a disposable VM or container on a separate network, with no management or production routes, no host Docker socket and a time limit. It clones only the approved repository.
4. The worker creates a branch, runs repository tests/lint/security checks, and opens a draft PR. Give it a short-lived repository-scoped token with Contents and Pull requests permissions only; do not expose infrastructure secrets. The GitHub Actions `GITHUB_TOKEN` may not be sufficient for every cross-repo workflow; evaluate a narrowly scoped GitHub App.
5. Telegram receives a status/PR link through a separate notification service with no job execution privilege. No Telegram message can elevate issue readiness or deploy production.
6. For `kevinofsydney/homelab`, a trusted coding agent may review and automatically merge the exact passing PR commit under the owner's standing authorization in root `AGENTS.md`. Other repositories follow their own approval policies. Disposable workers retain their restricted token scopes; repository merge authorization does not grant them production privileges. Production deployment requires separate explicit operator approval. A deploy job uses a distinct protected environment and credentials, checks the exact commit SHA, backs up, applies the change, checks health and records rollback steps.

Do not install an automated worker until this policy has been tested on a disposable repository. Test hostile issue text, untrusted PRs, token exfiltration attempts, a blocked management route and job timeouts. See `docs/security.md`.
