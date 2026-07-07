package main

import (
	"testing"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/stretchr/testify/require"
)

func TestResolveToolsAll(t *testing.T) {
	tools, err := resolveTools("all")
	require.NoError(t, err)
	require.ElementsMatch(t, []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, tools)
}

func TestResolveToolsEmptyDefaultsToAll(t *testing.T) {
	tools, err := resolveTools("")
	require.NoError(t, err)
	require.ElementsMatch(t, []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, tools)
}

func TestResolveToolsSingle(t *testing.T) {
	tools, err := resolveTools("codex")
	require.NoError(t, err)
	require.Equal(t, []manifest.Tool{manifest.ToolCodex}, tools)
}

func TestResolveToolsUnknown(t *testing.T) {
	_, err := resolveTools("bogus")
	require.Error(t, err)
}
