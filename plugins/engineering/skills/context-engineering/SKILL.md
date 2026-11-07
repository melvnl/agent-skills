---
name: context-engineering
description: Manages what an agent loads and keeps in its context window: minimal targeted reading, bounded command output, persisted state instead of conversation memory, chunked processing of large documents, subagents for isolated exploration, and handoffs that survive compaction. Use for long tasks, large codebases or documents, multi-session work, or when context is running low.
---

# Context Engineering

## Overview

An agent's context window is its working memory, and it is finite. Filling it with whole files, long logs, and stale history makes reasoning worse and eventually forces compaction, which drops detail. Context engineering keeps the window focused on the current task and keeps durable state in files, so work stays accurate over long sessions and resumes cleanly in new ones.

## When to use

- Long or multi-session tasks: feature implementation, PRD analysis, migrations, audits.
- Large codebases or documents that can't be read whole.
- Before a pause, a handoff, or when context is getting full.
- After compaction or a session restart, to rebuild accurate state.

**When not to use:** a short, single-file change, where the overhead isn't worth it.

## Inputs and context

1. The task's goal and its done-when.
2. Where durable state lives: in a Software Factory repo, `tasks/STATUS.md`, the task file, specs; otherwise, a working notes file the user agrees to.
3. What tools exist for targeted reading: search (`grep`, `rg`, glob), line-range reads, symbol navigation.

## Process

### Load less, more precisely

1. **Search before reading.** Locate symbols, ids, and terms first (`grep -rn "evaluate_eligibility"`), then read only the relevant ranges.
2. **Read in order of authority**, stopping when you know enough: the entry point (`CLAUDE.md`) → state file → the spec rows and design section for this task → the code and tests you'll touch → their direct callers.
3. **Bound command output.** Filter test runs to failures (`pytest -q`, `-x`, `--tb=short`), page logs (`tail -n 200`, `grep` for the request id), cap listings (`| head -50`). Never paste unbounded output into the conversation.
4. **Summarize, then drop.** After reading a large file or log, write down the 3–5 facts that matter (with `file:line`) and work from those.

### Keep state in files, not in the conversation

5. **Decisions, findings, and progress go to disk as they happen**: task file notes, STATUS, the analysis document. The conversation is not a database.
6. **Large documents get a running index.** Process them section by section (e.g. a 200-page PRD), writing extracted results and a "sections done" list to the output file after each chunk, so an interruption loses at most one chunk.
7. **Re-verify after compaction or resume.** Summaries lose nuance. Re-read the state file and re-run `git status` and the relevant tests before trusting remembered facts (factory `RESUME_WORK`).

### Isolate exploration

8. **Delegate broad searches to a subagent** when only the conclusion matters ("find every place that publishes to the scoring queue"). The subagent's reading stays out of the main context; ask for paths, line numbers, and a short answer. Start it with a fresh context and a self-contained prompt.
9. Don't delegate work whose details you need to reason about directly, or tasks small enough to do inline.

### Hand off deliberately

10. **Write a handoff** before stopping mid-task or when context is nearly full (template below), into STATUS (factory) or the agreed notes file.

## Output

A handoff block that lets a fresh session continue without this conversation:

```markdown
## Handoff 2026-11-07 16:40
- Goal: F-07 automatic eligibility decision (spec: specs/F-07-eligibility/SPEC.md)
- Done: T-1, T-2 (✅, verified: `pytest tests/eligibility -q` 14 passed)
- In progress: T-3 manual-review band; rule table edited (src/eligibility/rules.py:40-62); boundary tests not yet written
- Next action: write tests for 549/550/599/600 in tests/eligibility/test_bands.py, then run the module suite
- Decisions: inclusive bands confirmed by owner (BR-5); see task notes
- Open: Q-3 bureau sandbox access (blocks T-4)
- Don't: change AC-2 wording (approved); touch migrations (T-6, needs approval)
```

## Verification

- [ ] Every fact the next step depends on is in a file, not only in the conversation.
- [ ] The handoff names the exact next action and how to verify the last completed step.
- [ ] After resuming, state was re-verified against git and tests before continuing.
- [ ] No unbounded output was pulled into context.

## Escalation

Ask when the task can't be split into chunks that fit (it may need re-scoping), or when durable state has no agreed home in a non-factory repo (agree on a notes file before writing one).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'll read the whole module to be safe." | You'll reason worse about the 30 lines that matter. Search, then read ranges. |
| "I remember what we decided." | After compaction you remember a summary. Write decisions down when they happen. |
| "The full log might have something useful." | Grep it for the request id and the error, then read around the hits. |
