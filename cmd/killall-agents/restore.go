package main

import (
	"fmt"
	"path/filepath"
	"strings"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/backup"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/restore"
)

func NewRestoreCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, fromFlag string

	cmd := &cobra.Command{
		Use:   "restore",
		Short: "Restore customization from a backup",
		RunE: func(cmd *cobra.Command, args []string) error {
			if toolFlag == "" || toolFlag == "all" {
				return fmt.Errorf("--tool must be claude or codex")
			}
			t := manifest.Tool(toolFlag)
			if _, err := manifest.Lookup(t); err != nil {
				return err
			}
			if fromFlag == "" {
				return fmt.Errorf("--from is required")
			}

			backupDir := fromFlag
			if !strings.ContainsRune(backupDir, filepath.Separator) {
				configRoot, _, err := paths.ConfigRoot(t, manifest.ScopeGlobal, "", homeDir)
				if err != nil {
					return err
				}
				backupDir = filepath.Join(paths.BackupRoot(configRoot), fromFlag)
			}

			m, err := backup.ReadManifest(fs, backupDir)
			if err != nil {
				return err
			}
			if err := restore.Run(fs, m, backupDir); err != nil {
				return err
			}
			fmt.Fprintf(cmd.OutOrStdout(), "restored %s from %s\n", t, backupDir)
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "", "claude|codex (required)")
	cmd.Flags().StringVar(&fromFlag, "from", "", "backup id or path (required)")
	return cmd
}
