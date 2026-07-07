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
