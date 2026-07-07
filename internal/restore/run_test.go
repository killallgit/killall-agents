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
