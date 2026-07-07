package main

import (
	"fmt"

	"github.com/killallgit/killall-agents/internal/manifest"
)

func resolveTools(flag string) ([]manifest.Tool, error) {
	switch flag {
	case "", "all":
		return []manifest.Tool{manifest.ToolClaude, manifest.ToolCodex}, nil
	case "claude":
		return []manifest.Tool{manifest.ToolClaude}, nil
	case "codex":
		return []manifest.Tool{manifest.ToolCodex}, nil
	default:
		return nil, fmt.Errorf("unknown --tool %q", flag)
	}
}
