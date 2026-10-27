#!/usr/bin/env bash
# Run as the unprivileged coder user. All tools stay under ~/.local/ai-tools.
set -euo pipefail
: "${NODE_TARBALL_URL:?Set official Node.js Linux x64 tarball URL}"
: "${NODE_SHA256:?Set SHA256 from the official Node.js SHASUMS256.txt}"
: "${CODEX_VERSION:?Set reviewed @openai/codex version}"
: "${OPENCODE_VERSION:?Set reviewed @opencode/cli version}"
[[ "$(id -un)" == coder ]] || { echo 'Run as the unprivileged coder account' >&2; exit 2; }
[[ "$NODE_TARBALL_URL" =~ ^https://nodejs\.org/dist/v[0-9]+\.[0-9]+\.[0-9]+/node-v[0-9]+\.[0-9]+\.[0-9]+-linux-x64\.tar\.xz$ ]] || {
  echo 'Use an official versioned Node.js Linux x64 tarball URL' >&2; exit 2;
}
[[ "$NODE_SHA256" =~ ^[[:xdigit:]]{64}$ ]] || { echo 'Invalid Node SHA256' >&2; exit 2; }
for version in "$CODEX_VERSION" "$OPENCODE_VERSION"; do
  [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Use exact stable CLI versions' >&2; exit 2; }
done
root="$HOME/.local/ai-tools"
mkdir -p "$root/node" "$root/npm" "$root/download"
archive="$root/download/node.tar.xz"
curl --fail --location --proto '=https' --tlsv1.2 "$NODE_TARBALL_URL" -o "$archive"
printf '%s  %s\n' "$NODE_SHA256" "$archive" | sha256sum --check --status
tar -xJf "$archive" -C "$root/node" --strip-components=1
export PATH="$root/node/bin:$root/npm/node_modules/.bin:$PATH"
npm install --prefix "$root/npm" --cache "$root/npm-cache" --no-audit --no-fund "@openai/codex@$CODEX_VERSION" "@opencode/cli@$OPENCODE_VERSION"
"$root/npm/node_modules/.bin/codex" --version
"$root/npm/node_modules/.bin/opencode" --version
echo "Add $root/node/bin and $root/npm/node_modules/.bin to your shell PATH. Sign in interactively; do not copy session credentials."
