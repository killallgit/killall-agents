package backup

import (
	"encoding/json"
	"path/filepath"

	"github.com/spf13/afero"
)

type Entry struct {
	Category   string `json:"category"`
	SourcePath string `json:"sourcePath"`
	BackupPath string `json:"backupPath"`
}

type Manifest struct {
	Tool       string   `json:"tool"`
	Scope      string   `json:"scope"`
	Root       string   `json:"root"`
	Categories []string `json:"categories"`
	CreatedAt  string   `json:"createdAt"`
	Entries    []Entry  `json:"entries"`
}

const manifestFileName = "manifest.json"

func WriteManifest(fs afero.Fs, dir string, m Manifest) error {
	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	return afero.WriteFile(fs, filepath.Join(dir, manifestFileName), data, 0o644)
}

func ReadManifest(fs afero.Fs, dir string) (Manifest, error) {
	data, err := afero.ReadFile(fs, filepath.Join(dir, manifestFileName))
	if err != nil {
		return Manifest{}, err
	}
	var m Manifest
	if err := json.Unmarshal(data, &m); err != nil {
		return Manifest{}, err
	}
	return m, nil
}
