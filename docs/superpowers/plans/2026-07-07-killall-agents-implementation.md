# killall-agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `killall-agents`, a Go CLI that inventories, backs up, strips, and restores Claude Code / Codex CLI customization (skills, agents, commands, hooks, rules, plugins, settings, memory files) down to a vanilla state, fully revertible.

**Architecture:** Functional core / imperative shell. `internal/manifest` (pure data) and `internal/planner` (pure `Build` function) decide *what* to touch; `internal/backup`, `internal/strip`, `internal/restore` are the thin imperative shell that actually touches disk, always through the `afero.Fs` interface so tests run against an in-memory filesystem. `cmd/killall-agents` wires cobra commands to these packages with no business logic of its own.

**Tech Stack:** Go 1.23+, `github.com/spf13/cobra`, `github.com/spf13/afero`, `github.com/stretchr/testify/require`, `golangci-lint`, `Taskfile.yml`, GitHub Actions.

Full design reference: `docs/superpowers/specs/2026-07-07-strip-skills-design.md`.

## Global Constraints

- Module path: `github.com/killallgit/killall-agents`. Binary name: `killall-agents`.
- Go 1.23+. CLI framework `cobra`. Filesystem abstraction `afero` — business logic never calls `os.*` directly, only through `afero.Fs`.
- Allowlist only: a path is touched only if it appears in a tool's `internal/manifest` category definition. No recursive/wildcard deletion of a parent directory.
- Copy-before-delete, never move, on every write path.
- Backups mirror the original relative directory tree exactly and live at `<configRoot>/killall-agents-backups/<tool>-<timestamp>/`.
- `strip` always shows the full plan and requires confirmation unless `--yes`; `--dry-run` never writes to disk.
- Session/transcript/telemetry/credential paths (e.g. `.credentials.json`, `auth.json`, `projects/`, `sessions/`, `history.jsonl`) are never named anywhere in this codebase.
- Prefer many small, single-purpose files/packages over generic abstractions (see `AGENTS.md`). If a package needs a paragraph to explain what it's for, split it.

---

### Task 1: Project scaffolding

**Files:**
- Create: `go.mod`, `go.sum`
- Create: `cmd/killall-agents/main.go` (placeholder)
- Create: `Taskfile.yml`
- Create: `.golangci.yml`
- Create: `.gitignore`

**Interfaces:**
- Consumes: nothing (first task).
- Produces: a buildable Go module with `cobra`, `afero`, `testify` available as dependencies; `task build`/`task test`/`task lint`/`task fmt`/`task ci` runnable.

- [ ] **Step 1: Create the module and directory skeleton**

Run:
```bash
mkdir -p cmd/killall-agents internal/manifest internal/planner internal/fsutil internal/backup internal/strip internal/restore internal/inventory internal/paths
go mod init github.com/killallgit/killall-agents
```
Expected: `go.mod` created containing `module github.com/killallgit/killall-agents`.

- [ ] **Step 2: Add dependencies**

Run:
```bash
go get github.com/spf13/cobra@latest github.com/spf13/afero@latest github.com/stretchr/testify@latest
```
Expected: `go.mod` gains three `require` lines; `go.sum` is created.

- [ ] **Step 3: Add a placeholder `main.go` so the module builds**

`cmd/killall-agents/main.go`:
```go
package main

func main() {}
```

- [ ] **Step 4: Run `go mod tidy` and verify the build**

Run:
```bash
go mod tidy
go build ./...
```
Expected: both exit 0, no output.

- [ ] **Step 5: Add `Taskfile.yml`**

`Taskfile.yml`:
```yaml
version: '3'

tasks:
  build:
    desc: Build the killall-agents binary
    cmds:
      - go build -o bin/killall-agents ./cmd/killall-agents

  test:
    desc: Run tests with race detector and coverage
    cmds:
      - go test ./... -race -cover

  lint:
    desc: Run golangci-lint
    cmds:
      - golangci-lint run

  fmt:
    desc: Check gofmt formatting
    cmds:
      - test -z "$(gofmt -l .)"

  ci:
    desc: Everything CI runs
    cmds:
      - task: fmt
      - task: lint
      - task: test
      - task: build
```

- [ ] **Step 6: Add `.golangci.yml`**

`.golangci.yml`:
```yaml
run:
  timeout: 3m

linters:
  enable:
    - govet
    - staticcheck
    - unused
    - errcheck
```

- [ ] **Step 7: Add `.gitignore`**

`.gitignore`:
```
/bin/
```

- [ ] **Step 8: Verify `task ci` runs clean on the placeholder**

Run:
```bash
task ci
```
Expected: exit 0 (fmt check passes trivially, lint passes on an empty `main`, `go test ./...` reports "no test files" for every package, build produces `bin/killall-agents`).

- [ ] **Step 9: Commit**

```bash
git add go.mod go.sum cmd/killall-agents/main.go Taskfile.yml .golangci.yml .gitignore
git commit -m "chore: scaffold Go module, Taskfile, lint config"
```

---

### Task 2: `internal/manifest` — per-tool category data

**Files:**
- Create: `internal/manifest/manifest.go`
- Create: `internal/manifest/claude.go`
- Create: `internal/manifest/codex.go`
- Create: `internal/manifest/registry.go`
- Test: `internal/manifest/manifest_test.go`

**Interfaces:**
- Consumes: nothing.
- Produces: `manifest.Tool` (`ToolClaude`, `ToolCodex`), `manifest.Scope` (`ScopeGlobal`, `ScopeProject`), `manifest.BaseKind` (`BaseConfig`, `BaseInstruction`), `manifest.PathSpec{Base BaseKind; Rel string}`, `manifest.Category{Name string; Paths []PathSpec; Excludes []string}`, `manifest.ToolManifest{Tool Tool; Categories []Category}`, `manifest.Claude() ToolManifest`, `manifest.Codex() ToolManifest`, `manifest.Lookup(tool Tool) (ToolManifest, error)`.

- [ ] **Step 1: Write the failing tests**

`internal/manifest/manifest_test.go`:
```go
package manifest_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/stretchr/testify/require"
)

func TestClaudeHasCoreCategories(t *testing.T) {
	m := manifest.Claude()
	require.Equal(t, manifest.ToolClaude, m.Tool)
	require.ElementsMatch(t,
		[]string{"skills", "agents", "commands", "hooks", "rules", "plugins", "mcp", "settings", "memory"},
		categoryNames(m),
	)
}

func TestCodexHasNoAgentsOrCommands(t *testing.T) {
	names := categoryNames(manifest.Codex())
	require.NotContains(t, names, "agents")
	require.NotContains(t, names, "commands")
}

func TestCodexSkillsExcludesSystemDir(t *testing.T) {
	cat := findCategory(manifest.Codex(), "skills")
	require.Contains(t, cat.Excludes, "skills/.system")
}

func TestLookupUnknownTool(t *testing.T) {
	_, err := manifest.Lookup(manifest.Tool("bogus"))
	require.Error(t, err)
}

func TestLookupKnownTools(t *testing.T) {
	m, err := manifest.Lookup(manifest.ToolClaude)
	require.NoError(t, err)
	require.Equal(t, manifest.ToolClaude, m.Tool)

	m, err = manifest.Lookup(manifest.ToolCodex)
	require.NoError(t, err)
	require.Equal(t, manifest.ToolCodex, m.Tool)
}

func categoryNames(m manifest.ToolManifest) []string {
	out := make([]string, len(m.Categories))
	for i, c := range m.Categories {
		out[i] = c.Name
	}
	return out
}

func findCategory(m manifest.ToolManifest, name string) manifest.Category {
	for _, c := range m.Categories {
		if c.Name == name {
			return c
		}
	}
	return manifest.Category{}
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/manifest/... -v`
Expected: FAIL — package `manifest` has no exported symbols yet (compile error).

