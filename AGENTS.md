# AGENTS.md

Agent contract for `killall-agents` (module `github.com/killallgit/killall-agents`, binary `killall-agents`). Full design: `docs/superpowers/specs/2026-07-07-strip-skills-design.md`.

## Stack

- Go 1.23+
- CLI framework: `github.com/spf13/cobra`
- Filesystem abstraction: `github.com/spf13/afero` — business logic depends on `afero.Fs`/small interfaces, never calls `os` directly
- Test assertions: `github.com/stretchr/testify/require`
- Lint: `golangci-lint`
- Task runner: `Taskfile.yml` (`task build`, `task test`, `task lint`, `task fmt`, `task ci`)
- CI: `.github/workflows/ci.yml` runs `task ci` on every push/PR to `main` — the exact same command a developer runs locally, so CI and local can't drift

## Design principles

- **SOLID**, applied Go-idiomatically: small interfaces at package boundaries, dependency inversion via `afero.Fs`, one responsibility per package.
- **Functional core / imperative shell**: planning/decision logic (`internal/planner`, `internal/manifest`) is pure — same inputs, same output, no I/O, testable against `afero.MemMapFs`. All disk mutation lives in a thin, isolated shell (`internal/backup`, `internal/strip`, `internal/restore`).
- **Many small, single-purpose modules over indirection.** Prefer several small packages/files that each do one obvious thing over fewer packages hiding behind generic/clever abstractions. If a package needs a paragraph to explain what it's for, split it. Don't add an interface, wrapper, or abstraction layer for a single caller.
- **Allowlist, not denylist.** The tool only ever touches paths explicitly named in a per-tool category manifest. Never recurse/wildcard-delete a parent directory.
- Every write path (`backup`, `strip`, `restore`) must be copy-before-delete and preserve the original relative directory tree, so a revert is a straight copy-back with no reconstruction logic.

## Working in this repo

- Every changed line should trace to the task at hand — no drive-by refactors, no speculative flexibility.
- Match existing style; don't reformat or "improve" unrelated code.
- New tool support (beyond Claude Code / Codex) should only ever require adding a manifest — never touching `planner`/`backup`/`strip`/`restore`.
