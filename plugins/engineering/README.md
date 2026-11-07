# melvin-engineering

Spec-driven engineering core: the Software Factory and the skills for turning requirements into verified, incremental changes.

## Skills

### Software Factory

- **[factory-init](skills/factory-init/SKILL.md)**: Bootstrap (or `--verify`) the `.factory/` software factory in a repository.
- **[factory-router](skills/factory-router/SKILL.md)**: Classify, size, and route each request in a factory repo to its workflow.

`skills/factory-init/assets/factory-router.SKILL.md` is a bundled copy of `skills/factory-router/SKILL.md`, installed into target repos. Edit the source and copy it over; `scripts/validate.py` fails on drift.

### Specification and planning

- **[prd-analysis](skills/prd-analysis/SKILL.md)**: Analyze a large or AI-generated PRD: extract requirements with source references, surface contradictions, ambiguities, duplicates, and missing NFRs.
- **[specification-decomposition](skills/specification-decomposition/SKILL.md)**: Turns analyzed requirements into stable ids, domain groups, a feature catalog, and atomic feature specs with traceability.
- **[acceptance-criteria-engineering](skills/acceptance-criteria-engineering/SKILL.md)**: Writes and reviews atomic, testable Given/When/Then criteria covering boundaries, permissions, state, failures, idempotency, time, money, observability and audit.
- **[requirement-traceability](skills/requirement-traceability/SKILL.md)**: Keeps the requirement → feature → AC → task → code → test chain intact, with a deterministic checker for untraced or dangling ids.
- **[planning-and-task-breakdown](skills/planning-and-task-breakdown/SKILL.md)**: Breaks an approved spec into small, ordered, verifiable tasks with AC coverage, test and instrumentation requirements, and done-when conditions.

### Engineering execution

- **[loop-engineering](skills/loop-engineering/SKILL.md)**: Runs each task as a closed loop (implement, instrument, test, diagnose, fix, verify, checkpoint) with explicit stop conditions and persisted state.
- **[context-engineering](skills/context-engineering/SKILL.md)**: Keeps the context window focused: targeted reading, bounded output, state in files, chunked large documents, subagent exploration, compaction-proof handoffs.
- **[test-driven-development](skills/test-driven-development/SKILL.md)**: Red-green-refactor from the acceptance criteria: each test observed failing for the right reason, minimal change, refactor under green. Python/pytest aware.
- **[debugging-and-error-recovery](skills/debugging-and-error-recovery/SKILL.md)**: Diagnoses from evidence: reproduce, minimize, one hypothesis at a time, bisect, root cause, same pattern elsewhere, and safe recovery to green.
- **[git-workflow](skills/git-workflow/SKILL.md)**: Small Conventional Commits with explicit staging and reviewed diffs; no unrelated changes, secrets, history rewrites or pushes without approval.
