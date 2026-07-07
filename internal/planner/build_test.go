package planner_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/spf13/afero"
	"github.com/stretchr/testify/require"
)

func TestBuildIncludesExistingPathsOnly(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.claude/skills/foo", 0o755))

	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "skills", Paths: []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "skills"}}},
			{Name: "agents", Paths: []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "agents"}}},
		},
	}

	plan, err := planner.Build(m, fs, "/home/u/.claude", "/home/u/.claude")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, "skills", plan.Entries[0].Category)
	require.Equal(t, "/home/u/.claude/skills", plan.Entries[0].SourcePath)
	require.Equal(t, "skills", plan.Entries[0].RelPath)
}

func TestBuildUsesInstructionRootForMemoryStyleCategory(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/proj/CLAUDE.md", []byte("hi"), 0o644))

	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "memory", Paths: []manifest.PathSpec{{Base: manifest.BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}

	plan, err := planner.Build(m, fs, "/proj/.claude", "/proj")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, "/proj/CLAUDE.md", plan.Entries[0].SourcePath)
}

func TestBuildInstructionRootRelPathDoesNotEscapeInProjectScope(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, afero.WriteFile(fs, "/proj/CLAUDE.md", []byte("hi"), 0o644))

	m := manifest.ToolManifest{
		Tool: manifest.ToolClaude,
		Categories: []manifest.Category{
			{Name: "memory", Paths: []manifest.PathSpec{{Base: manifest.BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}

	plan, err := planner.Build(m, fs, "/proj/.claude", "/proj")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, "CLAUDE.md", plan.Entries[0].RelPath)
	require.NotContains(t, plan.Entries[0].RelPath, "..")
}

func TestBuildRecordsExcludesRelativeToSource(t *testing.T) {
	fs := afero.NewMemMapFs()
	require.NoError(t, fs.MkdirAll("/home/u/.codex/skills/.system", 0o755))

	m := manifest.ToolManifest{
		Tool: manifest.ToolCodex,
		Categories: []manifest.Category{
			{
				Name:     "skills",
				Paths:    []manifest.PathSpec{{Base: manifest.BaseConfig, Rel: "skills"}},
				Excludes: []string{"skills/.system"},
			},
		},
	}

	plan, err := planner.Build(m, fs, "/home/u/.codex", "/home/u/.codex")
	require.NoError(t, err)
	require.Len(t, plan.Entries, 1)
	require.Equal(t, []string{".system"}, plan.Entries[0].Excludes)
}
