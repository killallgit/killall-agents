"""Summarize how the project agents ran: tokens, time, tool calls and errors from Claude and Codex transcripts, and outcomes from the orchestrator's runs.jsonl."""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

AGENTS = ("planner", "grunt", "builder", "reviewer", "hall-monitor")


def key(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "-", path)


def minutes(stamps: list[str]) -> float:
    times = [datetime.fromisoformat(stamp) for stamp in stamps]
    return (max(times) - min(times)).total_seconds() / 60 if times else 0.0


def first_line(content: object) -> str:
    if isinstance(content, list):
        content = " ".join(part.get("text", "") for part in content if isinstance(part, dict))
    lines = [line.strip() for line in str(content).splitlines() if line.strip()]
    if len(lines) > 1 and re.fullmatch(r"Exit code \d+", lines[0]):
        return f"{lines[0]}: {lines[1]}"[:90]
    return lines[0][:90] if lines else "?"


def entries(file):
    for line in file:
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue  # a live session can leave its last line half written


def context(usage: dict) -> int:
    return usage.get("input_tokens", 0) + usage.get("cache_creation_input_tokens", 0) + usage.get("cache_read_input_tokens", 0)


def claude_runs(root: Path, since: float):
    for meta in root.glob("*/*/subagents/*.meta.json"):
        transcript = meta.with_name(meta.name.removesuffix(".meta.json") + ".jsonl")
        if not transcript.is_file() or transcript.stat().st_mtime < since:
            continue
        usage, models, stamps, tools, errors = {}, Counter(), [], 0, []
        for entry in entries(transcript.open(encoding="utf-8")):
            message = entry.get("message") or {}
            content = message.get("content") if isinstance(message.get("content"), list) else []
            content = [part for part in content if isinstance(part, dict)]
            if "timestamp" in entry:
                stamps.append(entry["timestamp"])
            if entry.get("type") == "assistant":
                # One API message spans several entries that each repeat its usage.
                usage[message.get("id")] = message.get("usage") or {}
                models[message.get("model")] += 1
                tools += sum(part.get("type") == "tool_use" for part in content)
            errors += [first_line(part.get("content")) for part in content if part.get("type") == "tool_result" and part.get("is_error")]
        yield {
            "host": "claude",
            "agent": json.loads(meta.read_text(encoding="utf-8")).get("agentType", "?").rsplit(":", 1)[-1],
            "project": meta.parents[2].name,
            "tokens_in": sum(context(u) for u in usage.values()),
            "peak": max(map(context, usage.values()), default=0),
            "tokens_out": sum(u.get("output_tokens", 0) for u in usage.values()),
            "minutes": minutes(stamps),
            "tools": tools,
            "errors": errors,
            "model": models.most_common(1)[0][0] if models else "?",
        }


def codex_runs(root: Path, since: float):
    for path in root.glob("*/*/*/rollout-*.jsonl"):
        if path.stat().st_mtime < since:
            continue
        with path.open(encoding="utf-8") as file:
            meta = next(entries(file), {}).get("payload", {})
            if meta.get("thread_source") != "subagent":
                continue
            # A subagent's rollout starts with history copied from its parent.
            start = meta.get("subagent_history_start_ordinal", 0)
            total, peak, tools, model, stamps = {}, 0, 0, "?", []
            for entry in entries(file):
                if entry.get("ordinal", 0) < start:
                    continue
                payload = entry.get("payload") or {}
                stamps.append(entry["timestamp"])
                if payload.get("type") == "token_count" and payload.get("info"):
                    total = payload["info"]["total_token_usage"]
                    peak = max(peak, payload["info"].get("last_token_usage", {}).get("input_tokens", 0))
                elif payload.get("type") in ("function_call", "custom_tool_call"):
                    tools += 1
                elif payload.get("type") == "thread_settings_applied":
                    model = payload["thread_settings"].get("model", "?")
        yield {
            "host": "codex",
            "agent": meta.get("agent_role", "?"),
            "project": key(meta.get("cwd", "")),
            "tokens_in": total.get("input_tokens", 0),
            "tokens_out": total.get("output_tokens", 0),
            "peak": peak,
            "minutes": minutes(stamps),
            "tools": tools,
            "errors": None,
            "model": model,
        }


