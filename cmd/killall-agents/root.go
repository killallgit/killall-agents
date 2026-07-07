package main

import (
	"io"

	"github.com/spf13/afero"
	"github.com/spf13/cobra"

	"github.com/killallgit/killall-agents/internal/paths"
)

func NewRootCmd(fs afero.Fs, homeDir paths.HomeDirFunc, in io.Reader) *cobra.Command {
	root := &cobra.Command{
		Use:   "killall-agents",
		Short: "Backup and strip Claude Code / Codex customization",
	}
	root.AddCommand(NewInventoryCmd(fs, homeDir))
	return root
}
