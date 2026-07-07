package backup

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/killallgit/killall-agents/internal/planner"
)

func Run(fs afero.Fs, plan planner.Plan, backupDir, tool, scope, root string, categories []string, createdAt string) (Manifest, error) {
	m := Manifest{
		Tool:       tool,
		Scope:      scope,
		Root:       root,
		Categories: categories,
		CreatedAt:  createdAt,
	}
	for _, e := range plan.Entries {
		dst := filepath.Join(backupDir, e.RelPath)
		if err := fsutil.CopyPath(fs, e.SourcePath, dst, e.Excludes); err != nil {
			return Manifest{}, fmt.Errorf("backing up %s: %w", e.SourcePath, err)
		}
		m.Entries = append(m.Entries, Entry{
			Category:   e.Category,
			SourcePath: e.SourcePath,
			BackupPath: e.RelPath,
		})
	}
	if err := WriteManifest(fs, backupDir, m); err != nil {
		return Manifest{}, err
	}
	return m, nil
}
