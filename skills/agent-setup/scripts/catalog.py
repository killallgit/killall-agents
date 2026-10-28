"""Render the engineering catalog in factory/catalog/ into each host's agent format."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[3] / "factory" / "catalog"
MARKER = "killall-agents"
# A source names its model by tier; each host maps a tier to a model id the user can override.
# The Codex ids repeat those in scripts/build_agents.py; test_catalog.py checks that they agree.
DEFAULT_MODELS = {
    "claude": {"opus": "opus", "sonnet": "sonnet", "haiku": "haiku"},
    "codex": {"opus": "gpt-6-astra", "sonnet": "gpt-6.1-sol", "haiku": "gpt-6-luna"},
}
WRITE_TOOLS = {"Edit", "Write"}


@dataclass(frozen=True)
class Agent:
    slug: str
    meta: dict[str, str]
    body: str

    @property
    def readonly(self) -> bool:
        return not WRITE_TOOLS & set(self.meta["tools"].split(", "))


def parse(text: str) -> tuple[dict[str, str], str]:
    end = text.index("\n---\n", 4)
    meta = {}
    for line in text[4:end].splitlines():
        key, value = line.split(": ", 1)
        meta[key] = json.loads(value) if value.startswith('"') else value
    return meta, text[end + 5 :].strip() + "\n"


def load() -> list[Agent]:
    agents = []
    for path in sorted(CATALOG.glob("*.md")):
        meta, body = parse(path.read_text(encoding="utf-8"))
        agents.append(Agent(path.stem, meta, body))
    return agents


def quoted(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def plain(value: str) -> str:
    """A YAML scalar that stays on one line."""
    return quoted(value) if ": " in value or " #" in value or value[0] in "\"'[{&*!|>%@`#" else value


def render(host: str, agent: Agent, models: dict[str, dict[str, str]]) -> tuple[str, str]:
    """Returns the file name and content of one agent for one host."""
    meta, name = agent.meta, agent.slug
    tier = meta["model"]
    if host == "claude":
        front = [("name", plain(meta["name"])), ("description", plain(meta["description"])), ("tools", meta["tools"]), ("model", models["claude"][tier]),
                 ("effort", meta["effort"]), ("maxTurns", meta["maxTurns"]), ("color", plain(meta["color"]))]
        return name + ".md", "---\n" + "".join(f"{k}: {v}\n" for k, v in front) + f"---\n\n{agent.body}\n<!-- {MARKER} -->\n"
    if host == "cursor":
        return name + ".md", (f"---\nname: {quoted(meta['name'])}\ndescription: {quoted(meta['description'])}\nmodel: inherit\n"
                              f"readonly: {str(agent.readonly).lower()}\n---\n\n{agent.body}\n<!-- {MARKER} -->\n")
    if "'''" in agent.body:
        raise SystemExit(f"{agent.slug} contains ''' and cannot be a TOML literal")
    lines = [f"# {MARKER}", f"name = {quoted(meta['name'])}", f"description = {quoted(meta['description'])}",
             f"model = {quoted(models['codex'][tier])}", f"model_reasoning_effort = {quoted(meta['effort'])}"]
    if agent.readonly:
        lines.append('sandbox_mode = "read-only"')
    return name + ".toml", "\n".join(lines) + f"\ndeveloper_instructions = '''\n{agent.body.strip()}\n'''\n"
