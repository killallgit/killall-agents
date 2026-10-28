---
name: wrap-up
description: Close out finished work in a git repository — confirm the current branch is merged and nothing is stranded, update the main checkout, groom beads, prune merged worktrees and branches, and ask about what remains. Use after a PR lands, or when the user says "wrap up", "are we done", "is everything merged", "clean up local git", or "prune".
---

# Wrap up

A script does the mechanical work; a Haiku agent runs it in the background; you speak to the user only for a stop, a question, or the final table. Everything is local: nothing is pushed or deleted on a remote.

## Run it

Resolve `scripts/wrap_up.py` against this skill's directory to an absolute path. In Claude Code, start the `git-janitor` agent in the background with that path, the session's worktree, and any flags; on another host, or without that agent, run it yourself:

```sh
python3 <skill dir>/scripts/wrap_up.py --repo <worktree> [--default <branch>] [--update-main] [--dry-run]
```

The script prints JSON. In order, it:

1. Checks the current branch is merged: a merged PR, or a tip reachable from `origin/<default>`. If not, it stops.
2. Checks the current worktree and branch for work that never merged: uncommitted files, stashes, unpublished commits. If any, it stops.
3. Fast-forwards the main project directory. When that directory is on another branch, it asks instead.
3.5. Closes beads whose id appears in a commit on the default branch, merges identical duplicates, and finds the next bead. It skips this when `bd` is missing or uninitialized.
4. Removes clean worktrees and deletes local branches that are merged, including squash-merged ones. It keeps the worktree this session runs in.
5. Lists what remains and asks whether to check if it is superseded.

## Act on the result

- **`stopped`**: tell the user the cause in a few lines and do nothing else. At step 1, find out why the work is not merged: read the PR, its checks, and its reviews. At step 2, read the diff and log to say why the work is there. Discard nothing.
- **`asks`**: put each question to the user. For `update-main`, rerun with `--update-main` on yes. For `check-superseded`, on yes examine each item in `remaining` with `git cherry`, a tree comparison, file content, and `gh pr list --state all --head "<branch>"`. In Claude Code, send each unmerged branch to `git-janitor-investigator` in bounded parallel calls, with its tip, the default ref, upstream, and worktree path, and recheck pivotal findings yourself. A branch with no upstream has "unpublished status unknown", never zero. Report each piece in one line as superseded, landed, or still valuable, with the evidence. Delete nothing.
- **`judgment`**: do what the entry says. For stale beads, read each one and, when what it asks for is gone or overtaken, `bd close <id> --reason "obsolete: <why>"`. Close rather than `bd delete`, which cannot be undone. Combine similar beads with `bd find-duplicates` and `bd supersede <old> --with <new>`. Do not ask.
- **`done`**: relay `table`.

## Report

Finish with the script's table, with any rows you changed or added, and no other prose:

| What | Action | Why |
| --- | --- | --- |

It has a row for the merge check, stranded work, the main directory, beads, each worktree and branch pruned or kept, and, last, `Next bead`; the script leaves that row out when beads is absent.