- [ ] **Step 3: Write `internal/manifest/manifest.go`**

```go
package manifest

type Tool string

const (
	ToolClaude Tool = "claude"
	ToolCodex  Tool = "codex"
)

type Scope string

const (
	ScopeGlobal  Scope = "global"
	ScopeProject Scope = "project"
)

type BaseKind int

const (
	// BaseConfig resolves relative to the tool's config dir (~/.claude, ~/.codex).
	BaseConfig BaseKind = iota
	// BaseInstruction resolves relative to where instruction files live:
	// the config dir itself for global scope, its parent for project scope.
	BaseInstruction
)

type PathSpec struct {
	Base BaseKind
	Rel  string
}

type Category struct {
	Name     string
	Paths    []PathSpec
	Excludes []string
}

type ToolManifest struct {
	Tool       Tool
	Categories []Category
}
```

- [ ] **Step 4: Write `internal/manifest/claude.go`**

```go
package manifest

func Claude() ToolManifest {
	return ToolManifest{
		Tool: ToolClaude,
		Categories: []Category{
			{Name: "skills", Paths: []PathSpec{{Base: BaseConfig, Rel: "skills"}}},
			{Name: "agents", Paths: []PathSpec{{Base: BaseConfig, Rel: "agents"}}},
			{Name: "commands", Paths: []PathSpec{{Base: BaseConfig, Rel: "commands"}}},
			{Name: "hooks", Paths: []PathSpec{{Base: BaseConfig, Rel: "hooks"}}},
			{Name: "rules", Paths: []PathSpec{{Base: BaseConfig, Rel: "rules"}}},
			{Name: "plugins", Paths: []PathSpec{{Base: BaseConfig, Rel: "plugins"}}},
			{Name: "mcp", Paths: []PathSpec{{Base: BaseInstruction, Rel: ".mcp.json"}}},
			{Name: "settings", Paths: []PathSpec{
				{Base: BaseConfig, Rel: "settings.json"},
				{Base: BaseConfig, Rel: "settings.local.json"},
			}},
			{Name: "memory", Paths: []PathSpec{{Base: BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}
}
```

- [ ] **Step 5: Write `internal/manifest/codex.go`**

```go
package manifest

func Codex() ToolManifest {
	return ToolManifest{
		Tool: ToolCodex,
		Categories: []Category{
			{
				Name:     "skills",
				Paths:    []PathSpec{{Base: BaseConfig, Rel: "skills"}},
				Excludes: []string{"skills/.system"},
			},
			{Name: "rules", Paths: []PathSpec{{Base: BaseConfig, Rel: "rules"}}},
			{Name: "hooks", Paths: []PathSpec{{Base: BaseConfig, Rel: "hooks.json"}}},
			{Name: "plugins", Paths: []PathSpec{{Base: BaseConfig, Rel: "plugins"}}},
			{Name: "settings", Paths: []PathSpec{{Base: BaseConfig, Rel: "config.toml"}}},
			{Name: "memory", Paths: []PathSpec{{Base: BaseInstruction, Rel: "AGENTS.md"}}},
		},
	}
}
```

- [ ] **Step 6: Write `internal/manifest/registry.go`**

```go
package manifest

import "fmt"

func Lookup(tool Tool) (ToolManifest, error) {
	switch tool {
	case ToolClaude:
		return Claude(), nil
	case ToolCodex:
		return Codex(), nil
	default:
		return ToolManifest{}, fmt.Errorf("unknown tool %q", tool)
	}
}
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `go test ./internal/manifest/... -v`
Expected: PASS, all 5 tests.

- [ ] **Step 8: Commit**

```bash
git add internal/manifest
git commit -m "feat: add per-tool category manifests for claude and codex"
```

---

### Task 3: `internal/planner` — pure plan builder

**Files:**
- Create: `internal/planner/plan.go`
- Create: `internal/planner/build.go`
- Test: `internal/planner/build_test.go`

**Interfaces:**
- Consumes: `manifest.ToolManifest`, `manifest.Category`, `manifest.PathSpec`, `manifest.BaseConfig`/`manifest.BaseInstruction` (Task 2).
- Produces: `planner.Entry{Category, SourcePath, RelPath string; Excludes []string}`, `planner.Plan{Entries []Entry}`, `planner.Build(m manifest.ToolManifest, fs afero.Fs, configRoot, instructionRoot string) (Plan, error)`.

- [ ] **Step 1: Write the failing tests**

`internal/planner/build_test.go`:
```go
package planner_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestBuildIncludesExistingPathsOnly(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.claude/skills/foo", 0o755))

	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "skills", Paths: []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "skills"}}},
			{Name: "agents", Paths: []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "agents"}}},
		},
	}

	plan, err := planner.Build(m, fs, "/home/u/.claude", "/home/u/.claude")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, "skills", plan.Entries[0].Category)
	require.Equal(t, "/home/u/.claude/skills", plan.Entries[0].SourcePath)
	require.Equal(t, "skills", plan.Entries[0].RelPath)
}

func TestBuildUsesInstructionRootForMemoryStyleCategory(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/proj/CLAUDE.md", []byte("hi"), 0o644))

	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "memory", Paths: []manifest.PathSpec{{Base: manifest.BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}

	plan, err := planner.Build(m, fs, "/proj/.claude", "/proj")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, "/proj/CLAUDE.md", plan.Entries[0].SourcePath)
}

func TestBuildRecordsExcludesRelativeToSource(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.codex/skills/.system", 0o755))

	m := manifest.ToolManifest{
		Tool: manifest.ToolCodex,
		Categories: []manifest.Category{
			{
				Name:     "skills",
				Paths:    []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "skills"}},
				Excludes: []string{"skills/.system"},
			},
		},
	}

	plan, err := planner.Build(m, fs, "/home/u/.codex", "/home/u/.codex")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, []string{".system"}, plan.Entries[0].Excludes)
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/planner/... -v`
Expected: FAIL — package `planner` doesn't exist yet.

- [ ] **Step 3: Write `internal/planner/plan.go`**

```go
package planner

type Entry struct {
	Category   string
	SourcePath string
	RelPath    string
	Excludes   []string
}

type Plan struct {
	Entries []Entry
}
```

- [ ] **Step 4: Write `internal/planner/build.go`**

```go
package planner

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/manifest"
)

