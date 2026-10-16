# Plan: extract killall-agents

Scope: [agent-extraction spec](../docs/specs/agent-extraction.md). Tasks and checkpoints are tracked in [todo.md](todo.md). V1 extraction is implemented on the migration branch; publication and source retirement are pending. V2 remains planned.

## Decisions

- Replace the abandoned `killallgit/killall-agents` Go CLI. Preserve its Git history with ordinary migration commits; no force-push or separate replacement repository.
- Move the four plugin agents and all of `skills/agent-setup/`, including its renderer, templates, tests and fixtures. Keep ordinary skills here. Move the factory research with the agents.
- Copy the complete `follow-the-rules` skill and its four reference examples into the agents package; retain the original in the skills package. Record provenance, without a new synchronization mechanism.
- V1 extracts the existing agents with unchanged models, tools and workflow. V2 adds grunt plus a basic setup TUI for agent selection and custom grunt configuration. Grunt handles routine Git updates, exact tests and concise failure reports, with no code fixes or broad diagnosis.
- Preserve existing generated paths, ownership markers and global state location. The repo rename is not a state migration.
- Keep the wrapper's dependency on `killall-skills:git-janitor` explicit. Builders and hall-monitors use the bundled `follow-the-rules` copy. Use the existing inline investigator fallback when the agent plugin is absent; verify namespaced lookup when both plugins are present.
- Reuse the existing static host manifests and Python renderer. Use a distinct agents marketplace identity to avoid colliding with the installed skills marketplace.
- Proposed releases: `killall-agents` catalog starts at `1.0.0`; removing shipped agents/setup from `killall-skills` warrants `4.0.0` with an explicit installation migration note. Verify existing tags before choosing final versions.

## Dependency order

Portable upgrade fixtures → destination replacement → independent destination verification → publish agents → remove source copies → verify skills and installation migration.

V2: discover/configure the execution harness → verify grunt → add the basic TUI for agent selection and custom grunt settings. V2 does not block extraction.

The source plugin stays functional until the new package is available. The brief overlap is a migration window, not two maintained implementations. Install the agents plugin only after updating the skills plugin to avoid duplicate agent definitions.

## Implementation slices

1. **Make legacy upgrades portable.** Export the two historical skill snapshots used by existing cases, with their original commit IDs; load them as local fixtures. Keep arbitrary current-repository ref comparisons supported where applicable. Prove the existing upgrade assertions still run without historical source Git objects.
2. **Replace the prototype with the working catalog.** Start a branch from the remote's real main, preserve unrelated work, retire tracked prototype content, and copy the inventoried agent package plus the full `follow-the-rules` skill. Add native packaging, a short README and replacement agent instructions. Keep agent definitions byte-for-byte equivalent except necessary packaging references.
3. **Verify the new package independently.** Run all 55 checks in a separate checkout, confirm no source-history/network dependency, exercise refresh/removal against an old generated project with lane JSON, and verify manifest paths and supported host discovery. Replace obsolete Go CI with the two existing Python suites; disclose unavailable live hosts.
4. **Publish the destination, then retire source copies.** Open coordinated PRs and land the verified agents package first. Remove the catalog/setup/research copies here, update manifests and README, document the two-plugin dependency and upgrade order, and bump release metadata consistently. Verify remaining skill suites and cross-links before landing the source removal.

These are four coherent migration slices. The exact-copy import and tracked prototype retirement necessarily touch more than five paths; keep those mechanical changes separate from fixture-loader and packaging edits. Splitting each copied file into an individual task would leave unusable intermediate packages without reducing implementation risk.

## Verification

In the new repository:

```sh
python3 skills/agent-setup/evals/run.py
python3 skills/agent-setup/evals/state.py
git diff --check
```

Require 49 renderer cases and 6 state tests, including legacy upgrades, ownership conflicts, TOML preservation, worktree identity and lane preservation. Parse every host manifest and confirm all referenced paths exist. Installation checks must distinguish native plugin agents from generated project agents.

For source removal, discover and run the remaining skills' documented checks rather than inventing a build command. Verify `git-janitor` can still run without the optional investigator. Check the source diff contains only the agreed extraction, metadata and migration docs.

## Risks

| Risk | Mitigation |
| --- | --- |
| Empty local destination has no relationship to remote history | Fetch existing main and branch from it; inspect local and remote work before mutations |
| Legacy evals depend on old source commits | Check in minimal historical snapshots with provenance; test offline independence |
| Duplicate agents or unresolved skills during transition | Publish first, document upgrade/install order, verify cross-plugin lookup |
| Active state disappears after rename | Keep the current state path and markers unchanged; compare lane bytes after refresh/removal |
| Old Go workflows govern the new catalog | Retire prototype-specific instructions and checks together; run the actual Python suites |

Execution is sequential across repositories. Host smoke checks may run independently after the destination is stable. No new runtime, shared database, symlinks or remote worker service is needed for extraction.

## V2: grunt and setup TUI

Tasks 5–6 in `todo.md` implement the role contract and TUI described in the spec. Discover an existing harness/provider configuration per installation instead of assuming Pi everywhere. Here, Pi runs locally and calls Strata remotely using `qwen3.8-flash-next-q2_0`, medium effort and the user-specified 66k context. This default is configured and a tool-free live request passed; the full grunt execution workflow remains unimplemented.

Stream logs to artifacts, return concise results and hand failures to the existing builder/reviewer. The terminal picker chooses installed agents and lets the user configure grunt's harness/model, with visible dependencies and a final apply step. Preserve the noninteractive renderer. No separate state store, dashboard or general-purpose remote agent framework.
