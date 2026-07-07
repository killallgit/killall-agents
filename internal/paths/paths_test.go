package paths_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/stretchr/testify/require"
)

func TestConfigRootGlobalUsesHomeDir(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	configRoot, instructionRoot, err := paths.ConfigRoot(manifest.ToolClaude, manifest.ScopeGlobal, "", home)
	require.NoError(t, err)
	require.Equal(t, "/home/u/.claude", configRoot)
	require.Equal(t, configRoot, instructionRoot)
}

func TestConfigRootProjectUsesProjectPath(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	configRoot, instructionRoot, err := paths.ConfigRoot(manifest.ToolCodex, manifest.ScopeProject, "/work/proj", home)
	require.NoError(t, err)
	require.Equal(t, "/work/proj/.codex", configRoot)
	require.Equal(t, "/work/proj", instructionRoot)
}

func TestConfigRootProjectRequiresPath(t *testing.T) {
	home := func() (string, error) { return "/home/u", nil }

	_, _, err := paths.ConfigRoot(manifest.ToolClaude, manifest.ScopeProject, "", home)
	require.Error(t, err)
}

func TestBackupRootIsUnderConfigRoot(t *testing.T) {
	require.Equal(t, "/home/u/.claude/killall-agents-backups", paths.BackupRoot("/home/u/.claude"))
}
