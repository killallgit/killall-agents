"""Checks install.py against a throwaway Git repository."""

import json
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

INSTALL = Path(__file__).resolve().parent / "install.py"
FACTORY = INSTALL.parents[2].parent / "factory"
RETIRED_FILES = (".claude/agents/hall-monitor.md", ".claude/agents/git-janitor.md", ".claude/agents/comment-janitor.md", ".cursor/agents/planner.md")


def run(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(INSTALL), "--dest", str(repo), *args], capture_output=True, text=True)


def check_every_agent_pins_a_model_for_every_tool() -> None:
    pins = tomllib.loads((FACTORY / "models.toml").read_text(encoding="utf-8"))
    agents = sorted(path.stem for path in FACTORY.glob("*.md"))
    assert sorted(pins) == agents, "models.toml and factory/ list different agents"
    for name in agents:
        assert all(pins[name].get(tool, "").split() for tool in ("claude", "codex", "opencode")), f"{name} leaves a tool to inherit the session model"


def main() -> None:
    check_every_agent_pins_a_model_for_every_tool()
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        exclude = repo / ".git/info/exclude"
        (repo / ".worktreeinclude").write_text(".env\n")
        (repo / ".claude/agents").mkdir(parents=True)
        (repo / ".claude/agents/mine.md").write_text("the user's own agent\n")
        (repo / ".cursor/agents").mkdir(parents=True)
        for old in RETIRED_FILES:
            (repo / old).write_text("old\n\n<!-- killall-agents -->\n")

        (repo / ".claude/agents/builder.md").write_text("the user's builder\n")
        refused = run(repo)
        assert refused.returncode != 0 and "--force" in refused.stderr
        assert (repo / ".claude/agents/builder.md").read_text() == "the user's builder\n"

        installed = run(repo, "--force")
        assert installed.returncode == 0, installed.stderr
        version = json.loads((INSTALL.parents[2].parent / ".claude-plugin/plugin.json").read_text())["version"]
        assert f"(killall-agents {version})" in installed.stdout

        planner = (repo / ".claude/agents/planner.md").read_text()
        assert "\nmodel: opus\neffort: high\n" in planner and "\ncodex" not in planner
        assert 'model = "gpt-6-astra"' in (repo / ".codex/agents/planner.toml").read_text()
        opencode = (repo / ".opencode/agents/planner.md").read_text()
        assert "model: anthropic/claude-opus-5-5\n" in opencode and "mode: subagent" in opencode
        assert "\nskills: follow-the-rules\n" in (repo / ".claude/agents/builder.md").read_text()
        tomllib.loads((repo / ".codex/agents/reviewer.toml").read_text())

        assert (repo / ".claude/agents/mine.md").is_file(), "foreign agent removed"
        assert not any((repo / old).exists() for old in RETIRED_FILES), "a retired agent stays"
        assert "/.codex/agents/planner.toml\n" in exclude.read_text()
        assert (repo / ".worktreeinclude").read_text().startswith(".env\n# killall-agents:start\n/.claude/agents/builder.md\n")
        status = subprocess.run(["git", "-C", str(repo), "status", "--porcelain", "--untracked-files=all"], capture_output=True, text=True).stdout
        assert status == "?? .claude/agents/mine.md\n", status

        assert run(repo, "--tools", "claude").returncode == 0
        assert not (repo / ".codex").exists() and (repo / ".claude/agents/planner.md").is_file(), "a run keeps only the tools it names"

        assert run(repo, "--remove").returncode == 0
        assert sorted(path.name for path in (repo / ".claude/agents").iterdir()) == ["mine.md"]
        assert (repo / ".worktreeinclude").read_text() == ".env\n"
        assert not (repo / ".codex").exists() and not (repo / ".opencode").exists()
        assert "killall-agents" not in exclude.read_text()
    print("install checks passed")


if __name__ == "__main__":
    main()
