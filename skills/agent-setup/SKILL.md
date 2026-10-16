---
name: agent-setup
description: Install, refresh, or remove the packaged planner, grunt, builder, reviewer, and hall-monitor agents in one project for Claude Code, Codex, and Cursor.
disable-model-invocation: true
argument-hint: "[remove] [path]"
---

# Agent setup

Copy the packaged agents into one project. Nothing is installed globally except the one guarded orchestrator line below.

1. Use the given path, otherwise `git rev-parse --show-toplevel`.
2. From this skill's directory, run `python3 scripts/install.py --dest <git-root>`; add `--remove` when the first argument is `remove`, or `--hosts claude,codex` to limit hosts. It writes `.claude/agents/`, `.codex/agents/`, and `.cursor/agents/`, deletes its own copies and agent-setup 1.x files it no longer writes, and lists the copies in `.git/info/exclude` and `.worktreeinclude`. When it refuses a same-named agent it did not write, ask before rerunning with `--force`.
3. List the other files in those folders. For any that duplicates a role here, such as an older orchestrator or coder agent, ask, then delete the confirmed ones.
4. Make sure each host's user instructions hold this line, and add it when missing: `${CLAUDE_CONFIG_DIR:-~/.claude}/CLAUDE.md` for Claude Code, `${CODEX_HOME:-~/.codex}/AGENTS.md` for Codex. Cursor has no instruction file, so give the user the line to paste under Settings → Rules → User Rules.

   > When you are the top-level session, not an agent another agent started, and this project has the `planner` and `builder` agents, you are its orchestrator: load the `orchestrate` skill before multi-step work.

5. Check: the `follow-the-rules` skill resolves on each host; `pi auth check --provider <Pi's defaultProvider> --json` reports `ready`, or grunt falls back to builders; Codex trusts the project and can write to the lane state folder (`codex --add-dir <folder>`).
6. Report the files written and removed, the instruction lines added, and every check that failed.
