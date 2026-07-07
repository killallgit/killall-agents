package manifest

import "fmt"

func Lookup(tool Tool) (ToolManifest, error) {
	switch tool {
	case ToolClaude:
		return Claude(), nil
	case ToolCodex:
		return Codex(), nil
	default:
		return ToolManifest{}, fmt.Errorf("unknown tool %q", tool)
	}
}
