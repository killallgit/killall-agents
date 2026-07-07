# Cold Turkey: backup and strip Claude Code / Codex customization

- Status: Approved
- Date: 2026-07-07
- Module: `github.com/killallgit/strip-skills`
- Binary: `turkey`

Project name is "Cold Turkey" (quitting your plugin/skill habit cold turkey); repo and module keep the `strip-skills` name, the CLI binary is `turkey`. Note: there's an unrelated existing app called "Cold Turkey" (a website blocker) — different product category, not a real collision risk for a personal CLI tool, but worth knowing if this is ever published under that name.

## Problem

Coding LLM tools (Claude Code, Codex CLI) accumulate user customization over time: skills, subagents, slash commands, hooks, rules, installed plugins, MCP server registrations, and global instruction files (`CLAUDE.md`/`AGENTS.md`). There is no built-in way to:

1. Get a full inventory of what customization is currently installed.
2. Back it up in a form that can be trivially reverted.
3. Strip a tool back down to a vanilla, out-of-the-box state — e.g. to test whether a bug is caused by a plugin/skill, or to get a clean baseline for a new project.

Both tools also store a lot of *non*-customization state in the same top-level directory (credentials, session transcripts, telemetry, caches, sqlite databases, daemon sockets). Any tool that touches these directories must not touch that state.

## Goals

- Inventory, back up, and strip customization for both Claude Code and Codex CLI.
- Support both global (`~/.claude`, `~/.codex`) and per-project (`<project>/.claude`, `<project>/.codex`) scope.
- Backups preserve the original directory tree exactly, so revert is a straight copy-back with no reconstruction logic.
- Never touch anything outside an explicit, hardcoded allowlist of paths per tool (credentials, sessions, telemetry, caches, daemon/runtime state are structurally unreachable — not excluded by a denylist, just never named).
- Strip always requires a shown plan and explicit confirmation (or `--dry-run` to preview only, or `--yes` to skip the prompt).

## Non-goals (v1)

- Session/transcript history — explicitly out of scope, never read or written.
- Surgical editing of `settings.json`/`config.toml` (splitting "core prefs" from "customization" keys). V1 backs the whole file up and deletes it; neither tool requires the file to exist to start.
- Codex `automations/` (scheduled routines) — not modeled as a category in v1.
- Other coding tools (Cursor, Windsurf, etc.) — Claude Code and Codex only for now. Architecture should make adding a third tool a matter of adding a manifest, not touching planner/executor code.

## Category manifests

Each tool declares its own fixed list of categories and the concrete paths they map to. Categories that don't exist for a given tool are simply absent from its manifest (no universal category list forced onto every tool).

### Claude Code (`<root>` = `~/.claude` or `<project>/.claude`)

| Category | Paths | Action on strip |
|---|---|---|
| `skills` | `<root>/skills/` | delete dir |
| `agents` | `<root>/agents/` | delete dir |
| `commands` | `<root>/commands/` | delete dir |
| `hooks` | `<root>/hooks/` | delete dir |
| `rules` | `<root>/rules/` | delete dir |
| `plugins` | `<root>/plugins/` (cache, data, marketplaces/, installed_plugins.json, known_marketplaces.json) | delete dir/files |
| `mcp` | `<root-parent>/.mcp.json` (project) or `<root>/.mcp.json` (global) | delete file |
| `settings` | `<root>/settings.json`, `<root>/settings.local.json` | delete file(s) |
| `memory` | `<root-parent>/CLAUDE.md` (project) or `<root>/CLAUDE.md` (global) | delete file |

Never referenced by any category (and therefore never touched): `.credentials.json`, `projects/`, `sessions/`, `history.jsonl`, `file-history/`, `session-env/`, `shell-snapshots/`, `paste-cache/`, `telemetry/`, `usage-data/`, `daemon*`, `ide/`, `jobs/`, `debug/`, `cache/`, `config/`, `backups/`, `policy-limits.json`, `remote-settings.json`, `.last-*`, `.DS_Store`, and `turkey-backups/` itself.

### Codex CLI (`<root>` = `~/.codex` or `<project>/.codex`)

| Category | Paths | Action on strip |
|---|---|---|
| `skills` | `<root>/skills/` **excluding** `<root>/skills/.system` | delete everything except excluded path |
| `rules` | `<root>/rules/` | delete dir |
| `hooks` | `<root>/hooks.json` | delete file |
| `plugins` | `<root>/plugins/` (cache, staging dirs) | delete dir |
| `settings` | `<root>/config.toml` | delete file |
| `memory` | `<root>/AGENTS.md` (global) or `<project>/AGENTS.md` (project) | delete file |

No `agents` or `commands` category — Codex has no subagent or slash-command concept on disk today.

Never referenced: `auth.json`, `sessions/`, `archived_sessions/`, `history.jsonl`, `session_index.jsonl`, `memories/`, `memories_1.sqlite*`, `goals_1.sqlite*`, `logs_2.sqlite*`, `state_5.sqlite*`, `sqlite/`, `telemetry`-equivalents, `cache/` (app directory / apps-server caches, distinct from `plugins/cache`), `automations/`, `browser/`, `computer-use/`, `node_repl/`, `process_manager/`, `shell_snapshots/`, `ambient-suggestions/`, `.tmp/`, `installation_id`, `models_cache.json`, `version.json`.

