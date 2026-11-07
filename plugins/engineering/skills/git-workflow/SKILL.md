---
name: git-workflow
description: Makes small, reviewable, Conventional Commits with explicit staging, a reviewed staged diff, no unrelated or pre-existing user changes, no secrets, and no history rewriting or pushing without approval. Use whenever committing, branching, preparing a PR, or recovering from a git mistake.
---

# Git Workflow

## Overview

Version history is how changes get reviewed, bisected, reverted, and explained later. Agents damage it in typical ways: `git add -A` sweeping in unrelated files, one giant commit, amending away someone's work, force-pushing. This skill keeps every commit small, intentional, and attributable, and it never takes an irreversible git action without approval.

## When to use

- Any commit, branch, or pull request.
- The owner asks for incremental commits per module or task.
- Something went wrong in git (wrong files committed, a failed hook, a bad merge).

**When not to use:** deciding *what* a change should contain → `planning-and-task-breakdown`. This skill is how it is recorded.

## Inputs and context

1. **Authorization**: has the owner asked for commits in this session or project? If not, prepare the change and ask before committing. Pushing always needs explicit approval.
2. The project's conventions: commit message format, branch naming, required trailers, PR template, protected branches (`CLAUDE.md`, `CONTRIBUTING.md`, recent `git log`).
3. `git status` and `git diff`, **before starting work**, to know which changes are pre-existing and not yours.

## Process

1. **Inspect first.** `git status --porcelain`, the current branch, and `git log --oneline -5`. Note pre-existing modifications; they are not part of your commits unless the owner says so.
2. **Branch** off the default branch for any non-trivial work, using the project's naming (e.g. `feat/F-07-eligibility`). Don't commit directly to the default branch unless that is the project's workflow.
3. **One meaningful change per commit**: a skill, a task, a migration, a fix. Refactors and behavior changes go in separate commits.
4. **Stage explicitly by path**: `git add -- path/a path/b`. Never `git add -A`, `git add .`, or `git commit -a`. If a file mixes your change with unrelated pre-existing edits, don't stage it wholesale: ask, or stage only your hunks non-interactively (`git diff path > p.patch`, edit the patch, `git apply --cached p.patch`).
5. **Review the staged diff**: `git diff --cached --stat` and `git diff --cached`. Check for unrelated files, debug code, generated artifacts, and **secrets or personal data**. If a secret was ever staged, unstage it and tell the owner (rotation may be needed).
6. **Validate before committing**: run the gates relevant to the change. Don't commit a red build unless the owner asked for a work-in-progress commit.
7. **Write a Conventional Commit**: `type(scope): summary` in the imperative, ≤ ~72 characters (`feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `build`, `ci`). The body explains *why* and anything a reviewer must know (migration steps, follow-ups). Add trailers the project requires.
8. **Commit, then inspect again**: `git status --porcelain` and `git log --oneline -1` to confirm exactly what was recorded and that nothing was left behind or swept in.
9. **If a pre-commit hook fails**, the commit did not happen. Fix the issue, re-stage, and make a **new** commit. Don't `--amend` (it would alter the previous commit), and don't bypass hooks with `--no-verify` unless the owner explicitly asks.

### Never without explicit approval

`git push` (any); `--force` / `--force-with-lease`; `commit --amend` on existing commits; `rebase` or squash of shared history; `reset --hard`; `clean -fd`; `checkout -- <path>` or `restore` that discards uncommitted work; `branch -D`; deleting tags; rewriting someone else's commits.

### Recovery

- Committed the wrong file and haven't pushed: `git reset --soft HEAD~1` keeps the changes staged. It is still a history change, so ask first in a shared branch.
- Lost work: `git reflog` shows previous HEAD positions; recover with a new branch at that point (`git branch rescue <sha>`).
- Bad merge in progress: `git merge --abort`.

### Pull requests

Title in Conventional Commit form; body with what changed and why, how it was verified (actual commands and results), risks and rollback notes, and linked spec/task ids. Follow the project's template if one exists.

## Output

Commits that each pass `git show --stat` review on their own, and a short report: commits created (hash + subject), what was left uncommitted and why, and confirmation of a clean (or explained) working tree.

## Verification

- [ ] `git status` was checked before and after each commit.
- [ ] Every staged path belongs to the commit's module; no pre-existing user changes were included.
- [ ] The staged diff was reviewed for secrets, debug code, and generated files.
- [ ] Messages follow Conventional Commits and explain why.
- [ ] No push, amend, force, rebase, or destructive command ran without approval.

## Escalation

Ask when: commits weren't authorized; a file mixes your changes with someone else's; a secret appears in history (a pushed secret must be rotated, not only removed); the branch has diverged from the remote; or a hook blocks the commit for reasons you can't fix within scope.
