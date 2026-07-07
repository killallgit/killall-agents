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
