package planner

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/manifest"
)

func Build(m manifest.ToolManifest, fs afero.Fs, configRoot, instructionRoot string) (Plan, error) {
	var plan Plan
	for _, cat := range m.Categories {
		for _, ps := range cat.Paths {
			base := configRoot
			if ps.Base == manifest.BaseInstruction {
				base = instructionRoot
			}
			abs := filepath.Join(base, ps.Rel)

			exists, err := afero.Exists(fs, abs)
			if err != nil {
				return Plan{}, fmt.Errorf("checking %s: %w", abs, err)
			}
			if !exists {
				continue
			}

			rel, err := filepath.Rel(configRoot, abs)
			if err != nil {
				return Plan{}, fmt.Errorf("computing relative path for %s: %w", abs, err)
			}

			plan.Entries = append(plan.Entries, Entry{
				Category:   cat.Name,
				SourcePath: abs,
				RelPath:    filepath.ToSlash(rel),
				Excludes:   excludesFor(configRoot, abs, cat.Excludes),
			})
		}
	}
	return plan, nil
}

func excludesFor(configRoot, abs string, excludes []string) []string {
	var out []string
	for _, ex := range excludes {
		exAbs := filepath.Join(configRoot, ex)
		if exAbs == abs || strings.HasPrefix(exAbs, abs+string(filepath.Separator)) {
			exRel, err := filepath.Rel(abs, exAbs)
			if err != nil {
				continue
			}
			out = append(out, filepath.ToSlash(exRel))
		}
	}
	return out
}
