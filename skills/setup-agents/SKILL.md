---
name: setup-agents
description: Install, refresh, or remove the packaged agents for Claude Code, Codex, and Cursor. The planner, grunt, builder, reviewer, hall-monitor, git-janitor, and comment-janitor lane agents go in one project; the engineering catalog of specialist agents goes in one project or user-wide.
disable-model-invocation: true
argument-hint: "[remove] [path]"
---

# Set up agents

Copy the packaged agents into a project, or the catalog into the user-wide folders. A person at a terminal can run `python3 scripts/install.py` from this skill's directory with no flags and answer its questions: where, which tools, a multi-select of agents, and the catalog models. The steps below drive the same script with flags, because a session cannot answer those prompts.

1. Decide the selection. A plain request installs the lane agents in the project at the given path, otherwise `git rev-parse --show-toplevel`. When the user wants the engineering catalog or a custom set, ask one multi-select question for the scope (this project or user-wide), the tools (Claude Code, Codex, Cursor), and the agents (`lanes`, `catalog`, or names from `factory/catalog/`). Lane agents install per project only.
2. From this skill's directory, run `python3 scripts/install.py --yes` with `--dest <git-root>`, `--scope user|project`, `--hosts claude,codex`, `--agents lanes,catalog,<names>`, and `--model HOST:TIER=ID` to change a catalog model. Add `--remove` when the first argument is `remove`. It writes into each tool's `agents/` folder and sets each catalog agent's model, effort, tools, and sandbox for that tool. A project install lists the files in `.git/info/exclude` and `.worktreeinclude` and strips the orchestrator entry agent-setup 2.x added. It refuses a project path whose `.claude`, `.codex`, or `.cursor` folder is the user-wide one. A run adds to what is installed; add `--prune` to also remove copies it wrote that are no longer selected. It keeps every file it did not write. When it refuses a same-named agent it did not write, ask before rerunning with `--force`.
3. For a project install, list the other files in the agent folders. For any that duplicates a role here, such as an older orchestrator or coder agent, ask, then delete the confirmed ones.
4. For a project install, check: the `follow-the-rules` skill resolves on each host; `pi auth check --provider <Pi's defaultProvider> --json` reports `ready`, or grunt falls back to builders; Read the repository's `AGENTS.md` for the gate, default branch, and worktree rules the orchestrator will quote; report any it lacks.
5. Show the user only the block the script prints. Add a line only for something unexpected: a refusal, a question from step 2 or 3, or a failed check. Tell the user to run `/reload-plugins` or restart, since agents added mid-session are not registered until then; check that one installed agent resolves.