func Build(m manifest.ToolManifest, fs afero.Fs, configRoot, instructionRoot string) (Plan, error) {
	var plan Plan
	for _, cat := range m.Categories {
		for _, ps := range cat.Paths {
			base := configRoot
			if ps.Base == manifest.BaseInstruction {
				base = instructionRoot
			}
			abs := filepath.Join(base, ps.Rel)

			exists, err := afero.Exists(fs, abs)
			if err != nil {
				return Plan{}, fmt.Errorf("checking %s: %w", abs, err)
			}
			if !exists {
				continue
			}

			rel, err := filepath.Rel(configRoot, abs)
			if err != nil {
				return Plan{}, fmt.Errorf("computing relative path for %s: %w", abs, err)
			}

			plan.Entries = append(plan.Entries, Entry{
				Category:   cat.Name,
				SourcePath: abs,
				RelPath:    filepath.ToSlash(rel),
				Excludes:   excludesFor(configRoot, abs, cat.Excludes),
			})
		}
	}
	return plan, nil
}

func excludesFor(configRoot, abs string, excludes []string) []string {
	var out []string
	for _, ex := range excludes {
		exAbs := filepath.Join(configRoot, ex)
		if exAbs == abs || strings.HasPrefix(exAbs, abs+string(filepath.Separator)) {
			exRel, err := filepath.Rel(abs, exAbs)
			if err != nil {
				continue
			}
			out = append(out, filepath.ToSlash(exRel))
		}
	}
	return out
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `go test ./internal/planner/... -v`
Expected: PASS, all 3 tests.

- [ ] **Step 6: Commit**

```bash
git add internal/planner
git commit -m "feat: add pure Plan builder"
```

---

### Task 4: `internal/fsutil` — copy and delete over `afero.Fs`

**Files:**
- Create: `internal/fsutil/copy.go`
- Create: `internal/fsutil/delete.go`
- Create: `internal/fsutil/exclude.go`
- Test: `internal/fsutil/copy_test.go`
- Test: `internal/fsutil/delete_test.go`

**Interfaces:**
- Consumes: `afero.Fs` (third-party).
- Produces: `fsutil.CopyPath(fs afero.Fs, src, dst string, excludes []string) error`, `fsutil.DeletePath(fs afero.Fs, path string, excludes []string) error`.

- [ ] **Step 1: Write the failing tests**

`internal/fsutil/copy_test.go`:
```go
package fsutil_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestCopyPathCopiesFileTree(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/a/note.md", []byte("hello"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/b.md", []byte("world"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/skills", "/dst/skills", nil))

	data, err := afero.ReadFile(fs, "/dst/skills/a/note.md")
	require.NoError(t, err)
	require.Equal(t, "hello", string(data))

	data, err = afero.ReadFile(fs, "/dst/skills/b.md")
	require.NoError(t, err)
	require.Equal(t, "world", string(data))
}

func TestCopyPathSkipsExcludedSubpath(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/mine.md", []byte("mine"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/skills", "/dst/skills", []string{".system"}))

	exists, _ := afero.Exists(fs, "/dst/skills/.system/keep.md")
	require.False(t, exists)
	exists, _ = afero.Exists(fs, "/dst/skills/mine.md")
	require.True(t, exists)
}

func TestCopyPathCopiesSingleFile(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/CLAUDE.md", []byte("hi"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/CLAUDE.md", "/dst/CLAUDE.md", nil))

	data, err := afero.ReadFile(fs, "/dst/CLAUDE.md")
	require.NoError(t, err)
	require.Equal(t, "hi", string(data))
}
```

`internal/fsutil/delete_test.go`:
```go
package fsutil_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestDeletePathRemovesTree(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/agents/a.md", []byte("x"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/agents", nil))

	exists, _ := afero.Exists(fs, "/src/agents")
	require.False(t, exists)
}

func TestDeletePathKeepsExcludedChild(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/mine.md", []byte("mine"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/skills", []string{".system"}))

	exists, _ := afero.Exists(fs, "/src/skills/.system/keep.md")
	require.True(t, exists)
	exists, _ = afero.Exists(fs, "/src/skills/mine.md")
	require.False(t, exists)
}

func TestDeletePathRemovesSingleFile(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/settings.json", []byte("{}"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/settings.json", nil))

	exists, _ := afero.Exists(fs, "/src/settings.json")
	require.False(t, exists)
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/fsutil/... -v`
Expected: FAIL — package `fsutil` doesn't exist yet.

- [ ] **Step 3: Write `internal/fsutil/exclude.go`**

```go
package fsutil

import (
	"path/filepath"
	"strings"
)

func isExcluded(rel string, excludes []string) bool {
	for _, ex := range excludes {
		if rel == ex || strings.HasPrefix(rel, ex+string(filepath.Separator)) {
			return true
		}
	}
	return false
}
```

- [ ] **Step 4: Write `internal/fsutil/copy.go`**

```go
package fsutil

import (
	"os"
	"path/filepath"

	"github.com/spf13/afero"
)

func CopyPath(fs afero.Fs, src, dst string, excludes []string) error {
	info, err := fs.Stat(src)
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return copyFile(fs, src, dst)
	}
	return afero.Walk(fs, src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		if isExcluded(rel, excludes) {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return fs.MkdirAll(target, info.Mode())
		}
		return copyFile(fs, path, target)
	})
}

func copyFile(fs afero.Fs, src, dst string) error {
	data, err := afero.ReadFile(fs, src)
	if err != nil {
		return err
	}
	if err := fs.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}
	return afero.WriteFile(fs, dst, data, 0o644)
}
```

- [ ] **Step 5: Write `internal/fsutil/delete.go`**

```go
package fsutil

import (
	"path/filepath"

	"github.com/spf13/afero"
)

func DeletePath(fs afero.Fs, path string, excludes []string) error {
	if len(excludes) == 0 {
		return fs.RemoveAll(path)
	}
	info, err := fs.Stat(path)
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return fs.Remove(path)
	}
	entries, err := afero.ReadDir(fs, path)
	if err != nil {
		return err
	}
	for _, e := range entries {
		if isExcluded(e.Name(), excludes) {
			continue
		}
		if err := fs.RemoveAll(filepath.Join(path, e.Name())); err != nil {
			return err
		}
	}
	return nil
}
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `go test ./internal/fsutil/... -v`
Expected: PASS, all 6 tests.

- [ ] **Step 7: Commit**

```bash
git add internal/fsutil
git commit -m "feat: add exclude-aware copy and delete over afero.Fs"
```

---

### Task 5: `internal/backup` — backup manifest and `Run`

**Files:**
- Create: `internal/backup/manifest.go`
- Create: `internal/backup/run.go`
- Test: `internal/backup/manifest_test.go`
- Test: `internal/backup/run_test.go`

**Interfaces:**
- Consumes: `planner.Plan`/`planner.Entry` (Task 3), `fsutil.CopyPath` (Task 4).
- Produces: `backup.Entry{Category, SourcePath, BackupPath string}`, `backup.Manifest{Tool, Scope, Root, CreatedAt string; Categories []string; Entries []Entry}`, `backup.WriteManifest(fs afero.Fs, dir string, m Manifest) error`, `backup.ReadManifest(fs afero.Fs, dir string) (Manifest, error)`, `backup.Run(fs afero.Fs, plan planner.Plan, backupDir, tool, scope, root string, categories []string, createdAt string) (Manifest, error)`.

- [ ] **Step 1: Write the failing tests**

`internal/backup/manifest_test.go`:
```go
package backup_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestManifestRoundTrip(t *testing.T) {
	fs := afero.NewMemMapFs()
	m := backup.Manifest{
		Tool:       "claude",
		Scope:      "global",
		Root:       "/home/u/.claude",
		Categories: []string{"skills"},
		CreatedAt:  "2026-07-07T00:00:00Z",
		Entries: []backup.Entry{
			{Category: "skills", SourcePath: "/home/u/.claude/skills", BackupPath: "skills"},
		},
	}

	require.NoError(t, backup.WriteManifest(fs, "/backupdir", m))

	got, err := backup.ReadManifest(fs, "/backupdir")
	require.NoError(t, err)
	require.Equal(t, m, got)
}
```

`internal/backup/run_test.go`:
```go
package backup_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestRunCopiesEntriesAndWritesManifest(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))

	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.claude/skills", RelPath: "skills"},
	}}

	backupDir := "/home/u/.claude/killall-agents-backups/claude-20260707"
	m, err := backup.Run(fs, plan, backupDir, "claude", "global", "/home/u/.claude", []string{"skills"}, "2026-07-07T00:00:00Z")
	require.NoError(t, err)
	require.Len(t, m.Entries, 1)

	data, err := afero.ReadFile(fs, backupDir+"/skills/a.md")
	require.NoError(t, err)
	require.Equal(t, "hi", string(data))

	got, err := backup.ReadManifest(fs, backupDir)
	require.NoError(t, err)
	require.Equal(t, m, got)
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/backup/... -v`
Expected: FAIL — package `backup` doesn't exist yet.

- [ ] **Step 3: Write `internal/backup/manifest.go`**

```go
package backup

