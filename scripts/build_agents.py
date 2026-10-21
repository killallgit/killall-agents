"""Write the Codex and Cursor copies of the agents in factory/claude/, which is the source."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FACTORY = ROOT / "factory"
# Codex model, Codex reasoning effort, Cursor readonly; Cursor agents inherit the session model.
HOSTS = {
    "planner": ("gpt-6-astra", "high", True),
    "grunt": ("gpt-6-luna", "low", False),
    "builder": ("gpt-6.1-sol", "medium", False),
    "reviewer": ("gpt-6.1-sol", "high", False),
    "hall-monitor": ("gpt-6.1-sol", "medium", True),
}


def split(text: str) -> tuple[dict[str, str], str]:
    end = text.index("\n---\n", 4)
    meta = dict(line.split(": ", 1) for line in text[4:end].splitlines())
    return meta, text[end + 5 :].strip() + "\n"


def toml_literal(value: str) -> str:
    if "'''" in value:
        raise SystemExit("an agent body contains ''' and cannot be a TOML literal")
    return "'''\n" + value.strip() + "\n'''"


def outputs() -> dict[Path, str]:
    found = {}
    for name, (model, effort, readonly) in HOSTS.items():
        meta, body = split((FACTORY / "claude" / f"{name}.md").read_text(encoding="utf-8"))
        description = json.dumps(meta["description"], ensure_ascii=False)
        found[FACTORY / "codex" / f"{name}.toml"] = (
            f"# killall-agents\nname = {json.dumps(name)}\ndescription = {description}\n"
            f"model = {json.dumps(model)}\nmodel_reasoning_effort = {json.dumps(effort)}\n"
            f"developer_instructions = {toml_literal(body)}\n"
        )
        found[FACTORY / "cursor" / f"{name}.md"] = f"---\nname: {name}\ndescription: {description}\nmodel: inherit\nreadonly: {str(readonly).lower()}\n---\n\n{body}"
    return found


def main() -> None:
    expected = outputs()
    if "--check" not in sys.argv:
        for path, content in expected.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        return
    present = {path for host in ("codex", "cursor") for path in (FACTORY / host).glob("*")}
    stale = sorted(path for path in present | set(expected) if not path.is_file() or path.read_text(encoding="utf-8") != expected.get(path))
    if stale:
        sys.exit("out of date, run scripts/build_agents.py: " + ", ".join(str(path.relative_to(ROOT)) for path in stale))
    import tomllib

    for path in expected:
        if path.suffix == ".toml":
            tomllib.loads(path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
