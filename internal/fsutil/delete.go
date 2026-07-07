package fsutil

import (
	"path/filepath"

	"github.com/spf13/afero"
)

func DeletePath(fs afero.Fs, path string, excludes []string) error {
	if len(excludes) == 0 {
		return fs.RemoveAll(path)
	}
	info, err := fs.Stat(path)
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return fs.Remove(path)
	}
	entries, err := afero.ReadDir(fs, path)
	if err != nil {
		return err
	}
	for _, e := range entries {
		if isExcluded(e.Name(), excludes) {
			continue
		}
		if err := fs.RemoveAll(filepath.Join(path, e.Name())); err != nil {
			return err
		}
	}
	return nil
}
