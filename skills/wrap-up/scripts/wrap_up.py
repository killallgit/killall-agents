"""Run the mechanical steps of wrap-up in one repository and print a JSON report.

The report's "status" is "done", "asks" (a question for the user is pending), or
"stopped" (a person has to look). The script exits 0 whenever it printed a report.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True)


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", *args], repo)


def text(process: subprocess.CompletedProcess[str]) -> str:
    return process.stdout.strip()


class Report:
    def __init__(self, dry_run: bool) -> None:
        self.dry_run = dry_run
        self.rows: list[dict[str, str]] = []
        self.questions: list[dict[str, str]] = []
        self.judgment: list[str] = []
        self.remaining: list[dict] = []
        self.facts: dict = {}
        self.stopped_at: str | None = None
        self.next_bead: str | None = None

    def row(self, what: str, action: str, why: str) -> None:
        self.rows.append({"what": what, "action": action, "why": why})

    def stop(self, step: str, why: str, **facts: object) -> None:
        self.stopped_at = step
        self.row(f"Step {step}", "stopped", why)
        self.facts = facts

    def change(self, command: list[str], cwd: Path) -> bool:
        return self.dry_run or run(command, cwd).returncode == 0

    def render(self) -> str:
        status = "stopped" if self.stopped_at else "asks" if self.questions else "done"
        lines = ["| What | Action | Why |", "| --- | --- | --- |"]
        changes = ("pruned", "deleted", "closed", "fast-forwarded", "merged duplicates")
        lines += [f"| {r['what']} | {'would be ' if self.dry_run and r['action'].startswith(changes) else ''}{r['action']} | {r['why']} |" for r in self.rows]
        if self.next_bead:
            lines.append(f"| Next bead | {self.next_bead} | first ready |")
        return json.dumps(
            {
                "status": status,
                "stopped_at": self.stopped_at,
                "dry_run": self.dry_run,
                "rows": self.rows,
                "facts": self.facts,
                "questions": self.questions,
                "judgment": self.judgment,
                "remaining": self.remaining,
                "next_bead": self.next_bead,
                "table": "\n".join(lines),
            },
            indent=2,
        )


def default_branch(repo: Path, given: str | None) -> str | None:
    if given:
        return given
    if ref := text(git(repo, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")):
        return ref.removeprefix("origin/")
    if shutil.which("gh") and (name := text(run(["gh", "repo", "view", "--json", "defaultBranchRef", "--jq", ".defaultBranchRef.name"], repo))):
        return name
    local = [name for name in ("main", "master") if git(repo, "rev-parse", "--verify", "-q", f"refs/heads/{name}").returncode == 0]
    return local[0] if len(local) == 1 else None


def worktrees(repo: Path) -> list[dict[str, str]]:
    found, current = [], {}
    for line in [*text(git(repo, "worktree", "list", "--porcelain")).splitlines(), ""]:
        if not line:
            found += [current] if current else []
            current = {}
            continue
        key, _, value = line.partition(" ")
        current[key] = value
    return found


def branch_of(worktree: dict[str, str]) -> str:
    return worktree.get("branch", "").removeprefix("refs/heads/")


def pull_requests(repo: Path, branch: str) -> list[dict] | None:
    """None means unknown: gh is missing or failed."""
    if not shutil.which("gh"):
        return None
    process = run(["gh", "pr", "list", "--head", branch, "--state", "all", "--limit", "100", "--json", "number,state,isDraft,mergedAt,headRefOid,baseRefName,url"], repo)
    return json.loads(process.stdout) if process.returncode == 0 else None


def merged_by(repo: Path, default: str, branch: str, tip: str) -> str | None:
    """Names what landed the tip on the default branch, or None."""
    if git(repo, "merge-base", "--is-ancestor", tip, f"origin/{default}").returncode == 0:
        return f"reachable from origin/{default}"
    for pr in pull_requests(repo, branch) or []:
        if pr["state"] == "MERGED" and pr["baseRefName"] == default and git(repo, "merge-base", "--is-ancestor", tip, pr["headRefOid"]).returncode == 0:
            return f"PR #{pr['number']} merged"
    return None


def dirty(path: Path) -> list[str]:
    return text(git(path, "status", "--porcelain", "--untracked-files=all")).splitlines()


def check_current(repo: Path, default: str, branch: str, report: Report) -> None:
    if not branch:
        return report.stop("1", "HEAD is detached, so there is no branch to check")
    if branch == default:
        unpublished = int(text(git(repo, "rev-list", "--count", f"origin/{default}..HEAD")) or 0)
        if unpublished:
            return report.stop("2", f"{default} has {unpublished} commits origin/{default} lacks")
        report.row("Current work", "merged", f"on {default}")
    else:
        tip = text(git(repo, "rev-parse", "HEAD"))
        if not (landed := merged_by(repo, default, branch, tip)):
            upstream = git(repo, "rev-parse", "--abbrev-ref", "@{u}").returncode == 0
            return report.stop(
                "1",
                f"{branch} is not merged",
                branch=branch,
                pull_requests=pull_requests(repo, branch),
                unpushed=int(text(git(repo, "rev-list", "--count", "@{u}..HEAD")) or 0) if upstream else "no upstream",
            )
        report.row("Current work", "merged", f"{branch}: {landed}")
    stashes = [s for s in text(git(repo, "stash", "list", "--format=%gs")).splitlines() if s.startswith((f"On {branch}:", f"WIP on {branch}:"))]
    if left := dirty(repo) or stashes:
        report.stop("2", f"{len(left)} uncommitted or stashed items remain", paths=dirty(repo), stashes=stashes)
    else:
        report.row("Stranded work", "none", "current worktree is clean, no stashes")


def update_main(primary: Path, default: str, switch: bool, report: Report) -> None:
    branch = branch_of(worktrees(primary)[0])
    if branch != default:
        if not switch:
            report.questions.append({"id": "update-main", "ask": f"The main directory is on {branch or 'a detached HEAD'}. Check out and update {default}? Rerun with --update-main on yes."})
            return report.row("Main directory", "left alone", f"on {branch or 'a detached HEAD'}, not {default}")
        if left := dirty(primary):
            return report.row("Main directory", "left alone", f"{len(left)} dirty paths block switching to {default}")
        if not report.change(["git", "switch", default], primary):
            return report.stop("3", f"could not switch the main directory to {default}")
    before = text(git(primary, "rev-parse", "HEAD"))
    if not report.change(["git", "merge", "--ff-only", f"origin/{default}"], primary):
        return report.stop("3", f"the main directory cannot fast-forward to origin/{default}", output=git(primary, "merge", "--ff-only", f"origin/{default}").stderr.strip())
    moved = int(text(git(primary, "rev-list", "--count", f"{before}..HEAD")) or 0)
    report.row("Main directory", f"fast-forwarded {moved} commits" if moved else "up to date", default)


def groom_beads(primary: Path, default: str, report: Report) -> None:
    if not shutil.which("bd") or run(["bd", "info"], primary).returncode != 0:
        return
    listing = run(["bd", "list", "--json", "--status", "open,in_progress", "--limit", "0"], primary)
    try:
        beads = json.loads(listing.stdout)
        beads = beads.get("issues", []) if isinstance(beads, dict) else beads
    except ValueError:
        beads = []
        report.judgment.append("`bd list --json` was unreadable, so no bead was checked against the default branch")
    closed = []
    for bead in beads:
        if not bead.get("id"):
            continue
        pattern = rf"(^|[^A-Za-z0-9_-]){re.escape(bead['id'])}([^A-Za-z0-9_-]|$)"
        if commit := text(git(primary, "log", f"origin/{default}", "-n", "1", "--extended-regexp", f"--grep={pattern}", "--format=%h")):
            if report.change(["bd", "close", bead["id"], "--reason", f"landed in {commit}"], primary):
                closed.append(bead["id"])
    if closed:
        report.row("Beads", f"closed {len(closed)}", ", ".join(closed))
    merged = run(["bd", "duplicates", "--auto-merge"], primary) if not report.dry_run else None
    if merged and merged.stdout.strip():
        report.row("Beads", "merged duplicates", merged.stdout.strip().splitlines()[-1])
    if stale := text(run(["bd", "stale"], primary)):
        report.judgment.append("Stale beads to read, then close when obsolete with `bd close <id> --reason \"obsolete: ...\"`:\n" + stale[:2000])
    if ready := text(run(["bd", "ready", "--json"], primary)):
        try:
            first = json.loads(ready)[0]
            report.next_bead = f"{first['id']} {first['title']}"
        except (ValueError, LookupError, TypeError):
            report.judgment.append("`bd ready --json` was unreadable, so the next bead is unknown")


def prune(repo: Path, current: Path, default: str, report: Report) -> None:
    for entry in worktrees(repo)[1:]:
        path, branch = Path(entry["worktree"]), branch_of(entry)
        if path.resolve() == current.resolve():
            report.row(f"Worktree {path}", "kept", "this session is running in it; remove it after leaving")
        elif "locked" in entry or not branch:
            report.remaining.append({"worktree": str(path), "branch": branch or None, "why": "locked" if "locked" in entry else "detached HEAD"})
        elif (landed := merged_by(repo, default, branch, entry["HEAD"])) and not dirty(path):
            if report.change(["git", "worktree", "remove", str(path)], repo):
                report.row(f"Worktree {path}", "pruned", landed)
            else:
                report.remaining.append({"worktree": str(path), "branch": branch, "why": "git worktree remove failed"})
        else:
            report.remaining.append({"worktree": str(path), "branch": branch, "why": "uncommitted changes" if landed else "not merged"})
    report.change(["git", "worktree", "prune"], repo)
    checked_out = {branch_of(entry) for entry in worktrees(repo)}
    refs = text(git(repo, "for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads")).splitlines()
    for ref in refs:
        branch, tip = ref.split(" ")
        if branch == default or branch in checked_out:
            continue
        if landed := merged_by(repo, default, branch, tip):
            if text(git(repo, "rev-parse", f"refs/heads/{branch}")) == tip and report.change(["git", "branch", "-D", "--", branch], repo):
                report.row(f"Branch {branch}", "deleted", landed)
        else:
            report.remaining.append(evidence(repo, default, branch, tip, checked_out))


def evidence(repo: Path, default: str, branch: str, tip: str, checked_out: set[str]) -> dict:
    upstream = text(git(repo, "for-each-ref", "--format=%(upstream:short)", f"refs/heads/{branch}"))
    committed = datetime.fromisoformat(text(git(repo, "log", "-1", "--format=%cI", tip)))
    return {
        "branch": branch,
        "tip": tip,
        "ahead_of_default": int(text(git(repo, "rev-list", "--count", f"origin/{default}..{tip}")) or 0),
        "upstream": upstream or None,
        "ahead_of_upstream": int(text(git(repo, "rev-list", "--count", f"{upstream}..{tip}")) or 0) if upstream else None,
        "days_since_commit": (datetime.now(timezone.utc) - committed).days,
        "checked_out": branch in checked_out,
        "why": "not merged",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(), help="any directory inside the repository; the session's worktree")
    parser.add_argument("--default", help="the default branch, when it cannot be found")
    parser.add_argument("--update-main", action="store_true", help="switch the main directory to the default branch and fast-forward it")
    parser.add_argument("--dry-run", action="store_true", help="make no change")
    args = parser.parse_args()
    report = Report(args.dry_run)
    current = Path(text(git(args.repo, "rev-parse", "--show-toplevel")))
    if git(current, "fetch", "--prune", "origin").returncode != 0:
        report.stop("0", "git fetch --prune origin failed", output=git(current, "fetch", "origin").stderr.strip())
    elif not (default := default_branch(current, args.default)):
        report.stop("0", "the default branch is unclear; pass --default")
    else:
        primary = Path(worktrees(current)[0]["worktree"])
        check_current(current, default, text(git(current, "branch", "--show-current")), report)
        if not report.stopped_at:
            update_main(primary, default, args.update_main, report)
        if not report.stopped_at:
            groom_beads(primary, default, report)
            prune(current, current, default, report)
            if stashes := text(git(current, "stash", "list")).splitlines():
                report.remaining.append({"stashes": len(stashes), "why": "stashes belong to no branch the script can judge"})
            for item in report.remaining:
                label = f"Worktree {item['worktree']}" if "worktree" in item else f"Branch {item['branch']}" if "branch" in item else "Stashes"
                report.row(label, "kept", item["why"])
            if report.remaining:
                report.questions.append({"id": "check-superseded", "ask": "Some work cannot be pruned automatically. Find out whether it is superseded?"})
    print(report.render())


if __name__ == "__main__":
    main()
