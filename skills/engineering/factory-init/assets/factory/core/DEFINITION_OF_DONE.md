# Definition of Done

> **Scope:** Project-agnostic. Projects may add stricter items in their own docs but may not remove these.

A feature, fix, or refactor is **done** only when every applicable item below is true. "Done except for…" is not done. Unmet items are either completed or explicitly converted into approved follow-up tasks.

---

## 1. Requirements

- [ ] All functional requirements in the spec are implemented (traceable by requirement ID).
- [ ] Non-functional requirements (performance, accessibility, responsiveness, offline behavior, etc.) are met or deviations are approved.
- [ ] No requirements were invented; any assumptions are documented in the implementation report.

## 2. Acceptance criteria

- [ ] Every acceptance criterion has been verified — by an automated test where feasible, otherwise by a documented manual check.
- [ ] Acceptance criteria were not changed without approval; any approved change is recorded in the spec.

## 3. Implementation

- [ ] Code follows `CODING_STANDARDS.md` and `ENGINEERING_STANDARDS.md`.
- [ ] Loading, empty, error, and success states handled for user-facing views.
- [ ] No unresolved `TODO`s without a task reference.
- [ ] No debug code, commented-out code, or unused dependencies.

## 4. Tests and quality gates

- [ ] New/changed behavior has unit and/or integration tests; critical journeys have E2E coverage.
- [ ] Bug fixes include a regression test.
- [ ] Lint passes.
- [ ] Type checking passes.
- [ ] Unit tests pass.
- [ ] Integration tests pass.
- [ ] E2E tests for affected critical journeys pass.
- [ ] Production build succeeds.
- [ ] All of the above were **actually run**, and results are reported in the implementation report.

## 5. Documentation

- [ ] Feature spec / technical design reflect what was actually built.
- [ ] Architecture, data model, contracts, or security docs updated if affected.
- [ ] ADR added for any significant decision.
- [ ] Developer-facing docs (setup, commands, env vars) updated if changed.
- [ ] Project status / task tracking updated.

## 6. Security and privacy

- [ ] Data isolation between users/tenants preserved (and tested, where multi-user data is involved).
- [ ] No secrets or personal data committed, logged, or exposed to clients.
- [ ] Input validated at trust boundaries.
- [ ] Sensitive data handling follows the project's security & privacy document.

## 7. Regressions

- [ ] No known critical or high-severity regressions.
- [ ] Known minor issues are documented as tasks with severity.
- [ ] Backward compatibility of persisted data and contracts preserved, or migration provided.

## 8. Review and approval

- [ ] Code review completed per `.factory/workflows/CODE_REVIEW.md`; blocking findings addressed.
- [ ] Implementation report written (`.factory/templates/IMPLEMENTATION_REPORT.md`).
- [ ] Human approval obtained where required (merges to main, destructive operations, contract/security changes, acceptance-criteria changes).
