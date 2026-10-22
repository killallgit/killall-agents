# Usage insights: what a month of sessions says about the agents

Research date: 2026-10-21. Source: Claude Code `/insights` over 65 analyzed sessions (2026-09-23 to 2026-10-22), plus a tool-call count taken directly from the session transcripts. Project, customer and ticket details are left out because this repository is public. The raw report is kept privately.

## Friction that agent design can address

| Observed | Implication for `factory/` and `orchestrate` |
| --- | --- |
| Top friction was "wrong approach" (28 sessions): the orchestrator picked a path, scope or tool the user did not intend. | The orchestrator should present its lane plan and wait for a go-ahead before any fan-out. |
| Six general-purpose review agents were started on Opus and stopped for token waste. | Route review and audit work to the packaged `reviewer` and `hall-monitor` agents, never to a general-purpose agent. Only `planner` is Opus. |
| Orchestration was started before the user said go, and again after a large context paste. | Consolidate state first (branches, worktrees, PRs), then plan. |
| Project rules were missed until corrected: redundant comments, no comment audit before commit, tests asserting on log or error text. | Builders should run the comment audit before committing, and `follow-the-rules` should state the no-log-text-assertions rule. |
| Claude asked permission on already-approved merges, yet acted without asking elsewhere. | The orchestrate skill should state an explicit autonomy contract: routine merges proceed; destructive or production operations stop. |

## Why Bash dominates over Read

Counted from 82 session transcripts: 13,319 `Bash` calls against 561 `Read`, 156 `Grep` and 128 `Glob`. Classifying Bash calls by first word shows that a large share is itself file reading or searching:

| First word | Calls |
| --- | --- |
| `git` | 1,780 |
| `grep` | 1,731 |
| `sed` | 1,596 |
| `gh` | 840 |
| `python3` | 816 |
| `cat` | 779 |
| `kubectl` | 564 |
| `ls` | 488 |
| `rg` | 118 |
| `head` | 41 |

`grep`, `sed`, `cat`, `ls`, `rg` and `head` add up to about 4,750 calls, roughly 36% of all Bash calls and about eight times the number of `Read` calls. Command-first classification is approximate: `sed` may also be an in-place edit, and a first word can hide a pipeline.

Candidate causes, not yet tested:

- A global instruction tells the agent to batch related commands into one Bash call, which favors shell reads over one `Read` per file.
- `sed -n 'a,bp'` and `grep -n` are habitual ways to read a slice or locate a line, and they bypass `Read`'s offset and limit.
- Output filtering applied to shell commands may make shell reads look cheaper than they are.

What to try: have the packaged agents prefer `Read` with `offset` and `limit` for known files and `Grep` for search, reserve Bash for `git`, `gh`, `kubectl` and builds, then compare the same count after a few sessions.

## Agent model settings

- The planner is the one agent that should be Opus. The factory already does this: `planner` is Opus/high, `builder` Sonnet/medium, `reviewer` Sonnet/high, `grunt` Haiku/low, `hall-monitor` Haiku/medium.
- Agent files with no `model:` line inherit the parent session's model, so a project whose agents lack one follows whatever the session runs.
- `effortLevel` set to high for every model raises token use everywhere; medium is a cheaper default for builder-style work.

## Open questions

- Does preferring `Read` and `Grep` over shell reads actually reduce tokens, or only change the tool name?
- Should `orchestrate` print a per-lane model and rough cost estimate before the user approves the plan?
