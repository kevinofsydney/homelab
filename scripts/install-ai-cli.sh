#!/usr/bin/env bash
# Run as the unprivileged coder user. All tools stay under ~/.local/ai-tools.
set -euo pipefail
[[ $# -eq 0 || ( $# -eq 1 && "$1" == --check ) ]] || { echo 'Usage: install-ai-cli.sh [--check]' >&2; exit 2; }
: "${NODE_TARBALL_URL:?Set official Node.js Linux x64 tarball URL}"
: "${NODE_SHA256:?Set SHA256 from the official Node.js SHASUMS256.txt}"
: "${CODEX_VERSION:?Set reviewed @openai/codex version}"
: "${OPENCODE_VERSION:?Set reviewed @opencode/cli version}"
: "${DSH_VERSION:?Set reviewed DeepSeek Harness version}"
: "${DSH_SHA512:?Set reviewed DeepSeek Harness SHA512}"
[[ "$(id -un)" == coder ]] || { echo 'Run as the unprivileged coder account' >&2; exit 2; }
[[ "$NODE_TARBALL_URL" =~ ^https://nodejs\.org/dist/v[0-9]+\.[0-9]+\.[0-9]+/node-v[0-9]+\.[0-9]+\.[0-9]+-linux-x64\.tar\.xz$ ]] || {
  echo 'Use an official versioned Node.js Linux x64 tarball URL' >&2; exit 2;
}
[[ "$NODE_SHA256" =~ ^[[:xdigit:]]{64}$ ]] || { echo 'Invalid Node SHA256' >&2; exit 2; }
for version in "$CODEX_VERSION" "$OPENCODE_VERSION"; do
  [[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Use exact stable CLI versions' >&2; exit 2; }
done
[[ "$DSH_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$ ]] || { echo 'Use an exact DeepSeek Harness version' >&2; exit 2; }
[[ "$DSH_SHA512" =~ ^[[:xdigit:]]{128}$ ]] || { echo 'Invalid DeepSeek Harness SHA512' >&2; exit 2; }
root="$HOME/.local/ai-tools"
if [[ "${1:-}" == --check ]]; then
  node="$root/node/bin/node"
  [[ -x "$node" ]] || { echo 'Node is missing' >&2; exit 1; }
  expected_node="${NODE_TARBALL_URL##*/node-v}"
  expected_node="${expected_node%-linux-x64.tar.xz}"
  [[ "$("$node" --version)" == "v$expected_node" ]] || { echo 'Node version differs' >&2; exit 1; }
  for pair in "@openai/codex:$CODEX_VERSION" "@opencode/cli:$OPENCODE_VERSION" "@deepseek-ai/dsh:$DSH_VERSION"; do
    package="${pair%:*}"; expected="${pair##*:}"
    actual=$("$node" -e 'try { console.log(require(process.argv[1]).version) } catch (_) { process.exit(1) }' "$root/npm/node_modules/$package/package.json") || { echo "$package missing" >&2; exit 1; }
    [[ "$actual" == "$expected" ]] || { echo "$package version differs" >&2; exit 1; }
  done
  for binary in codex opencode dsh; do [[ -x "$root/npm/node_modules/.bin/$binary" ]] || { echo "$binary launcher missing" >&2; exit 1; }; done
  echo 'CHECK: installed versions and launchers match; no changes made. Installed package contents were not re-hashed.'
  exit 0
fi
mkdir -p "$root/node" "$root/npm" "$root/download"
archive="$root/download/node.tar.xz"
curl --fail --location --proto '=https' --tlsv1.2 "$NODE_TARBALL_URL" -o "$archive"
printf '%s  %s\n' "$NODE_SHA256" "$archive" | sha256sum --check --status
tar -xJf "$archive" -C "$root/node" --strip-components=1
export PATH="$root/node/bin:$root/npm/node_modules/.bin:$PATH"
dsh_archive="$root/download/dsh-$DSH_VERSION.tgz"
curl --fail --location --proto '=https' --tlsv1.2 "https://registry.npmjs.org/@deepseek-ai/dsh/-/dsh-$DSH_VERSION.tgz" -o "$dsh_archive"
printf '%s  %s\n' "$DSH_SHA512" "$dsh_archive" | sha512sum --check --status
npm install --prefix "$root/npm" --cache "$root/npm-cache" --no-audit --no-fund "@openai/codex@$CODEX_VERSION" "@opencode/cli@$OPENCODE_VERSION" "$dsh_archive"
"$root/npm/node_modules/.bin/codex" --version
"$root/npm/node_modules/.bin/opencode" --version
"$root/npm/node_modules/.bin/dsh" --version
echo "Add $root/node/bin and $root/npm/node_modules/.bin to your shell PATH. Sign in interactively; do not copy session credentials."
