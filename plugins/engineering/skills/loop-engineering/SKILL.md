---
name: loop-engineering
description: Runs implementation as a disciplined loop per task: select, load context, implement, instrument, run targeted tests, evaluate, diagnose, fix, verify, checkpoint, with explicit stop conditions and persisted state. Use when implementing a planned task list, working autonomously over many steps, or when progress stalls in fix-retry cycles.
---

# Loop Engineering

## Overview

Autonomous implementation fails in predictable ways: drifting scope, retrying the same fix, skipping verification, and losing state when context runs out. Loop engineering makes each unit of work a closed loop with evidence at every turn, a checkpoint on disk, and rules for when to stop. Progress then survives interruptions, and failures are diagnosed instead of retried blindly.

## When to use

- Implementing tasks from a `tasks/<F-ID>-<slug>.md` breakdown (Phase 5 of `PRD_TO_IMPLEMENTATION`, step 7 of `NEW_FEATURE`).
- Any multi-step change where the agent works for a long stretch without a human in the loop.
- A fix-and-retry cycle isn't converging.

**When not to use:** there is no plan yet → `planning-and-task-breakdown`. Diagnosing one hard bug in depth → `debugging-and-error-recovery` (the loop calls it from step 7).

## Inputs and context

1. The task file and the selected task's row: covers, dependencies, done-when.
2. The spec and design sections that task covers (not the whole document).
3. The current repository state: `git status`, branch, and whether the build is green **before** starting.
4. The project's quality-gate commands (`engineering/DEVELOPMENT_GUIDE.md`, `CLAUDE.md`).
5. `tasks/STATUS.md`: last checkpoint, blockers.

## Process

```text
SELECT TASK -> LOAD CONTEXT -> IMPLEMENT -> INSTRUMENT -> RUN TARGETED TESTS -> EVALUATE
     ^                                                                            |
     |                                    pass ---------------------------------> VERIFY -> CHECKPOINT
     |                                    fail -> DIAGNOSE -> FIX -> (back to RUN TARGETED TESTS)
     +---------------------------------------- NEXT TASK <---------------------------+
```

1. **Select.** Choose the next task whose dependencies are done. Prefer finishing in-progress work and fixing a red build. Mark it 🟨 in the task file.
2. **Load context.** Read only what the task needs: its spec rows and ACs, the design section, the code and tests it touches and their callers. Confirm the build is green before changing anything; if it isn't, that becomes the task.
3. **Implement** the smallest change that satisfies the task, test first where practical (`test-driven-development`). Stay inside the task's scope; note unrelated findings as follow-ups.
4. **Instrument** what the observability plan assigns to this task (`structured-logging-and-instrumentation`), or note that none applies.
5. **Run targeted tests**: the tests for this task, then the module's suite. Read the actual output.
6. **Evaluate** against the task's done-when, not against "tests pass".
7. **On failure, diagnose before fixing.** State the observed failure, a hypothesis, and the check that would confirm it. Fix the cause, not the symptom. Never change a test's expectation to make it pass unless the test is demonstrably wrong (and then say so in the report).
8. **Verify** with the project's gates for the touched area (lint, typecheck, tests) and the done-when.
9. **Checkpoint** (below).
10. **Next task**, or stop if a stop condition holds.

### Stop conditions

Stop the loop and report (or escalate) when any of these is true:

| Condition | Action |
|---|---|
| The same test fails after **3** fix attempts with the same hypothesis | Stop fixing; switch to `debugging-and-error-recovery` with a new hypothesis, or escalate |
| Two consecutive iterations produced no measurable progress | Stop; summarize what was tried and ask |
| The fix requires changing the spec, acceptance criteria, contracts, or data model | Stop; that needs approval |
| The task grows beyond its scope or size estimate by ~2× | Stop; re-plan the task |
| A destructive or approval-required action is needed | Stop; ask |
| The build is red and you're about to start the next task | Don't. Fix or revert to green first |

### Checkpoint

After each task, and before any pause or expected context compaction, persist:

- Task file: status (✅ / 🟨 / ⛔ with reason), notes and decisions made.
- `tasks/STATUS.md`: active feature and task, **next action**, blockers, and last verification (date, command, result).
- Git: in projects where the owner authorized commits, one commit per completed task with only that task's files staged; otherwise leave the change uncommitted and say so.

A checkpoint must let a fresh session continue without this conversation (`context-engineering`).

## Output

Per task, a short loop record (in the task notes, or the reply for small work):

```markdown
T-3 ✅ Manual-review band 550–599
- Tests: tests/eligibility/test_bands.py (4 new) -> `pytest tests/eligibility -q`: 18 passed
- Gates: ruff check (0), mypy src/eligibility (0 errors)
- Instrumentation: none new (covered by T-1 completion event); verified rule_version field present
- Iterations: 2 (first failure: off-by-one at 599, inclusive bound; fixed in rule table)
- Next: T-4
```

## Verification

- [ ] Each completed task's done-when was checked by running something; outputs were read, not assumed.
- [ ] No test was skipped, deleted, or weakened to pass.
- [ ] The task file and STATUS reflect reality after every task.
- [ ] Stop conditions were honored; any stop is reported with what was tried.
- [ ] Each task's diff contains only that task's changes.

## Escalation

Covered by the stop conditions. In short: escalate on repeated failure without a new hypothesis, scope or contract change, required approvals, or missing information that only the owner has.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "One more quick try." | The third identical attempt is a loop, not engineering. Change the hypothesis or stop. |
| "I'll update the task file at the end." | The end is when context runs out. Checkpoint every task. |
| "Tests pass, so the task is done." | Done-when may require more: an event, a migration check, a contract. |
| "I'll start the next task and fix the build later." | Now two problems overlap, and neither is isolated. |
