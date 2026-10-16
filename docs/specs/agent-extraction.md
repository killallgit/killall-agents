# Spec: extract the agent catalog

Status: v1 extraction scope established; implementation plan at `../../tasks/plan.md`. V1 moves the basic agents and bundles a copy of `follow-the-rules`. V2 adds a basic setup TUI, agent selection and custom grunt harness configuration.

## Objective

Give agent definitions and their setup tooling one owner outside `killall-skills`, so they can evolve independently. Preserve current behavior while moving them. Keep the existing shared templates and renderer; introduce no new agent framework.

Destination: `killallgit/killall-agents`. On 2026-10-16 the owner confirmed that its old Go backup/strip/restore CLI was an abandoned prototype and can be removed completely. Replace the tracked prototype contents in a normal commit, preserving repository history. The local empty Git directory must be connected to the existing remote history before starting a migration branch; do not initialize a competing history or force-push.

## Ownership

| Moves to the agent catalog | Stays in killall-skills |
| --- | --- |
| `agents/git-janitor.md`, `git-janitor-investigator.md`, `comment-janitor.md`, `hall-monitor.md` | Ordinary skills, including `git-janitor` and `follow-the-rules`, and their tests |
| Entire `skills/agent-setup/`: setup skill, four role templates, state guide, renderer, metadata, evals and fixtures | Existing plugin identity and packaging for the remaining skills |
| `docs/research/agent-factory-patterns.md` and relevant README guidance | A short migration/install link replacing moved documentation |
| Copy of the complete `skills/follow-the-rules/`, including its four referenced examples | Original `follow-the-rules` remains available in the skills plugin |

The plugin hall-monitor and generated lane hall-monitor are different definitions. Preserve both in their current locations and roles during extraction. Do not combine or rewrite them in this change.

## Compatibility contract

- Publish and verify the destination before removing the source definitions. Document the install/update sequence; do not silently fetch or execute a different repository.
- Keep generated file paths, role names, models, effort, tool restrictions, ownership markers and removal behavior unchanged initially.
- Keep `~/.config/killall-skills/agents/state/<encoded-main-checkout>/` unchanged, honoring valid `XDG_CONFIG_HOME`. Repository naming alone must not split active state or lose lane JSON.
- Preserve `killall-skills:git-janitor` references in the moved wrapper: it still delegates to the skill owned by `killall-skills`. Document that dependency and missing-skill behavior.
- Bundle the full `follow-the-rules` skill as the owner requested. Verify builders and hall-monitors resolve that bundled copy. This is an intentional copy, not a symlink or automatic cross-repository updater; retain its referenced files and record its source revision.
- The remaining git-janitor skill must still work without the agent plugin, using its existing inline fallback when the investigator is unavailable. Verify agent lookup when both plugins are installed.
- Retain current host support: Claude plugin agents; generated Claude/Codex/Cursor roles through setup. Do not claim moving Markdown makes it a native Codex or Cursor plugin agent.
- Update both repositories' READMEs, plugin/marketplace descriptions, install instructions and cross-links together. Determine version changes from the final packaging change; do not reset the remaining skills plugin's version.

## Structure and style

Keep `agents/`, `skills/agent-setup/` and the research note at their current relative paths in the destination. Add host packaging using the existing manifest shapes, adapted to `killall-agents`. Retire the prototype's Go source, dependencies, Taskfile, lint configuration, CI and obsolete docs/instructions; replace relevant documentation and packaging with catalog guidance. Give the new marketplace a distinct identity so it can coexist with the existing skills marketplace.

Reuse the Python standard-library renderer and existing Markdown/frontmatter and TOML formats. Host settings remain in shared role templates, for example:

```yaml
claude_model: sonnet
claude_effort: high
codex_model: gpt-6.1-sol
codex_effort: high
```

## Verification commands

Run from the destination root after extraction:

```sh
python3 skills/agent-setup/evals/run.py
python3 skills/agent-setup/evals/state.py
git diff --check
```

The baseline is 49 renderer cases and 6 state tests. These commands already exist in the source repository. No separate build or lint command is configured for this Python skill. The retired Go CLI's checks are replaced by checks for the extracted package.

## Testing strategy

Preserve the meaningful assertions, including legacy upgrades/removal, foreign-setting refusal, TOML preservation, shared worktree identity, path collisions, lane preservation and local excludes. Use temporary repositories and isolated configuration directories.

Migration risk: existing upgrade cases use `git archive` on historical `killall-skills` commits, including `d92095b` and `1fe222f4a6f3f3a9ddbcb52c188bbc8c6700747a`. A plain copy into a fresh repository breaks those tests. Prefer checked-in minimal historical skill snapshots with provenance and update the fixture loader to read them; preserve coverage and keep routine tests independent of network access or a sibling clone. The metadata comparison command must document which repository's refs it accepts after extraction.

Verify an existing generated project can be refreshed and removed by the extracted setup without changing lane JSON. Smoke-check installation, role discovery and skill resolution for supported hosts; report unavailable hosts explicitly.

## Boundaries

