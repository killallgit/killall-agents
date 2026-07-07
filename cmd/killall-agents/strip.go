package main

import (
	"bufio"
	"fmt"
	"io"
	"strings"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/inventory"
	"github.com/killallgit/killall-agents/internal/manifest"
	"github.com/killallgit/killall-agents/internal/paths"
	"github.com/killallgit/killall-agents/internal/planner"
	"github.com/killallgit/killall-agents/internal/strip"
)

func NewStripCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command {
	var toolFlag, projectFlag, categoriesFlag string
	var dryRun, yes bool

	cmd := &cobra.Command{
		Use:   "strip",
		Short: "Back up then remove customization",
		RunE: func(cmd *cobra.Command, args []string) error {
			tools, err := resolveTools(toolFlag)
			if err != nil {
				return err
			}
			reader := bufio.NewReader(in)
			for _, t := range tools {
				m, err := manifest.Lookup(t)
				if err != nil {
					return err
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
					return err
				}

				plan, err := planner.Build(m, fs, configRoot, instructionRoot)
				if err != nil {
					return err
				}

				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "== plan for %s (%s) ==\n", t, configRoot)
				_, _ = fmt.Fprint(cmd.OutOrStdout(), inventory.Format(plan))

				if len(plan.Entries) == 0 || dryRun {
					continue
				}
				if !yes && !confirm(cmd.OutOrStdout(), reader) {
					_, _ = fmt.Fprintln(cmd.OutOrStdout(), "aborted")
					continue
				}

				if _, _, err := runBackup(cmd.OutOrStdout(), fs, homeDir, t, projectFlag, categoriesFlag); err != nil {
					return err
				}
				if err := strip.Run(fs, plan); err != nil {
					return err
				}
				_, _ = fmt.Fprintf(cmd.OutOrStdout(), "stripped %s\n", t)
			}
			return nil
		},
	}
	cmd.Flags().StringVar(&toolFlag, "tool", "all", "claude|codex|all")
	cmd.Flags().StringVar(&projectFlag, "project", "", "project path (default: global)")
	cmd.Flags().StringVar(&categoriesFlag, "categories", "", "comma-separated category filter (default: all)")
	cmd.Flags().BoolVar(&dryRun, "dry-run", false, "print plan only, no writes")
	cmd.Flags().BoolVar(&yes, "yes", false, "skip confirmation prompt")
	return cmd
}

func confirm(w io.Writer, r *bufio.Reader) bool {
	_, _ = fmt.Fprint(w, "proceed with backup + strip? [y/N]: ")
	line, _ := r.ReadString('\n')
	line = strings.TrimSpace(strings.ToLower(line))
	return line == "y" || line == "yes"
}