import (
	"encoding/json"
	"path/filepath"

	"github.com/spf13/afero"
)

type Entry struct {
	Category   string `json:"category"`
	SourcePath string `json:"sourcePath"`
	BackupPath string `json:"backupPath"`
}

type Manifest struct {
	Tool       string   `json:"tool"`
	Scope      string   `json:"scope"`
	Root       string   `json:"root"`
	Categories []string `json:"categories"`
	CreatedAt  string   `json:"createdAt"`
	Entries    []Entry  `json:"entries"`
}

const manifestFileName = "manifest.json"

func WriteManifest(fs afero.Fs, dir string, m Manifest) error {
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	return afero.WriteFile(fs, filepath.Join(dir, manifestFileName), data, 0o644)
}

func ReadManifest(fs afero.Fs, dir string) (Manifest, error) {
	data, err := afero.ReadFile(fs, filepath.Join(dir, manifestFileName))
	if err != nil {
		return Manifest{}, err
	}
	var m Manifest
	if err := json.Unmarshal(data, &m); err != nil {
		return Manifest{}, err
	}
	return m, nil
}
```

- [ ] **Step 4: Write `internal/backup/run.go`**

```go
package backup

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/killallgit/killall-agents/internal/planner"
)

func Run(fs afero.Fs, plan planner.Plan, backupDir, tool, scope, root string, categories []string, createdAt string) (Manifest, error) {
	m := Manifest{
		Tool:       tool,
		Scope:      scope,
		Root:       root,
		Categories: categories,
		CreatedAt:  createdAt,
	}
	for _, e := range plan.Entries {
		dst := filepath.Join(backupDir, e.RelPath)
		if err := fsutil.CopyPath(fs, e.SourcePath, dst, e.Excludes); err != nil {
			return Manifest{}, fmt.Errorf("backing up %s: %w", e.SourcePath, err)
		}
		m.Entries = append(m.Entries, Entry{
			Category:   e.Category,
			SourcePath: e.SourcePath,
			BackupPath: e.RelPath,
		})
	}
	if err := WriteManifest(fs, backupDir, m); err != nil {
		return Manifest{}, err
	}
	return m, nil
}
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `go test ./internal/backup/... -v`
Expected: PASS, both tests.

- [ ] **Step 6: Commit**

```bash
git add internal/backup
git commit -m "feat: add backup manifest and Run executor"
```

---

### Task 6: `internal/strip` — delete executor

**Files:**
- Create: `internal/strip/run.go`
- Test: `internal/strip/run_test.go`

**Interfaces:**
- Consumes: `planner.Plan`/`planner.Entry` (Task 3), `fsutil.DeletePath` (Task 4).
- Produces: `strip.Run(fs afero.Fs, plan planner.Plan) error`.

- [ ] **Step 1: Write the failing tests**

`internal/strip/run_test.go`:
```go
package strip_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/killallgit/killall-agents/internal/strip"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestRunDeletesPlanEntries(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))

	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.claude/skills", RelPath: "skills"},
	}}

	require.NoError(t, strip.Run(fs, plan))

	exists, _ := afero.Exists(fs, "/home/u/.claude/skills")
	require.False(t, exists)
}

func TestRunRespectsExcludes(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.codex/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/home/u/.codex/skills/mine.md", []byte("mine"), 0o644))

	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.codex/skills", RelPath: "skills", Excludes: []string{".system"}},
	}}

	require.NoError(t, strip.Run(fs, plan))

	exists, _ := afero.Exists(fs, "/home/u/.codex/skills/.system/keep.md")
	require.True(t, exists)
	exists, _ = afero.Exists(fs, "/home/u/.codex/skills/mine.md")
	require.False(t, exists)
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/strip/... -v`
Expected: FAIL — package `strip` doesn't exist yet.

- [ ] **Step 3: Write `internal/strip/run.go`**

```go
package strip

import (
	"fmt"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/killallgit/killall-agents/internal/planner"
)

func Run(fs afero.Fs, plan planner.Plan) error {
	for _, e := range plan.Entries {
		if err := fsutil.DeletePath(fs, e.SourcePath, e.Excludes); err != nil {
			return fmt.Errorf("stripping %s: %w", e.SourcePath, err)
		}
	}
	return nil
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `go test ./internal/strip/... -v`
Expected: PASS, both tests.

- [ ] **Step 5: Commit**

```bash
git add internal/strip
git commit -m "feat: add strip Run executor"
```

---

### Task 7: `internal/restore` — restore executor

**Files:**
- Create: `internal/restore/run.go`
- Test: `internal/restore/run_test.go`

**Interfaces:**
- Consumes: `backup.Manifest`/`backup.Entry` (Task 5), `fsutil.CopyPath` (Task 4).
- Produces: `restore.Run(fs afero.Fs, m backup.Manifest, backupDir string) error`.

- [ ] **Step 1: Write the failing test**

`internal/restore/run_test.go`:
```go
package restore_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/restore"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestRunCopiesBackupEntriesBackToSource(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/backupdir/skills/a.md", []byte("hi"), 0o644))

	m := backup.Manifest{
		Entries: []backup.Entry{
			{Category: "skills", SourcePath: "/home/u/.claude/skills", BackupPath: "skills"},
		},
	}

	require.NoError(t, restore.Run(fs, m, "/backupdir"))

	data, err := afero.ReadFile(fs, "/home/u/.claude/skills/a.md")
	require.NoError(t, err)
	require.Equal(t, "hi", string(data))
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./internal/restore/... -v`
Expected: FAIL — package `restore` doesn't exist yet.

- [ ] **Step 3: Write `internal/restore/run.go`**

```go
package restore

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/fsutil"
)

