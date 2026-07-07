package manifest_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/stretchr/testify/require"
)

func TestClaudeHasCoreCategories(t *testing.T) {
	m := manifest.Claude()
	require.Equal(t, manifest.ToolClaude, m.Tool)
	require.ElementsMatch(t,
		[]string{"skills", "agents", "commands", "hooks", "rules", "plugins", "mcp", "settings", "memory"},
		categoryNames(m),
	)
}

func TestCodexHasNoAgentsOrCommands(t *testing.T) {
	names := categoryNames(manifest.Codex())
	require.NotContains(t, names, "agents")
	require.NotContains(t, names, "commands")
}

func TestCodexSkillsExcludesSystemDir(t *testing.T) {
	cat := findCategory(manifest.Codex(), "skills")
	require.Contains(t, cat.Excludes, "skills/.system")
}

func TestLookupUnknownTool(t *testing.T) {
	_, err := manifest.Lookup(manifest.Tool("bogus"))
	require.Error(t, err)
}

func TestLookupKnownTools(t *testing.T) {
	m, err := manifest.Lookup(manifest.ToolClaude)
	require.NoError(t, err)
	require.Equal(t, manifest.ToolClaude, m.Tool)

	m, err = manifest.Lookup(manifest.ToolCodex)
	require.NoError(t, err)
	require.Equal(t, manifest.ToolCodex, m.Tool)
}

func categoryNames(m manifest.ToolManifest) []string {
	out := make([]string, len(m.Categories))
	for i, c := range m.Categories {
		out[i] = c.Name
	}
	return out
}

func findCategory(m manifest.ToolManifest, name string) manifest.Category {
	for _, c := range m.Categories {
		if c.Name == name {
			return c
		}
	}
	return manifest.Category{}
}
