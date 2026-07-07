package strip_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/killallgit/killall-agents/internal/strip"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestRunDeletesPlanEntries(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.claude/skills/a.md", []byte("hi"), 0o644))

	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.claude/skills", RelPath: "skills"},
	}}

	require.NoError(t, strip.Run(fs, plan))

	exists, _ := afero.Exists(fs, "/home/u/.claude/skills")
	require.False(t, exists)
}

func TestRunRespectsExcludes(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/home/u/.codex/skills/.system/keep.md", []byte("keep"), 0o644))
	require.NoError(t, afero.WriteFile(fs, "/home/u/.codex/skills/mine.md", []byte("mine"), 0o644))

	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.codex/skills", RelPath: "skills", Excludes: []string{".system"}},
	}}

	require.NoError(t, strip.Run(fs, plan))

	exists, _ := afero.Exists(fs, "/home/u/.codex/skills/.system/keep.md")
	require.True(t, exists)
	exists, _ = afero.Exists(fs, "/home/u/.codex/skills/mine.md")
	require.False(t, exists)
}
