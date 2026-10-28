#!/usr/bin/env python3
"""Interactively add Hermes credentials without putting secrets in arguments."""
import argparse
import base64
import getpass
import json
import os
import pwd
from pathlib import Path
import re
import stat
import sys
import tempfile

FIELDS = {
    "telegram": ("TELEGRAM_BOT_TOKEN", re.compile(r"[0-9]+:[A-Za-z0-9_-]+")),
    "openrouter": ("OPENROUTER_API_KEY", re.compile(r"sk-or-[A-Za-z0-9_-]+")),
    "owner": ("TELEGRAM_ALLOWED_USERS", re.compile(r"[1-9][0-9]{0,19}")),
    "exa": ("EXA_API_KEY", re.compile(r"[A-Za-z0-9_-]{16,128}")),
    "github": ("GITHUB_TOKEN", re.compile(r"github_pat_[A-Za-z0-9_]{20,255}")),
    "n8n-mcp": ("N8N_MCP_TOKEN", re.compile(r"[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+")),
}


def jwt_audience(token):
    """Return the unverified `aud` claim of a JWT, or None if it cannot be read."""
    try:
        payload = token.split(".")[1]
        claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    except (IndexError, ValueError):
        return None
    audience = claims.get("aud") if isinstance(claims, dict) else None
    return audience if isinstance(audience, str) else None


def check_value(field, value):
    """Return an error message when a well-formed value is still the wrong kind of credential."""
    if field == "n8n-mcp" and jwt_audience(value) != "mcp-server-api":
        return "Not an n8n instance MCP access token (expected aud mcp-server-api; an n8n REST API key has aud public-api)"
    return None


def write_value(home, key, value, replace=False):
    """Preserve existing dotenv entries, refuse links/duplicates and write atomically."""
    directory = Path(home) / ".hermes"
    if directory.is_symlink():
        raise ValueError("Hermes configuration directory must not be a symlink")
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(directory, 0o700)
    target = directory / ".env"
    if target.is_symlink():
        raise ValueError("Refusing a symlinked .env")
    if target.exists() and (not target.is_file() or target.stat().st_uid != os.geteuid()):
        raise ValueError("Existing .env must be a regular file owned by this user")
    lines = target.read_text(encoding="utf-8").splitlines() if target.exists() else []
    pattern = re.compile(r"^\s*(?:export\s+)?" + re.escape(key) + r"\s*=")
    matches = [index for index, line in enumerate(lines) if pattern.match(line)]
    if len(matches) > 1:
        raise ValueError("Duplicate entries require manual review")
    if matches and not replace:
        raise ValueError("Entry exists; use --replace to update it")
    line = f"{key}={value}"
    if matches:
        lines[matches[0]] = line
    else:
        lines.append(line)
    fd, temporary = tempfile.mkstemp(prefix=".env.", dir=directory)
    try:
        os.fchmod(fd, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write("\n".join(lines) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, target)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("field", choices=FIELDS)
    parser.add_argument("--replace", action="store_true")
    args = parser.parse_args()
    if pwd.getpwuid(os.geteuid()).pw_name != "hermes":
        parser.exit(2, "Run as the hermes account; nothing saved.\n")
    key, pattern = FIELDS[args.field]
    if not sys.stdin.isatty():
        parser.exit(2, "Interactive terminal required; nothing saved.\n")
    value = getpass.getpass(f"Enter {args.field} value (input hidden): ").strip()
    if not pattern.fullmatch(value):
        parser.exit(2, "Invalid value format; nothing saved.\n")
    problem = check_value(args.field, value)
    if problem:
        parser.exit(2, f"{problem}; nothing saved.\n")
    try:
        write_value(Path.home(), key, value, args.replace)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Could not save value: {error}\n")
    print(f"Saved {key}; value was not displayed.")


if __name__ == "__main__":
    main()
