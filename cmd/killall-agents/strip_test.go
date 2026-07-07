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
