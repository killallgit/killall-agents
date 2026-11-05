# Pending work

- [ ] Run the rendered Codex and opencode agent files in the real tools and confirm each loads with its pinned model. Only the Claude Code files are known to match what worked before.
- [ ] opencode agents have no tool restriction, so the planner and reviewer are not read-only there. Add one if opencode v2 documents a stable field.
- [ ] Try the reviewer on a different provider than the builder (a CLI call to another harness) and compare its findings with the same-provider reviewer.
- [ ] Context fit is the orchestrator's judgment; Pi does not report overflow. Add a check if real tasks overflow.
- [ ] Pi runs with full tools and no edit limits. Restrict it with a Pi extension if read-only jobs need enforcement, and give it a turn limit.
- [ ] Count the reviewer's findings as fixed or dismissed per lane, and retune it if most are dismissed.
