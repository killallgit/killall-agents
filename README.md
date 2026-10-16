# killall-agents

Agent catalog and per-project agents for Claude Code, Codex, and Cursor. Ordinary workflow skills live in [killall-skills](https://github.com/killallgit/killall-skills).

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

Cursor: install from `https://github.com/killallgit/killall-agents` in **Customize**.

Skills CLI (setup and rules only):

```sh
npx skills add killallgit/killall-agents
```

Includes `agent-setup`, `orchestrate` and `follow-the-rules`.

## Agent catalog

| Agent | Purpose |
| --- | --- |
| `git-janitor` | Runs the separately installed `killall-skills:git-janitor` skill in its own context |
| `git-janitor-investigator` | Collects read-only branch/worktree evidence for the janitor |
| `comment-janitor` | Reviews changed comments for useful intent |

Claude Code loads these from the plugin. Mention `@agent-killall-agents:git-janitor` in a conversation to invoke the janitor directly. Keep `killall-skills` installed to use that agent's cleanup skill.

## Project agents

Run `/killall-agents:agent-setup` in Claude Code, or `$agent-setup` in Codex, inside a project. It copies these agents from [`factory/`](factory/) into the project's `.claude/agents/`, `.codex/agents/` and `.cursor/agents/`, adds the orchestrator entry to the project's `CLAUDE.local.md`, `.codex/config.toml` and `.cursor/rules/killall-orchestrator.mdc`, keeps all of it out of Git through `.git/info/exclude`, and lists it in `.worktreeinclude` so Claude Code worktrees get it too. Nothing is installed globally. `remove` takes it all out again.

| Agent | Job | Claude model / effort | Codex model / effort |
| --- | --- | --- | --- |
| `planner` | Turns a spec into lanes, contracts and acceptance checks; read-only | Opus / high | `gpt-6-astra` / high |
| `grunt` | Relays a task that fits 64K tokens to the local [Pi](https://github.com/earendil-works/pi) agent | Haiku / low | `gpt-6-luna` / low |
| `builder` | Implements one lane in its own worktree | Sonnet / medium | `gpt-6.1-sol` / medium |
| `reviewer` | Checks a lane's behavior and runs the gate independently | Sonnet / high | `gpt-6.1-sol` / high |
| `hall-monitor` | Checks a lane against `follow-the-rules` and the codebase's patterns; read-only | Haiku / medium | `gpt-6-luna` / medium |

Cursor agents inherit the session model. The orchestrator entry tells the project's top-level session to load the [`orchestrate`](skills/orchestrate/SKILL.md) skill. The skill is the project-manager loop: plan with the planner, run lanes with grunt and builders, check with reviewer and hall-monitor. Agents read the gate, branch and worktree rules from the project's own `AGENTS.md`.

Grunt needs `pi` on `PATH` with a ready provider. Builders and hall-monitor need the included `follow-the-rules` skill. Lane records live at `${XDG_CONFIG_HOME:-~/.config}/killall-skills/agents/state/<encoded-main-checkout>/`, shared by a checkout's worktrees and hosts.

## Development

`factory/claude/` is the source. After editing it, regenerate the Codex and Cursor copies:

```sh
python3 scripts/build_agents.py          # write factory/codex and factory/cursor
python3 scripts/build_agents.py --check  # CI: copies are current and valid
python3 skills/agent-setup/scripts/test_install.py
```

See [pending work](tasks/todo.md) and [factory research](docs/research/agent-factory-patterns.md) for design background.
