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
