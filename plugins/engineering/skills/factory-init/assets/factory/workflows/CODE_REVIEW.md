# Workflow: Code Review

> **Scope:** Project-agnostic. Applies to human and AI reviewers, and to an agent's self-review before handing off.

## Purpose

Catch defects, risks, and maintainability problems before they reach the main branch, and confirm the change satisfies its specification.

## Inputs

- The diff.
- The spec / bug report / refactoring brief the change implements.
- The technical design and relevant project docs.
- Verification output (test, lint, type-check, build results).

## Outputs

A list of findings, each with: **severity**, location (`file:line`), the problem, a concrete failure scenario, and a suggested fix.

| Severity | Meaning | Merge? |
|---|---|---|
| **Blocker** | Incorrect behavior, data loss, security/isolation flaw, spec violation, broken build | Must fix |
| **Major** | Likely bug in edge case, missing tests for new behavior, architectural violation | Fix or get explicit approval to defer |
| **Minor** | Maintainability, naming, small inefficiency | Author's discretion |
| **Nit** | Style preference not enforced by tooling | Optional |

## Execution steps

1. **Understand intent.** Read the spec/acceptance criteria first, then the diff.
2. **Check verification evidence.** Were quality gates actually run? Are results included? If not, request them.
3. **Review against the checklist below**, from highest risk to lowest.
4. **Write findings** with concrete scenarios — "this breaks when X is empty because Y", not "this looks wrong".
5. **Decide:** approve, approve with follow-ups, or request changes.

## Review checklist

### Correctness
- [ ] Implements every requirement/acceptance criterion in scope — and nothing unrequested.
- [ ] Edge cases: empty, zero, null, max, boundary equality, duplicates, concurrency, timezones/dates, unit conversions, rounding.
- [ ] Error paths handled per `ENGINEERING_STANDARDS.md` § 5.

### Business logic
- [ ] Domain rules match the spec exactly (thresholds, inclusivity of boundaries, units).
- [ ] Business logic lives in the domain layer, not in UI or adapters.

### Security & privacy
- [ ] Authorization enforced at the server/data layer; per-user/tenant isolation preserved.
- [ ] Input validated at trust boundaries; output encoded.
- [ ] No secrets, tokens, or personal data in code, logs, fixtures, or client bundles.

### Performance
- [ ] No unbounded queries/loops over user data; no N+1 patterns.
- [ ] Client bundle impact considered for new dependencies.
- [ ] Expensive work not repeated on every render/request without need.

### Maintainability
- [ ] Follows `CODING_STANDARDS.md`: naming, modularity, type safety, no unnecessary abstractions.
- [ ] Docs updated where behavior, architecture, or contracts changed.

### Test quality
- [ ] New behavior covered; tests assert outcomes, not implementation details.
- [ ] Bug fixes include a regression test.
- [ ] No tests disabled/skipped/weakened; no expectation changes without justification.
- [ ] Tests are deterministic and isolated.

### Architecture consistency
- [ ] Respects module boundaries and dependency direction.
- [ ] Consistent with ADRs; new significant decisions have an ADR.

### Potential regressions
- [ ] Callers of changed code still behave correctly.
- [ ] Persisted data and contracts remain backward compatible (or migration provided).

## Quality gates

- No open Blocker findings.
- Major findings fixed or explicitly deferred with human approval and a task reference.

## Human approval required

- Final approval to merge to the main branch is given by a human.
