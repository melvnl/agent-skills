# Workflow: Bug Fix

> **Scope:** Project-agnostic.

## Purpose

Fix a defect at its root cause with the smallest appropriate change, and prevent recurrence with a regression test.

## Inputs

- Bug report: observed behavior, expected behavior (or reference to the spec), steps to reproduce, environment, severity.
- The relevant spec / acceptance criteria.
- The relevant implementation and its tests.

## Outputs

- A failing-then-passing regression test.
- The fix.
- A short report (inline or `IMPLEMENTATION_REPORT.md` for significant bugs) including root cause.
- Updated spec if the bug revealed an ambiguous or missing requirement (with approval).

## Execution steps

1. **Triage.** Confirm severity: *critical* (data loss, security, isolation breach, app unusable), *high* (core journey broken), *medium* (workaround exists), *low* (cosmetic). Critical security/data issues: notify the human owner immediately.
2. **Reproduce.** Reproduce locally with minimal steps. If you cannot reproduce, gather more information — do not guess-fix.
3. **Define expected behavior.** Cite the spec/acceptance criterion. If the spec is silent or ambiguous, **ask** — do not invent the expected behavior.
4. **Write a regression test** at the lowest level that reproduces the bug. Run it and **observe it fail** for the right reason.
5. **Identify the root cause.** Trace from symptom to cause; ask "why" until you reach the defect, not a symptom. Check for the same pattern elsewhere and note it.
6. **Implement the smallest appropriate fix** at the root cause. No unrelated refactors (record them as follow-ups).
7. **Verify.** Regression test passes; full relevant test suites, lint, type-check, and build pass; manually re-run the original reproduction steps.
8. **Check blast radius.** Review callers of the changed code; confirm existing functionality remains intact.
9. **Report.** Root cause, fix, test added, verification results, related risks found.

## Quality gates

- Regression test failed before the fix and passes after.
- No existing test was modified to pass, unless the test itself was wrong (justified explicitly in the report).
- All quality gates in `TESTING_STANDARDS.md` § 10 pass.

## Human approval required

- Changing the expected behavior defined in a spec.
- Fixes involving data migrations, data repair of existing records, or security/authorization rules.
- Merge to the main branch.
