# killall-agents

Public agent catalog and per-project agents for Claude Code, Codex, and Cursor. Keep credentials, machine-specific settings and runtime state out of this repository.

The project agents' source is `factory/claude/`; `scripts/build_agents.py` writes the Codex and Cursor copies beside it, and the per-host Codex models live in that script. `skills/agent-setup/scripts/install.py` copies `factory/` into one project. The orchestrator is the `orchestrate` skill, not an agent. Keep the lane state location and the `<!-- killall-agents -->` / `# killall-agents` ownership markers stable.

Run from the repository root:

```sh
python3 scripts/build_agents.py --check
python3 skills/agent-setup/scripts/test_install.py
git diff --check
```

`skills/follow-the-rules/` is an independent copy from [killall-skills](https://github.com/killallgit/killall-skills/tree/a016d77ff5f86821f0292a5a00dbf4600b0d8a15/skills/follow-the-rules); preserve its relative reference links. The git-janitor agent still requires the separately installed `killall-skills:git-janitor` skill.

Pending grunt and setup TUI work is tracked in `tasks/todo.md`.
