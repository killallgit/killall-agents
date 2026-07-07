package fsutil_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestDeletePathRemovesTree(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/agents/a.md", []byte("x"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/agents", nil))

	exists, _ := afero.Exists(fs, "/src/agents")
	require.False(t, exists)
}

func TestDeletePathKeepsExcludedChild(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/mine.md", []byte("mine"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/skills", []string{".system"}))

	exists, _ := afero.Exists(fs, "/src/skills/.system/keep.md")
	require.True(t, exists)
	exists, _ = afero.Exists(fs, "/src/skills/mine.md")
	require.False(t, exists)
}

func TestDeletePathRemovesSingleFile(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/settings.json", []byte("{}"), 0o644))

	require.NoError(t, fsutil.DeletePath(fs, "/src/settings.json", nil))

	exists, _ := afero.Exists(fs, "/src/settings.json")
	require.False(t, exists)
}
