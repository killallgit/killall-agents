package restore

import (
	"fmt"
	"path/filepath"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/fsutil"
)

func Run(fs afero.Fs, m backup.Manifest, backupDir string) error {
	for _, e := range m.Entries {
		src := filepath.Join(backupDir, e.BackupPath)
		if err := fsutil.CopyPath(fs, src, e.SourcePath, nil); err != nil {
			return fmt.Errorf("restoring %s: %w", e.SourcePath, err)
		}
	}
	return nil
}
