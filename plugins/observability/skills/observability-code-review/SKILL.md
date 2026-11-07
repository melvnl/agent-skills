---
name: observability-code-review
description: Reviews a backend diff for observability quality: missing or redundant logs, lost correlation context, wrong severity, sensitive data in logs, unstructured or verbose messages, missing error context or duration, unbounded metric labels. Use when reviewing a change, PR or branch that touches backend code, or when asked for an observability review.
---

# Observability Code Review

## Overview

A change can pass every test and still be undebuggable in production, or leak a token into the log platform. This review checks the diff for whether its signals will explain failures, stay correlated across boundaries, stay safe, and stay affordable. It is usable on its own or as part of a broader code review, and it reports *over*-instrumentation as readily as gaps.

## When to use

- Reviewing a PR, branch, or diff that changes endpoints, services, consumers, jobs, external integrations, error handling, or logging.
- The Software Factory `CODE_REVIEW` or observability-review workflow reaches its observability step.
- Asked "is this observable?", "check the logging", or "review instrumentation".

**When not to use:** designing observability for a feature from scratch → `observability-engineering`. Writing the instrumentation yourself → `structured-logging-and-instrumentation`.

## Inputs and context

1. **The diff and its base**: `git diff <base>...HEAD` (ask for the base if unclear; default to the merge base with the main branch).
2. **The spec or task**, and the design's *Observability plan* if one exists: the review checks the implementation against it.
3. **The project's logging conventions** (if unknown, discover them as `structured-logging-and-instrumentation` describes): library, wrapper, formatter, how context is attached, event and field naming.
4. **What already observes the code**: middleware access logs, framework logs, APM auto-instrumentation, existing metrics. A "missing log" that middleware already emits is not a finding.
5. The data the code handles, for sensitivity checks (`logging-security-and-redaction` tiers).

## Process

1. **List the operations the diff changes**: each endpoint, handler, consumer, job, external call, state transition, and error path.
2. **For each operation**, apply the decision framework from `structured-logging-and-instrumentation`: are its important boundaries (completion with outcome and duration, failures, retries, fallbacks, state transitions) observable? Compare with the observability plan.
3. **For each added or changed log call**, check it against the review categories ([references/review-checklist.md](references/review-checklist.md)): necessity, structure, severity, fields, sensitivity, volume, duplication.
4. **For each exception path**, check that it is logged once at the handling layer with an `error_code` and context, not at every layer and not swallowed silently.
5. **For each boundary crossing** (outbound HTTP, publish, consume, task enqueue, executor), check correlation propagation (`distributed-tracing-and-correlation`).
6. **For each new metric**, check type, unit, and label cardinality.
7. **Separate audit from diagnostics**: if the code relies on a log line as the record of a decision, money movement, or permission change, flag it. Audit needs a durable record (`financial-auditability`).
8. **Verify before you report.** For each candidate finding, confirm it against the code: read the formatter config before claiming fields are dropped; read the middleware before claiming a request isn't logged; check the value's origin before calling it PII. Drop findings you can't support.
9. **Write findings** in the output format, most severe first.

### Severity

Aligned with the Software Factory `CODE_REVIEW` scale:

| Severity | Observability examples |
|---|---|
| **Blocker** | Tier-1 secret or raw tier-2 data in a log; log statement that will crash (`extra` key collision, invented wrapper method) |
| **Major** | Critical operation with no failure signal; correlation lost across a boundary; exception swallowed with no log; audit relying on a log line; unbounded metric label |
| **Minor** | Wrong level (business rejection at ERROR); duplicated exception logging; missing `duration_ms` on an important operation; verbose message carrying data that belongs in fields |
| **Nit** | Event naming inconsistency, field order |

## Output

```markdown
## Observability review: <branch or PR>
Scope: <base>..<head>, <n> files; observability plan: <link or "none">

| # | Severity | Location | Finding | Failure scenario | Suggested fix |
|---|---|---|---|---|---|
| 1 | Blocker | api/views.py:42 | Logs `request.headers` | Authorization bearer tokens land in the log platform | Log `request_id` and route only |
| 2 | Major | workers/score.py:17 | Consumer drops `correlation_id` | Can't join worker failures to the originating API request | Extract attribute and bind context (see distributed-tracing-and-correlation) |

Confirmed good: <what is already well instrumented, briefly>
Not reviewed / unverifiable: <e.g. production log pipeline parsing>
Verdict: approve | approve with follow-ups | request changes
```

No findings is a valid result: say what was checked.

## Verification

- [ ] Every operation the diff changes was considered, including error paths.
- [ ] Every finding cites `file:line`, a concrete failure scenario, and a fix, and was confirmed against the code (formatter, middleware, data origin).
- [ ] Over-instrumentation (noise, duplicates, hot-path INFO) was checked, not only gaps.
- [ ] Sensitive-data findings name the tier, never quote the sensitive value.
- [ ] Limits of the review are stated.

## Escalation

Escalate (don't decide alone) when: a Blocker sensitive-data finding concerns code **already deployed** (possible exposure incident); the project has no logging convention to review against; or the fix requires a platform decision (new tracing SDK, new metric backend).

## Red flags in a review

- Approving because "logging looks fine" without listing the operations checked
- Demanding a log on every function: that's a false positive, not rigor
- Flagging `user_id` as PII without checking what the id is (or accepting it without checking)
- Claiming fields are dropped without reading the formatter configuration

## References

- [references/review-checklist.md](references/review-checklist.md): category-by-category checks with detection hints.
