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
