---
name: planning-and-task-breakdown
description: Breaks an approved spec and design into small, ordered, independently verifiable tasks with dependencies, acceptance-criteria coverage, test and instrumentation requirements, and explicit done-when conditions. Use when planning implementation of a feature, before coding a multi-step change, or when work needs to be resumable across sessions.
---

# Planning and Task Breakdown

## Overview

A good plan turns a feature into a sequence of steps that each leave the system working and each prove something. Small, ordered, verifiable tasks keep diffs reviewable, make progress measurable, and let any session (human or agent) resume from the task file instead of from memory. This skill produces that plan in the Software Factory `TASK_BREAKDOWN` format.

## When to use

- A feature spec (and design, for substantial work) is approved and implementation is next.
- A change will take more than one sitting, or touch more than one layer.
- Phase 4 of `PRD_TO_IMPLEMENTATION`; step 6 of the factory `NEW_FEATURE` workflow.

**When not to use:** the spec isn't approved yet → finish `specification-decomposition` / `acceptance-criteria-engineering` first. Trivial changes (factory trivial threshold) need no task file.

## Inputs and context

1. The approved `SPEC.md` (requirements, acceptance criteria) and `DESIGN.md` (components, data changes, contracts, error handling, observability plan).
2. The affected code and tests: what exists, what changes, where the seams are.
3. Project gates and commands (`engineering/DEVELOPMENT_GUIDE.md`).
4. Constraints: migrations needing staged rollout, feature flags, dependencies on other features or teams.

## Process

1. **Start from the acceptance criteria.** Every AC must end up covered by at least one task. List them.
2. **Find the walking skeleton.** The first task is the thinnest end-to-end slice that exercises the real path (one endpoint → service → persistence → response) with one AC passing. It surfaces integration problems early.
3. **Slice vertically after that.** Each subsequent task adds one behavior (one AC, or one boundary or failure case) through all the layers it needs. Avoid "all models, then all services, then all endpoints": nothing works until the end.
4. **Pull risk forward.** Unknowns (a new integration, a performance unknown, an ambiguous library behavior) become early **spike** tasks with a question and a time box, producing a decision, not production code.
5. **Separate what must be separate**:
   - Schema changes as their own tasks, using expand → migrate → contract when data or availability matters (`database-migrations`).
   - Refactors needed to make room, as their own tasks, before the behavior change (factory rule: no mixed refactor + feature diffs).
   - Contract changes (API, events) before their consumers.
6. **Size each task** to ≤ ~half a day and a reviewable diff (≲ 400 meaningful lines). Split anything larger.
7. **Specify each task completely**: what changes; dependencies (`T-n`); which FR/AC it covers; **tests** to add or extend (level and the AC they prove); **instrumentation** from the observability plan that belongs to this task; and a **done-when** that is verifiable by running something ("`pytest tests/eligibility -k threshold` passes; completion event visible in caplog test").
8. **Order by dependency**, then risk, then value. Mark tasks that can run in parallel.
9. **Add closing tasks**: regression run, observability verification, docs and state updates, implementation report.
10. ⏸ **Gate (substantial work):** present the plan with scope, non-goals, risks and open questions, and wait for approval.

## Output

`tasks/<F-ID>-<slug>.md` from `.factory/templates/TASK_BREAKDOWN.md`:

```markdown
| ID | Task | Depends on | Covers (FR/AC) | Done when | Status |
|---|---|---|---|---|---|
| T-1 | Walking skeleton: POST /v1/eligibility returns a decision for score 600 | — | FR-12, AC-1 | API test for AC-1 passes; completion event emitted | ⬜ |
| T-2 | Spike: bureau sandbox timeout behavior (1h box) | — | NFR-3 | decision note in Notes | ⬜ |
| T-3 | Manual-review band 550–599 | T-1 | BR-5, AC-2 | unit tests at 549/550/599/600 pass | ⬜ |
| T-4 | Bureau timeout fallback + WARNING event + metric | T-1, T-2 | AC-3 | integration test with stubbed timeout passes | ⬜ |
| T-5 | Regression, traceability, observability check, report | T-1..T-4 | all | gates green; trace_check 0 FAIL; report written | ⬜ |
```

Each row may carry a short detail block under the table for tests and instrumentation when the row gets too wide.

## Verification

- [ ] Every acceptance criterion is covered by at least one task.
- [ ] The first task is an end-to-end slice; no task is a horizontal layer with nothing verifiable.
- [ ] Every task has a runnable done-when, named tests, and its share of the instrumentation.
- [ ] No task mixes refactoring with behavior change; schema changes are separate and staged when needed.
- [ ] Dependencies form a DAG; parallelizable tasks are marked.
- [ ] Every task is ≤ ~half a day; larger ones were split.

## Escalation

Ask when: the plan reveals a spec gap or contradiction (fix the spec first, with approval); a task needs a new dependency, infrastructure, or a destructive migration; or the feature can't be sliced without a phase or contract decision.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'll do the models first, then wire it up." | Then nothing is verifiable until the end, and integration bugs arrive last. |
| "Tests come in the final task." | Then the done-when of every other task is unverifiable. Tests belong to the task that adds the behavior. |
| "Logging is a cleanup task." | Instrumentation belongs to the task that adds the operation, or it gets cut. |
