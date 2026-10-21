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

Keep `scripts/build_agents.py --check` and `test_install.py` passing throughout.
