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

func TestStripCmdMultiToolConfirmationsAreIndependent(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/home/u/.codex/skills/b.md", []byte("hi"), 0o644))
	home := func() (string, error) { return "/home/u", nil }

	cmd := NewStripCmd(fs, home, strings.NewReader("n\ny\n"))
	buf := &bytes.Buffer{}
	cmd.SetOut(buf)
	cmd.SetArgs([]string{"--tool", "all", "--categories", "skills"})

	require.NoError(t, cmd.Execute())

	claudeExists, _ := afero.Exists(fs, "/home/u/.claude/skills/a.md")
	require.True(t, claudeExists, "claude should abort on 'n' and leave files untouched")

	codexFileExists, _ := afero.Exists(fs, "/home/u/.codex/skills/b.md")
	require.False(t, codexFileExists, "codex should proceed on 'y' and have its files stripped")

	entries, err := afero.ReadDir(fs, "/home/u/.codex/killall-agents-backups")
	require.NoError(t, err)
	require.Len(t, entries, 1, "codex should have been backed up before stripping")
}
