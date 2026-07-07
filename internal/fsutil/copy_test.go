package fsutil_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestCopyPathCopiesFileTree(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/a/note.md", []byte("hello"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/b.md", []byte("world"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/skills", "/dst/skills", nil))

	data, err := afero.ReadFile(fs, "/dst/skills/a/note.md")
	require.NoError(t, err)
	require.Equal(t, "hello", string(data))

	data, err = afero.ReadFile(fs, "/dst/skills/b.md")
	require.NoError(t, err)
	require.Equal(t, "world", string(data))
}

func TestCopyPathSkipsExcludedSubpath(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/src/skills/mine.md", []byte("mine"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/skills", "/dst/skills", []string{".system"}))

	exists, _ := afero.Exists(fs, "/dst/skills/.system/keep.md")
	require.False(t, exists)
	exists, _ = afero.Exists(fs, "/dst/skills/mine.md")
	require.True(t, exists)
}

func TestCopyPathCopiesSingleFile(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/src/CLAUDE.md", []byte("hi"), 0o644))

	require.NoError(t, fsutil.CopyPath(fs, "/src/CLAUDE.md", "/dst/CLAUDE.md", nil))

	data, err := afero.ReadFile(fs, "/dst/CLAUDE.md")
	require.NoError(t, err)
	require.Equal(t, "hi", string(data))
}
