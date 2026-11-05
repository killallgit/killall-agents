"""Checks the pure parts of release.py: version bumps, rewriting every manifest, and the publish steps."""

import tempfile
from pathlib import Path

import release


def main() -> None:
    assert release.bump_version("2.7.0", "major") == "3.0.0"
    assert release.bump_version("2.7.4", "minor") == "2.8.0"
    assert release.bump_version("2.7.4", "patch") == "2.7.5"
    for bad_version, level in (("2.7", "patch"), ("2.7.0", "huge")):
        try:
            release.bump_version(bad_version, level)
        except ValueError:
            continue
        raise AssertionError(f"accepted {bad_version} {level}")

    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        for manifest in release.MANIFESTS:
            (work / manifest).parent.mkdir(exist_ok=True)
            (work / manifest).write_text('{\n  "name": "x",\n  "version": "2.7.0",\n  "description": "keep"\n}\n')
        assert release.read_version(work) == "2.7.0"
        release.write_version(work, "3.0.0")
        assert all('"version": "3.0.0"' in (work / m).read_text() and '"description": "keep"' in (work / m).read_text() for m in release.MANIFESTS)

    steps = release.publish_steps("3.0.0")
    assert steps[1][-1] == "chore: release v3.0.0" and steps[3][-3:] == ["origin", "HEAD:main", "v3.0.0"] and "--atomic" in steps[3]
    print("release checks passed")


if __name__ == "__main__":
    main()
