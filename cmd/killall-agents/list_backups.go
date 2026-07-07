package main

import (
	"fmt"
	"os"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
)

func NewListBackupsCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag string

	cmd := &cobra.Command{
		Use:   "list-backups",
		Short: "List available backups",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				configRoot, _, err := paths.ConfigRoot(t, manifest.ScopeGlobal, "", homeDir)
				if err != nil {
					return err
				}
				entries, err := afero.ReadDir(fs, paths.BackupRoot(configRoot))
				if err != nil {
					if os.IsNotExist(err) {
						continue
					}
					return err
				}
				for _, e := range entries {
					_, _ = fmt.Fprintf(cmd.OutOrStdout(), "%s\t%s\n", t, e.Name())
				}
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	return cmd
}
