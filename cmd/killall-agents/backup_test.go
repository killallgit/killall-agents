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
