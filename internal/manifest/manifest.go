package manifest

type Tool string

const (
	ToolClaude Tool = "claude"
	ToolCodex  Tool = "codex"
)

type Scope string

const (
	ScopeGlobal  Scope = "global"
	ScopeProject Scope = "project"
)

type BaseKind int

const (
	// BaseConfig resolves relative to the tool's config dir (~/.claude, ~/.codex).
	BaseConfig BaseKind = iota
	// BaseInstruction resolves relative to where instruction files live:
	// the config dir itself for global scope, its parent for project scope.
	BaseInstruction
)

type PathSpec struct {
	Base BaseKind
	Rel  string
}

type Category struct {
	Name     string
	Paths    []PathSpec
	Excludes []string
}

type ToolManifest struct {
	Tool       Tool
	Categories []Category
}
