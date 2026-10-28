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

## Project agents

Run `/killall-agents:agent-setup` in Claude Code, or `$agent-setup` in Codex, inside a project. It copies these agents from [`factory/`](factory/) into the project's `.claude/agents/`, `.codex/agents/` and `.cursor/agents/`, keeps them out of Git through `.git/info/exclude`, and lists them in `.worktreeinclude` so Claude Code worktrees get them too. Nothing is installed globally. `remove` takes it all out again.

| Agent | Job | Claude model / effort | Codex model / effort |
| --- | --- | --- | --- |
| `planner` | Turns a spec into lanes, contracts and acceptance checks; read-only | Opus / high | `gpt-6-astra` / high |
| `grunt` | Relays a task that fits 64K tokens to the local [Pi](https://github.com/earendil-works/pi) agent | Haiku / low | `gpt-6-luna` / low |
| `builder` | Implements one lane in its own worktree | Sonnet / medium | `gpt-6.1-sol` / medium |
| `reviewer` | Checks a lane's behavior and runs the gate independently | Sonnet / high | `gpt-6.1-sol` / high |
| `hall-monitor` | Quick check of a lane's changes against `follow-the-rules`; read-only | Sonnet / low | `gpt-6.1-sol` / low |

Claude Code also gets three utility agents. They have no Codex or Cursor copy.

| Agent | Purpose |
| --- | --- |
| `git-janitor` | Wraps up finished work: fast-forwards or rebases local branches, checks the main checkout is clean and no work is stranded, then proposes removing merged worktrees and branches. Mention `@agent-git-janitor` to invoke it directly |
| `git-janitor-investigator` | Collects read-only branch/worktree evidence for the janitor |
| `comment-janitor` | Reviews changed comments for useful intent |

Installing the plugin adds no agents.

Cursor agents inherit the session model. Ask the top-level session to use the [`orchestrate`](skills/orchestrate/SKILL.md) skill to run a spec. The skill is the project-manager loop: plan with the planner, run lanes with grunt and builders, check with reviewer and hall-monitor. Agents read the gate, branch and worktree rules from the project's own `AGENTS.md`.

Grunt needs `pi` on `PATH` with a ready provider. Builders and hall-monitor need the included `follow-the-rules` skill.

## Development

`factory/claude/` is the source. After editing it, regenerate the Codex and Cursor copies:

```sh
python3 scripts/build_agents.py          # write factory/codex and factory/cursor
python3 scripts/build_agents.py --check  # CI: copies are current and valid
python3 skills/agent-setup/scripts/test_install.py
```

See [pending work](tasks/todo.md) and [factory research](docs/research/agent-factory-patterns.md) for design background.
