"""Checks wrap_up.py against throwaway Git repositories and a fake gh."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "wrap_up.py"
FAKE_GH = """#!/bin/sh
case "$*" in
  *"--head squashed"*) cat "$FAKE_GH_PR" ;;
  *) echo '[]' ;;
esac
"""


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(repo), *args], capture_output=True, text=True, check=True).stdout.strip()


def commit(repo: Path, name: str) -> str:
    (repo / name).write_text(name)
    git(repo, "add", name)
    git(repo, "commit", "-qm", name)
    return git(repo, "rev-parse", "HEAD")


def branches(repo: Path) -> list[str]:
    return git(repo, "branch", "--format=%(refname:short)").splitlines()


def wrap_up(repo: Path, *args: str) -> dict:
    done = subprocess.run([sys.executable, str(SCRIPT), "--repo", str(repo), *args], capture_output=True, text=True)
    return json.loads(done.stdout)


def action(report: dict, what: str) -> str | None:
    return next((row["action"] for row in report["rows"] if row["what"].endswith(what)), None)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp).resolve()
        (tmp / "bin").mkdir()
        (tmp / "bin/gh").write_text(FAKE_GH)
        (tmp / "bin/gh").chmod(0o755)
        os.environ.update(HOME=str(tmp), PATH=f"{tmp / 'bin'}:{os.environ['PATH']}", FAKE_GH_PR=str(tmp / "pr.json"))

        git(tmp, "init", "-q", "--bare", "-b", "main", "origin.git")
        git(tmp, "clone", "-q", "origin.git", "primary")
        primary = tmp / "primary"
        commit(primary, "base")
        git(primary, "push", "-q", "-u", "origin", "main")
        git(primary, "remote", "set-head", "origin", "main")
        for name in ("lane", "done"):
            git(primary, "worktree", "add", "-q", "-b", name, str(tmp / name))
            commit(tmp / name, name)
        git(primary, "branch", "squashed", "main")
        git(primary, "branch", "open", "main")
        git(primary, "worktree", "add", "-q", str(tmp / "squashed"), "squashed")
        squashed_tip = commit(tmp / "squashed", "squashed.txt")
        git(primary, "worktree", "remove", str(tmp / "squashed"))
        git(primary, "worktree", "add", "-q", str(tmp / "open"), "open")
        commit(tmp / "open", "open.txt")

        git(primary, "merge", "-q", "--ff-only", "lane")
        git(primary, "merge", "-q", "--no-ff", "-m", "merge done", "done")
        commit(primary, "squashed.txt")
        git(primary, "push", "-q", "origin", "main")
        (tmp / "pr.json").write_text(json.dumps([{"number": 7, "state": "MERGED", "isDraft": False, "mergedAt": "x", "headRefOid": squashed_tip, "baseRefName": "main", "url": "u"}]))
        git(tmp, "clone", "-q", "origin.git", "other")
        commit(tmp / "other", "ahead")
        git(tmp / "other", "push", "-q", "origin", "main")

        stopped = wrap_up(tmp / "open")
        assert stopped["status"] == "stopped" and stopped["stopped_at"] == "1", stopped
        assert stopped["facts"]["branch"] == "open"
        git(primary, "worktree", "remove", str(tmp / "open"))

        (tmp / "lane/scratch.txt").write_text("unsaved")
        stopped = wrap_up(tmp / "lane")
        assert stopped["status"] == "stopped" and stopped["stopped_at"] == "2", stopped
        assert stopped["facts"]["paths"] == ["?? scratch.txt"]
        (tmp / "lane/scratch.txt").unlink()

        before = branches(primary)
        planned = wrap_up(tmp / "lane", "--dry-run")
        assert branches(primary) == before and (tmp / "done").is_dir(), "dry run changed something"
        assert "would be pruned" in planned["table"]

        report = wrap_up(tmp / "lane")
        assert report["status"] == "asks" and [q["id"] for q in report["questions"]] == ["check-superseded"], report
        assert action(report, "Main directory") == "fast-forwarded 1 commits"
        assert action(report, str(tmp / "done")) == "pruned"
        assert action(report, str(tmp / "lane")) == "kept", "the session's own worktree stays"
        assert action(report, "Branch squashed") == "deleted" and action(report, "Branch done") == "deleted"
        assert sorted(branches(primary)) == ["lane", "main", "open"], branches(primary)
        assert [item["branch"] for item in report["remaining"]] == ["open"]
        assert report["remaining"][0]["ahead_of_default"] == 1

        git(primary, "switch", "-q", "-c", "holder")
        asked = wrap_up(tmp / "lane")
        assert [q["id"] for q in asked["questions"]][0] == "update-main" and git(primary, "branch", "--show-current") == "holder"
        wrap_up(tmp / "lane", "--update-main")
        assert git(primary, "branch", "--show-current") == "main" and "holder" not in branches(primary)
    print("wrap-up checks passed")


if __name__ == "__main__":
    main()
