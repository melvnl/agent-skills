---
name: test-driven-development
description: Drives implementation through red-green-refactor: a test list from the acceptance criteria, one failing test at a time observed failing for the right reason, the minimal change to pass, then refactoring under green tests. Python/pytest aware. Use when implementing a feature or bug fix, adding behavior to existing code, or pinning legacy behavior before changing it.
---

# Test-Driven Development

## Overview

Writing the test first forces the behavior to be specified before it is built, proves the test can fail, and leaves a regression suite as a by-product. Each cycle is small: one failing test, the least code that passes it, then cleanup while everything stays green. This skill is the procedure. The Software Factory's `TESTING_STANDARDS` defines the rules (levels, coverage, mocking policy) that it follows.

## When to use

- Implementing a task with acceptance criteria, or a bug fix (the regression test comes first).
- Adding behavior to existing code.
- Before refactoring or changing legacy code with weak tests (write characterization tests first).

**When not to use:** a time-boxed spike whose code will be thrown away. Throwaway UI exploration. Both still need tests before anything ships.

## Inputs and context

1. The acceptance criteria and business rules the task covers.
2. The project's test stack and conventions: runner (`pytest`, `unittest`, Django's test runner), layout, fixtures/factories, how the database is handled, the plugins in use. Read two existing tests in the same area and match them.
3. The commands to run a single test and a module's suite.
4. Language and library versions: don't use pytest or Django testing features the project's versions lack.

## Process

1. **Write a test list** from the task's acceptance criteria: happy path, boundaries, invalid input, permissions, state, failures (the `acceptance-criteria-engineering` matrix). Order it simplest first.
2. **Red.** Write one test for the next item. Name it as the behavior (`test_score_599_goes_to_manual_review`) and cite the criterion (`# F-07 AC-2`). Run it and **watch it fail for the right reason**: an assertion about the missing behavior, not an import error, a typo, or a fixture failure. A test that has never failed proves nothing.
3. **Green.** Write the minimal code that makes it pass. Hard-coding is acceptable briefly; the next test forces generalization.
4. **Run the module's suite**, not just the new test.
5. **Refactor** names, duplication, and structure in both code and tests while green. Run the suite after each step. Never refactor while red.
6. **Repeat** until the list is empty. Add items you discover to the list instead of chasing them immediately.
7. **Choose the test level deliberately**: pure business rules → unit tests without I/O; persistence, schemas, and API handlers → integration tests against a real or faithful store; critical journeys → a few end-to-end tests. Mock only what the factory mocking policy allows (third-party network, clock, randomness).
8. **For legacy code**, first pin current behavior with characterization tests (assert what it *does*, even if odd), then change it test-first.

Python patterns (parametrized boundaries, time injection, factories, Django and FastAPI test setup, asserting logs): [references/python-testing.md](references/python-testing.md).

## Output

- Tests that cite their acceptance criteria, and the implementation that passes them.
- A test note in the task record: tests added (level, criterion), the red observation for each new behavior ("failed with `AssertionError: 'approved' != 'manual_review'`"), and the final suite result.

## Verification

- [ ] Each new behavior's test was seen failing for the right reason before the implementation.
- [ ] The module's suite passes; the command and result are recorded.
- [ ] Every acceptance criterion in scope has a test, or is marked Manual with a reason.
- [ ] No existing test was deleted, skipped, or weakened. Any changed expectation is justified in the report.
- [ ] Tests are deterministic: no real clock, randomness, network, or order dependence.

## Escalation

Ask when: the expected behavior isn't specified (the test can't be written without inventing it); a needed test requires infrastructure that doesn't exist (a test database, a sandbox); or an existing test conflicts with the spec (which one is right is an owner decision).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "I'll write the tests after; same result." | Tests written after the code tend to assert what the code does, not what it should do, and are never seen failing. |
| "This is too simple to test." | Simple code with a wrong boundary is the classic production bug. |
| "Mock the repository to keep it fast." | The factory policy says use a real or faithful store for persistence tests. Mocks hide query bugs. |
| "The test is flaky; add a retry." | Flakiness is a bug in the test or the code. Find the nondeterminism. |

## References

- [references/python-testing.md](references/python-testing.md): pytest and unittest patterns for boundaries, time, factories, Django, FastAPI, logs, and characterization tests.
