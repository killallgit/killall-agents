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

Includes `agent-setup`, `orchestrate`, `wrap-up` and `follow-the-rules`.

## Install agents

Run the installer in a terminal and answer its questions:

```sh
python3 skills/agent-setup/scripts/install.py
```

It asks where the agents go (user-wide, or the current project), which tools (Claude Code, Codex, Cursor), and which agents from a multi-select, then the model for each catalog tier, and confirms before it writes anything. Type `q` to quit. A rerun starts from what is already installed, and an install makes the folders match your selection: it removes copies it wrote that you deselected and keeps every other file.

In a session, `/killall-agents:agent-setup` in Claude Code or `$agent-setup` in Codex runs the same script with flags: `--scope user|project`, `--hosts claude,codex`, `--agents lanes,catalog,<names>`, `--model codex:opus=<id>`, `--remove`, and `--force` to replace a same-named agent it did not write.

A project install copies the agents into the project's `.claude/agents/`, `.codex/agents/` and `.cursor/agents/`, keeps them out of Git through `.git/info/exclude`, and lists them in `.worktreeinclude` so Claude Code worktrees get them too. A user-wide install writes to `~/.claude/agents`, `~/.codex/agents` and `~/.cursor/agents` (or `CLAUDE_CONFIG_DIR` and `CODEX_HOME`). The lane agents below install per project only.

## Lane agents

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
| `git-janitor` | Haiku background runner for the [`wrap-up`](skills/wrap-up/SKILL.md) skill: runs its script and returns the table, or the one roadblock that needs you |
| `git-janitor-investigator` | Collects read-only branch/worktree evidence for the janitor |
| `comment-janitor` | Reviews changed comments for useful intent |

Installing the plugin adds no agents. Run the `wrap-up` skill after a PR lands: it confirms the work merged and nothing is stranded, updates the main checkout, grooms beads, prunes merged worktrees and branches, and asks only about what is left.

## Engineering catalog

Twenty-four specialist agents in [`factory/catalog/`](factory/catalog/), one source file each. The installer fills in each tool's format, so Claude Code gets `model`, `effort`, `tools` and `maxTurns`, Codex gets `model`, `model_reasoning_effort` and, for agents that only read, `sandbox_mode = "read-only"`, and Cursor gets `readonly`. Installed names carry an `engineering-` prefix.

| Agents | Access | Claude model / effort | Codex model / effort |
| --- | --- | --- | --- |
| `autonomous-optimization-architect`, `backend-architect`, `incident-response-commander`, `multi-agent-systems-architect`, `software-architect` | Reads only | Opus / high | `gpt-6-astra` / high |
| `privacy-engineer` | Edits files | Opus / high | `gpt-6-astra` / high |
| `code-reviewer`, `network-engineer`, `sre` | Reads only | Sonnet / high | `gpt-6.1-sol` / high |
| `knowledge-graph-engineer`, `rust-refactoring-specialist`, `search-relevance-engineer` | Edits files | Sonnet / high | `gpt-6.1-sol` / high |
| `desktop-app-engineer`, `developer-tooling-engineer`, `devops-automator`, `frontend-developer`, `it-service-manager`, `minimal-change-engineer`, `mobile-app-builder`, `platform-engineer`, `senior-developer`, `technical-writer` | Edits files | Sonnet / medium | `gpt-6.1-sol` / medium |
| `codebase-onboarding-engineer` | Reads only | Sonnet / low | `gpt-6.1-sol` / low |
| `git-workflow-master` | Edits files | Sonnet / low | `gpt-6.1-sol` / low |

"Reads only" agents get no `Edit` or `Write` in Claude Code and a read-only sandbox in Codex; `incident-response-commander` and `network-engineer` also get no `Bash`. The catalog is adapted from [agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, copy in [`factory/catalog/LICENSE`](factory/catalog/LICENSE)) with the persona, memory and metrics sections and most sample code removed, which cut the set from about 315 KB to under 200 KB. Edit a source file, and the next install picks it up.

Cursor agents inherit the session model. Ask the top-level session to use the [`orchestrate`](skills/orchestrate/SKILL.md) skill to run a spec. The skill is the project-manager loop: plan with the planner, run lanes with grunt and builders, check with reviewer and hall-monitor. Agents read the gate, branch and worktree rules from the project's own `AGENTS.md`.

Grunt needs `pi` on `PATH` with a ready provider. Builders and hall-monitor need the included `follow-the-rules` skill.

## Development

`factory/claude/` is the source. After editing it, regenerate the Codex and Cursor copies:

```sh
python3 scripts/build_agents.py          # write factory/codex and factory/cursor
python3 scripts/build_agents.py --check  # CI: copies are current and valid
python3 skills/agent-setup/scripts/test_install.py
python3 skills/agent-setup/scripts/test_catalog.py
```

See [pending work](tasks/todo.md) and [factory research](docs/research/agent-factory-patterns.md) for design background.
