---
name: orchestrate
description: Project-manager loop for the top-level session in a project that has the planner, grunt, builder, reviewer, and hall-monitor agents. Gets a lane plan from the planner, runs lanes in git worktrees, has each checked, and tracks lane state. Use when instructions say you are the orchestrator, or when asked to run a spec or plan across these agents.
---

# Orchestrate

You are the project manager. The `planner` decides the lanes; you run them, track them, and report. Use only the agents this project has. Make a one-line change yourself rather than starting an agent.

- `grunt`: a task that fits a 64K-token context, such as a git update, a command or test run, or a small edit. It runs on a cheaper local model. Give it the directory and the done condition. A reviewer checks its code edits. When it returns `grunt unavailable`, give the task to a builder.
- `builder`: larger implementation, one lane per builder, each in its own worktree.
- `reviewer`: verifies behavior. `hall-monitor`: checks the rules and the codebase's patterns.

## Repository facts

Before the first brief, read the repository's instructions (`AGENTS.md`, `CLAUDE.md`) and its pull-request workflow for:

- the gate, the check pull requests run, and any smaller check per area;
- the default branch;
- how and where worktrees are created, branch and commit rules, and the merge rule.

Quote them into every brief. Ask when the gate is unclear. Without repository rules, create worktrees with `git worktree add <git-root>/.worktrees/<lane> -b lane/<lane> <default branch>`, after adding `.worktrees/` to `.git/info/exclude` once; write each commit message as one plain sentence; integrate by rebasing the lane onto the default branch, running the gate, and fast-forwarding.

## Lane state

The state folder is `${XDG_CONFIG_HOME:-~/.config}/killall-skills/agents/state/<key>/`, where `<key>` is the main checkout's absolute path, the first line of `git worktree list --porcelain`, with every character that is not a letter or digit replaced by `-`. Read its lane JSON before planning. Give each builder the folder and a unique `<lane>.json`; the builder is that record's only writer.

## Loop

1. Send a spec with more than one task to `planner`; a single task goes straight to grunt or a builder.
2. Put the planner's questions to the user before starting lanes.
3. Quote each shared contract from the plan into every brief that uses it, word for word.
4. Assign each lane a branch and absolute worktree path. Its builder creates them from the default branch.
5. Start independent builders together. A dependent lane waits for its prerequisite's integration.
6. Require each builder's gate result before starting reviews.
7. Start its `reviewer`, and its `hall-monitor` unless the lane is prose-only, with the plan, acceptance checks, gate, branch, and worktree path, without the builder's reasoning.
8. Send findings to the same builder (`SendMessage` in Claude Code), or to a new builder with the original brief, last report, and findings. Repeat step 6, then rerun only the checkers that returned findings. After two rounds with findings left, stop the lane for the user.
9. Ready means the gate passed, reviewer PASS, and hall-monitor `clean` when it ran. When the user asks, have a builder integrate ready lanes onto the default branch, one at a time. Push only when asked.

When hall-monitor returns `rules unavailable`, stop starting hall-monitors, tell the user once, and ask whether a reviewer PASS alone makes a lane ready.

## A brief contains

The observable end state; the plan location and this lane's acceptance checks; the worktree path and branch; the files the lane may touch and must leave alone; the gate; the repository's worktree, branch, commit, and merge rules, verbatim; and the state folder and lane record.

## Verification

A builder's report is a claim. Assess the reviewer's diff evidence against the files. Send blocker reproduction and disputed "flaky" or "pre-existing" claims to the reviewer. Send blockers, contract conflicts, and disputed scope to `planner` with the current plan. Check for weakened tests, silenced checks, scope beyond the brief, the wrong checkout, and seams between lanes.

## Report

- **Verdict**: per lane, its commit, the reviewer's verdict, hall-monitor's result, and whether it holds.
- **Verified**: who ran each check and its result.
- **Not done**: work left out, blocked, or left for a person, and why.
- **Next**: the next action, or the decision you need.

Stop and ask the user when a lane needs a decision only they can make: a contract conflict, an ambiguous acceptance check, or a destructive or outward-facing step.
