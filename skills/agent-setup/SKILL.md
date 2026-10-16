---
name: agent-setup
description: Install, refresh, or remove the packaged planner, grunt, builder, reviewer, and hall-monitor agents in one project for Claude Code, Codex, and Cursor.
disable-model-invocation: true
argument-hint: "[remove] [path]"
---

# Agent setup

Copy the packaged agents and the orchestrator entry into one project. Nothing is installed globally.

1. Use the given path, otherwise `git rev-parse --show-toplevel`.
2. From this skill's directory, run `python3 scripts/install.py --dest <git-root>`; add `--remove` when the first argument is `remove`, or `--hosts claude,codex` to limit hosts. It writes:
   - the agents into `.claude/agents/`, `.codex/agents/`, and `.cursor/agents/`;
   - the orchestrator entry, which tells the top-level session to load the `orchestrate` skill: a marked block in `CLAUDE.local.md`, a marked `developer_instructions` block in `.codex/config.toml`, and `.cursor/rules/killall-orchestrator.mdc`;
   - every path above into `.git/info/exclude` and `.worktreeinclude`.

   It deletes its own files a host no longer gets and undoes agent-setup 1.x. When it refuses a same-named agent it did not write, ask before rerunning with `--force`. When `.codex/config.toml` already sets `developer_instructions`, ask whether to move them into `AGENTS.md` or leave Codex out.
3. List the other files in the agent folders. For any that duplicates a role here, such as an older orchestrator or coder agent, ask, then delete the confirmed ones.
4. Check: the `follow-the-rules` skill resolves on each host; `pi auth check --provider <Pi's defaultProvider> --json` reports `ready`, or grunt falls back to builders; Codex trusts the project and can write to the lane state folder (`codex --add-dir <folder>`). Read the repository's `AGENTS.md` for the gate, default branch, and worktree rules the orchestrator will quote; report any it lacks.
5. Report the files written and removed, and every check that failed.
