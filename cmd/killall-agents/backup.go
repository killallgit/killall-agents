package main

import (
	"fmt"
	"io"
	"path/filepath"
	"strings"
	"time"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
)

func NewBackupCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, projectFlag, categoriesFlag string

	cmd := &cobra.Command{
		Use:   "backup",
		Short: "Back up customization without stripping it",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				if _, _, err := runBackup(cmd.OutOrStdout(), fs, homeDir, t, projectFlag, categoriesFlag); err != nil {
					return err
				}
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	cmd.Flags().StringVar(&categoriesFlag, "categories", "", "comma-separated category filter (default: all)")
	return cmd
}

func runBackup(w io.Writer, fs afero.Fs, homeDir paths.HomeDirFunc, t manifest.Tool, projectFlag, categoriesFlag string) (backup.Manifest, string, error) {
	m, err := manifest.Lookup(t)
	if err != nil {
		return backup.Manifest{}, "", err
	}
	if categoriesFlag != "" {
		m = filterCategories(m, strings.Split(categoriesFlag, ","))
	}

	scope := manifest.ScopeGlobal
	if projectFlag != "" {
		scope = manifest.ScopeProject
	}

	configRoot, instructionRoot, err := paths.ConfigRoot(t, scope, projectFlag, homeDir)
	if err != nil {
		return backup.Manifest{}, "", err
	}

	plan, err := planner.Build(m, fs, configRoot, instructionRoot)
	if err != nil {
		return backup.Manifest{}, "", err
	}

	stamp := time.Now().UTC().Format("20060102-150405")
	backupDir := filepath.Join(paths.BackupRoot(configRoot), fmt.Sprintf("%s-%s", t, stamp))

	man, err := backup.Run(fs, plan, backupDir, string(t), string(scope), configRoot, categoryNames(m), time.Now().UTC().Format(time.RFC3339))
	if err != nil {
		return backup.Manifest{}, "", err
	}

	_, _ = fmt.Fprintf(w, "backed up %s -> %s\n", t, backupDir)
	return man, backupDir, nil
}

func filterCategories(m manifest.ToolManifest, names []string) manifest.ToolManifest {
	want := map[string]bool{}
	for _, n := range names {
		want[strings.TrimSpace(n)] = true
	}
	var kept []manifest.Category
	for _, c := range m.Categories {
		if want[c.Name] {
			kept = append(kept, c)
		}
	}
	return manifest.ToolManifest{Tool: m.Tool, Categories: kept}
}

func categoryNames(m manifest.ToolManifest) []string {
	names := make([]string, len(m.Categories))
	for i, c := range m.Categories {
		names[i] = c.Name
	}
	return names
}
