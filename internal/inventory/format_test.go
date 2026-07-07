package inventory_test

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/stretchr/testify/require"
)

func TestFormatListsEntriesByCategory(t *testing.T) {
	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.claude/skills"},
	}}
	out := inventory.Format(plan)
	require.Contains(t, out, "skills")
	require.Contains(t, out, "/home/u/.claude/skills")
}

func TestFormatNotesProtectedExcludes(t *testing.T) {
	plan := planner.Plan{Entries: []planner.Entry{
		{Category: "skills", SourcePath: "/home/u/.codex/skills", Excludes: []string{".system"}},
	}}
	out := inventory.Format(plan)
	require.Contains(t, out, "protected")
	require.Contains(t, out, ".system")
}

func TestFormatEmptyPlan(t *testing.T) {
	out := inventory.Format(planner.Plan{})
	require.Contains(t, out, "No matching customization found")
}
