"""Checks agent_report.py against small Claude, Codex, and runs.jsonl fixtures."""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from agent_report import claude_runs, codex_runs, outcomes, report  # noqa: E402


def lines(path: Path, *entries: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(entry) + "\n" for entry in entries))


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        agent = root / "claude/-repo/session/subagents/agent-1"
        agent.with_suffix(".meta.json").parent.mkdir(parents=True)
        agent.with_suffix(".meta.json").write_text('{"agentType": "killall-agents:builder"}')
        usage = {"input_tokens": 10, "cache_creation_input_tokens": 20, "cache_read_input_tokens": 70, "output_tokens": 5}
        tool = {"type": "tool_use", "id": "t1", "name": "Bash", "input": {}}
        lines(
            agent.with_suffix(".jsonl"),
            {"type": "user", "timestamp": "2026-10-16T10:00:00Z", "message": {"content": "brief"}},
            {"type": "assistant", "timestamp": "2026-10-16T10:01:00Z", "message": {"id": "m1", "model": "claude-sonnet-5-5", "usage": usage, "content": [{"type": "text", "text": "hi"}]}},
            {"type": "assistant", "timestamp": "2026-10-16T10:01:00Z", "message": {"id": "m1", "model": "claude-sonnet-5-5", "usage": usage, "content": [tool]}},
            {"type": "user", "timestamp": "2026-10-16T10:03:00Z", "message": {"content": [{"type": "tool_result", "is_error": True, "content": "Exit code 1\nboom"}]}},
        )
        with agent.with_suffix(".jsonl").open("a") as file:
            file.write('{"type": "assist')
        [claude] = claude_runs(root / "claude", 0)
        assert (claude["agent"], claude["tokens_in"], claude["peak"], claude["tokens_out"], claude["tools"]) == ("builder", 100, 100, 5, 1), claude
        assert claude["minutes"] == 3 and claude["errors"] == ["Exit code 1: boom"], claude

        meta = {"payload": {"thread_source": "subagent", "agent_role": "grunt", "cwd": "/repo", "subagent_history_start_ordinal": 2}}
        lines(
            root / "codex/2026/10/16/rollout-a.jsonl",
            meta,
            {"ordinal": 1, "timestamp": "2026-10-16T09:00:00Z", "payload": {"type": "function_call"}},
            {"ordinal": 2, "timestamp": "2026-10-16T10:00:00Z", "payload": {"type": "custom_tool_call"}},
            {"ordinal": 3, "timestamp": "2026-10-16T10:02:00Z", "payload": {"type": "token_count", "info": {"total_token_usage": {"input_tokens": 50, "output_tokens": 4}, "last_token_usage": {"input_tokens": 30}}}},
        )
        lines(root / "codex/2026/10/16/rollout-b.jsonl", {"payload": {"thread_source": "user"}})
        [codex] = codex_runs(root / "codex", 0)
        assert (codex["agent"], codex["tokens_in"], codex["peak"], codex["tools"], codex["minutes"]) == ("grunt", 50, 30, 1, 2), codex

        log = root / "state/-repo/runs.jsonl"
        lines(
            log,
            {"time": "2026-10-16T10:00:00Z", "lane": "a", "agent": "reviewer", "round": 1, "result": "CHANGES"},
            {"time": "2026-10-16T10:30:00Z", "lane": "a", "agent": "reviewer", "round": 2, "result": "PASS"},
            {"time": "2026-10-16T10:40:00", "lane": "b", "agent": "reviewer", "round": 1, "result": "PASS"},
        )
        with log.open("a") as file:
            file.write("not json\n")
        rows = list(outcomes(root / "state", 0))
        assert len(rows) == 3, rows
        text = report([claude, codex], rows)
        assert "reviewer PASS on round 1: 1/2" in text and "mean rounds 1.5" in text, text
        assert "Exit code 1: boom" in text, text


if __name__ == "__main__":
    main()
