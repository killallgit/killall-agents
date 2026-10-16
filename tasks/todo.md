# V2: grunt and setup TUI

## Grunt

- [ ] Discover installed harnesses and reuse the selected harness's provider and credential configuration. Keep machine settings local. The initial target is local Pi calling a remote Strata model; Git, files and tests remain local to Pi.
- [ ] Add a small-context grunt role for Git updates, exact test execution and concise failure reports. Keep implementation and diagnosis with builders/reviewers; the orchestrator only dispatches work.
- [ ] Pass a bounded brief: job ID, execution target, absolute checkout, expected branch/commit, allowed Git update, test commands, timeout and log destination. Read repository instructions, status and relevant output rather than broad repository context.
- [ ] Verify checkout identity and cleanliness before updating. Fetch only the named remote and fast-forward only the named branch. Stop on dirty files, divergence, conflicts or unexpected identity; preserve all existing work. Exclude stash, reset, rebase, cleanup, commit, push and unrelated branch merges.
- [ ] Run supplied commands once with timeouts. Stream full logs to artifacts and return a bounded excerpt, exit codes, available test counts, before/after commit and log reference. Distinguish pass, fail, blocked, cancelled and not run. A failed prerequisite blocks dependent tests.
- [ ] Route results through the existing lane-state writer and failures to the responsible builder/reviewer. Keep independent reviewer checks. Grunt cannot edit source/tests, adjust expectations or delegate; verify the selected harness can enforce those limits.
- [ ] Test clean updates, dirty/diverged/wrong checkouts, failing tests, timeouts and provider failures. Confirm bounded reports, retrievable logs and no source/test edits; verify one real job through the selected harness.

Pi provides a [JSONL RPC interface](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md). Discover harness command, provider/model, effort, context capacity and execution controls before enabling grunt; report unsupported configurations instead of silently substituting them. The configured remote model is `qwen3.8-flash-next-q2_0`, medium effort, with a user-supplied 65,536-token context and 8,192-token output limit. A tool-free request passed; the server does not advertise context capacity. Full grunt execution remains to be verified.

## Setup TUI

Depends on a working grunt adapter.

- [ ] Add a terminal picker for host and agents, show required dependencies, and confirm the selection before applying. Preserve the noninteractive renderer.
- [ ] Configure grunt from discovered local harness/provider profiles, preselecting existing defaults. Persist harness/model/effort/context settings locally without putting credentials or endpoints in shared templates.
- [ ] Install selected agents and accepted dependencies only. Refresh owned definitions on rerun; preserve unrelated files, unselected existing agents and lane state. Cancellation before apply writes nothing.
- [ ] Test selection, dependencies, cancellation, reruns, unavailable harnesses and saved grunt settings driving a real job.

Keep the existing 49 renderer cases and 6 state checks passing throughout.
