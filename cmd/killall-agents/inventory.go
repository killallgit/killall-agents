package main

import (
	"fmt"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
)

func NewInventoryCmd(fs afero.Fs, homeDir paths.HomeDirFunc) *cobra.Command {
	var toolFlag, projectFlag string

	cmd := &cobra.Command{
		Use:   "inventory",
		Short: "Show installed customization for a tool",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			for _, t := range tools {
				m, err := manifest.Lookup(t)
				if err != nil {
					return err
				}
				scope := manifest.ScopeGlobal
				if projectFlag != "" {
					scope = manifest.ScopeProject
				}
				configRoot, instructionRoot, err := paths.ConfigRoot(t, scope, projectFlag, homeDir)
				if err != nil {
					return err
				}
				plan, err := planner.Build(m, fs, configRoot, instructionRoot)
				if err != nil {
					return err
				}
				fmt.Fprintf(cmd.OutOrStdout(), "== %s (%s) ==\n", t, configRoot)
				fmt.Fprint(cmd.OutOrStdout(), inventory.Format(plan))
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	return cmd
}
