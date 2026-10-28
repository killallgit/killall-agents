"""Checks the engineering catalog and the installer's user-wide, catalog, and interactive paths."""

import os
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import catalog  # noqa: E402

INSTALL = HERE / "install.py"
TOOLS = {"Read", "Grep", "Glob", "Bash", "Edit", "Write", "WebFetch", "WebSearch"}
EFFORTS = {"low", "medium", "high"}


def check_sources() -> None:
    agents = catalog.load()
    assert len(agents) >= 20, "catalog is missing agents"
    for agent in agents:
        meta = agent.meta
        assert set(meta) == {"name", "description", "tools", "model", "effort", "maxTurns", "color"}, (agent.slug, set(meta))
        assert meta["model"] in catalog.DEFAULT_MODELS["claude"], agent.slug
        assert meta["effort"] in EFFORTS, agent.slug
        assert set(meta["tools"].split(", ")) <= TOOLS, agent.slug
        assert meta["maxTurns"].isdigit(), agent.slug
        assert sum(line.startswith("```") for line in agent.body.splitlines()) % 2 == 0, f"{agent.slug} has an unclosed code fence"
        assert "'''" not in agent.body, agent.slug
        assert "Identity & Memory" not in agent.body and "Learning & Memory" not in agent.body, f"{agent.slug} kept persona sections"
    big = [agent.slug for agent in agents if len(agent.body.encode()) > 20_000]
    assert not big, f"over 20 KB: {big}"


def check_render() -> None:
    models = {"claude": dict(catalog.DEFAULT_MODELS["claude"]), "codex": {**catalog.DEFAULT_MODELS["codex"], "opus": "gpt-test"}}
    for agent in catalog.load():
        name, text = catalog.render("claude", agent, models)
        assert name == f"engineering-{agent.slug}.md" and text.rstrip().endswith("<!-- killall-agents -->")
        front = text.split("\n---\n", 1)[0]
        assert f"model: {agent.meta['model']}\n" in front + "\n"
        assert not any(line.startswith("color: #") for line in front.splitlines()), f"{agent.slug}: an unquoted # starts a YAML comment"
        name, text = catalog.render("codex", agent, models)
        data = tomllib.loads(text)
        assert text.startswith("# killall-agents\n") and name.endswith(".toml")
        assert data["model"] == models["codex"][agent.meta["model"]] and data["model_reasoning_effort"] == agent.meta["effort"]
        assert data["developer_instructions"].strip() == agent.body.strip()
        assert (data.get("sandbox_mode") == "read-only") == agent.readonly == ("Edit" not in agent.meta["tools"] and "Write" not in agent.meta["tools"])
        assert f"readonly: {str(agent.readonly).lower()}" in catalog.render("cursor", agent, models)[1]


def run(env: dict[str, str], *args: str, stdin: str | None = None, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, str(INSTALL), *args], capture_output=True, text=True, input=stdin, env=os.environ | env, cwd=cwd)


def names(folder: Path) -> list[str]:
    return sorted(p.name for p in folder.glob("*")) if folder.is_dir() else []


def main() -> None:
    check_sources()
    check_render()
    with tempfile.TemporaryDirectory() as tmp:
        user = Path(tmp) / "user"
        env = {"HOME": str(user), "CLAUDE_CONFIG_DIR": f"{user}/.claude", "CODEX_HOME": f"{user}/.codex"}
        (user / ".claude").mkdir(parents=True)
        (user / ".codex").mkdir()
        claude, codex = user / ".claude/agents", user / ".codex/agents"
        total = len(catalog.load())

        done = run(env, "--scope", "user", "--hosts", "claude,codex")
        assert done.returncode == 0, done.stderr
        assert len(names(claude)) == total and len(names(codex)) == total and "(killall-agents " in done.stdout
        assert not (user / ".cursor").exists()

        lanes = run(env, "--scope", "user", "--agents", "lanes")
        assert lanes.returncode != 0 and "per project" in lanes.stderr
        assert run(env, "--scope", "user", "--agents", "nope").returncode != 0
        assert run(env, "--scope", "user", "--model", "codex:opus").returncode != 0

        (claude / "engineering-sre.md").write_text("my own sre\n")
        (claude / "mine.md").write_text("unrelated\n")
        refused = run(env, "--scope", "user", "--hosts", "claude", "--agents", "sre")
        assert refused.returncode != 0 and "--force" in refused.stderr
        assert (claude / "engineering-sre.md").read_text() == "my own sre\n"
        assert run(env, "--scope", "user", "--hosts", "claude", "--agents", "sre", "--force").returncode == 0
        assert names(claude) == ["engineering-sre.md", "mine.md"], "a rerun keeps files that are not ours and drops our unselected ones"
        assert names(codex) == [], "an unselected host loses our copies"

        # Interactive. Claude is preselected because it holds our copy; clearing it asks again, then Codex joins,
        # two agents replace the preselected one, and one Codex model changes.
        asked = run(env, "--interactive", stdin="1\n1\n\n2\n\nn 1-2\n\ny\n\ngpt-test\ny\n")
        assert asked.returncode == 0, asked.stderr
        assert "pick at least one tool" in asked.stdout
        assert names(claude) == ["engineering-autonomous-optimization-architect.md", "engineering-backend-architect.md", "mine.md"]
        assert tomllib.loads((codex / "engineering-backend-architect.toml").read_text())["model"] == "gpt-test"
        # A rerun starts from what is installed, so accepting every default keeps the same two.
        again = run(env, "--interactive", stdin="1\n\n\n\ny\n")
        assert again.returncode == 0 and len(names(codex)) == 2, again.stdout
        cancelled = run(env, "--interactive", stdin="1\n\nn 3\n\n\nn\n")
        assert cancelled.returncode != 0 and "cancelled" in cancelled.stderr and len(names(codex)) == 2
        assert run(env, "--interactive", stdin="1\n").returncode != 0, "end of input is a cancel"

        assert run(env, "--scope", "user", "--remove").returncode == 0
        assert names(claude) == ["mine.md"] and names(codex) == []

        # Project scope takes catalog agents beside the lane agents and lists them in Git's exclude file.
        repo = Path(tmp) / "repo"
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        done = run(env, "--dest", str(repo), "--hosts", "claude", "--agents", "lanes,code-reviewer")
        assert done.returncode == 0, done.stderr
        assert "planner" in done.stdout and "1 engineering" in done.stdout
        assert (repo / ".claude/agents/engineering-code-reviewer.md").is_file()
        assert "/.claude/agents/engineering-code-reviewer.md\n" in (repo / ".git/info/exclude").read_text()
        piped = run(env, "--interactive", stdin="2\n2\n\n\n\ny\n", cwd=repo)
        assert piped.returncode == 0, piped.stdout + piped.stderr
        for path in (".claude/agents/engineering-code-reviewer.md", ".codex/agents/engineering-code-reviewer.toml", ".codex/agents/planner.toml"):
            assert (repo / path).is_file(), f"{path}: the picker keeps what was installed and adds Codex"
        assert run(env, "--dest", str(repo), "--remove").returncode == 0
        assert not (repo / ".claude").exists() and not (repo / ".codex").exists()
    print("catalog checks passed")


if __name__ == "__main__":
    main()
