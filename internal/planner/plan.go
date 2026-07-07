package planner

type Entry struct {
	Category   string
	SourcePath string
	RelPath    string
	Excludes   []string
}

type Plan struct {
	Entries []Entry
}
