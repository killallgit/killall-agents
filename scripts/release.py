"""Test origin/main, bump the plugin version in every manifest, commit, tag, and push. usage: release.py patch|minor|major"""

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SEMVER = re.compile(r"\A(\d+)\.(\d+)\.(\d+)\Z")
VERSION_LINE = re.compile(r'("version": ")([^"]+)(")')
LEVELS = ("patch", "minor", "major")
MANIFESTS = (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json")
CHECKS = (["python3", "skills/setup-agents/scripts/test_install.py"], ["python3", "scripts/test_release.py"])
GIT_LOCATION_VARS = {"GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"}


def bump_version(current: str, level: str) -> str:
    match = SEMVER.match(current)
    if match is None:
        raise ValueError(f"not a major.minor.patch version: {current}")
    if level not in LEVELS:
        raise ValueError(f"level must be one of {LEVELS}")
    major, minor, patch = map(int, match.groups())
    bumped = {"major": (major + 1, 0, 0), "minor": (major, minor + 1, 0), "patch": (major, minor, patch + 1)}[level]
    return ".".join(map(str, bumped))


def read_version(work: Path) -> str:
    found = VERSION_LINE.search((work / MANIFESTS[0]).read_text(encoding="utf-8"))
    if found is None:
        raise SystemExit(f"no version in {MANIFESTS[0]}")
    return found.group(2)


def write_version(work: Path, version: str) -> None:
    for manifest in MANIFESTS:
        path = work / manifest
        path.write_text(VERSION_LINE.sub(rf"\g<1>{version}\g<3>", path.read_text(encoding="utf-8"), count=1), encoding="utf-8")


def publish_steps(version: str) -> list[list[str]]:
    tag = f"v{version}"
    return [
        ["git", "add", *MANIFESTS],
        ["git", "commit", "-m", f"chore: release {tag}"],
        ["git", "tag", "-a", tag, "-m", tag],
        ["git", "push", "--atomic", "origin", "HEAD:main", tag],
    ]


def clean_env() -> dict[str, str]:
    return {key: value for key, value in os.environ.items() if key not in GIT_LOCATION_VARS}


def run(step: list[str], cwd: Path) -> None:
    subprocess.run(step, check=True, cwd=cwd, env=clean_env())


def output(step: list[str], cwd: Path) -> str:
    return subprocess.run(step, check=True, capture_output=True, text=True, cwd=cwd, env=clean_env()).stdout


def release_from(work: Path, level: str) -> str:
    for step in CHECKS:
        run(step, work)
    version = bump_version(read_version(work), level)
    tag = f"v{version}"
    if output(["git", "tag", "--list", tag], work).strip():
        raise SystemExit(f"{tag} already exists")
    write_version(work, version)
    try:
        for step in publish_steps(version):
            run(step, work)
    except subprocess.CalledProcessError:
        if output(["git", "tag", "--list", tag], work).strip():
            run(["git", "tag", "-d", tag], work)
        raise
    return tag


def release(root: Path, level: str) -> str:
    run(["git", "fetch", "origin", "--tags"], root)
    with tempfile.TemporaryDirectory() as parent:
        work = Path(parent) / "release"
        run(["git", "worktree", "add", "--detach", str(work), "origin/main"], root)
        try:
            return release_from(work, level)
        finally:
            run(["git", "worktree", "remove", "--force", str(work)], root)


def main(argv: list[str]) -> int:
    if len(argv) != 1 or argv[0] not in LEVELS:
        print(f"usage: release.py {'|'.join(LEVELS)}", file=sys.stderr)
        return 2
    try:
        tag = release(Path(__file__).resolve().parent.parent, argv[0])
    except subprocess.CalledProcessError as error:
        print(f"failed: {' '.join(error.cmd)}", file=sys.stderr)
        return 1
    print(f"released {tag}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
