package paths

import (
	"fmt"
	"path/filepath"

	"github.com/killallgit/killall-agents/internal/manifest"
)

type HomeDirFunc func() (string, error)

func ConfigRoot(tool manifest.Tool, scope manifest.Scope, projectPath string, homeDir HomeDirFunc) (configRoot, instructionRoot string, err error) {
	dirName := "." + string(tool)

	if scope == manifest.ScopeProject {
		if projectPath == "" {
			return "", "", fmt.Errorf("project path required for project scope")
		}
		return filepath.Join(projectPath, dirName), projectPath, nil
	}

	home, err := homeDir()
	if err != nil {
		return "", "", err
	}
	configRoot = filepath.Join(home, dirName)
	return configRoot, configRoot, nil
}

func BackupRoot(configRoot string) string {
	return filepath.Join(configRoot, "killall-agents-backups")
}
