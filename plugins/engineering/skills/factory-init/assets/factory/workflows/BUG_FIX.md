# Workflow: Bug Fix

> **Scope:** Project-agnostic.

## Purpose

Fix a defect at its root cause with the smallest appropriate change, and prevent recurrence with a regression test.

## Entry conditions

- Behavior differs from what a spec, acceptance criterion, or business rule defines, **or** a failure needs investigation to decide whether it is a bug.
- For a live production problem, `PRODUCTION_INCIDENT.md` runs first (mitigate, then diagnose); this workflow fixes the cause.

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
2. **Investigate.** Read the whole error and traceback; collect evidence by correlation id (logs, traces, metrics) and recent changes (commits, deploys, configuration, flags). Reproduce locally with minimal steps, then minimize the case. If you cannot reproduce, gather more information — do not guess-fix. Test hypotheses one at a time and record each as confirmed or refuted; use bisection when the behavior used to work.
3. **Define expected behavior.** Cite the spec/acceptance criterion. If the spec is silent or ambiguous, **ask** — do not invent the expected behavior.
4. **Write a regression test** at the lowest level that reproduces the bug. Run it and **observe it fail** for the right reason.
5. **Identify the root cause.** Trace from symptom to cause; ask "why" until you reach the defect, not a symptom. Check for the same pattern elsewhere and note it. Remove any temporary diagnostics before finishing, and never log secrets or personal data while debugging.
6. **Implement the smallest appropriate fix** at the root cause. No unrelated refactors (record them as follow-ups).
7. **Verify.** Regression test passes; full relevant test suites, lint, type-check, and build pass; manually re-run the original reproduction steps.
8. **Check blast radius.** Review callers of the changed code; confirm existing functionality remains intact.
9. **Check observability.** If the bug was hard to detect or diagnose, add the missing signal (an error event, a metric, a correlation id) or record why not.
10. **Report.** Symptom, evidence, hypotheses tested, root cause, fix, test added, verification results, related risks found.

## Quality gates

- Regression test failed before the fix and passes after.
- No existing test was modified to pass, unless the test itself was wrong (justified explicitly in the report).
- All quality gates in `TESTING_STANDARDS.md` § 10 pass.

## Exit conditions

- Regression test passes, gates pass, report written; **or** investigation concluded that behavior matches the spec (then it is a requirement question, routed as a documentation change with approval).

## Human approval required

- Changing the expected behavior defined in a spec.
- Fixes involving data migrations, data repair of existing records, or security/authorization rules.
- Merge to the main branch.
