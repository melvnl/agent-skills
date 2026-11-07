# Testing Standards

> **Scope:** Project-agnostic. Each project declares its concrete test tools and commands in its development guide.

## Non-negotiable rules

1. Every business logic function has unit tests.
2. Every API endpoint / service contract has integration tests.
3. Every database / persistence operation is tested against a real or faithful in-memory implementation.
4. Critical user journeys have end-to-end (E2E) tests.
5. **Never remove, skip, or disable existing tests to make a build pass.**
6. **Never modify expected values just to satisfy tests.** If an expectation is wrong, explain why in the change description and get it reviewed.
7. **Never claim tests pass without running them** and observing the result.

---

## 1. Test pyramid

| Level | Purpose | Speed target | Typical share |
|---|---|---|---|
| Unit | Pure logic: calculations, validation, state transitions, mapping | ms per test | Most tests |
| Integration | A module with its real collaborators: persistence adapter + store, service + schema validation, API handler + DB | < 1 s per test | Moderate |
| E2E | Full user journeys through the real UI/API | seconds per test | Few, high value |

## 2. Unit testing

- Test **behavior through the public interface**, not private implementation details.
- One behavior per test; test name states the behavior: `returns zero remaining when consumption equals target`.
- Structure: **Arrange / Act / Assert**.
- Cover: happy path, boundaries (0, 1, max, empty, exactly-at-threshold), invalid input, and each branch of business rules.
- Deterministic: no real clock, randomness, or network — inject them.

## 3. Integration testing

- Exercise real boundaries: storage adapters against a real or faithful in-memory engine, request handlers with schema validation, data-layer authorization rules against a real database where feasible.
- **Authorization/isolation tests are mandatory** for multi-user data: assert that user A cannot read or write user B's records.
- Reset state between tests (see Test isolation).

## 4. End-to-end testing

- Cover each **critical user journey** defined in the product docs (the project lists them explicitly).
- Use stable selectors (accessible roles/labels or dedicated test IDs), never CSS structure.
- Run against a production-like build.
- Keep E2E tests independent; each creates the data it needs.

## 5. Regression testing

- Every bug fix adds a test that **fails before the fix and passes after** (see `.factory/workflows/BUG_FIX.md`).
- Name or tag regression tests with the bug reference.
- Before a refactor, ensure behavior is pinned by tests (characterization tests if needed).

## 6. Coverage expectations

Coverage is a signal, not a goal. Defaults (a project may raise them):

| Code category | Line/branch coverage expectation |
|---|---|
| Domain / business logic | ≥ 90% lines, all business-rule branches covered |
| Application services, adapters | ≥ 70% |
| UI components | Behavior-tested for interactive components; snapshot-only tests do not count |
| Generated code, config, type-only files | Excluded |

A change must not reduce coverage of the modules it touches without justification.

## 7. Test data and fixtures

- Use **builders/factories** with sensible defaults (`buildOrder({ total: 0 })`) instead of large hand-written literals.
- Fixtures are minimal, realistic, and **synthetic** — never real personal data.
- Fixed dates/times in tests use explicit timezones.
- Shared fixtures live in one place per module; do not copy-paste fixture blobs.

## 8. Mocking policy

| Mock | Do not mock |
|---|---|
| Network calls to third-party services | The code under test |
| Clock, randomness, UUID generation (inject) | Pure domain functions |
| Slow or non-deterministic external systems | Your own persistence layer in integration tests (use a real/in-memory engine) |
| Paid APIs (AI/ML providers, payments) | Types/schemas |

- Prefer **fakes** (working lightweight implementations) over call-recording mocks.
- Mocks assert on outcomes, not on incidental call order.
- A test that mocks everything tests nothing; if setup is mostly mocks, test at a higher level.

## 9. Test isolation

- Tests do not depend on execution order or on each other's data.
- Each test sets up and tears down its own state (fresh in-memory DB, cleared storage, reset mocks).
- No shared mutable globals between tests.
- Tests can run in parallel unless explicitly marked otherwise with a reason.
- Flaky tests are bugs: quarantine with a tracking task and fix promptly — do not silently retry.

## 10. Quality gates

A change cannot be merged unless all gates pass. Projects map each gate to a concrete command in their development guide.

| Gate | Required |
|---|---|
| Formatting & lint | Zero errors |
| Type check | Zero errors |
| Unit tests | All pass |
| Integration tests | All pass |
| E2E tests (critical journeys) | All pass before release / phase completion; on every change if fast enough |
| Build | Production build succeeds |
| Coverage | Meets § 6 for touched modules |
| Security | No new high/critical dependency vulnerabilities |
