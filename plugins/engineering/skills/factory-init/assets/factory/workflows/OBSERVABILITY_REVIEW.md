# Workflow: Observability Review

> **Scope:** Project-agnostic. Applies to any change that adds or modifies backend behavior: endpoints, services, consumers, jobs, external integrations, error handling, or logging.

## Purpose

Confirm, independently of the implementer, that a change will be debuggable in production: important operations are observable, correlation survives every boundary, logs carry no secrets or personal data, and signals are worth their volume and cost.

## Entry conditions

- The change is implemented and its own tests pass.
- The diff range and the spec or task are known.
- The reviewer is not the implementer.

## Inputs

- The diff and its base.
- The spec and the design's *Observability plan* (`templates/TECHNICAL_DESIGN.md` § 8), when one exists.
- The project's logging, correlation, and metrics conventions (development guide).

## Outputs

- A findings list: severity, `file:line`, finding, failure scenario, suggested fix (severity scale from `CODE_REVIEW.md`).
- The list of operations checked, what is confirmed good, and what couldn't be verified.
- The *Instrumentation* section of the implementation report, confirmed or corrected.

## Execution steps

1. **Learn the conventions** before judging: logger library or wrapper, formatter, how correlation ids reach records, metric naming.
2. **List the operations** the diff changes, including error and fallback paths.
3. **Check signals per operation**: completion with outcome and duration, failures with error codes, retries, fallbacks, state transitions. Compare with the observability plan. Something already emitted by middleware or tracing is not a gap.
4. **Check each log call**: necessary, structured (constant event, context in fields), correct level (business rejections are not errors), concise, not duplicated across layers, no whole objects, bodies, or headers.
5. **Check sensitive data**: no secrets in any form; no raw personal or financial identifiers; exception text sanitized. Never quote a sensitive value in the review.
6. **Check correlation** at every boundary the diff touches: inbound requests, outbound calls, published and consumed messages, background tasks, thread and task hand-offs.
7. **Check metrics**: correct type and unit; labels bounded (no ids, raw paths, or messages).
8. **Check audit reliance**: decisions or financial changes recorded only as log lines are a finding; they need durable records.
9. **Confirm every finding** against the code (formatter configuration, middleware, data origin) before reporting it. Report over-instrumentation as well as gaps.
10. **Decide**: approve, approve with follow-ups, or request changes.

If the `observability-code-review` skill or the `observability-engineer` agent is available, use it for steps 2–9.

## Quality gates

| Gate | Passes when |
|---|---|
| Coverage | Every changed operation has been checked and listed |
| Safety | No Blocker sensitive-data findings open |
| Correlation | Every boundary in the diff propagates the project's correlation ids, or the gap is an approved follow-up |
| Evidence | Every finding has a location, a failure scenario, and a fix |

## Exit conditions

- Verdict recorded with the findings list; Blockers fixed and re-reviewed, or escalated.

## Human approval required

- Accepting an open Blocker or Major finding as a known risk.
- Any change to logging conventions, retention, or observability tooling.
- Immediate escalation (not a review comment) when sensitive data may already be in production logs.
