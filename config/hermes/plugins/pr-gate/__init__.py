"""Hold pull request creation and merges until the owner approves in chat.

Owner decision 2026-10-28: Hermes runs with approval prompts off, but every pull
request needs the owner's go-ahead. A terminal, code or file-write call that would
open or merge a pull request is blocked unless the owner's latest message in the
same session starts with "approve". The model cannot write owner messages, so it
has to ask. This is a workflow check, not a security boundary: Hermes has sudo on
its own VM and could remove the plugin.
"""

import os
import re
import sqlite3
from pathlib import Path
from typing import Any, Optional

CHECKED_TOOLS = {"terminal", "execute_code", "write_file", "patch"}

_WRITE = r"(?:-X|--request|--method)\s*['\"]?(?:POST|PUT)\b|\s(?:-d|--data[\w-]*|--json|-f|-F|--field|--raw-field)[\s=]|requests\.(?:post|put)\(|httpx\.(?:post|put)\(|method\s*=\s*['\"](?:POST|PUT)"
PR_ACTIONS = [
    re.compile(r"\bgh\s+pr\s+(?:create|new|merge)\b", re.I),
    re.compile(r"/pulls/\d+/merge\b", re.I),
    re.compile(r"\b(?:createPullRequest|mergePullRequest|enablePullRequestAutoMerge)\b"),
    re.compile(r"/pulls\b[^\n]*?(?:" + _WRITE + ")|(?:" + _WRITE + r")[^\n]*?/pulls\b", re.I),
]
APPROVAL = re.compile(r"^\W*(?:approve|approved)\b", re.I)

BLOCK_MESSAGE = (
    "BLOCKED by the owner's pull request rule: opening or merging a pull request needs the owner's approval. "
    "Message the owner with the repository, branch, a short summary of the change and its size "
    "(or, for a merge, which PR and why), and ask them to reply \"approve\". End your turn and wait. "
    "When their next message starts with \"approve\", retry the same action. "
    "Do not look for another way to open or merge it."
)


def _strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from _strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from _strings(item)


def _is_pr_action(args: Any) -> bool:
    text = "\n".join(_strings(args))
    return any(pattern.search(text) for pattern in PR_ACTIONS)


def _latest_user_message(session_id: str) -> str:
    home = Path(os.environ.get("HERMES_HOME") or Path.home() / ".hermes")
    try:
        with sqlite3.connect(f"file:{home / 'state.db'}?mode=ro", uri=True, timeout=5) as db:
            row = db.execute(
                "select content from messages where session_id = ? and role = 'user' order by id desc limit 1",
                (session_id,),
            ).fetchone()
    except sqlite3.Error:
        return ""
    return (row[0] or "") if row else ""


def _on_pre_tool_call(tool_name: str = "", args: Any = None, session_id: str = "", **_: Any) -> Optional[dict]:
    if tool_name not in CHECKED_TOOLS or not _is_pr_action(args):
        return None
    if session_id and APPROVAL.match(_latest_user_message(session_id)):
        return None
    return {"action": "block", "message": BLOCK_MESSAGE}


def register(ctx) -> None:
    ctx.register_hook("pre_tool_call", _on_pre_tool_call)
