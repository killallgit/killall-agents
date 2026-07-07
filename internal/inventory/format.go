package inventory

import (
	"fmt"
	"strings"

	"github.com/killallgit/killall-agents/internal/planner"
)

func Format(plan planner.Plan) string {
	if len(plan.Entries) == 0 {
		return "No matching customization found.\n"
	}
	var b strings.Builder
	for _, e := range plan.Entries {
		fmt.Fprintf(&b, "%-12s %s\n", e.Category, e.SourcePath)
		for _, ex := range e.Excludes {
			fmt.Fprintf(&b, "%-12s   (protected, will not touch: %s)\n", "", ex)
		}
	}
	return b.String()
}