def outcomes(root: Path, since: float):
    cutoff = datetime.fromtimestamp(since, timezone.utc)
    for log in root.glob("*/runs.jsonl"):
        for row in entries(log.open(encoding="utf-8")):
            try:
                stamp = datetime.fromisoformat(row["time"])
                if (stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)) >= cutoff:
                    yield row | {"project": log.parent.name}
            except (ValueError, KeyError, TypeError, AttributeError):
                continue


def median(values: list[float]) -> float:
    return statistics.median(values) if values else 0


def report(runs: list[dict], rows: list[dict]) -> str:
    out = [f"{'host':7}{'agent':14}{'runs':>5}{'med in':>11}{'med peak':>9}{'max peak':>9}{'med out':>9}{'med min':>8}{'med tools':>10}{'err %':>7}  models"]
    groups = defaultdict(list)
    for run in runs:
        groups[run["host"], run["agent"]].append(run)
    for (host, agent), group in sorted(groups.items()):
        tools = sum(run["tools"] for run in group)
        errors = None if group[0]["errors"] is None else sum(len(run["errors"]) for run in group)
        rate = "-" if errors is None else f"{100 * errors / tools:.0f}" if tools else "0"
        models = ", ".join(f"{model} {count}" for model, count in Counter(run["model"] for run in group).most_common(2))
        out.append(
            f"{host:7}{agent:14}{len(group):>5}{median([r['tokens_in'] for r in group]):>11,.0f}{median([r['peak'] for r in group]):>9,.0f}{max(r['peak'] for r in group):>9,.0f}{median([r['tokens_out'] for r in group]):>9,.0f}"
            f"{median([r['minutes'] for r in group]):>8.1f}{median([r['tools'] for r in group]):>10.0f}{rate:>7}  {models}"
        )
    for (host, agent), group in sorted(groups.items()):
        common = Counter(error for run in group for error in run["errors"] or []).most_common(3)
        if common:
            out.append(f"\nTop tool errors, {host} {agent}:")
            out += [f"  {count:>3}  {error}" for error, count in common]

    out.append("\nOutcomes (runs.jsonl):")
    if not rows:
        return "\n".join(out + ["  none recorded yet"])
    results = defaultdict(Counter)
    lanes = defaultdict(list)
    for row in rows:
        results[row.get("agent", "?")][row.get("result", "?")] += 1
        lanes[row["project"], row.get("lane")].append(row)
    for agent, counts in sorted(results.items()):
        out.append(f"  {agent:14}{sum(counts.values()):>4}  " + " · ".join(f"{result} {count}" for result, count in counts.most_common()))
    rounds = [max(row.get("round", 1) for row in lane) for lane in lanes.values()]
    first_pass = sum(1 for lane in lanes.values() if any(row.get("agent") == "reviewer" and row.get("round", 1) == 1 and row.get("result") == "PASS" for row in lane))
    reviewed = sum(1 for lane in lanes.values() if any(row.get("agent") == "reviewer" for row in lane))
    out.append(f"  lanes {len(lanes)}, mean rounds {statistics.mean(rounds):.1f}, reviewer PASS on round 1: {first_pass}/{reviewed}")
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=float, default=30, help="look back this many days (default 30)")
    parser.add_argument("--project", help="only projects whose path contains this")
    parser.add_argument("--all", action="store_true", help="include agents outside this catalog")
    args = parser.parse_args()
    since = time.time() - args.days * 86400
    home = Path.home()
    codex = Path(os.environ.get("CODEX_HOME", home / ".codex")) / "sessions"
    state = Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "killall-skills/agents/state"
    runs = [*claude_runs(home / ".claude/projects", since), *codex_runs(codex, since)]
    rows = list(outcomes(state, since))
    if args.project:
        runs = [run for run in runs if key(args.project) in run["project"]]
        rows = [row for row in rows if key(args.project) in row["project"]]
    if not args.all:
        runs = [run for run in runs if run["agent"] in AGENTS]
    print(report(runs, rows))


if __name__ == "__main__":
    main()
