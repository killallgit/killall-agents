package backup_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/manifest"
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

func TestRunDoesNotCollideAcrossSuccessiveProjectScopeBackups(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/proj/CLAUDE.md", []byte("content-v1"), 0o644))

	// Instruction-root category ("memory") in project scope: configRoot
	// (/proj/.claude) differs from instructionRoot (/proj), which is exactly
	// the scenario that used to make planner.Build emit an escaping RelPath
	// ("../CLAUDE.md"), collapsing every backupDir to the same collision path.
	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "memory", Paths: []manifest.PathSpec{{Base: manifest.BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}

	plan1, err := planner.Build(m, fs, "/proj/.claude", "/proj")
	require.NoError(t, err)

	backupDir1 := "/proj/.claude/killall-agents-backups/claude-20260707-150405"
	_, err = backup.Run(fs, plan1, backupDir1, "claude", "project", "/proj", []string{"memory"}, "2026-07-07T15:04:05Z")
	require.NoError(t, err)

	require.NoError(t, afero.WriteFile(fs, "/proj/CLAUDE.md", []byte("content-v2"), 0o644))

	plan2, err := planner.Build(m, fs, "/proj/.claude", "/proj")
	require.NoError(t, err)

	backupDir2 := "/proj/.claude/killall-agents-backups/claude-20260707-150406"
	_, err = backup.Run(fs, plan2, backupDir2, "claude", "project", "/proj", []string{"memory"}, "2026-07-07T15:04:06Z")
	require.NoError(t, err)

	data1, err := afero.ReadFile(fs, backupDir1+"/CLAUDE.md")
	require.NoError(t, err)
	require.Equal(t, "content-v1", string(data1))

	data2, err := afero.ReadFile(fs, backupDir2+"/CLAUDE.md")
	require.NoError(t, err)
	require.Equal(t, "content-v2", string(data2))
}