func Run(fs afero.Fs, m backup.Manifest, backupDir string) error {
	for _, e := range m.Entries {
		src := filepath.Join(backupDir, e.BackupPath)
		if err := fsutil.CopyPath(fs, src, e.SourcePath, nil); err != nil {
			return fmt.Errorf("restoring %s: %w", e.SourcePath, err)
		}
	}
	return nil
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `go test ./internal/restore/... -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add internal/restore
git commit -m "feat: add restore Run executor"
```

---

### Task 8: `internal/inventory` — plan formatting

**Files:**
- Create: `internal/inventory/format.go`
- Test: `internal/inventory/format_test.go`

**Interfaces:**
- Consumes: `planner.Plan`/`planner.Entry` (Task 3).
- Produces: `inventory.Format(plan planner.Plan) string`.

- [ ] **Step 1: Write the failing tests**

`internal/inventory/format_test.go`:
```go
package inventory_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/stretchr/testify/require"
)

func TestFormatListsEntriesByCategory(t *testing.T) {
	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.claude/skills"},
	}}
	out := inventory.Format(plan)
	require.Contains(t, out, "skills")
	require.Contains(t, out, "/home/u/.claude/skills")
}

func TestFormatNotesProtectedExcludes(t *testing.T) {
	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.codex/skills", Excludes: []string{".system"}},
	}}
	out := inventory.Format(plan)
	require.Contains(t, out, "protected")
	require.Contains(t, out, ".system")
}

func TestFormatEmptyPlan(t *testing.T) {
	out := inventory.Format(planner.Plan{})
	require.Contains(t, out, "No matching customization found")
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/inventory/... -v`
Expected: FAIL — package `inventory` doesn't exist yet.

- [ ] **Step 3: Write `internal/inventory/format.go`**

```go
package inventory

import (
	"fmt"
	"strings"

	"github.com/killallgit/killall-agents/internal/planner"
)

func Format(plan planner.Plan) string {
	if len(plan.Entries) == 0 {
		return "No matching customization found.\n"
	}
	var b strings.Builder
	for _, e := range plan.Entries {
		fmt.Fprintf(&b, "%-12s %s\n", e.Category, e.SourcePath)
		for _, ex := range e.Excludes {
			fmt.Fprintf(&b, "%-12s   (protected, will not touch: %s)\n", "", ex)
		}
	}
	return b.String()
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `go test ./internal/inventory/... -v`
Expected: PASS, all 3 tests.

- [ ] **Step 5: Commit**

```bash
git add internal/inventory
git commit -m "feat: add plan formatting for CLI output"
```

---

### Task 9: `internal/paths` — config root and backup root resolution

**Files:**
- Create: `internal/paths/paths.go`
- Test: `internal/paths/paths_test.go`

**Interfaces:**
- Consumes: `manifest.Tool`, `manifest.Scope`, `manifest.ScopeGlobal`, `manifest.ScopeProject` (Task 2).
- Produces: `paths.HomeDirFunc func() (string, error)`, `paths.ConfigRoot(tool manifest.Tool, scope manifest.Scope, projectPath string, homeDir HomeDirFunc) (configRoot, instructionRoot string, err error)`, `paths.BackupRoot(configRoot string) string`.

- [ ] **Step 1: Write the failing tests**

`internal/paths/paths_test.go`:
```go
package paths_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/stretchr/testify/require"
)

func TestConfigRootGlobalUsesHomeDir(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	configRoot, instructionRoot, err := paths.ConfigRoot(manifest.ToolClaude, manifest.ScopeGlobal, "", home)
	require.NoError(t, err)
	require.Equal(t, "/home/u/.claude", configRoot)
	require.Equal(t, configRoot, instructionRoot)
}

func TestConfigRootProjectUsesProjectPath(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	configRoot, instructionRoot, err := paths.ConfigRoot(manifest.ToolCodex, manifest.ScopeProject, "/work/proj", home)
	require.NoError(t, err)
	require.Equal(t, "/work/proj/.codex", configRoot)
	require.Equal(t, "/work/proj", instructionRoot)
}

func TestConfigRootProjectRequiresPath(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	_, _, err := paths.ConfigRoot(manifest.ToolClaude, manifest.ScopeProject, "", home)
	require.Error(t, err)
}

