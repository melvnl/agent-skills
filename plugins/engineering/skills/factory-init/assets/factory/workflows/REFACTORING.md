# Workflow: Refactoring

> **Scope:** Project-agnostic.

## Purpose

Improve internal structure (readability, modularity, performance, testability) **without changing observable behavior**.

## Inputs

- Motivation (pain point, upcoming feature that needs it, measured performance issue).
- The code to be refactored, its tests, and its callers.
- Relevant architecture docs/ADRs.

## Outputs

- A short refactoring brief (in the task file or PR description): motivation, scope, invariants, plan.
- Refactored code in small commits; tests unchanged in expectation.
- Updated architecture docs/ADR if module boundaries or patterns change.

## Execution steps

1. **Identify the motivation.** State the concrete problem and how the refactor addresses it. "Cleaner" alone is not sufficient for a large refactor.
2. **Establish behavioral invariants.** List what must not change: outputs, side effects, persisted data formats, public contracts, performance bounds, error behavior.
3. **Define scope.** Name the files/modules in scope and explicitly out of scope. Estimate size; if > one reviewable change, split into stages that each leave the system working.
4. **Add or verify regression tests.** Ensure invariants are pinned by tests. Add characterization tests for untested behavior **before** changing code. Run them green.
5. **Refactor incrementally.** One mechanical transformation per step (rename, extract, move, inline, replace conditional…). Run tests after each step.
6. **Verify behavior is unchanged.** Full quality gates pass. No test expectation changed. For persisted data or contracts, verify compatibility explicitly.
7. **Update docs** if structure, boundaries, or conventions changed.

## Quality gates

- Tests green before the first change and after every step.
- **Zero changes to test expectations.** If an expectation must change, stop — that is a behavior change; split it out and follow `NEW_FEATURE.md` or `BUG_FIX.md`.
- No mixed commits (refactor + behavior change).

## Human approval required

- Refactors that cross module boundaries, change public contracts, change persisted data structures, or exceed a single reviewable change.
- Introducing or removing an architectural pattern (requires an ADR).
