# Extraction tasks

Spec: [agent-extraction](../docs/specs/agent-extraction.md). Approach: [plan](plan.md).

## 1. Portable legacy-upgrade fixtures

- [x] Export minimal snapshots for `d92095b` and `1fe222f4a6f3f3a9ddbcb52c188bbc8c6700747a`, recording provenance.
- [x] Update the fixture loader to use snapshots for those versions; retain meaningful upgrade/removal assertions and document comparison-ref semantics.
- [x] Verify all 49 renderer cases and 6 state tests pass; verify old upgrade cases in a checkout without source-history objects.

Dependencies: none. Likely edits: `evals/fixtures/make_repo.py`, two snapshot fixture files, `evals/README.md`, and `evals/compare_previous.py` only if needed. Scope: medium.

## 2. Working destination package

- [x] Connect the empty local destination to the real remote main, inspect existing work, and create a migration branch preserving published history.
- [x] Replace tracked Go prototype content with the inventoried agent catalog, complete setup package, research, native manifests and concise instructions/install docs. Include a copy of the full five-file `follow-the-rules` skill, retaining the original in the skills repo.
- [x] Verify imported definitions and generated output retain existing behavior and paths; parse host manifests and check their targets.

Dependencies: 1. Paths: destination prototype files, `agents/`, `skills/agent-setup/`, research, host manifests, README and AGENTS.md. Scope: mechanical replacement plus small packaging edits; commit those concerns separately.

## Checkpoint: destination exists independently

- [x] Source plugin still works unchanged.
- [x] Destination retains the old repository's history and contains no Go prototype runtime/configuration.
- [x] All 55 baseline checks pass in the destination; no copied credentials or machine-specific settings.
- [x] Review extraction and packaging before publishing.

## 3. Destination verification and CI

- [x] Replace the prototype workflow with the two Python checks; preserve the existing test count and assertions.
- [x] Verify legacy upgrade, rerun and removal preserve lane JSON in isolated existing-project fixtures, without source Git history or network access.
- [x] Native Claude validation and component discovery passed: two skills and four agents. Bundled rules and all relative links are present. Codex/Cursor manifests parse and skill paths resolve; their live installation and model-driven skill invocation were not run.

Dependencies: 2. Likely edits: `.github/workflows/ci.yml`, eval fixtures/tests only for migration gaps, README for observed install details. Scope: small/medium. Verify: both Python commands in the plan, manifest validation, installation smoke.

## Checkpoint: destination ready

- [x] Destination CI passes and migration evidence is recorded.
- [x] Review/land the agents package before removing source copies: killall-agents PR #1.

## 4. Retire source copies and publish migration

- [x] Remove only the moved plugin agents, setup package and research after the destination is available; source changes are in killall-skills PR #18.
- [x] Update source README, marketplace/plugin metadata and versions; document update/install order, dependency on remaining skills and unchanged state paths.
- [ ] Land source PR #18 after its checks clear; confirm final published package availability and that only one maintained agent copy remains. Remaining Python/eval metadata, shell syntax, links and native Claude component inventories passed; live agent workflow evals were not run.

Dependencies: 3 and published destination. Paths: moved source paths, README, three plugin manifests and two marketplace manifests. Scope: mechanical removal plus small documentation/metadata edits, committed separately. Verify: remaining documented skill checks, manifest parsing, cross-links and install migration.

## Checkpoint: extraction complete

- [ ] Existing generated projects refresh/remove without losing state.
- [ ] Ordinary skills remain usable without the agent plugin; dependent agents resolve skills when both plugins are installed.
- [ ] New agents and updated skills packages are published in dependency order, with all authorized extraction work included.
- [ ] Existing roles remain unchanged by extraction; grunt and the setup TUI are v2 tasks 5–6.

## V2 / 5. Add grunt with harness discovery

- [x] Discover and configure this installation's Pi defaults: Strata provider, `qwen3.8-flash-next-q2_0`, medium effort, 65,536 context metadata and the existing 8,192 output limit. Verify the remote model is advertised and a tool-free default-provider request returns `OK`. Server capacity is not independently reported.
- [ ] Define grunt and discover/select the harness per installation; use the bounded brief in the spec. Reuse the selected harness's existing provider/credential configuration and wire orchestrator dispatch without giving it implementation tools.
- [ ] Support checkout/status verification, safe fetch/fast-forward, exact test commands with timeouts, retrievable full logs and short structured pass/fail/blocked/cancelled/not-run reports. Route results to the existing lane-state writer and failures to the responsible builder/reviewer.
- [ ] Verify happy-path Git update/tests plus dirty/diverged/wrong checkout, failing tests, timeout and provider failure. Confirm no source/test edits or destructive Git actions, bounded returned output, and one real grunt job through the selected harness/model.

Dependencies: 4 for implementation; local harness preflight is complete independently. Likely edits in `killall-agents`: grunt definition, existing orchestration instructions, minimal dispatch adapter, focused adapter tests and README. Scope: medium; reuse the selected harness rather than adding a remote service. Verify: focused fixture-based checks, the unchanged 55 setup checks and a live grunt execution smoke. Credentials/endpoints remain local.

## V2 / 6. Basic setup TUI

- [ ] Add a small terminal picker for target host and selected agents, showing required dependencies and confirming the selection before apply. Preserve the noninteractive renderer for automation.
- [ ] Let users define custom grunt harness/model/effort/context settings using discovered local profiles, preselecting this machine's Pi/Strata defaults when available. Persist execution settings locally without copying credentials into templates.
- [ ] Test selected-only installation, dependency handling, cancellation without writes, rerun/state preservation, unavailable harnesses and saved grunt settings driving a verified job.

Dependencies: 5. Likely edits: setup entrypoint/renderer, setup instructions, focused selection/config tests and README. Scope: medium. Verify: interactive smoke plus focused fixture tests and all baseline setup checks. No TUI work in v1.
