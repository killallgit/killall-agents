# killall-agents

Public lane agents and workflow skills for Claude Code, Codex, and opencode. Keep credentials, machine-specific settings and runtime state out of this repository.

The agents' source is `factory/<name>.md` in Claude Code's format, with each tool's model in `factory/models.toml`. `skills/setup-agents/scripts/install.py` renders one file per tool (Claude Code, Codex, opencode) into a project. The orchestrator is the `orchestrate` skill, not an agent. Keep the `<!-- killall-agents -->` / `# killall-agents` ownership markers stable.

Run from the repository root:

```sh
python3 skills/setup-agents/scripts/test_install.py
python3 scripts/test_release.py
git diff --check
```

Builders and reviewers load `house-rules` from [killall-craft](https://github.com/killallgit/killall-craft); this repository ships no copy of it. Keep agents out of a root `agents/` folder, which Claude Code loads on plugin install; they belong in `factory/` so only `setup-agents` installs them.

Pending grunt and setup TUI work is tracked in `tasks/todo.md`.