Vendor-exclude paths (like Codex's `skills/.system`) are a per-category `exclude` list in the manifest. This is the mechanism for "don't strip stuff that ships with the tool" — starts short, grows as more vendor-owned paths are identified.

## Commands

```
turkey inventory --tool claude|codex|all [--project <path>]
turkey backup    --tool claude|codex|all [--categories skills,agents,...] [--project <path>]
turkey strip     --tool claude|codex|all [--categories ...] [--project <path>] [--dry-run] [--yes]
turkey restore   --tool claude|codex --from <backup-id|path> [--categories ...]
turkey list-backups --tool claude|codex|all
```

- `inventory` scans and prints what exists per category, no writes.
- `backup` copies the selected categories into a timestamped backup snapshot. Standalone command — usable without stripping, e.g. for periodic snapshots.
- `strip` always: scan → build plan → print plan (every path, and whether it will be deleted or is excluded) → require confirmation unless `--yes` → `backup` (copy) → delete originals. `--dry-run` stops after printing the plan.
- `restore` replays a backup's manifest in reverse: copies files from the backup snapshot back to their original absolute paths.
- Default scope with no `--project` flag is global (`~/.claude`, `~/.codex`). `--project <path>` scopes to that project's `.claude`/`.codex` dirs and root-level `CLAUDE.md`/`AGENTS.md`/`.mcp.json` instead.

## Backup format

`~/.claude/turkey-backups/<tool>-<timestamp>/` (chosen location: colocated with the tool's own config dir, per explicit user decision — the backup dir itself is never a member of any category manifest, so it cannot be swept up by a later strip run).

Layout mirrors the original relative tree exactly:

```
~/.claude/turkey-backups/claude-20260707-143000/
  manifest.json
  skills/codebase-memory/...
  agents/...
  settings.json
  CLAUDE.md
  ...
```

`manifest.json`:

```json
{
  "tool": "claude",
  "scope": "global",
  "root": "/Users/ryan/.claude",
  "categories": ["skills", "agents", "settings", "memory"],
  "createdAt": "2026-07-07T14:30:00Z",
  "entries": [
    {"category": "skills", "sourcePath": "/Users/ryan/.claude/skills/codebase-memory", "backupPath": "skills/codebase-memory", "action": "deleted"},
    {"category": "settings", "sourcePath": "/Users/ryan/.claude/settings.json", "backupPath": "settings.json", "action": "deleted"}
  ]
}
```

`restore` reads `entries` and copies `backupPath` back to `sourcePath` — no path-guessing.

## Architecture

Functional core / imperative shell, since Go is neither pure-OOP nor pure-FP and the literal combination of "SOLID" and "functional paradigms" needs a concrete idiom to mean something in Go:

```
cmd/turkey/             cobra command wiring only, no business logic
internal/manifest/      pure data: per-tool category definitions (immutable structs)
internal/planner/        pure function: Build(manifest, fs) -> Plan. No side effects.
internal/fsutil/         small interfaces (Copier, Deleter, Lister) over afero.Fs
internal/backup/         imperative shell: executes a Plan's copy step, writes manifest.json
internal/strip/          imperative shell: executes a Plan's delete step
internal/restore/        imperative shell: reads a backup manifest.json, copies back
internal/inventory/      pure formatting of a Plan/scan result for CLI output
```

- **SRP**: planning, executing, and reporting are separate packages.
- **OCP**: adding a third tool (or a new category) means adding manifest data; `planner`/`backup`/`strip`/`restore` do not change.
- **ISP/DIP**: business logic depends on small interfaces (`Copier`, `Deleter`) backed by `afero.Fs`, not concrete `os` calls — real filesystem in production, `afero.MemMapFs` in tests. `planner.Build` is a pure function over an `afero.Fs` snapshot, fully unit-testable without touching real disk.

### Libraries

- `github.com/spf13/cobra` — CLI framework.
- `github.com/spf13/afero` — filesystem abstraction (dependency inversion boundary; enables in-memory testing).
- `encoding/json` (stdlib) — `manifest.json` read/write, parsing existing JSON config files for inventory display.
- `github.com/stretchr/testify/require` — test assertions.
- `golangci-lint` — linting.
- Go 1.23+.

### CI / Taskfile

- `Taskfile.yml`: `task build`, `task test` (`go test ./... -race -cover`), `task lint` (golangci-lint), `task fmt`, `task ci` (fmt-check + lint + test + build).
- `.github/workflows/ci.yml`: checkout → setup-go → install `task` → run `task ci`. Triggers on push/PR to `main`. CI and local dev call the exact same `task ci` target so they can't drift.

## Safety model

- Allowlist only: a path is touched only if it's named in a tool's category manifest. No recursive/wildcard deletion of a parent directory.
- Copy-before-delete, never move, during `strip`'s backup step.
- `strip` always shows a full plan before doing anything; requires confirmation unless `--yes`; `--dry-run` never writes.
- Vendor-exclude lists protect known tool-shipped paths (e.g. Codex `skills/.system`) from being deleted even though they live inside a stripped category's directory.

## Known open risk

"Vanilla" for `settings.json`/`config.toml` is assumed to mean *file does not exist* (neither tool requires the file to start fresh). To be verified against actual fresh-install behavior during implementation; if a tool refuses to start without the file, fall back to writing the smallest valid stub instead of leaving it absent.
