package manifest

func Codex() ToolManifest {
	return ToolManifest{
		Tool: ToolCodex,
		Categories: []Category{
			{
				Name:     "skills",
				Paths:    []PathSpec{{Base: BaseConfig, Rel: "skills"}},
				Excludes: []string{"skills/.system"},
			},
			{Name: "rules", Paths: []PathSpec{{Base: BaseConfig, Rel: "rules"}}},
			{Name: "hooks", Paths: []PathSpec{{Base: BaseConfig, Rel: "hooks.json"}}},
			{Name: "plugins", Paths: []PathSpec{{Base: BaseConfig, Rel: "plugins"}}},
			{Name: "settings", Paths: []PathSpec{{Base: BaseConfig, Rel: "config.toml"}}},
			{Name: "memory", Paths: []PathSpec{{Base: BaseInstruction, Rel: "AGENTS.md"}}},
		},
	}
}
