# Workflow: Resume Work

> **Scope:** Project-agnostic. Use at the start of any session that continues prior work (new agent session, after a break, or after another contributor's changes).

## Purpose

Rebuild an accurate picture of the project's state from the repository — not from memory — and pick the next actionable task without repeating or contradicting completed work.

## Inputs

- The repository (code, docs, git history if available).
- The project's status file (conventionally `tasks/STATUS.md`) and task breakdowns.
- Specs, designs, and implementation reports.

## Outputs

- A short state summary: phase, completed, in progress, pending, blocked.
- The selected next task, with the reason it was chosen.
- Updated status/task files if they were stale.

## Execution steps

1. **Read the entry point** (`CLAUDE.md` or equivalent) and the status file.
2. **Inspect the actual repository state.**
   - Version control: current branch, uncommitted changes, recent commits.
   - Directory structure and recently modified files.
   - Do not trust the status file blindly — confirm claims against code and tests.
3. **Review specs, designs, and task breakdowns** for the current phase. Note each task's status.
4. **Run the quality gates** (if code exists) to learn the true health of the build. Record actual results.
5. **Classify work:**

   | Status | Evidence required |
   |---|---|
   | Done | Code + tests exist, gates pass, implementation report exists |
   | In progress | Partial code, or task marked in progress, or uncommitted changes |
   | Pending | Specified but not started |
   | Blocked | Depends on an open question, approval, or external dependency (name it) |

6. **Reconcile discrepancies.** If docs say done but code/tests disagree (or vice versa), report the discrepancy; do not silently "fix" status.
7. **Determine the next actionable task:** prefer (a) finishing in-progress work, (b) fixing a red build, (c) the next unblocked pending task in roadmap order. Never redo a task verified as done.
8. **Update the status file** if it was stale, then proceed with the applicable workflow (`NEW_FEATURE.md`, `BUG_FIX.md`, …).

## Quality gates

- State summary is based on inspected evidence, and any unverified claims are labeled as such.
- The selected task is unblocked and its spec exists (or writing the spec *is* the task).

## Human approval required

- Resolving blocked items that depend on human decisions.
- Discarding or reverting someone else's uncommitted or in-progress work.
