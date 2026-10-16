# killall-agents

Public agent catalog and project setup for Claude Code, Codex, and Cursor (beta). Keep credentials, machine-specific settings and runtime state out of this repository.

Role templates and host settings live in `skills/agent-setup/templates/`; `scripts/render_agents.py` in that skill adapts them to host files. Preserve existing generated paths, ownership markers, foreign-setting checks and the shared state location when changing setup.

Run from the repository root:

```sh
python3 skills/agent-setup/evals/run.py
python3 skills/agent-setup/evals/state.py
git diff --check
```

Upgrade fixtures include historical renderer/template snapshots so tests work in shallow checkouts without source-repository history or network access.

`skills/follow-the-rules/` is an intentional complete copy from killall-skills. See `docs/provenance.md`; preserve its relative reference links. The git-janitor agent still requires the separately installed `killall-skills:git-janitor` skill.

The abandoned Go CLI was retired; its implementation remains in Git history. V2 grunt and setup TUI work is tracked in `tasks/todo.md` and is not implemented in v1.
