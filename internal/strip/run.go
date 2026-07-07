package strip

import (
	"fmt"

	"github.com/spf13/afero"

	"github.com/killallgit/killall-agents/internal/fsutil"
	"github.com/killallgit/killall-agents/internal/planner"
)

func Run(fs afero.Fs, plan planner.Plan) error {
	for _, e := range plan.Entries {
		if err := fsutil.DeletePath(fs, e.SourcePath, e.Excludes); err != nil {
			return fmt.Errorf("stripping %s: %w", e.SourcePath, err)
		}
	}
	return nil
}
