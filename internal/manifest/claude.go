package manifest

func Claude() ToolManifest {
	return ToolManifest{
		Tool: ToolClaude,
		Categories: []Category{
			{Name: "skills", Paths: []PathSpec{{Base: BaseConfig, Rel: "skills"}}},
			{Name: "agents", Paths: []PathSpec{{Base: BaseConfig, Rel: "agents"}}},
			{Name: "commands", Paths: []PathSpec{{Base: BaseConfig, Rel: "commands"}}},
			{Name: "hooks", Paths: []PathSpec{{Base: BaseConfig, Rel: "hooks"}}},
			{Name: "rules", Paths: []PathSpec{{Base: BaseConfig, Rel: "rules"}}},
			{Name: "plugins", Paths: []PathSpec{{Base: BaseConfig, Rel: "plugins"}}},
			{Name: "mcp", Paths: []PathSpec{{Base: BaseInstruction, Rel: ".mcp.json"}}},
			{Name: "settings", Paths: []PathSpec{
				{Base: BaseConfig, Rel: "settings.json"},
				{Base: BaseConfig, Rel: "settings.local.json"},
			}},
			{Name: "memory", Paths: []PathSpec{{Base: BaseInstruction, Rel: "CLAUDE.md"}}},
		},
	}
}
