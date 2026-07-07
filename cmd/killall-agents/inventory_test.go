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
