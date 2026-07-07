package main

import (
	"os"

	"github.com/spf13/afero"
)

func main() {
	root := NewRootCmd(afero.NewOsFs(), os.UserHomeDir, os.Stdin)
	if err := root.Execute(); err != nil {
		os.Exit(1)
	}
}
