---
name: agent-setup
description: Install, refresh, or remove the packaged planner, grunt, builder, reviewer, and hall-monitor agents, plus Claude Code's git-janitor and comment-janitor agents, in one project for Claude Code, Codex, and Cursor.
disable-model-invocation: true
argument-hint: "[remove] [path]"
---

# Agent setup

Copy the packaged agents into one project. Nothing is installed globally.

1. Use the given path, otherwise `git rev-parse --show-toplevel`.
2. From this skill's directory, run `python3 scripts/install.py --dest <git-root>`; add `--remove` when the first argument is `remove`, or `--hosts claude,codex` to limit hosts. It writes the agents into `.claude/agents/`, `.codex/agents/`, and `.cursor/agents/`, lists them in `.git/info/exclude` and `.worktreeinclude`, and strips the orchestrator entry agent-setup 2.x added. It refuses a path whose `.claude`, `.codex`, or `.cursor` folder is the user-wide one. When it refuses a same-named agent it did not write, ask before rerunning with `--force`.
3. List the other files in the agent folders. For any that duplicates a role here, such as an older orchestrator or coder agent, ask, then delete the confirmed ones.
4. Check: the `follow-the-rules` skill resolves on each host; `pi auth check --provider <Pi's defaultProvider> --json` reports `ready`, or grunt falls back to builders; Read the repository's `AGENTS.md` for the gate, default branch, and worktree rules the orchestrator will quote; report any it lacks.
5. Show the user only the block the script prints. Add a line only for something unexpected: a refusal, a question from step 2 or 3, or a failed check. Tell the user to run `/reload-plugins` or restart, since agents added mid-session are not registered until then; check that `builder` resolves.
