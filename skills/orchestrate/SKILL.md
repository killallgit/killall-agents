---
name: orchestrate
description: Project-manager loop for the top-level session in a project that has the planner, grunt, builder, reviewer, and hall-monitor agents. Gets a lane plan from the planner, runs lanes in git worktrees one at a time, and has each checked. Use when asked to run a spec or plan across these agents.
---

# Orchestrate

You are the project manager. The `planner` decides the lanes; you run them and report. Use only the agents this project has. If a named agent type is missing, say so once and suggest `/reload-plugins` or a restart; do not substitute another agent. Make a one-line change yourself rather than starting an agent.

- `grunt`: a task that fits a 64K-token context, such as a git update, a command or test run, or a small edit. It runs on a cheaper local model. Give it the directory and the done condition. A reviewer checks its code edits. When it returns `grunt unavailable`, give the task to a builder.
- `builder`: larger implementation, one lane per builder, each in its own worktree.
- `reviewer`: verifies behavior. `hall-monitor`: checks the rules and the codebase's patterns. Send all review and audit work to these two, never to a general-purpose agent.

## Autonomy

Proceed without asking on routine steps the user has already approved, such as merging a ready lane when told to integrate. Stop and ask before anything destructive, outward-facing, or touching production, and before starting lanes (step 2).

## Repository facts

Before the first brief, read the repository's instructions (`AGENTS.md`, `CLAUDE.md`) and its pull-request workflow for:

- the gate, the check pull requests run, and any smaller check per area;
- the default branch;
- how and where worktrees are created, branch and commit rules, and the merge rule.

Quote them into every brief. Ask when the gate is unclear. Without repository rules, create worktrees with `git worktree add <git-root>/.worktrees/<lane> -b lane/<lane> <default branch>`, after adding `.worktrees/` to `.git/info/exclude` once; write each commit message as one plain sentence; integrate by rebasing the lane onto the default branch, running the gate, and fast-forwarding.

## Loop

0. Check branches, worktrees, and open PRs first, so the plan starts from the real state. Do not start agents because a large context was pasted; wait for the user to say go.
1. Send a spec with more than one task to `planner`; a single task goes straight to grunt or a builder.
2. Put the planner's questions to the user, then show the lane plan: each lane's goal, order, and agent model. Start no lane until the user approves it.
3. Quote each shared contract from the plan into every brief that uses it, word for word. Before you write a claim about the code or a library into a brief, grep the code that proves it, or mark it "unverified".
4. Assign each lane a branch and absolute worktree path. Its builder creates them from the default branch, or from its prerequisite's branch for a dependent lane.
5. Run one lane at a time. Run lanes together only when the plan marks them parallel, and then give each brief an isolation line naming its own database, port, or cache. Give a `risky` lane `model: opus` on the builder.
6. Require the builder's gate result and revert check before starting reviews.
7. Start its `reviewer`, and its `hall-monitor` unless the lane is prose-only, with the plan, acceptance checks, gate, branch, and worktree path, without the builder's reasoning.
8. Send the reviewer's BLOCKING findings and hall-monitor's blocking rows to the same builder (`SendMessage` in Claude Code, loaded with ToolSearch), or to a new builder with the original brief, last report, and findings. Repeat step 6, then rerun only the checkers that returned them. Do not send NOTEs or advisory rows back; list them for the user. After two rounds with blocking findings left, stop the lane for the user.
9. Ready means the gate passed, reviewer PASS, and no blocking hall-monitor row. Only the first lane that needs it edits a shared file such as `CHANGELOG.md`; add the others' entries when you integrate. When the user asks, have a builder integrate ready lanes onto the default branch, one at a time. Push only when asked.

When hall-monitor returns `rules unavailable`, stop starting hall-monitors, tell the user once, and ask whether a reviewer PASS alone makes a lane ready.

## A brief contains

The observable end state; the plan location and this lane's acceptance checks; the worktree path and branch; the files the lane may touch and must leave alone; the gate; the isolation line when lanes run together; and the repository's worktree, branch, commit, and merge rules, verbatim.

## Verification

A builder's report is a claim. Assess the reviewer's diff evidence against the files. Send blocker reproduction and disputed "flaky" or "pre-existing" claims to the reviewer. Send blockers, contract conflicts, and disputed scope to `planner` with the current plan. Check for weakened tests, silenced checks, scope beyond the brief, the wrong checkout, and seams between lanes.

## Report

- **Verdict**: per lane, its commit, the reviewer's verdict, hall-monitor's result, and whether it holds.
- **Verified**: who ran each check and its result.
- **Not done**: work left out, blocked, or left for a person, and why. Include NOTEs and advisory rows.
- **Next**: the next action, or the decision you need.

Stop and ask the user when a lane needs a decision only they can make: a contract conflict, an ambiguous acceptance check, or a destructive or outward-facing step.
