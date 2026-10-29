# killall-agents

Agent catalog + per-project agents for Claude Code, Codex, Cursor. Ordinary workflow skills live in [killall-skills](https://github.com/killallgit/killall-skills).

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

Includes `setup-agents`, `orchestrate`, `wrap-up`, `follow-the-rules`.

## Install agents

Run installer in terminal, answer questions:

```sh
python3 skills/setup-agents/scripts/install.py
```

Asks where agents go (user-wide or current project), which tools (Claude Code, Codex, Cursor), which agents from multi-select, then model for each catalog tier. Confirms before writing anything. Type `q` to quit. Rerun starts from what is already installed; prompts make folders match selection: remove copies it wrote that you deselected, keep every other file.

In session, `/killall-agents:setup-agents` in Claude Code or `$setup-agents` in Codex runs same script with flags: `--scope user|project`, `--hosts claude,codex`, `--agents lanes,catalog,<names>`, `--model codex:opus=<id>`, `--remove`, and `--force` to replace same-named agent it did not write. Flags add to what is installed; `--prune` also removes copies you did not select. No `--scope`: flags install into current project, prompts suggest user-wide.

Project install copies agents into project's `.claude/agents/`, `.codex/agents/` and `.cursor/agents/`, keeps them out of Git through `.git/info/exclude`, lists them in `.worktreeinclude` so Claude Code worktrees get them too. User-wide install writes to `~/.claude/agents`, `~/.codex/agents` and `~/.cursor/agents` (or `CLAUDE_CONFIG_DIR` and `CODEX_HOME`). Lane agents below install per project only.

## Lane agents

| Agent | Job | Claude model / effort | Codex model / effort |
| --- | --- | --- | --- |
| `planner` | Turns spec into lanes, contracts, acceptance checks; read-only | Opus / high | `gpt-6-astra` / high |
| `grunt` | Relays task fitting 64K tokens to local [Pi](https://github.com/earendil-works/pi) agent | Haiku / low | `gpt-6-luna` / low |
| `builder` | Implements one lane in own worktree | Sonnet / medium | `gpt-6.1-sol` / medium |
| `reviewer` | Checks lane behavior, runs gate independently | Sonnet / high | `gpt-6.1-sol` / high |
| `hall-monitor` | Quick check of lane changes against `follow-the-rules`; read-only | Sonnet / low | `gpt-6.1-sol` / low |

Claude Code also gets three utility agents. No Codex or Cursor copy.

| Agent | Purpose |
| --- | --- |
| `git-janitor` | Haiku background runner for [`wrap-up`](skills/wrap-up/SKILL.md) skill: runs its script, returns table, or the one roadblock needing you |
| `git-janitor-investigator` | Collects read-only branch/worktree evidence for janitor |
| `comment-janitor` | Reviews changed comments for useful intent |

Installing plugin adds no agents. Run `wrap-up` skill after PR lands: confirms work merged and nothing stranded, updates main checkout, grooms beads, prunes merged worktrees and branches, asks only about what is left.

## Engineering catalog

Twenty-four specialist agents in [`factory/catalog/`](factory/catalog/), one source file each. Installer fills in each tool's format: Claude Code gets `model`, `effort`, `tools`, `maxTurns`; Codex gets `model`, `model_reasoning_effort` and, for agents that only read, `sandbox_mode = "read-only"`; Cursor gets `readonly`.
| Agents | Access | Claude model / effort | Codex model / effort |
| --- | --- | --- | --- |
| `autonomous-optimization-architect`, `backend-architect`, `incident-response-commander`, `multi-agent-systems-architect`, `software-architect` | Reads only | Opus / high | `gpt-6-astra` / high |
| `privacy-engineer` | Edits files | Opus / high | `gpt-6-astra` / high |
| `code-reviewer`, `network-engineer`, `sre` | Reads only | Sonnet / high | `gpt-6.1-sol` / high |
| `knowledge-graph-engineer`, `rust-refactoring-specialist`, `search-relevance-engineer` | Edits files | Sonnet / high | `gpt-6.1-sol` / high |
| `desktop-app-engineer`, `developer-tooling-engineer`, `devops-automator`, `frontend-developer`, `it-service-manager`, `minimal-change-engineer`, `mobile-app-builder`, `platform-engineer`, `senior-developer`, `technical-writer` | Edits files | Sonnet / medium | `gpt-6.1-sol` / medium |
| `codebase-onboarding-engineer` | Reads only | Sonnet / low | `gpt-6.1-sol` / low |
| `git-workflow-master` | Edits files | Sonnet / low | `gpt-6.1-sol` / low |

"Reads only" agents get no `Edit` or `Write` in Claude Code, read-only sandbox in Codex; `incident-response-commander` and `network-engineer` also get no `Bash`. Other reads-only agents keep `Bash` in Claude Code, so only Codex and Cursor enforce read-only for them. Catalog adapted from [agency-agents](https://github.com/msitarzewski/agency-agents) (MIT, copy in [`factory/catalog/LICENSE`](factory/catalog/LICENSE)) with persona, memory, metrics sections and most sample code removed, cutting set from about 315 KB to under 200 KB. Edit source file, next install picks it up.

Cursor agents inherit session model. Ask top-level session to use [`orchestrate`](skills/orchestrate/SKILL.md) skill to run a spec. Skill is project-manager loop: plan with planner, run lanes with grunt and builders, check with reviewer and hall-monitor. Agents read gate, branch, worktree rules from project's own `AGENTS.md`.

Grunt needs `pi` on `PATH` with ready provider. Builders and hall-monitor need included `follow-the-rules` skill.

## Development

`factory/claude/` is source. After editing, regenerate Codex and Cursor copies:

```sh
python3 scripts/build_agents.py          # write factory/codex and factory/cursor
python3 scripts/build_agents.py --check  # CI: copies are current and valid
python3 skills/setup-agents/scripts/test_install.py
python3 skills/setup-agents/scripts/test_catalog.py
```

See [pending work](tasks/todo.md) and [factory research](docs/research/agent-factory-patterns.md) for design background.