---
name: repo
description: Switch the GitHub repository you and the owner are working on. Lists the owner's repos, clones or updates the chosen one in ~/workspaces, and records it as the current repo. Invoked by the owner's /repo command in Telegram.
---

# /repo

The owner works on one repository at a time. `/repo` picks which one.

## 1. Choose the repository

- **With an argument** (`/repo <repo>`, or `owner/name`): use that repository. The owner is `kevinofsydney` unless another is given.
- **Without one:** run `python3 ~/.hermes/skills/software-development/repo/scripts/list-repos.py`. It prints `name, visibility, last push, description`, most recently pushed first, and never prints the token. Then use the clarify tool with the **4 most recently pushed** repository names as choices (the owner can tap "Other" and type any other name). Put the current repo first if it is among them. If the owner asks for the full list, send it as plain text.

If the name does not match a repository in the list, say so and offer the closest matches.

## 2. Clone or update it

Work in `~/workspaces/<name>`. Git authenticates to GitHub through the credential helper in `~/.gitconfig`; never print the token or put it in a URL.

- Not cloned yet: `git clone https://github.com/kevinofsydney/<name>.git ~/workspaces/<name>`.
- Already cloned: `git -C ~/workspaces/<name> fetch --prune`. If the working tree is clean and the checked-out branch is the default branch, `git pull --ff-only`. If there are uncommitted changes or a work branch is checked out, leave them alone and report them.

## 3. Record it

Replace any earlier "Current repo" entry in your memory with one line:
`Current repo: kevinofsydney/<name> at ~/workspaces/<name> (set <date>)`.
Until the owner switches again, run commands in that directory (`cd ~/workspaces/<name>` first, or `git -C`), and assume requests about "the code" or "the repo" mean this one.

## 4. Report

One short message: the repository, default branch, checked-out branch, the last 3 commits (`git log --oneline -3`), any uncommitted changes, and a one-line summary of what the repo is (from the README if there is one).

## Always work on a branch

Never commit to or push the default branch (`main` or `master`). For each piece of work, create a branch such as `hermes/<short-topic>`, push it, and open a pull request; opening or merging a pull request needs the owner to reply "approve" (see the PR rule in your memory).
