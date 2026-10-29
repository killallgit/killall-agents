# killall-agents

Public agent catalog and per-project agents for Claude Code, Codex, and Cursor. Keep credentials, machine-specific settings and runtime state out of this repository.

The project agents' source is `factory/claude/`; `scripts/build_agents.py` writes the Codex and Cursor copies beside it (the janitor agents are Claude-only and have none), and the per-host Codex models live in that script. `skills/setup-agents/scripts/install.py` copies `factory/` into one project, and installs the engineering catalog in `factory/catalog/` (one source file per agent, rendered per host by `catalog.py`) into a project or the user-wide folders. The orchestrator is the `orchestrate` skill, not an agent. Keep the `<!-- killall-agents -->` / `# killall-agents` ownership markers stable.

Run from the repository root:

```sh
python3 scripts/build_agents.py --check
python3 skills/setup-agents/scripts/test_install.py
python3 skills/setup-agents/scripts/test_catalog.py
python3 skills/wrap-up/scripts/test_wrap_up.py
git diff --check
```

`skills/follow-the-rules/` is an independent copy from [killall-skills](https://github.com/killallgit/killall-skills/tree/a016d77ff5f86821f0292a5a00dbf4600b0d8a15/skills/follow-the-rules); preserve its relative reference links. Keep agents out of a root `agents/` folder, which Claude Code loads on plugin install; they belong in `factory/` so only `setup-agents` installs them.

Pending grunt and setup TUI work is tracked in `tasks/todo.md`.
