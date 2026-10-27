# V2: grunt and setup TUI

## Grunt

Grunt is a thin host agent (Claude Haiku, Codex `gpt-6-luna`) that relays one task to `pi -p --no-session` and returns Pi's report. Pi uses its own default provider and model, currently Strata `qwen3.8-flash-next-q2_0` at medium effort with a 65,536-token context. The orchestrator sends tasks that fit a 64K-token context to grunt, larger implementation to builders, has a reviewer check grunt's code edits, and falls back to builders on `grunt unavailable`. A Claude orchestrator routed a failing-test fix through grunt, Pi fixed and committed it, and a reviewer passed it.

- [x] Verify grunt live on Codex: a `codex exec` smoke test relayed through `pi -p --no-session`, after the template stopped implying a Pi timeout flag.
- [ ] Verify grunt live on Cursor. Cursor wrappers inherit the session model, so they cost more than Claude's.
- [ ] Context fit is the orchestrator's judgment; Pi does not report overflow. Add a check if real tasks overflow.
- [ ] Pi runs with full tools and no edit limits. Restrict it with a Pi extension if read-only jobs need enforcement.

## Setup TUI

- [ ] Add a terminal picker for host and agents, show required dependencies, and confirm the selection before applying. Keep `install.py` usable without the picker.
- [ ] Configure grunt from discovered local harness/provider profiles, preselecting existing defaults. Persist harness/model/effort/context settings locally without putting credentials or endpoints in the packaged agents.
- [ ] Install selected agents and accepted dependencies only. Refresh owned definitions on rerun; preserve unrelated files and unselected existing agents. Cancellation before apply writes nothing.
- [ ] Test selection, dependencies, cancellation, reruns, unavailable harnesses and saved grunt settings driving a real job.

# Agent definition review

Compare each agent with community definitions (Anthropic's `claude-plugins-official` plugins, The Agency, the Claude Code subagent docs) and take only what earns its tokens. No persona preambles, since expert personas do not improve accuracy. Judge changes by using the agents, not by an eval suite.

- [x] builder: smallest-diff rule, narrower reading of an ambiguous brief, and a `Noticed` report section. `orchestrate` now carries Noticed into its Not done. From The Agency's `minimal-change-engineer`.
- [x] reviewer: pre-existing problems are at most a NOTE, and hidden failures (broad catch, logged-and-ignored error, masking fallback, mock outside tests) are a check. Skipped the 0-100 confidence score from Anthropic's feature-dev code-reviewer: reviewer already cites code and runs mutations.
- [ ] hall-monitor: `follow-the-rules` does not cover swallowed errors, and hall-monitor invents no standards, so that check went to reviewer. Open question: should hall-monitor report only what the diff introduced, or violations anywhere in the files it reads whole?
- [x] comment-janitor: a KEEP must also be true, so each claim is checked against the code (from Anthropic's `comment-analyzer`). Fixed the `# commenator` heading, set `model: sonnet` and `effort: medium`, and added `Grep` with the Read/Grep steer the other agents carry. Left the long trigger-phrase description alone.
- [ ] planner: cite the existing patterns found with file:line, as in Anthropic's `code-architect`.
- [ ] git-janitor, git-janitor-investigator, grunt: no community analog worth taking; review only if wanted.
- [ ] Frontmatter we do not use: `maxTurns`, `memory`, `permissionMode`, `omitClaudeMd`. Check the docs, then decide per agent.

Keep `scripts/build_agents.py --check` and `test_install.py` passing throughout.