- Always: preserve existing work, active state and foreign settings; keep one maintained source for each agent definition; verify the destination before source removal. The requested `follow-the-rules` copy is an explicit exception for skills.
- Authorized: remove the abandoned Go prototype's tracked contents as part of replacing it with the catalog. Preserve any newly discovered unrelated or unpublished work.
- Resolve later: the requested agent tweaks and the Pi/Strata adapter, each separately from extraction.
- Never: rewrite published Git history, copy machine-specific configuration or credentials, or weaken upgrade tests to make the move pass.

## Success criteria

1. The destination owns all four plugin agents, the complete setup package and a full `follow-the-rules` copy; the Go prototype is retired, its Git history remains, and ordinary skills remain independently usable from `killall-skills`.
2. All 55 baseline checks pass in an independent destination checkout, with legacy-upgrade coverage and no dependency on source-repository history or network access.
3. Existing generated projects retain their paths and lane state through refresh/removal. Install instructions and cross-plugin skill lookup match observed host behavior.

## Grunt: routine Git and test execution

Add `grunt` in v2 as a small-context execution role. Discover and configure its available harness per installation rather than assuming everyone uses Pi. The default on this installation is local Pi calling a remote Strata model: provider `strata`, model `qwen3.8-flash-next-q2_0`, medium effort, and a user-specified 66k window represented locally as 65,536 tokens. Pi executes tools in its local checkout; a remote model endpoint does not imply remote Git, tests or files. Keep existing builder/reviewer roles for implementation and diagnosis.

Local preflight on 2026-10-16 found Pi 0.85.1 and the existing Strata profile. Pi defaults were configured for this model and medium effort; a tool-free request through those defaults returned `OK`. The authenticated server advertises the model ID but no context capacity. The 65,536 context setting follows the owner's supplied window; retain the existing 8,192 output-token allowance and keep input, instructions, tools and log excerpts below the remaining budget. No endpoint, credential or machine-specific path belongs in the public package.

| Job | Contract |
| --- | --- |
| Update Git | Inspect status, fetch the brief's remote, and fast-forward the named branch when clean. Report dirty files, divergence, conflicts or unexpected checkout identity as blocked. No automatic stash, reset, rebase, cleanup, commit, push or merge of other branches. |
| Run tests | Run the exact supplied commands in the assigned checkout, with the supplied timeout. Capture each exit code, counts when available, and complete logs. Run once per request; report a failed prerequisite as blocked and skipped tests as not run. |
| Report failures | Return a short result: job/repository/branch, before-and-after commit, Git actions, command, exit code, test summary, relevant failure excerpt and retrievable full-log reference. Distinguish pass, fail, blocked, cancelled and not run. Report observed errors without broad root-cause investigation or code fixes. |

The brief contains only job ID, execution target, absolute checkout, expected branch/commit, allowed Git update, test commands, timeout and log destination. Read required repository instructions plus status and relevant output; do not load the whole spec, repository or lane history. Stream full logs to an artifact and return a bounded excerpt rather than filling agent context with passing output. Missing necessary context is a handoff, not permission to explore the whole codebase.

Grunt does not edit source/tests, adjust test expectations, decide integration, or delegate. Its intended tools are checkout/status inspection, the permitted Git operations, supplied test execution and log retrieval. Verify what Strata/Pi can enforce; broad shell access alone does not enforce this role boundary.

The orchestrator delegates routine execution to grunt and sends its failure report to the responsible builder/reviewer. Existing independent reviewer checks still apply. Return results to the existing designated lane-state writer; do not create a second tracker or assume local and remote home-directory state folders share a filesystem.

Acceptance: a clean checkout updates and runs its tests; dirty/diverged/wrong checkouts stop without discarding work; a failing test returns a concise failure plus full logs without code changes; a timeout or provider failure is never a passing result. Test dispatch/report handling with isolated fixtures first, then verify a real grunt job using the selected harness and provider. Preserve all 55 extraction checks and add focused checks for these new behaviors.

Pi documents a headless JSONL control interface in its [official RPC reference](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/docs/rpc.md). Reuse the installed Pi profile and credential resolver; no Strata worker-launch service is needed for this deployment. Discover another installation's harness command, provider/model, effort, advertised context and available execution/reporting controls before enabling grunt. Report unsupported or unavailable configurations rather than silently changing model, harness or execution machine.

## V2: basic setup TUI

After v1 is moved and verified, make agent setup a minimal terminal picker: choose the host and agents to install, then review the resulting selection before writing. Show required role dependencies so users cannot unknowingly install an orchestrator with missing workers. Keep existing noninteractive renderer commands working for automation.

Offer a custom grunt configuration in the same flow. Discover existing harnesses and provider profiles first; preselect the user's configured default, show its model/effort/context, and allow a different supported harness or model. For this machine, select the Pi/Strata defaults above. Store machine-specific execution configuration locally, without embedding credentials or endpoint addresses in shared agent templates.

Acceptance: only selected agents plus explicitly accepted dependencies are installed; selection changes preserve unrelated files and active lane state; rerunning setup refreshes selected owned definitions without deleting unselected existing agents implicitly; cancellation before apply writes nothing. Custom grunt settings persist locally and drive an observed test job. Test selection, dependency handling, reruns, cancellation, missing harnesses and custom configuration. Use a small terminal interface; no dashboard or additional remote service.

## Open questions

- No further clarification blocks v1. Discover other users' harness capabilities during v2 setup; unsupported integrations can be identified there.
- Further agent tweaks beyond grunt and the setup TUI remain separate changes once named.
