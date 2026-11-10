# killall-agents

Four lane agents and workflow skills for Claude Code, Codex and opencode. Ordinary workflow skills live in [killall-skills](https://github.com/killallgit/killall-skills).

## Install

Claude Code:

```text
/plugin marketplace add killallgit/killall-agents
/plugin install killall-agents@killall-agents
```

Codex:

```sh
codex plugin marketplace add killallgit/killall-agents
codex plugin add killall-agents@killall-agents
```

Skills CLI (setup and rules only):

```sh
npx skills add killallgit/killall-agents
```

Includes `setup-agents`, `orchestrate`.

## Install agents

From a project's git root:

```sh
python3 skills/setup-agents/scripts/install.py [--tools claude,codex,opencode] [--remove] [--force]
```

Writes one file per tool into `.claude/agents/`, `.codex/agents/` and `.opencode/agents/`, each with that tool's model from [`factory/models.toml`](factory/models.toml), so no agent inherits the session's model. Keeps the copies out of Git through `.git/info/exclude` and lists them in `.worktreeinclude` so Claude Code worktrees get them. Rerun to refresh; it removes copies from older versions and keeps every file it did not write. `--force` replaces a same-named agent it did not write. In session: `/killall-agents:setup-agents` in Claude Code or `$setup-agents` in Codex.

## Lane agents

Edit [`factory/models.toml`](factory/models.toml) to change a model, then rerun the installer.

| Agent | Job | Claude | Codex | opencode |
| --- | --- | --- | --- | --- |
| `planner` | Turns spec into lanes, contracts, acceptance checks; read-only | Opus / high | `gpt-6-astra` / high | Opus |
| `grunt` | Relays task fitting 64K tokens to local [Pi](https://github.com/earendil-works/pi) agent | Haiku / low | `gpt-6-luna` / low | Haiku |
| `builder` | Implements one lane in own worktree | Sonnet / medium | `gpt-6.1-sol` / medium | Sonnet |
| `reviewer` | Checks lane behavior, `house-rules` and comments; runs gate independently | Sonnet / high | `gpt-6.1-sol` / high | Sonnet |

Installing plugin adds no agents. To land finished work, use `/lets-finish` from [killall-skills](https://github.com/killallgit/killall-skills).

opencode agents run as subagents with the model pinned; the `tools` restriction is Claude Code only.

Ask top-level session to use [`orchestrate`](skills/orchestrate/SKILL.md) skill to run a spec. Skill is project-manager loop: plan with planner, run lanes with grunt and builders, check with reviewer. Agents read gate, branch, worktree rules from project's own `AGENTS.md`.

Grunt needs `pi` on `PATH` with ready provider. Builders and reviewers need the `house-rules` skill from [killall-craft](https://github.com/killallgit/killall-craft) installed.

## Development

`factory/<name>.md` is source, in Claude Code's format. `factory/models.toml` maps each agent to a model per tool. The installer renders both into each tool's file at install time.

```sh
python3 skills/setup-agents/scripts/test_install.py
python3 scripts/test_release.py
```

Release with `task tag:patch`, `task tag:minor` or `task tag:major`: it tests `origin/main`, bumps the version in all three plugin manifests, tags it, and pushes.

See [pending work](tasks/todo.md).