func TestBackupRootIsUnderConfigRoot(t *testing.T) {
	require.Equal(t, "/home/u/.claude/killall-agents-backups", paths.BackupRoot("/home/u/.claude"))
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./internal/paths/... -v`
Expected: FAIL — package `paths` doesn't exist yet.

- [ ] **Step 3: Write `internal/paths/paths.go`**

```go
package paths

import (
	"fmt"
	"path/filepath"

	"github.com/killallgit/killall-agents/internal/manifest"
)

type HomeDirFunc func() (string, error)

func ConfigRoot(tool manifest.Tool, scope manifest.Scope, projectPath string, homeDir HomeDirFunc) (configRoot, instructionRoot string, err error) {
	dirName := "." + string(tool)

	if scope == manifest.ScopeProject {
		if projectPath == "" {
			return "", "", fmt.Errorf("project path required for project scope")
		}
		return filepath.Join(projectPath, dirName), projectPath, nil
	}

	home, err := homeDir()
	if err != nil {
		return "", "", err
	}
	configRoot = filepath.Join(home, dirName)
	return configRoot, configRoot, nil
}

func BackupRoot(configRoot string) string {
	return filepath.Join(configRoot, "killall-agents-backups")
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `go test ./internal/paths/... -v`
Expected: PASS, all 4 tests.

- [ ] **Step 5: Commit**

```bash
git add internal/paths
git commit -m "feat: add config root and backup root resolution"
```

---

### Task 10: CLI scaffolding — `main.go`, `root.go`, `tools.go`

**Files:**
- Create: `cmd/killall-agents/main.go` (replaces Task 1 placeholder)
- Create: `cmd/killall-agents/root.go`
- Create: `cmd/killall-agents/tools.go`
- Test: `cmd/killall-agents/tools_test.go`

**Interfaces:**
- Consumes: `manifest.Tool`, `manifest.ToolClaude`, `manifest.ToolCodex` (Task 2), `paths.HomeDirFunc` (Task 9).
- Produces: `resolveTools(flag string) ([]manifest.Tool, error)`, `NewRootCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command` (subcommands are added to this in Tasks 11–15, each via a one-line change immediately before `return root`).

- [ ] **Step 1: Write the failing test**

`cmd/killall-agents/tools_test.go`:
```go
package main

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/stretchr/testify/require"
)

func TestResolveToolsAll(t *testing.T) {
	tools, err := resolveTools("all")
	require.NoError(t, err)
	require.ElementsMatch(t, []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, tools)
}

func TestResolveToolsEmptyDefaultsToAll(t *testing.T) {
	tools, err := resolveTools("")
	require.NoError(t, err)
	require.ElementsMatch(t, []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, tools)
}

func TestResolveToolsSingle(t *testing.T) {
	tools, err := resolveTools("codex")
	require.NoError(t, err)
	require.Equal(t, []manifest.Tool{manifest.ToolCodex}, tools)
}

func TestResolveToolsUnknown(t *testing.T) {
	_, err := resolveTools("bogus")
	require.Error(t, err)
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./cmd/killall-agents/... -v`
Expected: FAIL — `resolveTools` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/tools.go`**

```go
package main

import (
	"fmt"

	"github.com/killallgit/killall-agents/internal/manifest"
)

func resolveTools(flag string) ([]manifest.Tool, error) {
	switch flag {
	case "", "all":
		return []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, nil
	case "claude":
		return []manifest.Tool{manifest.ToolClaude}, nil
	case "codex":
		return []manifest.Tool{manifest.ToolCodex}, nil
	default:
		return nil, fmt.Errorf("unknown --tool %q", flag)
	}
}
```

- [ ] **Step 4: Write `cmd/killall-agents/root.go`**

```go
package main

import (
	"io"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/paths"
)

func NewRootCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command {
	root := &cobra.Command{
		Use:   "killall-agents",
		Short: "Backup and strip Claude Code / Codex customization",
	}
	return root
}
```

- [ ] **Step 5: Replace `cmd/killall-agents/main.go`**

```go
package main

import (
	"os"

	"github.com/spf13/afero"
)

func main() {
	root := NewRootCmd(afero.NewOsFs(), os.UserHomeDir, os.Stdin)
	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}
```

- [ ] **Step 6: Run test to verify it passes, and confirm the binary still builds**

Run:
```bash
go test ./cmd/killall-agents/... -v
go build ./...
```
Expected: tests PASS; build exits 0.

- [ ] **Step 7: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add CLI scaffolding with tool resolution"
```

---

### Task 11: `inventory` subcommand

**Files:**
- Create: `cmd/killall-agents/inventory.go`
- Modify: `cmd/killall-agents/root.go`
- Test: `cmd/killall-agents/inventory_test.go`

**Interfaces:**
- Consumes: `resolveTools` (Task 10), `manifest.Lookup` (Task 2), `paths.ConfigRoot` (Task 9), `planner.Build` (Task 3), `inventory.Format` (Task 8).
- Produces: `NewInventoryCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command`.

- [ ] **Step 1: Write the failing test**

`cmd/killall-agents/inventory_test.go`:
```go
package main

import (
	"bytes"
	"testing"

	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestInventoryCmdPrintsFoundCategories(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.claude/skills/foo", 0o755))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewInventoryCmd(fs, home)
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude"})

	require.NoError(t, cmd.Execute())
	require.Contains(t, buf.String(), "skills")
	require.Contains(t, buf.String(), "/home/u/.claude/skills")
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./cmd/killall-agents/... -run TestInventoryCmd -v`
Expected: FAIL — `NewInventoryCmd` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/inventory.go`**

```go
package main

import (
	"fmt"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
)

func NewInventoryCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, projectFlag string

	cmd := &cobra.Command{
		Use:   "inventory",
		Short: "Show installed customization for a tool",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				m, err := manifest.Lookup(t)
				if err != nil {
					return err
				}
				scope := manifest.ScopeGlobal
				if projectFlag != "" {
					scope = manifest.ScopeProject
				}
				configRoot, instructionRoot, err := paths.ConfigRoot(t, scope, projectFlag, homeDir)
				if err != nil {
					return err
				}
				plan, err := planner.Build(m, fs, configRoot, instructionRoot)
				if err != nil {
					return err
				}
				fmt.Fprintf(cmd.OutOrStdout(), "== %s (%s) ==\n", t, configRoot)
				fmt.Fprint(cmd.OutOrStdout(), inventory.Format(plan))
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	return cmd
}
```

- [ ] **Step 4: Modify `cmd/killall-agents/root.go` — add the subcommand**

In `NewRootCmd`, immediately before `return root`, add:
```go
	root.AddCommand(NewInventoryCmd(fs, homeDir))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `go test ./cmd/killall-agents/... -run TestInventoryCmd -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add inventory subcommand"
```

---

### Task 12: `backup` subcommand

**Files:**
- Create: `cmd/killall-agents/backup.go`
- Modify: `cmd/killall-agents/root.go`
- Test: `cmd/killall-agents/backup_test.go`

**Interfaces:**
- Consumes: `resolveTools` (Task 10), `manifest.Lookup`/`manifest.ToolManifest`/`manifest.Category` (Task 2), `paths.ConfigRoot`/`paths.BackupRoot` (Task 9), `planner.Build` (Task 3), `backup.Run` (Task 5).
- Produces: `NewBackupCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command`, and helpers reused by Task 13: `runBackup(w io.Writer, fs afero.Fs, homeDir paths.HomeDirFunc, t manifest.Tool, projectFlag, categoriesFlag string) (backup.Manifest, string, error)`, `filterCategories(m manifest.ToolManifest, names []string) manifest.ToolManifest`, `categoryNames(m manifest.ToolManifest) []string`.

- [ ] **Step 1: Write the failing test**

`cmd/killall-agents/backup_test.go`:
```go
package main

import (
	"bytes"
	"testing"

	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestBackupCmdCopiesFilesAndPrintsPath(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewBackupCmd(fs, home)
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude", "--categories", "skills"})

	require.NoError(t, cmd.Execute())
	require.Contains(t, buf.String(), "backed up claude ->")

	entries, err := afero.ReadDir(fs, "/home/u/.claude/killall-agents-backups")
	require.NoError(t, err)
	require.Len(t, entries, 1)
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./cmd/killall-agents/... -run TestBackupCmd -v`
Expected: FAIL — `NewBackupCmd` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/backup.go`**

```go
package main

import (
	"fmt"
	"io"
	"path/filepath"
	"strings"
	"time"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
)

func NewBackupCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, projectFlag, categoriesFlag string

	cmd := &cobra.Command{
		Use:   "backup",
		Short: "Back up customization without stripping it",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				if _, _, err := runBackup(cmd.OutOrStdout(), fs, homeDir, t, projectFlag, categoriesFlag); err != nil {
					return err
				}
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	cmd.Flags().StringVar(&categoriesFlag, "categories", "", "comma-separated category filter (default: all)")
	return cmd
}

func runBackup(w io.Writer, fs afero.Fs, homeDir paths.HomeDirFunc, t manifest.Tool, projectFlag, categoriesFlag string) (backup.Manifest, string, error) {
	m, err := manifest.Lookup(t)
	if err != nil {
		return backup.Manifest{}, "", err
	}
	if categoriesFlag != "" {
		m = filterCategories(m, strings.Split(categoriesFlag, ","))
	}

	scope := manifest.ScopeGlobal
	if projectFlag != "" {
		scope = manifest.ScopeProject
	}

	configRoot, instructionRoot, err := paths.ConfigRoot(t, scope, projectFlag, homeDir)
	if err != nil {
		return backup.Manifest{}, "", err
	}

	plan, err := planner.Build(m, fs, configRoot, instructionRoot)
	if err != nil {
		return backup.Manifest{}, "", err
	}

	stamp := time.Now().UTC().Format("20060102-150405")
	backupDir := filepath.Join(paths.BackupRoot(configRoot), fmt.Sprintf("%s-%s", t, stamp))

	man, err := backup.Run(fs, plan, backupDir, string(t), string(scope), configRoot, categoryNames(m), time.Now().UTC().Format(time.RFC3339))
	if err != nil {
		return backup.Manifest{}, "", err
	}

	fmt.Fprintf(w, "backed up %s -> %s\n", t, backupDir)
	return man, backupDir, nil
}

func filterCategories(m manifest.ToolManifest, names []string) manifest.ToolManifest {
	want := map[string]bool{}
	for _, n := range names {
		want[strings.TrimSpace(n)] = true
	}
	var kept []manifest.Category
	for _, c := range m.Categories {
		if want[c.Name] {
			kept = append(kept, c)
		}
	}
	return manifest.ToolManifest{Tool: m.Tool, Categories: kept}
}

func categoryNames(m manifest.ToolManifest) []string {
	names := make([]string, len(m.Categories))
	for i, c := range m.Categories {
		names[i] = c.Name
	}
	return names
}
```

- [ ] **Step 4: Modify `cmd/killall-agents/root.go` — add the subcommand**

In `NewRootCmd`, immediately before `return root`, add:
```go
	root.AddCommand(NewBackupCmd(fs, homeDir))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `go test ./cmd/killall-agents/... -run TestBackupCmd -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add backup subcommand"
```

---

### Task 13: `strip` subcommand

**Files:**
- Create: `cmd/killall-agents/strip.go`
- Modify: `cmd/killall-agents/root.go`
- Test: `cmd/killall-agents/strip_test.go`

**Interfaces:**
- Consumes: `resolveTools` (Task 10), `manifest.Lookup` (Task 2), `paths.ConfigRoot` (Task 9), `planner.Build` (Task 3), `inventory.Format` (Task 8), `runBackup`/`filterCategories` (Task 12), `strip.Run` (Task 6).
- Produces: `NewStripCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command`.

- [ ] **Step 1: Write the failing tests**

`cmd/killall-agents/strip_test.go`:
```go
package main

import (
	"bytes"
	"strings"
	"testing"

	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestStripCmdDryRunLeavesFilesUntouched(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewStripCmd(fs, home, strings.NewReader(""))
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude", "--categories", "skills", "--dry-run"})

	require.NoError(t, cmd.Execute())

	exists, _ := afero.Exists(fs, "/home/u/.claude/skills/a.md")
	require.True(t, exists)
}

func TestStripCmdWithYesBacksUpThenDeletes(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewStripCmd(fs, home, strings.NewReader(""))
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude", "--categories", "skills", "--yes"})

	require.NoError(t, cmd.Execute())

	exists, _ := afero.Exists(fs, "/home/u/.claude/skills")
	require.False(t, exists)

	entries, err := afero.ReadDir(fs, "/home/u/.claude/killall-agents-backups")
	require.NoError(t, err)
	require.Len(t, entries, 1)
}

func TestStripCmdWithoutYesRequiresConfirmation(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewStripCmd(fs, home, strings.NewReader("n\n"))
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude", "--categories", "skills"})

	require.NoError(t, cmd.Execute())

	exists, _ := afero.Exists(fs, "/home/u/.claude/skills/a.md")
	require.True(t, exists)
	require.Contains(t, buf.String(), "aborted")
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./cmd/killall-agents/... -run TestStripCmd -v`
Expected: FAIL — `NewStripCmd` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/strip.go`**

```go
package main

import (
	"bufio"
	"fmt"
	"io"
	"strings"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/killallgit/killall-agents/internal/strip"
)

func NewStripCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command {
	var toolFlag, projectFlag, categoriesFlag string
	var dryRun, yes bool

	cmd := &cobra.Command{
		Use:   "strip",
		Short: "Back up then remove customization",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				m, err := manifest.Lookup(t)
				if err != nil {
					return err
				}
				if categoriesFlag != "" {
					m = filterCategories(m, strings.Split(categoriesFlag, ","))
				}

				scope := manifest.ScopeGlobal
				if projectFlag != "" {
					scope = manifest.ScopeProject
				}
				configRoot, instructionRoot, err := paths.ConfigRoot(t, scope, projectFlag, homeDir)
				if err != nil {
					return err
				}

				plan, err := planner.Build(m, fs, configRoot, instructionRoot)
				if err != nil {
					return err
				}

				fmt.Fprintf(cmd.OutOrStdout(), "== plan for %s (%s) ==\n", t, configRoot)
				fmt.Fprint(cmd.OutOrStdout(), inventory.Format(plan))

				if len(plan.Entries) == 0 || dryRun {
					continue
				}
				if !yes && !confirm(cmd.OutOrStdout(), in) {
					fmt.Fprintln(cmd.OutOrStdout(), "aborted")
					continue
				}

				if _, _, err := runBackup(cmd.OutOrStdout(), fs, homeDir, t, projectFlag, categoriesFlag); err != nil {
					return err
				}
				if err := strip.Run(fs, plan); err != nil {
					return err
				}
				fmt.Fprintf(cmd.OutOrStdout(), "stripped %s\n", t)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	cmd.Flags().StringVar(&categoriesFlag, "categories", "", "comma-separated category filter (default: all)")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "print plan only, no writes")
	cmd.Flags().BoolVar(&yes, "yes", false, "skip confirmation prompt")
	return cmd
}

func confirm(w io.Writer, in io.Reader) bool {
	fmt.Fprint(w, "proceed with backup + strip? [y/N]: ")
	line, _ := bufio.NewReader(in).ReadString('\n')
	line = strings.TrimSpace(strings.ToLower(line))
	return line == "y" || line == "yes"
}
```

- [ ] **Step 4: Modify `cmd/killall-agents/root.go` — add the subcommand**

In `NewRootCmd`, immediately before `return root`, add:
```go
	root.AddCommand(NewStripCmd(fs, homeDir, in))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `go test ./cmd/killall-agents/... -run TestStripCmd -v`
Expected: PASS, all 3 tests.

- [ ] **Step 6: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add strip subcommand with confirm/dry-run/yes"
```

---

### Task 14: `restore` subcommand

**Files:**
- Create: `cmd/killall-agents/restore.go`
- Modify: `cmd/killall-agents/root.go`
- Test: `cmd/killall-agents/restore_test.go`

**Interfaces:**
- Consumes: `manifest.Lookup` (Task 2), `paths.ConfigRoot`/`paths.BackupRoot` (Task 9), `backup.ReadManifest` (Task 5), `restore.Run` (Task 7).
- Produces: `NewRestoreCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command`.

- [ ] **Step 1: Write the failing test**

`cmd/killall-agents/restore_test.go`:
```go
package main

import (
	"bytes"
	"testing"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestRestoreCmdCopiesFilesBack(t *testing.T) {
	fs := afero.NewMemMapFs()
	backupDir := "/home/u/.claude/killall-agents-backups/claude-20260707"
	require.NoError(t, afero.WriteFile(fs, backupDir+"/skills/a.md", []byte("hi"), 0o644))
	man := backup.Manifest{
		Entries: []backup.Entry{
			{Category: "skills", SourcePath: "/home/u/.claude/skills", BackupPath: "skills"},
		},
	}
	require.NoError(t, backup.WriteManifest(fs, backupDir, man))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewRestoreCmd(fs, home)
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude", "--from", "claude-20260707"})

	require.NoError(t, cmd.Execute())

	data, err := afero.ReadFile(fs, "/home/u/.claude/skills/a.md")
	require.NoError(t, err)
	require.Equal(t, "hi", string(data))
}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `go test ./cmd/killall-agents/... -run TestRestoreCmd -v`
Expected: FAIL — `NewRestoreCmd` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/restore.go`**

```go
package main

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/restore"
)

func NewRestoreCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, fromFlag string

	cmd := &cobra.Command{
		Use:   "restore",
		Short: "Restore customization from a backup",
		RunE: func(cmd *cobra.Command, args []string) error {
			if toolFlag == "" || toolFlag == "all" {
				return fmt.Errorf("--tool must be claude or codex")
			}
			t := manifest.Tool(toolFlag)
			if _, err := manifest.Lookup(t); err != nil {
				return err
			}
			if fromFlag == "" {
				return fmt.Errorf("--from is required")
			}

			backupDir := fromFlag
			if !strings.ContainsRune(backupDir, filepath.Separator) {
				configRoot, _, err := paths.ConfigRoot(t, manifest.ScopeGlobal, "", homeDir)
				if err != nil {
					return err
				}
				backupDir = filepath.Join(paths.BackupRoot(configRoot), fromFlag)
			}

			m, err := backup.ReadManifest(fs, backupDir)
			if err != nil {
				return err
			}
			if err := restore.Run(fs, m, backupDir); err != nil {
				return err
			}
			fmt.Fprintf(cmd.OutOrStdout(), "restored %s from %s\n", t, backupDir)
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "", "claude|codex (required)")
	cmd.Flags().StringVar(&fromFlag, "from", "", "backup id or path (required)")
	return cmd
}
```

- [ ] **Step 4: Modify `cmd/killall-agents/root.go` — add the subcommand**

In `NewRootCmd`, immediately before `return root`, add:
```go
	root.AddCommand(NewRestoreCmd(fs, homeDir))
```

- [ ] **Step 5: Run test to verify it passes**

Run: `go test ./cmd/killall-agents/... -run TestRestoreCmd -v`
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add restore subcommand"
```

---

### Task 15: `list-backups` subcommand

**Files:**
- Create: `cmd/killall-agents/list_backups.go`
- Modify: `cmd/killall-agents/root.go`
- Test: `cmd/killall-agents/list_backups_test.go`

**Interfaces:**
- Consumes: `resolveTools` (Task 10), `paths.ConfigRoot`/`paths.BackupRoot` (Task 9).
- Produces: `NewListBackupsCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command`.

- [ ] **Step 1: Write the failing test**

`cmd/killall-agents/list_backups_test.go`:
```go
package main

import (
	"bytes"
	"testing"

	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestListBackupsCmdPrintsBackupIDs(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.claude/killall-agents-backups/claude-20260707-120000", 0o755))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewListBackupsCmd(fs, home)
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "claude"})

	require.NoError(t, cmd.Execute())
	require.Contains(t, buf.String(), "claude-20260707-120000")
}

func TestListBackupsCmdHandlesNoBackupsYet(t *testing.T) {
	fs := afero.NewMemMapFs()
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewListBackupsCmd(fs, home)
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "codex"})

	require.NoError(t, cmd.Execute())
	require.Empty(t, buf.String())
}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `go test ./cmd/killall-agents/... -run TestListBackupsCmd -v`
Expected: FAIL — `NewListBackupsCmd` undefined.

- [ ] **Step 3: Write `cmd/killall-agents/list_backups.go`**

```go
package main

import (
	"fmt"
	"os"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
)

func NewListBackupsCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag string

	cmd := &cobra.Command{
		Use:   "list-backups",
		Short: "List available backups",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				configRoot, _, err := paths.ConfigRoot(t, manifest.ScopeGlobal, "", homeDir)
				if err != nil {
					return err
				}
				entries, err := afero.ReadDir(fs, paths.BackupRoot(configRoot))
				if err != nil {
					if os.IsNotExist(err) {
						continue
					}
					return err
				}
				for _, e := range entries {
					fmt.Fprintf(cmd.OutOrStdout(), "%s\t%s\n", t, e.Name())
				}
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	return cmd
}
```

- [ ] **Step 4: Modify `cmd/killall-agents/root.go` — add the subcommand**

In `NewRootCmd`, immediately before `return root`, add:
```go
	root.AddCommand(NewListBackupsCmd(fs, homeDir))
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `go test ./cmd/killall-agents/... -run TestListBackupsCmd -v`
Expected: PASS, both tests.

- [ ] **Step 6: Commit**

```bash
git add cmd/killall-agents
git commit -m "feat: add list-backups subcommand"
```

---

### Task 16: Full test suite and lint gate

**Files:**
- Modify: whichever files `golangci-lint`/`go vet` flag (none known in advance).

**Interfaces:**
- Consumes: everything from Tasks 1–15.
- Produces: a green `task ci` run — the deliverable this task's reviewer checks.

- [ ] **Step 1: Run the full suite**

Run: `go test ./... -race -cover -v`
Expected: PASS for every package (`manifest`, `planner`, `fsutil`, `backup`, `strip`, `restore`, `inventory`, `paths`, `main`/`cmd/killall-agents`).

- [ ] **Step 2: Run the full CI target**

Run: `task ci`
Expected: exit 0. If `golangci-lint` or `gofmt` report issues, fix them in the flagged files (formatting, unused imports/vars, error-check misses) and re-run `task ci` until it exits 0.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "chore: fix lint/fmt issues found by task ci"
```
(Skip this step if Step 2 was already clean — nothing to commit.)

---

### Task 17: GitHub Actions CI workflow

**Files:**
- Create: `.github/workflows/ci.yml`

**Interfaces:**
- Consumes: `Taskfile.yml`'s `ci` target (Task 1).
- Produces: a CI workflow that runs on every push/PR to `main`.

- [ ] **Step 1: Write `.github/workflows/ci.yml`**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  ci:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'

      - name: Install Task
        uses: arduino/setup-task@v2
        with:
          version: 3.x

      - name: Install golangci-lint
        run: go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest

      - name: Run CI tasks
        run: task ci
```

- [ ] **Step 2: Validate the YAML is well-formed**

Run:
```bash
python3 -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"
```
Expected: exits 0, no output.

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions workflow running task ci"
```

- [ ] **Step 4: Push and confirm the Actions run is green (requires your confirmation before pushing)**

This step pushes to the remote — confirm with the user before running `git push`, then check the Actions tab on GitHub for a green run on the pushed branch/PR.

---

## Done criteria

- `task ci` passes locally (fmt, lint, test, build).
- `killall-agents inventory --tool all` reports categories found under `~/.claude` and `~/.codex` (or `--project <path>`).
- `killall-agents strip --tool claude --dry-run` prints a plan and writes nothing.
- `killall-agents strip --tool claude --yes` backs up then deletes, and the backup directory mirrors the original tree.
- `killall-agents restore --tool claude --from <backup-id>` puts everything back.
- `killall-agents list-backups --tool all` lists prior backups.
- GitHub Actions runs `task ci` on push/PR to `main`.
