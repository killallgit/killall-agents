"""Install the lane agents into a project, one file per tool with that tool's model from factory/models.toml. Rerun to refresh; --remove undoes it."""

import argparse
import json
import re
import subprocess
import tomllib
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[3]
FACTORY = PLUGIN / "factory"
VERSION = json.loads((PLUGIN / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))["version"]
TOOLS = ("claude", "codex", "opencode")
MARKDOWN_MARK = "<!-- killall-agents -->"
TOML_MARK = "# killall-agents"
# Written by earlier versions, or for a tool no longer supported: removed on every run.
RETIRED_AGENTS = ("hall-monitor", "git-janitor", "git-janitor-investigator", "comment-janitor")
RETIRED_TOOLS = ("cursor",)
BLOCK = re.compile(r"^# killall-agents:start.*?# killall-agents:end\n\n?", re.MULTILINE | re.DOTALL)


def split(text: str) -> tuple[dict[str, str], str]:
    end = text.index("\n---\n", 4)
    meta = dict(line.split(": ", 1) for line in text[4:end].splitlines())
    return meta, text[end + 5 :].strip() + "\n"


def model_and_effort(pin: str) -> tuple[str, str | None]:
    model, _, effort = pin.partition(" ")
    return model, effort or None


def for_claude(meta: dict[str, str], body: str, pin: str) -> str:
    model, effort = model_and_effort(pin)
    head = "".join(f"{key}: {value}\n" for key, value in {**meta, "model": model, "effort": effort}.items() if value)
    return f"---\n{head}---\n\n{body}\n{MARKDOWN_MARK}\n"


def for_codex(meta: dict[str, str], body: str, pin: str) -> str:
    if "'''" in body:
        raise SystemExit(f"{meta['name']} contains ''' and cannot be a TOML literal")
    model, effort = model_and_effort(pin)
    return (
        f"{TOML_MARK}\nname = {json.dumps(meta['name'])}\ndescription = {json.dumps(meta['description'], ensure_ascii=False)}\n"
        f"model = {json.dumps(model)}\nmodel_reasoning_effort = {json.dumps(effort)}\n"
        f"developer_instructions = '''\n{body}'''\n"
    )


def for_opencode(meta: dict[str, str], body: str, pin: str) -> str:
    return f"---\ndescription: {json.dumps(meta['description'], ensure_ascii=False)}\nmode: subagent\nmodel: {pin}\n---\n\n{body}\n{MARKDOWN_MARK}\n"


RENDER = {"claude": (for_claude, ".md"), "codex": (for_codex, ".toml"), "opencode": (for_opencode, ".md")}


def sources() -> dict[str, tuple[dict[str, str], str]]:
    return {path.stem: split(path.read_text(encoding="utf-8")) for path in sorted(FACTORY.glob("*.md"))}


def models() -> dict[str, dict[str, str]]:
    return tomllib.loads((FACTORY / "models.toml").read_text(encoding="utf-8"))


def agent_file(root: Path, tool: str, name: str) -> Path:
    return root / f".{tool}" / "agents" / f"{name}{RENDER[tool][1]}"


def ours(path: Path, names: set[str]) -> bool:
    """A marker alone is not enough: a file of someone else's that mentions it must keep its own name to be spared."""
    if not path.is_file() or path.stem not in names:
        return False
    return any(mark in path.read_text(encoding="utf-8", errors="ignore") for mark in (MARKDOWN_MARK, TOML_MARK))


def set_block(path: Path, body: str) -> None:
    """Rewrites our marked block and keeps every other line; an empty body drops the block."""
    text = BLOCK.sub("", path.read_text(encoding="utf-8")) if path.is_file() else ""
    if body:
        text += ("" if not text or text.endswith("\n") else "\n") + f"# killall-agents:start\n{body}# killall-agents:end\n"
    if text.strip():
        path.write_text(text, encoding="utf-8")
    elif path.is_file():
        path.unlink()


def keep_out_of_git(root: Path, paths: list[Path]) -> None:
    """Git ignores the copies, and .worktreeinclude has Claude Code put them in each worktree."""
    exclude = root / subprocess.check_output(["git", "-C", str(root), "rev-parse", "--git-path", "info/exclude"], text=True).strip()
    listed = "".join(f"/{path.relative_to(root).as_posix()}\n" for path in paths)
    set_block(exclude, listed + "/.worktreeinclude\n" if paths else "")
    set_block(root / ".worktreeinclude", listed)


def remove_ours(root: Path, names: set[str]) -> None:
    for tool in (*TOOLS, *RETIRED_TOOLS):
        folder = root / f".{tool}" / "agents"
        for path in folder.glob("*"):
            if ours(path, names):
                path.unlink()
        for empty in (folder, folder.parent):
            if empty.is_dir() and not any(empty.iterdir()):
                empty.rmdir()


def install(root: Path, tools: list[str], force: bool) -> dict[Path, str]:
    found, pins = sources(), models()
    names = set(found) | set(RETIRED_AGENTS)
    copies = {agent_file(root, tool, name): RENDER[tool][0](*found[name], pins[name][tool]) for tool in tools for name in found}
    foreign = [str(path) for path in copies if path.exists() and not ours(path, names)]
    if foreign and not force:
        raise SystemExit("not written by killall-agents, rerun with --force to replace: " + ", ".join(foreign))
    remove_ours(root, names)
    for path, content in copies.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    keep_out_of_git(root, sorted(copies))
    return copies


def project_root(given: Path | None) -> Path:
    if given:
        return given.resolve()
    top = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
    if top.returncode:
        raise SystemExit("not inside a Git repository; pass --dest")
    return Path(top.stdout.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dest", type=Path, help="the project's git root (default: the current repository)")
    parser.add_argument("--tools", default=",".join(TOOLS), help="comma-separated: claude, codex, opencode (default: all)")
    parser.add_argument("--remove", action="store_true", help="remove the agents this script wrote")
    parser.add_argument("--force", action="store_true", help="replace a same-named agent this script did not write")
    args = parser.parse_args()
    root = project_root(args.dest)
    if root == Path.home():
        raise SystemExit(f"{root} is not a project; run setup in a project's git root")
    tools = [tool for tool in args.tools.split(",") if tool]
    if unknown := [tool for tool in tools if tool not in TOOLS]:
        raise SystemExit(f"unknown tool: {', '.join(unknown)}")
    if args.remove:
        remove_ours(root, set(sources()) | set(RETIRED_AGENTS))
        keep_out_of_git(root, [])
        print(f"Agents removed from {root}")
        return
    copies = install(root, tools, args.force)
    print(f"Agents installed in {root} (killall-agents {VERSION})")
    for tool in tools:
        print(f"  {tool:<9}" + ", ".join(path.stem for path in copies if path.parent == root / f".{tool}" / "agents"))


if __name__ == "__main__":
    main()
