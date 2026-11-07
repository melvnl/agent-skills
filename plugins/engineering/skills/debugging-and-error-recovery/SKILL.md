---
name: debugging-and-error-recovery
description: Diagnoses defects from evidence: reproduce, minimize, form and test one hypothesis at a time, bisect, instrument temporarily, find the root cause and the same pattern elsewhere, and recover safely when a change breaks the build. Use for bugs, failing tests, production errors, flaky behavior, or when fix attempts aren't converging.
---

# Debugging and Error Recovery

## Overview

Most wasted debugging time comes from fixing a guess. This skill replaces guessing with a loop of observation, hypothesis, and test. It ends at a root cause backed by evidence, a fix at that cause, and a regression test that failed before the fix. It also covers recovery: getting back to a known-good state when a change has broken things, instead of stacking fixes on a red build.

## When to use

- A bug report, failing test, exception in logs, or incorrect output.
- Flaky or intermittent behavior.
- A fix-and-retry cycle isn't converging (a `loop-engineering` stop condition).
- The build or environment broke after a change.

**When not to use:** the gated bug-fix *process* (triage, approvals, report) is the factory `BUG_FIX` workflow. This skill is the diagnosis technique used inside it. Live production incidents follow `PRODUCTION_INCIDENT` first: stabilize, then diagnose.

## Inputs and context

1. The symptom exactly as observed: error text, stack trace, request or correlation id, timestamps, environment, frequency.
2. Expected behavior with its source (spec acceptance criterion, business rule). If no source defines it, don't decide it: ask.
3. Recent changes: `git log` on the affected paths, recent deploys, config and flag changes, dependency upgrades.
4. Logs and traces for the failing case, found by correlation id (`distributed-tracing-and-correlation`).
5. The code path and its tests.

## Process

1. **Read the whole error.** The first line of the traceback is rarely the cause; read to the innermost frame in project code and the `During handling of the above exception` chain.
2. **Reproduce** with the smallest setup: a failing test is best, then a script, then a documented manual sequence. If it can't be reproduced, gather more evidence (inputs, environment differences, timing) instead of guess-fixing.
3. **Minimize.** Strip inputs and steps until removing anything makes the failure disappear. The minimal case usually points at the cause.
4. **Hypothesize one cause at a time**, and write it down with the observation that would confirm or refute it ("If the bound is exclusive, score 600 returns manual_review").
5. **Test the hypothesis** with the cheapest decisive check: an assertion, a debugger breakpoint, a targeted log line, a query, a unit test. Record the result. Refuted hypotheses are progress; keep the list.
6. **Bisect when it used to work.** `git bisect` with the reproduction as the test (`git bisect run pytest path::test -x -q`) finds the introducing commit mechanically.
7. **Instrument temporarily** when the state is invisible. Mark temporary diagnostics (`# DEBUG(T-12): remove`) and remove them before finishing. Never log secrets or PII while debugging (`logging-security-and-redaction`).
8. **Find the root cause.** Ask why until you reach the defect, not a symptom ("score 600 misclassified" → "band uses `>`" → "rule table copied from a spec draft with exclusive bounds").
9. **Search for the same pattern elsewhere** (same function used elsewhere, same copy-pasted logic) and list the hits.
10. **Fix test-first**: a regression test that fails for the right reason, then the smallest fix at the root cause (`test-driven-development`). Re-run the original reproduction.

### Recovery when a change breaks things

- Stop adding changes. Identify the last known-good state (commit, or stash of the working tree).
- Return to green first: revert or stash the breaking change and confirm the suite passes, then reapply in smaller steps. Never start new work on a red build.
- Destructive recovery (`git reset --hard`, discarding someone's uncommitted work, dropping data) needs explicit approval.

### Usual suspects in backend code

Time zones and day boundaries; float arithmetic on money; inclusive vs exclusive bounds; N+1 queries and missing indexes; transaction boundaries (work done before commit, `on_commit` hooks, reads outside the transaction); races between workers (lost updates, duplicate processing); retries of non-idempotent operations; stale cache entries; encoding and collation (MySQL case-insensitive comparisons); configuration differences between environments; dependency upgrades changing defaults.

## Output

A diagnosis note (task notes, bug report, or implementation report):

```markdown
### Diagnosis
- Symptom: score 600 returned manual_review (req-8f2..., 2026-11-07 09:14 UTC)
- Reproduction: tests/eligibility/test_bands.py::test_score_600_approved (failed before fix)
- Hypotheses: H1 stale rule cache (refuted: cache disabled in test); H2 exclusive bound (confirmed)
- Root cause: rules.py:48 uses `score > 600`; BR-4 says >= 600
- Same pattern: rules.py:52 (manual band upper bound): fixed with test
- Fix: inclusive bounds + 4 boundary tests; suite 18 passed
- Temporary diagnostics removed: yes
```

## Verification

- [ ] The regression test failed before the fix and passes after; the reproduction no longer fails.
- [ ] The root cause is stated with evidence, not inferred from the fix working.
- [ ] Other occurrences of the pattern were searched and handled or listed.
- [ ] Temporary instrumentation is removed; no secrets or PII were logged while debugging.
- [ ] The relevant suites pass after the fix.

## Escalation

Ask when: expected behavior is undefined or disputed; the fix requires a data repair, migration, or security change (factory approval rules); the bug implies data was corrupted or exposed in production (incident handling); or evidence requires production access you don't have.

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "It's probably X; let me just change it." | If the change seems to work, you still don't know why. That's how bugs come back. |
| "Can't reproduce, so I'll add a defensive check." | That hides the symptom and the cause stays. Gather evidence first. |
| "Add a retry; it's flaky." | Flakiness has a cause (time, order, shared state, race). Retries hide it. |
