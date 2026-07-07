package fsutil

import (
	"os"
	"path/filepath"

	"github.com/spf13/afero"
)

func CopyPath(fs afero.Fs, src, dst string, excludes []string) error {
	info, err := fs.Stat(src)
	if err != nil {
		return err
	}
	if !info.IsDir() {
		return copyFile(fs, src, dst)
	}
	return afero.Walk(fs, src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, err := filepath.Rel(src, path)
		if err != nil {
			return err
		}
		if isExcluded(rel, excludes) {
			if info.IsDir() {
				return filepath.SkipDir
			}
			return nil
		}
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return fs.MkdirAll(target, info.Mode())
		}
		return copyFile(fs, path, target)
	})
}

func copyFile(fs afero.Fs, src, dst string) error {
	data, err := afero.ReadFile(fs, src)
	if err != nil {
		return err
	}
	if err := fs.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}
	return afero.WriteFile(fs, dst, data, 0o644)
}
