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
- [x] hall-monitor: now a fast pass for low-hanging violations of `follow-the-rules`, judged from the diff alone at low effort. Dropped the caller/callee walk, the sibling-pattern search, and the LSP trial: reviewer owns callers and tests. PATTERN rows are gone, so only a VIOLATION blocks. Watch whether anything it used to catch (convention drift) goes missing, and whether haiku is fast enough.
- [x] comment-janitor: a KEEP must also be true, so each claim is checked against the code (from Anthropic's `comment-analyzer`). Fixed the `# commenator` heading, set `model: sonnet` and `effort: medium`, and added `Grep` with the Read/Grep steer the other agents carry. Left the long trigger-phrase description alone.
- [x] planner: each lane names the existing code it follows as path:line, and the orchestrate brief carries it to the builder (from Anthropic's `code-architect`). Skipped its "pick one approach and commit": orchestrate stops to ask the user on design choices.
- [x] git-janitor, git-janitor-investigator, grunt: nothing to take from the community. git-janitor now sets `model: sonnet` and `effort: medium` instead of inheriting the session's model. The investigator and grunt were already minimal (haiku, narrow tools).
- [x] wrap-up: the end-of-work checklist is the `wrap-up` skill, with `skills/wrap-up/scripts/wrap_up.py` doing the mechanical steps and the `git-janitor` agent (Haiku, background) running it and reporting only a stop, a question, or the final table. The agent no longer depends on `killall-skills:git-janitor`. Subagents cannot ask the user, so the skill asks. Obsolete beads are closed, not deleted, since delete cannot be undone. Try it after the next PR lands; `killall-skills:end-session` overlaps it.
- [x] Tool audit: every agent's `tools` checked against what its prompt does. reviewer lost `Skill`, which it never uses. git-janitor inherited every tool, including all MCP servers (mail, chat, docs); it is now limited to Bash, Read, Grep, Glob, Skill and Agent (for the investigator). The rest already matched.
- [x] Frontmatter: `maxTurns` on grunt (5), git-janitor-investigator (20) and hall-monitor (15); `omitClaudeMd` on grunt and the investigator, which need no project instructions. Skipped `memory` (it grants write tools and writes runtime state into the repo) and `permissionMode: plan` (it would block the reviewer's gate run). The turn limits are guesses; adjust if an agent comes back partial.

Keep `scripts/build_agents.py --check` and `test_install.py` passing throughout.
