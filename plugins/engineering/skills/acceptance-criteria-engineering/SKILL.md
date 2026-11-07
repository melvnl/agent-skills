---
name: acceptance-criteria-engineering
description: Writes and reviews acceptance criteria as atomic, testable Given/When/Then statements that cover boundaries, invalid input, permissions, state, dependency failures, idempotency, time, money, observability and audit, each mapped to requirements and a verification method. Use when writing or reviewing a spec's acceptance criteria, or when "done" is unclear.
---

# Acceptance Criteria Engineering

## Overview

Acceptance criteria are the contract a feature is verified against. Vague ones ("works correctly", "is fast") let defects pass review and turn sign-off into opinion. This skill produces criteria that are observable, unambiguous, traced to requirements, and systematically cover the cases where production defects actually come from: boundaries, permissions, state, failures, retries, and time.

## When to use

- Writing section 8 (*Acceptance criteria*) and section 9 (*Edge cases*) of a feature spec.
- Reviewing a spec before approval, or a PR against its spec.
- Anyone asks "how do we know this is done?".

**When not to use:** deciding *what* the requirements are → `prd-analysis` / `specification-decomposition`. Writing the tests themselves → `test-driven-development`.

## Inputs and context

1. The spec's functional and non-functional requirements with ids, and the PRD business rules (`BR-n`) they rely on.
2. The domain model: actors and permissions, entity states and allowed transitions.
3. External dependencies and their failure modes (from the design, when one exists).
4. Project conventions for money, time zones, and identifiers (`engineering/` docs).
5. The observability plan and audit requirements, when the feature has them.

## Process

1. **For each requirement**, write the happy-path criterion first: `Given <precondition>, When <action>, Then <observable outcome>`.
2. **Expand coverage** with the matrix below. Add a criterion for each category that *applies*; mark the rest not applicable in the review, so absence is deliberate.
3. **Make each criterion observable.** The *Then* names something a test or a person can check: a response code and body field, a persisted state, a published message, an emitted event, a metric, a notification. Never internal implementation ("calls `ScoreService`").
4. **Make it unambiguous.** Exact values and inclusivity ("score = 600 is eligible"), units and currency, time zone, ordering, and which actor.
5. **Keep it atomic.** One behavior per criterion. "And" in a *Then* is fine for one outcome's facets; two independent behaviors become two criteria.
6. **Trace and assign verification.** Each criterion cites the requirement ids it verifies and a method: *Unit*, *Integration*, *E2E*, or *Manual* (with the reason automation isn't feasible).
7. **Run the review checklist** (below). Rewrite failures; turn unknowns into open questions in the spec rather than guessing values.
8. After approval, criteria change only through the spec's change log with approval (Software Factory rule).

### Coverage matrix

| Category | Ask | Example *Then* |
|---|---|---|
| Boundaries | exactly at, just below, just above each threshold; empty, zero, max | score 599 → manual review; score 600 → approved |
| Invalid input | malformed, missing, out of range, wrong type | 422 with `error_code=INVALID_INCOME`; nothing persisted |
| Permissions | each actor that must *not* be able to act; cross-tenant / other-user access | 403; no state change; attempt logged at WARNING |
| State | action in each disallowed state | rejecting an already-approved application → 409, state unchanged |
| Dependency failure | timeout, error, malformed response from each dependency | bureau timeout → fallback decision recorded with `reason=BUREAU_TIMEOUT` |
| Idempotency and duplicates | same request twice, retried message, double click | second submission returns the first result; one record exists |
| Concurrency | two actors or workers on the same record | one update wins; the other gets 409; no lost update |
| Time | day boundaries, time zones, expiries, clock skew | offer created 23:59 WIB expires at 23:59 WIB next day |
| Money and precision | rounding, currency, minimum units | amounts stored as exact decimals; rounding half-even to 2 places |
| Observability | the operation's completion and failure signals | completion event carries `request_id`, `status`, `duration_ms`; no PII fields |
| Audit | decisions and changes that must be reconstructable | decision record stores inputs snapshot, rule version, actor |
| NFRs | measurable target, load profile, how measured | p95 < 300 ms at 50 rps in the staging load test |

## Output

The spec's acceptance criteria table and edge cases:

```markdown
| ID | Given | When | Then | Verifies | Method |
|---|---|---|---|---|---|
| AC-1 | an application with bureau score 600 | eligibility is evaluated | status is `approved` and the decision record stores rule_version | FR-12, BR-4 | Unit |
| AC-2 | an application with bureau score 599 | eligibility is evaluated | status is `manual_review` | BR-5 | Unit |
| AC-3 | the bureau call times out | eligibility is evaluated | a fallback decision with reason `BUREAU_TIMEOUT` is stored and a WARNING event is emitted | FR-12, NFR-3 | Integration |
```

## Verification (review checklist)

- [ ] Every requirement in the spec has at least one criterion; every criterion cites a requirement.
- [ ] Every *Then* is observable and free of implementation detail.
- [ ] No vague words (*fast, correct, properly, appropriate, user-friendly, secure*) without a measurable definition.
- [ ] Every threshold has explicit inclusivity; every quantity has a unit; every date rule has a time zone.
- [ ] Each applicable coverage category has a criterion; non-applicable ones are noted.
- [ ] Each criterion has a verification method; *Manual* ones say why.
- [ ] Unknown values are open questions, not guesses.

## Escalation

Ask the owner when: a threshold, limit, or business outcome isn't specified; two requirements imply conflicting outcomes for the same case; a criterion would change approved behavior; or an NFR target is missing (targets are product decisions).

## Common rationalizations

| Rationalization | Reality |
|---|---|
| "Edge cases are implied." | Implied cases are untested cases. Write them, or mark them not applicable. |
| "The happy path is enough for now." | Production defects come from the other rows of the matrix. |
| "I'll pick a sensible threshold." | That's inventing a requirement. Ask. |
