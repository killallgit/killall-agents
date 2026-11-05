---
name: setup-agents
description: Install, refresh, or remove the planner, grunt, builder, and reviewer lane agents in one project for Claude Code, Codex, and opencode, each with its own pinned model.
disable-model-invocation: true
argument-hint: "[remove] [path]"
---

# Set up agents

Copy the lane agents into a project, one file per tool, with that tool's model from `factory/models.toml`.

1. The project is the given path, otherwise `git rev-parse --show-toplevel`. Run it from the main checkout, not a linked worktree, since the Git exclude file is shared.
2. From this skill's directory, run `python3 scripts/install.py --dest <git-root>`. Add `--tools claude,codex` to limit the tools (copies for the others are removed), `--remove` when the first argument is `remove`, and `--force` only after the user agrees to replace a same-named agent it did not write. It writes into each tool's `agents/` folder, lists the files in `.git/info/exclude` and `.worktreeinclude`, removes copies from older versions, and keeps every file it did not write.
3. List the other files in the project's agent folders. For any that duplicates a role here, such as an older orchestrator or coder agent, ask, then delete the confirmed ones.
4. Check: the `follow-the-rules` skill resolves on each tool; `pi auth check --provider <Pi's defaultProvider> --json` reports `ready`, or grunt falls back to builders; read the repository's `AGENTS.md` for the gate, default branch, and worktree rules the orchestrator will quote, and report any it lacks.
5. Show the user only the block the script prints. Add a line only for something unexpected: a refusal, a question from step 3, or a failed check. Tell the user to run `/reload-plugins` or restart, since agents added mid-session are not registered until then; check that one installed agent resolves.
